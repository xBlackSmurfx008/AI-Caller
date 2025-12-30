"""Background tasks for messaging system (conversation summarization)"""

import asyncio
from typing import List
from sqlalchemy.orm import Session
from datetime import datetime, timedelta

from src.database.database import SessionLocal
from src.database.models import Message, Interaction, MemorySummary
from src.messaging.messaging_service import MessagingService
from src.utils.logging import get_logger

logger = get_logger(__name__)


class MessagingBackgroundTasks:
    """Background task processor for messaging operations"""
    
    def __init__(self):
        """Initialize background tasks"""
        self.messaging_service = MessagingService()
        self.processing = False
    
    async def process_conversation_summaries(self):
        """
        Process conversations that need summarization
        Runs periodically to check for conversations that should be summarized
        """
        db = SessionLocal()
        try:
            # Find conversations that need summarization
            # Get distinct conversation IDs with recent messages
            from sqlalchemy import func, distinct
            
            # Get conversations with messages from the last hour
            one_hour_ago = datetime.utcnow() - timedelta(hours=1)
            
            recent_conversations = db.query(
                distinct(Message.conversation_id)
            ).filter(
                Message.conversation_id.isnot(None),
                Message.timestamp >= one_hour_ago,
                Message.direction == "inbound"  # Only process inbound messages
            ).all()
            
            processed_count = 0
            
            for (conversation_id,) in recent_conversations:
                if not conversation_id:
                    continue
                
                try:
                    # Check if should summarize
                    if self.messaging_service.should_trigger_summary(
                        db=db,
                        conversation_id=conversation_id,
                        idle_minutes=5,
                        message_threshold=3  # Lower threshold for background processing
                    ):
                        # Process conversation
                        interaction = self.messaging_service.process_conversation_for_memory(
                            db=db,
                            conversation_id=conversation_id
                        )
                        
                        if interaction:
                            processed_count += 1
                            logger.info(
                                "conversation_summarized",
                                conversation_id=conversation_id,
                                interaction_id=interaction.id
                            )
                except Exception as e:
                    logger.error(
                        "conversation_summary_processing_error",
                        error=str(e),
                        conversation_id=conversation_id
                    )
                    db.rollback()
                    continue
            
            if processed_count > 0:
                logger.info("conversation_summaries_processed", count=processed_count)
            
        except Exception as e:
            logger.error("process_conversation_summaries_error", error=str(e))
            db.rollback()
        finally:
            db.close()
    
    async def run_periodic_tasks(self, interval_seconds: int = 300):
        """
        Run background tasks periodically
        
        Args:
            interval_seconds: How often to check for tasks (default: 5 minutes)
        """
        self.processing = True
        logger.info("messaging_background_tasks_started", interval=interval_seconds)
        
        while self.processing:
            try:
                await self.process_conversation_summaries()
            except Exception as e:
                logger.error("background_task_error", error=str(e))
            
            await asyncio.sleep(interval_seconds)
    
    def stop(self):
        """Stop background task processing"""
        self.processing = False
        logger.info("messaging_background_tasks_stopped")


# Global instance
_messaging_background_tasks = MessagingBackgroundTasks()

