"""Authentication middleware and dependencies"""

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from jose import jwt, JWTError
from typing import Optional
from datetime import datetime, timedelta
from functools import lru_cache

from src.database.database import get_db
from src.database.models import User
from src.utils.config import get_settings
from src.utils.logging import get_logger

logger = get_logger(__name__)
settings = get_settings()
security = HTTPBearer()

# In-memory cache for user data (with TTL simulation)
_user_cache: dict = {}
_cache_ttl_seconds = 300  # 5 minutes


def _get_cached_user(user_id: str, db: Session) -> Optional[User]:
    """Get user from cache or database"""
    cache_key = f"user:{user_id}"
    cache_entry = _user_cache.get(cache_key)
    
    # Check if cache entry is valid
    if cache_entry:
        cached_time, user = cache_entry
        if datetime.utcnow() - cached_time < timedelta(seconds=_cache_ttl_seconds):
            return user
        else:
            # Cache expired, remove it
            _user_cache.pop(cache_key, None)
    
    # Fetch from database
    user = db.query(User).filter(User.id == user_id).first()
    if user:
        # Cache the user
        _user_cache[cache_key] = (datetime.utcnow(), user)
        # Limit cache size (remove oldest entries if over 1000)
        if len(_user_cache) > 1000:
            oldest_key = min(_user_cache.keys(), key=lambda k: _user_cache[k][0])
            _user_cache.pop(oldest_key, None)
    
    return user


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db),
) -> User:
    """
    Get current authenticated user from JWT token
    
    Raises:
        HTTPException: If token is invalid or user not found
    """
    token = credentials.credentials
    
    try:
        payload = jwt.decode(
            token,
            settings.JWT_SECRET_KEY,
            algorithms=[settings.JWT_ALGORITHM]
        )
        user_id: str = payload.get("sub")
        if user_id is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication credentials",
                headers={"WWW-Authenticate": "Bearer"},
            )
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Try cache first, then database
    user = _get_cached_user(user_id, db)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is inactive",
        )
    
    return user


def get_current_user_optional(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(HTTPBearer(auto_error=False)),
    db: Session = Depends(get_db),
) -> Optional[User]:
    """
    Get current user if authenticated, otherwise return None
    
    Used for endpoints that work with or without authentication
    """
    if credentials is None:
        return None
    
    try:
        return get_current_user(credentials, db)
    except HTTPException:
        return None

