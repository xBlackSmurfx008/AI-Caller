"""Database models"""

from sqlalchemy import Column, String, Text, JSON, DateTime, Boolean, Integer, ForeignKey, Float
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid

from src.database.database import Base


class Task(Base):
    """Task model for persistent storage"""
    __tablename__ = "tasks"

    task_id = Column(String, primary_key=True, index=True)
    status = Column(String, nullable=False, index=True)
    task = Column(Text, nullable=False)
    requires_confirmation = Column(Boolean, default=False)
    planned_tool_calls = Column(JSON, nullable=True)
    policy_reasons = Column(JSON, nullable=True)
    result = Column(JSON, nullable=True)
    error = Column(Text, nullable=True)
    context = Column(JSON, nullable=True)
    plan_response = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)


class ChatSession(Base):
    """Durable chat thread for Godfather assistant conversations."""
    __tablename__ = "chat_sessions"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()), index=True)
    title = Column(String, nullable=True)
    # Scope: global Godfather thread or per-project thread
    # - scope_type: "global" | "project"
    # - scope_id: for project scope, project_id; for global scope, can be NULL
    scope_type = Column(String, nullable=False, default="global", index=True)
    scope_id = Column(String, nullable=True, index=True)
    # Optional actor identity (useful if multiple users are added later)
    actor_phone = Column(String, nullable=True, index=True)
    actor_email = Column(String, nullable=True, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    messages = relationship("ChatMessage", back_populates="session", cascade="all, delete-orphan")
    summary = relationship("ChatSessionSummary", back_populates="session", uselist=False, cascade="all, delete-orphan")


class ChatMessage(Base):
    """Message within a chat session (user/assistant/system/tool)."""
    __tablename__ = "chat_messages"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()), index=True)
    session_id = Column(String, ForeignKey("chat_sessions.id", ondelete="CASCADE"), nullable=False, index=True)
    role = Column(String, nullable=False, index=True)  # "system", "user", "assistant", "tool"
    content = Column(Text, nullable=False)
    meta_data = Column("metadata", JSON, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    session = relationship("ChatSession", back_populates="messages")


class ChatSessionSummary(Base):
    """Rolling summary for a chat session (compressed history)."""
    __tablename__ = "chat_session_summaries"

    session_id = Column(String, ForeignKey("chat_sessions.id", ondelete="CASCADE"), primary_key=True, index=True)
    summary = Column(Text, nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    version = Column(Integer, default=1)

    session = relationship("ChatSession", back_populates="summary")


class Contact(Base):
    """Contact model for storing user contacts"""
    __tablename__ = "contacts"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()), index=True)
    name = Column(String, nullable=False, index=True)
    phone_number = Column(String, nullable=True, index=True)
    email = Column(String, nullable=True, index=True)
    organization = Column(String, nullable=True)
    notes = Column(Text, nullable=True)
    tags = Column(JSON, nullable=True)  # Array of tags for categorization
    industries = Column(JSON, nullable=True)  # Array of industries
    location = Column(String, nullable=True)  # Geographic location
    relationship_score = Column(Float, default=0.0)  # 0.0 to 1.0 relationship strength
    value_map = Column(JSON, nullable=True)  # {"offers": [...], "wants": [...], "mutual_benefits": [...]}
    is_sensitive = Column(Boolean, default=False)  # Do-not-suggest flag
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    
    # Relationships
    interactions = relationship("Interaction", back_populates="contact", cascade="all, delete-orphan")
    memory_state = relationship("ContactMemoryState", back_populates="contact", uselist=False, cascade="all, delete-orphan")
    project_stakeholders = relationship("ProjectStakeholder", back_populates="contact", cascade="all, delete-orphan")
    commitments = relationship("Commitment", back_populates="contact", cascade="all, delete-orphan")
    messages = relationship("Message", back_populates="contact", cascade="all, delete-orphan")
    channel_identities = relationship("ChannelIdentity", back_populates="contact", cascade="all, delete-orphan")


class Interaction(Base):
    """Raw interaction content (email, SMS, call transcript)"""
    __tablename__ = "interactions"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()), index=True)
    contact_id = Column(String, ForeignKey("contacts.id", ondelete="CASCADE"), nullable=False, index=True)
    message_id = Column(String, ForeignKey("messages.id", ondelete="SET NULL"), nullable=True, index=True)  # Link to Message if applicable
    channel = Column(String, nullable=False, index=True)  # "email", "sms", "mms", "whatsapp", "call"
    raw_content = Column(Text, nullable=False)  # Full transcript/message content
    # NOTE: `metadata` is reserved by SQLAlchemy Declarative.
    # Keep DB column name as "metadata" for compatibility, but expose as `meta_data`.
    meta_data = Column("metadata", JSON, nullable=True)  # Additional metadata (subject, call_sid, etc.)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    
    # Relationships
    contact = relationship("Contact", back_populates="interactions")
    message = relationship("Message", foreign_keys=[message_id])
    memory_summary = relationship("MemorySummary", back_populates="interaction", uselist=False, cascade="all, delete-orphan")


class MemorySummary(Base):
    """Structured summary of an interaction"""
    __tablename__ = "memory_summaries"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()), index=True)
    interaction_id = Column(String, ForeignKey("interactions.id", ondelete="CASCADE"), nullable=False, unique=True, index=True)
    summary = Column(Text, nullable=False)  # TL;DR summary
    key_facts = Column(JSON, nullable=True)  # Array of key facts learned
    sentiment_score = Column(Float, nullable=True)  # -1.0 to 1.0
    sentiment_explanation = Column(Text, nullable=True)
    godfather_goals = Column(JSON, nullable=True)  # Array of current/implied goals
    commitments = Column(JSON, nullable=True)  # Array of commitments with deadlines
    next_actions = Column(JSON, nullable=True)  # Array of suggested next actions
    preferences = Column(JSON, nullable=True)  # Preferences and constraints learned
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    
    # Relationships
    interaction = relationship("Interaction", back_populates="memory_summary")


class ContactMemoryState(Base):
    """Rolling current understanding of a contact (merged across all channels)"""
    __tablename__ = "contact_memory_state"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()), index=True)
    contact_id = Column(String, ForeignKey("contacts.id", ondelete="CASCADE"), nullable=False, unique=True, index=True)
    latest_summary = Column(Text, nullable=True)  # Most recent summary
    sentiment_trend = Column(String, nullable=True)  # "positive", "neutral", "negative", "improving", "declining"
    active_goals = Column(JSON, nullable=True)  # Current active Godfather goals
    outstanding_actions = Column(JSON, nullable=True)  # Open loops / next actions
    relationship_status = Column(String, nullable=True)  # Relationship status description
    key_preferences = Column(JSON, nullable=True)  # Important preferences and constraints
    last_interaction_at = Column(DateTime(timezone=True), nullable=True)
    last_updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    
    # Enhanced fields for Master Networker CRM
    relationship_score_trend = Column(String, nullable=True)  # "rising", "stable", "declining"
    open_loops = Column(JSON, nullable=True)  # Array of open conversation loops
    commitments_made = Column(JSON, nullable=True)  # Array of Godfather commitments to this person
    commitments_received = Column(JSON, nullable=True)  # Array of their commitments to Godfather
    
    # Value mapping (what they offer/want/how to help)
    offers = Column(JSON, nullable=True)  # Their skills, resources, influence
    wants = Column(JSON, nullable=True)  # Their goals, pain points
    ways_to_help_them = Column(JSON, nullable=True)  # Specific ways Godfather can add value
    
    # Communication preferences
    preferred_channels = Column(JSON, nullable=True)  # Array of preferred channels in order
    best_times = Column(JSON, nullable=True)  # Best times to reach (e.g., ["morning", "weekday"])
    sensitivities = Column(JSON, nullable=True)  # Topics/boundaries to respect
    do_not_contact = Column(Boolean, default=False)  # Block all suggestions
    
    # Reciprocity tracking
    reciprocity_balance = Column(Float, default=0.0)  # Positive = they owe us, Negative = we owe them
    last_value_given_at = Column(DateTime(timezone=True), nullable=True)
    last_value_received_at = Column(DateTime(timezone=True), nullable=True)
    
    # Relationships
    contact = relationship("Contact", back_populates="memory_state")


class Goal(Base):
    """Godfather goal (short-term or long-term)"""
    __tablename__ = "goals"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()), index=True)
    title = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    goal_type = Column(String, nullable=False)  # "short_term" or "long_term"
    status = Column(String, default="active")  # "active", "completed", "paused", "cancelled"
    priority = Column(Integer, default=5)  # 1-10, higher is more important
    target_date = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    
    # Relationships
    projects = relationship("Project", back_populates="goal", cascade="all, delete-orphan")


class Project(Base):
    """Real-world project with milestones and deliverables"""
    __tablename__ = "projects"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()), index=True)
    goal_id = Column(String, ForeignKey("goals.id", ondelete="SET NULL"), nullable=True, index=True)
    title = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    status = Column(String, default="active")  # "active", "completed", "paused", "cancelled", "blocked"
    priority = Column(Integer, default=5)  # 1-10, higher is more important (P0=10, P1=8, P2=5, P3=3)
    target_due_date = Column(DateTime(timezone=True), nullable=True)  # Target completion date
    milestones = Column(JSON, nullable=True)  # Array of milestone objects
    constraints = Column(JSON, nullable=True)  # {"time": "...", "budget": "...", "bandwidth": "..."}
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    
    # Relationships
    goal = relationship("Goal", back_populates="projects")
    stakeholders = relationship("ProjectStakeholder", back_populates="project", cascade="all, delete-orphan")
    tasks = relationship("ProjectTask", back_populates="project", cascade="all, delete-orphan")


class ProjectStakeholder(Base):
    """Many-to-many relationship between projects and contacts"""
    __tablename__ = "project_stakeholders"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()), index=True)
    project_id = Column(String, ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True)
    contact_id = Column(String, ForeignKey("contacts.id", ondelete="CASCADE"), nullable=False, index=True)
    role = Column(String, nullable=True)  # "collaborator", "advisor", "partner", "stakeholder"
    how_they_help = Column(Text, nullable=True)  # How this contact can help the project
    how_we_help = Column(Text, nullable=True)  # How we can help them
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    
    # Relationships
    project = relationship("Project", back_populates="stakeholders")
    contact = relationship("Contact", back_populates="project_stakeholders")


class ProjectTask(Base):
    """Task linked to a project with scheduling and AI execution support"""
    __tablename__ = "project_tasks"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()), index=True)
    project_id = Column(String, ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True)
    title = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    status = Column(String, default="todo")  # "todo", "scheduled", "in_progress", "blocked", "done"
    priority = Column(Integer, default=5)  # 1-10, higher is more important
    
    # Scheduling fields
    estimated_minutes = Column(Integer, nullable=True)  # Estimated duration
    deadline_type = Column(String, nullable=True)  # "HARD" or "FLEX" (flexible)
    due_at = Column(DateTime(timezone=True), nullable=True, index=True)  # Deadline datetime
    earliest_start_at = Column(DateTime(timezone=True), nullable=True)  # Cannot start before this
    locked_schedule = Column(Boolean, default=False)  # If True, cannot be rescheduled automatically
    
    # Dependencies (stored as JSON array of task_ids)
    dependencies = Column(JSON, nullable=True)  # Array of task IDs that must complete first
    
    # Task metadata
    tags = Column(JSON, nullable=True)  # Array of tags: ["deep_work", "shallow_work", etc.]
    energy_level = Column(String, nullable=True)  # "low", "medium", "high"
    
    # AI execution
    execution_mode = Column(String, default="HUMAN")  # "HUMAN", "AI", "HYBRID"
    
    # Legacy fields (keeping for backward compatibility)
    due_date = Column(DateTime(timezone=True), nullable=True)  # Deprecated, use due_at
    assigned_contact_id = Column(String, ForeignKey("contacts.id", ondelete="SET NULL"), nullable=True, index=True)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    
    # Relationships
    project = relationship("Project", back_populates="tasks")
    calendar_blocks = relationship("CalendarBlock", back_populates="task", cascade="all, delete-orphan")
    ai_executions = relationship("AIExecution", back_populates="task", cascade="all, delete-orphan")


class Commitment(Base):
    """Track promises made by Godfather or others"""
    __tablename__ = "commitments"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()), index=True)
    contact_id = Column(String, ForeignKey("contacts.id", ondelete="CASCADE"), nullable=True, index=True)
    project_id = Column(String, ForeignKey("projects.id", ondelete="SET NULL"), nullable=True, index=True)
    description = Column(Text, nullable=False)
    committed_by = Column(String, nullable=False)  # "godfather" or "contact"
    deadline = Column(DateTime(timezone=True), nullable=True)
    status = Column(String, default="pending")  # "pending", "completed", "overdue", "cancelled"
    is_trust_risk = Column(Boolean, default=False)  # Flag for missed commitments
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    
    # Relationships
    contact = relationship("Contact", back_populates="commitments")


class Suggestion(Base):
    """AI-generated suggestion for relationship actions"""
    __tablename__ = "suggestions"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()), index=True)
    suggestion_type = Column(String, nullable=False)  # "contact", "introduction", "value_first", "follow_up", "repair", "growth"
    contact_id = Column(String, ForeignKey("contacts.id", ondelete="CASCADE"), nullable=True, index=True)
    project_id = Column(String, ForeignKey("projects.id", ondelete="SET NULL"), nullable=True, index=True)
    intent = Column(Text, nullable=False)  # Why this matters
    rationale = Column(Text, nullable=True)  # Detailed explanation
    expected_upside_godfather = Column(Text, nullable=True)
    expected_upside_contact = Column(Text, nullable=True)
    risk_flags = Column(JSON, nullable=True)  # Array of risk notes
    message_draft = Column(Text, nullable=True)  # Suggested message/talk track
    best_timing = Column(String, nullable=True)  # "now", "later", "next_meeting"
    score = Column(Float, nullable=True)  # Ranking score
    status = Column(String, default="pending")  # "pending", "approved", "executed", "dismissed"
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    expires_at = Column(DateTime(timezone=True), nullable=True)


class IntroductionRecommendation(Base):
    """Recommendation to introduce two contacts"""
    __tablename__ = "introduction_recommendations"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()), index=True)
    contact_a_id = Column(String, ForeignKey("contacts.id", ondelete="CASCADE"), nullable=False, index=True)
    contact_b_id = Column(String, ForeignKey("contacts.id", ondelete="CASCADE"), nullable=False, index=True)
    mutual_benefit = Column(Text, nullable=False)  # Why they should meet
    context = Column(Text, nullable=True)  # Additional context
    suggested_approach = Column(Text, nullable=True)  # How to make the introduction
    score = Column(Float, nullable=True)  # Ranking score
    status = Column(String, default="pending")  # "pending", "approved", "executed", "dismissed"
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)


class Message(Base):
    """Message model for Twilio SMS/MMS/WhatsApp messages"""
    __tablename__ = "messages"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()), index=True)
    contact_id = Column(String, ForeignKey("contacts.id", ondelete="CASCADE"), nullable=True, index=True)  # Nullable for unknown senders
    channel = Column(String, nullable=False, index=True)  # "sms", "mms", "whatsapp"
    direction = Column(String, nullable=False, index=True)  # "inbound", "outbound"
    timestamp = Column(DateTime(timezone=True), nullable=False, index=True)
    raw_payload = Column(JSON, nullable=True)  # Full Twilio payload
    text_content = Column(Text, nullable=True)  # Message body
    media_urls = Column(JSON, nullable=True)  # Array of media URLs for MMS
    conversation_id = Column(String, nullable=True, index=True)  # Groups messages into conversations
    twilio_message_sid = Column(String, unique=True, nullable=True, index=True)  # Twilio MessageSid for deduplication
    status = Column(String, nullable=True)  # "queued", "sent", "delivered", "failed", "received"
    error_code = Column(String, nullable=True)  # Error code if failed
    is_read = Column(Boolean, default=False, index=True)  # Unread tracking for inbound messages
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    
    # Relationships
    contact = relationship("Contact", back_populates="messages")
    approval = relationship("OutboundApproval", back_populates="message", uselist=False, cascade="all, delete-orphan")


class ChannelIdentity(Base):
    """Map phone numbers/WhatsApp IDs to contacts"""
    __tablename__ = "channel_identities"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()), index=True)
    contact_id = Column(String, ForeignKey("contacts.id", ondelete="CASCADE"), nullable=False, index=True)
    channel = Column(String, nullable=False, index=True)  # "sms", "whatsapp"
    address = Column(String, nullable=False, index=True)  # Phone number or WhatsApp ID in E.164 format
    verified = Column(Boolean, default=False)  # Whether this identity is verified
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    
    # Relationships
    contact = relationship("Contact", back_populates="channel_identities")


class OutboundApproval(Base):
    """Track approval workflow for outbound messages"""
    __tablename__ = "outbound_approvals"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()), index=True)
    message_id = Column(String, ForeignKey("messages.id", ondelete="CASCADE"), nullable=False, unique=True, index=True)
    draft_id = Column(String, nullable=True)  # Reference to suggestion/draft if applicable
    approved_by = Column(String, nullable=True)  # User ID or "godfather"
    approved_at = Column(DateTime(timezone=True), nullable=True)
    sent_at = Column(DateTime(timezone=True), nullable=True)
    status = Column(String, default="pending")  # "pending", "approved", "rejected", "sent", "failed"
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    
    # Relationships
    message = relationship("Message", back_populates="approval")


class CalendarBlock(Base):
    """Calendar event block linked to a task"""
    __tablename__ = "calendar_blocks"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()), index=True)
    task_id = Column(String, ForeignKey("project_tasks.id", ondelete="CASCADE"), nullable=False, index=True)
    calendar_event_id = Column(String, nullable=True, index=True)  # Google Calendar event ID
    start_at = Column(DateTime(timezone=True), nullable=False, index=True)
    end_at = Column(DateTime(timezone=True), nullable=False)
    locked = Column(Boolean, default=False)  # If True, cannot be moved automatically
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    
    # Relationships
    task = relationship("ProjectTask", back_populates="calendar_blocks")


class WorkPreferences(Base):
    """User work preferences for scheduling"""
    __tablename__ = "work_preferences"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()), index=True)
    working_hours_start = Column(String, default="09:00")  # HH:MM format
    working_hours_end = Column(String, default="17:00")  # HH:MM format
    working_days = Column(JSON, nullable=True)  # Array of day numbers: [0,1,2,3,4] for Mon-Fri
    focus_blocks = Column(JSON, nullable=True)  # Array of {"start": "HH:MM", "end": "HH:MM"} for deep work times
    buffer_minutes = Column(Integer, default=15)  # Buffer time between meetings/tasks
    max_blocks_per_day = Column(Integer, default=8)  # Maximum scheduled task blocks per day
    task_switching_penalty = Column(Integer, default=0)  # Minutes to add when switching between tasks
    timezone = Column(String, default="UTC")  # IANA timezone string
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)


class AIAutonomyConfig(Base):
    """Runtime AI autonomy configuration stored in DB (overrides env defaults when present)."""
    __tablename__ = "ai_autonomy_config"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()), index=True)
    level = Column(String, default="balanced")  # "cautious" | "balanced" | "autopilot"
    settings = Column(JSON, nullable=True)  # Stores UI settings for future expansion
    auto_execute_high_risk = Column(Boolean, default=False, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)


class GodfatherProfile(Base):
    """Godfather personal profile (used as durable 'who I am' context for the assistant)."""
    __tablename__ = "godfather_profile"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()), index=True)

    full_name = Column(String, nullable=True)
    preferred_name = Column(String, nullable=True)
    pronouns = Column(String, nullable=True)

    location = Column(String, nullable=True)  # City/region
    timezone = Column(String, default="UTC")

    company = Column(String, nullable=True)
    title = Column(String, nullable=True)

    bio = Column(Text, nullable=True)  # short bio
    assistant_notes = Column(Text, nullable=True)  # "how you want the assistant to behave for you"

    # Extra structured info (lightweight, extendable)
    preferences = Column(JSON, nullable=True)  # e.g. {"tone":"direct","signoff":"-Stephen", ...}

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)


class AIExecution(Base):
    """AI task execution record"""
    __tablename__ = "ai_executions"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()), index=True)
    task_id = Column(String, ForeignKey("project_tasks.id", ondelete="CASCADE"), nullable=False, index=True)
    execution_plan = Column(JSON, nullable=True)  # Steps + tools required + expected outputs
    status = Column(String, default="pending")  # "pending", "running", "completed", "failed", "approved"
    outputs = Column(JSON, nullable=True)  # Deliverables: drafts, docs, research notes, etc.
    tool_calls = Column(JSON, nullable=True)  # Log of tool calls made
    required_approvals = Column(JSON, nullable=True)  # Array of actions requiring approval
    summary = Column(Text, nullable=True)  # Summary of what was done
    error = Column(Text, nullable=True)  # Error message if failed
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    
    # Relationships
    task = relationship("ProjectTask", back_populates="ai_executions")


class PreferenceCategory(Base):
    """Category for organizing preferences"""
    __tablename__ = "preference_categories"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()), index=True)
    name = Column(String, nullable=False, unique=True, index=True)  # e.g., "groceries", "travel", "healthcare"
    display_name = Column(String, nullable=True)  # Human-readable name
    description = Column(Text, nullable=True)
    default_entry_id = Column(String, nullable=True)  # Optional default preference for this category
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)


class PreferenceEntry(Base):
    """Trusted List / Favorites & Defaults entry"""
    __tablename__ = "preference_entries"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()), index=True)
    owner_user_id = Column(String, nullable=True, index=True)  # For multi-user support (optional)
    
    # Core fields
    type = Column(String, nullable=False, index=True)  # VENDOR | PROVIDER | WEBSITE | LOCATION | TOOL | AVOID
    category = Column(String, nullable=False, index=True)  # groceries | travel | healthcare | etc.
    name = Column(String, nullable=False, index=True)
    priority = Column(String, default="PRIMARY", index=True)  # PRIMARY | SECONDARY | AVOID
    
    # Metadata
    tags = Column(JSON, nullable=True)  # Array of tags: ["default", "backup", "premium", "budget"]
    url = Column(String, nullable=True)
    phone = Column(String, nullable=True)
    address = Column(Text, nullable=True)
    notes = Column(Text, nullable=True)
    constraints = Column(JSON, nullable=True)  # Structured JSON: {"only_for": "business_travel", "max_price": 400}
    
    # Usage tracking
    last_used_at = Column(DateTime(timezone=True), nullable=True, index=True)
    
    # Relationships (optional - link to contacts if provider is also a contact)
    related_contact_id = Column(String, ForeignKey("contacts.id", ondelete="SET NULL"), nullable=True, index=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    
    # Relationships
    related_contact = relationship("Contact", foreign_keys=[related_contact_id])


class PricingRule(Base):
    """API pricing rule registry"""
    __tablename__ = "pricing_rules"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()), index=True)
    provider = Column(String, nullable=False, index=True)  # "openai", "twilio", "google", etc.
    service = Column(String, nullable=False, index=True)  # "chat", "sms", "mms", "whatsapp", "voice", etc.
    service_type = Column(String, nullable=False)  # "LLM", "messaging", "transcription", "maps", etc.
    pricing_model = Column(String, nullable=False)  # "PER_TOKEN", "PER_REQUEST", "PER_MESSAGE", "PER_MINUTE", "PER_IMAGE"
    
    # Pricing details (JSON for flexibility)
    unit_costs = Column(JSON, nullable=False)  # {"input_token": 0.00001, "output_token": 0.00003} or {"per_message": 0.0075}
    currency = Column(String, default="USD")
    effective_date = Column(DateTime(timezone=True), nullable=False, index=True)  # When this pricing takes effect
    expires_at = Column(DateTime(timezone=True), nullable=True)  # When this pricing expires (null = current)
    
    # Metadata
    documentation_url = Column(String, nullable=True)
    notes = Column(Text, nullable=True)
    rate_limits = Column(JSON, nullable=True)  # {"requests_per_minute": 60, "tokens_per_minute": 90000}
    free_tier = Column(JSON, nullable=True)  # {"included_requests": 1000, "included_tokens": 1000000}
    
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)


class CostEvent(Base):
    """Atomic billable event (single source of truth for costs)"""
    __tablename__ = "cost_events"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()), index=True)
    event_id = Column(String, unique=True, nullable=True, index=True)  # Provider request ID for idempotency
    
    # Context
    task_id = Column(String, nullable=True, index=True)  # Task that triggered this
    project_id = Column(String, nullable=True, index=True)  # Project this task belongs to
    agent_id = Column(String, nullable=True, index=True)  # Agent/sub-agent identifier
    execution_id = Column(String, nullable=True, index=True)  # AIExecution ID if applicable
    
    # Provider details
    provider = Column(String, nullable=False, index=True)  # "openai", "twilio", etc.
    service = Column(String, nullable=False, index=True)  # "chat", "sms", etc.
    metric_type = Column(String, nullable=False)  # "tokens", "requests", "messages", "minutes", "images"
    
    # Cost calculation
    units = Column(Float, nullable=False)  # Number of units consumed
    unit_cost = Column(Float, nullable=True)  # Cost per unit (resolved from pricing registry)
    total_cost = Column(Float, nullable=False)  # units * unit_cost
    
    # Metadata
    # NOTE: `metadata` is reserved by SQLAlchemy Declarative.
    meta_data = Column("metadata", JSON, nullable=True)  # Model name, endpoint, region, phone carrier, etc.
    timestamp = Column(DateTime(timezone=True), server_default=func.now(), nullable=False, index=True)
    
    # Status
    is_priced = Column(Boolean, default=True)  # False if pricing rule was missing
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)


class TaskCostEstimate(Base):
    """Pre-flight cost estimate for a task"""
    __tablename__ = "task_cost_estimates"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()), index=True)
    task_id = Column(String, nullable=False, unique=True, index=True)  # One estimate per task
    estimated_total_cost = Column(Float, nullable=False)
    confidence_score = Column(Float, nullable=True)  # 0.0 to 1.0
    
    # Breakdown (JSON array of predicted cost events)
    breakdown = Column(JSON, nullable=False)  # [{"provider": "openai", "service": "chat", "estimated_cost": 0.15, ...}]
    
    # Optimization suggestions
    cost_optimizations = Column(JSON, nullable=True)  # [{"suggestion": "...", "potential_savings": 0.05}]
    
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)


class TaskCostActual(Base):
    """Post-task actual cost aggregation"""
    __tablename__ = "task_cost_actuals"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()), index=True)
    task_id = Column(String, nullable=False, unique=True, index=True)  # One actual per task
    actual_total_cost = Column(Float, nullable=False)
    
    # Breakdown (aggregated from cost_events)
    breakdown = Column(JSON, nullable=False)  # [{"provider": "openai", "service": "chat", "actual_cost": 0.18, "events_count": 3}]
    
    # Variance analysis
    estimated_cost = Column(Float, nullable=True)  # From TaskCostEstimate
    variance = Column(Float, nullable=True)  # actual - estimated
    variance_percentage = Column(Float, nullable=True)  # (variance / estimated) * 100
    
    # Which API caused the variance
    variance_breakdown = Column(JSON, nullable=True)  # [{"provider": "openai", "variance": 0.03, "reason": "..."}]
    
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)


class Budget(Base):
    """Budget configuration for cost tracking"""
    __tablename__ = "budgets"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()), index=True)
    scope = Column(String, nullable=False, index=True)  # "overall", "provider", "project", "agent"
    scope_id = Column(String, nullable=True, index=True)  # Provider name, project_id, agent_id, or null for overall
    period = Column(String, nullable=False, index=True)  # "daily", "weekly", "monthly"
    limit = Column(Float, nullable=False)  # Budget limit in USD
    currency = Column(String, default="USD")
    
    # Enforcement
    enforcement_mode = Column(String, default="warn")  # "warn", "require_confirmation", "hard_stop"
    
    # Status
    is_active = Column(Boolean, default=True, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)


class CostAlert(Base):
    """Cost alert triggered when budget thresholds are crossed"""
    __tablename__ = "cost_alerts"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()), index=True)
    budget_id = Column(String, ForeignKey("budgets.id", ondelete="CASCADE"), nullable=True, index=True)
    alert_type = Column(String, nullable=False, index=True)  # "budget_exceeded", "forecast_exceeded", "task_estimate_high"
    severity = Column(String, default="warning")  # "info", "warning", "critical"
    
    # Context
    scope = Column(String, nullable=False)  # "overall", "provider", "project", "agent"
    scope_id = Column(String, nullable=True)
    period = Column(String, nullable=False)
    
    # Metrics
    current_spend = Column(Float, nullable=False)
    limit = Column(Float, nullable=False)
    percentage_used = Column(Float, nullable=False)  # (current_spend / limit) * 100
    forecasted_spend = Column(Float, nullable=True)  # Projected end-of-period spend
    
    # Message
    message = Column(Text, nullable=False)
    # NOTE: `metadata` is reserved by SQLAlchemy Declarative.
    meta_data = Column("metadata", JSON, nullable=True)  # Additional context
    
    # Status
    is_resolved = Column(Boolean, default=False, index=True)
    resolved_at = Column(DateTime(timezone=True), nullable=True)
    resolved_by = Column(String, nullable=True)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False, index=True)


class ProjectExecutionConfirmation(Base):
    """
    Project Execution Confirmation (PEC) - Validates project scope, plan,
    tool feasibility, constraints, and risks before execution.
    """
    __tablename__ = "project_execution_confirmations"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()), index=True)
    project_id = Column(String, ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True)
    version = Column(Integer, default=1, nullable=False)  # PEC version for this project
    
    # Status
    status = Column(String, default="draft", index=True)  # "draft", "pending_approval", "approved", "rejected", "superseded"
    execution_gate = Column(String, nullable=False)  # "READY", "READY_WITH_QUESTIONS", "BLOCKED"
    
    # Full PEC content as JSON
    summary = Column(JSON, nullable=True)  # Project summary section
    deliverables = Column(JSON, nullable=True)  # List of deliverables
    milestones = Column(JSON, nullable=True)  # List of milestones with timeline
    task_plan = Column(JSON, nullable=True)  # Task breakdown with estimates
    task_tool_map = Column(JSON, nullable=True)  # Tool/skill mapping per task with feasibility
    dependencies = Column(JSON, nullable=True)  # Task dependencies
    risks = Column(JSON, nullable=True)  # Risk analysis
    preferences_applied = Column(JSON, nullable=True)  # Trusted list / favorites applied
    constraints_applied = Column(JSON, nullable=True)  # Constraints (work hours, budget, etc.)
    assumptions = Column(JSON, nullable=True)  # Explicit assumptions
    gaps = Column(JSON, nullable=True)  # Missing information / data gaps
    cost_estimate = Column(JSON, nullable=True)  # Optional cost estimate
    approval_checklist = Column(JSON, nullable=True)  # Checklist items for approval
    stakeholders = Column(JSON, nullable=True)  # Stakeholders involved
    
    # Approval tracking
    approved_by = Column(String, nullable=True)
    approved_at = Column(DateTime(timezone=True), nullable=True)
    approval_notes = Column(Text, nullable=True)
    
    # Version tracking
    previous_pec_id = Column(String, ForeignKey("project_execution_confirmations.id", ondelete="SET NULL"), nullable=True)
    change_reason = Column(Text, nullable=True)  # Why was this PEC regenerated
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    
    # Relationships
    project = relationship("Project", backref="execution_confirmations")


# ============================================================================
# MASTER NETWORKER CRM - RELATIONSHIP OPERATIONS MODELS
# ============================================================================

class RelationshipAction(Base):
    """AI-recommended relationship action with full context and approval workflow"""
    __tablename__ = "relationship_actions"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()), index=True)
    run_id = Column(String, ForeignKey("daily_run_results.id", ondelete="CASCADE"), nullable=True, index=True)
    contact_id = Column(String, ForeignKey("contacts.id", ondelete="CASCADE"), nullable=False, index=True)
    project_id = Column(String, ForeignKey("projects.id", ondelete="SET NULL"), nullable=True, index=True)
    
    # Action type and details
    action_type = Column(String, nullable=False, index=True)  # reply, follow_up, intro, gratitude, check_in, ask, offer, schedule
    priority_score = Column(Float, default=0.5)  # 0.0 to 1.0
    
    # Context and reasoning
    why_now = Column(Text, nullable=True)  # Why this action is recommended now
    expected_win_win_outcome = Column(Text, nullable=True)  # Expected outcome for both parties
    risk_flags = Column(JSON, nullable=True)  # Array of risk notes
    
    # Draft content
    draft_message = Column(Text, nullable=True)  # Suggested message text
    draft_channel = Column(String, nullable=True)  # email, sms, whatsapp, call
    draft_subject = Column(String, nullable=True)  # For emails
    
    # Approval workflow
    requires_approval = Column(Boolean, default=True)
    status = Column(String, default="pending", index=True)  # pending, approved, executed, dismissed, expired
    approved_by = Column(String, nullable=True)
    approved_at = Column(DateTime(timezone=True), nullable=True)
    executed_at = Column(DateTime(timezone=True), nullable=True)
    
    # Scheduling
    suggested_schedule_at = Column(DateTime(timezone=True), nullable=True)  # Best time to execute
    calendar_block_id = Column(String, nullable=True)  # If scheduled as a calendar block
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    expires_at = Column(DateTime(timezone=True), nullable=True)
    
    # Relationships
    contact = relationship("Contact", foreign_keys=[contact_id])
    project = relationship("Project", foreign_keys=[project_id])


class DailyRunResult(Base):
    """Results from each scheduled relationship ops run"""
    __tablename__ = "daily_run_results"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()), index=True)
    run_type = Column(String, nullable=False, index=True)  # morning, midday, afternoon, evening
    run_date = Column(DateTime(timezone=True), nullable=False, index=True)
    
    # Run metadata
    status = Column(String, default="running", index=True)  # running, completed, failed
    started_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    error_message = Column(Text, nullable=True)
    
    # Ingested data counts
    interactions_ingested = Column(Integer, default=0)
    contacts_updated = Column(Integer, default=0)
    
    # Generated outputs (stored as JSON for flexibility)
    top_actions = Column(JSON, nullable=True)  # Top 5 actions for quick view
    messages_to_reply = Column(JSON, nullable=True)  # Pending replies
    intros_to_consider = Column(JSON, nullable=True)  # Introduction recommendations
    trust_risks = Column(JSON, nullable=True)  # Commitments at risk
    value_first_moves = Column(JSON, nullable=True)  # Value-first opportunities
    scheduled_blocks_proposed = Column(JSON, nullable=True)  # Calendar block proposals
    tasks_created = Column(JSON, nullable=True)  # Task IDs created
    approvals_needed = Column(JSON, nullable=True)  # Actions requiring approval
    
    # Summary for display
    summary_title = Column(String, nullable=True)  # e.g., "Morning Command Plan"
    summary_text = Column(Text, nullable=True)  # Executive summary of the run
    
    # Relationship health metrics
    relationship_wins = Column(JSON, nullable=True)  # What went well (for evening run)
    relationship_slips = Column(JSON, nullable=True)  # What slipped (trust debt)
    reconnect_tomorrow = Column(JSON, nullable=True)  # Top 3 to reconnect with
    health_score_trend = Column(Float, nullable=True)  # Overall trend
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    
    # Relationships
    actions = relationship("RelationshipAction", backref="run", cascade="all, delete-orphan")


class GodfatherIntention(Base):
    """Godfather's intention/goal for a specific contact"""
    __tablename__ = "godfather_intentions"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()), index=True)
    contact_id = Column(String, ForeignKey("contacts.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # Intention details
    intention = Column(Text, nullable=False)  # What the Godfather wants from/with this person
    intention_type = Column(String, nullable=True)  # collaboration, mentorship, partnership, advisory, etc.
    priority = Column(Integer, default=5)  # 1-10
    
    # Status
    status = Column(String, default="active")  # active, achieved, paused, cancelled
    target_date = Column(DateTime(timezone=True), nullable=True)
    
    # Progress tracking
    milestones = Column(JSON, nullable=True)  # Array of milestones
    current_progress = Column(Text, nullable=True)  # Free-form progress notes
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    
    # Relationships
    contact = relationship("Contact", backref="godfather_intentions")


class OAuthToken(Base):
    """OAuth tokens for external services (Gmail, Google Calendar, Outlook, etc.)
    
    Stores tokens in database for serverless environments where file storage is ephemeral.
    """
    __tablename__ = "oauth_tokens"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()), index=True)
    provider = Column(String, nullable=False, index=True)  # gmail, google_calendar, outlook
    token_data = Column(JSON, nullable=False)  # Full token JSON (access_token, refresh_token, etc.)
    scopes = Column(JSON, nullable=True)  # List of OAuth scopes
    email = Column(String, nullable=True)  # Associated email address
    expires_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

