"""
Unit tests for Azure Function: risk_calculator

Tests the scheduled risk calculation Azure Function including:
- Timer trigger handling (including past-due scenarios)
- Early return when risk conditions are not active
- Full pipeline execution when risk conditions are active
- Error handling for each pipeline step
- Graceful handling of unexpected exceptions
- RISK_ACTIVE_THRESHOLD environment variable configuration
- function.json has correct timer binding (every 5 minutes)

Requirements: 3.4, 4.3
"""

import json
import os
from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import MagicMock, Mock, call, patch

import pytest

# ---------------------------------------------------------------------------
# Helpers / fixtures
# ---------------------------------------------------------------------------

FUNCTION_JSON_PATH = (
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


def _make_flood_prediction(region_id: int, risk_score: float, category_str: str = None):
    """Create a mock FloodRiskPrediction."""
    from uris_ai.ml.flood_risk_engine import FloodRiskPrediction, RiskCategory

    if category_str is None:
        # Derive category from score
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


def _make_traffic_impact(region_id: int, affected_roads=None, is_isolated=False):
    """Create a mock TrafficImpact."""
    from uris_ai.ml.traffic_analyzer import TrafficImpact, CongestionLevel

    if affected_roads is None:
        affected_roads = [1, 2]

    congestion_levels = {road_id: CongestionLevel.SEDANG for road_id in affected_roads}

    return TrafficImpact(
        region_id=region_id,
        affected_roads=affected_roads,
        congestion_levels=congestion_levels,
        is_isolated=is_isolated,
        timestamp=datetime.now(timezone.utc),
    )


def _make_accessibility_report(region_id: int, affected_facilities=None):
    """Create a mock AccessibilityReport."""
    from uris_ai.ml.service_accessibility import AccessibilityReport

    if affected_facilities is None:
        affected_facilities = [10, 11]

    return AccessibilityReport(
        region_id=region_id,
        affected_facilities=affected_facilities,
        alternative_facilities={fid: [] for fid in affected_facilities},
        overload_warnings=[],
        timestamp=datetime.now(timezone.utc),
    )


# ---------------------------------------------------------------------------
# Tests for _get_risk_active_threshold helper
# ---------------------------------------------------------------------------


class TestGetRiskActiveThreshold:
    """Tests for the _get_risk_active_threshold helper function."""

    def test_returns_default_when_env_not_set(self):
        """Returns DEFAULT_RISK_ACTIVE_THRESHOLD when env var is not set."""
        from uris_ai.functions.risk_calculator import (
            DEFAULT_RISK_ACTIVE_THRESHOLD,
            _get_risk_active_threshold,
        )

        env = {k: v for k, v in os.environ.items() if k != "RISK_ACTIVE_THRESHOLD"}
        with patch.dict(os.environ, env, clear=True):
            result = _get_risk_active_threshold()

        assert result == DEFAULT_RISK_ACTIVE_THRESHOLD

    def test_parses_float_from_env(self):
        """Parses a float value from RISK_ACTIVE_THRESHOLD env var."""
        from uris_ai.functions.risk_calculator import _get_risk_active_threshold

        with patch.dict(os.environ, {"RISK_ACTIVE_THRESHOLD": "75.0"}):
            result = _get_risk_active_threshold()

        assert result == 75.0

    def test_parses_integer_string_from_env(self):
        """Parses an integer string from RISK_ACTIVE_THRESHOLD env var."""
        from uris_ai.functions.risk_calculator import _get_risk_active_threshold

        with patch.dict(os.environ, {"RISK_ACTIVE_THRESHOLD": "60"}):
            result = _get_risk_active_threshold()

        assert result == 60.0

    def test_falls_back_to_default_on_invalid_value(self):
        """Falls back to default when env var contains a non-numeric value."""
        from uris_ai.functions.risk_calculator import (
            DEFAULT_RISK_ACTIVE_THRESHOLD,
            _get_risk_active_threshold,
        )

        with patch.dict(os.environ, {"RISK_ACTIVE_THRESHOLD": "not-a-number"}):
            result = _get_risk_active_threshold()

        assert result == DEFAULT_RISK_ACTIVE_THRESHOLD


# ---------------------------------------------------------------------------
# Tests for _is_risk_conditions_active helper
# ---------------------------------------------------------------------------


class TestIsRiskConditionsActive:
    """Tests for the _is_risk_conditions_active helper function."""

    def test_returns_false_when_no_predictions(self):
        """Returns False when the predictions list is empty."""
        from uris_ai.functions.risk_calculator import _is_risk_conditions_active

        assert _is_risk_conditions_active([], threshold=50.0) is False

    def test_returns_false_when_all_scores_below_threshold(self):
        """Returns False when all flood risk scores are at or below the threshold."""
        from uris_ai.functions.risk_calculator import _is_risk_conditions_active

        predictions = [
            _make_flood_prediction(1, 30.0),
            _make_flood_prediction(2, 50.0),
        ]
        assert _is_risk_conditions_active(predictions, threshold=50.0) is False

    def test_returns_true_when_any_score_exceeds_threshold(self):
        """Returns True when at least one flood risk score exceeds the threshold."""
        from uris_ai.functions.risk_calculator import _is_risk_conditions_active

        predictions = [
            _make_flood_prediction(1, 30.0),
            _make_flood_prediction(2, 51.0),
        ]
        assert _is_risk_conditions_active(predictions, threshold=50.0) is True

    def test_returns_true_when_all_scores_exceed_threshold(self):
        """Returns True when all flood risk scores exceed the threshold."""
        from uris_ai.functions.risk_calculator import _is_risk_conditions_active

        predictions = [
            _make_flood_prediction(1, 60.0),
            _make_flood_prediction(2, 80.0),
        ]
        assert _is_risk_conditions_active(predictions, threshold=50.0) is True

    def test_threshold_is_exclusive(self):
        """A score exactly equal to the threshold does NOT activate risk conditions."""
        from uris_ai.functions.risk_calculator import _is_risk_conditions_active

        predictions = [_make_flood_prediction(1, 50.0)]
        assert _is_risk_conditions_active(predictions, threshold=50.0) is False


# ---------------------------------------------------------------------------
# Tests for main() entry point
# ---------------------------------------------------------------------------


class TestRiskCalculatorMain:
    """Tests for the main() Azure Function entry point."""

    @patch("uris_ai.functions.risk_calculator._run_risk_calculation_pipeline")
    def test_main_calls_pipeline(self, mock_pipeline):
        """main() calls _run_risk_calculation_pipeline."""
        from uris_ai.functions.risk_calculator import main

        timer = _make_timer(past_due=False)
        with patch.dict(os.environ, {"RISK_REGION_IDS": "1,2,3"}):
            main(timer)

        mock_pipeline.assert_called_once()

    @patch("uris_ai.functions.risk_calculator._run_risk_calculation_pipeline")
    def test_main_logs_warning_when_past_due(self, mock_pipeline):
        """main() logs a warning when the timer is past due."""
        from uris_ai.functions.risk_calculator import main

        timer = _make_timer(past_due=True)

        with patch("uris_ai.functions.risk_calculator.logger") as mock_logger:
            with patch.dict(os.environ, {"RISK_REGION_IDS": "1"}):
                main(timer)

        mock_logger.warning.assert_called_once()
        warning_msg = mock_logger.warning.call_args[0][0]
        assert "past due" in warning_msg.lower()

    @patch("uris_ai.functions.risk_calculator._run_risk_calculation_pipeline")
    def test_main_does_not_raise_on_unexpected_exception(self, mock_pipeline):
        """main() catches unexpected exceptions and does not re-raise them."""
        from uris_ai.functions.risk_calculator import main

        mock_pipeline.side_effect = RuntimeError("Unexpected crash")
        timer = _make_timer()

        # Should NOT raise — the function host must not crash
        with patch.dict(os.environ, {"RISK_REGION_IDS": "1"}):
            main(timer)  # No exception expected

    @patch("uris_ai.functions.risk_calculator._run_risk_calculation_pipeline")
    def test_main_logs_error_on_unexpected_exception(self, mock_pipeline):
        """main() logs an error when an unexpected exception occurs."""
        from uris_ai.functions.risk_calculator import main

        mock_pipeline.side_effect = RuntimeError("Unexpected crash")
        timer = _make_timer()

        with patch("uris_ai.functions.risk_calculator.logger") as mock_logger:
            with patch.dict(os.environ, {"RISK_REGION_IDS": "1"}):
                main(timer)

        mock_logger.error.assert_called_once()
        error_msg = mock_logger.error.call_args[0][0]
        assert "Unhandled error" in error_msg

    @patch("uris_ai.functions.risk_calculator._run_risk_calculation_pipeline")
    def test_main_passes_threshold_to_pipeline(self, mock_pipeline):
        """main() passes the configured threshold to the pipeline."""
        from uris_ai.functions.risk_calculator import main

        timer = _make_timer()
        with patch.dict(
            os.environ,
            {"RISK_REGION_IDS": "1,2", "RISK_ACTIVE_THRESHOLD": "70.0"},
        ):
            main(timer)

        call_args = mock_pipeline.call_args
        # Second positional arg is threshold
        assert call_args[0][1] == 70.0

    @patch("uris_ai.functions.risk_calculator._run_risk_calculation_pipeline")
    def test_main_passes_region_ids_to_pipeline(self, mock_pipeline):
        """main() passes the configured region IDs to the pipeline."""
        from uris_ai.functions.risk_calculator import main

        timer = _make_timer()
        with patch.dict(os.environ, {"RISK_REGION_IDS": "5,6,7"}):
            main(timer)

        call_args = mock_pipeline.call_args
        assert call_args[0][0] == [5, 6, 7]


# ---------------------------------------------------------------------------
# Tests for _run_risk_calculation_pipeline() — early return path
# ---------------------------------------------------------------------------


class TestPipelineEarlyReturn:
    """Tests for the early-return path when risk conditions are not active."""

    @patch("uris_ai.ml.flood_risk_engine.FloodRiskEngine", autospec=True)
    def test_returns_early_when_risk_not_active(self, MockFloodEngine):
        """Pipeline returns early and skips further steps when risk is not active."""
        from uris_ai.functions.risk_calculator import _run_risk_calculation_pipeline

        mock_engine = MockFloodEngine.return_value
        # All scores below threshold
        mock_engine.get_latest_predictions.return_value = [
            _make_flood_prediction(1, 20.0),
            _make_flood_prediction(2, 30.0),
        ]

        with patch(
            "uris_ai.ml.traffic_analyzer.TrafficAnalyzer", autospec=True
        ) as MockTraffic:
            _run_risk_calculation_pipeline([1, 2], 50.0, "2024-01-15T10:00:00")

            # TrafficAnalyzer should NOT be instantiated or called
            MockTraffic.assert_not_called()

    @patch("uris_ai.ml.flood_risk_engine.FloodRiskEngine", autospec=True)
    def test_logs_info_when_risk_not_active(self, MockFloodEngine):
        """Pipeline logs an INFO message when risk conditions are not active."""
        from uris_ai.functions.risk_calculator import _run_risk_calculation_pipeline

        mock_engine = MockFloodEngine.return_value
        mock_engine.get_latest_predictions.return_value = [
            _make_flood_prediction(1, 10.0),
        ]

        with patch("uris_ai.functions.risk_calculator.logger") as mock_logger:
            _run_risk_calculation_pipeline([1], 50.0, "2024-01-15T10:00:00")

        # Should log at INFO level about skipping — check the format string
        assert mock_logger.info.call_count >= 1
        all_format_strings = [c.args[0] for c in mock_logger.info.call_args_list]
        assert any(
            "not active" in fmt.lower() or "skipping" in fmt.lower()
            for fmt in all_format_strings
        )


# ---------------------------------------------------------------------------
# Tests for _run_risk_calculation_pipeline() — full pipeline path
# ---------------------------------------------------------------------------


class TestPipelineFullExecution:
    """Tests for the full pipeline execution when risk conditions are active."""

    def _setup_mocks(self, flood_predictions, traffic_impact, accessibility_report, risk_scores):
        """Helper to set up all pipeline mocks."""
        mock_flood_engine = MagicMock()
        mock_flood_engine.batch_predict.return_value = flood_predictions

        mock_traffic_analyzer = MagicMock()
        mock_traffic_analyzer.analyze_traffic_impact.return_value = traffic_impact

        mock_accessibility = MagicMock()
        mock_accessibility.evaluate_accessibility.return_value = accessibility_report

        mock_scoring_engine = MagicMock()
        mock_scoring_engine.batch_calculate.return_value = risk_scores

        return (
            mock_flood_engine,
            mock_traffic_analyzer,
            mock_accessibility,
            mock_scoring_engine,
        )

    @patch("uris_ai.ml.risk_scoring_engine.RiskScoringEngine", autospec=True)
    @patch("uris_ai.ml.service_accessibility.ServiceAccessibilityModule", autospec=True)
    @patch("uris_ai.ml.traffic_analyzer.TrafficAnalyzer", autospec=True)
    @patch("uris_ai.ml.flood_risk_engine.FloodRiskEngine", autospec=True)
    def test_full_pipeline_runs_all_steps(
        self,
        MockFloodEngine,
        MockTrafficAnalyzer,
        MockAccessibility,
        MockScoringEngine,
    ):
        """All pipeline steps are executed when risk conditions are active."""
        from uris_ai.functions.risk_calculator import _run_risk_calculation_pipeline

        region_ids = [1, 2]
        flood_preds = [
            _make_flood_prediction(1, 60.0, "TINGGI"),
            _make_flood_prediction(2, 40.0, "SEDANG"),
        ]
        traffic_impact = _make_traffic_impact(1)
        accessibility_report = _make_accessibility_report(1)

        MockFloodEngine.return_value.get_latest_predictions.return_value = flood_preds
        MockTrafficAnalyzer.return_value.analyze_traffic_impact.return_value = traffic_impact
        MockAccessibility.return_value.evaluate_accessibility.return_value = accessibility_report
        MockScoringEngine.return_value.batch_calculate.return_value = {1: 55.0, 2: 35.0}

        _run_risk_calculation_pipeline(region_ids, 50.0, "2024-01-15T10:00:00")

        MockFloodEngine.return_value.get_latest_predictions.assert_called_once_with(region_ids)
        MockTrafficAnalyzer.return_value.analyze_traffic_impact.assert_called()
        MockAccessibility.return_value.evaluate_accessibility.assert_called()
        MockScoringEngine.return_value.batch_calculate.assert_called_once_with(region_ids)
        MockScoringEngine.return_value.save_risk_history.assert_called()

    @patch("uris_ai.ml.risk_scoring_engine.RiskScoringEngine", autospec=True)
    @patch("uris_ai.ml.service_accessibility.ServiceAccessibilityModule", autospec=True)
    @patch("uris_ai.ml.traffic_analyzer.TrafficAnalyzer", autospec=True)
    @patch("uris_ai.ml.flood_risk_engine.FloodRiskEngine", autospec=True)
    def test_traffic_analyzer_called_only_for_high_risk_regions(
        self,
        MockFloodEngine,
        MockTrafficAnalyzer,
        MockAccessibility,
        MockScoringEngine,
    ):
        """TrafficAnalyzer is only called for TINGGI/KRITIS regions."""
        from uris_ai.functions.risk_calculator import _run_risk_calculation_pipeline

        region_ids = [1, 2, 3]
        flood_preds = [
            _make_flood_prediction(1, 80.0, "KRITIS"),   # high risk
            _make_flood_prediction(2, 30.0, "SEDANG"),   # low risk
            _make_flood_prediction(3, 60.0, "TINGGI"),   # high risk
        ]

        MockFloodEngine.return_value.get_latest_predictions.return_value = flood_preds
        MockTrafficAnalyzer.return_value.analyze_traffic_impact.return_value = (
            _make_traffic_impact(1)
        )
        MockAccessibility.return_value.evaluate_accessibility.return_value = (
            _make_accessibility_report(1)
        )
        MockScoringEngine.return_value.batch_calculate.return_value = {
            1: 70.0, 2: 25.0, 3: 55.0
        }

        _run_risk_calculation_pipeline(region_ids, 50.0, "2024-01-15T10:00:00")

        # Should be called for regions 1 and 3 (KRITIS and TINGGI), not region 2
        assert MockTrafficAnalyzer.return_value.analyze_traffic_impact.call_count == 2

    @patch("uris_ai.ml.risk_scoring_engine.RiskScoringEngine", autospec=True)
    @patch("uris_ai.ml.service_accessibility.ServiceAccessibilityModule", autospec=True)
    @patch("uris_ai.ml.traffic_analyzer.TrafficAnalyzer", autospec=True)
    @patch("uris_ai.ml.flood_risk_engine.FloodRiskEngine", autospec=True)
    def test_save_risk_history_called_for_each_scored_region(
        self,
        MockFloodEngine,
        MockTrafficAnalyzer,
        MockAccessibility,
        MockScoringEngine,
    ):
        """save_risk_history is called once for each region that has a score."""
        from uris_ai.functions.risk_calculator import _run_risk_calculation_pipeline

        region_ids = [1, 2]
        flood_preds = [
            _make_flood_prediction(1, 60.0, "TINGGI"),
            _make_flood_prediction(2, 55.0, "TINGGI"),
        ]

        MockFloodEngine.return_value.get_latest_predictions.return_value = flood_preds
        MockTrafficAnalyzer.return_value.analyze_traffic_impact.return_value = (
            _make_traffic_impact(1)
        )
        MockAccessibility.return_value.evaluate_accessibility.return_value = (
            _make_accessibility_report(1)
        )
        MockScoringEngine.return_value.batch_calculate.return_value = {1: 55.0, 2: 50.0}

        _run_risk_calculation_pipeline(region_ids, 50.0, "2024-01-15T10:00:00")

        assert MockScoringEngine.return_value.save_risk_history.call_count == 2


# ---------------------------------------------------------------------------
# Tests for error handling in each pipeline step
# ---------------------------------------------------------------------------


class TestPipelineErrorHandling:
    """Tests for graceful error handling in each pipeline step."""

    @patch("uris_ai.ml.flood_risk_engine.FloodRiskEngine", autospec=True)
    def test_flood_engine_error_is_handled_gracefully(self, MockFloodEngine):
        """Pipeline handles FloodRiskEngine errors without crashing."""
        from uris_ai.functions.risk_calculator import _run_risk_calculation_pipeline

        MockFloodEngine.return_value.get_latest_predictions.side_effect = RuntimeError(
            "Model not loaded"
        )

        # Should NOT raise
        _run_risk_calculation_pipeline([1, 2], 50.0, "2024-01-15T10:00:00")

    @patch("uris_ai.ml.flood_risk_engine.FloodRiskEngine", autospec=True)
    def test_flood_engine_error_is_logged(self, MockFloodEngine):
        """FloodRiskEngine errors are logged as errors."""
        from uris_ai.functions.risk_calculator import _run_risk_calculation_pipeline

        MockFloodEngine.return_value.get_latest_predictions.side_effect = RuntimeError(
            "Model not loaded"
        )

        with patch("uris_ai.functions.risk_calculator.logger") as mock_logger:
            _run_risk_calculation_pipeline([1], 50.0, "2024-01-15T10:00:00")

        mock_logger.error.assert_called()

    @patch("uris_ai.ml.risk_scoring_engine.RiskScoringEngine", autospec=True)
    @patch("uris_ai.ml.service_accessibility.ServiceAccessibilityModule", autospec=True)
    @patch("uris_ai.ml.traffic_analyzer.TrafficAnalyzer", autospec=True)
    @patch("uris_ai.ml.flood_risk_engine.FloodRiskEngine", autospec=True)
    def test_traffic_analyzer_error_is_handled_gracefully(
        self,
        MockFloodEngine,
        MockTrafficAnalyzer,
        MockAccessibility,
        MockScoringEngine,
    ):
        """Pipeline continues when TrafficAnalyzer raises an exception."""
        from uris_ai.functions.risk_calculator import _run_risk_calculation_pipeline

        flood_preds = [_make_flood_prediction(1, 70.0, "TINGGI")]
        MockFloodEngine.return_value.get_latest_predictions.return_value = flood_preds
        MockTrafficAnalyzer.return_value.analyze_traffic_impact.side_effect = (
            RuntimeError("DB connection failed")
        )
        MockScoringEngine.return_value.batch_calculate.return_value = {1: 60.0}

        # Should NOT raise
        _run_risk_calculation_pipeline([1], 50.0, "2024-01-15T10:00:00")

    @patch("uris_ai.ml.risk_scoring_engine.RiskScoringEngine", autospec=True)
    @patch("uris_ai.ml.service_accessibility.ServiceAccessibilityModule", autospec=True)
    @patch("uris_ai.ml.traffic_analyzer.TrafficAnalyzer", autospec=True)
    @patch("uris_ai.ml.flood_risk_engine.FloodRiskEngine", autospec=True)
    def test_accessibility_error_is_handled_gracefully(
        self,
        MockFloodEngine,
        MockTrafficAnalyzer,
        MockAccessibility,
        MockScoringEngine,
    ):
        """Pipeline continues when ServiceAccessibilityModule raises an exception."""
        from uris_ai.functions.risk_calculator import _run_risk_calculation_pipeline

        flood_preds = [_make_flood_prediction(1, 70.0, "TINGGI")]
        MockFloodEngine.return_value.get_latest_predictions.return_value = flood_preds
        MockTrafficAnalyzer.return_value.analyze_traffic_impact.return_value = (
            _make_traffic_impact(1)
        )
        MockAccessibility.return_value.evaluate_accessibility.side_effect = (
            RuntimeError("Facility data unavailable")
        )
        MockScoringEngine.return_value.batch_calculate.return_value = {1: 60.0}

        # Should NOT raise
        _run_risk_calculation_pipeline([1], 50.0, "2024-01-15T10:00:00")

    @patch("uris_ai.ml.risk_scoring_engine.RiskScoringEngine", autospec=True)
    @patch("uris_ai.ml.service_accessibility.ServiceAccessibilityModule", autospec=True)
    @patch("uris_ai.ml.traffic_analyzer.TrafficAnalyzer", autospec=True)
    @patch("uris_ai.ml.flood_risk_engine.FloodRiskEngine", autospec=True)
    def test_scoring_engine_error_is_handled_gracefully(
        self,
        MockFloodEngine,
        MockTrafficAnalyzer,
        MockAccessibility,
        MockScoringEngine,
    ):
        """Pipeline handles RiskScoringEngine.batch_calculate errors without crashing."""
        from uris_ai.functions.risk_calculator import _run_risk_calculation_pipeline

        flood_preds = [_make_flood_prediction(1, 70.0, "TINGGI")]
        MockFloodEngine.return_value.get_latest_predictions.return_value = flood_preds
        MockTrafficAnalyzer.return_value.analyze_traffic_impact.return_value = (
            _make_traffic_impact(1)
        )
        MockAccessibility.return_value.evaluate_accessibility.return_value = (
            _make_accessibility_report(1)
        )
        MockScoringEngine.return_value.batch_calculate.side_effect = RuntimeError(
            "DB session not configured"
        )

        # Should NOT raise
        _run_risk_calculation_pipeline([1], 50.0, "2024-01-15T10:00:00")

    @patch("uris_ai.ml.risk_scoring_engine.RiskScoringEngine", autospec=True)
    @patch("uris_ai.ml.service_accessibility.ServiceAccessibilityModule", autospec=True)
    @patch("uris_ai.ml.traffic_analyzer.TrafficAnalyzer", autospec=True)
    @patch("uris_ai.ml.flood_risk_engine.FloodRiskEngine", autospec=True)
    def test_save_history_error_is_handled_gracefully(
        self,
        MockFloodEngine,
        MockTrafficAnalyzer,
        MockAccessibility,
        MockScoringEngine,
    ):
        """Pipeline handles save_risk_history errors without crashing."""
        from uris_ai.functions.risk_calculator import _run_risk_calculation_pipeline

        flood_preds = [_make_flood_prediction(1, 70.0, "TINGGI")]
        MockFloodEngine.return_value.get_latest_predictions.return_value = flood_preds
        MockTrafficAnalyzer.return_value.analyze_traffic_impact.return_value = (
            _make_traffic_impact(1)
        )
        MockAccessibility.return_value.evaluate_accessibility.return_value = (
            _make_accessibility_report(1)
        )
        MockScoringEngine.return_value.batch_calculate.return_value = {1: 60.0}
        MockScoringEngine.return_value.save_risk_history.side_effect = RuntimeError(
            "DB write failed"
        )

        # Should NOT raise
        _run_risk_calculation_pipeline([1], 50.0, "2024-01-15T10:00:00")


# ---------------------------------------------------------------------------
# Tests for function.json binding configuration
# ---------------------------------------------------------------------------


class TestFunctionJsonConfig:
    """Tests that function.json has the correct binding configuration."""

    def test_function_json_exists(self):
        """function.json exists in the risk_calculator directory."""
        assert FUNCTION_JSON_PATH.exists(), (
            f"function.json not found at {FUNCTION_JSON_PATH}"
        )

        with open(FUNCTION_JSON_PATH) as f:
            config = json.load(f)

        assert "bindings" in config

    def test_function_json_has_timer_trigger(self):
        """function.json defines a timerTrigger binding."""
        with open(FUNCTION_JSON_PATH) as f:
            config = json.load(f)

        bindings = config["bindings"]
        timer_bindings = [b for b in bindings if b.get("type") == "timerTrigger"]
        assert len(timer_bindings) == 1, "Expected exactly one timerTrigger binding"

    def test_function_json_timer_schedule_is_every_5_minutes(self):
        """Timer trigger schedule is set to run every 5 minutes (0 */5 * * * *)."""
        with open(FUNCTION_JSON_PATH) as f:
            config = json.load(f)

        timer_binding = next(
            b for b in config["bindings"] if b.get("type") == "timerTrigger"
        )
        assert timer_binding["schedule"] == "0 */5 * * * *", (
            f"Expected schedule '0 */5 * * * *', got '{timer_binding['schedule']}'"
        )

    def test_function_json_timer_binding_direction_is_in(self):
        """Timer trigger binding direction is 'in'."""
        with open(FUNCTION_JSON_PATH) as f:
            config = json.load(f)

        timer_binding = next(
            b for b in config["bindings"] if b.get("type") == "timerTrigger"
        )
        assert timer_binding["direction"] == "in"

    def test_function_json_script_file_is_init_py(self):
        """function.json scriptFile points to __init__.py."""
        with open(FUNCTION_JSON_PATH) as f:
            config = json.load(f)

        assert config.get("scriptFile") == "__init__.py"
