"""Escalation management system"""

from typing import Dict, Any, Optional, List
from datetime import datetime

from sqlalchemy.orm import Session

from src.database.database import get_db
from src.database.models import Call, Escalation, EscalationStatus
from src.escalation.agent_router import AgentRouter
from src.qa.sentiment_analyzer import SentimentAnalyzer
from src.utils.logging import get_logger

logger = get_logger(__name__)


class EscalationManager:
    """Manages call escalations to human agents"""

    def __init__(self):
        """Initialize escalation manager"""
        self.agent_router = AgentRouter()
        self.sentiment_analyzer = SentimentAnalyzer()

    async def check_escalation_triggers(
        self,
        call_id: str,
        interaction_text: str,
        escalation_config: Dict[str, Any],
        db: Optional[Session] = None,
    ) -> Optional[Dict[str, Any]]:
        """
        Check if escalation is triggered
        
        Args:
            call_id: Call identifier
            interaction_text: Latest interaction text
            escalation_config: Escalation configuration from template
            db: Database session
            
        Returns:
            Escalation trigger information or None
        """
        if not escalation_config.get("enabled", True):
            return None

        triggers = escalation_config.get("triggers", [])

        for trigger in triggers:
            trigger_type = trigger.get("type")

            if trigger_type == "sentiment":
                if self._check_sentiment_trigger(interaction_text, trigger):
                    return {
                        "type": "sentiment",
                        "details": trigger,
                        "reason": "Negative sentiment detected",
                    }

            elif trigger_type == "keyword":
                if self._check_keyword_trigger(interaction_text, trigger):
                    return {
                        "type": "keyword",
                        "details": trigger,
                        "reason": "Escalation keyword detected",
                    }

            elif trigger_type == "complexity":
                if self._check_complexity_trigger(interaction_text, trigger):
                    return {
                        "type": "complexity",
                        "details": trigger,
                        "reason": "High complexity detected",
                    }

        return None

    def _check_sentiment_trigger(
        self,
        text: str,
        trigger_config: Dict[str, Any],
    ) -> bool:
        """Check sentiment-based trigger"""
        threshold = trigger_config.get("threshold", -0.5)
        sentiment = self.sentiment_analyzer.analyze(text)
        return sentiment["score"] <= threshold

    def _check_keyword_trigger(
        self,
        text: str,
        trigger_config: Dict[str, Any],
    ) -> bool:
        """Check keyword-based trigger"""
        keywords = trigger_config.get("keywords", [])
        text_lower = text.lower()
        return any(keyword.lower() in text_lower for keyword in keywords)

    def _check_complexity_trigger(
        self,
        text: str,
        trigger_config: Dict[str, Any],
    ) -> bool:
        """Check complexity-based trigger (simplified)"""
        # Simple complexity metric: word count and sentence structure
        words = text.split()
        sentences = text.split(".")
        avg_words_per_sentence = len(words) / len(sentences) if sentences else 0

        # Threshold for complexity (would be more sophisticated in production)
        threshold = trigger_config.get("threshold", 0.8)
        complexity_score = min(1.0, (avg_words_per_sentence / 20.0))  # Normalize

        return complexity_score >= threshold

    async def escalate(
        self,
        call_id: str,
        trigger_info: Dict[str, Any],
        conversation_summary: Optional[str] = None,
        context_data: Optional[Dict[str, Any]] = None,
        db: Optional[Session] = None,
    ) -> Escalation:
        """
        Escalate a call to a human agent
        
        Args:
            call_id: Call identifier
            trigger_info: Trigger information
            conversation_summary: Optional conversation summary
            context_data: Optional context data
            db: Database session
            
        Returns:
            Escalation model instance
        """
        if db is None:
            db = next(get_db())

        try:
            # Find available agent
            agent = await self.agent_router.find_available_agent(db=db)

            if not agent:
                raise ValueError("No available agents")

            # Create escalation record
            escalation = Escalation(
                call_id=call_id,
                status=EscalationStatus.PENDING,
                trigger_type=trigger_info["type"],
                trigger_details=trigger_info.get("details", {}),
                assigned_agent_id=agent.id,
                agent_name=agent.name,
                conversation_summary=conversation_summary,
                context_data=context_data or {},
                requested_at=datetime.utcnow(),
            )

            db.add(escalation)
            db.commit()
            db.refresh(escalation)

            logger.info(
                "call_escalated",
                call_id=call_id,
                escalation_id=escalation.id,
                agent_id=agent.id,
            )

            return escalation

        except Exception as e:
            db.rollback()
            logger.error("escalation_failed", error=str(e), call_id=call_id)
            raise

