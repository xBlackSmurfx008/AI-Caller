"""Scheduling and planning API routes"""

from fastapi import APIRouter, HTTPException, Depends, status
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import List, Optional

from src.database.database import get_db
from src.orchestrator.scheduler import TaskScheduler
from src.orchestrator.orchestrator_service import OrchestratorService
from src.orchestrator.weekly_review import WeeklyReviewGenerator
from src.utils.logging import get_logger

router = APIRouter()
logger = get_logger(__name__)
scheduler = TaskScheduler()
orchestrator = OrchestratorService()
review_generator = WeeklyReviewGenerator()


@router.post("/schedule-all")
async def schedule_all_tasks(
    force_reschedule: bool = False,
    db: Session = Depends(get_db)
):
    """Schedule all schedulable tasks"""
    result = scheduler.schedule_tasks(db, force_reschedule=force_reschedule)
    return result


@router.get("/daily-plan")
async def get_daily_plan(db: Session = Depends(get_db)):
    """Get today's daily plan"""
    plan = orchestrator.generate_daily_plan(db)
    return plan


@router.post("/projects/{project_id}/plan")
async def generate_project_plan(
    project_id: str,
    goal_description: str,
    target_due_date: Optional[str] = None,
    priority: int = 5,
    db: Session = Depends(get_db)
):
    """Generate AI project plan from goal description"""
    from datetime import datetime
    from src.database.models import Project
    
    # Check if project exists
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found"
        )
    
    due_date = None
    if target_due_date:
        try:
            due_date = datetime.fromisoformat(target_due_date.replace("Z", "+00:00"))
        except Exception:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid date format"
            )
    
    result = orchestrator.generate_project_plan(
        db,
        goal_description,
        project_title=project.title,
        target_due_date=due_date,
        priority=priority
    )
    return result


@router.get("/weekly-review")
async def get_weekly_review(
    week_start: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """Generate weekly review"""
    from datetime import datetime
    
    week_start_dt = None
    if week_start:
        try:
            week_start_dt = datetime.fromisoformat(week_start.replace("Z", "+00:00"))
        except Exception:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid date format"
            )
    
    review = review_generator.generate_weekly_review(db, week_start_dt)
    return review

