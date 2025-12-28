"""Call action endpoints (initiate, escalate, intervene, end)"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from datetime import datetime
import uuid

from src.database.database import get_db
from src.database.models import (
    Call, CallStatus, Escalation, EscalationStatus,
    HumanAgent, Notification
)
from src.api.schemas.calls import (
    CallInitiateRequest,
    EscalateRequest,
    InterveneRequest,
    EndCallRequest,
    CallResponse,
)
from src.telephony.call_handler import CallHandler
from src.telephony.twilio_client import TwilioService
from src.api.routes.websocket import (
    emit_call_started,
    emit_call_updated,
    emit_call_ended,
    emit_escalation_triggered,
    emit_notification_created,
)
from src.api.utils import handle_service_errors
from src.utils.logging import get_logger
from src.utils.errors import TelephonyError
from .utils import call_to_response

logger = get_logger(__name__)
router = APIRouter()
call_handler = CallHandler()
twilio_service = TwilioService()


@router.post("/initiate")
@handle_service_errors
async def initiate_call(
    request: CallInitiateRequest,
    db: Session = Depends(get_db),
):
    """Initiate an outbound call"""
    try:
        # Create call record in database (this also initiates Twilio call)
        call = call_handler.initiate_outbound_call(
            to_number=request.to_number,
            from_number=request.from_number or None,
            business_id=request.business_id,
            template_id=request.template_id,
            agent_id=request.agent_id,
            agent_personality=request.agent_personality,
            db=db,
        )
        
        # Update metadata if provided
        if request.metadata:
            if call.meta_data is None:
                call.meta_data = {}
            call.meta_data.update(request.metadata)
            db.commit()
            db.refresh(call)
        
        # Emit WebSocket event
        await emit_call_started(call_to_response(call, db))
        
        logger.info("call_initiated", call_id=call.id, call_sid=call.twilio_call_sid)
        return {"call": CallResponse.model_validate(call_to_response(call, db))}
    
    except TelephonyError as e:
        logger.error("call_initiation_failed", error=str(e), error_type=type(e).__name__)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.post("/{call_id}/escalate")
@handle_service_errors
async def escalate_call(
    call_id: str,
    request: EscalateRequest,
    db: Session = Depends(get_db),
):
    """Escalate a call to a human agent"""
    call = db.query(Call).filter(Call.id == call_id).first()
    
    if not call:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Call with ID {call_id} not found"
        )
    
    # Find available agent
    agent = None
    if request.agent_id:
        agent = db.query(HumanAgent).filter(
            HumanAgent.id == request.agent_id,
            HumanAgent.is_active == True,
            HumanAgent.is_available == True
        ).first()
    else:
        # Auto-assign: find first available agent
        agent = db.query(HumanAgent).filter(
            HumanAgent.is_active == True,
            HumanAgent.is_available == True
        ).first()
    
    if not agent:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No available agents found"
        )
    
    # Create escalation
    escalation = Escalation(
        call_id=call_id,
        status=EscalationStatus.PENDING,
        trigger_type="manual",
        trigger_details={"reason": request.reason} if request.reason else {},
        assigned_agent_id=agent.id,
        agent_name=agent.name,
        conversation_summary=request.context_note,
        context_data={},
    )
    
    db.add(escalation)
    call.status = CallStatus.ESCALATED
    agent.is_available = False
    db.commit()
    db.refresh(escalation)
    
    # Create notification for call escalation
    notification = Notification(
        id=str(uuid.uuid4()),
        user_id=current_user.id,
        type="call_escalated",
        title=f"Call {call_id[:8]}... Escalated",
        message=f"Call has been escalated to {agent.name}. Reason: {request.reason or 'Manual escalation'}",
        read=False,
        metadata={
            "call_id": call_id,
            "escalation_id": escalation.id,
            "agent_id": agent.id,
            "agent_name": agent.name,
        },
        action_url=f"/calls/{call_id}",
    )
    db.add(notification)
    db.commit()
    db.refresh(notification)
    
    # Emit WebSocket events
    escalation_data = {
        "id": escalation.id,
        "call_id": escalation.call_id,
        "status": escalation.status.value,
        "trigger_type": escalation.trigger_type,
        "assigned_agent_id": escalation.assigned_agent_id,
        "agent_name": escalation.agent_name,
    }
    await emit_escalation_triggered(call_id, escalation_data)
    await emit_call_updated(call_to_response(call, db))
    
    # Emit notification event
    notification_data = {
        "id": notification.id,
        "type": notification.type,
        "title": notification.title,
        "message": notification.message,
        "read": notification.read,
        "created_at": notification.created_at.isoformat(),
            "metadata": notification.meta_data,
        "action_url": notification.action_url,
    }
    await emit_notification_created(current_user.id, notification_data)
    
    # Return escalation in expected format
    escalation_response = {
        "id": escalation.id,
        "call_id": escalation.call_id,
        "status": escalation.status.value,
        "trigger_type": escalation.trigger_type,
        "trigger_details": escalation.trigger_details or {},
        "assigned_agent_id": escalation.assigned_agent_id,
        "agent_name": escalation.agent_name,
        "conversation_summary": escalation.conversation_summary,
        "context_data": escalation.context_data or {},
        "requested_at": escalation.requested_at.isoformat(),
        "accepted_at": escalation.accepted_at.isoformat() if escalation.accepted_at else None,
        "completed_at": escalation.completed_at.isoformat() if escalation.completed_at else None,
    }
    
    logger.info("call_escalated", call_id=call_id, agent_id=agent.id)
    return {"escalation": escalation_response}


@router.post("/{call_id}/intervene")
@handle_service_errors
async def intervene_in_call(
    call_id: str,
    request: InterveneRequest,
    db: Session = Depends(get_db),
):
    """Intervene in an active call"""
    # Verify call belongs to user's business configs
    user_business_ids = db.query(BusinessConfig.id).filter(
        BusinessConfig.created_by_user_id == current_user.id
    ).subquery()
    call = db.query(Call).filter(
        Call.id == call_id,
        Call.business_id.in_(db.query(user_business_ids))
    ).first()
    
    if not call:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Call with ID {call_id} not found"
        )
    
    if call.status == CallStatus.COMPLETED:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot intervene in completed call"
        )
    
    # Store intervention in metadata
    if call.meta_data is None:
        call.meta_data = {}
    interventions = call.meta_data.get("interventions", [])
    interventions.append({
        "action": request.action,
        "message": request.message,
        "instructions": request.instructions,
        "timestamp": datetime.utcnow().isoformat(),
    })
    call.meta_data["interventions"] = interventions
    db.commit()
    db.refresh(call)
    
    # Emit WebSocket event
    await emit_call_updated(call_to_response(call, db))
    
    logger.info("call_intervened", call_id=call_id, action=request.action)
    return {"success": True, "message": "Intervention applied successfully"}


@router.post("/{call_id}/end")
@handle_service_errors
async def end_call(
    call_id: str,
    request: EndCallRequest,
    db: Session = Depends(get_db),
):
    """End an active call"""
    # Verify call belongs to user's business configs
    user_business_ids = db.query(BusinessConfig.id).filter(
        BusinessConfig.created_by_user_id == current_user.id
    ).subquery()
    call = db.query(Call).filter(
        Call.id == call_id,
        Call.business_id.in_(db.query(user_business_ids))
    ).first()
    
    if not call:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Call with ID {call_id} not found"
        )
    
    if call.status == CallStatus.COMPLETED:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Call is already completed"
        )
    
    # End call via Twilio if active
    if call.twilio_call_sid and call.status in [CallStatus.IN_PROGRESS, CallStatus.RINGING]:
        try:
            twilio_service.update_call(call.twilio_call_sid, status="completed")
        except Exception as e:
            logger.error("twilio_end_call_failed", error=str(e), error_type=type(e).__name__, call_sid=call.twilio_call_sid)
    
    # Update call status
    call.status = CallStatus.COMPLETED
    call.ended_at = datetime.utcnow()
    
    if request.reason or request.notes:
        if call.meta_data is None:
            call.meta_data = {}
        notes = call.meta_data.get("notes", [])
        notes.append({
            "type": "end_call",
            "reason": request.reason,
            "notes": request.notes,
            "timestamp": datetime.utcnow().isoformat(),
        })
        call.meta_data["notes"] = notes
    
    db.commit()
    db.refresh(call)
    
    # Emit WebSocket events
    await emit_call_ended(call_id)
    await emit_call_updated(call_to_response(call, db))
    
    logger.info("call_ended", call_id=call_id)
    return {"call": CallResponse.model_validate(call_to_response(call, db))}

