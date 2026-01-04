"""
Email ingestion routes for periodic email sync (Gmail/Outlook → Interactions).

This module provides:
1. /api/email-ingest/gmail - Sync recent Gmail messages to Interactions
2. /api/email-ingest/outlook - Sync recent Outlook messages to Interactions
3. /api/email-ingest/trigger - Manually trigger a sync (or called by cron)

The sync is "pull-based" - we fetch recent emails and store as Interactions.
Deduplication is handled by message_id in metadata.
"""

from __future__ import annotations

import base64
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel
from sqlalchemy.orm import Session

from src.database.database import get_db
from src.memory.background_tasks import queue_summary_generation
from src.memory.memory_service import MemoryService
from src.security.auth import require_godfather
from src.utils.logging import get_logger

logger = get_logger(__name__)
router = APIRouter()

memory_service = MemoryService()


class EmailIngestResult(BaseModel):
    provider: str
    ok: bool
    ingested: int = 0
    skipped: int = 0
    error: Optional[str] = None


def _extract_email_address(from_header: str) -> Optional[str]:
    """Extract email address from 'Name <email@example.com>' format."""
    if not from_header:
        return None
    from_header = from_header.strip()
    if "<" in from_header and ">" in from_header:
        start = from_header.rfind("<") + 1
        end = from_header.rfind(">")
        return from_header[start:end].strip().lower()
    if "@" in from_header:
        return from_header.strip().lower()
    return None


async def _ingest_gmail_messages(
    db: Session,
    max_messages: int = 50,
    query: str = "newer_than:1d",
) -> EmailIngestResult:
    """
    Fetch recent Gmail messages and store as Interactions.
    
    Args:
        db: Database session
        max_messages: Max messages to fetch
        query: Gmail search query (default: last 24 hours)
    
    Returns:
        EmailIngestResult with counts
    """
    try:
        from src.email.gmail import is_gmail_connected, list_gmail_messages, get_gmail_message
    except ImportError:
        return EmailIngestResult(provider="gmail", ok=False, error="Gmail module not available")
    
    if not is_gmail_connected():
        return EmailIngestResult(provider="gmail", ok=False, error="Gmail not connected")
    
    ingested = 0
    skipped = 0
    
    try:
        # List recent messages
        result = list_gmail_messages(query=query, max_results=max_messages)
        messages = result.get("messages", [])
        
        for msg_stub in messages:
            msg_id = msg_stub.get("id")
            if not msg_id:
                continue
            
            try:
                # Get full message
                full_msg = get_gmail_message(msg_id, format="full")
                payload = full_msg.get("payload", {})
                headers = {h["name"]: h["value"] for h in payload.get("headers", [])}
                
                from_email = _extract_email_address(headers.get("From", ""))
                if not from_email:
                    skipped += 1
                    continue
                
                # Skip if this is from us (outbound - already captured by send_email)
                # We primarily want to capture inbound emails
                # TODO: Could also capture outbound by checking "To" header
                
                # Extract body
                body_text = ""
                if "parts" in payload:
                    for part in payload["parts"]:
                        if part.get("mimeType") == "text/plain":
                            data = part.get("body", {}).get("data", "")
                            if data:
                                body_text = base64.urlsafe_b64decode(data).decode("utf-8", errors="ignore")
                                break
                else:
                    if payload.get("mimeType") == "text/plain":
                        data = payload.get("body", {}).get("data", "")
                        if data:
                            body_text = base64.urlsafe_b64decode(data).decode("utf-8", errors="ignore")
                
                if not body_text:
                    body_text = full_msg.get("snippet", "")
                
                # Find or create contact
                contact = memory_service.create_contact_if_missing(db, email=from_email)
                
                # Build raw content
                subject = headers.get("Subject", "(no subject)")
                raw_content = f"Email from {from_email}:\nSubject: {subject}\n\n{body_text}"
                
                # Store as interaction (dedup by message_id in metadata)
                meta = {
                    "provider": "gmail",
                    "message_id": msg_id,
                    "thread_id": full_msg.get("threadId"),
                    "from": headers.get("From"),
                    "to": headers.get("To"),
                    "subject": subject,
                    "date": headers.get("Date"),
                    "direction": "inbound",
                }
                
                interaction = memory_service.store_interaction(
                    db=db,
                    contact_id=contact.id,
                    channel="email",
                    raw_content=raw_content,
                    metadata=meta,
                )
                
                # Queue summary generation
                try:
                    queue_summary_generation(interaction.id, contact.id, contact.name)
                except Exception as e:
                    logger.warning("gmail_summary_queue_failed", error=str(e))
                
                ingested += 1
                
            except Exception as e:
                logger.warning("gmail_message_ingest_failed", message_id=msg_id, error=str(e))
                skipped += 1
        
        return EmailIngestResult(provider="gmail", ok=True, ingested=ingested, skipped=skipped)
        
    except Exception as e:
        logger.error("gmail_ingest_failed", error=str(e))
        return EmailIngestResult(provider="gmail", ok=False, error=str(e))


async def _ingest_outlook_messages(
    db: Session,
    max_messages: int = 50,
) -> EmailIngestResult:
    """
    Fetch recent Outlook messages and store as Interactions.
    
    Args:
        db: Database session
        max_messages: Max messages to fetch
    
    Returns:
        EmailIngestResult with counts
    """
    try:
        from src.email.outlook import is_outlook_connected, list_outlook_messages, get_outlook_message
    except ImportError:
        return EmailIngestResult(provider="outlook", ok=False, error="Outlook module not available")
    
    if not is_outlook_connected():
        return EmailIngestResult(provider="outlook", ok=False, error="Outlook not connected")
    
    ingested = 0
    skipped = 0
    
    try:
        # List recent messages (Outlook doesn't have simple date query like Gmail)
        # We'll just get the most recent and let dedup handle already-synced ones
        result = list_outlook_messages(top=max_messages)
        messages = result.get("messages", [])
        
        for msg in messages:
            msg_id = msg.get("id")
            if not msg_id:
                continue
            
            try:
                # Get full message if needed (list may already have full content)
                from_addr = msg.get("from", {}).get("emailAddress", {}).get("address", "")
                if not from_addr:
                    skipped += 1
                    continue
                
                from_email = from_addr.lower()
                
                # Find or create contact
                contact = memory_service.create_contact_if_missing(db, email=from_email)
                
                # Build raw content
                subject = msg.get("subject", "(no subject)")
                body_content = msg.get("body", {}).get("content", "") or msg.get("bodyPreview", "")
                raw_content = f"Email from {from_email}:\nSubject: {subject}\n\n{body_content}"
                
                # Store as interaction
                meta = {
                    "provider": "outlook",
                    "message_id": msg_id,
                    "conversation_id": msg.get("conversationId"),
                    "from": from_email,
                    "subject": subject,
                    "date": msg.get("receivedDateTime"),
                    "direction": "inbound",
                }
                
                interaction = memory_service.store_interaction(
                    db=db,
                    contact_id=contact.id,
                    channel="email",
                    raw_content=raw_content,
                    metadata=meta,
                )
                
                # Queue summary generation
                try:
                    queue_summary_generation(interaction.id, contact.id, contact.name)
                except Exception as e:
                    logger.warning("outlook_summary_queue_failed", error=str(e))
                
                ingested += 1
                
            except Exception as e:
                logger.warning("outlook_message_ingest_failed", message_id=msg_id, error=str(e))
                skipped += 1
        
        return EmailIngestResult(provider="outlook", ok=True, ingested=ingested, skipped=skipped)
        
    except Exception as e:
        logger.error("outlook_ingest_failed", error=str(e))
        return EmailIngestResult(provider="outlook", ok=False, error=str(e))


@router.post("/gmail")
async def ingest_gmail(
    request: Request,
    max_messages: int = 50,
    query: str = "newer_than:1d",
    db: Session = Depends(get_db),
):
    """
    Ingest recent Gmail messages into Interactions.
    
    Auth: requires Godfather token.
    """
    require_godfather(request)
    result = await _ingest_gmail_messages(db, max_messages=max_messages, query=query)
    return result


@router.post("/outlook")
async def ingest_outlook(
    request: Request,
    max_messages: int = 50,
    db: Session = Depends(get_db),
):
    """
    Ingest recent Outlook messages into Interactions.
    
    Auth: requires Godfather token.
    """
    require_godfather(request)
    result = await _ingest_outlook_messages(db, max_messages=max_messages)
    return result


@router.post("/trigger")
async def trigger_email_ingest(
    request: Request,
    providers: Optional[List[str]] = None,
    db: Session = Depends(get_db),
):
    """
    Trigger email ingestion for one or more providers.
    
    Args:
        providers: List of providers to sync ("gmail", "outlook"). Default: all connected.
    
    Auth: requires Godfather token.
    """
    require_godfather(request)
    
    results = {}
    providers = providers or ["gmail", "outlook"]
    
    if "gmail" in providers:
        results["gmail"] = await _ingest_gmail_messages(db)
    
    if "outlook" in providers:
        results["outlook"] = await _ingest_outlook_messages(db)
    
    return {"ok": True, "results": results}

