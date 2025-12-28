"""Setup wizard routes"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import Optional, List, Dict, Any
from pydantic import BaseModel
import uuid

from src.database.database import get_db
from src.database.models import BusinessConfig, HumanAgent, KnowledgeEntry, User
from src.database.schemas import BusinessConfigCreate, HumanAgentCreate
from src.api.utils import handle_service_errors, handle_service_errors_sync
from src.api.middleware.auth import get_current_user
from src.utils.logging import get_logger
from src.services.knowledge_service import KnowledgeService

logger = get_logger(__name__)
router = APIRouter()


class SetupCompleteRequest(BaseModel):
    """Schema for setup completion"""
    business_config: Dict[str, Any]
    agents: List[Dict[str, Any]] = []
    knowledge_base: List[Dict[str, Any]] = []
    api_config: Optional[Dict[str, Any]] = None


class SetupCompleteResponse(BaseModel):
    """Schema for setup completion response"""
    success: bool
    business_config_id: Optional[str] = None
    agents_created: int = 0
    knowledge_entries_created: int = 0
    message: str


@router.post("/complete", response_model=SetupCompleteResponse)
@handle_service_errors
async def complete_setup(
    request: SetupCompleteRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Complete setup wizard and save all configuration"""
    try:
        business_config_id = None
        agents_created = 0
        knowledge_entries_created = 0
        
        # Create business config
        if request.business_config:
            config = BusinessConfig(
                id=str(uuid.uuid4()),
                name=request.business_config.get("name", "Default Business"),
                type=request.business_config.get("type", "customer_support"),
                config_data=request.business_config.get("config_data", {}),
                is_active=True,
                created_by_user_id=current_user.id,
            )
            db.add(config)
            db.flush()  # Flush to get the ID without committing
            business_config_id = config.id
            logger.info("setup_business_config_created", config_id=business_config_id, user_id=current_user.id)
        
        # Create agents
        if request.agents:
            for agent_data in request.agents:
                # Check if email already exists
                existing = db.query(HumanAgent).filter(HumanAgent.email == agent_data.get("email")).first()
                if existing:
                    logger.warning("setup_agent_email_exists", email=agent_data.get("email"))
                    continue
                
                agent = HumanAgent(
                    id=str(uuid.uuid4()),
                    name=agent_data.get("name", ""),
                    email=agent_data.get("email", ""),
                    phone_number=agent_data.get("phone_number"),
                    extension=agent_data.get("extension"),
                    skills=agent_data.get("skills", []),
                    departments=agent_data.get("departments", []),
                    is_available=agent_data.get("is_available", True),
                    is_active=agent_data.get("is_active", True),
                    meta_data=agent_data.get("metadata", {}),
                )
                db.add(agent)
                agents_created += 1
            logger.info("setup_agents_created", count=agents_created, user_id=current_user.id)
        
        # Create knowledge base entries
        if request.knowledge_base:
            try:
                knowledge_service = KnowledgeService()
                for kb_entry in request.knowledge_base:
                    try:
                        from src.api.schemas.knowledge import DocumentUpload
                        document = DocumentUpload(
                            title=kb_entry.get("title", "Untitled"),
                            content=kb_entry.get("content", ""),
                            source=kb_entry.get("source"),
                            source_type=kb_entry.get("source_type", "text"),
                            business_id=business_config_id,
                        )
                        await knowledge_service.upload_document(document, db)
                        knowledge_entries_created += 1
                    except Exception as e:
                        logger.warning("setup_kb_entry_failed", error=str(e), entry=kb_entry.get("title"))
                        continue
            except Exception as e:
                logger.warning("knowledge_service_init_failed", error=str(e))
                # Continue even if knowledge service fails
            logger.info("setup_kb_entries_created", count=knowledge_entries_created, user_id=current_user.id)
        
        # Commit all changes
        db.commit()
        
        logger.info("setup_completed", 
                   user_id=current_user.id,
                   business_config_id=business_config_id,
                   agents_created=agents_created,
                   knowledge_entries_created=knowledge_entries_created)
        
        return SetupCompleteResponse(
            success=True,
            business_config_id=business_config_id,
            agents_created=agents_created,
            knowledge_entries_created=knowledge_entries_created,
            message="Setup completed successfully"
        )
    
    except Exception as e:
        db.rollback()
        logger.error("setup_completion_failed", error=str(e), user_id=current_user.id)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to complete setup: {str(e)}"
        )

