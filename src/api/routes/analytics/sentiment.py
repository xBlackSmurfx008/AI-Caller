"""Sentiment analytics endpoint"""

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from typing import Optional

from src.database.database import get_db
from src.database.models import QAScore, Call
from src.api.schemas.analytics import (
    SentimentStatistics,
    SentimentTrend,
)
from src.api.utils import handle_service_errors_sync
from src.utils.logging import get_logger
from .utils import get_date_range

logger = get_logger(__name__)
router = APIRouter()


@router.get("/sentiment", response_model=SentimentStatistics)
@handle_service_errors_sync
def get_sentiment_statistics(
    from_date: Optional[str] = Query(None),
    to_date: Optional[str] = Query(None),
    business_id: Optional[str] = Query(None),
    db: Session = Depends(get_db),
):
    """Get sentiment analysis statistics"""
    start_date, end_date = get_date_range(from_date, to_date, 30)
    
    query = db.query(QAScore).join(Call).filter(
        Call.started_at >= start_date,
        Call.started_at <= end_date,
        QAScore.sentiment_label.isnot(None)
    )
    
    if business_id:
        query = query.filter(Call.business_id == business_id)
    
    qa_scores = query.all()
    
    if not qa_scores:
        return SentimentStatistics()
    
    # Distribution
    distribution = {"positive": 0, "neutral": 0, "negative": 0}
    sentiment_scores = []
    for score in qa_scores:
        if score.sentiment_label:
            distribution[score.sentiment_label] = distribution.get(score.sentiment_label, 0) + 1
        if score.sentiment_score:
            sentiment_scores.append(score.sentiment_score)
    
    average_sentiment_score = sum(sentiment_scores) / len(sentiment_scores) if sentiment_scores else 0.0
    
    # Trends
    daily_sentiment = {}
    for score in qa_scores:
        day = score.created_at.date().isoformat()
        if day not in daily_sentiment:
            daily_sentiment[day] = {"positive": 0, "neutral": 0, "negative": 0, "scores": []}
        if score.sentiment_label:
            daily_sentiment[day][score.sentiment_label] += 1
        if score.sentiment_score:
            daily_sentiment[day]["scores"].append(score.sentiment_score)
    
    trends = [
        SentimentTrend(
            period=day,
            positive=data["positive"],
            neutral=data["neutral"],
            negative=data["negative"],
            average_score=sum(data["scores"]) / len(data["scores"]) if data["scores"] else 0.0
        )
        for day, data in sorted(daily_sentiment.items())
    ]
    
    # Correlation (simplified)
    # Calculate correlation between sentiment scores and QA scores
    sentiment_qa_pairs = [
        (s.sentiment_score, s.overall_score)
        for s in qa_scores
        if s.sentiment_score is not None
    ]
    
    if len(sentiment_qa_pairs) > 1:
        # Simple correlation calculation
        sentiment_values = [p[0] for p in sentiment_qa_pairs]
        qa_values = [p[1] for p in sentiment_qa_pairs]
        
        mean_sentiment = sum(sentiment_values) / len(sentiment_values)
        mean_qa = sum(qa_values) / len(qa_values)
        
        numerator = sum((s - mean_sentiment) * (q - mean_qa) for s, q in zip(sentiment_values, qa_values))
        denom_sentiment = sum((s - mean_sentiment) ** 2 for s in sentiment_values)
        denom_qa = sum((q - mean_qa) ** 2 for q in qa_values)
        
        if denom_sentiment > 0 and denom_qa > 0:
            correlation = numerator / ((denom_sentiment * denom_qa) ** 0.5)
        else:
            correlation = 0.0
    else:
        correlation = 0.0
    
    # Escalation correlation (simplified)
    escalation_correlation = 0.0  # Would need more complex calculation
    
    return SentimentStatistics(
        distribution=distribution,
        average_sentiment_score=float(average_sentiment_score),
        trends=trends,
        correlation={
            "sentiment_vs_qa": round(correlation, 3),
            "sentiment_vs_escalation": round(escalation_correlation, 3),
        }
    )

