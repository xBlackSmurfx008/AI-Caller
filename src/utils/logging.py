"""Structured logging configuration"""

import logging
import sys
from typing import Any

try:
    import structlog
    from structlog.types import Processor

    def setup_logging(log_level: str = "INFO") -> None:
        """Setup structured logging with JSON output"""
        logging.basicConfig(
            format="%(message)s",
            stream=sys.stdout,
            level=getattr(logging, log_level.upper()),
        )

        processors: list[Processor] = [
            structlog.contextvars.merge_contextvars,
            structlog.processors.add_log_level,
            structlog.processors.StackInfoRenderer(),
            structlog.dev.set_exc_info,
        ]

        import os
        if os.getenv("APP_ENV", "development") == "production":
            processors.append(structlog.processors.JSONRenderer())
        else:
            processors.append(structlog.dev.ConsoleRenderer())

        structlog.configure(
            processors=processors,
            wrapper_class=structlog.make_filtering_bound_logger(
                logging.getLevelName(log_level.upper())
            ),
            context_class=dict,
            logger_factory=structlog.PrintLoggerFactory(),
            cache_logger_on_first_use=True,
        )

    def get_logger(name: str) -> Any:
        """Get a structured logger instance"""
        return structlog.get_logger(name)
except ImportError:
    # Fallback to standard logging if structlog not available
    logging.basicConfig(level=logging.INFO)
    
    # Adapt logger to accept arbitrary kwargs (e.g., logger.info(..., project_id=""))
    # by tucking them under LogRecord.extra.context so standard logging won't error.
    class ContextAdapter(logging.LoggerAdapter):
        def process(self, msg, kwargs):
            extra = kwargs.pop("extra", {})
            # Keep standard logging kwargs intact
            passthrough_keys = {"exc_info", "stack_info", "stacklevel"}
            passthrough = {k: kwargs.pop(k) for k in list(kwargs.keys()) if k in passthrough_keys}

            merged: dict[str, Any] = {}
            if isinstance(extra, dict):
                merged.update(extra)
            elif extra:
                merged["_extra"] = extra

            if kwargs:
                merged.update(kwargs)

            if merged:
                passthrough["extra"] = {"context": merged}

            return msg, passthrough
    
    def setup_logging(log_level: str = "INFO") -> None:
        """Setup basic logging"""
        logging.basicConfig(level=getattr(logging, log_level.upper()))
    
    def get_logger(name: str) -> Any:
        """Get a standard logger instance"""
        return ContextAdapter(logging.getLogger(name), {})
