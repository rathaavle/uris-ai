"""
Azure Function: Scheduled Risk Calculation

Timer trigger that runs every 5 minutes to calculate Urban Risk Scores
for all regions when risk conditions are active.

Risk conditions are considered active when any region has a flood risk
score above the configurable threshold (default: 50.0, set via
RISK_ACTIVE_THRESHOLD env var).

Requirements: 3.4, 4.3, 7.3
"""

import logging
import os
from datetime import datetime, timezone
from typing import List

import azure.functions as func

logger = logging.getLogger(__name__)

# Default threshold above which risk conditions are considered active
DEFAULT_RISK_ACTIVE_THRESHOLD = 50.0

# Default region IDs for Jakarta and West Java
DEFAULT_REGION_IDS: List[int] = list(range(1, 11))  # Regions 1-10 as default


def _get_risk_active_threshold() -> float:
    """
    Get the risk-active threshold from the environment.

    Reads from RISK_ACTIVE_THRESHOLD environment variable.
    Falls back to DEFAULT_RISK_ACTIVE_THRESHOLD if not set or invalid.

    Returns:
        Threshold value as a float
    """
    raw = os.environ.get("RISK_ACTIVE_THRESHOLD", "")
    if raw:
        try:
            return float(raw)
        except ValueError:
            logger.warning(
                "Invalid RISK_ACTIVE_THRESHOLD value '%s', using default %.1f",
                raw,
                DEFAULT_RISK_ACTIVE_THRESHOLD,
            )
    return DEFAULT_RISK_ACTIVE_THRESHOLD


def _get_region_ids() -> List[int]:
    """
    Get the list of region IDs to process.

    Reads from RISK_REGION_IDS environment variable (comma-separated integers).
    Falls back to DEFAULT_REGION_IDS if not set or invalid.

    Returns:
        List of region IDs
    """
    region_ids_env = os.environ.get("RISK_REGION_IDS", "")
    if region_ids_env:
        try:
            return [int(rid.strip()) for rid in region_ids_env.split(",") if rid.strip()]
        except ValueError:
            logger.warning(
                "Invalid RISK_REGION_IDS value '%s', using defaults", region_ids_env
            )
    return DEFAULT_REGION_IDS


def main(mytimer: func.TimerRequest) -> None:
    """
    Azure Function entry point for scheduled risk calculation.

    Triggered every 5 minutes via timer trigger (NCRONTAB: 0 */5 * * * *).
    Checks whether risk conditions are active and, if so, runs the full
    risk calculation pipeline for all configured regions.

    Args:
        mytimer: Azure Functions timer trigger object
    """
    utc_timestamp = datetime.now(timezone.utc).isoformat()

    if mytimer.past_due:
        logger.warning(
            "Risk calculator timer is past due. Execution time: %s", utc_timestamp
        )

    logger.info(
        "Risk calculator triggered at %s",
        utc_timestamp,
        extra={
            "function_name": "risk_calculator",
            "trigger_time": utc_timestamp,
            "past_due": mytimer.past_due,
        },
    )

    region_ids = _get_region_ids()
    threshold = _get_risk_active_threshold()

    try:
        _run_risk_calculation_pipeline(region_ids, threshold, utc_timestamp)
    except Exception as exc:
        # Catch all exceptions to prevent the function host from crashing.
        # The error is logged with full context for debugging.
        logger.error(
            "Unhandled error in risk_calculator function: %s",
            exc,
            exc_info=True,
            extra={
                "function_name": "risk_calculator",
                "trigger_time": utc_timestamp,
                "region_ids": region_ids,
            },
        )


def _is_risk_conditions_active(
    flood_predictions: list,
    threshold: float,
) -> bool:
    """
    Check whether risk conditions are currently active.

    Risk conditions are active when at least one region has a flood risk
    score above the given threshold.

    Args:
        flood_predictions: List of FloodRiskPrediction objects
        threshold: Score threshold above which risk is considered active

    Returns:
        True if any region exceeds the threshold, False otherwise
    """
    for prediction in flood_predictions:
        if prediction.risk_score > threshold:
            return True
    return False


def _run_risk_calculation_pipeline(
    region_ids: List[int],
    threshold: float,
    trigger_time: str,
) -> None:
    """
    Run the full risk calculation pipeline if risk conditions are active.

    Imports are deferred inside the function so that the Azure Functions
    host can load the module even when optional dependencies (e.g. the
    settings object that requires a .env file) are not fully configured.

    Pipeline steps:
    1. Get flood risk predictions for all regions (FloodRiskEngine)
    2. Check if risk conditions are active; return early if not
    3. Get traffic impact for high-risk regions (TrafficAnalyzer)
    4. Evaluate service accessibility for affected regions (ServiceAccessibilityModule)
    5. Calculate Urban Risk Score for all regions (RiskScoringEngine)
    6. Save risk history (RiskScoringEngine.save_risk_history)

    Args:
        region_ids: List of region IDs to process
        threshold: Risk-active threshold
        trigger_time: ISO-format UTC timestamp of the trigger (for logging)
    """
    # Deferred imports to avoid import-time side effects in the Functions host
    from uris_ai.ml.flood_risk_engine import FloodRiskEngine, RiskCategory
    from uris_ai.ml.traffic_analyzer import TrafficAnalyzer
    from uris_ai.ml.service_accessibility import ServiceAccessibilityModule
    from uris_ai.ml.risk_scoring_engine import RiskScoringEngine
    from uris_ai.utils import AlertLevel, AlertManager

    alert_manager = AlertManager(source="risk_calculator")
    start_time = datetime.now(timezone.utc)

    # --- Step 1: Flood risk predictions ---
    flood_engine = FloodRiskEngine()
    try:
        flood_predictions = flood_engine.get_latest_predictions(region_ids)
    except Exception as exc:
        alert_manager.send_alert(
            level=AlertLevel.ERROR,
            message=f"FloodRiskEngine.get_latest_predictions failed: {exc}",
            details={
                "function_name": "risk_calculator",
                "trigger_time": trigger_time,
                "step": "flood_risk",
                "error_type": type(exc).__name__,
                "error_message": str(exc),
            },
        )
        logger.error(
            "FloodRiskEngine.get_latest_predictions failed: %s",
            exc,
            exc_info=True,
            extra={
                "function_name": "risk_calculator",
                "trigger_time": trigger_time,
                "step": "flood_risk",
            },
        )
        return

    # --- Step 2: Check if risk conditions are active ---
    if not _is_risk_conditions_active(flood_predictions, threshold):
        logger.info(
            "Risk conditions not active (no region exceeds threshold %.1f). "
            "Skipping full pipeline.",
            threshold,
            extra={
                "function_name": "risk_calculator",
                "trigger_time": trigger_time,
                "threshold": threshold,
                "regions_checked": len(region_ids),
            },
        )
        return

    logger.info(
        "Risk conditions active. Running full pipeline for %d regions.",
        len(region_ids),
        extra={
            "function_name": "risk_calculator",
            "trigger_time": trigger_time,
            "regions_count": len(region_ids),
        },
    )

    # Build a map of region_id -> flood prediction for easy lookup
    flood_map = {p.region_id: p for p in flood_predictions}

    # Identify high-risk regions (TINGGI or KRITIS)
    high_risk_region_ids = [
        p.region_id
        for p in flood_predictions
        if p.category in (RiskCategory.TINGGI, RiskCategory.KRITIS)
    ]

    # --- Step 3: Traffic impact for high-risk regions ---
    traffic_analyzer = TrafficAnalyzer(db_session=None)
    traffic_impacts = {}
    for region_id in high_risk_region_ids:
        try:
            impact = traffic_analyzer.analyze_traffic_impact(
                region_id, flood_map[region_id]
            )
            traffic_impacts[region_id] = impact
        except Exception as exc:
            alert_manager.send_alert(
                level=AlertLevel.ERROR,
                message=f"TrafficAnalyzer.analyze_traffic_impact failed for region {region_id}: {exc}",
                details={
                    "function_name": "risk_calculator",
                    "trigger_time": trigger_time,
                    "step": "traffic_impact",
                    "region_id": region_id,
                    "error_type": type(exc).__name__,
                    "error_message": str(exc),
                },
            )
            logger.error(
                "TrafficAnalyzer.analyze_traffic_impact failed for region %d: %s",
                region_id,
                exc,
                exc_info=True,
                extra={
                    "function_name": "risk_calculator",
                    "trigger_time": trigger_time,
                    "step": "traffic_impact",
                    "region_id": region_id,
                },
            )

    # --- Step 4: Service accessibility for affected regions ---
    accessibility_module = ServiceAccessibilityModule(db_session=None)
    accessibility_reports = {}
    for region_id, traffic_impact in traffic_impacts.items():
        try:
            report = accessibility_module.evaluate_accessibility(
                region_id, traffic_impact
            )
            accessibility_reports[region_id] = report
        except Exception as exc:
            alert_manager.send_alert(
                level=AlertLevel.ERROR,
                message=(
                    f"ServiceAccessibilityModule.evaluate_accessibility failed "
                    f"for region {region_id}: {exc}"
                ),
                details={
                    "function_name": "risk_calculator",
                    "trigger_time": trigger_time,
                    "step": "service_accessibility",
                    "region_id": region_id,
                    "error_type": type(exc).__name__,
                    "error_message": str(exc),
                },
            )
            logger.error(
                "ServiceAccessibilityModule.evaluate_accessibility failed "
                "for region %d: %s",
                region_id,
                exc,
                exc_info=True,
                extra={
                    "function_name": "risk_calculator",
                    "trigger_time": trigger_time,
                    "step": "service_accessibility",
                    "region_id": region_id,
                },
            )

    # --- Step 5: Calculate Urban Risk Score for all regions ---
    scoring_engine = RiskScoringEngine(db_session=None)
    risk_scores = {}
    try:
        risk_scores = scoring_engine.batch_calculate(region_ids)
    except Exception as exc:
        alert_manager.send_alert(
            level=AlertLevel.ERROR,
            message=f"RiskScoringEngine.batch_calculate failed: {exc}",
            details={
                "function_name": "risk_calculator",
                "trigger_time": trigger_time,
                "step": "risk_scoring",
                "error_type": type(exc).__name__,
                "error_message": str(exc),
            },
        )
        logger.error(
            "RiskScoringEngine.batch_calculate failed: %s",
            exc,
            exc_info=True,
            extra={
                "function_name": "risk_calculator",
                "trigger_time": trigger_time,
                "step": "risk_scoring",
            },
        )

    # --- Step 6: Save risk history ---
    try:
        for region_id, score in risk_scores.items():
            flood_pred = flood_map.get(region_id)
            flood_risk_val = flood_pred.risk_score if flood_pred else 0.0

            traffic_impact_val = 0.0
            if region_id in traffic_impacts:
                # Use a simple proxy: fraction of affected roads as impact score
                impact = traffic_impacts[region_id]
                traffic_impact_val = min(100.0, len(impact.affected_roads) * 10.0)

            service_access_val = 0.0
            if region_id in accessibility_reports:
                report = accessibility_reports[region_id]
                # Use a simple proxy: fraction of affected facilities as score
                service_access_val = min(
                    100.0, len(report.affected_facilities) * 10.0
                )

            scoring_engine.save_risk_history(
                region_id=region_id,
                score=score,
                flood_risk=flood_risk_val,
                traffic_impact=traffic_impact_val,
                service_access=service_access_val,
            )
    except Exception as exc:
        alert_manager.send_alert(
            level=AlertLevel.ERROR,
            message=f"RiskScoringEngine.save_risk_history failed: {exc}",
            details={
                "function_name": "risk_calculator",
                "trigger_time": trigger_time,
                "step": "save_history",
                "error_type": type(exc).__name__,
                "error_message": str(exc),
            },
        )
        logger.error(
            "RiskScoringEngine.save_risk_history failed: %s",
            exc,
            exc_info=True,
            extra={
                "function_name": "risk_calculator",
                "trigger_time": trigger_time,
                "step": "save_history",
            },
        )

    duration_seconds = (datetime.now(timezone.utc) - start_time).total_seconds()

    logger.info(
        "Risk calculation pipeline completed: %d regions processed, "
        "%d scores calculated, duration=%.2fs",
        len(region_ids),
        len(risk_scores),
        duration_seconds,
        extra={
            "function_name": "risk_calculator",
            "trigger_time": trigger_time,
            "regions_processed": len(region_ids),
            "scores_calculated": len(risk_scores),
            "high_risk_regions": len(high_risk_region_ids),
            "duration_seconds": duration_seconds,
        },
    )
