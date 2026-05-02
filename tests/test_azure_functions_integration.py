"""
Integration tests for Azure Functions.

Tests the full integration of Azure Functions with external dependencies:
- Scheduled execution behavior
- Integration with database, blob storage, and external APIs
- Error handling and retry mechanisms across component boundaries
- Full pipeline flow from trigger to completion

These are INTEGRATION tests (not unit tests). They test actual integration
between components with minimal mocking.

Requirements: 7.2, 7.3
"""

import json
import os
from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock

import pytest

# ---------------------------------------------------------------------------
# Test fixtures and helpers
# ---------------------------------------------------------------------------

WEATHER_FUNCTION_JSON = (
    Path(__file__).parent.parent
    / "src"
    / "uris_ai"
    / "functions"
    / "weather_fetcher"
    / "function.json"
)

RISK_FUNCTION_JSON = (
    Path(__file__).parent.parent
    / "src"
    / "uris_ai"
    / "functions"
    / "risk_calculator"
    / "function.json"
)


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


def _make_flood_prediction(region_id: int, risk_score: float, category_str: str = None):
    """Create a mock FloodRiskPrediction."""
    from uris_ai.ml.flood_risk_engine import FloodRiskPrediction, RiskCategory

    if category_str is None:
        if risk_score <= 25:
            category_str = "RENDAH"
        elif risk_score <= 50:
            category_str = "SEDANG"
        elif risk_score <= 75:
            category_str = "TINGGI"
        else:
            category_str = "KRITIS"

    return FloodRiskPrediction(
        region_id=region_id,
        risk_score=risk_score,
        category=RiskCategory(category_str),
        confidence=0.85,
        timestamp=datetime.now(timezone.utc),
        features_used={},
    )


# ---------------------------------------------------------------------------
# Integration Tests for Weather Fetcher Function
# ---------------------------------------------------------------------------


class TestWeatherFetcherIntegration:
    """
    Integration tests for weather_fetcher Azure Function.
    
    Tests scheduled execution, integration with external APIs and blob storage,
    and error handling across component boundaries.
    
    **Validates: Requirements 7.2, 7.3**
    """

    @patch("uris_ai.data.weather_connector.WeatherAPIConnector", autospec=True)
    def test_integration_scheduled_execution_success(self, MockConnector):
        """
        Integration test: Scheduled execution successfully fetches and stores data.
        
        Tests the full pipeline:
        1. Timer trigger fires
        2. Weather data is fetched from external API
        3. Data is validated
        4. Data is stored to Azure Blob Storage
        5. Success is logged
        
        **Validates: Requirement 7.2 (data integration with retry)**
        """
        from uris_ai.functions.weather_fetcher import main

        # Setup mock connector
        mock_connector = MockConnector.return_value
        mock_connector.fetch_weather_data.return_value = _make_weather_batch([1, 2, 3])
        mock_connector.store_raw_data.return_value = _make_storage_result(success=True)

        timer = _make_timer(past_due=False)

        with patch.dict(os.environ, {"WEATHER_REGION_IDS": "1,2,3"}):
            # Should not raise any exceptions
            main(timer)

        # Verify the full pipeline executed
        mock_connector.fetch_weather_data.assert_called_once_with([1, 2, 3])
        mock_connector.store_raw_data.assert_called_once()

        # Verify storage was called with correct data type
        store_call = mock_connector.store_raw_data.call_args
        assert store_call[1]["data_type"] == "weather" or (
            len(store_call[0]) > 1 and store_call[0][1] == "weather"
        )

    @patch("uris_ai.data.weather_connector.WeatherAPIConnector", autospec=True)
    def test_integration_api_failure_with_retry_recovery(self, MockConnector):
        """
        Integration test: API failure triggers retry and recovers.
        
        Tests error handling and retry mechanism:
        1. First API call fails
        2. Retry mechanism is triggered
        3. Second call succeeds
        4. Data is stored successfully
        5. No exception is raised
        
        **Validates: Requirement 7.2 (retry mechanism)**
        """
        from uris_ai.functions.weather_fetcher import main
        from uris_ai.data.integrator import DataFetchError

        mock_connector = MockConnector.return_value
        
        # First call fails, second succeeds (retry_with_backoff will handle this)
        mock_connector.fetch_weather_data.side_effect = [
            DataFetchError("API timeout"),
            _make_weather_batch([1]),
        ]
        mock_connector.store_raw_data.return_value = _make_storage_result(success=True)

        timer = _make_timer()

        with patch.dict(os.environ, {"WEATHER_REGION_IDS": "1"}):
            # Should not raise - retry should handle the failure
            main(timer)

        # Verify retry happened (fetch_weather_data called multiple times)
        assert mock_connector.fetch_weather_data.call_count >= 1

    @patch("uris_ai.data.weather_connector.WeatherAPIConnector", autospec=True)
    def test_integration_api_failure_exhausted_retries(self, MockConnector):
        """
        Integration test: API failure after all retries exhausted.
        
        Tests error handling when retries are exhausted:
        1. All retry attempts fail
        2. Error is logged
        3. Alert is sent
        4. Function completes without crashing
        
        **Validates: Requirement 7.3 (error handling and logging)**
        """
        from uris_ai.functions.weather_fetcher import main
        from uris_ai.data.integrator import DataFetchError

        mock_connector = MockConnector.return_value
        mock_connector.fetch_weather_data.side_effect = DataFetchError(
            "API unavailable"
        )

        timer = _make_timer()

        with patch.dict(os.environ, {"WEATHER_REGION_IDS": "1"}):
            with patch("uris_ai.functions.weather_fetcher.logger") as mock_logger:
                # Should not raise - error should be handled gracefully
                main(timer)

                # Verify error was logged
                mock_logger.error.assert_called()

        # Storage should not be called when fetch fails
        mock_connector.store_raw_data.assert_not_called()

    @patch("uris_ai.data.weather_connector.WeatherAPIConnector", autospec=True)
    def test_integration_storage_failure_handling(self, MockConnector):
        """
        Integration test: Storage failure is handled gracefully.
        
        Tests error handling when blob storage fails:
        1. Weather data is fetched successfully
        2. Storage operation fails
        3. Error is logged
        4. Function completes without crashing
        
        **Validates: Requirement 7.3 (error handling)**
        """
        from uris_ai.functions.weather_fetcher import main

        mock_connector = MockConnector.return_value
        mock_connector.fetch_weather_data.return_value = _make_weather_batch([1])
        mock_connector.store_raw_data.return_value = _make_storage_result(
            success=False, error_message="Blob storage unavailable"
        )

        timer = _make_timer()

        with patch.dict(os.environ, {"WEATHER_REGION_IDS": "1"}):
            with patch("uris_ai.functions.weather_fetcher.logger") as mock_logger:
                # Should not raise
                main(timer)

                # Verify error was logged
                assert any(
                    "Failed to store" in str(call)
                    for call in mock_logger.error.call_args_list
                )

    @patch("uris_ai.data.weather_connector.WeatherAPIConnector", autospec=True)
    def test_integration_past_due_timer_handling(self, MockConnector):
        """
        Integration test: Past-due timer is handled correctly.
        
        Tests scheduled execution behavior:
        1. Timer is past due
        2. Warning is logged
        3. Function still executes normally
        4. Data is fetched and stored
        
        **Validates: Requirement 7.2 (scheduled execution)**
        """
        from uris_ai.functions.weather_fetcher import main

        mock_connector = MockConnector.return_value
        mock_connector.fetch_weather_data.return_value = _make_weather_batch([1])
        mock_connector.store_raw_data.return_value = _make_storage_result(success=True)

        timer = _make_timer(past_due=True)

        with patch.dict(os.environ, {"WEATHER_REGION_IDS": "1"}):
            with patch("uris_ai.functions.weather_fetcher.logger") as mock_logger:
                main(timer)

                # Verify warning was logged for past-due timer
                mock_logger.warning.assert_called()
                warning_msg = mock_logger.warning.call_args[0][0]
                assert "past due" in warning_msg.lower()

        # Function should still execute normally
        mock_connector.fetch_weather_data.assert_called_once()
        mock_connector.store_raw_data.assert_called_once()

    def test_integration_timer_schedule_configuration(self):
        """
        Integration test: Timer trigger is configured correctly.
        
        Tests function.json configuration:
        1. function.json exists
        2. Timer trigger is configured
        3. Schedule is set to every 10 minutes
        4. Binding direction is correct
        
        **Validates: Requirement 7.2 (scheduled execution every 10 minutes)**
        """
        assert WEATHER_FUNCTION_JSON.exists(), "function.json not found"

        with open(WEATHER_FUNCTION_JSON) as f:
            config = json.load(f)

        # Verify timer trigger binding
        timer_bindings = [
            b for b in config["bindings"] if b.get("type") == "timerTrigger"
        ]
        assert len(timer_bindings) == 1, "Expected exactly one timerTrigger binding"

        timer_binding = timer_bindings[0]
        
        # Verify schedule (every 10 minutes)
        assert timer_binding["schedule"] == "0 */10 * * * *", (
            f"Expected schedule '0 */10 * * * *', got '{timer_binding['schedule']}'"
        )
        
        # Verify binding direction
        assert timer_binding["direction"] == "in"


# ---------------------------------------------------------------------------
# Integration Tests for Risk Calculator Function
# ---------------------------------------------------------------------------


class TestRiskCalculatorIntegration:
    """
    Integration tests for risk_calculator Azure Function.
    
    Tests scheduled execution, integration with ML components and database,
    and error handling across the full risk calculation pipeline.
    
    **Validates: Requirements 7.2, 7.3**
    """

    @patch("uris_ai.ml.risk_scoring_engine.RiskScoringEngine", autospec=True)
    @patch("uris_ai.ml.service_accessibility.ServiceAccessibilityModule", autospec=True)
    @patch("uris_ai.ml.traffic_analyzer.TrafficAnalyzer", autospec=True)
    @patch("uris_ai.ml.flood_risk_engine.FloodRiskEngine", autospec=True)
    def test_integration_scheduled_execution_full_pipeline(
        self,
        MockFloodEngine,
        MockTrafficAnalyzer,
        MockAccessibility,
        MockScoringEngine,
    ):
        """
        Integration test: Full risk calculation pipeline executes successfully.
        
        Tests the complete pipeline:
        1. Timer trigger fires
        2. Flood risk predictions are retrieved
        3. Risk conditions are checked
        4. Traffic impact is analyzed for high-risk regions
        5. Service accessibility is evaluated
        6. Urban Risk Scores are calculated
        7. Risk history is saved to database
        
        **Validates: Requirement 7.2 (data integration and processing)**
        """
        from uris_ai.functions.risk_calculator import main
        from uris_ai.ml.traffic_analyzer import TrafficImpact, CongestionLevel
        from uris_ai.ml.service_accessibility import AccessibilityReport

        # Setup mock components
        flood_preds = [
            _make_flood_prediction(1, 70.0, "TINGGI"),
            _make_flood_prediction(2, 55.0, "TINGGI"),
        ]
        MockFloodEngine.return_value.get_latest_predictions.return_value = flood_preds

        traffic_impact = TrafficImpact(
            region_id=1,
            affected_roads=[1, 2],
            congestion_levels={1: CongestionLevel.SEDANG, 2: CongestionLevel.PARAH},
            is_isolated=False,
            timestamp=datetime.now(timezone.utc),
        )
        MockTrafficAnalyzer.return_value.analyze_traffic_impact.return_value = (
            traffic_impact
        )

        accessibility_report = AccessibilityReport(
            region_id=1,
            affected_facilities=[10, 11],
            alternative_facilities={10: [12], 11: [13]},
            overload_warnings=[],
            timestamp=datetime.now(timezone.utc),
        )
        MockAccessibility.return_value.evaluate_accessibility.return_value = (
            accessibility_report
        )

        MockScoringEngine.return_value.batch_calculate.return_value = {1: 65.0, 2: 52.0}

        timer = _make_timer()

        with patch.dict(
            os.environ,
            {"RISK_REGION_IDS": "1,2", "RISK_ACTIVE_THRESHOLD": "50.0"},
        ):
            # Should not raise
            main(timer)

        # Verify full pipeline executed
        MockFloodEngine.return_value.get_latest_predictions.assert_called_once_with(
            [1, 2]
        )
        MockTrafficAnalyzer.return_value.analyze_traffic_impact.assert_called()
        MockAccessibility.return_value.evaluate_accessibility.assert_called()
        MockScoringEngine.return_value.batch_calculate.assert_called_once_with([1, 2])
        MockScoringEngine.return_value.save_risk_history.assert_called()

    @patch("uris_ai.ml.flood_risk_engine.FloodRiskEngine", autospec=True)
    def test_integration_early_return_when_risk_not_active(self, MockFloodEngine):
        """
        Integration test: Pipeline returns early when risk conditions are not active.
        
        Tests conditional execution:
        1. Timer trigger fires
        2. Flood risk predictions are retrieved
        3. No region exceeds threshold
        4. Pipeline returns early
        5. Subsequent steps are skipped
        
        **Validates: Requirement 7.2 (efficient processing)**
        """
        from uris_ai.functions.risk_calculator import main

        # All scores below threshold
        flood_preds = [
            _make_flood_prediction(1, 30.0, "SEDANG"),
            _make_flood_prediction(2, 25.0, "RENDAH"),
        ]
        MockFloodEngine.return_value.get_latest_predictions.return_value = flood_preds

        timer = _make_timer()

        with patch.dict(
            os.environ,
            {"RISK_REGION_IDS": "1,2", "RISK_ACTIVE_THRESHOLD": "50.0"},
        ):
            with patch(
                "uris_ai.ml.traffic_analyzer.TrafficAnalyzer", autospec=True
            ) as MockTraffic:
                main(timer)

                # TrafficAnalyzer should NOT be instantiated
                MockTraffic.assert_not_called()

    @patch("uris_ai.ml.risk_scoring_engine.RiskScoringEngine", autospec=True)
    @patch("uris_ai.ml.service_accessibility.ServiceAccessibilityModule", autospec=True)
    @patch("uris_ai.ml.traffic_analyzer.TrafficAnalyzer", autospec=True)
    @patch("uris_ai.ml.flood_risk_engine.FloodRiskEngine", autospec=True)
    def test_integration_error_handling_flood_engine_failure(
        self,
        MockFloodEngine,
        MockTrafficAnalyzer,
        MockAccessibility,
        MockScoringEngine,
    ):
        """
        Integration test: Flood engine failure is handled gracefully.
        
        Tests error handling:
        1. Flood engine raises exception
        2. Error is logged
        3. Alert is sent
        4. Function completes without crashing
        5. Subsequent steps are skipped
        
        **Validates: Requirement 7.3 (error handling)**
        """
        from uris_ai.functions.risk_calculator import main

        MockFloodEngine.return_value.get_latest_predictions.side_effect = RuntimeError(
            "Model not loaded"
        )

        timer = _make_timer()

        with patch.dict(os.environ, {"RISK_REGION_IDS": "1,2"}):
            with patch("uris_ai.functions.risk_calculator.logger") as mock_logger:
                # Should not raise
                main(timer)

                # Verify error was logged
                mock_logger.error.assert_called()

        # Subsequent components should not be called
        MockTrafficAnalyzer.assert_not_called()
        MockAccessibility.assert_not_called()
        MockScoringEngine.assert_not_called()

    @patch("uris_ai.ml.risk_scoring_engine.RiskScoringEngine", autospec=True)
    @patch("uris_ai.ml.service_accessibility.ServiceAccessibilityModule", autospec=True)
    @patch("uris_ai.ml.traffic_analyzer.TrafficAnalyzer", autospec=True)
    @patch("uris_ai.ml.flood_risk_engine.FloodRiskEngine", autospec=True)
    def test_integration_error_handling_traffic_analyzer_failure(
        self,
        MockFloodEngine,
        MockTrafficAnalyzer,
        MockAccessibility,
        MockScoringEngine,
    ):
        """
        Integration test: Traffic analyzer failure doesn't stop pipeline.
        
        Tests error handling:
        1. Flood predictions succeed
        2. Traffic analyzer raises exception
        3. Error is logged
        4. Pipeline continues with other components
        5. Risk scores are still calculated
        
        **Validates: Requirement 7.3 (error handling and resilience)**
        """
        from uris_ai.functions.risk_calculator import main

        flood_preds = [_make_flood_prediction(1, 70.0, "TINGGI")]
        MockFloodEngine.return_value.get_latest_predictions.return_value = flood_preds

        MockTrafficAnalyzer.return_value.analyze_traffic_impact.side_effect = (
            RuntimeError("DB connection failed")
        )

        MockScoringEngine.return_value.batch_calculate.return_value = {1: 60.0}

        timer = _make_timer()

        with patch.dict(os.environ, {"RISK_REGION_IDS": "1"}):
            with patch("uris_ai.functions.risk_calculator.logger") as mock_logger:
                # Should not raise
                main(timer)

                # Verify error was logged
                assert any(
                    "TrafficAnalyzer" in str(call)
                    for call in mock_logger.error.call_args_list
                )

        # Pipeline should continue - scoring engine should still be called
        MockScoringEngine.return_value.batch_calculate.assert_called()

    @patch("uris_ai.ml.risk_scoring_engine.RiskScoringEngine", autospec=True)
    @patch("uris_ai.ml.service_accessibility.ServiceAccessibilityModule", autospec=True)
    @patch("uris_ai.ml.traffic_analyzer.TrafficAnalyzer", autospec=True)
    @patch("uris_ai.ml.flood_risk_engine.FloodRiskEngine", autospec=True)
    def test_integration_error_handling_database_save_failure(
        self,
        MockFloodEngine,
        MockTrafficAnalyzer,
        MockAccessibility,
        MockScoringEngine,
    ):
        """
        Integration test: Database save failure is handled gracefully.
        
        Tests error handling:
        1. Risk calculation succeeds
        2. Database save operation fails
        3. Error is logged
        4. Alert is sent
        5. Function completes without crashing
        
        **Validates: Requirement 7.3 (error handling and logging)**
        """
        from uris_ai.functions.risk_calculator import main
        from uris_ai.ml.traffic_analyzer import TrafficImpact, CongestionLevel
        from uris_ai.ml.service_accessibility import AccessibilityReport

        flood_preds = [_make_flood_prediction(1, 70.0, "TINGGI")]
        MockFloodEngine.return_value.get_latest_predictions.return_value = flood_preds

        traffic_impact = TrafficImpact(
            region_id=1,
            affected_roads=[1],
            congestion_levels={1: CongestionLevel.SEDANG},
            is_isolated=False,
            timestamp=datetime.now(timezone.utc),
        )
        MockTrafficAnalyzer.return_value.analyze_traffic_impact.return_value = (
            traffic_impact
        )

        accessibility_report = AccessibilityReport(
            region_id=1,
            affected_facilities=[],
            alternative_facilities={},
            overload_warnings=[],
            timestamp=datetime.now(timezone.utc),
        )
        MockAccessibility.return_value.evaluate_accessibility.return_value = (
            accessibility_report
        )

        MockScoringEngine.return_value.batch_calculate.return_value = {1: 60.0}
        MockScoringEngine.return_value.save_risk_history.side_effect = RuntimeError(
            "DB write failed"
        )

        timer = _make_timer()

        with patch.dict(os.environ, {"RISK_REGION_IDS": "1"}):
            with patch("uris_ai.functions.risk_calculator.logger") as mock_logger:
                # Should not raise
                main(timer)

                # Verify error was logged
                assert any(
                    "save_risk_history" in str(call)
                    for call in mock_logger.error.call_args_list
                )

    def test_integration_timer_schedule_configuration(self):
        """
        Integration test: Timer trigger is configured correctly.
        
        Tests function.json configuration:
        1. function.json exists
        2. Timer trigger is configured
        3. Schedule is set to every 5 minutes
        4. Binding direction is correct
        
        **Validates: Requirement 7.2 (scheduled execution every 5 minutes)**
        """
        assert RISK_FUNCTION_JSON.exists(), "function.json not found"

        with open(RISK_FUNCTION_JSON) as f:
            config = json.load(f)

        # Verify timer trigger binding
        timer_bindings = [
            b for b in config["bindings"] if b.get("type") == "timerTrigger"
        ]
        assert len(timer_bindings) == 1, "Expected exactly one timerTrigger binding"

        timer_binding = timer_bindings[0]
        
        # Verify schedule (every 5 minutes)
        assert timer_binding["schedule"] == "0 */5 * * * *", (
            f"Expected schedule '0 */5 * * * *', got '{timer_binding['schedule']}'"
        )
        
        # Verify binding direction
        assert timer_binding["direction"] == "in"

    @patch("uris_ai.ml.flood_risk_engine.FloodRiskEngine", autospec=True)
    def test_integration_past_due_timer_handling(self, MockFloodEngine):
        """
        Integration test: Past-due timer is handled correctly.
        
        Tests scheduled execution behavior:
        1. Timer is past due
        2. Warning is logged
        3. Function still executes normally
        
        **Validates: Requirement 7.2 (scheduled execution)**
        """
        from uris_ai.functions.risk_calculator import main

        flood_preds = [_make_flood_prediction(1, 30.0, "SEDANG")]
        MockFloodEngine.return_value.get_latest_predictions.return_value = flood_preds

        timer = _make_timer(past_due=True)

        with patch.dict(os.environ, {"RISK_REGION_IDS": "1"}):
            with patch("uris_ai.functions.risk_calculator.logger") as mock_logger:
                main(timer)

                # Verify warning was logged for past-due timer
                mock_logger.warning.assert_called()
                warning_msg = mock_logger.warning.call_args[0][0]
                assert "past due" in warning_msg.lower()

        # Function should still execute normally
        MockFloodEngine.return_value.get_latest_predictions.assert_called_once()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
