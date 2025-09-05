"""
Structured logging configuration using structlog.
"""

import logging
import sys
from typing import Any, Dict

import structlog
from structlog.stdlib import LoggerFactory

from app.core.config import settings


def setup_logging() -> structlog.stdlib.BoundLogger:
    """Setup structured logging with appropriate configuration."""
    
    # Configure standard library logging
    logging.basicConfig(
        format="%(message)s",
        stream=sys.stdout,
        level=logging.INFO if settings.ENVIRONMENT == "production" else logging.DEBUG,
    )
    
    # Configure structlog
    structlog.configure(
        processors=[
            structlog.stdlib.filter_by_level,
            structlog.stdlib.add_logger_name,
            structlog.stdlib.add_log_level,
            structlog.stdlib.PositionalArgumentsFormatter(),
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.processors.UnicodeDecoder(),
            structlog.processors.JSONRenderer() if settings.ENVIRONMENT == "production"
            else structlog.dev.ConsoleRenderer(colors=True),
        ],
        context_class=dict,
        logger_factory=LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )
    
    return structlog.get_logger()


def get_logger(name: str = None) -> structlog.stdlib.BoundLogger:
    """Get a logger instance with optional name."""
    if name:
        return structlog.get_logger(name)
    return structlog.get_logger()


class LoggingMixin:
    """Mixin class to add logging capabilities to any class."""
    
    @property
    def logger(self) -> structlog.stdlib.BoundLogger:
        """Get logger instance for this class."""
        return get_logger(self.__class__.__name__)
    
    def log_request(self, method: str, url: str, **kwargs: Any) -> None:
        """Log HTTP request details."""
        self.logger.info(
            "HTTP request",
            method=method,
            url=url,
            **kwargs
        )
    
    def log_response(self, status_code: int, duration: float, **kwargs: Any) -> None:
        """Log HTTP response details."""
        self.logger.info(
            "HTTP response",
            status_code=status_code,
            duration_ms=round(duration * 1000, 2),
            **kwargs
        )
    
    def log_error(self, error: Exception, context: Dict[str, Any] = None) -> None:
        """Log error with context."""
        self.logger.error(
            "Error occurred",
            error=str(error),
            error_type=type(error).__name__,
            **(context or {})
        )

