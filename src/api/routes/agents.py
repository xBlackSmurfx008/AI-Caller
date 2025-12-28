"""Agent management routes"""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import Optional, List
from pydantic import BaseModel
import uuid

from src.database.database import get_db
from src.database.models import HumanAgent, Escalation, EscalationStatus, Call, CallStatus
from src.database.schemas import HumanAgentCreate, HumanAgentResponse
from src.api.utils import handle_service_errors_sync
from src.utils.logging import get_logger

logger = get_logger(__name__)
router = APIRouter()


class AvailabilityUpdate(BaseModel):
    """Schema for availability update"""
    is_available: bool


def agent_to_response(agent: HumanAgent) -> dict:
    """Convert agent model to response format"""
    return {
        "id": agent.id,
        "name": agent.name,
        "email": agent.email,
        "phone_number": agent.phone_number,
        "extension": agent.extension,
        "is_available": agent.is_available,
        "is_active": agent.is_active,
        "skills": agent.skills or [],
        "departments": agent.departments or [],
        "total_calls_handled": agent.total_calls_handled,
        "average_rating": agent.average_rating,
        "created_at": agent.created_at.isoformat(),
        "updated_at": agent.updated_at.isoformat(),
        "last_active_at": agent.last_active_at.isoformat() if agent.last_active_at else None,
        "metadata": agent.meta_data or {},
    }


@router.get("/")
@handle_service_errors_sync
def list_agents(
    is_active: Optional[bool] = Query(None),
    is_available: Optional[bool] = Query(None),
    db: Session = Depends(get_db),
):
    """List all agents with optional filtering"""
    query = db.query(HumanAgent)
    
    if is_active is not None:
        query = query.filter(HumanAgent.is_active == is_active)
    
    if is_available is not None:
        query = query.filter(HumanAgent.is_available == is_available)
    
    agents = query.all()
    return {"agents": [HumanAgentResponse.model_validate(agent) for agent in agents]}


@router.get("/{agent_id}")
@handle_service_errors_sync
def get_agent(
    agent_id: str,
    db: Session = Depends(get_db),
):
    """Get a specific agent by ID"""
    agent = db.query(HumanAgent).filter(HumanAgent.id == agent_id).first()
    
    if not agent:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Agent with ID {agent_id} not found"
        )
    
    return {"agent": HumanAgentResponse.model_validate(agent)}


@router.post("/", status_code=status.HTTP_201_CREATED)
@handle_service_errors_sync
def create_agent(
    agent_data: HumanAgentCreate,
    db: Session = Depends(get_db),
):
    """Create a new agent"""
    # Check if email already exists
    existing = db.query(HumanAgent).filter(HumanAgent.email == agent_data.email).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Agent with email {agent_data.email} already exists"
        )
    
    # Create new agent
    agent = HumanAgent(
        id=str(uuid.uuid4()),
        name=agent_data.name,
        email=agent_data.email,
        phone_number=agent_data.phone_number,
        extension=agent_data.extension,
        skills=agent_data.skills or [],
        departments=agent_data.departments or [],
        is_available=agent_data.metadata.get("is_available", True) if agent_data.metadata else True,
        is_active=agent_data.metadata.get("is_active", True) if agent_data.metadata else True,
        meta_data=agent_data.metadata or {},
    )
    
    db.add(agent)
    db.commit()
    db.refresh(agent)
    
    logger.info("agent_created", agent_id=agent.id, email=agent.email)
    return {"agent": HumanAgentResponse.model_validate(agent)}


@router.put("/{agent_id}")
@handle_service_errors_sync
def update_agent(
    agent_id: str,
    agent_data: HumanAgentCreate,
    db: Session = Depends(get_db),
):
    """Update an existing agent"""
    agent = db.query(HumanAgent).filter(HumanAgent.id == agent_id).first()
    
    if not agent:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Agent with ID {agent_id} not found"
        )
    
    # Check if email is being changed and if new email already exists
    if agent_data.email != agent.email:
        existing = db.query(HumanAgent).filter(HumanAgent.email == agent_data.email).first()
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Agent with email {agent_data.email} already exists"
            )
    
    # Update agent fields
    agent.name = agent_data.name
    agent.email = agent_data.email
    agent.phone_number = agent_data.phone_number
    agent.extension = agent_data.extension
    agent.skills = agent_data.skills or []
    agent.departments = agent_data.departments or []
    
    # Update metadata if provided
    if agent_data.metadata:
        # Preserve existing metadata and update with new values
        current_meta = agent.meta_data or {}
        current_meta.update(agent_data.metadata)
        agent.meta_data = current_meta
    
    db.commit()
    db.refresh(agent)
    
    logger.info("agent_updated", agent_id=agent.id)
    return {"agent": HumanAgentResponse.model_validate(agent)}


@router.delete("/{agent_id}")
@handle_service_errors_sync
def delete_agent(
    agent_id: str,
    db: Session = Depends(get_db),
):
    """Delete an agent"""
    agent = db.query(HumanAgent).filter(HumanAgent.id == agent_id).first()
    
    if not agent:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Agent with ID {agent_id} not found"
        )
    
    # Check if agent has active escalations
    active_escalations = db.query(Escalation).filter(
        Escalation.assigned_agent_id == agent_id,
        Escalation.status.in_([EscalationStatus.PENDING, EscalationStatus.IN_PROGRESS])
    ).count()
    
    if active_escalations > 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot delete agent with {active_escalations} active escalation(s)"
        )
    
    db.delete(agent)
    db.commit()
    
    logger.info("agent_deleted", agent_id=agent_id)
    return {"message": "Agent deleted successfully"}


@router.patch("/{agent_id}/availability")
@handle_service_errors_sync
def update_agent_availability(
    agent_id: str,
    update_data: AvailabilityUpdate,
    db: Session = Depends(get_db),
):
    """Update agent availability status"""
    agent = db.query(HumanAgent).filter(HumanAgent.id == agent_id).first()
    
    if not agent:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Agent with ID {agent_id} not found"
        )
    
    agent.is_available = update_data.is_available
    if update_data.is_available:
        from datetime import datetime
        agent.last_active_at = datetime.utcnow()
    
    db.commit()
    db.refresh(agent)
    
    logger.info("agent_availability_updated", agent_id=agent.id, is_available=update_data.is_available)
    return {"agent": HumanAgentResponse.model_validate(agent)}


@router.get("/{agent_id}/usage")
@handle_service_errors_sync
def get_agent_usage(
    agent_id: str,
    db: Session = Depends(get_db),
):
    """Check agent usage before deletion"""
    agent = db.query(HumanAgent).filter(HumanAgent.id == agent_id).first()
    
    if not agent:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Agent with ID {agent_id} not found"
        )
    
    # Count active calls assigned to agent (via escalations)
    active_escalations = db.query(Escalation).filter(
        Escalation.assigned_agent_id == agent_id,
        Escalation.status.in_([EscalationStatus.PENDING, EscalationStatus.IN_PROGRESS])
    ).count()
    
    # Count active calls (calls that are escalated to this agent)
    active_calls = db.query(Call).join(Escalation).filter(
        Escalation.assigned_agent_id == agent_id,
        Call.status.in_([CallStatus.IN_PROGRESS, CallStatus.RINGING, CallStatus.ESCALATED]),
        Escalation.status.in_([EscalationStatus.PENDING, EscalationStatus.IN_PROGRESS])
    ).count()
    
    # Count total escalations handled by agent
    total_escalations = db.query(Escalation).filter(
        Escalation.assigned_agent_id == agent_id
    ).count()
    
    # Count total calls handled (via escalations)
    total_calls = db.query(Call).join(Escalation).filter(
        Escalation.assigned_agent_id == agent_id
    ).distinct(Call.id).count()
    
    return {
        "agent_id": agent_id,
        "is_in_use": active_escalations > 0 or active_calls > 0,
        "active_escalations": active_escalations,
        "active_calls": active_calls,
        "total_escalations": total_escalations,
        "total_calls": total_calls,
    }

