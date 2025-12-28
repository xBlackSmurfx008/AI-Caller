"""Phone number management routes"""

import uuid
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session

from src.database.database import get_db
from src.database.models import (
    PhoneNumber,
    AgentPhoneNumber,
    BusinessPhoneNumber,
    HumanAgent,
    BusinessConfig,
)
from src.database.schemas import (
    PhoneNumberCreate,
    PhoneNumberUpdate,
    PhoneNumberResponse,
    PhoneNumberSearchRequest,
    PhoneNumberPurchaseRequest,
    PhoneNumberAssignmentRequest,
)
from src.telephony.twilio_client import TwilioService
from src.api.utils import handle_service_errors_sync
from src.utils.logging import get_logger
from src.utils.errors import TelephonyError

logger = get_logger(__name__)
router = APIRouter()
twilio_service = TwilioService()


@router.get("/", response_model=List[PhoneNumberResponse])
@handle_service_errors_sync
def list_phone_numbers(
    status_filter: Optional[str] = Query(None, alias="status"),
    is_active: Optional[bool] = Query(None),
    country_code: Optional[str] = Query(None),
    db: Session = Depends(get_db),
):
    """List all phone numbers with optional filters"""
    query = db.query(PhoneNumber)
    
    if status_filter:
        query = query.filter(PhoneNumber.status == status_filter)
    if is_active is not None:
        query = query.filter(PhoneNumber.is_active == is_active)
    if country_code:
        query = query.filter(PhoneNumber.country_code == country_code)
    
    phone_numbers = query.order_by(PhoneNumber.created_at.desc()).all()
    return [PhoneNumberResponse.model_validate(pn) for pn in phone_numbers]


@router.get("/{phone_id}", response_model=PhoneNumberResponse)
@handle_service_errors_sync
def get_phone_number(
    phone_id: str,
    db: Session = Depends(get_db),
):
    """Get phone number details"""
    phone_number = db.query(PhoneNumber).filter(PhoneNumber.id == phone_id).first()
    
    if not phone_number:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Phone number with ID {phone_id} not found"
        )
    
    return PhoneNumberResponse.model_validate(phone_number)


@router.post("/", status_code=status.HTTP_201_CREATED, response_model=PhoneNumberResponse)
@handle_service_errors_sync
def create_phone_number(
    phone_data: PhoneNumberCreate,
    db: Session = Depends(get_db),
):
    """Add a phone number (manual entry)"""
    # Check if phone number already exists
    existing = db.query(PhoneNumber).filter(
        PhoneNumber.phone_number == phone_data.phone_number
    ).first()
    
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Phone number {phone_data.phone_number} already exists"
        )
    
    # Validate phone number format
    if not twilio_service.validate_phone_number(phone_data.phone_number):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid phone number format: {phone_data.phone_number}. Must be E.164 format (e.g., +1234567890)"
        )
    
    phone_number = PhoneNumber(
        id=str(uuid.uuid4()),
        phone_number=phone_data.phone_number,
        twilio_phone_sid=phone_data.twilio_phone_sid,
        friendly_name=phone_data.friendly_name,
        country_code=phone_data.country_code,
        region=phone_data.region,
        capabilities=phone_data.capabilities or {},
        status=phone_data.status,
        webhook_url=phone_data.webhook_url,
        webhook_method=phone_data.webhook_method,
        is_active=phone_data.is_active,
        meta_data=phone_data.metadata or {},
    )
    
    db.add(phone_number)
    db.commit()
    db.refresh(phone_number)
    
    logger.info("phone_number_created", phone_id=phone_number.id, phone_number=phone_number.phone_number)
    return PhoneNumberResponse.model_validate(phone_number)


@router.put("/{phone_id}", response_model=PhoneNumberResponse)
@handle_service_errors_sync
def update_phone_number(
    phone_id: str,
    phone_data: PhoneNumberUpdate,
    db: Session = Depends(get_db),
):
    """Update phone number configuration"""
    phone_number = db.query(PhoneNumber).filter(PhoneNumber.id == phone_id).first()
    
    if not phone_number:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Phone number with ID {phone_id} not found"
        )
    
    # Update fields
    if phone_data.friendly_name is not None:
        phone_number.friendly_name = phone_data.friendly_name
    if phone_data.webhook_url is not None:
        phone_number.webhook_url = phone_data.webhook_url
        # Update webhook in Twilio if phone has SID
        if phone_number.twilio_phone_sid:
            try:
                twilio_service.update_phone_number_config(
                    phone_number.twilio_phone_sid,
                    phone_data.webhook_url,
                    phone_data.webhook_method or phone_number.webhook_method,
                )
            except TelephonyError as e:
                logger.warning("twilio_webhook_update_failed", error=str(e), phone_id=phone_id)
    if phone_data.webhook_method is not None:
        phone_number.webhook_method = phone_data.webhook_method
    if phone_data.is_active is not None:
        phone_number.is_active = phone_data.is_active
    if phone_data.metadata is not None:
        phone_number.meta_data = phone_data.metadata
    
    db.commit()
    db.refresh(phone_number)
    
    logger.info("phone_number_updated", phone_id=phone_id)
    return PhoneNumberResponse.model_validate(phone_number)


@router.delete("/{phone_id}", status_code=status.HTTP_204_NO_CONTENT)
@handle_service_errors_sync
def delete_phone_number(
    phone_id: str,
    db: Session = Depends(get_db),
):
    """Release/delete a phone number"""
    phone_number = db.query(PhoneNumber).filter(PhoneNumber.id == phone_id).first()
    
    if not phone_number:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Phone number with ID {phone_id} not found"
        )
    
    # Release from Twilio if it has a SID
    if phone_number.twilio_phone_sid:
        try:
            twilio_service.release_phone_number(phone_number.twilio_phone_sid)
        except TelephonyError as e:
            logger.warning("twilio_release_failed", error=str(e), phone_id=phone_id)
            # Continue with deletion even if Twilio release fails
    
    # Delete all assignments
    db.query(AgentPhoneNumber).filter(AgentPhoneNumber.phone_number_id == phone_id).delete()
    db.query(BusinessPhoneNumber).filter(BusinessPhoneNumber.phone_number_id == phone_id).delete()
    
    # Delete phone number
    db.delete(phone_number)
    db.commit()
    
    logger.info("phone_number_deleted", phone_id=phone_id)
    return None


@router.get("/search/available", response_model=List[dict])
@handle_service_errors_sync
def search_available_numbers(
    country_code: str = Query("US"),
    area_code: Optional[str] = Query(None),
    capabilities: Optional[List[str]] = Query(None),
    limit: int = Query(20, le=100),
):
    """Search for available phone numbers via Twilio"""
    try:
        results = twilio_service.search_available_numbers(
            country_code=country_code,
            area_code=area_code,
            capabilities=capabilities,
            limit=limit,
        )
        return results
    except TelephonyError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.post("/purchase", status_code=status.HTTP_201_CREATED, response_model=PhoneNumberResponse)
@handle_service_errors_sync
def purchase_phone_number(
    request: PhoneNumberPurchaseRequest,
    db: Session = Depends(get_db),
):
    """Purchase a phone number from Twilio"""
    # Check if phone number already exists
    existing = db.query(PhoneNumber).filter(
        PhoneNumber.phone_number == request.phone_number
    ).first()
    
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Phone number {request.phone_number} already exists"
        )
    
    try:
        # Purchase from Twilio
        twilio_result = twilio_service.purchase_phone_number(request.phone_number)
        
        # Extract country code from phone number (first 1-3 digits after +)
        country_code = "US"  # Default, could be improved with better parsing
        
        # Create phone number record
        phone_number = PhoneNumber(
            id=str(uuid.uuid4()),
            phone_number=twilio_result["phone_number"],
            twilio_phone_sid=twilio_result["phone_sid"],
            friendly_name=twilio_result.get("friendly_name"),
            country_code=country_code,
            capabilities=twilio_result.get("capabilities", {}),
            status="active",
            webhook_url=None,  # Will be configured separately
            webhook_method="POST",
            is_active=True,
            meta_data={},
        )
        
        db.add(phone_number)
        db.commit()
        db.refresh(phone_number)
        
        # Auto-configure webhook if webhook URL is set in settings
        from src.utils.config import get_settings
        settings = get_settings()
        if settings.TWILIO_WEBHOOK_URL:
            webhook_url = f"{settings.TWILIO_WEBHOOK_URL}/webhooks/twilio/voice"
            try:
                twilio_service.update_phone_number_config(
                    twilio_result["phone_sid"],
                    webhook_url,
                    "POST",
                )
                phone_number.webhook_url = webhook_url
                db.commit()
                db.refresh(phone_number)
            except TelephonyError as e:
                logger.warning("auto_webhook_config_failed", error=str(e))
        
        logger.info("phone_number_purchased", phone_id=phone_number.id, phone_number=request.phone_number)
        return PhoneNumberResponse.model_validate(phone_number)
        
    except TelephonyError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.post("/{phone_id}/assign-agent/{agent_id}", response_model=dict)
@handle_service_errors_sync
def assign_phone_to_agent(
    phone_id: str,
    agent_id: str,
    assignment_data: PhoneNumberAssignmentRequest,
    db: Session = Depends(get_db),
):
    """Assign phone number to an agent"""
    # Verify phone number exists
    phone_number = db.query(PhoneNumber).filter(PhoneNumber.id == phone_id).first()
    if not phone_number:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Phone number with ID {phone_id} not found"
        )
    
    # Verify agent exists
    agent = db.query(HumanAgent).filter(HumanAgent.id == agent_id).first()
    if not agent:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Agent with ID {agent_id} not found"
        )
    
    # Check if assignment already exists
    existing = db.query(AgentPhoneNumber).filter(
        AgentPhoneNumber.agent_id == agent_id,
        AgentPhoneNumber.phone_number_id == phone_id,
    ).first()
    
    if existing:
        # Update primary status
        existing.is_primary = assignment_data.is_primary
        db.commit()
        db.refresh(existing)
        return {"message": "Assignment updated", "assignment": {"id": existing.id, "is_primary": existing.is_primary}}
    
    # If setting as primary, unset other primary assignments for this agent
    if assignment_data.is_primary:
        db.query(AgentPhoneNumber).filter(
            AgentPhoneNumber.agent_id == agent_id,
            AgentPhoneNumber.is_primary == True,
        ).update({"is_primary": False})
    
    # Create assignment
    assignment = AgentPhoneNumber(
        agent_id=agent_id,
        phone_number_id=phone_id,
        is_primary=assignment_data.is_primary,
    )
    
    db.add(assignment)
    db.commit()
    db.refresh(assignment)
    
    logger.info("phone_assigned_to_agent", phone_id=phone_id, agent_id=agent_id, is_primary=assignment_data.is_primary)
    return {"message": "Phone number assigned to agent", "assignment": {"id": assignment.id, "is_primary": assignment.is_primary}}


@router.delete("/{phone_id}/assign-agent/{agent_id}", status_code=status.HTTP_204_NO_CONTENT)
@handle_service_errors_sync
def unassign_phone_from_agent(
    phone_id: str,
    agent_id: str,
    db: Session = Depends(get_db),
):
    """Unassign phone number from an agent"""
    assignment = db.query(AgentPhoneNumber).filter(
        AgentPhoneNumber.agent_id == agent_id,
        AgentPhoneNumber.phone_number_id == phone_id,
    ).first()
    
    if not assignment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Assignment not found"
        )
    
    db.delete(assignment)
    db.commit()
    
    logger.info("phone_unassigned_from_agent", phone_id=phone_id, agent_id=agent_id)
    return None


@router.post("/{phone_id}/assign-business/{business_id}", response_model=dict)
@handle_service_errors_sync
def assign_phone_to_business(
    phone_id: str,
    business_id: str,
    assignment_data: PhoneNumberAssignmentRequest,
    db: Session = Depends(get_db),
):
    """Assign phone number to a business"""
    # Verify phone number exists
    phone_number = db.query(PhoneNumber).filter(PhoneNumber.id == phone_id).first()
    if not phone_number:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Phone number with ID {phone_id} not found"
        )
    
    # Verify business exists
    business = db.query(BusinessConfig).filter(BusinessConfig.id == business_id).first()
    if not business:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Business with ID {business_id} not found"
        )
    
    # Check if assignment already exists
    existing = db.query(BusinessPhoneNumber).filter(
        BusinessPhoneNumber.business_id == business_id,
        BusinessPhoneNumber.phone_number_id == phone_id,
    ).first()
    
    if existing:
        # Update primary status
        existing.is_primary = assignment_data.is_primary
        db.commit()
        db.refresh(existing)
        return {"message": "Assignment updated", "assignment": {"id": existing.id, "is_primary": existing.is_primary}}
    
    # If setting as primary, unset other primary assignments for this business
    if assignment_data.is_primary:
        db.query(BusinessPhoneNumber).filter(
            BusinessPhoneNumber.business_id == business_id,
            BusinessPhoneNumber.is_primary == True,
        ).update({"is_primary": False})
    
    # Create assignment
    assignment = BusinessPhoneNumber(
        business_id=business_id,
        phone_number_id=phone_id,
        is_primary=assignment_data.is_primary,
    )
    
    db.add(assignment)
    db.commit()
    db.refresh(assignment)
    
    logger.info("phone_assigned_to_business", phone_id=phone_id, business_id=business_id, is_primary=assignment_data.is_primary)
    return {"message": "Phone number assigned to business", "assignment": {"id": assignment.id, "is_primary": assignment.is_primary}}


@router.delete("/{phone_id}/assign-business/{business_id}", status_code=status.HTTP_204_NO_CONTENT)
@handle_service_errors_sync
def unassign_phone_from_business(
    phone_id: str,
    business_id: str,
    db: Session = Depends(get_db),
):
    """Unassign phone number from a business"""
    assignment = db.query(BusinessPhoneNumber).filter(
        BusinessPhoneNumber.business_id == business_id,
        BusinessPhoneNumber.phone_number_id == phone_id,
    ).first()
    
    if not assignment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Assignment not found"
        )
    
    db.delete(assignment)
    db.commit()
    
    logger.info("phone_unassigned_from_business", phone_id=phone_id, business_id=business_id)
    return None


@router.get("/{phone_id}/assignments", response_model=dict)
@handle_service_errors_sync
def get_phone_assignments(
    phone_id: str,
    db: Session = Depends(get_db),
):
    """Get all assignments for a phone number"""
    phone_number = db.query(PhoneNumber).filter(PhoneNumber.id == phone_id).first()
    
    if not phone_number:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Phone number with ID {phone_id} not found"
        )
    
    # Get agent assignments
    agent_assignments = db.query(AgentPhoneNumber).filter(
        AgentPhoneNumber.phone_number_id == phone_id
    ).all()
    
    # Get business assignments
    business_assignments = db.query(BusinessPhoneNumber).filter(
        BusinessPhoneNumber.phone_number_id == phone_id
    ).all()
    
    return {
        "phone_id": phone_id,
        "phone_number": phone_number.phone_number,
        "agents": [
            {
                "assignment_id": a.id,
                "agent_id": a.agent_id,
                "agent_name": db.query(HumanAgent).filter(HumanAgent.id == a.agent_id).first().name if db.query(HumanAgent).filter(HumanAgent.id == a.agent_id).first() else None,
                "is_primary": a.is_primary,
            }
            for a in agent_assignments
        ],
        "businesses": [
            {
                "assignment_id": b.id,
                "business_id": b.business_id,
                "business_name": db.query(BusinessConfig).filter(BusinessConfig.id == b.business_id).first().name if db.query(BusinessConfig).filter(BusinessConfig.id == b.business_id).first() else None,
                "is_primary": b.is_primary,
            }
            for b in business_assignments
        ],
    }

