"""
Tests for monitoring and logging functionality.

Tests cover:
- Application Insights integration
- Structured logging
- Alerting rules
- Health check endpoints
"""

import json
import logging
from datetime import datetime, timedelta, timezone
from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from uris_ai.utils.alerting import AlertLevel, AlertManager
from uris_ai.utils.alerting_rules import AlertType, alerting_engine
from uris_ai.utils.logging_config import StructuredFormatter, setup_logging
from uris_ai.utils.monitoring import ApplicationInsights


class TestStructuredLogging:
    """Test structured logging functionality."""

    def test_structured_formatter_basic(self):
        """Test that StructuredFormatter produces valid JSON."""
        formatter = StructuredFormatter()
        record = logging.LogRecord(
            name="test_component",
            level=logging.INFO,
            pathname="test.py",
            lineno=10,
            msg="Test message",
            args=(),
            exc_info=None,
        )

        output = formatter.format(record)
        log_data = json.loads(output)

        assert log_data["level"] == "INFO"
        assert log_data["component"] == "test_component"
        assert log_data["message"] == "Test message"
        assert "timestamp" in log_data

    def test_structured_formatter_with_context(self):
        """Test that custom dimensions are included in context."""
        formatter = StructuredFormatter()
        record = logging.LogRecord(
            name="test_component",
            level=logging.ERROR,
            pathname="test.py",
            lineno=10,
            msg="Error occurred",
            args=(),
            exc_info=None,
        )
        record.custom_dimensions = {"region_id": 123, "error_type": "TestError"}

        output = formatter.format(record)
        log_data = json.loads(output)

        assert "context" in log_data
        assert log_data["context"]["region_id"] == 123
        assert log_data["context"]["error_type"] == "TestError"

    def test_structured_formatter_with_exception(self):
        """Test that exceptions are properly formatted."""
        formatter = StructuredFormatter()
        try:
            raise ValueError("Test exception")
        except ValueError:
            import sys

            exc_info = sys.exc_info()

        record = logging.LogRecord(
            name="test_component",
            level=logging.ERROR,
            pathname="test.py",
            lineno=10,
            msg="Exception occurred",
            args=(),
            exc_info=exc_info,
        )

        output = formatter.format(record)
        log_data = json.loads(output)

        assert "context" in log_data
        assert "exception" in log_data["context"]
        assert log_data["context"]["exception"]["type"] == "ValueError"
        assert "Test exception" in log_data["context"]["exception"]["message"]
        assert "stack_trace" in log_data["context"]["exception"]

    def test_setup_logging(self):
        """Test that setup_logging configures loggers correctly."""
        setup_logging()
        root_logger = logging.getLogger()

        assert root_logger.level <= logging.INFO
        assert len(root_logger.handlers) > 0


class TestApplicationInsights:
    """Test Application Insights integration."""

    @patch("uris_ai.utils.monitoring.settings")
    def test_app_insights_disabled_when_no_connection_string(self, mock_settings):
        """Test that Application Insights is disabled without connection string."""
        mock_settings.enable_monitoring = True
        mock_settings.appinsights_connection_string = None

        ai = ApplicationInsights()
        assert not ai.enabled

    @patch("uris_ai.utils.monitoring.settings")
    def test_app_insights_disabled_when_monitoring_disabled(self, mock_settings):
        """Test that Application Insights is disabled when monitoring is off."""
        mock_settings.enable_monitoring = False
        mock_settings.appinsights_connection_string = "test_connection_string"

        ai = ApplicationInsights()
        assert not ai.enabled

    @patch("uris_ai.utils.monitoring.settings")
    @patch("uris_ai.utils.monitoring.AzureExporter")
    @patch("uris_ai.utils.monitoring.metrics_exporter")
    def test_track_request(self, mock_metrics, mock_exporter, mock_settings):
        """Test request tracking."""
        mock_settings.enable_monitoring = True
        mock_settings.appinsights_connection_string = "test_connection_string"

        ai = ApplicationInsights()
        ai.track_request(
            name="GET /test",
            duration_ms=150.5,
            success=True,
            response_code=200,
            properties={"user_id": "123"},
        )

        # Should not raise any exceptions

    @patch("uris_ai.utils.monitoring.settings")
    @patch("uris_ai.utils.monitoring.AzureExporter")
    @patch("uris_ai.utils.monitoring.metrics_exporter")
    def test_track_metric(self, mock_metrics, mock_exporter, mock_settings):
        """Test metric tracking."""
        mock_settings.enable_monitoring = True
        mock_settings.appinsights_connection_string = "test_connection_string"

        ai = ApplicationInsights()
        ai.track_metric("test_metric", 42.5, properties={"component": "test"})

        # Should not raise any exceptions

    @patch("uris_ai.utils.monitoring.settings")
    @patch("uris_ai.utils.monitoring.AzureExporter")
    @patch("uris_ai.utils.monitoring.metrics_exporter")
    def test_track_event(self, mock_metrics, mock_exporter, mock_settings):
        """Test event tracking."""
        mock_settings.enable_monitoring = True
        mock_settings.appinsights_connection_string = "test_connection_string"

        ai = ApplicationInsights()
        ai.track_event("test_event", properties={"action": "test"})

        # Should not raise any exceptions

    @patch("uris_ai.utils.monitoring.settings")
    @patch("uris_ai.utils.monitoring.AzureExporter")
    @patch("uris_ai.utils.monitoring.metrics_exporter")
    def test_track_exception(self, mock_metrics, mock_exporter, mock_settings):
        """Test exception tracking."""
        mock_settings.enable_monitoring = True
        mock_settings.appinsights_connection_string = "test_connection_string"

        ai = ApplicationInsights()
        try:
            raise ValueError("Test exception")
        except ValueError as exc:
            ai.track_exception(exc, properties={"context": "test"})

        # Should not raise any exceptions


class TestAlertingRules:
    """Test alerting rules engine."""

    def test_alerting_rules_initialization(self):
        """Test that alerting rules are properly initialized."""
        assert AlertType.SYSTEM_DOWNTIME in alerting_engine.rules
        assert AlertType.DATABASE_CONNECTION_FAILURE in alerting_engine.rules
        assert AlertType.ML_MODEL_FAILURE in alerting_engine.rules
        assert AlertType.SECURITY_BREACH in alerting_engine.rules
        assert AlertType.HIGH_ERROR_RATE in alerting_engine.rules
        assert AlertType.SLOW_RESPONSE_TIME in alerting_engine.rules
        assert AlertType.HIGH_RESOURCE_UTILIZATION in alerting_engine.rules
        assert AlertType.DATA_STALENESS in alerting_engine.rules

    def test_check_database_connection_triggers_alert(self):
        """Test that database connection failures trigger alerts."""
        rule = alerting_engine.rules[AlertType.DATABASE_CONNECTION_FAILURE]
        initial_count = len(alerting_engine.get_alert_history())

        alerting_engine.check_database_connection(failure_count=5)

        history = alerting_engine.get_alert_history()
        assert len(history) > initial_count
        assert history[-1]["alert_type"] == AlertType.DATABASE_CONNECTION_FAILURE.value

    def test_check_database_connection_no_alert_below_threshold(self):
        """Test that database connection failures below threshold don't trigger alerts."""
        initial_count = len(alerting_engine.get_alert_history())

        alerting_engine.check_database_connection(failure_count=1)

        history = alerting_engine.get_alert_history()
        # Should not add new alert
        assert len(history) == initial_count

    def test_check_error_rate_triggers_alert(self):
        """Test that high error rate triggers alerts."""
        initial_count = len(alerting_engine.get_alert_history())

        # 10 errors out of 100 requests = 10% error rate (> 5% threshold)
        alerting_engine.check_error_rate(error_count=10, total_requests=100)

        history = alerting_engine.get_alert_history()
        assert len(history) > initial_count
        assert history[-1]["alert_type"] == AlertType.HIGH_ERROR_RATE.value

    def test_check_error_rate_no_alert_below_threshold(self):
        """Test that error rate below threshold doesn't trigger alerts."""
        initial_count = len(alerting_engine.get_alert_history())

        # 3 errors out of 100 requests = 3% error rate (< 5% threshold)
        alerting_engine.check_error_rate(error_count=3, total_requests=100)

        history = alerting_engine.get_alert_history()
        assert len(history) == initial_count

    def test_check_response_time_triggers_alert(self):
        """Test that slow response time triggers alerts."""
        initial_count = len(alerting_engine.get_alert_history())

        # 6000ms > 5000ms threshold
        alerting_engine.check_response_time(avg_response_time_ms=6000.0)

        history = alerting_engine.get_alert_history()
        assert len(history) > initial_count
        assert history[-1]["alert_type"] == AlertType.SLOW_RESPONSE_TIME.value

    def test_check_data_staleness_triggers_alert(self):
        """Test that stale data triggers alerts."""
        initial_count = len(alerting_engine.get_alert_history())

        # Data from 15 minutes ago (> 10 minute threshold)
        stale_time = datetime.now(timezone.utc) - timedelta(minutes=15)
        alerting_engine.check_data_staleness(last_update=stale_time)

        history = alerting_engine.get_alert_history()
        assert len(history) > initial_count
        assert history[-1]["alert_type"] == AlertType.DATA_STALENESS.value

    def test_check_security_breach_triggers_critical_alert(self):
        """Test that security breaches trigger critical alerts."""
        initial_count = len(alerting_engine.get_alert_history())

        alerting_engine.check_security_breach(
            breach_type="unauthorized_access",
            details={"ip": "192.168.1.1", "endpoint": "/admin"},
        )

        history = alerting_engine.get_alert_history()
        assert len(history) > initial_count
        assert history[-1]["alert_type"] == AlertType.SECURITY_BREACH.value
        assert history[-1]["level"] == AlertLevel.CRITICAL.value

    def test_duplicate_alert_suppression(self):
        """Test that duplicate alerts are suppressed within time window."""
        # Clear alert history first to get a clean state
        alerting_engine._alert_history.clear()
        
        initial_count = len(alerting_engine.get_alert_history())

        # Send same alert twice in quick succession
        alerting_engine.check_response_time(avg_response_time_ms=6000.0)
        alerting_engine.check_response_time(avg_response_time_ms=6000.0)

        history = alerting_engine.get_alert_history()
        # Should only add one alert due to duplicate suppression
        assert len(history) == initial_count + 1


class TestHealthCheckEndpoints:
    """Test health check endpoints."""

    @pytest.fixture
    def client(self):
        """Create a test client for the FastAPI app."""
        from uris_ai.api.main import app

        return TestClient(app)

    def test_health_endpoint(self, client):
        """Test basic health check endpoint."""
        response = client.get("/health")
        assert response.status_code == 200

        data = response.json()
        assert data["status"] == "healthy"
        assert "version" in data
        assert "timestamp" in data

    def test_health_live_endpoint(self, client):
        """Test liveness check endpoint."""
        response = client.get("/health/live")
        assert response.status_code == 200

        data = response.json()
        assert data["status"] == "alive"
        assert "timestamp" in data

    def test_health_ready_endpoint(self, client):
        """Test readiness check endpoint."""
        response = client.get("/health/ready")
        assert response.status_code == 200

        data = response.json()
        assert "status" in data
        assert "checks" in data
        assert "timestamp" in data

        # Should have database and cache checks
        assert "database" in data["checks"]
        assert "cache" in data["checks"]
        assert "monitoring" in data["checks"]

    def test_health_ready_status_values(self, client):
        """Test that readiness check returns appropriate status values."""
        response = client.get("/health/ready")
        data = response.json()

        # Status should be either "ready" or "not_ready"
        assert data["status"] in ["ready", "not_ready"]

        # Check values should be valid
        for check_name, check_status in data["checks"].items():
            assert check_status in ["ok", "error", "unavailable", "disabled"]


class TestAlertManager:
    """Test AlertManager functionality."""

    def test_alert_manager_send_alert(self):
        """Test sending alerts through AlertManager."""
        manager = AlertManager("test_component")

        alert = manager.send_alert(
            level=AlertLevel.WARNING,
            message="Test warning",
            details={"key": "value"},
        )

        assert alert.level == AlertLevel.WARNING
        assert alert.source == "test_component"
        assert alert.message == "Test warning"
        assert alert.details["key"] == "value"

    def test_alert_manager_alert_on_failure(self):
        """Test alert_on_failure wrapper."""
        manager = AlertManager("test_component")

        def failing_function():
            raise ValueError("Test error")

        with pytest.raises(ValueError):
            manager.alert_on_failure(failing_function, level=AlertLevel.ERROR)

        # Alert should have been sent (logged)

    def test_alert_manager_alert_on_success(self):
        """Test that alert_on_failure doesn't alert on success."""
        manager = AlertManager("test_component")

        def successful_function():
            return "success"

        result = manager.alert_on_failure(successful_function)
        assert result == "success"
