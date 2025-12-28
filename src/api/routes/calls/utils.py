"""Utility functions for call routes"""

from typing import Optional, Dict, Any
from datetime import datetime
from sqlalchemy.orm import Session

from src.database.models import Call, QAScore, Escalation, HumanAgent
from src.api.schemas.calls import AssignedAgent


def parse_date(date_str: Optional[str]) -> Optional[datetime]:
    """Parse ISO 8601 date string"""
    if not date_str:
        return None
    try:
        return datetime.fromisoformat(date_str.replace('Z', '+00:00'))
    except ValueError:
        return None


def call_to_response(
    call: Call,
    db: Session,
    preloaded_data: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Convert call model to response format with computed fields.
    
    Args:
        call: Call model instance
        db: Database session
        preloaded_data: Optional preloaded data to avoid N+1 queries
                       Should contain 'qa_score', 'sentiment', 'escalation', 'agent'
    """
    # Calculate duration
    duration_seconds = None
    if call.ended_at and call.started_at:
        duration_seconds = (call.ended_at - call.started_at).total_seconds()
    
    # Use preloaded data if available, otherwise query
    if preloaded_data:
        qa_score = preloaded_data.get('qa_score')
        sentiment = preloaded_data.get('sentiment')
        escalation_status = preloaded_data.get('escalation_status')
        assigned_agent = preloaded_data.get('assigned_agent')
    else:
        # Get latest QA score
        qa_score = None
        sentiment = None
        latest_qa = db.query(QAScore).filter(QAScore.call_id == call.id).order_by(QAScore.created_at.desc()).first()
        if latest_qa:
            qa_score = latest_qa.overall_score
            sentiment = latest_qa.sentiment_label
        
        # Get latest escalation
        escalation_status = None
        assigned_agent = None
        latest_escalation = db.query(Escalation).filter(Escalation.call_id == call.id).order_by(Escalation.created_at.desc()).first()
        if latest_escalation:
            escalation_status = latest_escalation.status.value
            if latest_escalation.assigned_agent_id:
                agent = db.query(HumanAgent).filter(HumanAgent.id == latest_escalation.assigned_agent_id).first()
                if agent:
                    assigned_agent = AssignedAgent(id=agent.id, name=agent.name)
    
    return {
        "id": call.id,
        "twilio_call_sid": call.twilio_call_sid,
        "direction": call.direction.value,
        "status": call.status.value,
        "from_number": call.from_number,
        "to_number": call.to_number,
        "business_id": call.business_id,
        "template_id": call.template_id,
        "started_at": call.started_at.isoformat(),
        "ended_at": call.ended_at.isoformat() if call.ended_at else None,
        "duration_seconds": duration_seconds,
        "created_at": call.created_at.isoformat(),
        "updated_at": call.updated_at.isoformat(),
        "metadata": call.meta_data or {},
        "qa_score": qa_score,
        "sentiment": sentiment,
        "escalation_status": escalation_status,
        "assigned_agent": assigned_agent.dict() if assigned_agent else None,
    }

