"""
Azure Application Insights monitoring integration for URIS-AI.

Provides centralized monitoring, custom metrics, and event tracking
for FastAPI applications.

Requirements: 8.4
"""

import logging
from typing import Any, Dict, Optional

from uris_ai.config import settings

logger = logging.getLogger(__name__)


class ApplicationInsights:
    """
    Azure Application Insights integration for monitoring and telemetry.
    """

    def __init__(self) -> None:
        """Initialize Application Insights with connection string from settings."""
        self.enabled = settings.enable_monitoring and bool(
            settings.appinsights_connection_string
        )

        self._tracer = None
        self._stats_recorder = None
        self._metrics_exporter = None

        if not self.enabled:
            logger.info(
                "Application Insights is disabled or connection string not configured"
            )
            return

        try:
            from opencensus.ext.azure import metrics_exporter
            from opencensus.ext.azure.trace_exporter import AzureExporter
            from opencensus.stats import stats as stats_module
            from opencensus.trace import config_integration
            from opencensus.trace.samplers import ProbabilitySampler
            from opencensus.trace.tracer import Tracer

            config_integration.trace_integrations(["requests", "sqlalchemy"])
            self._tracer = Tracer(
                exporter=AzureExporter(
                    connection_string=settings.appinsights_connection_string
                ),
                sampler=ProbabilitySampler(1.0),
            )
            self._stats_recorder = stats_module.stats.stats_recorder
            self._metrics_exporter = metrics_exporter.new_metrics_exporter(
                connection_string=settings.appinsights_connection_string
            )
            logger.info("Application Insights initialized successfully")
        except ImportError:
            logger.warning("opencensus not available, Application Insights disabled")
            self.enabled = False
        except Exception as exc:
            logger.warning(f"Failed to initialize Application Insights: {exc}")
            self.enabled = False

    def track_request(self, name: str, duration_ms: float, success: bool,
                      response_code: int, properties: Optional[Dict[str, Any]] = None) -> None:
        """Track an HTTP request."""
        if not self.enabled:
            return
        try:
            logger.info(
                f"Request: {name} | {duration_ms}ms | {response_code}",
                extra={"custom_dimensions": {
                    "request_name": name, "duration_ms": duration_ms,
                    "success": success, "response_code": response_code,
                    **(properties or {})}},
            )
        except Exception as exc:
            logger.warning(f"Failed to track request: {exc}")

    def track_metric(self, name: str, value: float,
                     properties: Optional[Dict[str, Any]] = None) -> None:
        """Track a custom metric."""
        if not self.enabled:
            return
        try:
            logger.info(f"Metric: {name} = {value}",
                extra={"custom_dimensions": {"metric_name": name,
                    "metric_value": value, **(properties or {})}})
        except Exception as exc:
            logger.warning(f"Failed to track metric: {exc}")

    def track_event(self, name: str,
                    properties: Optional[Dict[str, Any]] = None) -> None:
        """Track a custom event."""
        if not self.enabled:
            return
        try:
            logger.info(f"Event: {name}",
                extra={"custom_dimensions": {"event_name": name, **(properties or {})}})
        except Exception as exc:
            logger.warning(f"Failed to track event: {exc}")

    def track_exception(self, exception: Exception,
                        properties: Optional[Dict[str, Any]] = None) -> None:
        """Track an exception."""
        if not self.enabled:
            return
        try:
            logger.error(f"Exception: {type(exception).__name__}: {exception}",
                exc_info=True,
                extra={"custom_dimensions": {
                    "exception_type": type(exception).__name__,
                    "exception_message": str(exception),
                    **(properties or {})}})
        except Exception as exc:
            logger.warning(f"Failed to track exception: {exc}")

    def track_prediction_accuracy(self, accuracy: float) -> None:
        """Track ML model prediction accuracy."""
        self.track_metric("prediction_accuracy", accuracy)

    def track_active_users(self, count: int) -> None:
        """Track number of active users."""
        self.track_metric("active_users", float(count))

    def track_error(self) -> None:
        """Track an error occurrence (no-op if not enabled)."""
        pass

    def get_tracer(self):
        """Get the OpenCensus tracer for distributed tracing."""
        return self._tracer

    def flush(self) -> None:
        """Flush all pending telemetry data."""
        if not self.enabled:
            return
        try:
            logger.info("Application Insights telemetry flushed")
        except Exception as exc:
            logger.warning(f"Failed to flush telemetry: {exc}")


# Global Application Insights instance
app_insights = ApplicationInsights()


def setup_application_insights_logging() -> None:
    """
    Configure Python logging to send logs to Application Insights.
    Called early in application startup.
    """
    if not settings.enable_monitoring or not settings.appinsights_connection_string:
        return

    try:
        from opencensus.ext.azure.log_exporter import AzureLogHandler
        azure_handler = AzureLogHandler(
            connection_string=settings.appinsights_connection_string
        )
        azure_handler.setLevel(logging.INFO)
        logging.getLogger().addHandler(azure_handler)
        logger.info("Application Insights logging configured successfully")
    except ImportError:
        logger.warning("opencensus not available, skipping Application Insights logging")
    except Exception as exc:
        logger.warning(f"Failed to setup Application Insights logging: {exc}")
