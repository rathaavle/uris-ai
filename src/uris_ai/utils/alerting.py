"""
Structured alerting module for URIS-AI.

Provides a reusable AlertManager that creates structured Alert objects,
logs them with extra fields compatible with Azure Application Insights,
and optionally forwards CRITICAL alerts to a dedicated logger.

Requirements: 7.3
"""

import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Callable, Dict, Optional

# Dedicated logger for critical alerts — can be routed to a separate
# Azure Application Insights channel or log sink.
_alerts_logger = logging.getLogger("uris_ai.alerts")


class AlertLevel(Enum):
    """Severity levels for alerts."""

    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


@dataclass
class Alert:
    """
    Represents a single structured alert event.

    Attributes:
        level: Severity level of the alert.
        source: Component that generated the alert (e.g. "weather_fetcher").
        message: Human-readable description of the alert condition.
        details: Arbitrary key/value pairs with additional context.
        timestamp: UTC timestamp when the alert was created.
    """

    level: AlertLevel
    source: str
    message: str
    details: Dict[str, Any]
    timestamp: datetime


class AlertManager:
    """
    Manages structured alert creation and logging for a single component.

    Alerts are logged using Python's standard ``logging`` module with
    structured ``extra`` fields so that Azure Application Insights can
    index them as custom dimensions.

    CRITICAL alerts are additionally forwarded to the ``uris_ai.alerts``
    logger so they can be routed to a dedicated monitoring channel.

    Args:
        source: Name of the component that owns this manager
            (e.g. ``"weather_fetcher"``).
    """

    def __init__(self, source: str) -> None:
        self.source = source
        self._logger = logging.getLogger(f"uris_ai.{source}")

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def send_alert(
        self,
        level: AlertLevel,
        message: str,
        details: Optional[Dict[str, Any]] = None,
    ) -> Alert:
        """
        Create an Alert, log it, and return it.

        The alert is logged at the Python log level that corresponds to
        *level*:

        - ``WARNING``  → ``logging.WARNING``
        - ``ERROR``    → ``logging.ERROR``
        - ``CRITICAL`` → ``logging.CRITICAL`` (also forwarded to
          ``uris_ai.alerts``)

        Args:
            level: Severity of the alert.
            message: Human-readable description.
            details: Optional dict with additional context fields.

        Returns:
            The created :class:`Alert` instance.
        """
        alert = Alert(
            level=level,
            source=self.source,
            message=message,
            details=details or {},
            timestamp=datetime.now(timezone.utc),
        )

        self._log_alert(alert)
        return alert

    def alert_on_failure(
        self,
        func: Callable[..., Any],
        *args: Any,
        level: AlertLevel = AlertLevel.ERROR,
        message: Optional[str] = None,
        **kwargs: Any,
    ) -> Any:
        """
        Call *func* and send an alert if it raises an exception.

        The exception is always re-raised after the alert is sent so that
        callers can handle it as normal.

        Args:
            func: Callable to invoke.
            *args: Positional arguments forwarded to *func*.
            level: Alert level to use when the function fails.
            message: Custom alert message.  Defaults to a generic message
                that includes the function name and exception text.
            **kwargs: Keyword arguments forwarded to *func*.

        Returns:
            The return value of *func* on success.

        Raises:
            Exception: Re-raises whatever *func* raised.
        """
        try:
            return func(*args, **kwargs)
        except Exception as exc:
            alert_message = message or (
                f"{getattr(func, '__name__', repr(func))} failed: {exc}"
            )
            self.send_alert(
                level=level,
                message=alert_message,
                details={
                    "function": getattr(func, "__name__", repr(func)),
                    "error_type": type(exc).__name__,
                    "error_message": str(exc),
                },
            )
            raise

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _log_alert(self, alert: Alert) -> None:
        """Log *alert* at the appropriate level with structured extra fields."""
        extra = {
            "alert_level": alert.level.value,
            "alert_source": alert.source,
            "alert_timestamp": alert.timestamp.isoformat(),
            **alert.details,
        }

        log_level = self._alert_level_to_log_level(alert.level)
        self._logger.log(log_level, "[%s] %s", alert.level.value, alert.message, extra=extra)

        # CRITICAL alerts are also forwarded to the dedicated alerts logger
        if alert.level == AlertLevel.CRITICAL:
            _alerts_logger.critical(
                "[CRITICAL] %s | source=%s | %s",
                alert.message,
                alert.source,
                alert.details,
                extra=extra,
            )

    @staticmethod
    def _alert_level_to_log_level(level: AlertLevel) -> int:
        """Map an :class:`AlertLevel` to a Python logging level integer."""
        mapping = {
            AlertLevel.WARNING: logging.WARNING,
            AlertLevel.ERROR: logging.ERROR,
            AlertLevel.CRITICAL: logging.CRITICAL,
        }
        return mapping[level]
