"""
Relationship Ops API Routes - Master Networker CRM
"""

from fastapi import APIRouter, HTTPException, Depends, status, BackgroundTasks
from sqlalchemy.orm import Session
from sqlalchemy import desc
from typing import List, Optional
from pydantic import BaseModel, Field
from datetime import datetime

from src.database.database import get_db
from src.database.models import DailyRunResult, RelationshipAction, Contact
from src.orchestrator.relationship_ops import RelationshipOpsService
from src.utils.logging import get_logger

router = APIRouter()
logger = get_logger(__name__)


# ============================================================================
# PYDANTIC MODELS
# ============================================================================

class RunTriggerRequest(BaseModel):
    run_type: str = Field(..., description="One of: morning, midday, afternoon, evening")
    force: bool = Field(default=False, description="Force run even if already executed today")


class RunTriggerResponse(BaseModel):
    run_id: str
    run_type: str
    status: str
    message: str


class DailyRunResponse(BaseModel):
    id: str
    run_type: str
    run_date: str
    status: str
    summary_title: Optional[str] = None
    summary_text: Optional[str] = None
    started_at: str
    completed_at: Optional[str] = None
    interactions_ingested: int
    contacts_updated: int
    top_actions: Optional[List[dict]] = None
    messages_to_reply: Optional[List[dict]] = None
    trust_risks: Optional[List[dict]] = None
    value_first_moves: Optional[List[dict]] = None
    intros_to_consider: Optional[List[dict]] = None
    approvals_needed: Optional[List[dict]] = None
    relationship_wins: Optional[List[dict]] = None
    relationship_slips: Optional[List[dict]] = None
    reconnect_tomorrow: Optional[List[dict]] = None
    health_score_trend: Optional[float] = None


class CommandCenterResponse(BaseModel):
    generated_at: str
    today_runs: List[dict]
    top_actions: List[dict]
    at_risk_commitments: List[dict]
    must_reply_messages: List[dict]
    pending_approvals_count: int
    ai_ready_actions: List[dict]


class ActionApprovalRequest(BaseModel):
    approved_by: str = Field(default="godfather")


class ActionDismissRequest(BaseModel):
    reason: Optional[str] = None


class RelationshipActionResponse(BaseModel):
    id: str
    action_type: str
    contact_id: Optional[str] = None
    contact_name: Optional[str] = None
    project_id: Optional[str] = None
    priority_score: float
    why_now: Optional[str] = None
    expected_win_win_outcome: Optional[str] = None
    risk_flags: Optional[List[str]] = None
    draft_message: Optional[str] = None
    draft_channel: Optional[str] = None
    requires_approval: bool
    status: str
    created_at: str
    expires_at: Optional[str] = None


# ============================================================================
# ROUTES
# ============================================================================

@router.post("/trigger", response_model=RunTriggerResponse)
async def trigger_run(
    request: RunTriggerRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """
    Manually trigger a relationship ops run.
    The run executes in the background and returns immediately.
    """
    if request.run_type not in ["morning", "midday", "afternoon", "evening"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid run_type: {request.run_type}. Must be one of: morning, midday, afternoon, evening"
        )
    
    service = RelationshipOpsService()
    
    # Execute in background
    def execute_run():
        from src.database.database import SessionLocal
        db_session = SessionLocal()
        try:
            service.execute_run(db_session, request.run_type, force=request.force)
        except Exception as e:
            logger.error("background_run_failed", run_type=request.run_type, error=str(e))
        finally:
            db_session.close()
    
    background_tasks.add_task(execute_run)
    
    return RunTriggerResponse(
        run_id="pending",
        run_type=request.run_type,
        status="triggered",
        message=f"{request.run_type.capitalize()} run triggered. Check /runs for results."
    )


@router.post("/trigger-sync", response_model=DailyRunResponse)
async def trigger_run_sync(
    request: RunTriggerRequest,
    db: Session = Depends(get_db)
):
    """
    Trigger a relationship ops run synchronously and wait for completion.
    Use for testing or when you need immediate results.
    """
    if request.run_type not in ["morning", "midday", "afternoon", "evening"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid run_type: {request.run_type}"
        )
    
    service = RelationshipOpsService()
    
    try:
        run = service.execute_run(db, request.run_type, force=request.force)
        return _format_run_response(run)
    except Exception as e:
        logger.error("sync_run_failed", run_type=request.run_type, error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Run failed: {str(e)}"
        )


@router.get("/runs", response_model=List[DailyRunResponse])
async def list_runs(
    limit: int = 20,
    run_type: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """List recent relationship ops runs"""
    query = db.query(DailyRunResult)
    
    if run_type:
        query = query.filter(DailyRunResult.run_type == run_type)
    
    runs = query.order_by(desc(DailyRunResult.run_date)).limit(limit).all()
    
    return [_format_run_response(run) for run in runs]


@router.get("/runs/{run_id}", response_model=DailyRunResponse)
async def get_run(
    run_id: str,
    db: Session = Depends(get_db)
):
    """Get details of a specific run"""
    run = db.query(DailyRunResult).filter(DailyRunResult.id == run_id).first()
    
    if not run:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Run not found"
        )
    
    return _format_run_response(run)


@router.get("/today", response_model=CommandCenterResponse)
async def get_today_command_center(db: Session = Depends(get_db)):
    """
    Get Today Command Center data - the primary view for daily relationship management.
    
    Returns:
    - Today's runs summaries
    - Top relationship actions (ranked)
    - At-risk commitments
    - Must-reply messages
    - Pending approvals count
    - AI-ready actions
    """
    service = RelationshipOpsService()
    data = service.get_today_command_center(db)
    return CommandCenterResponse(**data)


@router.get("/actions", response_model=List[RelationshipActionResponse])
async def list_actions(
    status_filter: Optional[str] = None,
    action_type: Optional[str] = None,
    contact_id: Optional[str] = None,
    limit: int = 50,
    db: Session = Depends(get_db)
):
    """List relationship actions with optional filters"""
    query = db.query(RelationshipAction)
    
    if status_filter:
        query = query.filter(RelationshipAction.status == status_filter)
    if action_type:
        query = query.filter(RelationshipAction.action_type == action_type)
    if contact_id:
        query = query.filter(RelationshipAction.contact_id == contact_id)
    
    actions = query.order_by(
        desc(RelationshipAction.priority_score),
        desc(RelationshipAction.created_at)
    ).limit(limit).all()
    
    return [_format_action_response(db, action) for action in actions]


@router.get("/actions/{action_id}", response_model=RelationshipActionResponse)
async def get_action(
    action_id: str,
    db: Session = Depends(get_db)
):
    """Get details of a specific action"""
    action = db.query(RelationshipAction).filter(RelationshipAction.id == action_id).first()
    
    if not action:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Action not found"
        )
    
    return _format_action_response(db, action)


@router.post("/actions/{action_id}/approve")
async def approve_action(
    action_id: str,
    request: ActionApprovalRequest,
    db: Session = Depends(get_db)
):
    """Approve a relationship action for execution"""
    service = RelationshipOpsService()
    
    try:
        action = service.approve_action(db, action_id, request.approved_by)
        return {
            "action_id": action.id,
            "status": action.status,
            "message": "Action approved successfully"
        }
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )


@router.post("/actions/{action_id}/dismiss")
async def dismiss_action(
    action_id: str,
    request: ActionDismissRequest,
    db: Session = Depends(get_db)
):
    """Dismiss/decline a relationship action"""
    service = RelationshipOpsService()
    
    try:
        action = service.dismiss_action(db, action_id, request.reason)
        return {
            "action_id": action.id,
            "status": action.status,
            "message": "Action dismissed"
        }
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )


@router.post("/actions/{action_id}/execute")
async def execute_action(
    action_id: str,
    db: Session = Depends(get_db)
):
    """Execute an approved relationship action (e.g., send message)"""
    service = RelationshipOpsService()
    
    try:
        result = service.execute_action(db, action_id)
        return result
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error("execute_action_failed", action_id=action_id, error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Execution failed: {str(e)}"
        )


@router.patch("/actions/{action_id}/draft")
async def update_action_draft(
    action_id: str,
    draft_message: str,
    draft_channel: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """Update the draft message for an action"""
    action = db.query(RelationshipAction).filter(RelationshipAction.id == action_id).first()
    
    if not action:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Action not found"
        )
    
    if action.status not in ["pending", "approved"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot update draft for action with status: {action.status}"
        )
    
    action.draft_message = draft_message
    if draft_channel:
        action.draft_channel = draft_channel
    
    db.commit()
    
    return {
        "action_id": action.id,
        "draft_message": action.draft_message,
        "draft_channel": action.draft_channel,
        "message": "Draft updated successfully"
    }


@router.get("/pending-approvals")
async def get_pending_approvals(
    limit: int = 20,
    db: Session = Depends(get_db)
):
    """Get all pending actions requiring approval"""
    actions = db.query(RelationshipAction).filter(
        RelationshipAction.status == "pending",
        RelationshipAction.requires_approval == True
    ).order_by(
        desc(RelationshipAction.priority_score),
        desc(RelationshipAction.created_at)
    ).limit(limit).all()
    
    return {
        "count": len(actions),
        "actions": [_format_action_response(db, action) for action in actions]
    }


@router.post("/batch-approve")
async def batch_approve_actions(
    action_ids: List[str],
    approved_by: str = "godfather",
    db: Session = Depends(get_db)
):
    """Approve multiple actions at once"""
    service = RelationshipOpsService()
    results = []
    
    for action_id in action_ids:
        try:
            action = service.approve_action(db, action_id, approved_by)
            results.append({
                "action_id": action_id,
                "status": "approved",
                "success": True
            })
        except Exception as e:
            results.append({
                "action_id": action_id,
                "status": "failed",
                "success": False,
                "error": str(e)
            })
    
    return {
        "total": len(action_ids),
        "approved": sum(1 for r in results if r["success"]),
        "failed": sum(1 for r in results if not r["success"]),
        "results": results
    }


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def _format_run_response(run: DailyRunResult) -> DailyRunResponse:
    """Format a DailyRunResult for API response"""
    return DailyRunResponse(
        id=run.id,
        run_type=run.run_type,
        run_date=run.run_date.isoformat(),
        status=run.status,
        summary_title=run.summary_title,
        summary_text=run.summary_text,
        started_at=run.started_at.isoformat(),
        completed_at=run.completed_at.isoformat() if run.completed_at else None,
        interactions_ingested=run.interactions_ingested or 0,
        contacts_updated=run.contacts_updated or 0,
        top_actions=run.top_actions,
        messages_to_reply=run.messages_to_reply,
        trust_risks=run.trust_risks,
        value_first_moves=run.value_first_moves,
        intros_to_consider=run.intros_to_consider,
        approvals_needed=run.approvals_needed,
        relationship_wins=run.relationship_wins,
        relationship_slips=run.relationship_slips,
        reconnect_tomorrow=run.reconnect_tomorrow,
        health_score_trend=run.health_score_trend
    )


def _format_action_response(db: Session, action: RelationshipAction) -> RelationshipActionResponse:
    """Format a RelationshipAction for API response"""
    contact_name = None
    if action.contact_id:
        contact = db.query(Contact).filter(Contact.id == action.contact_id).first()
        contact_name = contact.name if contact else None
    
    return RelationshipActionResponse(
        id=action.id,
        action_type=action.action_type,
        contact_id=action.contact_id,
        contact_name=contact_name,
        project_id=action.project_id,
        priority_score=action.priority_score or 0.5,
        why_now=action.why_now,
        expected_win_win_outcome=action.expected_win_win_outcome,
        risk_flags=action.risk_flags,
        draft_message=action.draft_message,
        draft_channel=action.draft_channel,
        requires_approval=action.requires_approval,
        status=action.status,
        created_at=action.created_at.isoformat(),
        expires_at=action.expires_at.isoformat() if action.expires_at else None
    )

