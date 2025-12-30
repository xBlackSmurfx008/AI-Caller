"""OpenAI client utilities with best practices, retry logic, and error handling."""

from typing import Optional, Dict, Any, List
from functools import wraps
import time
import random

from openai import OpenAI
from openai import RateLimitError, APIConnectionError, APIError, APITimeoutError
from src.utils.config import get_settings
from src.utils.logging import get_logger

logger = get_logger(__name__)
settings = get_settings()

# Models that are not chat-capable and will 404 on /v1/chat/completions
_NON_CHAT_SUBSTRINGS = (
    "instruct",
    "text-",
    "davinci",
    "curie",
    "babbage",
    "ada",
)
_CHAT_FALLBACK_MODEL = "gpt-4o-mini"


def ensure_chat_model(model: str) -> str:
    """
    Ensure the configured model works with chat/completions.
    Falls back to a known chat model if an instruct/text model is supplied.
    """
    chosen = (model or "").strip()
    lower = chosen.lower()
    if not chosen or any(sub in lower for sub in _NON_CHAT_SUBSTRINGS):
        fallback = _CHAT_FALLBACK_MODEL
        logger.warning(
            "openai_model_not_chat_fallback",
            configured_model=model,
            fallback_model=fallback,
        )
        return fallback
    return chosen


def create_openai_client(
    api_key: Optional[str] = None,
    timeout: float = 60.0,
    max_retries: int = 3,
) -> OpenAI:
    """
    Create an OpenAI client with best practices configuration.
    
    Args:
        api_key: OpenAI API key (defaults to settings)
        timeout: Request timeout in seconds (default: 60)
        max_retries: Maximum retry attempts (default: 3)
    
    Returns:
        Configured OpenAI client
    """
    client = OpenAI(
        api_key=api_key or settings.OPENAI_API_KEY,
        timeout=timeout,
        max_retries=max_retries,
    )
    return client


def retry_openai_call(
    max_retries: int = 3,
    initial_delay: float = 1.0,
    max_delay: float = 60.0,
    exponential_base: float = 2.0,
    jitter: bool = True,
):
    """
    Decorator to retry OpenAI API calls with exponential backoff.
    
    Handles OpenAI-specific exceptions:
    - RateLimitError: Rate limit exceeded (429)
    - APIConnectionError: Network/connection issues
    - APITimeoutError: Request timeout
    - APIError: Other API errors (with status code checking)
    
    Args:
        max_retries: Maximum number of retry attempts
        initial_delay: Initial delay in seconds
        max_delay: Maximum delay in seconds
        exponential_base: Base for exponential backoff
        jitter: Add random jitter to prevent thundering herd
    
    Usage:
        @retry_openai_call(max_retries=3)
        def call_openai():
            return client.chat.completions.create(...)
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            delay = initial_delay
            last_exception = None
            
            for attempt in range(max_retries + 1):
                try:
                    return func(*args, **kwargs)
                except RateLimitError as e:
                    last_exception = e
                    # Rate limit errors should respect retry-after header if available
                    retry_after = getattr(e, 'retry_after', None)
                    if retry_after:
                        delay = float(retry_after)
                        logger.warning(
                            "openai_rate_limit",
                            attempt=attempt + 1,
                            max_retries=max_retries,
                            retry_after=retry_after,
                            error=str(e)
                        )
                    else:
                        # Calculate exponential backoff
                        delay = min(initial_delay * (exponential_base ** attempt), max_delay)
                        if jitter:
                            delay = delay * (0.5 + random.random() * 0.5)
                        logger.warning(
                            "openai_rate_limit",
                            attempt=attempt + 1,
                            max_retries=max_retries,
                            delay=delay,
                            error=str(e)
                        )
                    
                    if attempt < max_retries:
                        time.sleep(delay)
                    else:
                        logger.error("openai_rate_limit_exhausted", attempts=attempt + 1, error=str(e))
                        raise
                        
                except (APIConnectionError, APITimeoutError) as e:
                    last_exception = e
                    if attempt < max_retries:
                        delay = min(initial_delay * (exponential_base ** attempt), max_delay)
                        if jitter:
                            delay = delay * (0.5 + random.random() * 0.5)
                        logger.warning(
                            "openai_connection_error",
                            attempt=attempt + 1,
                            max_retries=max_retries,
                            delay=delay,
                            error=str(e)
                        )
                        time.sleep(delay)
                    else:
                        logger.error("openai_connection_exhausted", attempts=attempt + 1, error=str(e))
                        raise
                        
                except APIError as e:
                    # Check status code - don't retry 4xx errors (except 429)
                    status_code = getattr(e, 'status_code', None)
                    if status_code and 400 <= status_code < 500 and status_code != 429:
                        logger.error("openai_client_error", status_code=status_code, error=str(e))
                        raise
                    
                    last_exception = e
                    if attempt < max_retries:
                        delay = min(initial_delay * (exponential_base ** attempt), max_delay)
                        if jitter:
                            delay = delay * (0.5 + random.random() * 0.5)
                        logger.warning(
                            "openai_api_error",
                            attempt=attempt + 1,
                            max_retries=max_retries,
                            delay=delay,
                            status_code=status_code,
                            error=str(e)
                        )
                        time.sleep(delay)
                    else:
                        logger.error("openai_api_error_exhausted", attempts=attempt + 1, error=str(e))
                        raise
                        
                except Exception as e:
                    # Don't retry unknown exceptions
                    logger.error("openai_unexpected_error", error=str(e), error_type=type(e).__name__)
                    raise
            
            # Should never reach here, but just in case
            if last_exception:
                raise last_exception
                
        return wrapper
    return decorator


def validate_tool_schema(tool: Dict[str, Any]) -> bool:
    """
    Validate that a tool schema follows OpenAI function calling requirements.
    
    Required structure:
    {
        "type": "function",
        "function": {
            "name": str,
            "description": str,
            "parameters": {
                "type": "object",
                "properties": {...},
                "required": [...]
            }
        }
    }
    
    Args:
        tool: Tool definition dictionary
    
    Returns:
        True if valid, False otherwise
    """
    if not isinstance(tool, dict):
        return False
    
    if tool.get("type") != "function":
        return False
    
    function = tool.get("function")
    if not isinstance(function, dict):
        return False
    
    if not function.get("name") or not isinstance(function.get("name"), str):
        return False
    
    if not function.get("description") or not isinstance(function.get("description"), str):
        return False
    
    parameters = function.get("parameters")
    if not isinstance(parameters, dict):
        return False
    
    if parameters.get("type") != "object":
        return False
    
    # Properties should be a dict
    properties = parameters.get("properties")
    if properties is not None and not isinstance(properties, dict):
        return False
    
    # Required should be a list
    required = parameters.get("required")
    if required is not None and not isinstance(required, list):
        return False
    
    return True


def validate_tools(tools: List[Dict[str, Any]]) -> tuple[bool, Optional[str]]:
    """
    Validate a list of tool schemas.
    
    Args:
        tools: List of tool definitions
    
    Returns:
        Tuple of (is_valid, error_message)
    """
    if not isinstance(tools, list):
        return False, "Tools must be a list"
    
    for i, tool in enumerate(tools):
        if not validate_tool_schema(tool):
            return False, f"Invalid tool schema at index {i}: {tool}"
    
    # Check for duplicate tool names
    names = [tool.get("function", {}).get("name") for tool in tools]
    duplicates = [name for name in names if names.count(name) > 1]
    if duplicates:
        return False, f"Duplicate tool names found: {duplicates}"
    
    return True, None


def get_openai_error_message(error: Exception) -> str:
    """
    Extract a user-friendly error message from OpenAI exceptions.
    
    Args:
        error: OpenAI exception
    
    Returns:
        User-friendly error message
    """
    if isinstance(error, RateLimitError):
        return "Rate limit exceeded. Please try again in a moment."
    elif isinstance(error, APIConnectionError):
        return "Connection error. Please check your internet connection and try again."
    elif isinstance(error, APITimeoutError):
        return "Request timed out. Please try again."
    elif isinstance(error, APIError):
        status_code = getattr(error, 'status_code', None)
        message = getattr(error, 'message', str(error))
        if status_code == 401:
            return "Authentication failed. Please check your API key."
        elif status_code == 403:
            return "Access forbidden. Please check your API permissions."
        elif status_code == 429:
            return "Rate limit exceeded. Please try again later."
        elif status_code == 500:
            return "OpenAI server error. Please try again later."
        else:
            return f"API error: {message}"
    else:
        return f"Unexpected error: {str(error)}"

