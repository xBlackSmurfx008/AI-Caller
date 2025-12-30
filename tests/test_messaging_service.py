"""Unit tests for messaging service"""

import pytest
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from unittest.mock import Mock, patch, MagicMock

from src.messaging.messaging_service import MessagingService
from src.database.models import Contact, Message, ChannelIdentity, OutboundApproval
from src.database.database import Base


@pytest.fixture
def db():
    """Create a test database session"""
    engine = create_engine("sqlite:///./test_messaging_service.db", connect_args={"check_same_thread": False})
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    yield db
    db.rollback()
    db.close()
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def messaging_service():
    """Create messaging service instance"""
    return MessagingService()


@pytest.fixture
def test_contact(db):
    """Create a test contact"""
    contact = Contact(
        name="Test Contact",
        phone_number="+15551234567",
        email="test@example.com"
    )
    db.add(contact)
    db.commit()
    db.refresh(contact)
    return contact


class TestMessagingService:
    """Test suite for MessagingService"""
    
    def test_normalize_twilio_payload_sms(self, messaging_service):
        """Test normalizing SMS payload"""
        payload = {
            "From": "+15551234567",
            "To": "+15559876543",
            "Body": "Test message",
            "MessageSid": "SM123456",
            "NumMedia": "0"
        }
        
        normalized = messaging_service.normalize_twilio_payload(payload)
        
        assert normalized["channel"] == "sms"
        assert normalized["from_address"] == "+15551234567"
        assert normalized["text_content"] == "Test message"
        assert normalized["twilio_message_sid"] == "SM123456"
        assert normalized["media_urls"] == []
    
    def test_normalize_twilio_payload_whatsapp(self, messaging_service):
        """Test normalizing WhatsApp payload"""
        payload = {
            "From": "whatsapp:+15551234567",
            "To": "whatsapp:+15559876543",
            "Body": "WhatsApp message",
            "MessageSid": "WA123456",
            "NumMedia": "0"
        }
        
        normalized = messaging_service.normalize_twilio_payload(payload)
        
        assert normalized["channel"] == "whatsapp"
        assert normalized["from_address"] == "+15551234567"  # Prefix removed
        assert normalized["text_content"] == "WhatsApp message"
    
    def test_normalize_twilio_payload_mms(self, messaging_service):
        """Test normalizing MMS payload"""
        payload = {
            "From": "+15551234567",
            "To": "+15559876543",
            "Body": "MMS message",
            "MessageSid": "MM123456",
            "NumMedia": "2",
            "MediaUrl0": "https://example.com/image1.jpg",
            "MediaUrl1": "https://example.com/image2.jpg"
        }
        
        normalized = messaging_service.normalize_twilio_payload(payload)
        
        assert normalized["channel"] == "mms"
        assert len(normalized["media_urls"]) == 2
        assert "https://example.com/image1.jpg" in normalized["media_urls"]
    
    def test_resolve_contact_existing(self, messaging_service, db, test_contact):
        """Test resolving existing contact"""
        # Create channel identity
        channel_identity = ChannelIdentity(
            contact_id=test_contact.id,
            channel="sms",
            address="+15551234567",
            verified=True
        )
        db.add(channel_identity)
        db.commit()
        
        contact, identity, is_provisional = messaging_service.resolve_contact(
            db=db,
            address="+15551234567",
            channel="sms"
        )
        
        assert contact.id == test_contact.id
        assert identity is not None
        assert is_provisional == False
    
    def test_resolve_contact_provisional(self, messaging_service, db):
        """Test creating provisional contact"""
        contact, identity, is_provisional = messaging_service.resolve_contact(
            db=db,
            address="+15559999999",
            channel="sms"
        )
        
        assert contact is not None
        assert "Unknown" in contact.name
        assert identity is not None
        assert is_provisional == True
        assert identity.verified == False
    
    def test_get_or_create_conversation_id(self, messaging_service, db, test_contact):
        """Test conversation ID generation"""
        conversation_id = messaging_service.get_or_create_conversation_id(
            db=db,
            contact_id=test_contact.id,
            channel="sms"
        )
        
        assert conversation_id == f"{test_contact.id}:sms"
    
    def test_store_inbound_message(self, messaging_service, db, test_contact):
        """Test storing inbound message"""
        normalized = {
            "channel": "sms",
            "from_address": "+15551234567",
            "to_address": "+15559876543",
            "text_content": "Test message",
            "twilio_message_sid": "SM123456",
            "timestamp": datetime.utcnow(),
            "media_urls": []
        }
        
        message = messaging_service.store_inbound_message(
            db=db,
            normalized_data=normalized,
            contact_id=test_contact.id
        )
        
        assert message.id is not None
        assert message.direction == "inbound"
        assert message.channel == "sms"
        assert message.text_content == "Test message"
        assert message.is_read == False  # New messages are unread
    
    def test_store_inbound_message_deduplication(self, messaging_service, db, test_contact):
        """Test message deduplication by MessageSid"""
        normalized = {
            "channel": "sms",
            "from_address": "+15551234567",
            "to_address": "+15559876543",
            "text_content": "Test message",
            "twilio_message_sid": "SM123456",
            "timestamp": datetime.utcnow(),
            "media_urls": []
        }
        
        # Store first message
        message1 = messaging_service.store_inbound_message(
            db=db,
            normalized_data=normalized,
            contact_id=test_contact.id
        )
        
        # Try to store duplicate
        message2 = messaging_service.store_inbound_message(
            db=db,
            normalized_data=normalized,
            contact_id=test_contact.id
        )
        
        # Should return same message
        assert message1.id == message2.id
    
    def test_get_unread_count(self, messaging_service, db, test_contact):
        """Test unread message counting"""
        conversation_id = messaging_service.get_or_create_conversation_id(
            db=db,
            contact_id=test_contact.id,
            channel="sms"
        )
        
        # Create unread messages
        for i in range(3):
            message = Message(
                contact_id=test_contact.id,
                channel="sms",
                direction="inbound",
                timestamp=datetime.utcnow(),
                text_content=f"Message {i}",
                conversation_id=conversation_id,
                is_read=False
            )
            db.add(message)
        
        # Create read message
        read_message = Message(
            contact_id=test_contact.id,
            channel="sms",
            direction="inbound",
            timestamp=datetime.utcnow(),
            text_content="Read message",
            conversation_id=conversation_id,
            is_read=True
        )
        db.add(read_message)
        db.commit()
        
        unread_count = messaging_service._get_unread_count(db, conversation_id)
        assert unread_count == 3
    
    def test_mark_conversation_as_read(self, messaging_service, db, test_contact):
        """Test marking conversation as read"""
        conversation_id = messaging_service.get_or_create_conversation_id(
            db=db,
            contact_id=test_contact.id,
            channel="sms"
        )
        
        # Create unread messages
        for i in range(2):
            message = Message(
                contact_id=test_contact.id,
                channel="sms",
                direction="inbound",
                timestamp=datetime.utcnow(),
                text_content=f"Message {i}",
                conversation_id=conversation_id,
                is_read=False
            )
            db.add(message)
        db.commit()
        
        # Mark as read
        count = messaging_service.mark_conversation_as_read(db, conversation_id)
        assert count == 2
        
        # Verify all are read
        unread_count = messaging_service._get_unread_count(db, conversation_id)
        assert unread_count == 0
    
    def test_should_trigger_summary(self, messaging_service, db, test_contact):
        """Test conversation summary trigger logic"""
        conversation_id = messaging_service.get_or_create_conversation_id(
            db=db,
            contact_id=test_contact.id,
            channel="sms"
        )
        
        # Create messages below threshold
        for i in range(2):
            message = Message(
                contact_id=test_contact.id,
                channel="sms",
                direction="inbound",
                timestamp=datetime.utcnow() - timedelta(minutes=10-i),
                text_content=f"Message {i}",
                conversation_id=conversation_id,
                is_read=False
            )
            db.add(message)
        db.commit()
        
        # Should not trigger (below threshold)
        should_trigger = messaging_service.should_trigger_summary(
            db=db,
            conversation_id=conversation_id,
            message_threshold=5
        )
        assert should_trigger == False
        
        # Add more messages to reach threshold
        for i in range(3, 6):
            message = Message(
                contact_id=test_contact.id,
                channel="sms",
                direction="inbound",
                timestamp=datetime.utcnow() - timedelta(minutes=10-i),
                text_content=f"Message {i}",
                conversation_id=conversation_id,
                is_read=False
            )
            db.add(message)
        db.commit()
        
        # Should trigger (meets threshold and idle)
        should_trigger = messaging_service.should_trigger_summary(
            db=db,
            conversation_id=conversation_id,
            idle_minutes=5,
            message_threshold=5
        )
        assert should_trigger == True

