"""Goals API routes for managing Godfather goals"""

from fastapi import APIRouter, HTTPException, Depends, status
from sqlalchemy.orm import Session
from typing import List, Optional
from pydantic import BaseModel
from datetime import datetime

from src.database.database import get_db
from src.database.models import Goal, Project
from src.utils.logging import get_logger

router = APIRouter()
logger = get_logger(__name__)


class GoalCreate(BaseModel):
    title: str
    description: Optional[str] = None
    goal_type: str  # "short_term" or "long_term"
    priority: Optional[int] = 5  # 1-10
    target_date: Optional[str] = None  # ISO format


class GoalUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    goal_type: Optional[str] = None
    status: Optional[str] = None
    priority: Optional[int] = None
    target_date: Optional[str] = None


class GoalResponse(BaseModel):
    id: str
    title: str
    description: Optional[str] = None
    goal_type: str
    status: str
    priority: int
    target_date: Optional[str] = None
    created_at: str
    updated_at: str
    project_count: Optional[int] = 0

    class Config:
        from_attributes = True


@router.post("/", response_model=GoalResponse)
async def create_goal(goal: GoalCreate, db: Session = Depends(get_db)):
    """Create a new goal"""
    # Validate goal_type
    if goal.goal_type not in ["short_term", "long_term"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="goal_type must be 'short_term' or 'long_term'"
        )
    
    # Validate priority range
    if goal.priority is not None and (goal.priority < 1 or goal.priority > 10):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="priority must be between 1 and 10"
        )
    
    target_date = None
    if goal.target_date:
        try:
            target_date = datetime.fromisoformat(goal.target_date.replace('Z', '+00:00'))
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid target_date format. Use ISO 8601 format."
            )
    
    db_goal = Goal(
        title=goal.title,
        description=goal.description,
        goal_type=goal.goal_type,
        priority=goal.priority or 5,
        target_date=target_date
    )
    
    db.add(db_goal)
    db.commit()
    db.refresh(db_goal)
    
    logger.info("goal_created", goal_id=db_goal.id, title=db_goal.title)
    return _goal_to_response(db_goal, db)


@router.get("/", response_model=List[GoalResponse])
async def list_goals(
    status: Optional[str] = None,
    goal_type: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """List all goals with optional filters"""
    query = db.query(Goal)
    
    if status:
        query = query.filter(Goal.status == status)
    if goal_type:
        query = query.filter(Goal.goal_type == goal_type)
    
    goals = query.order_by(Goal.priority.desc(), Goal.created_at.desc()).all()
    
    return [_goal_to_response(g, db) for g in goals]


@router.get("/{goal_id}", response_model=GoalResponse)
async def get_goal(goal_id: str, db: Session = Depends(get_db)):
    """Get a specific goal"""
    goal = db.query(Goal).filter(Goal.id == goal_id).first()
    if not goal:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Goal not found"
        )
    
    return _goal_to_response(goal, db)


@router.put("/{goal_id}", response_model=GoalResponse)
async def update_goal(
    goal_id: str,
    goal: GoalUpdate,
    db: Session = Depends(get_db)
):
    """Update a goal"""
    db_goal = db.query(Goal).filter(Goal.id == goal_id).first()
    if not db_goal:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Goal not found"
        )
    
    if goal.title is not None:
        db_goal.title = goal.title
    if goal.description is not None:
        db_goal.description = goal.description
    if goal.goal_type is not None:
        if goal.goal_type not in ["short_term", "long_term"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="goal_type must be 'short_term' or 'long_term'"
            )
        db_goal.goal_type = goal.goal_type
    if goal.status is not None:
        if goal.status not in ["active", "completed", "paused", "cancelled"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="status must be: active, completed, paused, or cancelled"
            )
        db_goal.status = goal.status
    if goal.priority is not None:
        if goal.priority < 1 or goal.priority > 10:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="priority must be between 1 and 10"
            )
        db_goal.priority = goal.priority
    if goal.target_date is not None:
        try:
            db_goal.target_date = datetime.fromisoformat(goal.target_date.replace('Z', '+00:00'))
        except:
            pass
    
    db.commit()
    db.refresh(db_goal)
    
    logger.info("goal_updated", goal_id=goal_id)
    return _goal_to_response(db_goal, db)


@router.delete("/{goal_id}")
async def delete_goal(goal_id: str, db: Session = Depends(get_db)):
    """Delete a goal"""
    goal = db.query(Goal).filter(Goal.id == goal_id).first()
    if not goal:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Goal not found"
        )
    
    db.delete(goal)
    db.commit()
    
    logger.info("goal_deleted", goal_id=goal_id)
    return {"success": True}


def _goal_to_response(goal: Goal, db: Session) -> GoalResponse:
    """Convert Goal model to GoalResponse"""
    project_count = db.query(Project).filter(Project.goal_id == goal.id).count()
    
    return GoalResponse(
        id=goal.id,
        title=goal.title,
        description=goal.description,
        goal_type=goal.goal_type,
        status=goal.status,
        priority=goal.priority,
        target_date=goal.target_date.isoformat() if goal.target_date else None,
        created_at=goal.created_at.isoformat(),
        updated_at=goal.updated_at.isoformat(),
        project_count=project_count
    )

