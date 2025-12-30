"""Integration tests for Twilio messaging webhooks"""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock
from datetime import datetime
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from src.main import app
from src.database.database import Base, get_db
from src.database.models import Contact, Message


@pytest.fixture
def client(db):
    """Create test client"""
    def _override_get_db():
        yield db

    app.dependency_overrides[get_db] = _override_get_db
    try:
        with TestClient(app) as c:
            yield c
    finally:
        app.dependency_overrides.pop(get_db, None)


@pytest.fixture
def db():
    """Create test database"""
    engine = create_engine("sqlite:///./test_messaging_webhooks.db", connect_args={"check_same_thread": False})
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    yield db
    db.rollback()
    db.close()
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def test_contact(db):
    """Create test contact"""
    contact = Contact(
        name="Test Contact",
        phone_number="+15551234567",
        email="test@example.com"
    )
    db.add(contact)
    db.commit()
    db.refresh(contact)
    return contact


class TestTwilioWebhooks:
    """Integration tests for Twilio webhook endpoints"""
    
    @patch('src.api.webhooks.twilio_webhook._validate_twilio_request')
    def test_inbound_message_webhook(self, mock_validate, client, db, test_contact):
        """Test inbound message webhook"""
        mock_validate.return_value = True
        
        form_data = {
            "From": "+15551234567",
            "To": "+15559876543",
            "Body": "Test inbound message",
            "MessageSid": "SM123456789",
            "NumMedia": "0"
        }
        
        response = client.post(
            "/webhooks/twilio/inbound-message",
            data=form_data
        )
        
        assert response.status_code == 200
        
        # Verify message was stored
        message = db.query(Message).filter(
            Message.twilio_message_sid == "SM123456789"
        ).first()
        
        assert message is not None
        assert message.direction == "inbound"
        assert message.text_content == "Test inbound message"
        assert message.is_read == False
    
    @patch('src.api.webhooks.twilio_webhook._validate_twilio_request')
    def test_inbound_message_invalid_signature(self, mock_validate, client):
        """Test webhook rejects invalid signature"""
        mock_validate.return_value = False
        
        form_data = {
            "From": "+15551234567",
            "To": "+15559876543",
            "Body": "Test message",
            "MessageSid": "SM123456789"
        }
        
        response = client.post(
            "/webhooks/twilio/inbound-message",
            data=form_data
        )
        
        assert response.status_code == 403
    
    @patch('src.api.webhooks.twilio_webhook._validate_twilio_request')
    def test_message_status_webhook(self, mock_validate, client, db, test_contact):
        """Test message status callback"""
        mock_validate.return_value = True
        
        # Create a message first
        from src.messaging.messaging_service import MessagingService
        messaging_service = MessagingService()
        
        normalized = {
            "channel": "sms",
            "from_address": "+15551234567",
            "to_address": "+15559876543",
            "text_content": "Test message",
            "twilio_message_sid": "SM123456789",
            "timestamp": datetime.utcnow(),
            "media_urls": []
        }
        
        message = messaging_service.store_inbound_message(
            db=db,
            normalized_data=normalized,
            contact_id=test_contact.id
        )
        
        # Update message with outbound status
        message.direction = "outbound"
        message.status = "queued"
        db.commit()
        
        # Send status callback
        form_data = {
            "MessageSid": "SM123456789",
            "MessageStatus": "delivered",
            "ErrorCode": None
        }
        
        response = client.post(
            "/webhooks/twilio/message-status",
            data=form_data
        )
        
        assert response.status_code == 200
        
        # Verify status was updated
        db.refresh(message)
        assert message.status == "delivered"
    
    @patch('src.api.webhooks.twilio_webhook._validate_twilio_request')
    def test_inbound_message_whatsapp(self, mock_validate, client, db):
        """Test WhatsApp inbound message"""
        mock_validate.return_value = True
        
        form_data = {
            "From": "whatsapp:+15551234567",
            "To": "whatsapp:+15559876543",
            "Body": "WhatsApp test",
            "MessageSid": "WA123456789",
            "NumMedia": "0"
        }
        
        response = client.post(
            "/webhooks/twilio/inbound-message",
            data=form_data
        )
        
        assert response.status_code == 200
        
        # Verify message was stored with correct channel
        message = db.query(Message).filter(
            Message.twilio_message_sid == "WA123456789"
        ).first()
        
        assert message is not None
        assert message.channel == "whatsapp"
    
    @patch('src.api.webhooks.twilio_webhook._validate_twilio_request')
    def test_inbound_message_mms(self, mock_validate, client, db):
        """Test MMS inbound message with media"""
        mock_validate.return_value = True
        
        form_data = {
            "From": "+15551234567",
            "To": "+15559876543",
            "Body": "MMS test",
            "MessageSid": "MM123456789",
            "NumMedia": "2",
            "MediaUrl0": "https://example.com/image1.jpg",
            "MediaUrl1": "https://example.com/image2.jpg"
        }
        
        response = client.post(
            "/webhooks/twilio/inbound-message",
            data=form_data
        )
        
        assert response.status_code == 200
        
        # Verify message was stored with media
        message = db.query(Message).filter(
            Message.twilio_message_sid == "MM123456789"
        ).first()
        
        assert message is not None
        assert message.channel == "mms"
        assert len(message.media_urls) == 2
        assert "https://example.com/image1.jpg" in message.media_urls

