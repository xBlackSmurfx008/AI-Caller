"""Project task management API routes with scheduling"""

from fastapi import APIRouter, HTTPException, Depends, status
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime

from src.database.database import get_db
from src.database.models import ProjectTask, Project, CalendarBlock
from src.orchestrator.scheduler import TaskScheduler
from src.orchestrator.ai_executor import AIExecutor
from src.utils.logging import get_logger

router = APIRouter()
logger = get_logger(__name__)
scheduler = TaskScheduler()
ai_executor = AIExecutor()


class TaskCreate(BaseModel):
    project_id: str
    title: str
    description: Optional[str] = None
    estimated_minutes: Optional[int] = None
    deadline_type: Optional[str] = None  # "HARD" or "FLEX"
    due_at: Optional[datetime] = None
    earliest_start_at: Optional[datetime] = None
    dependencies: Optional[List[str]] = None
    priority: Optional[int] = 5
    tags: Optional[List[str]] = None
    energy_level: Optional[str] = None
    execution_mode: Optional[str] = "HUMAN"  # "HUMAN", "AI", "HYBRID"


class TaskUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    status: Optional[str] = None
    estimated_minutes: Optional[int] = None
    deadline_type: Optional[str] = None
    due_at: Optional[datetime] = None
    earliest_start_at: Optional[datetime] = None
    dependencies: Optional[List[str]] = None
    priority: Optional[int] = None
    tags: Optional[List[str]] = None
    energy_level: Optional[str] = None
    execution_mode: Optional[str] = None
    locked_schedule: Optional[bool] = None


class TaskResponse(BaseModel):
    id: str
    project_id: str
    title: str
    description: Optional[str] = None
    status: str
    priority: Optional[int] = None
    estimated_minutes: Optional[int] = None
    deadline_type: Optional[str] = None
    due_at: Optional[str] = None
    earliest_start_at: Optional[str] = None
    dependencies: Optional[List[str]] = None
    tags: Optional[List[str]] = None
    energy_level: Optional[str] = None
    execution_mode: str
    locked_schedule: bool
    calendar_blocks: Optional[List[dict]] = None
    created_at: str
    updated_at: str

    class Config:
        from_attributes = True


@router.post("/", response_model=TaskResponse)
async def create_task(task: TaskCreate, db: Session = Depends(get_db)):
    """Create a new project task"""
    # Verify project exists
    project = db.query(Project).filter(Project.id == task.project_id).first()
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found"
        )
    
    db_task = ProjectTask(
        project_id=task.project_id,
        title=task.title,
        description=task.description,
        estimated_minutes=task.estimated_minutes,
        deadline_type=task.deadline_type,
        due_at=task.due_at,
        earliest_start_at=task.earliest_start_at,
        dependencies=task.dependencies,
        priority=task.priority or 5,
        tags=task.tags,
        energy_level=task.energy_level,
        execution_mode=task.execution_mode or "HUMAN",
        status="todo"
    )
    
    db.add(db_task)
    db.commit()
    db.refresh(db_task)
    
    logger.info("project_task_created", task_id=db_task.id, project_id=task.project_id)
    return _task_to_response(db_task, db)


@router.get("/{task_id}", response_model=TaskResponse)
async def get_task(task_id: str, db: Session = Depends(get_db)):
    """Get a specific task"""
    task = db.query(ProjectTask).filter(ProjectTask.id == task_id).first()
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found"
        )
    
    return _task_to_response(task, db)


@router.get("/", response_model=List[TaskResponse])
async def list_tasks(
    project_id: Optional[str] = None,
    status: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """List tasks with optional filters"""
    query = db.query(ProjectTask)
    
    if project_id:
        query = query.filter(ProjectTask.project_id == project_id)
    if status:
        query = query.filter(ProjectTask.status == status)
    
    tasks = query.order_by(ProjectTask.priority.desc(), ProjectTask.due_at.asc()).all()
    return [_task_to_response(t, db) for t in tasks]


@router.put("/{task_id}", response_model=TaskResponse)
async def update_task(
    task_id: str,
    task_update: TaskUpdate,
    db: Session = Depends(get_db)
):
    """Update a task"""
    task = db.query(ProjectTask).filter(ProjectTask.id == task_id).first()
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found"
        )
    
    # Update fields
    if task_update.title is not None:
        task.title = task_update.title
    if task_update.description is not None:
        task.description = task_update.description
    if task_update.status is not None:
        if task_update.status not in ["todo", "scheduled", "in_progress", "blocked", "done"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid status"
            )
        task.status = task_update.status
    if task_update.estimated_minutes is not None:
        task.estimated_minutes = task_update.estimated_minutes
    if task_update.deadline_type is not None:
        task.deadline_type = task_update.deadline_type
    if task_update.due_at is not None:
        task.due_at = task_update.due_at
    if task_update.earliest_start_at is not None:
        task.earliest_start_at = task_update.earliest_start_at
    if task_update.dependencies is not None:
        task.dependencies = task_update.dependencies
    if task_update.priority is not None:
        task.priority = task_update.priority
    if task_update.tags is not None:
        task.tags = task_update.tags
    if task_update.energy_level is not None:
        task.energy_level = task_update.energy_level
    if task_update.execution_mode is not None:
        task.execution_mode = task_update.execution_mode
    if task_update.locked_schedule is not None:
        task.locked_schedule = task_update.locked_schedule
    
    db.commit()
    db.refresh(task)
    
    logger.info("project_task_updated", task_id=task_id)
    return _task_to_response(task, db)


@router.delete("/{task_id}")
async def delete_task(task_id: str, db: Session = Depends(get_db)):
    """Delete a task"""
    task = db.query(ProjectTask).filter(ProjectTask.id == task_id).first()
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found"
        )
    
    # Delete calendar blocks
    blocks = db.query(CalendarBlock).filter(CalendarBlock.task_id == task_id).all()
    for block in blocks:
        if block.calendar_event_id:
            try:
                from src.calendar.google_calendar import delete_event
                delete_event(block.calendar_event_id)
            except Exception as e:
                logger.warning("failed_to_delete_calendar_event", error=str(e))
        db.delete(block)
    
    db.delete(task)
    db.commit()
    
    logger.info("project_task_deleted", task_id=task_id)
    return {"success": True}


@router.post("/{task_id}/schedule")
async def schedule_task(task_id: str, db: Session = Depends(get_db)):
    """Schedule a task into calendar"""
    task = db.query(ProjectTask).filter(ProjectTask.id == task_id).first()
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found"
        )
    
    result = scheduler.schedule_tasks(db, task_ids=[task_id])
    return result


@router.post("/{task_id}/reschedule")
async def reschedule_task(
    task_id: str,
    new_start: Optional[datetime] = None,
    db: Session = Depends(get_db)
):
    """Reschedule a task"""
    result = scheduler.reschedule_task(db, task_id, new_start)
    if not result.get("success"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=result.get("error", "Failed to reschedule")
        )
    return result


@router.post("/{task_id}/execute")
async def execute_ai_task(task_id: str, db: Session = Depends(get_db)):
    """Execute an AI-executable task"""
    task = db.query(ProjectTask).filter(ProjectTask.id == task_id).first()
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found"
        )
    
    if task.execution_mode not in ["AI", "HYBRID"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Task is not AI-executable"
        )
    
    result = await ai_executor.execute_task(db, task_id)
    if not result.get("success"):
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=result.get("error", "Execution failed")
        )
    return result


def _task_to_response(task: ProjectTask, db: Session) -> TaskResponse:
    """Convert ProjectTask to TaskResponse"""
    # Get calendar blocks
    blocks = db.query(CalendarBlock).filter(CalendarBlock.task_id == task.id).all()
    calendar_blocks = [
        {
            "id": b.id,
            "start_at": b.start_at.isoformat(),
            "end_at": b.end_at.isoformat(),
            "locked": b.locked,
            "calendar_event_id": b.calendar_event_id
        }
        for b in blocks
    ]
    
    return TaskResponse(
        id=task.id,
        project_id=task.project_id,
        title=task.title,
        description=task.description,
        status=task.status,
        priority=task.priority,
        estimated_minutes=task.estimated_minutes,
        deadline_type=task.deadline_type,
        due_at=task.due_at.isoformat() if task.due_at else None,
        earliest_start_at=task.earliest_start_at.isoformat() if task.earliest_start_at else None,
        dependencies=task.dependencies,
        tags=task.tags,
        energy_level=task.energy_level,
        execution_mode=task.execution_mode,
        locked_schedule=task.locked_schedule,
        calendar_blocks=calendar_blocks,
        created_at=task.created_at.isoformat(),
        updated_at=task.updated_at.isoformat()
    )

