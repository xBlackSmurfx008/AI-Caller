"""Simple Godfather-only API authentication."""

from __future__ import annotations

import os
from typing import Optional

from fastapi import HTTPException, Request, status

from src.utils.config import get_settings


def _extract_token(request: Request) -> Optional[str]:
    # Prefer explicit header
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
    Enforce Godfather-only token auth when GODFATHER_API_TOKEN is set.
    If token is empty, auth is disabled (dev-friendly).
    """
    # By default, don't let a developer's local `.env` break the test suite.
    # To test auth behavior, set GODFATHER_API_TOKEN_ENFORCE_IN_TESTS=1 in the test env.
    if os.getenv("PYTEST_CURRENT_TEST") and not os.getenv("GODFATHER_API_TOKEN_ENFORCE_IN_TESTS"):
        return

    settings = get_settings()
    required = (settings.GODFATHER_API_TOKEN or "").strip()
    if not required:
        return

    provided = _extract_token(request)
    if not provided or provided != required:
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


