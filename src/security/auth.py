"""API authentication for AI Caller."""

from __future__ import annotations

import os
from typing import Optional

from fastapi import HTTPException, Request, status

from src.utils.config import get_settings

# Simple auth token for this deployment
VALID_AUTH_TOKEN = "ai-caller-auth-2025-secure"


def _extract_token(request: Request) -> Optional[str]:
    """Extract auth token from request headers."""
    # Check for simple auth token
    token = request.headers.get("X-Auth-Token")
    if token:
        return token.strip()
    
    # Check for legacy Godfather token
    token = request.headers.get("X-Godfather-Token")
    if token:
        return token.strip()

    # Support Bearer token
    auth = request.headers.get("Authorization", "")
    if auth.lower().startswith("bearer "):
        return auth.split(" ", 1)[1].strip()
    
    return None


def require_godfather(request: Request) -> None:
    """
    Enforce authentication.
    Accepts:
    - X-Auth-Token header with valid token
    - X-Godfather-Token header (legacy)
    - Authorization: Bearer token
    """
    # Skip auth in tests unless explicitly requested
    if os.getenv("PYTEST_CURRENT_TEST") and not os.getenv("GODFATHER_API_TOKEN_ENFORCE_IN_TESTS"):
        return

    settings = get_settings()
    godfather_token = (settings.GODFATHER_API_TOKEN or "").strip()
    
    # If no auth configured at all, allow (dev mode)
    if not godfather_token and not VALID_AUTH_TOKEN:
        return

    provided = _extract_token(request)
    
    if not provided:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Unauthorized",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Check against valid tokens
    if provided == VALID_AUTH_TOKEN:
        request.state.user_id = "authenticated_user"
        request.state.user_email = "ceo@digiwealth.io"
        return
    
    if godfather_token and provided == godfather_token:
        request.state.user_id = "godfather"
        request.state.user_email = None
        return
    
    # No valid token matched
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Unauthorized",
        headers={"WWW-Authenticate": "Bearer"},
    )


def is_auth_exempt(path: str) -> bool:
    """
    Exemptions:
    - /api/health* (health endpoints)
    - /api/cron* (Vercel cron tick endpoint; endpoint itself enforces origin/token)
    - /api/*/oauth/* (OAuth callbacks and starts)
    - /docs, /redoc, /openapi.json (docs)
    """
    if path.startswith("/api/health"):
        return True
    if path.startswith("/api/cron"):
        return True
    if path.startswith("/api") and "/oauth/" in path:
        return True
    if path in {"/docs", "/redoc", "/openapi.json"}:
        return True
    return False
