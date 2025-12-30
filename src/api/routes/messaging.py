"""Messaging routes for Twilio SMS/MMS/WhatsApp"""

from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session
from typing import List, Optional
from pydantic import BaseModel
from datetime import datetime

from src.database.database import get_db
from src.database.models import Message, Contact, OutboundApproval, Suggestion
from src.messaging.messaging_service import MessagingService
from src.orchestrator.orchestrator_service import OrchestratorService
from src.memory.memory_service import MemoryService
from src.utils.logging import get_logger
from src.utils.rate_limit import limiter, get_rate_limit

# TODO: Add authentication middleware
# from src.api.middleware.auth import require_auth
# @require_auth  # Add to all endpoints

logger = get_logger(__name__)
router = APIRouter()

messaging_service = MessagingService()
orchestrator_service = OrchestratorService()
memory_service = MemoryService()


class MessageSendRequest(BaseModel):
    contact_id: str
    channel: str  # "sms", "mms", "whatsapp"
    text_content: str
    media_urls: Optional[List[str]] = None
    draft_id: Optional[str] = None


class MessageApproveRequest(BaseModel):
    message_id: str
    approved: bool


class MessageResponse(BaseModel):
    id: str
    contact_id: Optional[str]
    channel: str
    direction: str
    timestamp: str
    text_content: Optional[str]
    media_urls: Optional[List[str]]
    status: Optional[str]
    conversation_id: Optional[str]
    
    class Config:
        from_attributes = True


class ConversationResponse(BaseModel):
    conversation_id: str
    contact_id: Optional[str]
    contact_name: str
    channel: str
    messages: List[MessageResponse]
    unread_count: int = 0


class ConversationSummaryResponse(BaseModel):
    conversation_id: str
    contact_id: Optional[str]
    contact_name: str
    channel: str
    latest_message: dict
    unread_count: int = 0


class MessageDraftResponse(BaseModel):
    channel: str
    draft: str
    rationale: str
    risk_flags: Optional[List[str]]
    tone_guidance: Optional[str]


@router.get("/conversations", response_model=List[ConversationSummaryResponse])
@limiter.limit(get_rate_limit("messaging_conversations"))
async def list_conversations(
    request: Request,
    limit: int = 20,
    db: Session = Depends(get_db)
):
    """List all conversations"""
    conversations = messaging_service.get_all_conversations(db=db, limit=limit)
    return conversations


@router.get("/conversations/{contact_id}/{channel}", response_model=ConversationResponse)
async def get_conversation(
    contact_id: str,
    channel: str,
    limit: int = 50,
    db: Session = Depends(get_db)
):
    """Get conversation messages for a contact + channel"""
    # Verify contact exists
    contact = db.query(Contact).filter(Contact.id == contact_id).first()
    if not contact:
        raise HTTPException(status_code=404, detail="Contact not found")
    
    messages = messaging_service.get_conversation(
        db=db,
        contact_id=contact_id,
        channel=channel,
        limit=limit
    )
    
    return {
        "conversation_id": messaging_service.get_or_create_conversation_id(db, contact_id, channel),
        "contact_id": contact_id,
        "contact_name": contact.name,
        "channel": channel,
        "messages": [
            {
                "id": msg.id,
                "contact_id": msg.contact_id,
                "channel": msg.channel,
                "direction": msg.direction,
                "timestamp": msg.timestamp.isoformat(),
                "text_content": msg.text_content,
                "media_urls": msg.media_urls or [],
                "status": msg.status,
                "conversation_id": msg.conversation_id
            }
            for msg in messages
        ],
        "unread_count": messaging_service._get_unread_count(db, messaging_service.get_or_create_conversation_id(db, contact_id, channel))
    }


@router.post("/send", response_model=MessageResponse)
@limiter.limit(get_rate_limit("messaging_send"))
async def send_message(
    http_request: Request,
    request: MessageSendRequest,
    db: Session = Depends(get_db)
):
    """Create a draft message (requires approval before sending)"""
    # Check if contact exists
    contact = db.query(Contact).filter(Contact.id == request.contact_id).first()
    if not contact:
        raise HTTPException(status_code=404, detail="Contact not found")
    
    # Check if contact has do-not-message flag
    if contact.is_sensitive:
        raise HTTPException(
            status_code=403,
            detail="Contact is marked as do-not-message"
        )
    
    # Create draft message (requires approval)
    try:
        message, approval = messaging_service.create_draft_message(
            db=db,
            contact_id=request.contact_id,
            channel=request.channel,
            text_content=request.text_content,
            media_urls=request.media_urls,
            draft_id=request.draft_id
        )
        
        return {
            "id": message.id,
            "contact_id": message.contact_id,
            "channel": message.channel,
            "direction": message.direction,
            "timestamp": message.timestamp.isoformat(),
            "text_content": message.text_content,
            "media_urls": message.media_urls or [],
            "status": message.status,
            "conversation_id": message.conversation_id
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error("create_draft_message_error", error=str(e))
        db.rollback()
        raise HTTPException(status_code=500, detail="Failed to create draft message")


@router.post("/approve")
@limiter.limit(get_rate_limit("messaging_approve"))
async def approve_message(
    http_request: Request,
    request: MessageApproveRequest,
    db: Session = Depends(get_db)
):
    """Approve or reject a pending message"""
    approval = db.query(OutboundApproval).join(Message).filter(
        Message.id == request.message_id
    ).first()
    
    if not approval:
        raise HTTPException(status_code=404, detail="Message approval not found")
    
    if approval.status != "pending":
        raise HTTPException(
            status_code=400,
            detail=f"Message already {approval.status}"
        )
    
    if request.approved:
        # Send approved message via Twilio
        try:
            message, approval = messaging_service.send_approved_message(
                db=db,
                message_id=request.message_id
            )
            
            return {
                "success": True,
                "message": "Message sent",
                "message_id": message.id,
                "twilio_message_sid": message.twilio_message_sid,
                "status": message.status
            }
        except ValueError as e:
            db.rollback()
            raise HTTPException(status_code=400, detail=str(e))
        except Exception as e:
            logger.error("approve_and_send_failed", error=str(e))
            db.rollback()
            raise HTTPException(status_code=500, detail="Failed to send message")
    else:
        approval.status = "rejected"
        approval.approved_at = datetime.utcnow()
        db.commit()
        
        return {"success": True, "message": "Message rejected"}


@router.get("/drafts/{contact_id}", response_model=List[MessageDraftResponse])
@limiter.limit(get_rate_limit("messaging_drafts"))
async def get_message_drafts(
    request: Request,
    contact_id: str,
    channel: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """Get AI-generated message drafts for a contact"""
    # Verify contact exists
    contact = db.query(Contact).filter(Contact.id == contact_id).first()
    if not contact:
        raise HTTPException(status_code=404, detail="Contact not found")
    
    # Get memory context
    memory_context = memory_service.get_contact_context(db=db, contact_id=contact_id)
    
    # Get active suggestions
    suggestions = db.query(Suggestion).filter(
        Suggestion.contact_id == contact_id,
        Suggestion.status == "pending",
        Suggestion.message_draft.isnot(None)
    ).order_by(Suggestion.score.desc()).limit(5).all()
    
    drafts = []
    
    # Generate channel recommendations and drafts
    channels = ["sms", "whatsapp"] if not channel else [channel]
    
    for ch in channels:
        # Use orchestrator to generate draft
        try:
            draft_result = orchestrator_service.generate_message_draft(
                db=db,
                contact_id=contact_id,
                channel=ch,
                memory_context=memory_context
            )
            
            if draft_result:
                drafts.append({
                    "channel": ch,
                    "draft": draft_result.get("draft", ""),
                    "rationale": draft_result.get("rationale", ""),
                    "risk_flags": draft_result.get("risk_flags", []),
                    "tone_guidance": draft_result.get("tone_guidance")
                })
        except Exception as e:
            logger.error("draft_generation_failed", error=str(e), contact_id=contact_id, channel=ch)
    
    # Also include drafts from suggestions
    for suggestion in suggestions:
        if suggestion.message_draft:
            drafts.append({
                "channel": channel or "sms",  # Default channel
                "draft": suggestion.message_draft,
                "rationale": suggestion.rationale or "",
                "risk_flags": suggestion.risk_flags or [],
                "tone_guidance": None
            })
    
    return drafts


@router.get("/suggestions/{contact_id}")
@limiter.limit(get_rate_limit("messaging_suggestions"))
async def get_message_suggestions(
    request: Request,
    contact_id: str,
    db: Session = Depends(get_db)
):
    """Get AI suggestions for messaging a contact"""
    # Verify contact exists
    contact = db.query(Contact).filter(Contact.id == contact_id).first()
    if not contact:
        raise HTTPException(status_code=404, detail="Contact not found")
    
    # Get memory context
    memory_context = memory_service.get_contact_context(db=db, contact_id=contact_id)
    
    # Get channel recommendation
    channel_rec = orchestrator_service.recommend_channel(
        db=db,
        contact_id=contact_id,
        memory_context=memory_context
    )
    
    # Get active suggestions
    suggestions = db.query(Suggestion).filter(
        Suggestion.contact_id == contact_id,
        Suggestion.status == "pending"
    ).order_by(Suggestion.score.desc()).limit(10).all()
    
    return {
        "contact_id": contact_id,
        "contact_name": contact.name,
        "recommended_channel": channel_rec.get("channel", "sms"),
        "channel_rationale": channel_rec.get("rationale", ""),
        "suggestions": [
            {
                "id": sug.id,
                "type": sug.suggestion_type,
                "intent": sug.intent,
                "rationale": sug.rationale,
                "message_draft": sug.message_draft,
                "best_timing": sug.best_timing,
                "score": sug.score,
                "risk_flags": sug.risk_flags or []
            }
            for sug in suggestions
        ],
        "memory_context": memory_context
    }


@router.post("/conversations/{contact_id}/{channel}/read")
async def mark_conversation_read(
    contact_id: str,
    channel: str,
    db: Session = Depends(get_db)
):
    """Mark all messages in a conversation as read"""
    # Verify contact exists
    contact = db.query(Contact).filter(Contact.id == contact_id).first()
    if not contact:
        raise HTTPException(status_code=404, detail="Contact not found")
    
    conversation_id = messaging_service.get_or_create_conversation_id(db, contact_id, channel)
    
    try:
        count = messaging_service.mark_conversation_as_read(db, conversation_id)
        return {
            "success": True,
            "conversation_id": conversation_id,
            "messages_marked_read": count
        }
    except Exception as e:
        logger.error("mark_conversation_read_error", error=str(e))
        db.rollback()
        raise HTTPException(status_code=500, detail="Failed to mark conversation as read")

