"""API utility functions"""

from fastapi import HTTPException, status
from functools import wraps
from typing import Any, Callable, Coroutine, Optional
import inspect

from src.utils.errors import (
    AICallerError,
    KnowledgeBaseError,
    NotFoundError,
    ValidationError,
    TelephonyError,
    EscalationError,
)
from src.utils.logging import get_logger

logger = get_logger(__name__)


def create_error_response(code: str, message: str, details: Optional[dict] = None) -> dict:
    """Create consistent error response format"""
    return {
        "error": {
            "code": code,
            "message": message,
            "details": details or {},
        }
    }


def _handle_error(exception: Exception) -> None:
    """Shared error handling logic with consistent logging"""
    error_type = type(exception).__name__
    
    if isinstance(exception, NotFoundError):
        logger.warning("not_found_error", error=str(exception), error_type=error_type)
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=create_error_response("NOT_FOUND", str(exception))
        )
    elif isinstance(exception, (ValidationError, ValueError)):
        logger.warning("validation_error", error=str(exception), error_type=error_type)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=create_error_response("VALIDATION_ERROR", str(exception))
        )
    elif isinstance(exception, TelephonyError):
        logger.error("telephony_error", error=str(exception), error_type=error_type)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=create_error_response("TELEPHONY_ERROR", str(exception))
        )
    elif isinstance(exception, EscalationError):
        logger.error("escalation_error", error=str(exception), error_type=error_type)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=create_error_response("ESCALATION_ERROR", str(exception))
        )
    elif isinstance(exception, KnowledgeBaseError):
        logger.error("knowledge_base_error", error=str(exception), error_type=error_type)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=create_error_response("KNOWLEDGE_BASE_ERROR", str(exception))
        )
    elif isinstance(exception, AICallerError):
        logger.error("ai_caller_error", error=str(exception), error_type=error_type)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=create_error_response("AI_CALLER_ERROR", str(exception))
        )
    else:
        logger.error("unexpected_error", error=str(exception), error_type=error_type)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=create_error_response("INTERNAL_ERROR", "An unexpected error occurred")
        )


def handle_service_errors(func: Callable) -> Callable:
    """Decorator to handle service errors and convert to HTTP exceptions.
    
    Automatically detects if the function is async or sync and handles accordingly.
    """
    if inspect.iscoroutinefunction(func):
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            try:
                return await func(*args, **kwargs)
            except Exception as e:
                _handle_error(e)
        return async_wrapper
    else:
        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                _handle_error(e)
        return sync_wrapper


def handle_service_errors_sync(func: Callable) -> Callable:
    """Decorator to handle service errors for synchronous functions.
    
    This is kept for backward compatibility. Consider using handle_service_errors
    which automatically handles both sync and async functions.
    """
    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            _handle_error(e)
    return wrapper

