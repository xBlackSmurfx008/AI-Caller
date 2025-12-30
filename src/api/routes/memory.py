"""Memory API routes for accessing contact memory and interactions"""

from fastapi import APIRouter, HTTPException, Depends, status
from sqlalchemy.orm import Session
from typing import List, Optional
from pydantic import BaseModel
from datetime import datetime

from src.database.database import get_db
from src.database.models import Contact, Interaction, MemorySummary, ContactMemoryState
from src.memory.memory_service import MemoryService
from src.utils.logging import get_logger

router = APIRouter()
logger = get_logger(__name__)
memory_service = MemoryService()


class InteractionResponse(BaseModel):
    """Interaction response model"""
    id: str
    channel: str
    raw_content: str
    metadata: Optional[dict] = None
    created_at: str
    summary: Optional[dict] = None

    class Config:
        from_attributes = True


class PaginatedInteractionsResponse(BaseModel):
    """Paginated interactions response model"""
    items: List[InteractionResponse]
    total: int
    offset: int
    limit: int
    has_more: bool


class MemoryStateResponse(BaseModel):
    """Contact memory state response model"""
    contact_id: str
    latest_summary: Optional[str] = None
    sentiment_trend: Optional[str] = None
    active_goals: List[str] = []
    outstanding_actions: List[str] = []
    relationship_status: Optional[str] = None
    key_preferences: List[str] = []
    last_interaction_at: Optional[str] = None
    last_updated_at: str

    class Config:
        from_attributes = True


class ContactContextResponse(BaseModel):
    """Contact context response model"""
    has_memory: bool
    latest_summary: Optional[str] = None
    sentiment_trend: Optional[str] = None
    active_goals: List[str] = []
    outstanding_actions: List[str] = []
    relationship_status: Optional[str] = None
    key_preferences: List[str] = []
    last_interaction_at: Optional[str] = None
    recent_summaries: List[dict] = []


@router.get("/contacts/{contact_id}/context", response_model=ContactContextResponse)
async def get_contact_context(contact_id: str, db: Session = Depends(get_db)):
    """
    Get memory context for a contact to guide task execution
    
    Args:
        contact_id: Contact ID
        db: Database session
    
    Returns:
        Contact context with memory information
    """
    contact = db.query(Contact).filter(Contact.id == contact_id).first()
    if not contact:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Contact not found"
        )
    
    context = memory_service.get_contact_context(db, contact_id)
    return ContactContextResponse(**context)


@router.get("/contacts/{contact_id}/memory", response_model=MemoryStateResponse)
async def get_contact_memory(contact_id: str, db: Session = Depends(get_db)):
    """
    Get current memory state for a contact
    
    Args:
        contact_id: Contact ID
        db: Database session
    
    Returns:
        Contact memory state
    """
    contact = db.query(Contact).filter(Contact.id == contact_id).first()
    if not contact:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Contact not found"
        )
    
    memory_state = db.query(ContactMemoryState).filter(
        ContactMemoryState.contact_id == contact_id
    ).first()
    
    if not memory_state:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No memory found for this contact"
        )
    
    return MemoryStateResponse(
        contact_id=memory_state.contact_id,
        latest_summary=memory_state.latest_summary,
        sentiment_trend=memory_state.sentiment_trend,
        active_goals=memory_state.active_goals or [],
        outstanding_actions=memory_state.outstanding_actions or [],
        relationship_status=memory_state.relationship_status,
        key_preferences=memory_state.key_preferences or [],
        last_interaction_at=memory_state.last_interaction_at.isoformat() if memory_state.last_interaction_at else None,
        last_updated_at=memory_state.last_updated_at.isoformat() if memory_state.last_updated_at else datetime.utcnow().isoformat()
    )


@router.get("/contacts/{contact_id}/interactions", response_model=PaginatedInteractionsResponse)
async def get_contact_interactions(
    contact_id: str,
    limit: int = 50,
    offset: int = 0,
    channel: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """
    Get interactions for a contact
    
    Args:
        contact_id: Contact ID
        limit: Maximum number of interactions to return
        offset: Offset for pagination
        channel: Optional filter by channel ("email", "sms", "call")
        db: Database session
    
    Returns:
        Paginated list of interactions
    """
    contact = db.query(Contact).filter(Contact.id == contact_id).first()
    if not contact:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Contact not found"
        )
    
    query = db.query(Interaction).filter(Interaction.contact_id == contact_id)
    
    if channel:
        query = query.filter(Interaction.channel == channel)
    
    # Get total count
    total = query.count()
    
    # Get paginated results
    interactions = query.order_by(Interaction.created_at.desc()).offset(offset).limit(limit).all()
    
    results = []
    for interaction in interactions:
        summary = db.query(MemorySummary).filter(
            MemorySummary.interaction_id == interaction.id
        ).first()
        
        summary_data = None
        if summary:
            summary_data = {
                "summary": summary.summary,
                "sentiment_score": summary.sentiment_score,
                "sentiment_explanation": summary.sentiment_explanation,
                "key_facts": summary.key_facts,
                "godfather_goals": summary.godfather_goals,
                "commitments": summary.commitments,
                "next_actions": summary.next_actions,
                "preferences": summary.preferences
            }
        
        results.append(InteractionResponse(
            id=interaction.id,
            channel=interaction.channel,
            raw_content=interaction.raw_content,
            metadata=interaction.meta_data,
            created_at=interaction.created_at.isoformat(),
            summary=summary_data
        ))
    
    return PaginatedInteractionsResponse(
        items=results,
        total=total,
        offset=offset,
        limit=limit,
        has_more=offset + limit < total
    )


@router.get("/interactions", response_model=PaginatedInteractionsResponse)
async def get_all_interactions(
    limit: int = 100,
    offset: int = 0,
    channel: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """
    Get all interactions across all contacts (for message history)
    
    Args:
        limit: Maximum number of interactions to return
        offset: Offset for pagination
        channel: Optional filter by channel ("email", "sms", "call")
        db: Database session
    
    Returns:
        Paginated list of interactions with contact information
    """
    query = db.query(Interaction)
    
    if channel:
        query = query.filter(Interaction.channel == channel)
    else:
        # Default to email and SMS only (exclude calls for message history)
        query = query.filter(Interaction.channel.in_(["email", "sms"]))
    
    # Get total count before pagination
    total = query.count()
    
    # Get paginated results
    interactions = query.order_by(Interaction.created_at.desc()).offset(offset).limit(limit).all()
    
    results = []
    for interaction in interactions:
        # Get contact info
        contact = db.query(Contact).filter(Contact.id == interaction.contact_id).first()
        
        # Get summary if available
        summary = db.query(MemorySummary).filter(
            MemorySummary.interaction_id == interaction.id
        ).first()
        
        summary_data = None
        if summary:
            summary_data = {
                "summary": summary.summary,
                "sentiment_score": summary.sentiment_score,
                "sentiment_explanation": summary.sentiment_explanation,
                "key_facts": summary.key_facts,
                "godfather_goals": summary.godfather_goals,
                "commitments": summary.commitments,
                "next_actions": summary.next_actions,
                "preferences": summary.preferences
            }
        
        # Add contact info to metadata
        interaction_metadata = (interaction.meta_data or {}).copy()
        if contact:
            interaction_metadata["contact_name"] = contact.name
            interaction_metadata["contact_id"] = contact.id
        
        results.append(InteractionResponse(
            id=interaction.id,
            channel=interaction.channel,
            raw_content=interaction.raw_content,
            metadata=interaction_metadata,
            created_at=interaction.created_at.isoformat(),
            summary=summary_data
        ))
    
    return PaginatedInteractionsResponse(
        items=results,
        total=total,
        offset=offset,
        limit=limit,
        has_more=offset + limit < total
    )


@router.post("/contacts/{contact_id}/interactions/{interaction_id}/summarize")
async def trigger_summary_generation(
    contact_id: str,
    interaction_id: str,
    db: Session = Depends(get_db)
):
    """
    Manually trigger summary generation for an interaction
    
    Args:
        contact_id: Contact ID
        interaction_id: Interaction ID
        db: Database session
    
    Returns:
        Success message
    """
    contact = db.query(Contact).filter(Contact.id == contact_id).first()
    if not contact:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Contact not found"
        )
    
    interaction = db.query(Interaction).filter(
        Interaction.id == interaction_id,
        Interaction.contact_id == contact_id
    ).first()
    
    if not interaction:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Interaction not found"
        )
    
    # Check if summary already exists
    existing_summary = db.query(MemorySummary).filter(
        MemorySummary.interaction_id == interaction_id
    ).first()
    
    if existing_summary:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Summary already exists for this interaction"
        )
    
    try:
        memory_service.generate_summary(db, interaction_id, contact.name)
        return {"success": True, "message": "Summary generated successfully"}
    except Exception as e:
        logger.error("manual_summary_generation_failed", error=str(e), interaction_id=interaction_id)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate summary: {str(e)}"
        )

