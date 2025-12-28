"""Escalation analytics endpoint"""

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from typing import Optional

from src.database.database import get_db
from src.database.models import Escalation, EscalationStatus, Call
from src.api.schemas.analytics import (
    EscalationStatistics,
    EscalationByType,
    EscalationByStatus,
    EscalationTrend,
)
from src.api.utils import handle_service_errors_sync
from src.utils.logging import get_logger
from .utils import get_date_range

logger = get_logger(__name__)
router = APIRouter()


@router.get("/escalations", response_model=EscalationStatistics)
@handle_service_errors_sync
def get_escalation_statistics(
    from_date: Optional[str] = Query(None),
    to_date: Optional[str] = Query(None),
    business_id: Optional[str] = Query(None),
    db: Session = Depends(get_db),
):
    """Get escalation statistics"""
    start_date, end_date = get_date_range(from_date, to_date, 30)
    
    query = db.query(Escalation).join(Call).filter(
        Call.started_at >= start_date,
        Call.started_at <= end_date
    )
    
    if business_id:
        query = query.filter(Call.business_id == business_id)
    
    escalations = query.all()
    total_escalations = len(escalations)
    
    # Total calls for rate calculation
    calls_query = db.query(Call).filter(
        Call.started_at >= start_date,
        Call.started_at <= end_date
    )
    if business_id:
        calls_query = calls_query.filter(Call.business_id == business_id)
    total_calls = calls_query.count()
    
    escalation_rate = (total_escalations / total_calls * 100) if total_calls > 0 else 0.0
    
    # By trigger type
    trigger_counts = {}
    for esc in escalations:
        trigger_counts[esc.trigger_type] = trigger_counts.get(esc.trigger_type, 0) + 1
    
    by_trigger_type = [
        EscalationByType(
            trigger_type=trigger_type,
            count=count,
            percentage=round((count / total_escalations * 100), 2) if total_escalations > 0 else 0.0
        )
        for trigger_type, count in trigger_counts.items()
    ]
    
    # By status
    status_counts = {
        EscalationStatus.PENDING: 0,
        EscalationStatus.IN_PROGRESS: 0,
        EscalationStatus.COMPLETED: 0,
        EscalationStatus.CANCELLED: 0,
    }
    for esc in escalations:
        status_counts[esc.status] = status_counts.get(esc.status, 0) + 1
    
    by_status = EscalationByStatus(
        pending=status_counts[EscalationStatus.PENDING],
        in_progress=status_counts[EscalationStatus.IN_PROGRESS],
        completed=status_counts[EscalationStatus.COMPLETED],
        cancelled=status_counts[EscalationStatus.CANCELLED],
    )
    
    # Average resolution time
    completed_escalations = [e for e in escalations if e.completed_at and e.requested_at]
    if completed_escalations:
        resolution_times = [
            (e.completed_at - e.requested_at).total_seconds()
            for e in completed_escalations
        ]
        average_resolution_time = sum(resolution_times) / len(resolution_times)
    else:
        average_resolution_time = 0.0
    
    # Trends
    daily_escalations = {}
    daily_calls = {}
    for esc in escalations:
        day = esc.requested_at.date().isoformat()
        daily_escalations[day] = daily_escalations.get(day, 0) + 1
    
    for call in calls_query.all():
        day = call.started_at.date().isoformat()
        daily_calls[day] = daily_calls.get(day, 0) + 1
    
    trends = [
        EscalationTrend(
            period=day,
            escalation_count=daily_escalations.get(day, 0),
            escalation_rate=(daily_escalations.get(day, 0) / daily_calls.get(day, 1) * 100) if daily_calls.get(day, 0) > 0 else 0.0
        )
        for day in sorted(set(list(daily_escalations.keys()) + list(daily_calls.keys())))
    ]
    
    return EscalationStatistics(
        total_escalations=total_escalations,
        escalation_rate=float(escalation_rate),
        by_trigger_type=by_trigger_type,
        by_status=by_status,
        average_resolution_time=float(average_resolution_time),
        trends=trends,
    )

