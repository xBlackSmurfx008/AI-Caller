"""Context transfer for human escalation"""

from typing import Dict, Any, Optional

from sqlalchemy.orm import Session

from src.database.database import get_db
from src.database.models import Call, Escalation
from src.ai.conversation_manager import ConversationManager
from src.utils.logging import get_logger

logger = get_logger(__name__)


class ContextTransfer:
    """Handles context transfer to human agents"""

    def __init__(self):
        """Initialize context transfer"""
        pass

    async def prepare_context(
        self,
        call_id: str,
        db: Optional[Session] = None,
    ) -> Dict[str, Any]:
        """
        Prepare context for transfer to human agent
        
        Args:
            call_id: Call identifier
            db: Database session
            
        Returns:
            Context dictionary
        """
        if db is None:
            db = next(get_db())

        try:
            # Get call
            call = db.query(Call).filter(Call.id == call_id).first()
            if not call:
                raise ValueError(f"Call not found: {call_id}")

            # Get conversation history
            conversation_manager = ConversationManager(call_id=call_id)
            history = conversation_manager.get_conversation_history(db=db)

            # Generate summary
            summary = self._generate_summary(history)

            # Prepare context
            context = {
                "call_id": call_id,
                "call_sid": call.twilio_call_sid,
                "direction": call.direction.value,
                "from_number": call.from_number,
                "to_number": call.to_number,
                "started_at": call.started_at.isoformat() if call.started_at else None,
                "conversation_summary": summary,
                "conversation_history": history,
                "customer_info": self._extract_customer_info(history),
                "key_points": self._extract_key_points(history),
            }

            logger.info("context_prepared", call_id=call_id)

            return context

        except Exception as e:
            logger.error("context_preparation_error", error=str(e), call_id=call_id)
            raise

    def _generate_summary(self, history: list) -> str:
        """
        Generate conversation summary
        
        Args:
            history: Conversation history
            
        Returns:
            Summary string
        """
        if not history:
            return "No conversation history available."

        # Simple summary: first and last few interactions
        summary_parts = []

        # Add opening
        if history:
            first = history[0]
            summary_parts.append(f"Customer: {first.get('text', '')[:100]}")

        # Add key points from middle
        if len(history) > 2:
            middle = history[len(history) // 2]
            summary_parts.append(f"Key point: {middle.get('text', '')[:100]}")

        # Add latest
        if len(history) > 1:
            last = history[-1]
            summary_parts.append(f"Latest: {last.get('text', '')[:100]}")

        return "\n".join(summary_parts)

    def _extract_customer_info(self, history: list) -> Dict[str, Any]:
        """
        Extract customer information from conversation
        
        Args:
            history: Conversation history
            
        Returns:
            Customer info dictionary
        """
        # Simplified extraction - would use NLP in production
        customer_info = {}

        # Look for name mentions, account numbers, etc.
        for interaction in history:
            text = interaction.get("text", "").lower()
            # Simple pattern matching (would be more sophisticated)
            if "my name is" in text or "i'm" in text:
                # Extract name (simplified)
                pass

        return customer_info

    def _extract_key_points(self, history: list) -> list:
        """
        Extract key points from conversation
        
        Args:
            history: Conversation history
            
        Returns:
            List of key points
        """
        key_points = []

        # Extract customer questions and concerns
        for interaction in history:
            if interaction.get("speaker") == "customer":
                text = interaction.get("text", "")
                if len(text) > 20:  # Filter out short responses
                    key_points.append(text[:200])  # Truncate

        return key_points[:5]  # Return top 5

    async def transfer_context(
        self,
        escalation_id: int,
        context: Dict[str, Any],
        db: Optional[Session] = None,
    ) -> None:
        """
        Transfer context to escalation record
        
        Args:
            escalation_id: Escalation identifier
            context: Context dictionary
            db: Database session
        """
        if db is None:
            db = next(get_db())

        try:
            escalation = db.query(Escalation).filter(Escalation.id == escalation_id).first()
            if not escalation:
                raise ValueError(f"Escalation not found: {escalation_id}")

            escalation.conversation_summary = context.get("conversation_summary")
            escalation.context_data = context

            db.commit()

            logger.info("context_transferred", escalation_id=escalation_id)

        except Exception as e:
            db.rollback()
            logger.error("context_transfer_error", error=str(e), escalation_id=escalation_id)
            raise

