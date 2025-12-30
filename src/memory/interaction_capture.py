"""Helper functions for capturing interactions after tool execution"""

from typing import Dict, Any, Optional
from sqlalchemy.orm import Session
from src.memory.memory_service import MemoryService
from src.memory.background_tasks import queue_summary_generation, start_background_worker
from src.utils.logging import get_logger

logger = get_logger(__name__)
memory_service = MemoryService()

# Start background worker on module load
try:
    start_background_worker()
except Exception as e:
    logger.warning("failed_to_start_background_worker", error=str(e))


async def capture_sms_interaction(
    db: Session,
    to_number: str,
    message: str,
    message_sid: Optional[str] = None
) -> None:
    """
    Capture SMS interaction after sending
    
    Args:
        db: Database session
        to_number: Phone number SMS was sent to
        message: Message content
        message_sid: Optional Twilio message SID
    """
    try:
        # Find or create contact by phone number
        contact = memory_service.create_contact_if_missing(db, phone_number=to_number)
        
        # Store interaction
        raw_content = f"SMS sent to {contact.name}:\n{message}"
        metadata = {
            "message_sid": message_sid,
            "to_number": to_number,
            "direction": "outbound"
        }
        
        interaction = memory_service.store_interaction(
            db=db,
            contact_id=contact.id,
            channel="sms",
            raw_content=raw_content,
            metadata=metadata
        )
        
        # Queue summary generation in background
        try:
            queue_summary_generation(interaction.id, contact.id, contact.name)
        except Exception as e:
            logger.error("sms_summary_queue_failed", error=str(e), interaction_id=interaction.id)
            # Fallback to synchronous if queue fails
            try:
                memory_service.generate_summary(db, interaction.id, contact.name)
            except Exception as e2:
                logger.error("sms_summary_generation_failed", error=str(e2), interaction_id=interaction.id)
        
    except Exception as e:
        logger.error("sms_interaction_capture_failed", error=str(e), to_number=to_number)


async def capture_email_interaction(
    db: Session,
    to_email: str,
    subject: str,
    body: str
) -> None:
    """
    Capture email interaction after sending
    
    Args:
        db: Database session
        to_email: Email address email was sent to
        subject: Email subject
        body: Email body
    """
    try:
        # Find or create contact by email
        contact = memory_service.create_contact_if_missing(db, email=to_email)
        
        # Store interaction
        raw_content = f"Email sent to {contact.name}:\nSubject: {subject}\n\n{body}"
        metadata = {
            "to_email": to_email,
            "subject": subject,
            "direction": "outbound"
        }
        
        interaction = memory_service.store_interaction(
            db=db,
            contact_id=contact.id,
            channel="email",
            raw_content=raw_content,
            metadata=metadata
        )
        
        # Queue summary generation in background
        try:
            queue_summary_generation(interaction.id, contact.id, contact.name)
        except Exception as e:
            logger.error("email_summary_queue_failed", error=str(e), interaction_id=interaction.id)
            # Fallback to synchronous if queue fails
            try:
                memory_service.generate_summary(db, interaction.id, contact.name)
            except Exception as e2:
                logger.error("email_summary_generation_failed", error=str(e2), interaction_id=interaction.id)
        
    except Exception as e:
        logger.error("email_interaction_capture_failed", error=str(e), to_email=to_email)


def capture_call_transcript_sync(
    db: Session,
    contact_id: str,
    transcript: str,
    call_sid: Optional[str] = None,
    metadata: Optional[Dict[str, Any]] = None
) -> None:
    """
    Synchronous wrapper for capturing call transcripts
    
    Args:
        db: Database session
        contact_id: Contact ID
        transcript: Full call transcript
        call_sid: Optional Twilio call SID
        metadata: Optional additional metadata
    """
    import asyncio
    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            # If loop is running, we can't use run_until_complete
            # Schedule as task instead (fire and forget)
            asyncio.create_task(capture_call_transcript(
                db, contact_id, transcript, call_sid, metadata
            ))
        else:
            loop.run_until_complete(capture_call_transcript(
                db, contact_id, transcript, call_sid, metadata
            ))
    except RuntimeError:
        # No event loop, create new one
        asyncio.run(capture_call_transcript(
            db, contact_id, transcript, call_sid, metadata
        ))


async def capture_call_transcript(
    db: Session,
    contact_id: str,
    transcript: str,
    call_sid: Optional[str] = None,
    metadata: Optional[Dict[str, Any]] = None
) -> None:
    """
    Capture call transcript after call completes
    
    Args:
        db: Database session
        contact_id: Contact ID
        transcript: Full call transcript
        call_sid: Optional Twilio call SID
        metadata: Optional additional metadata
    """
    try:
        if not transcript or len(transcript.strip()) < 10:
            logger.info("call_transcript_skipped_too_short", contact_id=contact_id)
            return
        
        # Store interaction
        interaction_metadata = {
            "call_sid": call_sid,
            **(metadata or {})
        }
        
        interaction = memory_service.store_interaction(
            db=db,
            contact_id=contact_id,
            channel="call",
            raw_content=transcript,
            metadata=interaction_metadata
        )
        
        # Get contact name
        from src.database.models import Contact
        contact = db.query(Contact).filter(Contact.id == contact_id).first()
        contact_name = contact.name if contact else None
        
        # Queue summary generation in background
        try:
            queue_summary_generation(interaction.id, contact_id, contact_name)
        except Exception as e:
            logger.error("call_summary_queue_failed", error=str(e), interaction_id=interaction.id)
            # Fallback to synchronous if queue fails
            try:
                memory_service.generate_summary(db, interaction.id, contact_name)
            except Exception as e2:
                logger.error("call_summary_generation_failed", error=str(e2), interaction_id=interaction.id)
        
    except Exception as e:
        logger.error("call_transcript_capture_failed", error=str(e), contact_id=contact_id)

