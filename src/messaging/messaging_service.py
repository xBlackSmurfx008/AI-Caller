"""Messaging service for handling Twilio messages, conversation threading, and contact resolution"""

from typing import Dict, Any, Optional, List, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, desc
from datetime import datetime, timedelta, date
import uuid
import json

from src.database.models import (
    Contact, Message, ChannelIdentity, OutboundApproval, Interaction, ContactMemoryState, MemorySummary
)
from src.telephony.twilio_client import TwilioService
from src.memory.memory_service import MemoryService
from src.cost.cost_event_logger import CostEventLogger
from src.security.policy import Actor, is_godfather
from src.utils.logging import get_logger
from src.utils.config import get_settings

logger = get_logger(__name__)
settings = get_settings()


def _json_safe(value: Any) -> Any:
    """Recursively convert values to JSON-serializable types (for JSON columns)."""
    if isinstance(value, (datetime, date)):
        return value.isoformat()
    if isinstance(value, uuid.UUID):
        return str(value)
    if isinstance(value, dict):
        return {str(k): _json_safe(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [_json_safe(v) for v in value]
    return value


class MessagingService:
    """Service for managing Twilio messaging (SMS/MMS/WhatsApp)"""
    
    def __init__(self):
        """Initialize messaging service"""
        self.twilio = TwilioService()
        self.memory_service = MemoryService()
        self.cost_logger = CostEventLogger()
    
    def normalize_twilio_payload(
        self,
        payload: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Normalize Twilio webhook payload into internal schema
        
        Args:
            payload: Raw Twilio webhook payload
            
        Returns:
            Normalized message data
        """
        # Determine channel
        from_number = payload.get("From", "")
        to_number = payload.get("To", "")
        
        if from_number.startswith("whatsapp:") or to_number.startswith("whatsapp:"):
            channel = "whatsapp"
            # Remove whatsapp: prefix for address
            from_address = from_number.replace("whatsapp:", "") if from_number.startswith("whatsapp:") else from_number
            to_address = to_number.replace("whatsapp:", "") if to_number.startswith("whatsapp:") else to_number
        else:
            # Check if MMS (has media)
            num_media = payload.get("NumMedia", "0")
            if num_media and int(num_media) > 0:
                channel = "mms"
            else:
                channel = "sms"
            from_address = from_number
            to_address = to_number
        
        # Extract media URLs
        media_urls = []
        num_media = int(payload.get("NumMedia", "0"))
        if num_media > 0:
            for i in range(num_media):
                media_url = payload.get(f"MediaUrl{i}", "")
                if media_url:
                    media_urls.append(media_url)
        
        return {
            "channel": channel,
            "from_address": from_address,
            "to_address": to_address,
            "from_number": from_number,  # Keep original for Twilio API
            "to_number": to_number,  # Keep original for Twilio API
            "text_content": payload.get("Body", ""),
            "media_urls": media_urls,
            "twilio_message_sid": payload.get("MessageSid"),
            "timestamp": datetime.utcnow(),  # Use current time or parse from Twilio if available
        }
    
    def resolve_contact(
        self,
        db: Session,
        address: str,
        channel: str
    ) -> Tuple[Optional[Contact], Optional[ChannelIdentity], bool]:
        """
        Resolve contact from channel address (phone number or WhatsApp ID)
        
        Args:
            db: Database session
            address: Phone number or WhatsApp ID (E.164 format)
            channel: "sms", "mms", or "whatsapp"
            
        Returns:
            (contact, channel_identity, is_provisional) tuple
            - contact: Contact instance or None
            - channel_identity: ChannelIdentity instance or None
            - is_provisional: True if contact was just created
        """
        # Look up existing channel identity
        channel_identity = db.query(ChannelIdentity).filter(
            and_(
                ChannelIdentity.address == address,
                ChannelIdentity.channel == channel
            )
        ).first()
        
        if channel_identity:
            contact = db.query(Contact).filter(Contact.id == channel_identity.contact_id).first()
            return (contact, channel_identity, False)
        
        # Try to find contact by phone number (for SMS/MMS)
        if channel in ["sms", "mms"]:
            contact = db.query(Contact).filter(Contact.phone_number == address).first()
            if contact:
                # Create channel identity
                channel_identity = ChannelIdentity(
                    contact_id=contact.id,
                    channel=channel,
                    address=address,
                    verified=True
                )
                db.add(channel_identity)
                try:
                    db.commit()
                    db.refresh(channel_identity)
                except Exception as e:
                    db.rollback()
                    logger.error("create_channel_identity_failed", error=str(e))
                    raise
                return (contact, channel_identity, False)
        
        # Create provisional contact
        contact = Contact(
            name=f"Unknown ({address})",
            phone_number=address if channel in ["sms", "mms"] else None,
            notes=f"Provisional contact created from {channel} message"
        )
        db.add(contact)
        try:
            db.commit()
            db.refresh(contact)
        except Exception as e:
            db.rollback()
            logger.error("create_provisional_contact_failed", error=str(e))
            raise
        
        # Create channel identity
        channel_identity = ChannelIdentity(
            contact_id=contact.id,
            channel=channel,
            address=address,
            verified=False
        )
        db.add(channel_identity)
        try:
            db.commit()
            db.refresh(channel_identity)
        except Exception as e:
            db.rollback()
            logger.error("create_provisional_channel_identity_failed", error=str(e))
            raise
        
        logger.info(
            "provisional_contact_created",
            contact_id=contact.id,
            address=address,
            channel=channel
        )
        
        return (contact, channel_identity, True)
    
    def get_or_create_conversation_id(
        self,
        db: Session,
        contact_id: str,
        channel: str
    ) -> str:
        """
        Get or create conversation ID for a contact + channel combination
        
        Args:
            db: Database session
            contact_id: Contact ID
            channel: Channel name
            
        Returns:
            Conversation ID string
        """
        # Use format: contact_id:channel
        conversation_id = f"{contact_id}:{channel}"
        return conversation_id
    
    def store_inbound_message(
        self,
        db: Session,
        normalized_data: Dict[str, Any],
        contact_id: Optional[str] = None
    ) -> Message:
        """
        Store inbound message in database
        
        Args:
            db: Database session
            normalized_data: Normalized message data
            contact_id: Optional contact ID (if already resolved)
            
        Returns:
            Created Message instance
        """
        # Resolve contact if not provided
        if not contact_id:
            contact, _, _ = self.resolve_contact(
                db,
                normalized_data["from_address"],
                normalized_data["channel"]
            )
            contact_id = contact.id if contact else None
        
        # Get conversation ID
        conversation_id = None
        if contact_id:
            conversation_id = self.get_or_create_conversation_id(
                db,
                contact_id,
                normalized_data["channel"]
            )
        
        # Check for duplicate (by Twilio MessageSid)
        if normalized_data.get("twilio_message_sid"):
            existing = db.query(Message).filter(
                Message.twilio_message_sid == normalized_data["twilio_message_sid"]
            ).first()
            if existing:
                logger.warning(
                    "duplicate_message_ignored",
                    message_sid=normalized_data["twilio_message_sid"]
                )
                return existing
        
        # Check if message is from Godfather
        from_actor = Actor(
            kind="external",  # Will be determined by is_godfather check
            phone_number=normalized_data["from_address"]
        )
        is_from_godfather = is_godfather(from_actor)
        
        # Create message
        message = Message(
            contact_id=contact_id,
            channel=normalized_data["channel"],
            direction="inbound",
            timestamp=normalized_data["timestamp"],
            raw_payload=_json_safe(normalized_data),
            text_content=normalized_data.get("text_content"),
            media_urls=normalized_data.get("media_urls"),
            conversation_id=conversation_id,
            twilio_message_sid=normalized_data.get("twilio_message_sid"),
            status="received",
            is_read=is_from_godfather  # Godfather messages are auto-read
        )
        
        db.add(message)
        try:
            db.commit()
            db.refresh(message)
        except Exception as e:
            db.rollback()
            logger.error("store_inbound_message_commit_failed", error=str(e))
            raise
        
        logger.info(
            "inbound_message_stored",
            message_id=message.id,
            contact_id=contact_id,
            channel=normalized_data["channel"],
            is_from_godfather=is_from_godfather
        )
        
        return message
    
    def store_outbound_message(
        self,
        db: Session,
        contact_id: str,
        channel: str,
        text_content: str,
        media_urls: Optional[List[str]] = None,
        twilio_message_sid: Optional[str] = None,
        status: str = "queued",
        draft_id: Optional[str] = None
    ) -> Tuple[Message, OutboundApproval]:
        """
        Store outbound message in database
        
        Args:
            db: Database session
            contact_id: Contact ID
            channel: Channel name
            text_content: Message text
            media_urls: Optional media URLs
            twilio_message_sid: Twilio message SID if already sent
            status: Message status
            draft_id: Optional draft/suggestion ID
            
        Returns:
            (message, approval) tuple
        """
        # Get conversation ID
        conversation_id = self.get_or_create_conversation_id(db, contact_id, channel)
        
        # Create message
        message = Message(
            contact_id=contact_id,
            channel=channel,
            direction="outbound",
            timestamp=datetime.utcnow(),
            text_content=text_content,
            media_urls=media_urls or [],
            conversation_id=conversation_id,
            twilio_message_sid=twilio_message_sid,
            status=status
        )
        
        db.add(message)
        try:
            db.commit()
            db.refresh(message)
        except Exception as e:
            db.rollback()
            logger.error("store_outbound_message_commit_failed", error=str(e))
            raise
        
        # Create approval record
        approval = OutboundApproval(
            message_id=message.id,
            draft_id=draft_id,
            status="pending" if not twilio_message_sid else "sent",
            approved_at=datetime.utcnow() if twilio_message_sid else None,
            sent_at=datetime.utcnow() if twilio_message_sid else None
        )
        
        db.add(approval)
        try:
            db.commit()
            db.refresh(approval)
        except Exception as e:
            db.rollback()
            logger.error("store_outbound_approval_commit_failed", error=str(e))
            raise
        
        logger.info(
            "outbound_message_stored",
            message_id=message.id,
            contact_id=contact_id,
            channel=channel
        )
        
        return (message, approval)
    
    def create_draft_message(
        self,
        db: Session,
        contact_id: str,
        channel: str,
        text_content: str,
        media_urls: Optional[List[str]] = None,
        draft_id: Optional[str] = None
    ) -> Tuple[Message, OutboundApproval]:
        """
        Create a draft message (stored but not sent, requires approval)
        
        Args:
            db: Database session
            contact_id: Contact ID
            channel: Channel name ("sms", "mms", "whatsapp")
            text_content: Message text
            media_urls: Optional media URLs for MMS
            draft_id: Optional draft/suggestion ID
            
        Returns:
            (message, approval) tuple with status "pending"
        """
        # Verify contact exists
        contact = db.query(Contact).filter(Contact.id == contact_id).first()
        if not contact:
            raise ValueError(f"Contact {contact_id} not found")
        
        # Store message as draft (not sent yet)
        message, approval = self.store_outbound_message(
            db=db,
            contact_id=contact_id,
            channel=channel,
            text_content=text_content,
            media_urls=media_urls,
            twilio_message_sid=None,  # Not sent yet
            status="pending",
            draft_id=draft_id
        )
        
        return (message, approval)
    
    def send_approved_message(
        self,
        db: Session,
        message_id: str
    ) -> Tuple[Message, OutboundApproval]:
        """
        Send an approved message via Twilio
        
        Args:
            db: Database session
            message_id: Message ID to send
            
        Returns:
            (message, approval) tuple
        """
        # Get message and approval
        message = db.query(Message).filter(Message.id == message_id).first()
        if not message:
            raise ValueError(f"Message {message_id} not found")
        
        approval = db.query(OutboundApproval).filter(
            OutboundApproval.message_id == message_id
        ).first()
        if not approval:
            raise ValueError(f"Approval not found for message {message_id}")
        
        if approval.status != "pending":
            raise ValueError(f"Message approval is {approval.status}, cannot send")
        
        # Get contact
        contact = db.query(Contact).filter(Contact.id == message.contact_id).first()
        if not contact:
            raise ValueError(f"Contact {message.contact_id} not found")
        
        # Get channel identity to find address
        channel_identity = db.query(ChannelIdentity).filter(
            and_(
                ChannelIdentity.contact_id == message.contact_id,
                ChannelIdentity.channel == message.channel
            )
        ).first()
        
        if not channel_identity:
            # Try to use phone_number for SMS/MMS
            if message.channel in ["sms", "mms"] and contact.phone_number:
                to_address = contact.phone_number
            else:
                raise ValueError(f"No {message.channel} address found for contact {message.contact_id}")
        else:
            to_address = channel_identity.address
        
        # Format from_number based on channel
        from_number = settings.TWILIO_PHONE_NUMBER
        if message.channel == "whatsapp":
            from_number = f"whatsapp:{from_number}"
        
            # Send via Twilio
        try:
            result = self.twilio.send_message(
                to_number=to_address,
                body=message.text_content,
                from_number=from_number,
                media_urls=message.media_urls or []
            )
            
            # Update message with Twilio SID and status
            message.twilio_message_sid = result["message_sid"]
            message.status = result["status"]
            
            # Update approval
            approval.status = "sent"
            approval.approved_at = datetime.utcnow()
            approval.sent_at = datetime.utcnow()
            
            # Log cost event for Twilio message
            try:
                # Determine service type based on channel
                service_type = message.channel  # "sms", "mms", or "whatsapp"
                
                # Log cost event
                self.cost_logger.log_cost_event(
                    db=db,
                    provider="twilio",
                    service=service_type,
                    metric_type="messages",
                    units=1.0,
                    event_id=result["message_sid"],  # Use Twilio MessageSid for idempotency
                    metadata={
                        "channel": message.channel,
                        "to": to_address,
                        "from": from_number,
                        "has_media": len(message.media_urls or []) > 0,
                        "message_id": message.id
                    }
                )
            except Exception as e:
                # Don't fail message send if cost logging fails
                logger.error("cost_logging_failed", error=str(e), message_id=message.id)
            
            try:
                db.commit()
                db.refresh(message)
                db.refresh(approval)
            except Exception as e:
                db.rollback()
                logger.error("send_approved_message_commit_failed", error=str(e))
                raise
            
            logger.info(
                "message_sent",
                message_id=message.id,
                message_sid=result["message_sid"]
            )
            
            return (message, approval)
            
        except Exception as e:
            logger.error("send_approved_message_failed", error=str(e), message_id=message_id)
            # Update status to failed
            message.status = "failed"
            approval.status = "failed"
            try:
                db.commit()
            except Exception:
                db.rollback()
            raise
    
    def get_conversation(
        self,
        db: Session,
        contact_id: str,
        channel: str,
        limit: int = 50
    ) -> List[Message]:
        """
        Get conversation messages for a contact + channel
        
        Args:
            db: Database session
            contact_id: Contact ID
            channel: Channel name
            limit: Maximum number of messages
            
        Returns:
            List of messages ordered by timestamp
        """
        conversation_id = self.get_or_create_conversation_id(db, contact_id, channel)
        
        messages = db.query(Message).filter(
            Message.conversation_id == conversation_id
        ).order_by(desc(Message.timestamp)).limit(limit).all()
        
        # Reverse to get chronological order
        return list(reversed(messages))
    
    def get_all_conversations(
        self,
        db: Session,
        limit: int = 20
    ) -> List[Dict[str, Any]]:
        """
        Get all conversations (one per contact + channel)
        
        Args:
            db: Database session
            limit: Maximum number of conversations
            
        Returns:
            List of conversation dictionaries with latest message info
        """
        # Get distinct conversation IDs with latest message
        from sqlalchemy import func
        
        subquery = db.query(
            Message.conversation_id,
            func.max(Message.timestamp).label("latest_timestamp")
        ).filter(
            Message.conversation_id.isnot(None)
        ).group_by(Message.conversation_id).subquery()
        
        conversations = db.query(Message).join(
            subquery,
            and_(
                Message.conversation_id == subquery.c.conversation_id,
                Message.timestamp == subquery.c.latest_timestamp
            )
        ).order_by(desc(Message.timestamp)).limit(limit).all()
        
        result = []
        for msg in conversations:
            contact = db.query(Contact).filter(Contact.id == msg.contact_id).first() if msg.contact_id else None
            
            result.append({
                "conversation_id": msg.conversation_id,
                "contact_id": msg.contact_id,
                "contact_name": contact.name if contact else "Unknown",
                "channel": msg.channel,
                "latest_message": {
                    "id": msg.id,
                    "text_content": msg.text_content,
                    "timestamp": msg.timestamp.isoformat(),
                    "direction": msg.direction
                },
                "unread_count": self._get_unread_count(db, msg.conversation_id)
            })
        
        return result
    
    def _get_unread_count(
        self,
        db: Session,
        conversation_id: str
    ) -> int:
        """
        Get unread message count for a conversation
        
        Args:
            db: Database session
            conversation_id: Conversation ID
            
        Returns:
            Number of unread messages
        """
        unread_count = db.query(Message).filter(
            Message.conversation_id == conversation_id,
            Message.direction == "inbound",
            Message.is_read == False
        ).count()
        
        return unread_count
    
    def mark_conversation_as_read(
        self,
        db: Session,
        conversation_id: str
    ) -> int:
        """
        Mark all messages in a conversation as read
        
        Args:
            db: Database session
            conversation_id: Conversation ID
            
        Returns:
            Number of messages marked as read
        """
        updated = db.query(Message).filter(
            Message.conversation_id == conversation_id,
            Message.direction == "inbound",
            Message.is_read == False
        ).update({"is_read": True})
        
        try:
            db.commit()
        except Exception as e:
            db.rollback()
            logger.error("mark_conversation_read_failed", error=str(e))
            raise
        
        logger.info("conversation_marked_read", conversation_id=conversation_id, count=updated)
        return updated
    
    def should_trigger_summary(
        self,
        db: Session,
        conversation_id: str,
        idle_minutes: int = 5,
        message_threshold: int = 5
    ) -> bool:
        """
        Determine if conversation should be summarized
        
        Args:
            db: Database session
            conversation_id: Conversation ID
            idle_minutes: Minutes of inactivity before summarizing
            message_threshold: Minimum messages before summarizing
            
        Returns:
            True if should summarize
        """
        # Get recent messages
        recent_messages = db.query(Message).filter(
            Message.conversation_id == conversation_id
        ).order_by(desc(Message.timestamp)).limit(message_threshold).all()
        
        if len(recent_messages) < message_threshold:
            return False
        
        # Check if idle
        latest_message = recent_messages[0]
        time_since_last = datetime.utcnow() - latest_message.timestamp
        
        if time_since_last.total_seconds() < idle_minutes * 60:
            return False
        
        # Check if already summarized (by checking if latest interaction has summary)
        if recent_messages[0].contact_id:
            latest_interaction = db.query(Interaction).filter(
                Interaction.contact_id == recent_messages[0].contact_id
            ).order_by(desc(Interaction.created_at)).first()
            
            if latest_interaction:
                # Check if summary exists and is recent
                summary = db.query(MemorySummary).filter(
                    MemorySummary.interaction_id == latest_interaction.id
                ).first()
                
                if summary and summary.created_at > latest_message.timestamp:
                    return False
        
        return True
    
    def process_conversation_for_memory(
        self,
        db: Session,
        conversation_id: str
    ) -> Optional[Interaction]:
        """
        Process conversation and create interaction for memory service
        
        Args:
            db: Database session
            conversation_id: Conversation ID
            
        Returns:
            Created Interaction instance or None
        """
        # Get all messages in conversation
        messages = db.query(Message).filter(
            Message.conversation_id == conversation_id
        ).order_by(Message.timestamp).all()
        
        if not messages:
            return None
        
        # Get contact
        contact_id = messages[0].contact_id
        if not contact_id:
            return None
        
        # Build conversation text
        conversation_parts = []
        for msg in messages:
            direction_label = "You" if msg.direction == "outbound" else "Them"
            conversation_parts.append(f"{direction_label}: {msg.text_content or '[Media]'}")
        
        conversation_text = "\n".join(conversation_parts)
        
        # Create interaction
        interaction = self.memory_service.store_interaction(
            db=db,
            contact_id=contact_id,
            channel=messages[0].channel,
            raw_content=conversation_text,
            metadata={
                "conversation_id": conversation_id,
                "message_count": len(messages),
                "message_ids": [msg.id for msg in messages]
            }
        )
        
        # Generate summary
        try:
            contact = db.query(Contact).filter(Contact.id == contact_id).first()
            self.memory_service.generate_summary(
                db=db,
                interaction_id=interaction.id,
                contact_name=contact.name if contact else None
            )
        except Exception as e:
            logger.error("summary_generation_failed", error=str(e), conversation_id=conversation_id)
        
        return interaction

