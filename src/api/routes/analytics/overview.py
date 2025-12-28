"""Overview metrics endpoint"""

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import Optional

from src.database.database import get_db
from src.database.models import Call, CallStatus, QAScore
from src.api.schemas.analytics import OverviewMetrics
from src.api.utils import handle_service_errors_sync
from src.utils.logging import get_logger
from .utils import get_date_range

logger = get_logger(__name__)
router = APIRouter()


@router.get("/overview", response_model=OverviewMetrics)
@handle_service_errors_sync
def get_overview(
    from_date: Optional[str] = Query(None),
    to_date: Optional[str] = Query(None),
    business_id: Optional[str] = Query(None),
    db: Session = Depends(get_db),
):
    """Get overview metrics for dashboard"""
    start_date, end_date = get_date_range(from_date, to_date, 7)
    
    # Base query
    query = db.query(Call).filter(
        Call.started_at >= start_date,
        Call.started_at <= end_date
    )
    
    if business_id:
        query = query.filter(Call.business_id == business_id)
    
    # Total calls
    total_calls = query.count()
    
    # Status counts
    active_calls = query.filter(Call.status.in_([CallStatus.IN_PROGRESS, CallStatus.RINGING])).count()
    completed_calls = query.filter(Call.status == CallStatus.COMPLETED).count()
    failed_calls = query.filter(Call.status == CallStatus.FAILED).count()
    escalated_calls = query.filter(Call.status == CallStatus.ESCALATED).count()
    
    # Average QA score
    qa_query = db.query(func.avg(QAScore.overall_score)).join(Call).filter(
        Call.started_at >= start_date,
        Call.started_at <= end_date
    )
    if business_id:
        qa_query = qa_query.filter(Call.business_id == business_id)
    average_qa_score = qa_query.scalar() or 0.0
    
    # Average call duration
    duration_query = db.query(
        func.avg(
            func.extract('epoch', Call.ended_at - Call.started_at)
        )
    ).filter(
        Call.started_at >= start_date,
        Call.started_at <= end_date,
        Call.ended_at.isnot(None)
    )
    if business_id:
        duration_query = duration_query.filter(Call.business_id == business_id)
    average_call_duration = duration_query.scalar() or 0.0
    
    # Escalation rate
    escalation_rate = (escalated_calls / total_calls * 100) if total_calls > 0 else 0.0
    
    # Sentiment distribution
    sentiment_query = db.query(
        QAScore.sentiment_label,
        func.count(QAScore.id)
    ).join(Call).filter(
        Call.started_at >= start_date,
        Call.started_at <= end_date,
        QAScore.sentiment_label.isnot(None)
    )
    if business_id:
        sentiment_query = sentiment_query.filter(Call.business_id == business_id)
    sentiment_counts = {row[0]: row[1] for row in sentiment_query.group_by(QAScore.sentiment_label).all()}
    
    sentiment_distribution = {
        "positive": sentiment_counts.get("positive", 0),
        "neutral": sentiment_counts.get("neutral", 0),
        "negative": sentiment_counts.get("negative", 0),
    }
    
    # QA score distribution
    qa_dist_query = db.query(QAScore.overall_score).join(Call).filter(
        Call.started_at >= start_date,
        Call.started_at <= end_date
    )
    if business_id:
        qa_dist_query = qa_dist_query.filter(Call.business_id == business_id)
    
    qa_scores = [row[0] for row in qa_dist_query.all()]
    excellent = sum(1 for s in qa_scores if s >= 0.8)
    good = sum(1 for s in qa_scores if 0.6 <= s < 0.8)
    fair = sum(1 for s in qa_scores if 0.4 <= s < 0.6)
    poor = sum(1 for s in qa_scores if s < 0.4)
    
    qa_score_distribution = {
        "excellent": excellent,
        "good": good,
        "fair": fair,
        "poor": poor,
    }
    
    return OverviewMetrics(
        total_calls=total_calls,
        active_calls=active_calls,
        completed_calls=completed_calls,
        failed_calls=failed_calls,
        escalated_calls=escalated_calls,
        average_qa_score=float(average_qa_score),
        average_call_duration=float(average_call_duration),
        escalation_rate=float(escalation_rate),
        sentiment_distribution=sentiment_distribution,
        qa_score_distribution=qa_score_distribution,
    )

