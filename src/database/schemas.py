"""Pydantic schemas for API validation"""

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field, EmailStr


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


# Call Schemas
class CallBase(BaseModel):
    """Base call schema"""
    direction: CallDirection
    from_number: str
    to_number: str
    business_id: Optional[str] = None
    template_id: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)


class CallCreate(CallBase):
    """Schema for creating a call"""
    pass


class CallResponse(CallBase):
    """Schema for call response"""
    id: str
    twilio_call_sid: Optional[str] = None
    status: CallStatus
    started_at: datetime
    ended_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# Call Interaction Schemas
class CallInteractionBase(BaseModel):
    """Base call interaction schema"""
    speaker: str
    text: str
    audio_url: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)


class CallInteractionCreate(CallInteractionBase):
    """Schema for creating a call interaction"""
    call_id: str


class CallInteractionResponse(CallInteractionBase):
    """Schema for call interaction response"""
    id: int
    call_id: str
    timestamp: datetime
    created_at: datetime

    class Config:
        from_attributes = True


# Call Note Schemas
class CallNoteBase(BaseModel):
    """Base call note schema"""
    note: str
    tags: List[str] = Field(default_factory=list)
    category: Optional[str] = None


class CallNoteCreate(CallNoteBase):
    """Schema for creating a call note"""
    pass


class CallNoteUpdate(BaseModel):
    """Schema for updating a call note"""
    note: Optional[str] = None
    tags: Optional[List[str]] = None
    category: Optional[str] = None


class CallNoteResponse(CallNoteBase):
    """Schema for call note response"""
    id: int
    call_id: str
    created_by_user_id: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# Business Config Schemas
class BusinessConfigBase(BaseModel):
    """Base business config schema"""
    name: str
    type: str
    config_data: Dict[str, Any]


class BusinessConfigCreate(BusinessConfigBase):
    """Schema for creating a business config"""
    pass


class BusinessConfigResponse(BusinessConfigBase):
    """Schema for business config response"""
    id: str
    is_active: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# Knowledge Entry Schemas
class KnowledgeEntryBase(BaseModel):
    """Base knowledge entry schema"""
    title: str
    content: str
    source: Optional[str] = None
    source_type: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)


class KnowledgeEntryCreate(KnowledgeEntryBase):
    """Schema for creating a knowledge entry"""
    business_id: Optional[str] = None


class KnowledgeEntryResponse(KnowledgeEntryBase):
    """Schema for knowledge entry response"""
    id: int
    business_id: Optional[str] = None
    vector_id: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# QA Score Schemas
class QAScoreBase(BaseModel):
    """Base QA score schema"""
    overall_score: float = Field(ge=0.0, le=1.0)
    sentiment_score: Optional[float] = Field(None, ge=-1.0, le=1.0)
    compliance_score: Optional[float] = Field(None, ge=0.0, le=1.0)
    accuracy_score: Optional[float] = Field(None, ge=0.0, le=1.0)
    professionalism_score: Optional[float] = Field(None, ge=0.0, le=1.0)
    sentiment_label: Optional[str] = None
    compliance_issues: List[str] = Field(default_factory=list)
    flagged_issues: List[str] = Field(default_factory=list)
    review_notes: Optional[str] = None


class QAScoreCreate(QAScoreBase):
    """Schema for creating a QA score"""
    call_id: str
    reviewed_by: Optional[str] = "auto"


class QAScoreResponse(QAScoreBase):
    """Schema for QA score response"""
    id: int
    call_id: str
    reviewed_by: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# Escalation Schemas
class EscalationStatus(str, Enum):
    """Escalation status enumeration"""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class EscalationBase(BaseModel):
    """Base escalation schema"""
    trigger_type: str
    trigger_details: Dict[str, Any] = Field(default_factory=dict)
    conversation_summary: Optional[str] = None
    context_data: Dict[str, Any] = Field(default_factory=dict)


class EscalationCreate(EscalationBase):
    """Schema for creating an escalation"""
    call_id: str


class EscalationResponse(EscalationBase):
    """Schema for escalation response"""
    id: int
    call_id: str
    status: EscalationStatus
    assigned_agent_id: Optional[str] = None
    agent_name: Optional[str] = None
    requested_at: datetime
    accepted_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# User Schemas
class UserBase(BaseModel):
    """Base user schema"""
    email: EmailStr
    name: str


class UserCreate(UserBase):
    """Schema for creating a user"""
    password: str = Field(..., min_length=8)


class UserResponse(UserBase):
    """Schema for user response"""
    id: str
    is_active: bool
    is_superuser: bool
    created_at: datetime
    updated_at: datetime
    last_login_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class UserLogin(BaseModel):
    """Schema for user login"""
    email: EmailStr
    password: str


class Token(BaseModel):
    """Schema for authentication token"""
    access_token: str
    token_type: str = "bearer"
    user: UserResponse


class TokenRefresh(BaseModel):
    """Schema for token refresh"""
    refresh_token: str


# Human Agent Schemas
class HumanAgentBase(BaseModel):
    """Base human agent schema"""
    name: str
    email: EmailStr
    phone_number: Optional[str] = None
    extension: Optional[str] = None
    skills: List[str] = Field(default_factory=list)
    departments: List[str] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)


class HumanAgentCreate(HumanAgentBase):
    """Schema for creating a human agent"""
    pass


class HumanAgentResponse(HumanAgentBase):
    """Schema for human agent response"""
    id: str
    is_available: bool
    is_active: bool
    total_calls_handled: int
    average_rating: Optional[float] = None
    created_at: datetime
    updated_at: datetime
    last_active_at: Optional[datetime] = None

    class Config:
        from_attributes = True


# Phone Number Schemas
class PhoneNumberBase(BaseModel):
    """Base phone number schema"""
    phone_number: str
    friendly_name: Optional[str] = None
    country_code: str
    region: Optional[str] = None
    capabilities: Dict[str, Any] = Field(default_factory=dict)
    webhook_url: Optional[str] = None
    webhook_method: str = "POST"
    is_active: bool = True
    metadata: Dict[str, Any] = Field(default_factory=dict)


class PhoneNumberCreate(PhoneNumberBase):
    """Schema for creating a phone number"""
    twilio_phone_sid: Optional[str] = None
    status: str = "active"


class PhoneNumberUpdate(BaseModel):
    """Schema for updating a phone number"""
    friendly_name: Optional[str] = None
    webhook_url: Optional[str] = None
    webhook_method: Optional[str] = None
    is_active: Optional[bool] = None
    metadata: Optional[Dict[str, Any]] = None


class PhoneNumberResponse(PhoneNumberBase):
    """Schema for phone number response"""
    id: str
    twilio_phone_sid: Optional[str] = None
    status: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class PhoneNumberSearchRequest(BaseModel):
    """Schema for searching available phone numbers"""
    country_code: str = "US"
    area_code: Optional[str] = None
    capabilities: Optional[List[str]] = None
    limit: int = 20


class PhoneNumberPurchaseRequest(BaseModel):
    """Schema for purchasing a phone number"""
    phone_number: str


class PhoneNumberAssignmentRequest(BaseModel):
    """Schema for assigning phone number to agent/business"""
    is_primary: bool = False

