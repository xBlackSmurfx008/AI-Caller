"""QA analytics endpoint"""

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from typing import Optional

from src.database.database import get_db
from src.database.models import QAScore, Call
from src.api.schemas.analytics import (
    QAStatistics,
    QAScoreDistribution,
    QATrend,
    TopIssue,
)
from src.api.utils import handle_service_errors_sync
from src.utils.logging import get_logger
from .utils import get_date_range

logger = get_logger(__name__)
router = APIRouter()


@router.get("/qa", response_model=QAStatistics)
@handle_service_errors_sync
def get_qa_statistics(
    from_date: Optional[str] = Query(None),
    to_date: Optional[str] = Query(None),
    business_id: Optional[str] = Query(None),
    db: Session = Depends(get_db),
):
    """Get QA score statistics"""
    start_date, end_date = get_date_range(from_date, to_date, 30)
    
    query = db.query(QAScore).join(Call).filter(
        Call.started_at >= start_date,
        Call.started_at <= end_date
    )
    
    if business_id:
        query = query.filter(Call.business_id == business_id)
    
    qa_scores = query.all()
    
    if not qa_scores:
        return QAStatistics()
    
    # Average scores
    total = len(qa_scores)
    average_scores = {
        "overall": sum(s.overall_score for s in qa_scores) / total,
        "sentiment": sum(s.sentiment_score or 0 for s in qa_scores) / total,
        "compliance": sum(s.compliance_score or 0 for s in qa_scores) / total,
        "accuracy": sum(s.accuracy_score or 0 for s in qa_scores) / total,
        "professionalism": sum(s.professionalism_score or 0 for s in qa_scores) / total,
    }
    
    # Score distribution
    ranges = [
        ("0.8-1.0", 0.8, 1.0),
        ("0.6-0.79", 0.6, 0.79),
        ("0.4-0.59", 0.4, 0.59),
        ("0.0-0.39", 0.0, 0.39),
    ]
    
    score_distribution = []
    for range_name, min_score, max_score in ranges:
        count = sum(1 for s in qa_scores if min_score <= s.overall_score <= max_score)
        percentage = (count / total * 100) if total > 0 else 0.0
        score_distribution.append(QAScoreDistribution(
            range=range_name,
            count=count,
            percentage=round(percentage, 2)
        ))
    
    # Trends (simplified - daily averages)
    trends = []
    # Group by day
    daily_scores = {}
    for score in qa_scores:
        day = score.created_at.date().isoformat()
        if day not in daily_scores:
            daily_scores[day] = []
        daily_scores[day].append(score.overall_score)
    
    for day, scores in sorted(daily_scores.items()):
        trends.append(QATrend(
            period=day,
            average_score=sum(scores) / len(scores)
        ))
    
    # Top issues
    all_issues = {}
    for score in qa_scores:
        for issue in (score.compliance_issues or []):
            all_issues[issue] = all_issues.get(issue, 0) + 1
        for issue in (score.flagged_issues or []):
            all_issues[issue] = all_issues.get(issue, 0) + 1
    
    top_issues = [
        TopIssue(
            issue=issue,
            count=count,
            percentage=round((count / total * 100), 2)
        )
        for issue, count in sorted(all_issues.items(), key=lambda x: x[1], reverse=True)[:10]
    ]
    
    return QAStatistics(
        average_scores=average_scores,
        score_distribution=score_distribution,
        trends=trends,
        top_issues=top_issues,
    )

