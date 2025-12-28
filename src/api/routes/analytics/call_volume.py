"""Call volume analytics endpoint"""

from fastapi import APIRouter, Depends, Query, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import func, case
from typing import Optional, List

from src.database.database import get_db
from src.database.models import Call, CallStatus, CallDirection
from src.api.schemas.analytics import CallVolumeData
from src.api.utils import handle_service_errors_sync
from src.utils.logging import get_logger
from .utils import parse_date

logger = get_logger(__name__)
router = APIRouter()


@router.get("/call-volume", response_model=List[CallVolumeData])
@handle_service_errors_sync
def get_call_volume(
    from_date: str = Query(...),
    to_date: str = Query(...),
    interval: str = Query("day", pattern="^(hour|day|week|month)$"),
    business_id: Optional[str] = Query(None),
    direction: Optional[str] = Query(None, pattern="^(inbound|outbound)$"),
    db: Session = Depends(get_db),
):
    """Get call volume statistics over time"""
    start_date = parse_date(from_date)
    end_date = parse_date(to_date)
    
    if not start_date or not end_date:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid date format. Use ISO 8601 format."
        )
    
    # Determine date truncation based on interval
    if interval == "hour":
        date_trunc = func.date_trunc('hour', Call.started_at)
    elif interval == "day":
        date_trunc = func.date_trunc('day', Call.started_at)
    elif interval == "week":
        date_trunc = func.date_trunc('week', Call.started_at)
    else:  # month
        date_trunc = func.date_trunc('month', Call.started_at)
    
    query = db.query(
        date_trunc.label('period'),
        func.count(Call.id).label('total_calls'),
        func.sum(case((Call.direction == CallDirection.INBOUND, 1), else_=0)).label('inbound_calls'),
        func.sum(case((Call.direction == CallDirection.OUTBOUND, 1), else_=0)).label('outbound_calls'),
        func.sum(case((Call.status == CallStatus.COMPLETED, 1), else_=0)).label('completed_calls'),
        func.sum(case((Call.status == CallStatus.ESCALATED, 1), else_=0)).label('escalated_calls'),
    ).filter(
        Call.started_at >= start_date,
        Call.started_at <= end_date
    )
    
    if business_id:
        query = query.filter(Call.business_id == business_id)
    
    if direction:
        if direction == "inbound":
            query = query.filter(Call.direction == CallDirection.INBOUND)
        else:
            query = query.filter(Call.direction == CallDirection.OUTBOUND)
    
    results = query.group_by('period').order_by('period').all()
    
    return [
        CallVolumeData(
            period=row.period.isoformat() if hasattr(row.period, 'isoformat') else str(row.period),
            total_calls=row.total_calls or 0,
            inbound_calls=int(row.inbound_calls or 0),
            outbound_calls=int(row.outbound_calls or 0),
            completed_calls=int(row.completed_calls or 0),
            escalated_calls=int(row.escalated_calls or 0),
        )
        for row in results
    ]

