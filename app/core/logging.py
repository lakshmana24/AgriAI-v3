"""
Structured logging configuration
"""
import logging
import sys
from typing import Any, Dict, Optional

import structlog
from structlog.types import EventDict, Processor

from app.core.config import get_settings

settings = get_settings()


def add_service_context(
    logger: logging.Logger, method_name: str, event_dict: EventDict
) -> EventDict:
    """Add service context to log events"""
    event_dict["service"] = {
        "name": settings.app_name,
        "version": settings.app_version,
    }
    return event_dict


def setup_logging() -> None:
    """Configure structured logging"""
    # Configure log processors
    shared_processors: list[Processor] = [
        structlog.contextvars.merge_contextvars,
        add_service_context,
        structlog.stdlib.add_log_level,
        structlog.stdlib.add_logger_name,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.UnicodeDecoder(),
    ]

    if settings.log_format == "json":
        formatter = structlog.processors.JSONRenderer()
    else:
        formatter = structlog.dev.ConsoleRenderer()

    # Configure structlog
    structlog.configure(
        processors=shared_processors + [formatter],
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.AsyncBoundLogger,
        cache_logger_on_first_use=True,
    )

    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(settings.log_level.upper())

    # Remove existing handlers
    for handler in root_logger.handlers:
        root_logger.removeHandler(handler)

    # Add console handler
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(
        logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        )
    )
    root_logger.addHandler(handler)

    # Configure uvicorn logging
    for log_name in ["uvicorn", "uvicorn.error"]:
        logging_logger = logging.getLogger(log_name)
        logging_logger.handlers.clear()
        logging_logger.propagate = True

    # Set log levels
    logging.getLogger("uvicorn").setLevel("WARNING")
    logging.getLogger("uvicorn.access").handlers.clear()
    logging.getLogger("uvicorn.access").propagate = True


def get_logger(name: Optional[str] = None) -> structlog.stdlib.BoundLogger:
    """Get a logger instance"""
    return structlog.get_logger(name or __name__)
