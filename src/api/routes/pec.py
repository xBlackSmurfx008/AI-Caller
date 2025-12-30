"""
Project Execution Confirmation (PEC) API Routes

Provides endpoints for generating, managing, and approving PECs.
"""

from fastapi import APIRouter, HTTPException, Depends, status
from sqlalchemy.orm import Session
from typing import Optional, List
from pydantic import BaseModel
from datetime import datetime

from src.database.database import get_db
from src.database.models import Project, ProjectExecutionConfirmation
from src.orchestrator.pec_generator import PECGenerator
from src.utils.logging import get_logger

router = APIRouter()
logger = get_logger(__name__)
pec_generator = PECGenerator()


# ============================================================================
# Pydantic Models
# ============================================================================

class PECGenerateRequest(BaseModel):
    """Request to generate a new PEC"""
    include_cost_estimate: bool = True


class PECApprovalRequest(BaseModel):
    """Request to approve a PEC"""
    approved_by: str = "user"
    approval_notes: Optional[str] = None


class ChecklistItemUpdate(BaseModel):
    """Update a checklist item status"""
    item: str
    status: str  # "pending", "approved", "rejected"


class PECResponse(BaseModel):
    """PEC response model"""
    id: str
    project_id: str
    version: int
    status: str
    execution_gate: str
    summary: Optional[dict] = None
    deliverables: Optional[list] = None
    milestones: Optional[list] = None
    task_plan: Optional[list] = None
    task_tool_map: Optional[list] = None
    dependencies: Optional[list] = None
    risks: Optional[list] = None
    preferences_applied: Optional[list] = None
    constraints_applied: Optional[list] = None
    assumptions: Optional[list] = None
    gaps: Optional[list] = None
    cost_estimate: Optional[dict] = None
    approval_checklist: Optional[list] = None
    stakeholders: Optional[list] = None
    approved_by: Optional[str] = None
    approved_at: Optional[str] = None
    approval_notes: Optional[str] = None
    created_at: str
    updated_at: str

    class Config:
        from_attributes = True


# ============================================================================
# PEC Generation Endpoints
# ============================================================================

@router.post("/projects/{project_id}/pec", response_model=PECResponse)
async def generate_pec(
    project_id: str,
    request: Optional[PECGenerateRequest] = None,
    db: Session = Depends(get_db)
):
    """
    Generate a new Project Execution Confirmation for a project.
    
    This creates a PEC that validates:
    - Project scope and deliverables
    - Task-tool mapping and feasibility
    - Preferences and constraints
    - Risks and gaps
    - Execution readiness
    """
    # Verify project exists
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found"
        )
    
    # Check for existing active PEC
    existing_pec = db.query(ProjectExecutionConfirmation).filter(
        ProjectExecutionConfirmation.project_id == project_id,
        ProjectExecutionConfirmation.status.in_(["draft", "pending_approval"])
    ).first()
    
    # Get version number
    max_version = db.query(ProjectExecutionConfirmation).filter(
        ProjectExecutionConfirmation.project_id == project_id
    ).count()
    new_version = max_version + 1
    
    try:
        # Generate PEC
        include_cost = request.include_cost_estimate if request else True
        pec_data = pec_generator.generate_pec(
            db, 
            project_id,
            include_cost_estimate=include_cost
        )
        
        # Mark existing PEC as superseded if exists
        if existing_pec:
            existing_pec.status = "superseded"
            previous_pec_id = existing_pec.id
        else:
            previous_pec_id = None
        
        # Create PEC record
        pec = ProjectExecutionConfirmation(
            id=pec_data["pec_id"],
            project_id=project_id,
            version=new_version,
            status="draft",
            execution_gate=pec_data["execution_gate"],
            summary=pec_data["summary"],
            deliverables=pec_data["deliverables"],
            milestones=pec_data["milestones"],
            task_plan=pec_data["task_plan"],
            task_tool_map=pec_data["task_tool_map"],
            dependencies=pec_data["dependencies"],
            risks=pec_data["risks"],
            preferences_applied=pec_data["preferences_applied"],
            constraints_applied=pec_data["constraints_applied"],
            assumptions=pec_data["assumptions"],
            gaps=pec_data["gaps"],
            cost_estimate=pec_data["cost_estimate"],
            approval_checklist=pec_data["approval_checklist"],
            stakeholders=pec_data["stakeholders"],
            previous_pec_id=previous_pec_id
        )
        
        db.add(pec)
        db.commit()
        db.refresh(pec)
        
        logger.info("pec_created", project_id=project_id, pec_id=pec.id, version=new_version)
        
        return PECResponse(
            id=pec.id,
            project_id=pec.project_id,
            version=pec.version,
            status=pec.status,
            execution_gate=pec.execution_gate,
            summary=pec.summary,
            deliverables=pec.deliverables,
            milestones=pec.milestones,
            task_plan=pec.task_plan,
            task_tool_map=pec.task_tool_map,
            dependencies=pec.dependencies,
            risks=pec.risks,
            preferences_applied=pec.preferences_applied,
            constraints_applied=pec.constraints_applied,
            assumptions=pec.assumptions,
            gaps=pec.gaps,
            cost_estimate=pec.cost_estimate,
            approval_checklist=pec.approval_checklist,
            stakeholders=pec.stakeholders,
            approved_by=pec.approved_by,
            approved_at=pec.approved_at.isoformat() if pec.approved_at else None,
            approval_notes=pec.approval_notes,
            created_at=pec.created_at.isoformat(),
            updated_at=pec.updated_at.isoformat()
        )
    except Exception as e:
        logger.error("pec_generation_failed", project_id=project_id, error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate PEC: {str(e)}"
        )


@router.get("/projects/{project_id}/pec", response_model=Optional[PECResponse])
async def get_current_pec(
    project_id: str,
    db: Session = Depends(get_db)
):
    """
    Get the current (latest) PEC for a project.
    Returns the most recent non-superseded PEC.
    """
    pec = db.query(ProjectExecutionConfirmation).filter(
        ProjectExecutionConfirmation.project_id == project_id,
        ProjectExecutionConfirmation.status != "superseded"
    ).order_by(ProjectExecutionConfirmation.version.desc()).first()
    
    if not pec:
        return None
    
    return PECResponse(
        id=pec.id,
        project_id=pec.project_id,
        version=pec.version,
        status=pec.status,
        execution_gate=pec.execution_gate,
        summary=pec.summary,
        deliverables=pec.deliverables,
        milestones=pec.milestones,
        task_plan=pec.task_plan,
        task_tool_map=pec.task_tool_map,
        dependencies=pec.dependencies,
        risks=pec.risks,
        preferences_applied=pec.preferences_applied,
        constraints_applied=pec.constraints_applied,
        assumptions=pec.assumptions,
        gaps=pec.gaps,
        cost_estimate=pec.cost_estimate,
        approval_checklist=pec.approval_checklist,
        stakeholders=pec.stakeholders,
        approved_by=pec.approved_by,
        approved_at=pec.approved_at.isoformat() if pec.approved_at else None,
        approval_notes=pec.approval_notes,
        created_at=pec.created_at.isoformat(),
        updated_at=pec.updated_at.isoformat()
    )


@router.get("/projects/{project_id}/pec/history", response_model=List[PECResponse])
async def get_pec_history(
    project_id: str,
    db: Session = Depends(get_db)
):
    """
    Get all PEC versions for a project (audit trail).
    """
    pecs = db.query(ProjectExecutionConfirmation).filter(
        ProjectExecutionConfirmation.project_id == project_id
    ).order_by(ProjectExecutionConfirmation.version.desc()).all()
    
    return [
        PECResponse(
            id=pec.id,
            project_id=pec.project_id,
            version=pec.version,
            status=pec.status,
            execution_gate=pec.execution_gate,
            summary=pec.summary,
            deliverables=pec.deliverables,
            milestones=pec.milestones,
            task_plan=pec.task_plan,
            task_tool_map=pec.task_tool_map,
            dependencies=pec.dependencies,
            risks=pec.risks,
            preferences_applied=pec.preferences_applied,
            constraints_applied=pec.constraints_applied,
            assumptions=pec.assumptions,
            gaps=pec.gaps,
            cost_estimate=pec.cost_estimate,
            approval_checklist=pec.approval_checklist,
            stakeholders=pec.stakeholders,
            approved_by=pec.approved_by,
            approved_at=pec.approved_at.isoformat() if pec.approved_at else None,
            approval_notes=pec.approval_notes,
            created_at=pec.created_at.isoformat(),
            updated_at=pec.updated_at.isoformat()
        )
        for pec in pecs
    ]


@router.get("/pec/{pec_id}", response_model=PECResponse)
async def get_pec_by_id(
    pec_id: str,
    db: Session = Depends(get_db)
):
    """
    Get a specific PEC by ID.
    """
    pec = db.query(ProjectExecutionConfirmation).filter(
        ProjectExecutionConfirmation.id == pec_id
    ).first()
    
    if not pec:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="PEC not found"
        )
    
    return PECResponse(
        id=pec.id,
        project_id=pec.project_id,
        version=pec.version,
        status=pec.status,
        execution_gate=pec.execution_gate,
        summary=pec.summary,
        deliverables=pec.deliverables,
        milestones=pec.milestones,
        task_plan=pec.task_plan,
        task_tool_map=pec.task_tool_map,
        dependencies=pec.dependencies,
        risks=pec.risks,
        preferences_applied=pec.preferences_applied,
        constraints_applied=pec.constraints_applied,
        assumptions=pec.assumptions,
        gaps=pec.gaps,
        cost_estimate=pec.cost_estimate,
        approval_checklist=pec.approval_checklist,
        stakeholders=pec.stakeholders,
        approved_by=pec.approved_by,
        approved_at=pec.approved_at.isoformat() if pec.approved_at else None,
        approval_notes=pec.approval_notes,
        created_at=pec.created_at.isoformat(),
        updated_at=pec.updated_at.isoformat()
    )


# ============================================================================
# PEC Approval Endpoints
# ============================================================================

@router.post("/pec/{pec_id}/approve", response_model=PECResponse)
async def approve_pec(
    pec_id: str,
    request: PECApprovalRequest,
    db: Session = Depends(get_db)
):
    """
    Approve a PEC and mark it ready for execution.
    
    A PEC must be in 'draft' or 'pending_approval' status to be approved.
    Blocked PECs cannot be approved until blocking issues are resolved.
    """
    pec = db.query(ProjectExecutionConfirmation).filter(
        ProjectExecutionConfirmation.id == pec_id
    ).first()
    
    if not pec:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="PEC not found"
        )
    
    if pec.status not in ["draft", "pending_approval"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot approve PEC with status '{pec.status}'"
        )
    
    if pec.execution_gate == "BLOCKED":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot approve blocked PEC. Resolve blocking issues first."
        )
    
    # Approve PEC
    pec.status = "approved"
    pec.approved_by = request.approved_by
    pec.approved_at = datetime.utcnow()
    pec.approval_notes = request.approval_notes
    
    db.commit()
    db.refresh(pec)
    
    logger.info("pec_approved", pec_id=pec_id, approved_by=request.approved_by)
    
    return PECResponse(
        id=pec.id,
        project_id=pec.project_id,
        version=pec.version,
        status=pec.status,
        execution_gate=pec.execution_gate,
        summary=pec.summary,
        deliverables=pec.deliverables,
        milestones=pec.milestones,
        task_plan=pec.task_plan,
        task_tool_map=pec.task_tool_map,
        dependencies=pec.dependencies,
        risks=pec.risks,
        preferences_applied=pec.preferences_applied,
        constraints_applied=pec.constraints_applied,
        assumptions=pec.assumptions,
        gaps=pec.gaps,
        cost_estimate=pec.cost_estimate,
        approval_checklist=pec.approval_checklist,
        stakeholders=pec.stakeholders,
        approved_by=pec.approved_by,
        approved_at=pec.approved_at.isoformat() if pec.approved_at else None,
        approval_notes=pec.approval_notes,
        created_at=pec.created_at.isoformat(),
        updated_at=pec.updated_at.isoformat()
    )


@router.post("/pec/{pec_id}/reject", response_model=PECResponse)
async def reject_pec(
    pec_id: str,
    request: PECApprovalRequest,
    db: Session = Depends(get_db)
):
    """
    Reject a PEC.
    """
    pec = db.query(ProjectExecutionConfirmation).filter(
        ProjectExecutionConfirmation.id == pec_id
    ).first()
    
    if not pec:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="PEC not found"
        )
    
    if pec.status not in ["draft", "pending_approval"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot reject PEC with status '{pec.status}'"
        )
    
    # Reject PEC
    pec.status = "rejected"
    pec.approval_notes = request.approval_notes
    
    db.commit()
    db.refresh(pec)
    
    logger.info("pec_rejected", pec_id=pec_id)
    
    return PECResponse(
        id=pec.id,
        project_id=pec.project_id,
        version=pec.version,
        status=pec.status,
        execution_gate=pec.execution_gate,
        summary=pec.summary,
        deliverables=pec.deliverables,
        milestones=pec.milestones,
        task_plan=pec.task_plan,
        task_tool_map=pec.task_tool_map,
        dependencies=pec.dependencies,
        risks=pec.risks,
        preferences_applied=pec.preferences_applied,
        constraints_applied=pec.constraints_applied,
        assumptions=pec.assumptions,
        gaps=pec.gaps,
        cost_estimate=pec.cost_estimate,
        approval_checklist=pec.approval_checklist,
        stakeholders=pec.stakeholders,
        approved_by=pec.approved_by,
        approved_at=pec.approved_at.isoformat() if pec.approved_at else None,
        approval_notes=pec.approval_notes,
        created_at=pec.created_at.isoformat(),
        updated_at=pec.updated_at.isoformat()
    )


@router.put("/pec/{pec_id}/checklist", response_model=PECResponse)
async def update_checklist_item(
    pec_id: str,
    update: ChecklistItemUpdate,
    db: Session = Depends(get_db)
):
    """
    Update a checklist item status.
    """
    pec = db.query(ProjectExecutionConfirmation).filter(
        ProjectExecutionConfirmation.id == pec_id
    ).first()
    
    if not pec:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="PEC not found"
        )
    
    if pec.status not in ["draft", "pending_approval"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot update checklist for approved/rejected PEC"
        )
    
    # Update checklist item
    checklist = pec.approval_checklist or []
    item_found = False
    for item in checklist:
        if item.get("item") == update.item:
            item["status"] = update.status
            item_found = True
            break
    
    if not item_found:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Checklist item '{update.item}' not found"
        )
    
    pec.approval_checklist = checklist
    db.commit()
    db.refresh(pec)
    
    return PECResponse(
        id=pec.id,
        project_id=pec.project_id,
        version=pec.version,
        status=pec.status,
        execution_gate=pec.execution_gate,
        summary=pec.summary,
        deliverables=pec.deliverables,
        milestones=pec.milestones,
        task_plan=pec.task_plan,
        task_tool_map=pec.task_tool_map,
        dependencies=pec.dependencies,
        risks=pec.risks,
        preferences_applied=pec.preferences_applied,
        constraints_applied=pec.constraints_applied,
        assumptions=pec.assumptions,
        gaps=pec.gaps,
        cost_estimate=pec.cost_estimate,
        approval_checklist=pec.approval_checklist,
        stakeholders=pec.stakeholders,
        approved_by=pec.approved_by,
        approved_at=pec.approved_at.isoformat() if pec.approved_at else None,
        approval_notes=pec.approval_notes,
        created_at=pec.created_at.isoformat(),
        updated_at=pec.updated_at.isoformat()
    )


# ============================================================================
# PEC Regeneration Endpoint
# ============================================================================

@router.post("/pec/{pec_id}/regenerate", response_model=PECResponse)
async def regenerate_pec(
    pec_id: str,
    reason: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """
    Regenerate a PEC after changes to the project or tasks.
    Creates a new version of the PEC and marks the old one as superseded.
    """
    existing_pec = db.query(ProjectExecutionConfirmation).filter(
        ProjectExecutionConfirmation.id == pec_id
    ).first()
    
    if not existing_pec:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="PEC not found"
        )
    
    project_id = existing_pec.project_id
    
    # Generate new PEC
    pec_data = pec_generator.regenerate_pec(
        db, project_id, previous_pec_id=pec_id
    )
    
    # Mark existing PEC as superseded
    existing_pec.status = "superseded"
    
    # Create new PEC
    new_version = existing_pec.version + 1
    
    pec = ProjectExecutionConfirmation(
        id=pec_data["pec_id"],
        project_id=project_id,
        version=new_version,
        status="draft",
        execution_gate=pec_data["execution_gate"],
        summary=pec_data["summary"],
        deliverables=pec_data["deliverables"],
        milestones=pec_data["milestones"],
        task_plan=pec_data["task_plan"],
        task_tool_map=pec_data["task_tool_map"],
        dependencies=pec_data["dependencies"],
        risks=pec_data["risks"],
        preferences_applied=pec_data["preferences_applied"],
        constraints_applied=pec_data["constraints_applied"],
        assumptions=pec_data["assumptions"],
        gaps=pec_data["gaps"],
        cost_estimate=pec_data["cost_estimate"],
        approval_checklist=pec_data["approval_checklist"],
        stakeholders=pec_data["stakeholders"],
        previous_pec_id=pec_id,
        change_reason=reason
    )
    
    db.add(pec)
    db.commit()
    db.refresh(pec)
    
    logger.info("pec_regenerated", project_id=project_id, pec_id=pec.id, version=new_version)
    
    return PECResponse(
        id=pec.id,
        project_id=pec.project_id,
        version=pec.version,
        status=pec.status,
        execution_gate=pec.execution_gate,
        summary=pec.summary,
        deliverables=pec.deliverables,
        milestones=pec.milestones,
        task_plan=pec.task_plan,
        task_tool_map=pec.task_tool_map,
        dependencies=pec.dependencies,
        risks=pec.risks,
        preferences_applied=pec.preferences_applied,
        constraints_applied=pec.constraints_applied,
        assumptions=pec.assumptions,
        gaps=pec.gaps,
        cost_estimate=pec.cost_estimate,
        approval_checklist=pec.approval_checklist,
        stakeholders=pec.stakeholders,
        approved_by=pec.approved_by,
        approved_at=pec.approved_at.isoformat() if pec.approved_at else None,
        approval_notes=pec.approval_notes,
        created_at=pec.created_at.isoformat(),
        updated_at=pec.updated_at.isoformat()
    )


# ============================================================================
# Execution Gate Check
# ============================================================================

@router.get("/projects/{project_id}/execution-ready")
async def check_execution_ready(
    project_id: str,
    db: Session = Depends(get_db)
):
    """
    Check if a project is ready for execution.
    Returns the execution gate status and any blocking issues.
    """
    # Get latest approved PEC
    pec = db.query(ProjectExecutionConfirmation).filter(
        ProjectExecutionConfirmation.project_id == project_id,
        ProjectExecutionConfirmation.status == "approved"
    ).order_by(ProjectExecutionConfirmation.version.desc()).first()
    
    if not pec:
        # Check if there's a draft PEC
        draft_pec = db.query(ProjectExecutionConfirmation).filter(
            ProjectExecutionConfirmation.project_id == project_id,
            ProjectExecutionConfirmation.status == "draft"
        ).first()
        
        if draft_pec:
            return {
                "execution_ready": False,
                "reason": "PEC requires approval",
                "pec_id": draft_pec.id,
                "execution_gate": draft_pec.execution_gate,
                "blocking_issues": draft_pec.gaps or []
            }
        else:
            return {
                "execution_ready": False,
                "reason": "No PEC generated for this project",
                "pec_id": None,
                "execution_gate": None,
                "blocking_issues": []
            }
    
    # Check if PEC is still valid (project not modified since PEC creation)
    project = db.query(Project).filter(Project.id == project_id).first()
    if project and project.updated_at > pec.created_at:
        return {
            "execution_ready": False,
            "reason": "Project modified since PEC approval - regeneration recommended",
            "pec_id": pec.id,
            "execution_gate": pec.execution_gate,
            "blocking_issues": [],
            "stale": True
        }
    
    return {
        "execution_ready": pec.execution_gate in ["READY", "READY_WITH_QUESTIONS"],
        "reason": None if pec.execution_gate == "READY" else "Some tasks require approval during execution",
        "pec_id": pec.id,
        "execution_gate": pec.execution_gate,
        "blocking_issues": [],
        "approved_at": pec.approved_at.isoformat() if pec.approved_at else None
    }

