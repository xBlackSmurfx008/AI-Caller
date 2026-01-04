"""Chat memory service: durable chat history + rolling summaries."""

from __future__ import annotations

from typing import Optional, List, Dict, Any

from sqlalchemy.orm import Session
from sqlalchemy import func

from src.database.models import ChatMessage, ChatSessionSummary
from src.utils.config import get_settings
from src.utils.openai_client import create_openai_client, ensure_chat_model
from src.utils.logging import get_logger

logger = get_logger(__name__)
settings = get_settings()


class ChatMemoryService:
    """
    Maintains a rolling summary for a chat session.

    This is intentionally lightweight:
    - summaries are plain text (not embeddings yet)
    - updated periodically to avoid extra cost every turn
    """

    def __init__(self):
        self.client = create_openai_client(timeout=60.0, max_retries=3)
        self.model = ensure_chat_model(getattr(settings, "OPENAI_MODEL", "gpt-4o"))

    def maybe_update_summary(
        self,
        db: Session,
        session_id: str,
        *,
        force: bool = False,
        every_n_messages: int = 12,
        max_messages_for_update: int = 60,
    ) -> Optional[ChatSessionSummary]:
        """
        Update the rolling summary if needed.
        """
        total = db.query(func.count(ChatMessage.id)).filter(ChatMessage.session_id == session_id).scalar() or 0
        if total == 0:
            return None

        if not force and (total % every_n_messages != 0):
            return None

        # Pull a bounded window of recent messages (avoid huge prompts).
        msgs: List[ChatMessage] = (
            db.query(ChatMessage)
            .filter(ChatMessage.session_id == session_id)
            .order_by(ChatMessage.created_at.desc())
            .limit(max_messages_for_update)
            .all()
        )
        msgs = list(reversed(msgs))

        existing = db.query(ChatSessionSummary).filter(ChatSessionSummary.session_id == session_id).first()
        existing_text = existing.summary if existing else ""

        transcript_lines: List[str] = []
        for m in msgs:
            role = (m.role or "").strip()
            if role not in {"user", "assistant"}:
                continue
            prefix = "User" if role == "user" else "Assistant"
            transcript_lines.append(f"{prefix}: {m.content}")

        transcript = "\n".join(transcript_lines).strip()
        if not transcript:
            return None

        prompt = f"""You are updating a rolling conversation summary.

Existing summary (may be empty):
{existing_text}

Newer conversation excerpts:
{transcript}

Write an updated summary that preserves:
- stable facts (preferences, constraints, identity, ongoing projects)
- decisions made and why
- open loops / TODOs / commitments
- important context that should persist across future turns

Keep it concise but information-dense (aim 10-20 bullet points max)."""

        try:
            resp = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You write concise, high-signal conversation summaries."},
                    {"role": "user", "content": prompt},
                ],
                temperature=0.2,
                max_tokens=400,
            )
            new_summary = (resp.choices[0].message.content or "").strip()
            if not new_summary:
                return None

            if existing:
                existing.summary = new_summary
                existing.version = (existing.version or 1) + 1
                db.commit()
                db.refresh(existing)
                return existing

            created = ChatSessionSummary(session_id=session_id, summary=new_summary, version=1)
            db.add(created)
            db.commit()
            db.refresh(created)
            return created
        except Exception as e:
            logger.warning("chat_summary_update_failed", session_id=session_id, error=str(e))
            db.rollback()
            return None


