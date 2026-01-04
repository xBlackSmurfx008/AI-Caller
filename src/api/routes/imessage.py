"""iMessage ingestion routes (Mac connector uploads normalized iMessage events)."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from src.database.database import get_db
from src.memory.background_tasks import queue_summary_generation
from src.memory.memory_service import MemoryService
from src.security.auth import require_godfather
from src.utils.logging import get_logger

logger = get_logger(__name__)
router = APIRouter()

memory_service = MemoryService()


class IMessageEvent(BaseModel):
    # Uniqueness / identity
    message_guid: str = Field(..., description="Unique GUID from Messages database (message.guid)")
    chat_identifier: Optional[str] = Field(None, description="Chat identifier (group/thread identifier)")

    # Who + direction
    handle: str = Field(..., description="Sender/peer handle (phone or email)")
    is_from_me: bool = Field(..., description="True if message was sent by you")

    # Content
    text: str = Field("", description="Message text (may be empty for attachments)")
    service: Optional[str] = Field(None, description="Service name, e.g. iMessage/SMS")

    # Timestamp
    sent_at_iso: Optional[str] = Field(None, description="Original message timestamp (ISO8601) if available")

    # Optional raw fields
    raw: Optional[Dict[str, Any]] = Field(default=None, description="Optional raw fields for debugging")


class IMessageIngestRequest(BaseModel):
    events: List[IMessageEvent]
    source: str = Field("mac_connector", description="Source identifier")
    uploaded_at_iso: Optional[str] = None


def _split_handle(handle: str) -> Dict[str, Optional[str]]:
    h = (handle or "").strip()
    if not h:
        return {"phone_number": None, "email": None}
    if "@" in h:
        return {"phone_number": None, "email": h}
    return {"phone_number": h, "email": None}


@router.post("/ingest")
async def ingest_imessage(
    request: Request,
    payload: IMessageIngestRequest,
    db: Session = Depends(get_db),
):
    """
    Ingest iMessage/SMS events from a Mac connector into Interaction rows.

    Auth: requires Godfather token (X-Auth-Token / X-Godfather-Token / Authorization: Bearer).
    """
    require_godfather(request)

    if not payload.events:
        return {"ok": True, "ingested": 0, "skipped": 0}

    ingested = 0
    skipped = 0
    errors: list[dict[str, Any]] = []

    for ev in payload.events:
        try:
            ident = _split_handle(ev.handle)
            if not ident["phone_number"] and not ident["email"]:
                skipped += 1
                continue

            contact = memory_service.create_contact_if_missing(
                db,
                phone_number=ident["phone_number"],
                email=ident["email"],
            )

            direction = "outbound" if ev.is_from_me else "inbound"
            raw_content = (
                f"iMessage {direction} ({ev.service or 'unknown'}):\n"
                f"{ev.text or ''}"
            ).strip()

            meta: Dict[str, Any] = {
                "provider": "apple_messages",
                "message_guid": ev.message_guid,
                "chat_identifier": ev.chat_identifier,
                "handle": ev.handle,
                "direction": direction,
                "service": ev.service,
                "sent_at_iso": ev.sent_at_iso,
                "source": payload.source,
                "uploaded_at_iso": payload.uploaded_at_iso or datetime.utcnow().isoformat(),
            }
            if ev.raw:
                meta["raw"] = ev.raw

            interaction = memory_service.store_interaction(
                db=db,
                contact_id=contact.id,
                channel="imessage",
                raw_content=raw_content,
                metadata=meta,
            )

            # Best-effort summary generation (background worker if enabled; safe to queue).
            try:
                queue_summary_generation(interaction.id, contact.id, contact.name)
            except Exception as e:
                logger.warning("imessage_summary_queue_failed", error=str(e), interaction_id=interaction.id)

            ingested += 1
        except Exception as e:
            err = {"guid": getattr(ev, "message_guid", None), "error": str(e)}
            errors.append(err)
            logger.warning("imessage_event_ingest_failed", **err)
            skipped += 1

    return {"ok": True, "ingested": ingested, "skipped": skipped, "errors": errors}


