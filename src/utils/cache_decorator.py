"""API response caching decorator"""

import json
import hashlib
from functools import wraps
from typing import Callable, Optional, Any
import redis

from src.utils.config import get_settings
from src.utils.logging import get_logger

logger = get_logger(__name__)
settings = get_settings()

_redis_client = None


def get_redis_client():
    """Get Redis client (singleton)"""
    global _redis_client
    if _redis_client is None:
        try:
            _redis_client = redis.from_url(settings.REDIS_URL, decode_responses=True)
            _redis_client.ping()
        except Exception as e:
            logger.warning("redis_cache_unavailable", error=str(e))
            _redis_client = None
    return _redis_client


def cache_response(ttl: int = 300, key_prefix: str = "api_cache"):
    """
    Decorator to cache API response
    
    Args:
        ttl: Time to live in seconds (default 5 minutes)
        key_prefix: Prefix for cache key
    
    Usage:
        @cache_response(ttl=600)
        async def get_data():
            ...
    """
    def decorator(func: Callable):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Generate cache key from function name and arguments
            cache_key_parts = [func.__name__]
            for arg in args:
                if isinstance(arg, (str, int, float, bool)):
                    cache_key_parts.append(str(arg))
            for key, value in sorted(kwargs.items()):
                if isinstance(value, (str, int, float, bool)):
                    cache_key_parts.append(f"{key}:{value}")
            
            cache_key = f"{key_prefix}:{hashlib.md5(':'.join(cache_key_parts).encode()).hexdigest()}"
            
            # Try to get from cache
            redis_client = get_redis_client()
            if redis_client:
                try:
                    cached = redis_client.get(cache_key)
                    if cached:
                        logger.debug("cache_hit", key=cache_key)
                        return json.loads(cached)
                except Exception as e:
                    logger.warning("cache_get_error", error=str(e))
            
            # Execute function
            result = await func(*args, **kwargs)
            
            # Cache result
            if redis_client:
                try:
                    redis_client.setex(
                        cache_key,
                        ttl,
                        json.dumps(result, default=str)
                    )
                    logger.debug("cache_set", key=cache_key, ttl=ttl)
                except Exception as e:
                    logger.warning("cache_set_error", error=str(e))
            
            return result
        return wrapper
    return decorator


def invalidate_cache(pattern: str):
    """Invalidate cache entries matching pattern"""
    redis_client = get_redis_client()
    if not redis_client:
        return
    
    try:
        keys = redis_client.keys(pattern)
        if keys:
            redis_client.delete(*keys)
            logger.info("cache_invalidated", pattern=pattern, count=len(keys))
    except Exception as e:
        logger.warning("cache_invalidation_error", error=str(e))

