"""
Alerting rules and configuration for URIS-AI.

Defines alert conditions for critical errors, performance degradation,
and security events. Integrates with Azure Application Insights and
the AlertManager.

Requirements: 8.4
"""

import logging
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from enum import Enum
from typing import Any, Dict, List, Optional

from uris_ai.utils.alerting import AlertLevel, AlertManager
from uris_ai.utils.monitoring import app_insights

logger = logging.getLogger(__name__)


class AlertType(Enum):
    """Types of alerts in the system."""

    # Critical Alerts
    SYSTEM_DOWNTIME = "system_downtime"
    DATABASE_CONNECTION_FAILURE = "database_connection_failure"
    ML_MODEL_FAILURE = "ml_model_failure"
    SECURITY_BREACH = "security_breach"

    # Warning Alerts
    HIGH_ERROR_RATE = "high_error_rate"
    SLOW_RESPONSE_TIME = "slow_response_time"
    HIGH_RESOURCE_UTILIZATION = "high_resource_utilization"
    DATA_STALENESS = "data_staleness"


@dataclass
class AlertRule:
    """
    Defines a rule for triggering alerts.

    Attributes:
        alert_type: Type of alert
        threshold: Threshold value that triggers the alert
        window_minutes: Time window for evaluation (in minutes)
        level: Alert severity level
        description: Human-readable description of the alert condition
    """

    alert_type: AlertType
    threshold: float
    window_minutes: int
    level: AlertLevel
    description: str


class AlertingRulesEngine:
    """
    Manages alerting rules and evaluates conditions.

    Monitors system metrics and triggers alerts when thresholds are exceeded.
    """

    def __init__(self) -> None:
        """Initialize the alerting rules engine."""
        self.alert_manager = AlertManager("alerting_rules_engine")
        self.rules = self._initialize_rules()
        self._alert_history: List[Dict[str, Any]] = []
        logger.info("Alerting rules engine initialized")

    def _initialize_rules(self) -> Dict[AlertType, AlertRule]:
        """
        Initialize alerting rules based on design specifications.

        Returns:
            Dictionary mapping alert types to their rules
        """
        return {
            # Critical Alerts
            AlertType.SYSTEM_DOWNTIME: AlertRule(
                alert_type=AlertType.SYSTEM_DOWNTIME,
                threshold=0.0,  # Any downtime triggers alert
                window_minutes=1,
                level=AlertLevel.CRITICAL,
                description="System is down or unreachable",
            ),
            AlertType.DATABASE_CONNECTION_FAILURE: AlertRule(
                alert_type=AlertType.DATABASE_CONNECTION_FAILURE,
                threshold=3.0,  # 3 consecutive failures
                window_minutes=5,
                level=AlertLevel.CRITICAL,
                description="Database connection failures detected",
            ),
            AlertType.ML_MODEL_FAILURE: AlertRule(
                alert_type=AlertType.ML_MODEL_FAILURE,
                threshold=5.0,  # 5 consecutive prediction failures
                window_minutes=10,
                level=AlertLevel.CRITICAL,
                description="ML model prediction failures detected",
            ),
            AlertType.SECURITY_BREACH: AlertRule(
                alert_type=AlertType.SECURITY_BREACH,
                threshold=1.0,  # Any security breach
                window_minutes=1,
                level=AlertLevel.CRITICAL,
                description="Security breach detected",
            ),
            # Warning Alerts
            AlertType.HIGH_ERROR_RATE: AlertRule(
                alert_type=AlertType.HIGH_ERROR_RATE,
                threshold=5.0,  # >5% error rate
                window_minutes=5,
                level=AlertLevel.WARNING,
                description="Error rate exceeds 5%",
            ),
            AlertType.SLOW_RESPONSE_TIME: AlertRule(
                alert_type=AlertType.SLOW_RESPONSE_TIME,
                threshold=5000.0,  # >5 seconds
                window_minutes=5,
                level=AlertLevel.WARNING,
                description="Response time exceeds 5 seconds",
            ),
            AlertType.HIGH_RESOURCE_UTILIZATION: AlertRule(
                alert_type=AlertType.HIGH_RESOURCE_UTILIZATION,
                threshold=80.0,  # >80% utilization
                window_minutes=10,
                level=AlertLevel.WARNING,
                description="Resource utilization exceeds 80%",
            ),
            AlertType.DATA_STALENESS: AlertRule(
                alert_type=AlertType.DATA_STALENESS,
                threshold=10.0,  # >10 minutes stale
                window_minutes=1,
                level=AlertLevel.WARNING,
                description="Data is stale (>10 minutes old)",
            ),
        }

    def check_system_downtime(self) -> None:
        """
        Check for system downtime.

        This should be called by external monitoring (e.g., Azure Monitor).
        """
        rule = self.rules[AlertType.SYSTEM_DOWNTIME]
        self._trigger_alert(
            rule,
            details={
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "message": "System health check failed",
            },
        )

    def check_database_connection(self, failure_count: int) -> None:
        """
        Check database connection health.

        Args:
            failure_count: Number of consecutive connection failures
        """
        rule = self.rules[AlertType.DATABASE_CONNECTION_FAILURE]
        if failure_count >= rule.threshold:
            self._trigger_alert(
                rule,
                details={
                    "failure_count": failure_count,
                    "threshold": rule.threshold,
                },
            )

    def check_ml_model_failures(self, failure_count: int, total_requests: int) -> None:
        """
        Check ML model prediction failures.

        Args:
            failure_count: Number of prediction failures
            total_requests: Total number of prediction requests
        """
        rule = self.rules[AlertType.ML_MODEL_FAILURE]
        if failure_count >= rule.threshold:
            failure_rate = (failure_count / total_requests * 100) if total_requests > 0 else 0
            self._trigger_alert(
                rule,
                details={
                    "failure_count": failure_count,
                    "total_requests": total_requests,
                    "failure_rate": f"{failure_rate:.2f}%",
                },
            )

    def check_security_breach(
        self, breach_type: str, details: Optional[Dict[str, Any]] = None
    ) -> None:
        """
        Report a security breach.

        Args:
            breach_type: Type of security breach
            details: Additional details about the breach
        """
        rule = self.rules[AlertType.SECURITY_BREACH]
        self._trigger_alert(
            rule,
            details={
                "breach_type": breach_type,
                **(details or {}),
            },
        )

    def check_error_rate(self, error_count: int, total_requests: int) -> None:
        """
        Check error rate.

        Args:
            error_count: Number of errors
            total_requests: Total number of requests
        """
        if total_requests == 0:
            return

        error_rate = (error_count / total_requests) * 100
        rule = self.rules[AlertType.HIGH_ERROR_RATE]

        if error_rate > rule.threshold:
            self._trigger_alert(
                rule,
                details={
                    "error_rate": f"{error_rate:.2f}%",
                    "error_count": error_count,
                    "total_requests": total_requests,
                    "threshold": f"{rule.threshold}%",
                },
            )

    def check_response_time(self, avg_response_time_ms: float) -> None:
        """
        Check average response time.

        Args:
            avg_response_time_ms: Average response time in milliseconds
        """
        rule = self.rules[AlertType.SLOW_RESPONSE_TIME]

        if avg_response_time_ms > rule.threshold:
            self._trigger_alert(
                rule,
                details={
                    "avg_response_time_ms": avg_response_time_ms,
                    "threshold_ms": rule.threshold,
                },
            )

    def check_resource_utilization(
        self, cpu_percent: float, memory_percent: float
    ) -> None:
        """
        Check resource utilization.

        Args:
            cpu_percent: CPU utilization percentage
            memory_percent: Memory utilization percentage
        """
        rule = self.rules[AlertType.HIGH_RESOURCE_UTILIZATION]

        if cpu_percent > rule.threshold or memory_percent > rule.threshold:
            self._trigger_alert(
                rule,
                details={
                    "cpu_percent": cpu_percent,
                    "memory_percent": memory_percent,
                    "threshold": rule.threshold,
                },
            )

    def check_data_staleness(self, last_update: datetime) -> None:
        """
        Check if data is stale.

        Args:
            last_update: Timestamp of last data update
        """
        rule = self.rules[AlertType.DATA_STALENESS]
        now = datetime.now(timezone.utc)
        
        # Ensure last_update is timezone-aware
        if last_update.tzinfo is None:
            last_update = last_update.replace(tzinfo=timezone.utc)
        
        staleness_minutes = (now - last_update).total_seconds() / 60

        if staleness_minutes > rule.threshold:
            self._trigger_alert(
                rule,
                details={
                    "last_update": last_update.isoformat(),
                    "staleness_minutes": staleness_minutes,
                    "threshold_minutes": rule.threshold,
                },
            )

    def _trigger_alert(
        self, rule: AlertRule, details: Optional[Dict[str, Any]] = None
    ) -> None:
        """
        Trigger an alert based on a rule.

        Args:
            rule: The alert rule that was triggered
            details: Additional details about the alert
        """
        # Check if we've already sent this alert recently (avoid spam)
        if self._is_duplicate_alert(rule.alert_type):
            logger.debug(f"Suppressing duplicate alert: {rule.alert_type.value}")
            return

        # Send alert through AlertManager
        alert = self.alert_manager.send_alert(
            level=rule.level,
            message=f"{rule.description}",
            details={
                "alert_type": rule.alert_type.value,
                "threshold": rule.threshold,
                "window_minutes": rule.window_minutes,
                **(details or {}),
            },
        )

        # Track alert in Application Insights
        app_insights.track_event(
            f"alert_{rule.alert_type.value}",
            properties={
                "level": rule.level.value,
                "description": rule.description,
                **(details or {}),
            },
        )

        # Record alert in history
        self._alert_history.append(
            {
                "alert_type": rule.alert_type.value,
                "level": rule.level.value,
                "timestamp": alert.timestamp,
                "details": details or {},
            }
        )

        # Trim history to last 100 alerts
        if len(self._alert_history) > 100:
            self._alert_history = self._alert_history[-100:]

    def _is_duplicate_alert(
        self, alert_type: AlertType, window_minutes: int = 5
    ) -> bool:
        """
        Check if an alert of the same type was sent recently.

        Args:
            alert_type: Type of alert to check
            window_minutes: Time window to check for duplicates

        Returns:
            True if a duplicate alert was found, False otherwise
        """
        cutoff = datetime.now(timezone.utc) - timedelta(minutes=window_minutes)

        for alert in reversed(self._alert_history):
            if alert["alert_type"] == alert_type.value:
                alert_time = alert["timestamp"]
                if alert_time > cutoff:
                    return True
                break

        return False

    def get_alert_history(self, limit: int = 50) -> List[Dict[str, Any]]:
        """
        Get recent alert history.

        Args:
            limit: Maximum number of alerts to return

        Returns:
            List of recent alerts
        """
        return self._alert_history[-limit:]


# Global alerting rules engine instance
alerting_engine = AlertingRulesEngine()
