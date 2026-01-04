"""Projects API routes for managing Godfather projects"""

from fastapi import APIRouter, HTTPException, Depends, status
from sqlalchemy.orm import Session
from typing import List, Optional
from pydantic import BaseModel
from datetime import datetime

from src.database.database import get_db
from src.database.models import Project, Goal, ProjectStakeholder, ProjectTask, Contact
from src.orchestrator.orchestrator_service import OrchestratorService
from src.utils.logging import get_logger

router = APIRouter()
logger = get_logger(__name__)
orchestrator = OrchestratorService()


class ProjectCreate(BaseModel):
    title: str
    description: Optional[str] = None
    goal_id: Optional[str] = None
    priority: Optional[int] = 5
    target_due_date: Optional[datetime] = None
    milestones: Optional[List[dict]] = None
    constraints: Optional[dict] = None


class ProjectUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    status: Optional[str] = None
    priority: Optional[int] = None
    target_due_date: Optional[datetime] = None
    milestones: Optional[List[dict]] = None
    constraints: Optional[dict] = None


class ProjectResponse(BaseModel):
    id: str
    goal_id: Optional[str] = None
    title: str
    description: Optional[str] = None
    status: str
    priority: Optional[int] = None
    target_due_date: Optional[str] = None
    milestones: Optional[List[dict]] = None
    constraints: Optional[dict] = None
    created_at: str
    updated_at: str

    class Config:
        from_attributes = True


class ProjectStakeholderCreate(BaseModel):
    contact_id: str
    role: Optional[str] = None
    how_they_help: Optional[str] = None
    how_we_help: Optional[str] = None


@router.post("/", response_model=ProjectResponse)
async def create_project(
    project: ProjectCreate,
    db: Session = Depends(get_db)
):
    """Create a new project"""
    db_project = Project(
        title=project.title,
        description=project.description,
        goal_id=project.goal_id,
        priority=project.priority or 5,
        target_due_date=project.target_due_date,
        milestones=project.milestones or [],
        constraints=project.constraints or {}
    )
    
    db.add(db_project)
    db.commit()
    db.refresh(db_project)
    
    logger.info("project_created", project_id=db_project.id, title=db_project.title)
    return ProjectResponse(
        id=db_project.id,
        goal_id=db_project.goal_id,
        title=db_project.title,
        description=db_project.description,
        status=db_project.status,
        milestones=db_project.milestones,
        constraints=db_project.constraints,
        created_at=db_project.created_at.isoformat(),
        updated_at=db_project.updated_at.isoformat()
    )


@router.get("/", response_model=List[ProjectResponse])
async def list_projects(
    status: Optional[str] = None,
    goal_id: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """List all projects with optional filters"""
    query = db.query(Project)
    
    if status:
        query = query.filter(Project.status == status)
    if goal_id:
        query = query.filter(Project.goal_id == goal_id)
    
    projects = query.order_by(Project.created_at.desc()).all()
    
    return [
        ProjectResponse(
            id=p.id,
            goal_id=p.goal_id,
            title=p.title,
            description=p.description,
            status=p.status,
            priority=p.priority,
            target_due_date=p.target_due_date.isoformat() if p.target_due_date else None,
            milestones=p.milestones,
            constraints=p.constraints,
            created_at=p.created_at.isoformat(),
            updated_at=p.updated_at.isoformat()
        )
        for p in projects
    ]


@router.get("/{project_id}", response_model=ProjectResponse)
async def get_project(project_id: str, db: Session = Depends(get_db)):
    """Get a specific project"""
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found"
        )
    
    return ProjectResponse(
        id=project.id,
        goal_id=project.goal_id,
        title=project.title,
        description=project.description,
        status=project.status,
        priority=project.priority,
        target_due_date=project.target_due_date.isoformat() if project.target_due_date else None,
        milestones=project.milestones,
        constraints=project.constraints,
        created_at=project.created_at.isoformat(),
        updated_at=project.updated_at.isoformat()
    )


@router.get("/{project_id}/context")
async def get_project_context(project_id: str, db: Session = Depends(get_db)):
    """Get full project context including network opportunities"""
    try:
        context = orchestrator.get_project_context(db, project_id)
        return context
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )


@router.get("/{project_id}/network-opportunities")
async def get_network_opportunities(
    project_id: str,
    limit: int = 10,
    db: Session = Depends(get_db)
):
    """Identify network contacts who could help with this project"""
    try:
        opportunities = orchestrator.identify_network_opportunities(
            db, project_id, limit
        )
        return {"opportunities": opportunities}
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )


@router.put("/{project_id}", response_model=ProjectResponse)
async def update_project(
    project_id: str,
    project: ProjectUpdate,
    db: Session = Depends(get_db)
):
    """Update a project"""
    db_project = db.query(Project).filter(Project.id == project_id).first()
    if not db_project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found"
        )
    
    if project.title is not None:
        db_project.title = project.title
    if project.description is not None:
        db_project.description = project.description
    if project.status is not None:
        if project.status not in ["active", "completed", "paused", "cancelled", "blocked"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="status must be: active, completed, paused, cancelled, or blocked"
            )
        db_project.status = project.status
    if project.priority is not None:
        db_project.priority = project.priority
    if project.target_due_date is not None:
        db_project.target_due_date = project.target_due_date
    if project.milestones is not None:
        db_project.milestones = project.milestones
    if project.constraints is not None:
        db_project.constraints = project.constraints
    
    db.commit()
    db.refresh(db_project)
    
    logger.info("project_updated", project_id=project_id)
    return ProjectResponse(
        id=db_project.id,
        goal_id=db_project.goal_id,
        title=db_project.title,
        description=db_project.description,
        status=db_project.status,
        priority=db_project.priority,
        target_due_date=db_project.target_due_date.isoformat() if db_project.target_due_date else None,
        milestones=db_project.milestones,
        constraints=db_project.constraints,
        created_at=db_project.created_at.isoformat(),
        updated_at=db_project.updated_at.isoformat()
    )


@router.get("/{project_id}/stakeholders")
async def get_stakeholders(project_id: str, db: Session = Depends(get_db)):
    """Get all stakeholders for a project with contact details"""
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found"
        )
    
    stakeholders = db.query(ProjectStakeholder).filter(
        ProjectStakeholder.project_id == project_id
    ).all()
    
    result = []
    for s in stakeholders:
        contact = db.query(Contact).filter(Contact.id == s.contact_id).first()
        result.append({
            "id": s.id,
            "contact_id": s.contact_id,
            "contact_name": contact.name if contact else "Unknown",
            "contact_email": contact.email if contact else None,
            "contact_phone": contact.phone_number if contact else None,
            "contact_organization": contact.organization if contact else None,
            "role": s.role,
            "how_they_help": s.how_they_help,
            "how_we_help": s.how_we_help,
            "created_at": s.created_at.isoformat()
        })
    
    return {"stakeholders": result}


@router.post("/{project_id}/stakeholders", response_model=dict)
async def add_stakeholder(
    project_id: str,
    stakeholder: ProjectStakeholderCreate,
    db: Session = Depends(get_db)
):
    """Add a stakeholder to a project"""
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found"
        )
    
    contact = db.query(Contact).filter(Contact.id == stakeholder.contact_id).first()
    if not contact:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Contact not found"
        )
    
    # Check if already a stakeholder
    existing = db.query(ProjectStakeholder).filter(
        ProjectStakeholder.project_id == project_id,
        ProjectStakeholder.contact_id == stakeholder.contact_id
    ).first()
    
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Contact is already a stakeholder"
        )
    
    db_stakeholder = ProjectStakeholder(
        project_id=project_id,
        contact_id=stakeholder.contact_id,
        role=stakeholder.role,
        how_they_help=stakeholder.how_they_help,
        how_we_help=stakeholder.how_we_help
    )
    
    db.add(db_stakeholder)
    db.commit()
    db.refresh(db_stakeholder)
    
    logger.info("stakeholder_added", project_id=project_id, contact_id=stakeholder.contact_id)
    return {"success": True, "stakeholder_id": db_stakeholder.id}


@router.delete("/{project_id}/stakeholders/{stakeholder_id}")
async def remove_stakeholder(
    project_id: str,
    stakeholder_id: str,
    db: Session = Depends(get_db)
):
    """Remove a stakeholder from a project"""
    stakeholder = db.query(ProjectStakeholder).filter(
        ProjectStakeholder.id == stakeholder_id,
        ProjectStakeholder.project_id == project_id
    ).first()
    
    if not stakeholder:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Stakeholder not found"
        )
    
    db.delete(stakeholder)
    db.commit()
    
    logger.info("stakeholder_removed", project_id=project_id, stakeholder_id=stakeholder_id)
    return {"success": True}


@router.delete("/{project_id}")
async def delete_project(project_id: str, db: Session = Depends(get_db)):
    """Delete a project"""
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found"
        )
    
    db.delete(project)
    db.commit()
    
    logger.info("project_deleted", project_id=project_id)
    return {"success": True}

