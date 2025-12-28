"""Agent routing for escalations"""

from datetime import datetime
from typing import Optional
from sqlalchemy.orm import Session

from src.database.database import get_db
from src.database.models import HumanAgent
from src.utils.logging import get_logger

logger = get_logger(__name__)


class AgentRouter:
    """Routes escalations to available human agents"""

    def __init__(self):
        """Initialize agent router"""
        pass

    async def find_available_agent(
        self,
        skills: Optional[list] = None,
        departments: Optional[list] = None,
        db: Optional[Session] = None,
    ) -> Optional[HumanAgent]:
        """
        Find an available human agent
        
        Args:
            skills: Optional required skills
            departments: Optional required departments
            db: Database session
            
        Returns:
            HumanAgent instance or None
        """
        if db is None:
            db = next(get_db())

        try:
            # Query for available agents
            query = db.query(HumanAgent).filter(
                HumanAgent.is_available == True,
                HumanAgent.is_active == True,
            )

            # Filter by skills if provided
            if skills:
                # This would need proper JSON querying in production
                # Simplified for now
                pass

            # Filter by departments if provided
            if departments:
                # This would need proper JSON querying in production
                # Simplified for now
                pass

            # Get first available agent (could implement round-robin, least busy, etc.)
            agent = query.first()

            if agent:
                logger.info("agent_found", agent_id=agent.id, agent_name=agent.name)
            else:
                logger.warning("no_available_agents")

            return agent

        except Exception as e:
            logger.error("agent_routing_error", error=str(e))
            return None

    async def mark_agent_busy(
        self,
        agent_id: str,
        db: Optional[Session] = None,
    ) -> None:
        """
        Mark agent as busy
        
        Args:
            agent_id: Agent identifier
            db: Database session
        """
        if db is None:
            db = next(get_db())

        try:
            agent = db.query(HumanAgent).filter(HumanAgent.id == agent_id).first()
            if agent:
                agent.is_available = False
                db.commit()
                logger.info("agent_marked_busy", agent_id=agent_id)

        except Exception as e:
            db.rollback()
            logger.error("agent_busy_mark_error", error=str(e), agent_id=agent_id)

    async def mark_agent_available(
        self,
        agent_id: str,
        db: Optional[Session] = None,
    ) -> None:
        """
        Mark agent as available
        
        Args:
            agent_id: Agent identifier
            db: Database session
        """
        if db is None:
            db = next(get_db())

        try:
            agent = db.query(HumanAgent).filter(HumanAgent.id == agent_id).first()
            if agent:
                agent.is_available = True
                agent.last_active_at = datetime.utcnow()
                db.commit()
                logger.info("agent_marked_available", agent_id=agent_id)

        except Exception as e:
            db.rollback()
            logger.error("agent_available_mark_error", error=str(e), agent_id=agent_id)

