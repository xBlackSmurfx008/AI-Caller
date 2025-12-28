"""Retry logic with exponential backoff for documentation scraping"""

import asyncio
from functools import wraps
from typing import Callable, TypeVar, Tuple, Any

import httpx

from src.utils.logging import get_logger

logger = get_logger(__name__)

T = TypeVar('T')


def retry_with_backoff(
    max_retries: int = 3,
    initial_delay: float = 1.0,
    max_delay: float = 8.0,
    exponential_base: float = 2.0,
    retryable_exceptions: Tuple[type, ...] = (httpx.HTTPError, httpx.TimeoutException, ConnectionError),
):
    """
    Decorator for retrying async functions with exponential backoff
    
    Args:
        max_retries: Maximum number of retry attempts
        initial_delay: Initial delay in seconds
        max_delay: Maximum delay in seconds
        exponential_base: Base for exponential backoff
        retryable_exceptions: Tuple of exceptions to retry on
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs) -> T:
            delay = initial_delay
            last_exception = None
            
            for attempt in range(max_retries + 1):
                try:
                    return await func(*args, **kwargs)
                except retryable_exceptions as e:
                    last_exception = e
                    
                    if attempt < max_retries:
                        logger.warning(
                            "retry_attempt",
                            function=func.__name__,
                            attempt=attempt + 1,
                            max_retries=max_retries,
                            delay=delay,
                            error=str(e),
                        )
                        await asyncio.sleep(delay)
                        delay = min(delay * exponential_base, max_delay)
                    else:
                        logger.error(
                            "retry_exhausted",
                            function=func.__name__,
                            attempts=max_retries + 1,
                            error=str(e),
                        )
                        raise
                except Exception as e:
                    # Don't retry on non-retryable exceptions
                    logger.error(
                        "non_retryable_error",
                        function=func.__name__,
                        error=str(e),
                        error_type=type(e).__name__,
                    )
                    raise
            
            # Should never reach here, but just in case
            if last_exception:
                raise last_exception
        
        return wrapper
    return decorator

