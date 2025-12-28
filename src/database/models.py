"""SQLAlchemy database models"""

from datetime import datetime
from enum import Enum
from typing import Optional

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Enum as SQLEnum,
    Float,
    ForeignKey,
    Integer,
    JSON,
    String,
    Text,
    Index,
    UniqueConstraint,
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship

Base = declarative_base()


class CallStatus(str, Enum):
    """Call status enumeration"""
    INITIATED = "initiated"
    RINGING = "ringing"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    ESCALATED = "escalated"


class CallDirection(str, Enum):
    """Call direction enumeration"""
    INBOUND = "inbound"
    OUTBOUND = "outbound"


class EscalationStatus(str, Enum):
    """Escalation status enumeration"""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class Call(Base):
    """Call model"""
    __tablename__ = "calls"

    id = Column(String, primary_key=True)
    twilio_call_sid = Column(String, unique=True, index=True)
    direction = Column(SQLEnum(CallDirection), nullable=False)
    status = Column(SQLEnum(CallStatus), default=CallStatus.INITIATED, nullable=False)
    
    # Phone numbers
    from_number = Column(String, nullable=False)
    to_number = Column(String, nullable=False)
    
    # Business context
    business_id = Column(String, ForeignKey("business_configs.id"), nullable=True)
    template_id = Column(String, nullable=True)
    
    # Timestamps
    started_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    ended_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Metadata
    meta_data = Column("metadata", JSON, default=dict)
    
    # Relationships
    interactions = relationship("CallInteraction", back_populates="call", cascade="all, delete-orphan")
    qa_scores = relationship("QAScore", back_populates="call", cascade="all, delete-orphan")
    escalations = relationship("Escalation", back_populates="call", cascade="all, delete-orphan")
    notes = relationship("CallNote", back_populates="call", cascade="all, delete-orphan")
    business_config = relationship("BusinessConfig", back_populates="calls")

    __table_args__ = (
        Index("idx_calls_status", "status"),
        Index("idx_calls_business", "business_id"),
        Index("idx_calls_started_at", "started_at"),
        Index("idx_calls_business_status", "business_id", "status"),  # Composite index for filtering
        Index("idx_calls_started_at_status", "started_at", "status"),  # Composite index for date+status queries
    )


class CallInteraction(Base):
    """Call interaction/transcript model"""
    __tablename__ = "call_interactions"

    id = Column(Integer, primary_key=True, autoincrement=True)
    call_id = Column(String, ForeignKey("calls.id"), nullable=False, index=True)
    
    # Interaction data
    speaker = Column(String, nullable=False)  # "ai" or "customer"
    text = Column(Text, nullable=False)
    audio_url = Column(String, nullable=True)
    
    # Timestamps
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    # Metadata
    meta_data = Column("metadata", JSON, default=dict)
    
    # Relationships
    call = relationship("Call", back_populates="interactions")

    __table_args__ = (
        Index("idx_interactions_call_timestamp", "call_id", "timestamp"),
    )


class CallNote(Base):
    """Call note model"""
    __tablename__ = "call_notes"

    id = Column(Integer, primary_key=True, autoincrement=True)
    call_id = Column(String, ForeignKey("calls.id"), nullable=False, index=True)
    created_by_user_id = Column(String, ForeignKey("users.id"), nullable=True, index=True)
    
    # Note content
    note = Column(Text, nullable=False)
    tags = Column(JSON, default=list)
    category = Column(String, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Relationships
    call = relationship("Call", back_populates="notes")
    created_by_user = relationship("User", foreign_keys=[created_by_user_id])

    __table_args__ = (
        Index("idx_call_notes_call", "call_id"),
        Index("idx_call_notes_user", "created_by_user_id"),
    )


class BusinessConfig(Base):
    """Business configuration/template model"""
    __tablename__ = "business_configs"

    id = Column(String, primary_key=True)
    name = Column(String, nullable=False)
    type = Column(String, nullable=False)  # "customer_support", "sales", "appointments", etc.
    created_by_user_id = Column(String, ForeignKey("users.id"), nullable=True, index=True)
    
    # Configuration data
    config_data = Column(JSON, nullable=False)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    
    # Relationships
    calls = relationship("Call", back_populates="business_config")
    knowledge_entries = relationship("KnowledgeEntry", back_populates="business_config")
    created_by_user = relationship("User", back_populates="business_configs")
    phone_numbers = relationship("BusinessPhoneNumber", back_populates="business", cascade="all, delete-orphan")


class KnowledgeEntry(Base):
    """Knowledge base entry model"""
    __tablename__ = "knowledge_entries"

    id = Column(Integer, primary_key=True, autoincrement=True)
    business_id = Column(String, ForeignKey("business_configs.id"), nullable=True, index=True)
    
    # Document information
    title = Column(String, nullable=False)
    content = Column(Text, nullable=False)
    source = Column(String, nullable=True)  # URL, file path, etc.
    source_type = Column(String, nullable=True)  # "pdf", "docx", "txt", "url", etc.
    
    # Vector database reference
    vector_id = Column(String, nullable=True, index=True)
    
    # Documentation-specific fields
    vendor = Column(String, nullable=True, index=True)  # openai, twilio, ringcentral, hubspot, google
    doc_type = Column(String, nullable=True, index=True)  # api_reference, guide, tutorial, example, troubleshooting
    api_version = Column(String, nullable=True)  # API version for version tracking
    endpoint = Column(String, nullable=True)  # API endpoint for API docs
    tags = Column(JSON, default=list)  # Flexible tagging
    last_synced = Column(DateTime, nullable=True)  # Last sync time for documentation
    
    # Metadata
    meta_data = Column("metadata", JSON, default=dict)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Relationships
    business_config = relationship("BusinessConfig", back_populates="knowledge_entries")

    __table_args__ = (
        Index("idx_knowledge_business", "business_id"),
        Index("idx_knowledge_vector", "vector_id"),
        Index("idx_knowledge_vendor", "vendor"),
        Index("idx_knowledge_doc_type", "doc_type"),
        Index("idx_knowledge_vendor_type", "vendor", "doc_type"),
    )


class SyncProgress(Base):
    """Documentation sync progress tracking model"""
    __tablename__ = "sync_progress"

    id = Column(Integer, primary_key=True, autoincrement=True)
    vendor = Column(String, nullable=False, index=True)
    status = Column(String, nullable=False, default="pending")  # pending, in_progress, completed, failed, cancelled
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    pages_scraped = Column(Integer, default=0, nullable=False)
    pages_processed = Column(Integer, default=0, nullable=False)
    total_pages = Column(Integer, nullable=True)
    current_url = Column(String, nullable=True)
    visited_urls = Column(JSON, default=list)  # List of visited URLs
    errors = Column(JSON, default=list)  # List of error messages
    meta_data = Column("metadata", JSON, default=dict)  # Additional metadata (using Column name to avoid conflict)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    __table_args__ = (
        Index("idx_sync_vendor_status", "vendor", "status"),
        Index("idx_sync_status", "status"),
    )


class QAScore(Base):
    """Quality assurance score model"""
    __tablename__ = "qa_scores"

    id = Column(Integer, primary_key=True, autoincrement=True)
    call_id = Column(String, ForeignKey("calls.id"), nullable=False, index=True)
    
    # Scores
    overall_score = Column(Float, nullable=False)
    sentiment_score = Column(Float, nullable=True)
    compliance_score = Column(Float, nullable=True)
    accuracy_score = Column(Float, nullable=True)
    professionalism_score = Column(Float, nullable=True)
    
    # Analysis
    sentiment_label = Column(String, nullable=True)  # "positive", "neutral", "negative"
    compliance_issues = Column(JSON, default=list)
    flagged_issues = Column(JSON, default=list)
    
    # Reviewer information
    reviewed_by = Column(String, nullable=True)  # User ID or "auto"
    review_notes = Column(Text, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Relationships
    call = relationship("Call", back_populates="qa_scores")

    __table_args__ = (
        Index("idx_qa_call", "call_id"),
        Index("idx_qa_score", "overall_score"),
    )


class Escalation(Base):
    """Escalation model"""
    __tablename__ = "escalations"

    id = Column(Integer, primary_key=True, autoincrement=True)
    call_id = Column(String, ForeignKey("calls.id"), nullable=False, index=True)
    
    # Escalation details
    status = Column(SQLEnum(EscalationStatus), default=EscalationStatus.PENDING, nullable=False)
    trigger_type = Column(String, nullable=False)  # "sentiment", "keyword", "complexity", "manual"
    trigger_details = Column(JSON, default=dict)
    
    # Agent information
    assigned_agent_id = Column(String, nullable=True)
    agent_name = Column(String, nullable=True)
    
    # Context transfer
    conversation_summary = Column(Text, nullable=True)
    context_data = Column(JSON, default=dict)
    
    # Timestamps
    requested_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    accepted_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Relationships
    call = relationship("Call", back_populates="escalations")

    __table_args__ = (
        Index("idx_escalation_call", "call_id"),
        Index("idx_escalation_status", "status"),
    )


class Notification(Base):
    """Notification model"""
    __tablename__ = "notifications"

    id = Column(String, primary_key=True)
    user_id = Column(String, ForeignKey("users.id"), nullable=True, index=True)
    type = Column(String, nullable=False)  # call_escalated, qa_alert, system_update, etc.
    title = Column(String, nullable=False)
    message = Column(Text, nullable=False)
    read = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    meta_data = Column("metadata", JSON, default=dict)  # Using Column name to avoid SQLAlchemy reserved word conflict
    action_url = Column(String, nullable=True)
    
    # Relationships
    user = relationship("User", back_populates="notifications")

    __table_args__ = (
        Index("idx_notifications_user", "user_id"),
        Index("idx_notifications_read", "read"),
        Index("idx_notifications_created_at", "created_at"),
        Index("idx_notifications_user_read", "user_id", "read"),  # Composite index for common query
    )


class User(Base):
    """User model for authentication"""
    __tablename__ = "users"

    id = Column(String, primary_key=True)
    email = Column(String, unique=True, nullable=False, index=True)
    hashed_password = Column(String, nullable=False)
    name = Column(String, nullable=False)
    
    # Status
    is_active = Column(Boolean, default=True, nullable=False)
    is_superuser = Column(Boolean, default=False, nullable=False)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    last_login_at = Column(DateTime, nullable=True)
    
    # Metadata
    meta_data = Column("metadata", JSON, default=dict)
    
    # Relationships
    notifications = relationship("Notification", back_populates="user")
    business_configs = relationship("BusinessConfig", back_populates="created_by_user")

    __table_args__ = (
        Index("idx_users_email", "email"),
        Index("idx_users_active", "is_active"),
    )


class HumanAgent(Base):
    """Human agent model"""
    __tablename__ = "human_agents"

    id = Column(String, primary_key=True)
    name = Column(String, nullable=False)
    email = Column(String, unique=True, nullable=False, index=True)
    
    # Status
    is_available = Column(Boolean, default=True, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    
    # Contact information
    phone_number = Column(String, nullable=True)
    extension = Column(String, nullable=True)
    
    # Skills/Departments
    skills = Column(JSON, default=list)
    departments = Column(JSON, default=list)
    
    # Statistics
    total_calls_handled = Column(Integer, default=0)
    average_rating = Column(Float, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    last_active_at = Column(DateTime, nullable=True)
    
    # Metadata
    meta_data = Column("metadata", JSON, default=dict)
    
    # Relationships
    phone_numbers = relationship("AgentPhoneNumber", back_populates="agent", cascade="all, delete-orphan")

    __table_args__ = (
        Index("idx_agents_available", "is_available", "is_active"),
    )


class PhoneNumber(Base):
    """Phone number model"""
    __tablename__ = "phone_numbers"

    id = Column(String, primary_key=True)
    phone_number = Column(String, unique=True, nullable=False, index=True)  # E.164 format
    twilio_phone_sid = Column(String, unique=True, nullable=True, index=True)  # Twilio SID
    friendly_name = Column(String, nullable=True)
    country_code = Column(String, nullable=False)
    region = Column(String, nullable=True)
    capabilities = Column(JSON, default=dict)  # voice, SMS, MMS, etc.
    status = Column(String, nullable=False, default="active")  # active, pending, released
    webhook_url = Column(String, nullable=True)
    webhook_method = Column(String, nullable=False, default="POST")
    is_active = Column(Boolean, default=True, nullable=False)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Metadata
    meta_data = Column("metadata", JSON, default=dict)
    
    # Relationships
    agent_assignments = relationship("AgentPhoneNumber", back_populates="phone_number", cascade="all, delete-orphan")
    business_assignments = relationship("BusinessPhoneNumber", back_populates="phone_number", cascade="all, delete-orphan")

    __table_args__ = (
        Index("idx_phone_numbers_status", "status"),
        Index("idx_phone_numbers_active", "is_active"),
        Index("idx_phone_numbers_country", "country_code"),
    )


class AgentPhoneNumber(Base):
    """Agent-Phone Number association model"""
    __tablename__ = "agent_phone_numbers"

    id = Column(Integer, primary_key=True, autoincrement=True)
    agent_id = Column(String, ForeignKey("human_agents.id"), nullable=False, index=True)
    phone_number_id = Column(String, ForeignKey("phone_numbers.id"), nullable=False, index=True)
    is_primary = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    # Relationships
    agent = relationship("HumanAgent", back_populates="phone_numbers")
    phone_number = relationship("PhoneNumber", back_populates="agent_assignments")

    __table_args__ = (
        UniqueConstraint("agent_id", "phone_number_id", name="uq_agent_phone_number"),
        Index("idx_agent_phone_primary", "agent_id", "is_primary"),
    )


class BusinessPhoneNumber(Base):
    """Business-Phone Number association model"""
    __tablename__ = "business_phone_numbers"

    id = Column(Integer, primary_key=True, autoincrement=True)
    business_id = Column(String, ForeignKey("business_configs.id"), nullable=False, index=True)
    phone_number_id = Column(String, ForeignKey("phone_numbers.id"), nullable=False, index=True)
    is_primary = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    # Relationships
    business = relationship("BusinessConfig", back_populates="phone_numbers")
    phone_number = relationship("PhoneNumber", back_populates="business_assignments")

    __table_args__ = (
        UniqueConstraint("business_id", "phone_number_id", name="uq_business_phone_number"),
        Index("idx_business_phone_primary", "business_id", "is_primary"),
    )

