"""Chat sessions API (durable chat history)."""

from __future__ import annotations

from datetime import datetime
from typing import Optional, List, Dict, Any
import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from src.database.database import get_db
from src.database.models import ChatSession, ChatMessage, ChatSessionSummary
from src.utils.logging import get_logger

router = APIRouter()
logger = get_logger(__name__)


class ChatSessionCreateRequest(BaseModel):
    title: Optional[str] = None
    scope_type: Optional[str] = None  # "global" | "project"
    scope_id: Optional[str] = None    # project_id when scope_type=="project"
    actor_phone: Optional[str] = None
    actor_email: Optional[str] = None


class ChatSessionResponse(BaseModel):
    id: str
    title: Optional[str] = None
    scope_type: Optional[str] = None
    scope_id: Optional[str] = None
    actor_phone: Optional[str] = None
    actor_email: Optional[str] = None
    created_at: str
    updated_at: str

    class Config:
        from_attributes = True


class ChatMessageResponse(BaseModel):
    id: str
    role: str
    content: str
    metadata: Optional[Dict[str, Any]] = None
    created_at: str

    class Config:
        from_attributes = True


class ChatSessionDetailResponse(BaseModel):
    session: ChatSessionResponse
    summary: Optional[str] = None
    messages: List[ChatMessageResponse]


@router.post("/sessions", response_model=ChatSessionResponse, status_code=status.HTTP_201_CREATED)
async def create_chat_session(req: ChatSessionCreateRequest, db: Session = Depends(get_db)):
    session = ChatSession(
        id=str(uuid.uuid4()),
        title=(req.title or None),
        scope_type=(req.scope_type or "global"),
        scope_id=req.scope_id,
        actor_phone=req.actor_phone,
        actor_email=req.actor_email,
    )
    db.add(session)
    db.commit()
    db.refresh(session)
    return ChatSessionResponse(
        id=session.id,
        title=session.title,
        scope_type=session.scope_type,
        scope_id=session.scope_id,
        actor_phone=session.actor_phone,
        actor_email=session.actor_email,
        created_at=session.created_at.isoformat() if session.created_at else datetime.utcnow().isoformat(),
        updated_at=session.updated_at.isoformat() if session.updated_at else datetime.utcnow().isoformat(),
    )


@router.get("/sessions", response_model=List[ChatSessionResponse])
async def list_chat_sessions(limit: int = 50, db: Session = Depends(get_db)):
    sessions = db.query(ChatSession).order_by(ChatSession.updated_at.desc()).limit(limit).all()
    return [
        ChatSessionResponse(
            id=s.id,
            title=s.title,
            scope_type=s.scope_type,
            scope_id=s.scope_id,
            actor_phone=s.actor_phone,
            actor_email=s.actor_email,
            created_at=s.created_at.isoformat() if s.created_at else datetime.utcnow().isoformat(),
            updated_at=s.updated_at.isoformat() if s.updated_at else datetime.utcnow().isoformat(),
        )
        for s in sessions
    ]


@router.get("/sessions/{session_id}", response_model=ChatSessionDetailResponse)
async def get_chat_session(session_id: str, limit: int = 200, db: Session = Depends(get_db)):
    session = db.query(ChatSession).filter(ChatSession.id == session_id).first()
    if not session:
        raise HTTPException(status_code=404, detail="Chat session not found")

    summary = db.query(ChatSessionSummary).filter(ChatSessionSummary.session_id == session_id).first()
    messages = (
        db.query(ChatMessage)
        .filter(ChatMessage.session_id == session_id)
        .order_by(ChatMessage.created_at.asc())
        .limit(limit)
        .all()
    )

    return ChatSessionDetailResponse(
        session=ChatSessionResponse(
            id=session.id,
            title=session.title,
            scope_type=session.scope_type,
            scope_id=session.scope_id,
            actor_phone=session.actor_phone,
            actor_email=session.actor_email,
            created_at=session.created_at.isoformat() if session.created_at else datetime.utcnow().isoformat(),
            updated_at=session.updated_at.isoformat() if session.updated_at else datetime.utcnow().isoformat(),
        ),
        summary=summary.summary if summary else None,
        messages=[
            ChatMessageResponse(
                id=m.id,
                role=m.role,
                content=m.content,
                metadata=m.meta_data,
                created_at=m.created_at.isoformat() if m.created_at else datetime.utcnow().isoformat(),
            )
            for m in messages
        ],
    )


@router.delete("/sessions/{session_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_chat_session(session_id: str, db: Session = Depends(get_db)):
    session = db.query(ChatSession).filter(ChatSession.id == session_id).first()
    if not session:
        return
    db.delete(session)
    db.commit()
    return


