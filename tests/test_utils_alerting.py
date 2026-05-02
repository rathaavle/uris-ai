"""
Unit tests for the alerting utility module.

Tests cover:
- send_alert creates Alert with correct fields
- WARNING/ERROR/CRITICAL alerts are logged at appropriate levels
- CRITICAL alerts are also sent to uris_ai.alerts logger
- alert_on_failure sends alert and re-raises exception

Requirements: 7.3
"""

import logging
from datetime import datetime, timezone
from unittest.mock import MagicMock, call, patch

import pytest

from uris_ai.utils.alerting import Alert, AlertLevel, AlertManager


# ---------------------------------------------------------------------------
# Helpers / fixtures
# ---------------------------------------------------------------------------


@pytest.fixture()
def manager() -> AlertManager:
    """Return an AlertManager for the 'test_component' source."""
    return AlertManager(source="test_component")


# ---------------------------------------------------------------------------
# Test: send_alert creates Alert with correct fields
# ---------------------------------------------------------------------------


class TestSendAlertCreatesAlert:
    def test_returns_alert_instance(self, manager):
        """send_alert returns an Alert object."""
        with patch.object(manager, "_log_alert"):
            alert = manager.send_alert(AlertLevel.WARNING, "test message")

        assert isinstance(alert, Alert)

    def test_alert_level_matches(self, manager):
        """The returned Alert has the level that was passed in."""
        with patch.object(manager, "_log_alert"):
            for level in AlertLevel:
                alert = manager.send_alert(level, "msg")
                assert alert.level == level

    def test_alert_source_matches_manager_source(self, manager):
        """The returned Alert.source equals the manager's source."""
        with patch.object(manager, "_log_alert"):
            alert = manager.send_alert(AlertLevel.ERROR, "msg")

        assert alert.source == "test_component"

    def test_alert_message_matches(self, manager):
        """The returned Alert.message equals the message passed in."""
        with patch.object(manager, "_log_alert"):
            alert = manager.send_alert(AlertLevel.ERROR, "something went wrong")

        assert alert.message == "something went wrong"

    def test_alert_details_defaults_to_empty_dict(self, manager):
        """When details is not provided, Alert.details is an empty dict."""
        with patch.object(manager, "_log_alert"):
            alert = manager.send_alert(AlertLevel.WARNING, "msg")

        assert alert.details == {}

    def test_alert_details_are_stored(self, manager):
        """Provided details dict is stored on the Alert."""
        details = {"region_id": 5, "error": "timeout"}
        with patch.object(manager, "_log_alert"):
            alert = manager.send_alert(AlertLevel.ERROR, "msg", details=details)

        assert alert.details == details

    def test_alert_timestamp_is_recent_utc(self, manager):
        """Alert.timestamp is a recent UTC datetime."""
        before = datetime.now(timezone.utc)
        with patch.object(manager, "_log_alert"):
            alert = manager.send_alert(AlertLevel.WARNING, "msg")
        after = datetime.now(timezone.utc)

        assert before <= alert.timestamp <= after


# ---------------------------------------------------------------------------
# Test: alerts are logged at appropriate levels
# ---------------------------------------------------------------------------


class TestAlertLoggingLevels:
    def test_warning_alert_logs_at_warning_level(self, manager):
        """WARNING alert is logged at logging.WARNING."""
        with patch.object(manager._logger, "log") as mock_log:
            manager.send_alert(AlertLevel.WARNING, "watch out")

        mock_log.assert_called_once()
        assert mock_log.call_args[0][0] == logging.WARNING

    def test_error_alert_logs_at_error_level(self, manager):
        """ERROR alert is logged at logging.ERROR."""
        with patch.object(manager._logger, "log") as mock_log:
            manager.send_alert(AlertLevel.ERROR, "something failed")

        mock_log.assert_called_once()
        assert mock_log.call_args[0][0] == logging.ERROR

    def test_critical_alert_logs_at_critical_level(self, manager):
        """CRITICAL alert is logged at logging.CRITICAL on the component logger."""
        with patch.object(manager._logger, "log") as mock_log, \
             patch("uris_ai.utils.alerting._alerts_logger") as mock_alerts_logger:
            manager.send_alert(AlertLevel.CRITICAL, "system down")

        mock_log.assert_called_once()
        assert mock_log.call_args[0][0] == logging.CRITICAL

    def test_log_message_contains_alert_level_and_message(self, manager):
        """The log message includes the alert level and the alert message text."""
        with patch.object(manager._logger, "log") as mock_log:
            manager.send_alert(AlertLevel.ERROR, "disk full")

        log_args = mock_log.call_args[0]
        # log(level, format_string, level_value, message)
        # log_args[0] = logging.ERROR (int)
        # log_args[1] = "[%s] %s" (format string)
        # log_args[2] = "ERROR" (level.value)
        # log_args[3] = "disk full" (message)
        assert "ERROR" in log_args[2]
        assert "disk full" in log_args[3]

    def test_log_includes_structured_extra_fields(self, manager):
        """The log call includes extra fields for structured logging."""
        with patch.object(manager._logger, "log") as mock_log:
            manager.send_alert(AlertLevel.WARNING, "msg", details={"key": "val"})

        kwargs = mock_log.call_args[1]
        assert "extra" in kwargs
        extra = kwargs["extra"]
        assert extra["alert_level"] == "WARNING"
        assert extra["alert_source"] == "test_component"
        assert "alert_timestamp" in extra


# ---------------------------------------------------------------------------
# Test: CRITICAL alerts are also sent to uris_ai.alerts logger
# ---------------------------------------------------------------------------


class TestCriticalAlertForwarding:
    def test_critical_alert_forwarded_to_alerts_logger(self, manager):
        """CRITICAL alerts are also logged to the uris_ai.alerts logger."""
        with patch("uris_ai.utils.alerting._alerts_logger") as mock_alerts_logger:
            manager.send_alert(AlertLevel.CRITICAL, "critical failure")

        mock_alerts_logger.critical.assert_called_once()

    def test_warning_alert_not_forwarded_to_alerts_logger(self, manager):
        """WARNING alerts are NOT forwarded to the uris_ai.alerts logger."""
        with patch("uris_ai.utils.alerting._alerts_logger") as mock_alerts_logger:
            manager.send_alert(AlertLevel.WARNING, "minor issue")

        mock_alerts_logger.critical.assert_not_called()

    def test_error_alert_not_forwarded_to_alerts_logger(self, manager):
        """ERROR alerts are NOT forwarded to the uris_ai.alerts logger."""
        with patch("uris_ai.utils.alerting._alerts_logger") as mock_alerts_logger:
            manager.send_alert(AlertLevel.ERROR, "error occurred")

        mock_alerts_logger.critical.assert_not_called()

    def test_critical_alert_message_in_alerts_logger_call(self, manager):
        """The critical alert message appears in the uris_ai.alerts log call."""
        with patch("uris_ai.utils.alerting._alerts_logger") as mock_alerts_logger:
            manager.send_alert(AlertLevel.CRITICAL, "database unreachable")

        log_call_args = mock_alerts_logger.critical.call_args[0]
        # The formatted string should contain the message
        full_msg = " ".join(str(a) for a in log_call_args)
        assert "database unreachable" in full_msg


# ---------------------------------------------------------------------------
# Test: alert_on_failure sends alert and re-raises exception
# ---------------------------------------------------------------------------


class TestAlertOnFailure:
    def test_returns_value_when_function_succeeds(self, manager):
        """alert_on_failure returns the function's return value on success."""
        result = manager.alert_on_failure(lambda: 99)
        assert result == 99

    def test_no_alert_sent_on_success(self, manager):
        """No alert is sent when the wrapped function succeeds."""
        with patch.object(manager, "send_alert") as mock_send:
            manager.alert_on_failure(lambda: "ok")

        mock_send.assert_not_called()

    def test_reraises_exception_after_alert(self, manager):
        """The original exception is re-raised after the alert is sent."""

        def boom():
            raise RuntimeError("kaboom")

        with pytest.raises(RuntimeError, match="kaboom"):
            manager.alert_on_failure(boom)

    def test_sends_alert_when_function_raises(self, manager):
        """An alert is sent when the wrapped function raises an exception."""

        def boom():
            raise ValueError("bad input")

        with patch.object(manager, "send_alert") as mock_send:
            with pytest.raises(ValueError):
                manager.alert_on_failure(boom)

        mock_send.assert_called_once()

    def test_default_alert_level_is_error(self, manager):
        """The default alert level for alert_on_failure is ERROR."""

        def boom():
            raise Exception("oops")

        with patch.object(manager, "send_alert") as mock_send:
            with pytest.raises(Exception):
                manager.alert_on_failure(boom)

        kwargs = mock_send.call_args.kwargs
        assert kwargs["level"] == AlertLevel.ERROR

    def test_custom_alert_level_is_used(self, manager):
        """A custom alert level is forwarded to send_alert."""

        def boom():
            raise Exception("oops")

        with patch.object(manager, "send_alert") as mock_send:
            with pytest.raises(Exception):
                manager.alert_on_failure(boom, level=AlertLevel.CRITICAL)

        kwargs = mock_send.call_args.kwargs
        assert kwargs["level"] == AlertLevel.CRITICAL

    def test_custom_message_is_used(self, manager):
        """A custom message is forwarded to send_alert."""

        def boom():
            raise Exception("oops")

        with patch.object(manager, "send_alert") as mock_send:
            with pytest.raises(Exception):
                manager.alert_on_failure(boom, message="Custom failure message")

        kwargs = mock_send.call_args.kwargs
        assert kwargs["message"] == "Custom failure message"

    def test_default_message_includes_function_name_and_error(self, manager):
        """The default message includes the function name and exception text."""

        def my_function():
            raise ValueError("specific error")

        with patch.object(manager, "send_alert") as mock_send:
            with pytest.raises(ValueError):
                manager.alert_on_failure(my_function)

        kwargs = mock_send.call_args.kwargs
        message = kwargs["message"]
        assert "my_function" in message
        assert "specific error" in message

    def test_alert_details_include_error_type_and_message(self, manager):
        """Alert details include error_type and error_message fields."""

        def boom():
            raise TypeError("wrong type")

        with patch.object(manager, "send_alert") as mock_send:
            with pytest.raises(TypeError):
                manager.alert_on_failure(boom)

        details = mock_send.call_args[1].get("details") or mock_send.call_args[0][2]
        assert details["error_type"] == "TypeError"
        assert details["error_message"] == "wrong type"

    def test_passes_args_and_kwargs_to_function(self, manager):
        """Positional and keyword arguments are forwarded to the wrapped function."""
        received = {}

        def capture(a, b, key=None):
            received["a"] = a
            received["b"] = b
            received["key"] = key
            return "done"

        result = manager.alert_on_failure(capture, 1, 2, key="value")
        assert result == "done"
        assert received == {"a": 1, "b": 2, "key": "value"}
