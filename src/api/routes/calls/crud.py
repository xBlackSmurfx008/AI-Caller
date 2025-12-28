"""Core CRUD operations for calls"""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import or_, func
from typing import Optional
import math

from src.database.database import get_db
from src.database.models import (
    Call, CallInteraction, CallStatus, CallDirection,
    QAScore, Escalation, HumanAgent, BusinessConfig
)
from src.api.schemas.calls import (
    CallResponse,
    CallsListResponse,
    InteractionsResponse,
    CallInteractionResponse,
    Pagination,
    AssignedAgent,
)
from src.api.utils import handle_service_errors_sync
from src.utils.logging import get_logger
from .utils import parse_date, call_to_response

logger = get_logger(__name__)
router = APIRouter()


@router.get("/", response_model=CallsListResponse)
@handle_service_errors_sync
def list_calls(
    page: int = Query(1, ge=1),
    limit: int = Query(50, ge=1, le=100),
    status: Optional[str] = Query(None),
    direction: Optional[str] = Query(None),
    business_id: Optional[str] = Query(None),
    from_date: Optional[str] = Query(None),
    to_date: Optional[str] = Query(None),
    search: Optional[str] = Query(None),
    sort_by: Optional[str] = Query("started_at", pattern="^(started_at|duration|qa_score)$"),
    sort_order: Optional[str] = Query("desc", pattern="^(asc|desc)$"),
    min_qa_score: Optional[float] = Query(None, ge=0.0, le=1.0),
    max_qa_score: Optional[float] = Query(None, ge=0.0, le=1.0),
    sentiment: Optional[str] = Query(None, pattern="^(positive|neutral|negative)$"),
    db: Session = Depends(get_db),
):
    """List calls with filtering, sorting, and pagination"""
    query = db.query(Call)
    
    # Status filter
    if status:
        try:
            call_status = CallStatus(status)
            query = query.filter(Call.status == call_status)
        except ValueError as e:
            logger.warning("invalid_call_status", status=status, error=str(e))
            # Invalid status value, skip filter
    
    # Direction filter
    if direction:
        try:
            call_direction = CallDirection(direction)
            query = query.filter(Call.direction == call_direction)
        except ValueError as e:
            logger.warning("invalid_call_direction", direction=direction, error=str(e))
            # Invalid direction value, skip filter
    
    # Business ID filter
    if business_id:
        query = query.filter(Call.business_id == business_id)
    
    # Date range filter
    if from_date:
        start_date = parse_date(from_date)
        if start_date:
            query = query.filter(Call.started_at >= start_date)
    
    if to_date:
        end_date = parse_date(to_date)
        if end_date:
            query = query.filter(Call.started_at <= end_date)
    
    # Search filter (phone numbers or call ID)
    if search:
        search_filter = or_(
            Call.from_number.contains(search),
            Call.to_number.contains(search),
            Call.id.like(f"%{search}%"),
            Call.twilio_call_sid.contains(search),
        )
        query = query.filter(search_filter)
    
    # QA score filter
    if min_qa_score is not None or max_qa_score is not None or sentiment:
        qa_subquery = db.query(QAScore.call_id, QAScore.overall_score, QAScore.sentiment_label).subquery()
        query = query.outerjoin(qa_subquery, Call.id == qa_subquery.c.call_id)
        
        if min_qa_score is not None:
            query = query.filter(qa_subquery.c.overall_score >= min_qa_score)
        if max_qa_score is not None:
            query = query.filter(qa_subquery.c.overall_score <= max_qa_score)
        if sentiment:
            query = query.filter(qa_subquery.c.sentiment_label == sentiment)
    
    # Get total count before pagination
    total = query.count()
    
    # Sorting
    if sort_by == "duration":
        # Sort by computed duration (requires subquery or post-processing)
        query = query.order_by(Call.started_at.desc() if sort_order == "desc" else Call.started_at.asc())
    elif sort_by == "qa_score":
        # Join with QA scores for sorting
        qa_subquery = db.query(
            QAScore.call_id,
            func.max(QAScore.overall_score).label('max_score')
        ).group_by(QAScore.call_id).subquery()
        query = query.outerjoin(qa_subquery, Call.id == qa_subquery.c.call_id)
        if sort_order == "desc":
            query = query.order_by(qa_subquery.c.max_score.desc().nullslast())
        else:
            query = query.order_by(qa_subquery.c.max_score.asc().nullslast())
    else:  # started_at (default)
        if sort_order == "desc":
            query = query.order_by(Call.started_at.desc())
        else:
            query = query.order_by(Call.started_at.asc())
    
    # Pagination
    offset = (page - 1) * limit
    calls = query.offset(offset).limit(limit).all()
    
    # Optimize: Preload related data to avoid N+1 queries
    call_ids = [call.id for call in calls]
    
    # Get all QA scores for these calls in one query
    qa_scores_map = {}
    if call_ids:
        # Get all QA scores for these calls, then filter to latest per call
        all_qa_scores = db.query(QAScore).filter(
            QAScore.call_id.in_(call_ids)
        ).order_by(QAScore.call_id, QAScore.created_at.desc()).all()
        
        # Group by call_id and take the first (latest) for each
        for qa_score in all_qa_scores:
            if qa_score.call_id not in qa_scores_map:
                qa_scores_map[qa_score.call_id] = {
                    'qa_score': qa_score.overall_score,
                    'sentiment': qa_score.sentiment_label
                }
    
    # Get all escalations for these calls in one query
    escalations_map = {}
    agents_map = {}
    if call_ids:
        escalations = db.query(Escalation).filter(
            Escalation.call_id.in_(call_ids)
        ).order_by(Escalation.created_at.desc()).all()
        
        # Group by call_id and get latest
        for esc in escalations:
            if esc.call_id not in escalations_map:
                escalations_map[esc.call_id] = esc
                if esc.assigned_agent_id:
                    agents_map[esc.call_id] = esc.assigned_agent_id
        
        # Load agents in one query
        agent_ids = list(set(agents_map.values()))
        if agent_ids:
            agents = db.query(HumanAgent).filter(HumanAgent.id.in_(agent_ids)).all()
            agents_by_id = {agent.id: agent for agent in agents}
        else:
            agents_by_id = {}
    
    # Convert to response format with preloaded data
    call_responses = []
    for call in calls:
        preloaded = {}
        if call.id in qa_scores_map:
            preloaded.update(qa_scores_map[call.id])
        
        if call.id in escalations_map:
            esc = escalations_map[call.id]
            preloaded['escalation_status'] = esc.status.value
            if esc.assigned_agent_id and esc.assigned_agent_id in agents_by_id:
                agent = agents_by_id[esc.assigned_agent_id]
                preloaded['assigned_agent'] = AssignedAgent(id=agent.id, name=agent.name)
        
        call_responses.append(CallResponse.model_validate(call_to_response(call, db, preloaded)))
    
    total_pages = math.ceil(total / limit) if limit > 0 else 1
    
    return CallsListResponse(
        calls=call_responses,
        pagination=Pagination(
            page=page,
            limit=limit,
            total=total,
            total_pages=total_pages,
            has_next=page < total_pages,
            has_prev=page > 1,
        )
    )


@router.get("/{call_id}")
@handle_service_errors_sync
def get_call(
    call_id: str,
    db: Session = Depends(get_db),
):
    """Get call details"""
    call = db.query(Call).filter(Call.id == call_id).first()
    
    if not call:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Call with ID {call_id} not found"
        )
    
    # Preload related data to avoid N+1 queries
    preloaded = {}
    
    # Get latest QA score
    latest_qa = db.query(QAScore).filter(QAScore.call_id == call_id).order_by(QAScore.created_at.desc()).first()
    if latest_qa:
        preloaded['qa_score'] = latest_qa.overall_score
        preloaded['sentiment'] = latest_qa.sentiment_label
    
    # Get latest escalation
    latest_escalation = db.query(Escalation).filter(Escalation.call_id == call_id).order_by(Escalation.created_at.desc()).first()
    if latest_escalation:
        preloaded['escalation_status'] = latest_escalation.status.value
        if latest_escalation.assigned_agent_id:
            agent = db.query(HumanAgent).filter(HumanAgent.id == latest_escalation.assigned_agent_id).first()
            if agent:
                preloaded['assigned_agent'] = AssignedAgent(id=agent.id, name=agent.name)
    
    return {"call": CallResponse.model_validate(call_to_response(call, db, preloaded))}


@router.get("/{call_id}/interactions", response_model=InteractionsResponse)
@handle_service_errors_sync
def get_call_interactions(
    call_id: str,
    limit: int = Query(1000, ge=1, le=10000),
    offset: int = Query(0, ge=0),
    speaker: Optional[str] = Query(None, pattern="^(ai|customer)$"),
    db: Session = Depends(get_db),
):
    """Get call interactions (transcript)"""
    call = db.query(Call).filter(Call.id == call_id).first()
    
    if not call:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Call with ID {call_id} not found"
        )
    
    query = db.query(CallInteraction).filter(CallInteraction.call_id == call_id)
    
    if speaker:
        query = query.filter(CallInteraction.speaker == speaker)
    
    total = query.count()
    interactions = query.order_by(CallInteraction.timestamp.asc()).offset(offset).limit(limit).all()
    
    interaction_responses = [
        CallInteractionResponse(
            id=interaction.id,
            call_id=interaction.call_id,
            speaker=interaction.speaker,
            text=interaction.text,
            audio_url=interaction.audio_url,
            timestamp=interaction.timestamp,
            metadata=interaction.meta_data or {},
            sentiment=None,  # Could be computed from metadata
        )
        for interaction in interactions
    ]
    
    return InteractionsResponse(
        interactions=interaction_responses,
        total=total,
    )

