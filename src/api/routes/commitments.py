"""Commitments API routes for managing promises and commitments"""

from fastapi import APIRouter, HTTPException, Depends, status
from sqlalchemy.orm import Session
from typing import List, Optional
from pydantic import BaseModel
from datetime import datetime

from src.database.database import get_db
from src.database.models import Commitment, Contact, Project
from src.orchestrator.commitment_manager import CommitmentManager
from src.utils.logging import get_logger

router = APIRouter()
logger = get_logger(__name__)
commitment_manager = CommitmentManager()


class CommitmentCreate(BaseModel):
    contact_id: Optional[str] = None
    project_id: Optional[str] = None
    description: str
    committed_by: str  # "godfather" or "contact"
    deadline: Optional[str] = None  # ISO format


class CommitmentUpdate(BaseModel):
    description: Optional[str] = None
    status: Optional[str] = None
    deadline: Optional[str] = None


class CommitmentResponse(BaseModel):
    id: str
    contact_id: Optional[str] = None
    project_id: Optional[str] = None
    description: str
    committed_by: str
    deadline: Optional[str] = None
    status: str
    is_trust_risk: bool
    created_at: str
    updated_at: str

    class Config:
        from_attributes = True


@router.post("/", response_model=CommitmentResponse)
async def create_commitment(
    commitment: CommitmentCreate,
    db: Session = Depends(get_db)
):
    """Create a new commitment"""
    # Validate contact exists if provided
    if commitment.contact_id:
        contact = db.query(Contact).filter(Contact.id == commitment.contact_id).first()
        if not contact:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Contact not found"
            )
    
    # Validate project exists if provided
    if commitment.project_id:
        project = db.query(Project).filter(Project.id == commitment.project_id).first()
        if not project:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Project not found"
            )
    
    # Validate committed_by
    if commitment.committed_by not in ["godfather", "contact"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="committed_by must be 'godfather' or 'contact'"
        )
    
    # Parse deadline
    deadline = None
    if commitment.deadline:
        try:
            deadline = datetime.fromisoformat(commitment.deadline.replace('Z', '+00:00'))
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid deadline format. Use ISO 8601 format."
            )
    
    db_commitment = Commitment(
        contact_id=commitment.contact_id,
        project_id=commitment.project_id,
        description=commitment.description,
        committed_by=commitment.committed_by,
        deadline=deadline,
        status="pending"
    )
    
    db.add(db_commitment)
    db.commit()
    db.refresh(db_commitment)
    
    logger.info("commitment_created", commitment_id=db_commitment.id)
    return _commitment_to_response(db_commitment)


@router.get("/", response_model=List[CommitmentResponse])
async def list_commitments(
    contact_id: Optional[str] = None,
    project_id: Optional[str] = None,
    status: Optional[str] = None,
    trust_risk_only: bool = False,
    db: Session = Depends(get_db)
):
    """List commitments with optional filters"""
    query = db.query(Commitment)
    
    if contact_id:
        query = query.filter(Commitment.contact_id == contact_id)
    if project_id:
        query = query.filter(Commitment.project_id == project_id)
    if status:
        query = query.filter(Commitment.status == status)
    if trust_risk_only:
        query = query.filter(Commitment.is_trust_risk == True)
    
    commitments = query.order_by(Commitment.deadline.asc()).all()
    return [_commitment_to_response(c) for c in commitments]


@router.get("/trust-risks", response_model=List[CommitmentResponse])
async def get_trust_risk_commitments(db: Session = Depends(get_db)):
    """Get all commitments flagged as trust risks"""
    commitments = commitment_manager.get_trust_risk_commitments(db)
    return [_commitment_to_response(c) for c in commitments]


@router.get("/{commitment_id}", response_model=CommitmentResponse)
async def get_commitment(commitment_id: str, db: Session = Depends(get_db)):
    """Get a specific commitment"""
    commitment = db.query(Commitment).filter(Commitment.id == commitment_id).first()
    if not commitment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Commitment not found"
        )
    
    return _commitment_to_response(commitment)


@router.put("/{commitment_id}", response_model=CommitmentResponse)
async def update_commitment(
    commitment_id: str,
    update: CommitmentUpdate,
    db: Session = Depends(get_db)
):
    """Update a commitment"""
    db_commitment = db.query(Commitment).filter(Commitment.id == commitment_id).first()
    if not db_commitment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Commitment not found"
        )
    
    if update.description is not None:
        db_commitment.description = update.description
    if update.status is not None:
        if update.status not in ["pending", "completed", "overdue", "cancelled"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid status. Must be: pending, completed, overdue, or cancelled"
            )
        db_commitment.status = update.status
        # Clear trust risk if completed
        if update.status == "completed":
            db_commitment.is_trust_risk = False
    if update.deadline is not None:
        try:
            db_commitment.deadline = datetime.fromisoformat(update.deadline.replace('Z', '+00:00'))
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid deadline format. Use ISO 8601 format."
            )
    
    db.commit()
    db.refresh(db_commitment)
    
    logger.info("commitment_updated", commitment_id=commitment_id)
    return _commitment_to_response(db_commitment)


@router.post("/update-overdue")
async def update_overdue_commitments(db: Session = Depends(get_db)):
    """Manually trigger update of overdue commitments"""
    count = commitment_manager.update_overdue_commitments(db)
    return {
        "success": True,
        "commitments_marked_overdue": count
    }


@router.delete("/{commitment_id}")
async def delete_commitment(commitment_id: str, db: Session = Depends(get_db)):
    """Delete a commitment"""
    commitment = db.query(Commitment).filter(Commitment.id == commitment_id).first()
    if not commitment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Commitment not found"
        )
    
    db.delete(commitment)
    db.commit()
    
    logger.info("commitment_deleted", commitment_id=commitment_id)
    return {"success": True}


def _commitment_to_response(commitment: Commitment) -> CommitmentResponse:
    """Convert Commitment model to CommitmentResponse"""
    return CommitmentResponse(
        id=commitment.id,
        contact_id=commitment.contact_id,
        project_id=commitment.project_id,
        description=commitment.description,
        committed_by=commitment.committed_by,
        deadline=commitment.deadline.isoformat() if commitment.deadline else None,
        status=commitment.status,
        is_trust_risk=commitment.is_trust_risk,
        created_at=commitment.created_at.isoformat(),
        updated_at=commitment.updated_at.isoformat()
    )

