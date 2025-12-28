"""API middleware"""

from fastapi import Request, Response, HTTPException, status
from starlette.middleware.base import BaseHTTPMiddleware
from typing import Dict, Tuple
from datetime import datetime, timedelta
import time

from src.utils.logging import get_logger

logger = get_logger(__name__)


class LoggingMiddleware(BaseHTTPMiddleware):
    """Request/response logging middleware"""

    async def dispatch(self, request: Request, call_next):
        """Log request and response"""
        start_time = time.time()
        logger.info(
            "request_received",
            method=request.method,
            path=request.url.path,
            client=request.client.host if request.client else None,
        )

        response = await call_next(request)
        
        duration = time.time() - start_time

        logger.info(
            "response_sent",
            method=request.method,
            path=request.url.path,
            status_code=response.status_code,
            duration_ms=round(duration * 1000, 2),
        )

        return response


class HTTPSRedirectMiddleware(BaseHTTPMiddleware):
    """Middleware to enforce HTTPS in production"""
    
    async def dispatch(self, request: Request, call_next):
        """Redirect HTTP to HTTPS in production"""
        from src.utils.config import get_settings
        settings = get_settings()
        
        # Only enforce HTTPS in production
        if settings.APP_ENV == "production":
            # Check if request is HTTP
            if request.url.scheme == "http":
                # Get the HTTPS URL
                https_url = str(request.url).replace("http://", "https://", 1)
                from fastapi.responses import RedirectResponse
                return RedirectResponse(url=https_url, status_code=301)
        
        return await call_next(request)


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Rate limiting middleware with Redis support for distributed systems"""
    
    def __init__(self, app, requests_per_minute: int = 100):
        super().__init__(app)
        self.requests_per_minute = requests_per_minute
        self.request_counts: Dict[str, list] = {}
        self._redis_client = None
        self._use_redis = False
        self._init_redis()
    
    def _init_redis(self):
        """Initialize Redis client if available"""
        try:
            import redis
            from src.utils.config import get_settings
            settings = get_settings()
            self._redis_client = redis.from_url(
                settings.REDIS_URL,
                socket_connect_timeout=1,
                decode_responses=True
            )
            self._redis_client.ping()
            self._use_redis = True
            logger.info("rate_limiting_using_redis")
        except Exception as e:
            logger.warning("redis_unavailable_falling_back_to_memory", error=str(e))
            self._use_redis = False
    
    def _get_client_id(self, request: Request) -> str:
        """Get client identifier for rate limiting"""
        # Try to get user ID from token if authenticated
        auth_header = request.headers.get("Authorization", "")
        if auth_header.startswith("Bearer "):
            try:
                from jose import jwt
                from src.utils.config import get_settings
                settings = get_settings()
                token = auth_header.split(" ")[1]
                payload = jwt.decode(token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])
                return f"user:{payload.get('sub', 'unknown')}"
            except Exception as e:
                logger.debug("jwt_decode_failed", error=str(e))
                # Fall through to IP-based identification
        
        # Fall back to IP address
        return request.client.host if request.client else "unknown"
    
    def _is_rate_limited_redis(self, client_id: str) -> bool:
        """Check rate limit using Redis"""
        if not self._redis_client:
            return False
        
        try:
            key = f"rate_limit:{client_id}"
            current = self._redis_client.incr(key)
            
            if current == 1:
                # Set expiration on first request
                self._redis_client.expire(key, 60)
            
            return current > self.requests_per_minute
        except Exception as e:
            logger.error("redis_rate_limit_error", error=str(e))
            # Fall back to in-memory
            return self._is_rate_limited_memory(client_id)
    
    def _is_rate_limited_memory(self, client_id: str) -> bool:
        """Check rate limit using in-memory storage"""
        now = datetime.utcnow()
        minute_ago = now - timedelta(minutes=1)
        
        # Clean old entries periodically (every 100 requests)
        if len(self.request_counts) > 1000:
            self._cleanup_old_entries(minute_ago)
        
        # Clean old entries for this client
        if client_id in self.request_counts:
            self.request_counts[client_id] = [
                ts for ts in self.request_counts[client_id]
                if ts > minute_ago
            ]
        else:
            self.request_counts[client_id] = []
        
        # Check limit
        if len(self.request_counts[client_id]) >= self.requests_per_minute:
            return True
        
        # Add current request
        self.request_counts[client_id].append(now)
        return False
    
    def _cleanup_old_entries(self, cutoff_time: datetime):
        """Clean up old entries from memory"""
        keys_to_remove = []
        for client_id, timestamps in self.request_counts.items():
            filtered = [ts for ts in timestamps if ts > cutoff_time]
            if not filtered:
                keys_to_remove.append(client_id)
            else:
                self.request_counts[client_id] = filtered
        
        for key in keys_to_remove:
            self.request_counts.pop(key, None)
    
    def _is_rate_limited(self, client_id: str) -> bool:
        """Check if client has exceeded rate limit"""
        if self._use_redis:
            return self._is_rate_limited_redis(client_id)
        else:
            return self._is_rate_limited_memory(client_id)
    
    def _get_remaining_requests(self, client_id: str) -> int:
        """Get remaining requests for client"""
        if self._use_redis:
            try:
                key = f"rate_limit:{client_id}"
                current = int(self._redis_client.get(key) or 0)
                return max(0, self.requests_per_minute - current)
            except Exception:
                return self.requests_per_minute
        else:
            now = datetime.utcnow()
            minute_ago = now - timedelta(minutes=1)
            if client_id in self.request_counts:
                count = len([ts for ts in self.request_counts[client_id] if ts > minute_ago])
                return max(0, self.requests_per_minute - count)
            return self.requests_per_minute
    
    async def dispatch(self, request: Request, call_next):
        """Apply rate limiting"""
        # Skip rate limiting for health checks
        if request.url.path in ["/health", "/"]:
            return await call_next(request)
        
        client_id = self._get_client_id(request)
        
        if self._is_rate_limited(client_id):
            logger.warning(
                "rate_limit_exceeded",
                client_id=client_id,
                path=request.url.path,
            )
            return Response(
                content='{"error": {"code": "RATE_LIMIT_EXCEEDED", "message": "Rate limit exceeded. Please try again later."}}',
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                media_type="application/json",
                headers={
                    "X-RateLimit-Limit": str(self.requests_per_minute),
                    "X-RateLimit-Remaining": "0",
                    "Retry-After": "60",
                }
            )
        
        response = await call_next(request)
        
        # Add rate limit headers
        remaining = self._get_remaining_requests(client_id)
        response.headers["X-RateLimit-Limit"] = str(self.requests_per_minute)
        response.headers["X-RateLimit-Remaining"] = str(remaining)
        
        return response

