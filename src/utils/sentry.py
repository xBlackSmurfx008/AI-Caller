"""Sentry error tracking integration"""

import os
from typing import Optional

from src.utils.config import get_settings
from src.utils.logging import get_logger

logger = get_logger(__name__)
settings = get_settings()

_sentry_initialized = False


def init_sentry(dsn: Optional[str] = None):
    """Initialize Sentry error tracking"""
    global _sentry_initialized
    
    if _sentry_initialized:
        return
    
    try:
        import sentry_sdk
        from sentry_sdk.integrations.fastapi import FastApiIntegration
        from sentry_sdk.integrations.sqlalchemy import SqlalchemyIntegration
        from sentry_sdk.integrations.redis import RedisIntegration
        
        sentry_dsn = dsn or os.getenv("SENTRY_DSN") or getattr(settings, "SENTRY_DSN", None)
        
        if not sentry_dsn:
            logger.info("sentry_not_configured", reason="no_dsn")
            return
        
        sentry_sdk.init(
            dsn=sentry_dsn,
            integrations=[
                FastApiIntegration(),
                SqlalchemyIntegration(),
                RedisIntegration(),
            ],
            traces_sample_rate=0.1,  # 10% of transactions
            environment=settings.APP_ENV,
            release=os.getenv("APP_VERSION", "unknown"),
        )
        
        _sentry_initialized = True
        logger.info("sentry_initialized")
        
    except ImportError:
        logger.warning("sentry_not_installed", message="Install sentry-sdk to enable error tracking")
    except Exception as e:
        logger.error("sentry_init_error", error=str(e))


def capture_exception(exception: Exception, **context):
    """Capture an exception in Sentry"""
    if not _sentry_initialized:
        return
    
    try:
        import sentry_sdk
        with sentry_sdk.push_scope() as scope:
            for key, value in context.items():
                scope.set_context(key, value)
            sentry_sdk.capture_exception(exception)
    except Exception as e:
        logger.error("sentry_capture_error", error=str(e))

