"""Authentication and user context utilities"""

from typing import Optional
from fastapi import Depends, HTTPException, Header
from sqlalchemy.orm import Session

from src.database.database import get_db

# For now, we'll use a simple user context system
# In production, replace with proper authentication (JWT, OAuth, etc.)


def get_current_user_id(
    x_user_id: Optional[str] = Header(None, alias="X-User-ID")
) -> Optional[str]:
    """
    Get current user ID from header.
    
    In production, this should:
    1. Validate JWT token
    2. Extract user ID from token
    3. Verify user exists and is active
    
    For now, returns the header value or None (single-user mode)
    """
    # If no user ID provided, assume single-user mode
    # In multi-user mode, this would raise HTTPException
    return x_user_id


def require_user_id(
    user_id: Optional[str] = Depends(get_current_user_id)
) -> str:
    """
    Require a user ID. Raises 401 if not provided.
    
    Use this for endpoints that require authentication.
    """
    if not user_id:
        # In single-user mode, return a default user ID
        # In multi-user mode, raise HTTPException
        # raise HTTPException(status_code=401, detail="Authentication required")
        return "default_user"  # Single-user mode
    
    return user_id


def filter_by_user(
    query,
    user_id: Optional[str],
    model_class,
    db: Session
):
    """
    Filter query by user ID if multi-user mode is enabled.
    
    In single-user mode, returns query unchanged.
    In multi-user mode, adds user_id filter.
    """
    # For now, single-user mode - no filtering
    # In multi-user mode, add: query = query.filter(model_class.user_id == user_id)
    return query

