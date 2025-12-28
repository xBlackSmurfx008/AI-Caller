"""Conversation state management"""

from datetime import datetime
from typing import Dict, List, Optional, Any
from collections import deque

from sqlalchemy.orm import Session

from src.database.database import get_db
from src.database.models import CallInteraction
from src.utils.logging import get_logger

logger = get_logger(__name__)


class ConversationManager:
    """Manages conversation state and context"""

    def __init__(self, call_id: str, max_context_length: int = 10000):
        """
        Initialize conversation manager
        
        Args:
            call_id: Call identifier
            max_context_length: Maximum context length in characters
        """
        self.call_id = call_id
        self.max_context_length = max_context_length
        self.conversation_history: deque = deque(maxlen=100)  # Keep last 100 interactions
        self.context_window: str = ""
        self.metadata: Dict[str, Any] = {}

    async def add_interaction(
        self,
        speaker: str,
        text: str,
        audio_url: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
        db: Optional[Session] = None,
    ) -> CallInteraction:
        """
        Add an interaction to the conversation
        
        Args:
            speaker: "ai" or "customer"
            text: Interaction text
            audio_url: Optional audio URL
            metadata: Optional metadata
            db: Database session
            
        Returns:
            CallInteraction model instance
        """
        if db is None:
            db = next(get_db())

        try:
            interaction = CallInteraction(
                call_id=self.call_id,
                speaker=speaker,
                text=text,
                audio_url=audio_url,
                timestamp=datetime.utcnow(),
                metadata=metadata or {},
            )

            db.add(interaction)
            db.commit()
            db.refresh(interaction)

            # Add to in-memory history
            self.conversation_history.append({
                "speaker": speaker,
                "text": text,
                "timestamp": interaction.timestamp,
            })

            # Update context window
            self._update_context_window()

            # Emit WebSocket event
            try:
                from src.api.routes.websocket import emit_interaction_added
                import asyncio
                
                interaction_data = {
                    "id": interaction.id,
                    "call_id": interaction.call_id,
                    "speaker": interaction.speaker,
                    "text": interaction.text,
                    "audio_url": interaction.audio_url,
                    "timestamp": interaction.timestamp.isoformat(),
                    "metadata": interaction.meta_data or {},
                }
                
                # Emit event (run in event loop if available)
                try:
                    loop = asyncio.get_event_loop()
                    if loop.is_running():
                        asyncio.create_task(emit_interaction_added(self.call_id, interaction_data))
                    else:
                        loop.run_until_complete(emit_interaction_added(self.call_id, interaction_data))
                except RuntimeError:
                    # No event loop, create new one
                    asyncio.run(emit_interaction_added(self.call_id, interaction_data))
            except Exception as e:
                logger.warning("websocket_emit_failed", error=str(e), call_id=self.call_id)

            logger.debug(
                "interaction_added",
                call_id=self.call_id,
                speaker=speaker,
                text_length=len(text),
            )

            return interaction
        except Exception as e:
            db.rollback()
            logger.error("interaction_add_failed", error=str(e), call_id=self.call_id)
            raise

    def get_conversation_history(
        self,
        limit: Optional[int] = None,
        db: Optional[Session] = None,
    ) -> List[Dict[str, Any]]:
        """
        Get conversation history
        
        Args:
            limit: Maximum number of interactions to return
            db: Database session
            
        Returns:
            List of interaction dictionaries
        """
        if db is None:
            db = next(get_db())

        try:
            query = db.query(CallInteraction).filter(
                CallInteraction.call_id == self.call_id
            ).order_by(CallInteraction.timestamp.asc())

            if limit:
                query = query.limit(limit)

            interactions = query.all()

            return [
                {
                    "id": i.id,
                    "speaker": i.speaker,
                    "text": i.text,
                    "timestamp": i.timestamp.isoformat(),
                    "metadata": i.metadata,
                }
                for i in interactions
            ]
        except Exception as e:
            logger.error("conversation_history_fetch_failed", error=str(e), call_id=self.call_id)
            return []

    def get_context_summary(self) -> str:
        """
        Get a summary of the conversation context
        
        Returns:
            Context summary string
        """
        if not self.conversation_history:
            return ""

        # Build context from recent interactions
        context_parts = []
        total_length = 0

        # Start from most recent and work backwards
        for interaction in reversed(self.conversation_history):
            text = f"{interaction['speaker'].upper()}: {interaction['text']}"
            if total_length + len(text) > self.max_context_length:
                break
            context_parts.insert(0, text)
            total_length += len(text)

        return "\n".join(context_parts)

    def _update_context_window(self) -> None:
        """Update the context window from conversation history"""
        self.context_window = self.get_context_summary()

    def get_metadata(self, key: str, default: Any = None) -> Any:
        """
        Get metadata value
        
        Args:
            key: Metadata key
            default: Default value
            
        Returns:
            Metadata value
        """
        return self.metadata.get(key, default)

    def set_metadata(self, key: str, value: Any) -> None:
        """
        Set metadata value
        
        Args:
            key: Metadata key
            value: Metadata value
        """
        self.metadata[key] = value

    def clear_metadata(self) -> None:
        """Clear all metadata"""
        self.metadata.clear()

