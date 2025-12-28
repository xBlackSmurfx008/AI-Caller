"""Pydantic schemas for analytics API"""

from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime


class OverviewMetrics(BaseModel):
    """Overview metrics response"""
    total_calls: int = 0
    active_calls: int = 0
    completed_calls: int = 0
    failed_calls: int = 0
    escalated_calls: int = 0
    average_qa_score: float = 0.0
    average_call_duration: float = 0.0
    escalation_rate: float = 0.0
    sentiment_distribution: Dict[str, int] = Field(default_factory=lambda: {"positive": 0, "neutral": 0, "negative": 0})
    qa_score_distribution: Dict[str, int] = Field(default_factory=lambda: {"excellent": 0, "good": 0, "fair": 0, "poor": 0})


class CallVolumeData(BaseModel):
    """Call volume data point"""
    period: str
    total_calls: int = 0
    inbound_calls: int = 0
    outbound_calls: int = 0
    completed_calls: int = 0
    escalated_calls: int = 0


class QAScoreDistribution(BaseModel):
    """QA score distribution entry"""
    range: str
    count: int = 0
    percentage: float = 0.0


class QATrend(BaseModel):
    """QA trend data point"""
    period: str
    average_score: float = 0.0


class TopIssue(BaseModel):
    """Top issue entry"""
    issue: str
    count: int = 0
    percentage: float = 0.0


class QAStatistics(BaseModel):
    """QA statistics response"""
    average_scores: Dict[str, float] = Field(default_factory=lambda: {
        "overall": 0.0,
        "sentiment": 0.0,
        "compliance": 0.0,
        "accuracy": 0.0,
        "professionalism": 0.0
    })
    score_distribution: List[QAScoreDistribution] = Field(default_factory=list)
    trends: List[QATrend] = Field(default_factory=list)
    top_issues: List[TopIssue] = Field(default_factory=list)


class SentimentTrend(BaseModel):
    """Sentiment trend data point"""
    period: str
    positive: int = 0
    neutral: int = 0
    negative: int = 0
    average_score: float = 0.0


class SentimentStatistics(BaseModel):
    """Sentiment statistics response"""
    distribution: Dict[str, int] = Field(default_factory=lambda: {"positive": 0, "neutral": 0, "negative": 0})
    average_sentiment_score: float = 0.0
    trends: List[SentimentTrend] = Field(default_factory=list)
    correlation: Dict[str, float] = Field(default_factory=lambda: {"sentiment_vs_qa": 0.0, "sentiment_vs_escalation": 0.0})


class EscalationByType(BaseModel):
    """Escalation by trigger type"""
    trigger_type: str
    count: int = 0
    percentage: float = 0.0


class EscalationByStatus(BaseModel):
    """Escalation by status"""
    pending: int = 0
    in_progress: int = 0
    completed: int = 0
    cancelled: int = 0


class EscalationTrend(BaseModel):
    """Escalation trend data point"""
    period: str
    escalation_count: int = 0
    escalation_rate: float = 0.0


class EscalationStatistics(BaseModel):
    """Escalation statistics response"""
    total_escalations: int = 0
    escalation_rate: float = 0.0
    by_trigger_type: List[EscalationByType] = Field(default_factory=list)
    by_status: EscalationByStatus = Field(default_factory=lambda: EscalationByStatus())
    average_resolution_time: float = 0.0
    trends: List[EscalationTrend] = Field(default_factory=list)


class ExportRequest(BaseModel):
    """Export request schema"""
    format: str = Field(..., pattern="^(csv|pdf)$")
    report_type: str = Field(..., pattern="^(overview|calls|qa|sentiment|escalations|full)$")
    from_date: Optional[str] = None
    to_date: Optional[str] = None
    business_id: Optional[str] = None
    include_charts: bool = False

