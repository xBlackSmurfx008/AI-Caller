"""Instrumentation helpers for cost tracking"""

from typing import Dict, Any, Optional
from sqlalchemy.orm import Session
from openai import OpenAI
from openai.types.chat import ChatCompletion

from src.cost.cost_event_logger import CostEventLogger
from src.utils.logging import get_logger

logger = get_logger(__name__)


class OpenAIInstrumentation:
    """Instrumentation wrapper for OpenAI API calls"""
    
    def __init__(self, db: Session):
        """Initialize with database session"""
        self.db = db
        self.cost_logger = CostEventLogger()
    
    def log_chat_completion(
        self,
        response: ChatCompletion,
        task_id: Optional[str] = None,
        project_id: Optional[str] = None,
        agent_id: Optional[str] = None,
        execution_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> None:
        """
        Log cost event for a chat completion
        
        Args:
            response: OpenAI ChatCompletion response
            task_id: Associated task ID
            project_id: Associated project ID
            agent_id: Agent identifier
            execution_id: AIExecution ID
            metadata: Additional metadata
        """
        try:
            usage = response.usage
            if not usage:
                return
            
            input_tokens = usage.prompt_tokens
            output_tokens = usage.completion_tokens
            total_tokens = usage.total_tokens
            
            # Get model from response
            model = response.model
            
            # Log input tokens
            self.cost_logger.log_cost_event(
                db=self.db,
                provider="openai",
                service="chat",
                metric_type="tokens",
                units=input_tokens,
                task_id=task_id,
                project_id=project_id,
                agent_id=agent_id,
                execution_id=execution_id,
                event_id=f"{response.id}:input",
                metadata={
                    "model": model,
                    "token_type": "input",
                    **(metadata or {})
                }
            )
            
            # Log output tokens
            self.cost_logger.log_cost_event(
                db=self.db,
                provider="openai",
                service="chat",
                metric_type="tokens",
                units=output_tokens,
                task_id=task_id,
                project_id=project_id,
                agent_id=agent_id,
                execution_id=execution_id,
                event_id=f"{response.id}:output",
                metadata={
                    "model": model,
                    "token_type": "output",
                    **(metadata or {})
                }
            )
            
        except Exception as e:
            logger.error("failed_to_log_openai_cost", error=str(e), response_id=getattr(response, 'id', None))


def instrument_openai_client(
    client: OpenAI,
    db: Session,
    task_id: Optional[str] = None,
    project_id: Optional[str] = None,
    agent_id: Optional[str] = None,
    execution_id: Optional[str] = None
) -> OpenAI:
    """
    Create an instrumented OpenAI client wrapper
    
    Note: This is a simplified approach. For production, you might want to use
    OpenAI's built-in usage tracking or middleware.
    
    Args:
        client: OpenAI client instance
        db: Database session
        task_id: Task ID for cost tracking
        project_id: Project ID
        agent_id: Agent ID
        execution_id: Execution ID
    
    Returns:
        Wrapped client (currently returns original - instrumentation happens via manual logging)
    """
    # For now, we'll instrument at the call site
    # This function is a placeholder for future middleware-based instrumentation
    return client

