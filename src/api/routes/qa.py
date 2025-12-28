"""Quality assurance routes"""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import func, and_
from typing import Optional, List
from datetime import datetime, timedelta

from src.database.database import get_db
from src.database.models import QAScore, Call
from src.database.schemas import QAScoreResponse
from src.api.utils import handle_service_errors_sync
from src.utils.logging import get_logger

logger = get_logger(__name__)
router = APIRouter()


def parse_date(date_str: Optional[str]) -> Optional[datetime]:
    """Parse ISO 8601 date string"""
    if not date_str:
        return None
    try:
        return datetime.fromisoformat(date_str.replace('Z', '+00:00'))
    except ValueError:
        return None


@router.get("/scores/{call_id}")
@handle_service_errors_sync
def get_qa_score(
    call_id: str,
    db: Session = Depends(get_db),
):
    """Get QA score for a call"""
    call = db.query(Call).filter(Call.id == call_id).first()
    
    if not call:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Call {call_id} not found"
        )
    
    # Get latest QA score for the call
    qa_score = db.query(QAScore).filter(QAScore.call_id == call_id).order_by(QAScore.created_at.desc()).first()
    
    if not qa_score:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"QA score not found for call {call_id}"
        )
    
    return {"qa_scores": QAScoreResponse.model_validate(qa_score)}


@router.get("/reports")
@handle_service_errors_sync
def get_qa_reports(
    from_date: Optional[str] = Query(None),
    to_date: Optional[str] = Query(None),
    business_id: Optional[str] = Query(None),
    min_score: Optional[float] = Query(None, ge=0.0, le=1.0),
    max_score: Optional[float] = Query(None, ge=0.0, le=1.0),
    db: Session = Depends(get_db),
):
    """Get QA reports with filtering"""
    
    query = db.query(QAScore).join(Call).filter(
        Call.business_id.in_(db.query(user_business_ids))
    )
    
    # Date range filter
    if from_date:
        start_date = parse_date(from_date)
        if start_date:
            query = query.filter(Call.started_at >= start_date)
    
    if to_date:
        end_date = parse_date(to_date)
        if end_date:
            query = query.filter(Call.started_at <= end_date)
    
    # Business ID filter
    if business_id:
        # Verify business_id belongs to user
        business = db.query(BusinessConfig).filter(
            BusinessConfig.id == business_id,
            BusinessConfig.created_by_user_id == current_user.id
        ).first()
        if business:
            query = query.filter(Call.business_id == business_id)
    
    # Score range filter
    if min_score is not None:
        query = query.filter(QAScore.overall_score >= min_score)
    if max_score is not None:
        query = query.filter(QAScore.overall_score <= max_score)
    
    # Get reports (latest QA score per call)
    qa_scores = query.order_by(QAScore.created_at.desc()).all()
    
    # Group by call_id to get latest per call
    latest_scores = {}
    for score in qa_scores:
        if score.call_id not in latest_scores:
            latest_scores[score.call_id] = score
    
    reports = [QAScoreResponse.model_validate(score) for score in latest_scores.values()]
    
    return {"reports": reports}
