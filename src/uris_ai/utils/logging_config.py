"""
Structured logging configuration for URIS-AI.

Provides JSON-formatted logging with proper log levels, structured fields,
and integration with Azure Application Insights.

Requirements: 7.3
"""

import json
import logging
import sys
from datetime import datetime, timezone
from typing import Any, Dict, Optional

from uris_ai.config import settings


class StructuredFormatter(logging.Formatter):
    """
    Custom formatter that outputs logs in structured JSON format.
    
    Log structure follows the design specification:
    {
        "timestamp": "2024-01-15T10:30:00Z",
        "level": "ERROR",
        "component": "Flood_Risk_Engine",
        "message": "Failed to generate prediction",
        "context": {
            "region_id": 123,
            "error_type": "ModelPredictionError",
            "stack_trace": "..."
        },
        "request_id": "unique-request-id"
    }
    """

    def format(self, record: logging.LogRecord) -> str:
        """
        Format a log record as JSON.

        Args:
            record: The log record to format

        Returns:
            JSON-formatted log string
        """
        # Base log structure
        log_data: Dict[str, Any] = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "component": record.name,
            "message": record.getMessage(),
        }

        # Add context from extra fields
        context: Dict[str, Any] = {}
        
        # Extract custom dimensions if present (from Application Insights)
        if hasattr(record, "custom_dimensions"):
            context.update(record.custom_dimensions)
        
        # Extract other extra fields
        for key, value in record.__dict__.items():
            if key not in [
                "name",
                "msg",
                "args",
                "created",
                "filename",
                "funcName",
                "levelname",
                "levelno",
                "lineno",
                "module",
                "msecs",
                "message",
                "pathname",
                "process",
                "processName",
                "relativeCreated",
                "thread",
                "threadName",
                "exc_info",
                "exc_text",
                "stack_info",
                "custom_dimensions",
            ]:
                context[key] = value

        # Add exception info if present
        if record.exc_info:
            context["exception"] = {
                "type": record.exc_info[0].__name__ if record.exc_info[0] else None,
                "message": str(record.exc_info[1]) if record.exc_info[1] else None,
                "stack_trace": self.formatException(record.exc_info),
            }

        # Add context to log data if not empty
        if context:
            log_data["context"] = context

        # Add request_id if present
        if hasattr(record, "request_id"):
            log_data["request_id"] = record.request_id

        return json.dumps(log_data, default=str)


class ConsoleFormatter(logging.Formatter):
    """
    Human-readable formatter for console output during development.
    
    Provides colored output with clear structure for easier debugging.
    """

    # ANSI color codes
    COLORS = {
        "DEBUG": "\033[36m",  # Cyan
        "INFO": "\033[32m",  # Green
        "WARNING": "\033[33m",  # Yellow
        "ERROR": "\033[31m",  # Red
        "CRITICAL": "\033[35m",  # Magenta
        "RESET": "\033[0m",  # Reset
    }

    def format(self, record: logging.LogRecord) -> str:
        """
        Format a log record for console output.

        Args:
            record: The log record to format

        Returns:
            Formatted log string with colors
        """
        color = self.COLORS.get(record.levelname, self.COLORS["RESET"])
        reset = self.COLORS["RESET"]

        # Format timestamp
        timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")

        # Base message
        message = (
            f"{color}[{record.levelname}]{reset} "
            f"{timestamp} | "
            f"{record.name} | "
            f"{record.getMessage()}"
        )

        # Add exception info if present
        if record.exc_info:
            message += f"\n{self.formatException(record.exc_info)}"

        return message


def setup_logging() -> None:
    """
    Configure logging for the entire application.
    
    Sets up:
    - Root logger with appropriate level
    - Console handler with human-readable format (development)
    - File handler with JSON format (production)
    - Integration with Application Insights
    
    This should be called once at application startup.
    """
    # Get log level from settings
    log_level = getattr(logging, settings.log_level.upper(), logging.INFO)

    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)

    # Remove existing handlers
    root_logger.handlers.clear()

    # Console handler (always enabled)
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(log_level)

    # Use different formatters based on environment
    if settings.app_env == "development" or settings.debug:
        console_handler.setFormatter(ConsoleFormatter())
    else:
        console_handler.setFormatter(StructuredFormatter())

    root_logger.addHandler(console_handler)

    # File handler for production (JSON format)
    if settings.app_env == "production":
        try:
            file_handler = logging.FileHandler("logs/uris-ai.log")
            file_handler.setLevel(log_level)
            file_handler.setFormatter(StructuredFormatter())
            root_logger.addHandler(file_handler)
        except Exception as exc:
            root_logger.warning(f"Failed to setup file logging: {exc}")

    # Configure third-party loggers to reduce noise
    logging.getLogger("urllib3").setLevel(logging.WARNING)
    logging.getLogger("azure").setLevel(logging.WARNING)
    logging.getLogger("opencensus").setLevel(logging.WARNING)
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)

    root_logger.info(
        f"Logging configured: level={settings.log_level}, env={settings.app_env}"
    )


def get_logger(name: str) -> logging.Logger:
    """
    Get a logger instance for a specific component.

    Args:
        name: Logger name (typically module name)

    Returns:
        Configured logger instance
    """
    return logging.getLogger(name)


class LoggerAdapter(logging.LoggerAdapter):
    """
    Logger adapter that adds request context to all log messages.
    
    Usage:
        logger = LoggerAdapter(logging.getLogger(__name__), {"request_id": "123"})
        logger.info("Processing request")  # Will include request_id in context
    """

    def process(
        self, msg: str, kwargs: Dict[str, Any]
    ) -> tuple[str, Dict[str, Any]]:
        """
        Process log message to add extra context.

        Args:
            msg: Log message
            kwargs: Keyword arguments

        Returns:
            Tuple of (message, kwargs) with added context
        """
        # Add extra context from adapter
        extra = kwargs.get("extra", {})
        extra.update(self.extra)
        kwargs["extra"] = extra
        return msg, kwargs
