"""Orchestrator API routes for suggestions and weekly reviews"""

from fastapi import APIRouter, HTTPException, Depends, status
from sqlalchemy.orm import Session
from typing import List, Optional
from pydantic import BaseModel
from datetime import datetime

from src.database.database import get_db
from src.database.models import Suggestion, IntroductionRecommendation
from src.orchestrator.orchestrator_service import OrchestratorService
from src.orchestrator.weekly_review import WeeklyReviewGenerator
from src.utils.logging import get_logger

router = APIRouter()
logger = get_logger(__name__)
orchestrator = OrchestratorService()
review_generator = WeeklyReviewGenerator()


class SuggestionResponse(BaseModel):
    id: str
    suggestion_type: str
    contact_id: Optional[str] = None
    project_id: Optional[str] = None
    intent: str
    rationale: Optional[str] = None
    expected_upside_godfather: Optional[str] = None
    expected_upside_contact: Optional[str] = None
    risk_flags: Optional[List[str]] = None
    message_draft: Optional[str] = None
    best_timing: Optional[str] = None
    score: Optional[float] = None
    status: str
    created_at: str

    class Config:
        from_attributes = True


class SuggestionUpdate(BaseModel):
    status: str  # "approved", "executed", "dismissed"


@router.post("/suggestions/generate")
async def generate_suggestions(
    limit: int = 20,
    db: Session = Depends(get_db)
):
    """Generate win-win relationship action suggestions"""
    try:
        suggestions = orchestrator.generate_suggestions(db, limit)
        return {
            "success": True,
            "count": len(suggestions),
            "suggestions": [
                {
                    "id": s.id,
                    "suggestion_type": s.suggestion_type,
                    "contact_id": s.contact_id,
                    "project_id": s.project_id,
                    "intent": s.intent,
                    "rationale": s.rationale,
                    "expected_upside_godfather": s.expected_upside_godfather,
                    "expected_upside_contact": s.expected_upside_contact,
                    "risk_flags": s.risk_flags,
                    "message_draft": s.message_draft,
                    "best_timing": s.best_timing,
                    "score": s.score,
                    "status": s.status,
                    "created_at": s.created_at.isoformat()
                }
                for s in suggestions
            ]
        }
    except Exception as e:
        logger.error("suggestion_generation_failed", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate suggestions: {str(e)}"
        )


@router.get("/suggestions", response_model=List[SuggestionResponse])
async def list_suggestions(
    status: Optional[str] = None,
    suggestion_type: Optional[str] = None,
    include_expired: bool = False,
    limit: int = 50,
    db: Session = Depends(get_db)
):
    """List suggestions with optional filters"""
    from datetime import datetime
    
    query = db.query(Suggestion)
    
    if status:
        query = query.filter(Suggestion.status == status)
    if suggestion_type:
        query = query.filter(Suggestion.suggestion_type == suggestion_type)
    
    # Filter out expired suggestions by default
    if not include_expired:
        now = datetime.utcnow()
        query = query.filter(
            (Suggestion.expires_at.is_(None)) | (Suggestion.expires_at > now)
        )
    
    suggestions = query.order_by(Suggestion.score.desc()).limit(limit).all()
    
    return [
        SuggestionResponse(
            id=s.id,
            suggestion_type=s.suggestion_type,
            contact_id=s.contact_id,
            project_id=s.project_id,
            intent=s.intent,
            rationale=s.rationale,
            expected_upside_godfather=s.expected_upside_godfather,
            expected_upside_contact=s.expected_upside_contact,
            risk_flags=s.risk_flags,
            message_draft=s.message_draft,
            best_timing=s.best_timing,
            score=s.score,
            status=s.status,
            created_at=s.created_at.isoformat()
        )
        for s in suggestions
    ]


@router.put("/suggestions/{suggestion_id}")
async def update_suggestion(
    suggestion_id: str,
    update: SuggestionUpdate,
    db: Session = Depends(get_db)
):
    """Update suggestion status"""
    suggestion = db.query(Suggestion).filter(Suggestion.id == suggestion_id).first()
    if not suggestion:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Suggestion not found"
        )
    
    suggestion.status = update.status
    db.commit()
    db.refresh(suggestion)
    
    logger.info("suggestion_updated", suggestion_id=suggestion_id, status=update.status)
    return {"success": True, "suggestion_id": suggestion_id, "status": suggestion.status}


@router.post("/introductions/generate")
async def generate_introductions(
    limit: int = 10,
    db: Session = Depends(get_db)
):
    """Generate introduction recommendations"""
    try:
        recommendations = orchestrator.generate_introduction_recommendations(db, limit)
        return {
            "success": True,
            "count": len(recommendations),
            "recommendations": recommendations
        }
    except Exception as e:
        logger.error("introduction_generation_failed", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate introductions: {str(e)}"
        )


@router.get("/introductions", response_model=List[dict])
async def list_introductions(
    status: Optional[str] = None,
    limit: int = 50,
    db: Session = Depends(get_db)
):
    """List introduction recommendations"""
    query = db.query(IntroductionRecommendation)
    
    if status:
        query = query.filter(IntroductionRecommendation.status == status)
    
    recommendations = query.order_by(IntroductionRecommendation.score.desc()).limit(limit).all()
    
    return [
        {
            "id": r.id,
            "contact_a_id": r.contact_a_id,
            "contact_b_id": r.contact_b_id,
            "mutual_benefit": r.mutual_benefit,
            "context": r.context,
            "suggested_approach": r.suggested_approach,
            "score": r.score,
            "status": r.status,
            "created_at": r.created_at.isoformat()
        }
        for r in recommendations
    ]


@router.get("/weekly-review")
async def get_weekly_review(
    week_start: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """Generate weekly Godfather review"""
    try:
        week_start_dt = None
        if week_start:
            try:
                week_start_dt = datetime.fromisoformat(week_start.replace('Z', '+00:00'))
            except:
                pass
        
        review = review_generator.generate_weekly_review(db, week_start_dt)
        return review
    except Exception as e:
        logger.error("weekly_review_generation_failed", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate weekly review: {str(e)}"
        )

