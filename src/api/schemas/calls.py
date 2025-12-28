"""Pydantic schemas for calls API"""

from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field
from enum import Enum


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


class CallInitiateRequest(BaseModel):
    """Schema for initiating a call"""
    to_number: str
    from_number: Optional[str] = None
    business_id: Optional[str] = None
    template_id: Optional[str] = None
    agent_id: Optional[str] = None  # Agent ID to use for routing and phone number selection
    agent_personality: Optional[str] = None  # Agent personality name (e.g., "CUSTOMER_SUPPORT_AGENT")
    metadata: Dict[str, Any] = Field(default_factory=dict)


class EscalateRequest(BaseModel):
    """Schema for escalating a call"""
    agent_id: Optional[str] = None
    reason: Optional[str] = None
    context_note: Optional[str] = None


class InterveneRequest(BaseModel):
    """Schema for intervening in a call"""
    action: str = Field(..., pattern="^(send_message|pause|resume|override_instructions)$")
    message: Optional[str] = None
    instructions: Optional[str] = None


class EndCallRequest(BaseModel):
    """Schema for ending a call"""
    reason: Optional[str] = None
    notes: Optional[str] = None


class AddNoteRequest(BaseModel):
    """Schema for adding a note to a call"""
    note: str
    tags: List[str] = Field(default_factory=list)
    category: Optional[str] = None


class CallFilters(BaseModel):
    """Schema for call list filters"""
    page: int = Field(1, ge=1)
    limit: int = Field(50, ge=1, le=100)
    status: Optional[CallStatus] = None
    direction: Optional[CallDirection] = None
    business_id: Optional[str] = None
    from_date: Optional[str] = None
    to_date: Optional[str] = None
    search: Optional[str] = None
    sort_by: Optional[str] = Field(None, pattern="^(started_at|duration|qa_score)$")
    sort_order: Optional[str] = Field("desc", pattern="^(asc|desc)$")
    min_qa_score: Optional[float] = Field(None, ge=0.0, le=1.0)
    max_qa_score: Optional[float] = Field(None, ge=0.0, le=1.0)
    sentiment: Optional[str] = Field(None, pattern="^(positive|neutral|negative)$")


class AssignedAgent(BaseModel):
    """Schema for assigned agent info"""
    id: str
    name: str


class CallResponse(BaseModel):
    """Schema for call response with computed fields"""
    id: str
    twilio_call_sid: str
    direction: CallDirection
    status: CallStatus
    from_number: str
    to_number: str
    business_id: Optional[str] = None
    template_id: Optional[str] = None
    started_at: datetime
    ended_at: Optional[datetime] = None
    duration_seconds: Optional[float] = None
    created_at: datetime
    updated_at: datetime
    metadata: Dict[str, Any] = Field(default_factory=dict)
    # Computed fields
    qa_score: Optional[float] = None
    sentiment: Optional[str] = None
    escalation_status: Optional[EscalationStatus] = None
    assigned_agent: Optional[AssignedAgent] = None

    class Config:
        from_attributes = True


class CallInteractionResponse(BaseModel):
    """Schema for call interaction response"""
    id: int
    call_id: str
    speaker: str
    text: str
    audio_url: Optional[str] = None
    timestamp: datetime
    metadata: Dict[str, Any] = Field(default_factory=dict)
    # Computed fields
    sentiment: Optional[Dict[str, Any]] = None

    class Config:
        from_attributes = True


class Pagination(BaseModel):
    """Schema for pagination info"""
    page: int
    limit: int
    total: int
    total_pages: int
    has_next: bool
    has_prev: bool


class CallsListResponse(BaseModel):
    """Schema for calls list response"""
    calls: List[CallResponse]
    pagination: Pagination


class InteractionsResponse(BaseModel):
    """Schema for interactions response"""
    interactions: List[CallInteractionResponse]
    total: int

