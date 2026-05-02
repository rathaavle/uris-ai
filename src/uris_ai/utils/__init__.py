"""Utility functions and classes for URIS-AI."""

from .alerting import Alert, AlertLevel, AlertManager
from .alerting_rules import AlertType, AlertRule, alerting_engine
from .logging_config import get_logger, setup_logging, LoggerAdapter
from .monitoring import app_insights, setup_application_insights_logging
from .retry import RetryConfig, RetryExhaustedError, retry_with_backoff

__all__ = [
    # Retry utilities
    "RetryConfig",
    "retry_with_backoff",
    "RetryExhaustedError",
    # Alerting utilities
    "AlertLevel",
    "Alert",
    "AlertManager",
    "AlertType",
    "AlertRule",
    "alerting_engine",
    # Logging utilities
    "setup_logging",
    "get_logger",
    "LoggerAdapter",
    # Monitoring utilities
    "app_insights",
    "setup_application_insights_logging",
]
