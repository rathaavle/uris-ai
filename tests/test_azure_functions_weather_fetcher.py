"""
Unit tests for Azure Function: weather_fetcher

Tests the scheduled weather data fetching Azure Function including:
- Timer trigger handling (including past-due scenarios)
- Successful weather data fetch and storage
- Error handling for DataFetchError
- Error handling for storage failures
- Region ID configuration via environment variable
- Graceful handling of unexpected exceptions

Requirements: 1.1, 7.2
"""

import os
from datetime import datetime
from unittest.mock import MagicMock, Mock, patch

import pytest

# ---------------------------------------------------------------------------
# Helpers / fixtures
# ---------------------------------------------------------------------------


def _make_timer(past_due: bool = False) -> Mock:
    """Create a mock Azure Functions TimerRequest."""
    timer = Mock()
    timer.past_due = past_due
    return timer


def _make_weather_batch(region_ids=None):
    """Create a mock WeatherDataBatch."""
    from uris_ai.data.models import WeatherData, WeatherDataBatch

    if region_ids is None:
        region_ids = [1, 2, 3]

    data = [
        WeatherData(
            region_id=rid,
            date=datetime(2024, 1, 15, 10, 0, 0),
            rainfall=50.0,
            humidity=80.0,
            temperature=28.0,
            wind_speed=15.0,
        )
        for rid in region_ids
    ]
    return WeatherDataBatch(
        data=data,
        timestamp=datetime(2024, 1, 15, 10, 0, 0),
        source="https://api.test.com/weather",
    )


def _make_storage_result(success: bool = True, error_message: str = None):
    """Create a mock StorageResult."""
    from uris_ai.data.models import StorageResult

    return StorageResult(
        success=success,
        blob_url="https://test.blob.core.windows.net/raw-data/weather/20240115_100000.json"
        if success
        else "",
        blob_name="weather/20240115_100000.json",
        size_bytes=1024 if success else 0,
        timestamp=datetime(2024, 1, 15, 10, 0, 0),
        error_message=error_message,
    )


# ---------------------------------------------------------------------------
# Tests for _get_region_ids helper
# ---------------------------------------------------------------------------


class TestGetRegionIds:
    """Tests for the _get_region_ids helper function."""

    def test_returns_default_when_env_not_set(self):
        """Returns DEFAULT_REGION_IDS when WEATHER_REGION_IDS is not set."""
        from uris_ai.functions.weather_fetcher import DEFAULT_REGION_IDS, _get_region_ids

        with patch.dict(os.environ, {}, clear=False):
            os.environ.pop("WEATHER_REGION_IDS", None)
            result = _get_region_ids()

        assert result == DEFAULT_REGION_IDS

    def test_parses_comma_separated_integers(self):
        """Parses a comma-separated list of integers from the environment variable."""
        from uris_ai.functions.weather_fetcher import _get_region_ids

        with patch.dict(os.environ, {"WEATHER_REGION_IDS": "1,2,3,4,5"}):
            result = _get_region_ids()

        assert result == [1, 2, 3, 4, 5]

    def test_handles_whitespace_around_values(self):
        """Handles whitespace around comma-separated values."""
        from uris_ai.functions.weather_fetcher import _get_region_ids

        with patch.dict(os.environ, {"WEATHER_REGION_IDS": " 10 , 20 , 30 "}):
            result = _get_region_ids()

        assert result == [10, 20, 30]

    def test_falls_back_to_defaults_on_invalid_value(self):
        """Falls back to DEFAULT_REGION_IDS when the env var contains non-integers."""
        from uris_ai.functions.weather_fetcher import DEFAULT_REGION_IDS, _get_region_ids

        with patch.dict(os.environ, {"WEATHER_REGION_IDS": "abc,def"}):
            result = _get_region_ids()

        assert result == DEFAULT_REGION_IDS

    def test_single_region_id(self):
        """Handles a single region ID without a comma."""
        from uris_ai.functions.weather_fetcher import _get_region_ids

        with patch.dict(os.environ, {"WEATHER_REGION_IDS": "42"}):
            result = _get_region_ids()

        assert result == [42]


# ---------------------------------------------------------------------------
# Tests for main() entry point
# ---------------------------------------------------------------------------


class TestWeatherFetcherMain:
    """Tests for the main() Azure Function entry point."""

    @patch("uris_ai.functions.weather_fetcher._fetch_and_store_weather")
    def test_main_calls_fetch_and_store(self, mock_fetch_store):
        """main() calls _fetch_and_store_weather with the configured region IDs."""
        from uris_ai.functions.weather_fetcher import main

        timer = _make_timer(past_due=False)

        with patch.dict(os.environ, {"WEATHER_REGION_IDS": "1,2,3"}):
            main(timer)

        mock_fetch_store.assert_called_once()
        call_args = mock_fetch_store.call_args
        assert call_args[0][0] == [1, 2, 3]  # region_ids positional arg

    @patch("uris_ai.functions.weather_fetcher._fetch_and_store_weather")
    def test_main_logs_warning_when_past_due(self, mock_fetch_store):
        """main() logs a warning when the timer is past due."""
        from uris_ai.functions.weather_fetcher import main

        timer = _make_timer(past_due=True)

        with patch("uris_ai.functions.weather_fetcher.logger") as mock_logger:
            with patch.dict(os.environ, {"WEATHER_REGION_IDS": "1"}):
                main(timer)

        # Warning should have been logged for past-due timer
        mock_logger.warning.assert_called_once()
        warning_msg = mock_logger.warning.call_args[0][0]
        assert "past due" in warning_msg.lower()

    @patch("uris_ai.functions.weather_fetcher._fetch_and_store_weather")
    def test_main_does_not_raise_on_unexpected_exception(self, mock_fetch_store):
        """main() catches unexpected exceptions and does not re-raise them."""
        from uris_ai.functions.weather_fetcher import main

        mock_fetch_store.side_effect = RuntimeError("Unexpected crash")
        timer = _make_timer()

        # Should NOT raise — the function host must not crash
        with patch.dict(os.environ, {"WEATHER_REGION_IDS": "1"}):
            main(timer)  # No exception expected

    @patch("uris_ai.functions.weather_fetcher._fetch_and_store_weather")
    def test_main_logs_error_on_unexpected_exception(self, mock_fetch_store):
        """main() logs an error when an unexpected exception occurs."""
        from uris_ai.functions.weather_fetcher import main

        mock_fetch_store.side_effect = RuntimeError("Unexpected crash")
        timer = _make_timer()

        with patch("uris_ai.functions.weather_fetcher.logger") as mock_logger:
            with patch.dict(os.environ, {"WEATHER_REGION_IDS": "1"}):
                main(timer)

        mock_logger.error.assert_called_once()
        error_msg = mock_logger.error.call_args[0][0]
        assert "Unhandled error" in error_msg

    @patch("uris_ai.functions.weather_fetcher._fetch_and_store_weather")
    def test_main_uses_default_region_ids_when_env_not_set(self, mock_fetch_store):
        """main() uses DEFAULT_REGION_IDS when WEATHER_REGION_IDS is not set."""
        from uris_ai.functions.weather_fetcher import DEFAULT_REGION_IDS, main

        timer = _make_timer()
        env_without_region_ids = {k: v for k, v in os.environ.items() if k != "WEATHER_REGION_IDS"}

        with patch.dict(os.environ, env_without_region_ids, clear=True):
            main(timer)

        call_args = mock_fetch_store.call_args
        assert call_args[0][0] == DEFAULT_REGION_IDS


# ---------------------------------------------------------------------------
# Tests for _fetch_and_store_weather()
# ---------------------------------------------------------------------------


class TestFetchAndStoreWeather:
    """Tests for the _fetch_and_store_weather() internal function.

    Because WeatherAPIConnector is imported inside _fetch_and_store_weather
    (deferred import), we patch it at its definition site:
    'uris_ai.data.weather_connector.WeatherAPIConnector'.
    """

    @patch("uris_ai.data.weather_connector.WeatherAPIConnector", autospec=True)
    def test_successful_fetch_and_store(self, MockConnector):
        """Fetches weather data and stores it to blob storage on success."""
        from uris_ai.functions.weather_fetcher import _fetch_and_store_weather

        mock_connector = MockConnector.return_value
        mock_connector.fetch_weather_data.return_value = _make_weather_batch([1, 2, 3])
        mock_connector.store_raw_data.return_value = _make_storage_result(success=True)

        _fetch_and_store_weather([1, 2, 3], "2024-01-15T10:00:00")

        mock_connector.fetch_weather_data.assert_called_once_with([1, 2, 3])
        mock_connector.store_raw_data.assert_called_once()

        # Verify store_raw_data was called with correct data_type
        store_call_kwargs = mock_connector.store_raw_data.call_args
        assert store_call_kwargs[1]["data_type"] == "weather" or (
            len(store_call_kwargs[0]) > 1 and store_call_kwargs[0][1] == "weather"
        )

    @patch("uris_ai.data.weather_connector.WeatherAPIConnector", autospec=True)
    def test_data_fetch_error_is_handled_gracefully(self, MockConnector):
        """DataFetchError from the connector is caught and does not propagate."""
        from uris_ai.data.integrator import DataFetchError
        from uris_ai.functions.weather_fetcher import _fetch_and_store_weather

        mock_connector = MockConnector.return_value
        mock_connector.fetch_weather_data.side_effect = DataFetchError(
            "API unavailable"
        )

        # Should NOT raise
        _fetch_and_store_weather([1, 2, 3], "2024-01-15T10:00:00")

        # store_raw_data should NOT be called when fetch fails
        mock_connector.store_raw_data.assert_not_called()

    @patch("uris_ai.data.weather_connector.WeatherAPIConnector", autospec=True)
    def test_data_fetch_error_is_logged(self, MockConnector):
        """DataFetchError is logged as an error."""
        from uris_ai.data.integrator import DataFetchError
        from uris_ai.functions.weather_fetcher import _fetch_and_store_weather

        mock_connector = MockConnector.return_value
        mock_connector.fetch_weather_data.side_effect = DataFetchError(
            "API unavailable"
        )

        with patch("uris_ai.functions.weather_fetcher.logger") as mock_logger:
            _fetch_and_store_weather([1, 2, 3], "2024-01-15T10:00:00")

        mock_logger.error.assert_called_once()

    @patch("uris_ai.data.weather_connector.WeatherAPIConnector", autospec=True)
    def test_storage_failure_is_logged(self, MockConnector):
        """Storage failure is logged as an error."""
        from uris_ai.functions.weather_fetcher import _fetch_and_store_weather

        mock_connector = MockConnector.return_value
        mock_connector.fetch_weather_data.return_value = _make_weather_batch([1])
        mock_connector.store_raw_data.return_value = _make_storage_result(
            success=False, error_message="Blob storage unavailable"
        )

        with patch("uris_ai.functions.weather_fetcher.logger") as mock_logger:
            _fetch_and_store_weather([1], "2024-01-15T10:00:00")

        # An error should have been logged for the storage failure
        mock_logger.error.assert_called_once()
        error_msg = mock_logger.error.call_args[0][0]
        assert "Failed to store" in error_msg

    @patch("uris_ai.data.weather_connector.WeatherAPIConnector", autospec=True)
    def test_successful_storage_is_logged_as_info(self, MockConnector):
        """Successful storage is logged at INFO level."""
        from uris_ai.functions.weather_fetcher import _fetch_and_store_weather

        mock_connector = MockConnector.return_value
        mock_connector.fetch_weather_data.return_value = _make_weather_batch([1, 2])
        mock_connector.store_raw_data.return_value = _make_storage_result(success=True)

        with patch("uris_ai.functions.weather_fetcher.logger") as mock_logger:
            _fetch_and_store_weather([1, 2], "2024-01-15T10:00:00")

        # At least two info logs: one for fetch success, one for storage success
        assert mock_logger.info.call_count >= 2

    @patch("uris_ai.data.weather_connector.WeatherAPIConnector", autospec=True)
    def test_store_raw_data_receives_metadata(self, MockConnector):
        """store_raw_data is called with metadata including trigger_time and region_count."""
        from uris_ai.functions.weather_fetcher import _fetch_and_store_weather

        trigger_time = "2024-01-15T10:00:00"
        region_ids = [1, 2, 3]

        mock_connector = MockConnector.return_value
        mock_connector.fetch_weather_data.return_value = _make_weather_batch(region_ids)
        mock_connector.store_raw_data.return_value = _make_storage_result(success=True)

        _fetch_and_store_weather(region_ids, trigger_time)

        store_call = mock_connector.store_raw_data.call_args
        metadata = store_call[1].get("metadata") or (
            store_call[0][2] if len(store_call[0]) > 2 else None
        )
        assert metadata is not None
        assert metadata.get("trigger_time") == trigger_time
        assert metadata.get("region_count") == str(len(region_ids))


# ---------------------------------------------------------------------------
# Tests for function.json binding configuration
# ---------------------------------------------------------------------------


class TestFunctionJsonConfig:
    """Tests that function.json has the correct binding configuration."""

    def test_function_json_exists(self):
        """function.json exists in the weather_fetcher directory."""
        import json
        from pathlib import Path

        function_json_path = (
            Path(__file__).parent.parent
            / "src"
            / "uris_ai"
            / "functions"
            / "weather_fetcher"
            / "function.json"
        )
        assert function_json_path.exists(), "function.json not found"

        with open(function_json_path) as f:
            config = json.load(f)

        assert "bindings" in config

    def test_function_json_has_timer_trigger(self):
        """function.json defines a timerTrigger binding."""
        import json
        from pathlib import Path

        function_json_path = (
            Path(__file__).parent.parent
            / "src"
            / "uris_ai"
            / "functions"
            / "weather_fetcher"
            / "function.json"
        )

        with open(function_json_path) as f:
            config = json.load(f)

        bindings = config["bindings"]
        timer_bindings = [b for b in bindings if b.get("type") == "timerTrigger"]
        assert len(timer_bindings) == 1, "Expected exactly one timerTrigger binding"

    def test_function_json_timer_schedule_is_every_10_minutes(self):
        """Timer trigger schedule is set to run every 10 minutes (0 */10 * * * *)."""
        import json
        from pathlib import Path

        function_json_path = (
            Path(__file__).parent.parent
            / "src"
            / "uris_ai"
            / "functions"
            / "weather_fetcher"
            / "function.json"
        )

        with open(function_json_path) as f:
            config = json.load(f)

        timer_binding = next(
            b for b in config["bindings"] if b.get("type") == "timerTrigger"
        )
        assert timer_binding["schedule"] == "0 */10 * * * *", (
            f"Expected schedule '0 */10 * * * *', got '{timer_binding['schedule']}'"
        )

    def test_function_json_timer_binding_direction_is_in(self):
        """Timer trigger binding direction is 'in'."""
        import json
        from pathlib import Path

        function_json_path = (
            Path(__file__).parent.parent
            / "src"
            / "uris_ai"
            / "functions"
            / "weather_fetcher"
            / "function.json"
        )

        with open(function_json_path) as f:
            config = json.load(f)

        timer_binding = next(
            b for b in config["bindings"] if b.get("type") == "timerTrigger"
        )
        assert timer_binding["direction"] == "in"
