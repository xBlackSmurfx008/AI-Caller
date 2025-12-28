"""Tests for database models"""

import pytest
from sqlalchemy.orm import Session
from datetime import datetime
import uuid

from src.database.models import (
    User, Call, CallInteraction, CallNote, BusinessConfig,
    KnowledgeEntry, QAScore, Escalation, Notification, HumanAgent,
    CallStatus, CallDirection, EscalationStatus
)


def test_user_model(db: Session):
    """Test User model creation and relationships"""
    user = User(
        id=str(uuid.uuid4()),
        email="test@example.com",
        name="Test User",
        hashed_password="hashed_password_here",
        is_active=True,
        is_superuser=False,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    
    assert user.email == "test@example.com"
    assert user.name == "Test User"
    assert user.is_active == True
    assert user.is_superuser == False
    assert user.created_at is not None


def test_business_config_model(db: Session):
    """Test BusinessConfig model"""
    user = User(
        id=str(uuid.uuid4()),
        email="owner@example.com",
        name="Owner",
        hashed_password="hash",
        is_active=True,
    )
    db.add(user)
    db.commit()
    
    config = BusinessConfig(
        id=str(uuid.uuid4()),
        name="Test Business",
        type="customer_support",
        config_data={"ai": {"model": "gpt-4o"}},
        created_by_user_id=user.id,
        is_active=True,
    )
    db.add(config)
    db.commit()
    db.refresh(config)
    
    assert config.name == "Test Business"
    assert config.type == "customer_support"
    assert config.created_by_user_id == user.id
    assert config.created_by_user == user  # Check relationship


def test_call_model(db: Session):
    """Test Call model and relationships"""
    config = BusinessConfig(
        id=str(uuid.uuid4()),
        name="Test Business",
        type="customer_support",
        config_data={},
        is_active=True,
    )
    db.add(config)
    db.commit()
    
    call = Call(
        id=str(uuid.uuid4()),
        twilio_call_sid="CA123456",
        direction=CallDirection.INBOUND,
        status=CallStatus.IN_PROGRESS,
        from_number="+1234567890",
        to_number="+0987654321",
        business_id=config.id,
        started_at=datetime.utcnow(),
    )
    db.add(call)
    db.commit()
    db.refresh(call)
    
    assert call.direction == CallDirection.INBOUND
    assert call.status == CallStatus.IN_PROGRESS
    assert call.business_id == config.id
    assert call.interactions == []  # Empty relationship initially


def test_call_interaction_model(db: Session):
    """Test CallInteraction model"""
    call = Call(
        id=str(uuid.uuid4()),
        twilio_call_sid="CA123",
        direction=CallDirection.INBOUND,
        status=CallStatus.IN_PROGRESS,
        from_number="+1234567890",
        to_number="+0987654321",
        started_at=datetime.utcnow(),
    )
    db.add(call)
    db.commit()
    
    interaction = CallInteraction(
        call_id=call.id,
        speaker="customer",
        text="Hello, I need help",
        timestamp=datetime.utcnow(),
    )
    db.add(interaction)
    db.commit()
    db.refresh(interaction)
    
    assert interaction.call_id == call.id
    assert interaction.speaker == "customer"
    assert interaction.text == "Hello, I need help"
    assert interaction.call == call  # Check relationship


def test_call_note_model(db: Session):
    """Test CallNote model"""
    user = User(
        id=str(uuid.uuid4()),
        email="user@example.com",
        name="User",
        hashed_password="hash",
        is_active=True,
    )
    db.add(user)
    
    call = Call(
        id=str(uuid.uuid4()),
        twilio_call_sid="CA123",
        direction=CallDirection.INBOUND,
        status=CallStatus.COMPLETED,
        from_number="+1234567890",
        to_number="+0987654321",
        started_at=datetime.utcnow(),
    )
    db.add(call)
    db.commit()
    
    note = CallNote(
        call_id=call.id,
        created_by_user_id=user.id,
        note="Important note about this call",
        tags=["follow-up", "urgent"],
        category="Issue",
    )
    db.add(note)
    db.commit()
    db.refresh(note)
    
    assert note.call_id == call.id
    assert note.created_by_user_id == user.id
    assert note.note == "Important note about this call"
    assert note.tags == ["follow-up", "urgent"]
    assert note.category == "Issue"


def test_qa_score_model(db: Session):
    """Test QAScore model"""
    call = Call(
        id=str(uuid.uuid4()),
        twilio_call_sid="CA123",
        direction=CallDirection.INBOUND,
        status=CallStatus.COMPLETED,
        from_number="+1234567890",
        to_number="+0987654321",
        started_at=datetime.utcnow(),
        ended_at=datetime.utcnow(),
    )
    db.add(call)
    db.commit()
    
    qa_score = QAScore(
        call_id=call.id,
        overall_score=0.85,
        sentiment_score=0.8,
        compliance_score=0.9,
        accuracy_score=0.85,
        professionalism_score=0.8,
        sentiment_label="positive",
        compliance_issues=[],
        flagged_issues=[],
        reviewed_by="auto",
    )
    db.add(qa_score)
    db.commit()
    db.refresh(qa_score)
    
    assert qa_score.call_id == call.id
    assert qa_score.overall_score == 0.85
    assert qa_score.sentiment_label == "positive"
    assert qa_score.call == call  # Check relationship


def test_escalation_model(db: Session):
    """Test Escalation model"""
    call = Call(
        id=str(uuid.uuid4()),
        twilio_call_sid="CA123",
        direction=CallDirection.INBOUND,
        status=CallStatus.ESCALATED,
        from_number="+1234567890",
        to_number="+0987654321",
        started_at=datetime.utcnow(),
    )
    db.add(call)
    db.commit()
    
    escalation = Escalation(
        call_id=call.id,
        status=EscalationStatus.PENDING,
        trigger_type="sentiment",
        trigger_details={"threshold": -0.5},
        assigned_agent_id="agent-123",
        agent_name="John Doe",
        conversation_summary="Customer frustrated with service",
        context_data={"sentiment_score": -0.6},
    )
    db.add(escalation)
    db.commit()
    db.refresh(escalation)
    
    assert escalation.call_id == call.id
    assert escalation.status == EscalationStatus.PENDING
    assert escalation.trigger_type == "sentiment"
    assert escalation.assigned_agent_id == "agent-123"
    assert escalation.call == call  # Check relationship


def test_notification_model(db: Session):
    """Test Notification model"""
    user = User(
        id=str(uuid.uuid4()),
        email="user@example.com",
        name="User",
        hashed_password="hash",
        is_active=True,
    )
    db.add(user)
    db.commit()
    
    notification = Notification(
        id=str(uuid.uuid4()),
        user_id=user.id,
        type="call_escalated",
        title="Call Escalated",
        message="Call CA123 has been escalated",
        read=False,
        metadata={"call_id": "call-123"},
        action_url="/calls/call-123",
    )
    db.add(notification)
    db.commit()
    db.refresh(notification)
    
    assert notification.user_id == user.id
    assert notification.type == "call_escalated"
    assert notification.read == False
    assert notification.user == user  # Check relationship


def test_knowledge_entry_model(db: Session):
    """Test KnowledgeEntry model"""
    config = BusinessConfig(
        id=str(uuid.uuid4()),
        name="Test Business",
        type="customer_support",
        config_data={},
        is_active=True,
    )
    db.add(config)
    db.commit()
    
    entry = KnowledgeEntry(
        business_id=config.id,
        title="FAQ Entry",
        content="This is a knowledge base entry",
        source="manual",
        source_type="text",
        vector_id="vec-123",
    )
    db.add(entry)
    db.commit()
    db.refresh(entry)
    
    assert entry.business_id == config.id
    assert entry.title == "FAQ Entry"
    assert entry.content == "This is a knowledge base entry"
    assert entry.business_config == config  # Check relationship


def test_human_agent_model(db: Session):
    """Test HumanAgent model"""
    agent = HumanAgent(
        id=str(uuid.uuid4()),
        name="John Agent",
        email="john@example.com",
        phone_number="+1234567890",
        extension="123",
        is_available=True,
        is_active=True,
        skills=["Customer Service", "Technical Support"],
        departments=["Support"],
        total_calls_handled=50,
        average_rating=4.5,
    )
    db.add(agent)
    db.commit()
    db.refresh(agent)
    
    assert agent.name == "John Agent"
    assert agent.email == "john@example.com"
    assert agent.is_available == True
    assert agent.skills == ["Customer Service", "Technical Support"]
    assert agent.total_calls_handled == 50
    assert agent.average_rating == 4.5


def test_model_relationships(db: Session):
    """Test model relationships work correctly"""
    user = User(
        id=str(uuid.uuid4()),
        email="user@example.com",
        name="User",
        hashed_password="hash",
        is_active=True,
    )
    db.add(user)
    
    config = BusinessConfig(
        id=str(uuid.uuid4()),
        name="Business",
        type="customer_support",
        config_data={},
        created_by_user_id=user.id,
        is_active=True,
    )
    db.add(config)
    
    call = Call(
        id=str(uuid.uuid4()),
        twilio_call_sid="CA123",
        direction=CallDirection.INBOUND,
        status=CallStatus.COMPLETED,
        from_number="+1234567890",
        to_number="+0987654321",
        business_id=config.id,
        started_at=datetime.utcnow(),
        ended_at=datetime.utcnow(),
    )
    db.add(call)
    
    note = CallNote(
        call_id=call.id,
        created_by_user_id=user.id,
        note="Test note",
    )
    db.add(note)
    
    db.commit()
    
    # Verify relationships
    assert call.business_config == config
    assert config.created_by_user == user
    assert note.call == call
    assert note.created_by_user == user
    assert call in config.calls
    assert note in call.notes

