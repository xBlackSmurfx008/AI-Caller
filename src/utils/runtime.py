"""Runtime/environment helpers (Vercel/serverless detection, feature gating)."""

from __future__ import annotations

import os


def is_vercel() -> bool:
    """True when running inside Vercel runtime."""
    # Vercel commonly sets at least one of these.
    return bool(os.getenv("VERCEL")) or bool(os.getenv("VERCEL_ENV")) or bool(os.getenv("VERCEL_REGION")) or bool(os.getenv("NOW_REGION"))


def is_serverless() -> bool:
    """
    Best-effort detection of serverless runtimes.
    We primarily care about Vercel here, but keep this generic.
    """
    return is_vercel() or bool(os.getenv("AWS_LAMBDA_FUNCTION_NAME"))


def allow_background_tasks() -> bool:
    """
    Background threads/infinite loops are unsafe on serverless.
    You can force-disable everywhere with DISABLE_BACKGROUND_TASKS=1.
    """
    disable = (os.getenv("DISABLE_BACKGROUND_TASKS") or "").strip().lower() in {"1", "true", "yes"}
    if disable:
        return False
    return not is_serverless()


