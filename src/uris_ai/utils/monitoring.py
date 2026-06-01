"""
Azure Application Insights monitoring integration for URIS-AI.

Provides centralized monitoring, custom metrics, and event tracking
for FastAPI applications.

Requirements: 8.4
"""

import logging
from typing import Any, Dict, Optional

from opencensus.ext.azure import metrics_exporter
from opencensus.ext.azure.log_exporter import AzureLogHandler
from opencensus.ext.azure.trace_exporter import AzureExporter
from opencensus.stats import aggregation as aggregation_module
from opencensus.stats import measure as measure_module
from opencensus.stats import stats as stats_module
from opencensus.stats import view as view_module
from opencensus.tags import tag_map as tag_map_module
from opencensus.trace import config_integration
from opencensus.trace.samplers import ProbabilitySampler
from opencensus.trace.tracer import Tracer

from uris_ai.config import settings

logger = logging.getLogger(__name__)


class ApplicationInsights:
    """
    Azure Application Insights integration for monitoring and telemetry.
    
    Provides:
    - Distributed tracing
    - Custom metrics
    - Custom events
    - Exception tracking
    - Performance monitoring
    """

    def __init__(self) -> None:
        """Initialize Application Insights with connection string from settings."""
        self.enabled = settings.enable_monitoring and bool(
            settings.appinsights_connection_string
        )
        
        if not self.enabled:
            logger.warning(
                "Application Insights is disabled or connection string not configured"
            )
            self._tracer: Optional[Tracer] = None
            self._stats_recorder: Optional[Any] = None
            self._metrics_exporter: Optional[Any] = None
            return

        # Initialize tracer for distributed tracing
        config_integration.trace_integrations(["requests", "sqlalchemy"])
        self._tracer = Tracer(
            exporter=AzureExporter(
                connection_string=settings.appinsights_connection_string
            ),
            sampler=ProbabilitySampler(1.0),  # Sample 100% of requests
        )

        # Initialize metrics
        self._stats_recorder = stats_module.stats.stats_recorder
        self._metrics_exporter = metrics_exporter.new_metrics_exporter(
            connection_string=settings.appinsights_connection_string
        )

        # Define custom measures
        self._request_duration_measure = measure_module.MeasureFloat(
            "request_duration", "Request duration in milliseconds", "ms"
        )
        self._prediction_accuracy_measure = measure_module.MeasureFloat(
            "prediction_accuracy", "ML model prediction accuracy", "%"
        )
        self._active_users_measure = measure_module.MeasureInt(
            "active_users", "Number of active users", "users"
        )
        self._error_count_measure = measure_module.MeasureInt(
            "error_count", "Number of errors", "errors"
        )

        # Create views for metrics
        self._create_views()

        logger.info("Application Insights initialized successfully")

    def _create_views(self) -> None:
        """Create metric views for aggregation."""
        if not self.enabled or not self._stats_recorder:
            return

        try:
            view_manager = stats_module.stats.view_manager

            # Request duration view
            request_duration_view = view_module.View(
                "request_duration_view",
                "Distribution of request durations",
                [],
                self._request_duration_measure,
                aggregation_module.DistributionAggregation(
                    [0, 100, 500, 1000, 2000, 5000, 10000]
                ),
            )
            view_manager.register_view(request_duration_view)

            # Prediction accuracy view
            prediction_accuracy_view = view_module.View(
                "prediction_accuracy_view",
                "ML model prediction accuracy",
                [],
                self._prediction_accuracy_measure,
                aggregation_module.LastValueAggregation(),
            )
            view_manager.register_view(prediction_accuracy_view)

            # Active users view
            active_users_view = view_module.View(
                "active_users_view",
                "Number of active users",
                [],
                self._active_users_measure,
                aggregation_module.LastValueAggregation(),
            )
            view_manager.register_view(active_users_view)

            # Error count view
            error_count_view = view_module.View(
                "error_count_view",
                "Total number of errors",
                [],
                self._error_count_measure,
                aggregation_module.CountAggregation(),
            )
            view_manager.register_view(error_count_view)
        except Exception as exc:
            logger.warning(f"Failed to create metric views: {exc}")

    def track_request(
        self,
        name: str,
        duration_ms: float,
        success: bool,
        response_code: int,
        properties: Optional[Dict[str, Any]] = None,
    ) -> None:
        """
        Track an HTTP request.

        Args:
            name: Request name (e.g., "GET /regions/{id}/risk")
            duration_ms: Request duration in milliseconds
            success: Whether the request was successful
            response_code: HTTP response code
            properties: Additional custom properties
        """
        if not self.enabled or not self._stats_recorder:
            return

        try:
            # Record request duration metric
            mmap = self._stats_recorder.new_measurement_map()
            tmap = tag_map_module.TagMap()
            mmap.measure_float_put(self._request_duration_measure, duration_ms)
            mmap.record(tmap)

            # Log request details
            logger.info(
                f"Request: {name} | Duration: {duration_ms}ms | "
                f"Success: {success} | Code: {response_code}",
                extra={
                    "custom_dimensions": {
                        "request_name": name,
                        "duration_ms": duration_ms,
                        "success": success,
                        "response_code": response_code,
                        **(properties or {}),
                    }
                },
            )
        except Exception as exc:
            logger.warning(f"Failed to track request: {exc}")

    def track_metric(
        self,
        name: str,
        value: float,
        properties: Optional[Dict[str, Any]] = None,
    ) -> None:
        """
        Track a custom metric.

        Args:
            name: Metric name
            value: Metric value
            properties: Additional custom properties
        """
        if not self.enabled:
            return

        try:
            logger.info(
                f"Metric: {name} = {value}",
                extra={
                    "custom_dimensions": {
                        "metric_name": name,
                        "metric_value": value,
                        **(properties or {}),
                    }
                },
            )
        except Exception as exc:
            logger.warning(f"Failed to track metric: {exc}")

    def track_event(
        self,
        name: str,
        properties: Optional[Dict[str, Any]] = None,
    ) -> None:
        """
        Track a custom event.

        Args:
            name: Event name
            properties: Event properties
        """
        if not self.enabled:
            return

        try:
            logger.info(
                f"Event: {name}",
                extra={
                    "custom_dimensions": {
                        "event_name": name,
                        **(properties or {}),
                    }
                },
            )
        except Exception as exc:
            logger.warning(f"Failed to track event: {exc}")

    def track_exception(
        self,
        exception: Exception,
        properties: Optional[Dict[str, Any]] = None,
    ) -> None:
        """
        Track an exception.

        Args:
            exception: The exception to track
            properties: Additional custom properties
        """
        if not self.enabled:
            return

        try:
            logger.error(
                f"Exception: {type(exception).__name__}: {exception}",
                exc_info=True,
                extra={
                    "custom_dimensions": {
                        "exception_type": type(exception).__name__,
                        "exception_message": str(exception),
                        **(properties or {}),
                    }
                },
            )
        except Exception as exc:
            logger.warning(f"Failed to track exception: {exc}")

    def track_prediction_accuracy(self, accuracy: float) -> None:
        """
        Track ML model prediction accuracy.

        Args:
            accuracy: Accuracy percentage (0-100)
        """
        if not self.enabled or not self._stats_recorder:
            return

        try:
            mmap = self._stats_recorder.new_measurement_map()
            tmap = tag_map_module.TagMap()
            mmap.measure_float_put(self._prediction_accuracy_measure, accuracy)
            mmap.record(tmap)

            self.track_metric("prediction_accuracy", accuracy)
        except Exception as exc:
            logger.warning(f"Failed to track prediction accuracy: {exc}")

    def track_active_users(self, count: int) -> None:
        """
        Track number of active users.

        Args:
            count: Number of active users
        """
        if not self.enabled or not self._stats_recorder:
            return

        try:
            mmap = self._stats_recorder.new_measurement_map()
            tmap = tag_map_module.TagMap()
            mmap.measure_int_put(self._active_users_measure, count)
            mmap.record(tmap)

            self.track_metric("active_users", float(count))
        except Exception as exc:
            logger.warning(f"Failed to track active users: {exc}")

    def track_error(self) -> None:
        """Track an error occurrence."""
        if not self.enabled or not self._stats_recorder:
            return

        try:
            mmap = self._stats_recorder.new_measurement_map()
            tmap = tag_map_module.TagMap()
            mmap.measure_int_put(self._error_count_measure, 1)
            mmap.record(tmap)
        except Exception as exc:
            logger.warning(f"Failed to track error: {exc}")

    def get_tracer(self) -> Optional[Tracer]:
        """
        Get the OpenCensus tracer for distributed tracing.

        Returns:
            Tracer instance or None if monitoring is disabled
        """
        return self._tracer

    def flush(self) -> None:
        """Flush all pending telemetry data."""
        if not self.enabled:
            return

        try:
            if self._metrics_exporter:
                self._metrics_exporter.export_metrics([])
            logger.info("Application Insights telemetry flushed")
        except Exception as exc:
            logger.warning(f"Failed to flush telemetry: {exc}")


# Global Application Insights instance
app_insights = ApplicationInsights()


def setup_application_insights_logging() -> None:
    """
    Configure Python logging to send logs to Application Insights.
    
    This should be called early in application startup.
    """
    if not settings.enable_monitoring or not settings.appinsights_connection_string:
        logger.warning("Application Insights logging not configured")
        return

    try:
        # Add Azure Log Handler to root logger
        azure_handler = AzureLogHandler(
            connection_string=settings.appinsights_connection_string
        )
        azure_handler.setLevel(logging.INFO)
        
        # Add handler to root logger
        root_logger = logging.getLogger()
        root_logger.addHandler(azure_handler)
        
        logger.info("Application Insights logging configured successfully")
    except Exception as exc:
        logger.error(f"Failed to setup Application Insights logging: {exc}")
