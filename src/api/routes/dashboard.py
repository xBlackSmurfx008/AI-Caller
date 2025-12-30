"""Dashboard API routes for relationship intelligence and network views"""

from fastapi import APIRouter, HTTPException, Depends, status
from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any
from pydantic import BaseModel
from datetime import datetime, timedelta

from src.database.database import get_db
from src.database.models import Contact, ContactMemoryState, Commitment, Suggestion, Project
from src.utils.logging import get_logger

router = APIRouter()
logger = get_logger(__name__)


class RelationshipDashboardResponse(BaseModel):
    contact_id: str
    contact_name: str
    relationship_score: float
    sentiment_trend: Optional[str] = None
    last_interaction_at: Optional[str] = None
    days_since_last_interaction: Optional[int] = None
    open_commitments: int
    pending_suggestions: int
    next_recommended_action: Optional[Dict[str, Any]] = None


@router.get("/contacts/{contact_id}/relationship-dashboard", response_model=RelationshipDashboardResponse)
async def get_relationship_dashboard(
    contact_id: str,
    db: Session = Depends(get_db)
):
    """Get relationship dashboard for a specific contact"""
    contact = db.query(Contact).filter(Contact.id == contact_id).first()
    if not contact:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Contact not found"
        )
    
    memory_state = db.query(ContactMemoryState).filter(
        ContactMemoryState.contact_id == contact_id
    ).first()
    
    # Count open commitments
    open_commitments = db.query(Commitment).filter(
        Commitment.contact_id == contact_id,
        Commitment.status.in_(["pending", "overdue"])
    ).count()
    
    # Count pending suggestions
    pending_suggestions = db.query(Suggestion).filter(
        Suggestion.contact_id == contact_id,
        Suggestion.status == "pending"
    ).count()
    
    # Get top suggestion
    top_suggestion = db.query(Suggestion).filter(
        Suggestion.contact_id == contact_id,
        Suggestion.status == "pending"
    ).order_by(Suggestion.score.desc()).first()
    
    next_action = None
    if top_suggestion:
        next_action = {
            "suggestion_id": top_suggestion.id,
            "type": top_suggestion.suggestion_type,
            "intent": top_suggestion.intent,
            "best_timing": top_suggestion.best_timing,
            "message_draft": top_suggestion.message_draft
        }
    
    days_since = None
    if memory_state and memory_state.last_interaction_at:
        days_since = (datetime.utcnow() - memory_state.last_interaction_at).days
    
    return RelationshipDashboardResponse(
        contact_id=contact.id,
        contact_name=contact.name,
        relationship_score=contact.relationship_score or 0.0,
        sentiment_trend=memory_state.sentiment_trend if memory_state else None,
        last_interaction_at=memory_state.last_interaction_at.isoformat() if memory_state and memory_state.last_interaction_at else None,
        days_since_last_interaction=days_since,
        open_commitments=open_commitments,
        pending_suggestions=pending_suggestions,
        next_recommended_action=next_action
    )


@router.get("/network-heatmap")
async def get_network_heatmap(
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """Get network heatmap data for visualization"""
    contacts = db.query(Contact).filter(
        Contact.is_sensitive == False
    ).limit(limit).all()
    
    heatmap_data = []
    for contact in contacts:
        memory_state = db.query(ContactMemoryState).filter(
            ContactMemoryState.contact_id == contact.id
        ).first()
        
        # Count connections (stakeholders in same projects)
        project_count = db.query(Project).join(
            "stakeholders"
        ).filter(
            Project.stakeholders.any(contact_id=contact.id)
        ).count()
        
        # Count active suggestions
        suggestion_count = db.query(Suggestion).filter(
            Suggestion.contact_id == contact.id,
            Suggestion.status == "pending"
        ).count()
        
        heatmap_data.append({
            "contact_id": contact.id,
            "contact_name": contact.name,
            "organization": contact.organization,
            "location": contact.location,
            "industries": contact.industries or [],
            "relationship_score": contact.relationship_score or 0.0,
            "sentiment_trend": memory_state.sentiment_trend if memory_state else None,
            "project_count": project_count,
            "suggestion_count": suggestion_count,
            "last_interaction": memory_state.last_interaction_at.isoformat() if memory_state and memory_state.last_interaction_at else None
        })
    
    return {
        "contacts": heatmap_data,
        "total_contacts": len(heatmap_data),
        "generated_at": datetime.utcnow().isoformat()
    }


@router.get("/projects/{project_id}/collaboration-plan")
async def get_collaboration_plan(
    project_id: str,
    db: Session = Depends(get_db)
):
    """Get detailed collaboration plan for a project"""
    from src.orchestrator.orchestrator_service import OrchestratorService
    
    orchestrator = OrchestratorService()
    
    try:
        project_context = orchestrator.get_project_context(db, project_id)
        network_opportunities = orchestrator.identify_network_opportunities(db, project_id, limit=10)
        
        # Get commitments related to this project
        commitments = db.query(Commitment).filter(
            Commitment.project_id == project_id
        ).all()
        
        # Get suggestions related to this project
        suggestions = db.query(Suggestion).filter(
            Suggestion.project_id == project_id,
            Suggestion.status == "pending"
        ).order_by(Suggestion.score.desc()).all()
        
        return {
            "project": {
                "id": project_context["project_id"],
                "title": project_context["title"],
                "description": project_context["description"],
                "status": project_context["status"],
                "milestones": project_context["milestones"]
            },
            "current_stakeholders": project_context["stakeholders"],
            "network_opportunities": network_opportunities,
            "commitments": [
                {
                    "id": c.id,
                    "description": c.description,
                    "committed_by": c.committed_by,
                    "deadline": c.deadline.isoformat() if c.deadline else None,
                    "status": c.status,
                    "is_trust_risk": c.is_trust_risk
                }
                for c in commitments
            ],
            "suggestions": [
                {
                    "id": s.id,
                    "type": s.suggestion_type,
                    "intent": s.intent,
                    "contact_id": s.contact_id,
                    "best_timing": s.best_timing,
                    "score": s.score
                }
                for s in suggestions
            ],
            "recommended_actions": [
                {
                    "action": "Add stakeholder",
                    "description": f"Consider adding {opp['contact_name']} as stakeholder",
                    "contact_id": opp["contact_id"],
                    "fit_score": opp["fit_score"]
                }
                for opp in network_opportunities[:5]
            ]
        }
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )

