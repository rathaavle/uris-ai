# Monitoring and Logging Documentation

## Overview

This document describes the monitoring and logging implementation for URIS-AI, covering Azure Application Insights integration, structured logging, alerting rules, and health check endpoints.

**Requirements Implemented:**

- **7.3**: Structured logging with JSON format
- **8.4**: System uptime monitoring, Application Insights integration, alerting rules
- **9.4**: Health check endpoints for failover and readiness

## Table of Contents

1. [Azure Application Insights](#azure-application-insights)
2. [Structured Logging](#structured-logging)
3. [Alerting Rules](#alerting-rules)
4. [Health Check Endpoints](#health-check-endpoints)
5. [Configuration](#configuration)
6. [Usage Examples](#usage-examples)

---

## Azure Application Insights

### Overview

Application Insights provides comprehensive monitoring, telemetry, and performance tracking for both FastAPI and Streamlit applications.

### Features

- **Distributed Tracing**: Track requests across services
- **Custom Metrics**: Track business and performance metrics
- **Custom Events**: Track user actions and system events
- **Exception Tracking**: Automatic exception logging
- **Performance Monitoring**: Request duration, response times

### Implementation

Located in `src/uris_ai/utils/monitoring.py`:

```python
from uris_ai.utils.monitoring import app_insights

# Track a request
app_insights.track_request(
    name="GET /regions/{id}/risk",
    duration_ms=150.5,
    success=True,
    response_code=200,
    properties={"region_id": 123}
)

# Track a custom metric
app_insights.track_metric(
    "prediction_accuracy",
    85.5,
    properties={"model_version": "1.0.0"}
)

# Track an event
app_insights.track_event(
    "user_login",
    properties={"username": "admin", "role": "government"}
)

# Track an exception
try:
    # Some operation
    pass
except Exception as exc:
    app_insights.track_exception(exc, properties={"context": "data_ingestion"})
```

### Automatic Integration

Application Insights is automatically integrated with:

1. **FastAPI**: Via `RequestLoggingMiddleware` in `src/uris_ai/api/middleware.py`
   - Tracks all HTTP requests
   - Records duration, status code, success/failure
   - Tracks error rates

2. **Streamlit**: Via dashboard initialization in `src/uris_ai/dashboard/app.py`
   - Tracks page views
   - Records user interactions
   - Monitors dashboard performance

### Configuration

Set the following environment variables:

```bash
ENABLE_MONITORING=true
APPINSIGHTS_CONNECTION_STRING="InstrumentationKey=your-key;IngestionEndpoint=https://..."
```

---

## Structured Logging

### Overview

Structured logging provides JSON-formatted logs with consistent structure, making them easy to parse, search, and analyze in Azure Log Analytics.

### Log Structure

All logs follow this format:

```json
{
  "timestamp": "2024-01-15T10:30:00Z",
  "level": "ERROR",
  "component": "Flood_Risk_Engine",
  "message": "Failed to generate prediction",
  "context": {
    "region_id": 123,
    "error_type": "ModelPredictionError",
    "stack_trace": "..."
  },
  "request_id": "unique-request-id"
}
```

### Log Levels

- **DEBUG**: Detailed information for debugging (disabled in production)
- **INFO**: General informational messages
- **WARNING**: Warning messages (data staleness, fallback to cached data)
- **ERROR**: Error messages (API failures, validation errors)
- **CRITICAL**: Critical errors (system failures, data corruption)

### Implementation

Located in `src/uris_ai/utils/logging_config.py`:

```python
from uris_ai.utils.logging_config import setup_logging, get_logger

# Setup logging (call once at application startup)
setup_logging()

# Get a logger for your component
logger = get_logger(__name__)

# Log messages
logger.info("Processing region data", extra={"region_id": 123})
logger.warning("Data is stale", extra={"last_update": "2024-01-15T10:00:00Z"})
logger.error("Failed to fetch weather data", extra={"error": "timeout"})
```

### Log Retention

- **Application logs**: 90 days
- **Error logs**: 1 year
- **Audit logs**: 2 years

### Console vs Production Logging

- **Development**: Human-readable colored output
- **Production**: JSON-formatted logs for Azure Log Analytics

---

## Alerting Rules

### Overview

Alerting rules monitor system health and trigger alerts when thresholds are exceeded. Alerts are sent through the AlertManager and tracked in Application Insights.

### Alert Types

#### Critical Alerts

1. **System Downtime**
   - Threshold: Any downtime
   - Window: 1 minute
   - Action: Immediate notification

2. **Database Connection Failure**
   - Threshold: 3 consecutive failures
   - Window: 5 minutes
   - Action: Critical alert to DevOps

3. **ML Model Failure**
   - Threshold: 5 consecutive prediction failures
   - Window: 10 minutes
   - Action: Critical alert to ML team

4. **Security Breach**
   - Threshold: Any security breach
   - Window: 1 minute
   - Action: Immediate critical alert

#### Warning Alerts

1. **High Error Rate**
   - Threshold: >5% error rate
   - Window: 5 minutes
   - Action: Warning notification

2. **Slow Response Time**
   - Threshold: >5 seconds average
   - Window: 5 minutes
   - Action: Performance warning

3. **High Resource Utilization**
   - Threshold: >80% CPU or memory
   - Window: 10 minutes
   - Action: Scaling recommendation

4. **Data Staleness**
   - Threshold: >10 minutes old
   - Window: 1 minute
   - Action: Data refresh warning

### Implementation

Located in `src/uris_ai/utils/alerting_rules.py`:

```python
from uris_ai.utils.alerting_rules import alerting_engine

# Check database connection health
alerting_engine.check_database_connection(failure_count=5)

# Check error rate
alerting_engine.check_error_rate(error_count=10, total_requests=100)

# Check response time
alerting_engine.check_response_time(avg_response_time_ms=6000.0)

# Check data staleness
from datetime import datetime, timedelta, timezone
stale_time = datetime.now(timezone.utc) - timedelta(minutes=15)
alerting_engine.check_data_staleness(last_update=stale_time)

# Report security breach
alerting_engine.check_security_breach(
    breach_type="unauthorized_access",
    details={"ip": "192.168.1.1", "endpoint": "/admin"}
)
```

### Alert Suppression

Duplicate alerts are suppressed within a 5-minute window to prevent alert spam.

---

## Health Check Endpoints

### Overview

Health check endpoints provide standardized ways to monitor system health, readiness, and liveness for orchestration platforms like Kubernetes and Azure App Service.

### Endpoints

#### 1. Basic Health Check

**Endpoint**: `GET /health`

**Purpose**: Verify the application is running

**Response**:

```json
{
  "status": "healthy",
  "version": "0.1.0",
  "timestamp": "2024-01-15T10:30:00Z"
}
```

**Status Codes**:

- `200 OK`: Application is running

---

#### 2. Readiness Check

**Endpoint**: `GET /health/ready`

**Purpose**: Verify the application is ready to handle requests (all dependencies are available)

**Response**:

```json
{
  "status": "ready",
  "checks": {
    "database": "ok",
    "cache": "ok",
    "monitoring": "ok"
  },
  "timestamp": "2024-01-15T10:30:00Z"
}
```

**Status Values**:

- `ready`: All critical services are available
- `not_ready`: One or more critical services are unavailable

**Check Values**:

- `ok`: Service is available and healthy
- `error`: Service is unavailable (critical)
- `unavailable`: Service is unavailable (non-critical)
- `disabled`: Service is disabled in configuration

**Status Codes**:

- `200 OK`: Always returns 200 (check the `status` field for actual readiness)

**Use Cases**:

- Kubernetes readiness probes
- Load balancer health checks
- Deployment verification

---

#### 3. Liveness Check

**Endpoint**: `GET /health/live`

**Purpose**: Verify the application process is alive and responsive

**Response**:

```json
{
  "status": "alive",
  "timestamp": "2024-01-15T10:30:00Z"
}
```

**Status Codes**:

- `200 OK`: Process is alive

**Use Cases**:

- Kubernetes liveness probes
- Process monitoring
- Automatic restart triggers

---

## Configuration

### Environment Variables

```bash
# Application Configuration
APP_ENV=production
LOG_LEVEL=INFO
DEBUG=false

# Monitoring
ENABLE_MONITORING=true
APPINSIGHTS_INSTRUMENTATION_KEY=your-instrumentation-key
APPINSIGHTS_CONNECTION_STRING=InstrumentationKey=your-key;IngestionEndpoint=https://...

# Azure Configuration
AZURE_SUBSCRIPTION_ID=your-subscription-id
AZURE_TENANT_ID=your-tenant-id
AZURE_RESOURCE_GROUP=uris-ai-rg
```

### Logging Configuration

Logging is configured in `src/uris_ai/utils/logging_config.py`:

- **Log Level**: Set via `LOG_LEVEL` environment variable (DEBUG, INFO, WARNING, ERROR, CRITICAL)
- **Format**: JSON in production, colored console in development
- **Output**: Console (stdout) and file (production only)

### Monitoring Configuration

Monitoring is configured in `src/uris_ai/utils/monitoring.py`:

- **Enabled**: Set via `ENABLE_MONITORING` environment variable
- **Connection String**: Set via `APPINSIGHTS_CONNECTION_STRING`
- **Sampling**: 100% of requests (configurable)

---

## Usage Examples

### Example 1: Logging in a Component

```python
import logging
from uris_ai.utils.logging_config import get_logger

logger = get_logger(__name__)

def process_region_data(region_id: int):
    logger.info(
        "Processing region data",
        extra={"region_id": region_id}
    )

    try:
        # Process data
        result = perform_calculation(region_id)

        logger.info(
            "Region data processed successfully",
            extra={
                "region_id": region_id,
                "result": result
            }
        )
        return result

    except Exception as exc:
        logger.error(
            "Failed to process region data",
            exc_info=True,
            extra={
                "region_id": region_id,
                "error_type": type(exc).__name__
            }
        )
        raise
```

### Example 2: Tracking Custom Metrics

```python
from uris_ai.utils.monitoring import app_insights

def predict_flood_risk(region_id: int):
    # Make prediction
    prediction = model.predict(features)
    accuracy = calculate_accuracy(prediction, actual)

    # Track prediction accuracy
    app_insights.track_prediction_accuracy(accuracy)

    # Track custom metric
    app_insights.track_metric(
        "flood_risk_prediction",
        prediction.risk_score,
        properties={
            "region_id": region_id,
            "model_version": "1.0.0"
        }
    )

    return prediction
```

### Example 3: Monitoring Active Users

```python
from uris_ai.utils.monitoring import app_insights

def track_dashboard_usage():
    # Count active users
    active_users = count_active_sessions()

    # Track in Application Insights
    app_insights.track_active_users(active_users)
```

### Example 4: Alerting on Errors

```python
from uris_ai.utils.alerting_rules import alerting_engine

def monitor_system_health():
    # Check database health
    db_failures = get_database_failure_count()
    alerting_engine.check_database_connection(db_failures)

    # Check error rate
    error_count = get_error_count()
    total_requests = get_total_requests()
    alerting_engine.check_error_rate(error_count, total_requests)

    # Check response time
    avg_response_time = get_average_response_time()
    alerting_engine.check_response_time(avg_response_time)
```

---

## Testing

Comprehensive tests are available in `tests/test_monitoring_logging.py`:

```bash
# Run monitoring and logging tests
python -m pytest tests/test_monitoring_logging.py -v

# Run with coverage
python -m pytest tests/test_monitoring_logging.py --cov=src/uris_ai/utils
```

Test coverage includes:

- Structured logging format validation
- Application Insights tracking
- Alerting rules and thresholds
- Health check endpoints
- Alert suppression logic

---

## Troubleshooting

### Application Insights Not Working

1. Check that `ENABLE_MONITORING=true` is set
2. Verify `APPINSIGHTS_CONNECTION_STRING` is correctly configured
3. Check logs for Application Insights initialization errors
4. Ensure network connectivity to Azure

### Logs Not Appearing in Azure

1. Verify Azure Log Handler is configured (check startup logs)
2. Check Application Insights connection string
3. Verify log level is appropriate (INFO or higher)
4. Check Azure portal for ingestion delays (can take 1-2 minutes)

### Alerts Not Triggering

1. Check that alerting rules are initialized (check startup logs)
2. Verify thresholds are being exceeded
3. Check for alert suppression (5-minute window)
4. Review alert history: `alerting_engine.get_alert_history()`

### Health Checks Failing

1. Check database connectivity
2. Verify Redis cache is accessible
3. Review application logs for errors
4. Test endpoints manually: `curl http://localhost:8000/health/ready`

---

## Best Practices

1. **Always use structured logging** with extra fields for context
2. **Track important business metrics** in Application Insights
3. **Set appropriate log levels** (avoid DEBUG in production)
4. **Monitor alert history** to tune thresholds
5. **Use health checks** for deployment verification
6. **Review Application Insights dashboards** regularly
7. **Set up Azure Monitor alerts** for critical conditions
8. **Test monitoring** in staging before production deployment

---

## References

- [Azure Application Insights Documentation](https://docs.microsoft.com/en-us/azure/azure-monitor/app/app-insights-overview)
- [OpenCensus Python](https://github.com/census-instrumentation/opencensus-python)
- [Python Logging Documentation](https://docs.python.org/3/library/logging.html)
- [Health Check Pattern](https://microservices.io/patterns/observability/health-check-api.html)
