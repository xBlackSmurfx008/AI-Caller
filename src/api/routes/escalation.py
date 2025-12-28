"""Escalation management routes"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from src.database.database import get_db
from src.database.models import HumanAgent
from src.database.schemas import HumanAgentResponse
from src.utils.logging import get_logger

logger = get_logger(__name__)
router = APIRouter()


@router.get("/agents")
async def list_available_agents(
    db: Session = Depends(get_db),
):
    """List available human agents for escalation"""
    agents = db.query(HumanAgent).filter(
        HumanAgent.is_active == True,
        HumanAgent.is_available == True
    ).all()
    
    return {"agents": [HumanAgentResponse.model_validate(agent) for agent in agents]}

