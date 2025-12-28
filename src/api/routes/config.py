"""Configuration management routes"""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import Optional, List
from pydantic import BaseModel
import uuid

from src.database.database import get_db
from src.database.models import BusinessConfig, Call, CallStatus, User
from src.database.schemas import BusinessConfigCreate, BusinessConfigResponse
from src.api.middleware.auth import get_current_user
from src.api.utils import handle_service_errors_sync, handle_service_errors
from src.utils.logging import get_logger

logger = get_logger(__name__)
router = APIRouter()


class TestConnectionRequest(BaseModel):
    """Schema for testing API connections"""
    openai_api_key: str
    twilio_account_sid: str
    twilio_auth_token: str
    twilio_phone_number: Optional[str] = None


class TestConnectionResponse(BaseModel):
    """Schema for test connection response"""
    openai: dict
    twilio: dict
    success: bool


@router.get("/personalities")
@handle_service_errors_sync
def list_personalities():
    """List available agent personalities"""
    from src.ai.agent_personality import get_personality_loader
    
    loader = get_personality_loader()
    personality_names = loader.list_personalities()
    
    # Load each personality to get metadata
    personality_list = []
    for name in personality_names:
        try:
            personality = loader.get_personality(name)
            if personality:
                personality_list.append({
                    "name": name,
                    "display_name": name.replace("_", " ").title(),
                    "traits": personality.traits[:5],  # Top 5 traits
                    "skills": personality.skills[:5],  # Top 5 skills
                    "voice_config": personality.voice_config,
                })
        except Exception as e:
            logger.error("personality_load_error", name=name, error=str(e))
    
    return {"personalities": personality_list}


@router.get("/templates")
@handle_service_errors_sync
def list_templates(
):
    """List available business templates"""
    from src.templates.template_loader import TemplateLoader
    
    loader = TemplateLoader()
    template_names = loader.list_templates()
    
    # Load each template to get metadata
    template_list = []
    for template_name in template_names:
        try:
            template_data = loader.load_template(template_name)
            template_list.append({
                "id": template_name,
                "name": template_data.get("name", template_name),
                "type": template_data.get("type", "unknown"),
                "description": template_data.get("description", ""),
                "config_data": template_data.get("config_data", {}),
            })
        except Exception as e:
            logger.warning("template_load_failed", template=template_name, error=str(e))
            continue
    
    return {"templates": template_list}


@router.post("/templates")
@handle_service_errors_sync
def create_template(
    template_data: dict,
):
    """Create a new business template"""
    # Templates are typically stored as YAML files, not in database
    # For now, return a message indicating this should be done via file system
    # In production, you might want to store templates in database or S3
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Template creation via API not yet implemented. Please create template files manually."
    )


@router.get("/templates/{template_id}")
@handle_service_errors_sync
def get_template(
    template_id: str,
):
    """Get template details"""
    from src.templates.template_loader import TemplateLoader
    
    loader = TemplateLoader()
    template = loader.load_template(template_id)
    
    if not template:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Template {template_id} not found"
        )
    
    return {
        "id": template_id,
        "name": template.get("name", template_id),
        "type": template.get("type", "unknown"),
        "description": template.get("description", ""),
        "config_data": template.get("config_data", {}),
    }


# Business Config Routes
@router.get("/business")
@handle_service_errors_sync
def list_business_configs(
    is_active: Optional[bool] = Query(None),
    db: Session = Depends(get_db),
):
    """List business configurations for the current user"""
    query = db.query(BusinessConfig).filter(BusinessConfig.created_by_user_id == current_user.id)
    
    if is_active is not None:
        query = query.filter(BusinessConfig.is_active == is_active)
    
    configs = query.all()
    return {"configs": [BusinessConfigResponse.model_validate(config) for config in configs]}


@router.get("/business/{config_id}")
@handle_service_errors_sync
def get_business_config(
    config_id: str,
    db: Session = Depends(get_db),
):
    """Get a specific business configuration"""
    config = db.query(BusinessConfig).filter(
        BusinessConfig.id == config_id,
        BusinessConfig.created_by_user_id == current_user.id
    ).first()
    
    if not config:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Business config with ID {config_id} not found"
        )
    
    return {"config": BusinessConfigResponse.model_validate(config)}


@router.post("/business", status_code=status.HTTP_201_CREATED)
@handle_service_errors_sync
def create_business_config(
    config_data: BusinessConfigCreate,
    db: Session = Depends(get_db),
):
    """Create a new business configuration"""
    # Create new config
    config = BusinessConfig(
        id=str(uuid.uuid4()),
        name=config_data.name,
        type=config_data.type,
        config_data=config_data.config_data,
        is_active=True,
        created_by_user_id=current_user.id,
    )
    
    db.add(config)
    db.commit()
    db.refresh(config)
    
    logger.info("business_config_created", config_id=config.id, name=config.name, user_id=current_user.id)
    return {"config": BusinessConfigResponse.model_validate(config)}


@router.put("/business/{config_id}")
@handle_service_errors_sync
def update_business_config(
    config_id: str,
    config_data: BusinessConfigCreate,
    db: Session = Depends(get_db),
):
    """Update an existing business configuration"""
    config = db.query(BusinessConfig).filter(
        BusinessConfig.id == config_id,
        BusinessConfig.created_by_user_id == current_user.id
    ).first()
    
    if not config:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Business config with ID {config_id} not found"
        )
    
    # Update config fields
    config.name = config_data.name
    config.type = config_data.type
    config.config_data = config_data.config_data
    
    db.commit()
    db.refresh(config)
    
    logger.info("business_config_updated", config_id=config.id, user_id=current_user.id)
    return {"config": BusinessConfigResponse.model_validate(config)}


@router.delete("/business/{config_id}")
@handle_service_errors_sync
def delete_business_config(
    config_id: str,
    db: Session = Depends(get_db),
):
    """Delete a business configuration"""
    config = db.query(BusinessConfig).filter(
        BusinessConfig.id == config_id,
        BusinessConfig.created_by_user_id == current_user.id
    ).first()
    
    if not config:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Business config with ID {config_id} not found"
        )
    
    # Check if config is in use by active calls
    active_calls = db.query(Call).filter(
        Call.business_id == config_id,
        Call.status.in_([CallStatus.IN_PROGRESS, CallStatus.RINGING, CallStatus.INITIATED])
    ).count()
    
    if active_calls > 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot delete config with {active_calls} active call(s)"
        )
    
    db.delete(config)
    db.commit()
    
    logger.info("business_config_deleted", config_id=config_id, user_id=current_user.id)
    return {"message": "Business config deleted successfully"}


@router.get("/business/{config_id}/usage")
@handle_service_errors_sync
def get_business_config_usage(
    config_id: str,
    db: Session = Depends(get_db),
):
    """Check if a business configuration is in use"""
    config = db.query(BusinessConfig).filter(
        BusinessConfig.id == config_id,
        BusinessConfig.created_by_user_id == current_user.id
    ).first()
    
    if not config:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Business config with ID {config_id} not found"
        )
    
    # Count calls using this config
    total_calls = db.query(Call).filter(Call.business_id == config_id).count()
    active_calls = db.query(Call).filter(
        Call.business_id == config_id,
        Call.status.in_([CallStatus.IN_PROGRESS, CallStatus.RINGING, CallStatus.INITIATED])
    ).count()
    
    return {
        "config_id": config_id,
        "is_in_use": total_calls > 0,
        "total_calls": total_calls,
        "active_calls": active_calls,
    }


@router.post("/test-connection", response_model=TestConnectionResponse)
@handle_service_errors
async def test_connection(
    request: TestConnectionRequest,
    current_user: User = Depends(get_current_user),
):
    """Test API connections for OpenAI and Twilio"""
    openai_status = {"connected": False, "error": None}
    twilio_status = {"connected": False, "error": None}
    
    # Test OpenAI API
    try:
        from openai import OpenAI
        client = OpenAI(api_key=request.openai_api_key)
        # Make a simple API call to test the connection
        models = client.models.list()
        # Verify we got a response
        if models:
            openai_status = {"connected": True, "error": None}
        else:
            openai_status = {"connected": False, "error": "No models returned"}
    except Exception as e:
        logger.warning("openai_test_failed", error=str(e))
        openai_status = {"connected": False, "error": str(e)}
    
    # Test Twilio API
    try:
        from twilio.rest import Client as TwilioClient
        from twilio.base.exceptions import TwilioException
        client = TwilioClient(request.twilio_account_sid, request.twilio_auth_token)
        # Fetch account info to test the connection
        account = client.api.accounts(request.twilio_account_sid).fetch()
        if account:
            twilio_status = {"connected": True, "error": None, "account_name": account.friendly_name}
        else:
            twilio_status = {"connected": False, "error": "No account returned"}
    except Exception as e:
        logger.warning("twilio_test_failed", error=str(e))
        twilio_status = {"connected": False, "error": str(e)}
    
    success = openai_status["connected"] and twilio_status["connected"]
    
    logger.info("connection_test_completed", 
                openai_connected=openai_status["connected"],
                twilio_connected=twilio_status["connected"],
                user_id=current_user.id if current_user else None)
    
    return TestConnectionResponse(
        openai=openai_status,
        twilio=twilio_status,
        success=success
    )

