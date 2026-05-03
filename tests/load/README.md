# URIS-AI Load Testing Guide

This directory contains load testing infrastructure for URIS-AI using [Locust](https://locust.io/).

## Overview

Load tests verify the following performance requirements:

- **Requirement 8.1**: Response time ≤5 seconds for 95% of requests under normal load
- **Requirement 8.2**: System should handle 500 concurrent users
- **Requirement 8.3**: Auto-scaling should activate when concurrent users exceed 500

## Prerequisites

### Install Locust

```bash
pip install locust
```

Or install from the project requirements:

```bash
pip install -r requirements.txt
```

### Test User Setup

Before running load tests, ensure test users are created in the database:

```python
# Create test users for load testing
from uris_ai.models.database import User, get_db
from uris_ai.services.auth_service import AuthService

db = next(get_db())
auth_service = AuthService()

test_users = [
    {"username": "test_user_1", "password": "test_password_1", "role": "public"},
    {"username": "test_user_2", "password": "test_password_2", "role": "public"},
    {"username": "test_user_3", "password": "test_password_3", "role": "public"},
]

for user_data in test_users:
    user = User(
        username=user_data["username"],
        password_hash=auth_service.hash_password(user_data["password"]),
        role=user_data["role"],
        is_active=True,
    )
    db.add(user)

db.commit()
```

### Test Data Setup

Ensure the database has test data:

- At least 10 regions (region_id 1-10)
- Risk scores for each region
- Recommendations for some regions
- Road network data for route finding

## Files

- **`locustfile.py`**: Main Locust test file with user behavior simulation
- **`locust.conf`**: Default configuration for Locust
- **`run_load_tests.py`**: Convenient script to run different test scenarios
- **`analyze_results.py`**: Script to analyze test results and validate requirements
- **`results/`**: Directory for test output files (CSV, HTML reports, logs)

## Running Load Tests

### Method 1: Using the Test Runner Script (Recommended)

The `run_load_tests.py` script provides convenient commands for different scenarios:

#### Baseline Test (100 users)

Establishes baseline performance metrics:

```bash
python tests/load/run_load_tests.py baseline --host http://localhost:8000
```

#### Target Load Test (500 users)

Verifies Requirement 8.2:

```bash
python tests/load/run_load_tests.py target --host http://localhost:8000
```

#### Stress Test (750 users)

Verifies auto-scaling (Requirement 8.3):

```bash
python tests/load/run_load_tests.py stress --host http://localhost:8000
```

#### Spike Test (500 users, rapid spawn)

Tests response to sudden traffic spikes:

```bash
python tests/load/run_load_tests.py spike --host http://localhost:8000
```

#### Run All Tests

Runs all scenarios in sequence:

```bash
python tests/load/run_load_tests.py all --host http://localhost:8000
```

### Method 2: Using Locust Directly

#### With Web UI

Start Locust with web interface:

```bash
locust -f tests/load/locustfile.py --host http://localhost:8000
```

Then open http://localhost:8089 in your browser and configure:

- Number of users: 500
- Spawn rate: 10 users/second
- Host: http://localhost:8000

#### Headless Mode

Run without web UI:

```bash
locust -f tests/load/locustfile.py \
       --host http://localhost:8000 \
       --users 500 \
       --spawn-rate 10 \
       --run-time 10m \
       --headless \
       --csv tests/load/results/load_test \
       --html tests/load/results/load_test_report.html
```

#### Using Configuration File

```bash
locust -f tests/load/locustfile.py --config tests/load/locust.conf
```

### Method 3: Distributed Load Testing

For very high load, run Locust in distributed mode:

#### Start Master

```bash
locust -f tests/load/locustfile.py \
       --master \
       --expect-workers 4 \
       --host http://localhost:8000
```

#### Start Workers (on same or different machines)

```bash
# Worker 1
locust -f tests/load/locustfile.py --worker --master-host localhost

# Worker 2
locust -f tests/load/locustfile.py --worker --master-host localhost

# Worker 3
locust -f tests/load/locustfile.py --worker --master-host localhost

# Worker 4
locust -f tests/load/locustfile.py --worker --master-host localhost
```

## Testing Different Environments

### Local Development

```bash
python tests/load/run_load_tests.py target --host http://localhost:8000
```

### Staging Environment

```bash
python tests/load/run_load_tests.py target --host https://uris-ai-staging.azurewebsites.net
```

### Production Environment

```bash
python tests/load/run_load_tests.py target --host https://uris-ai-production.azurewebsites.net
```

**⚠️ Warning**: Always coordinate with operations team before running load tests against production.

## Analyzing Results

### Using the Analysis Script

```bash
python tests/load/analyze_results.py tests/load/results/target_load_20240101_120000_stats.csv
```

The analyzer will:

- Display overall statistics
- Validate Requirement 8.1 (response time SLA)
- Validate Requirement 8.2 (concurrent users)
- Analyze auto-scaling indicators (Requirement 8.3)
- Show per-endpoint statistics
- Generate a summary report

### Manual Analysis

Results are saved in multiple formats:

#### CSV Files

- `*_stats.csv`: Aggregated statistics per endpoint
- `*_stats_history.csv`: Time-series data for all requests
- `*_failures.csv`: Details of failed requests

#### HTML Report

- `*_report.html`: Interactive HTML report with charts

#### Log File

- `*.log`: Detailed execution log

### Key Metrics to Review

1. **Response Time Percentiles**
   - P50 (Median): Typical user experience
   - P95: SLA threshold (must be ≤5 seconds)
   - P99: Worst-case for most users
   - Max: Absolute worst case

2. **Failure Rate**
   - Should be <1% under normal load
   - Higher rates indicate system issues

3. **Requests per Second (RPS)**
   - Indicates system throughput
   - Should remain stable under load

4. **Response Time Consistency**
   - P99/P95 ratio should be <3x
   - Higher ratios indicate performance variability

## Test Scenarios

### Baseline Test

- **Users**: 100
- **Duration**: 5 minutes
- **Purpose**: Establish baseline performance
- **Expected**: All metrics well within SLA

### Target Load Test

- **Users**: 500
- **Duration**: 10 minutes
- **Purpose**: Verify Requirement 8.2
- **Expected**: P95 ≤5 seconds, <1% failure rate

### Stress Test

- **Users**: 750
- **Duration**: 15 minutes
- **Purpose**: Verify auto-scaling (Requirement 8.3)
- **Expected**: Auto-scaling triggers, performance maintained

### Spike Test

- **Users**: 500
- **Spawn Rate**: 50 users/second
- **Duration**: 10 minutes
- **Purpose**: Test rapid traffic increase
- **Expected**: System handles spike gracefully

## User Behavior Simulation

The load test simulates realistic user behavior with weighted tasks:

- **40%**: View all region risk scores (`GET /regions/risk`)
- **25%**: View individual region risk score (`GET /regions/{id}/risk`)
- **15%**: View risk trend (`GET /regions/{id}/risk/trend`)
- **10%**: View recommendations (`GET /regions/{id}/recommendations`)
- **10%**: Find safe route (`POST /routes/safe`)

Wait time between tasks: 1-3 seconds (simulates user think time)

## Monitoring During Load Tests

### Application Insights

Monitor in Azure Application Insights:

1. **Performance**: Response times, request rates
2. **Failures**: Error rates, exception details
3. **Availability**: Uptime during test
4. **Live Metrics**: Real-time performance

### Azure Monitor

Monitor infrastructure metrics:

1. **CPU Usage**: Should trigger auto-scaling at 70%
2. **Memory Usage**: Should trigger auto-scaling at 75%
3. **Instance Count**: Should increase when load exceeds thresholds
4. **HTTP Queue Length**: Should remain low (<100)

### Database

Monitor Azure SQL Database:

1. **DTU Usage**: Should remain below 80%
2. **Query Performance**: Slow queries should be minimal
3. **Connection Pool**: Should not exhaust connections

### Cache

Monitor Azure Cache for Redis:

1. **Hit Rate**: Should be >80%
2. **Memory Usage**: Should remain below 80%
3. **Latency**: Should be <10ms

## Troubleshooting

### High Response Times

1. Check database query performance
2. Verify cache hit rate
3. Check external API latency
4. Review Application Insights for bottlenecks

### High Failure Rate

1. Check error logs for specific failures
2. Verify database connectivity
3. Check authentication issues
4. Review rate limiting configuration

### Auto-Scaling Not Triggering

1. Verify auto-scaling rules in Azure Portal
2. Check if cooldown period is preventing scaling
3. Review CPU/memory metrics
4. Ensure App Service Plan supports auto-scaling

### Inconsistent Performance

1. Check for database connection pool exhaustion
2. Verify cache is working correctly
3. Review external API response times
4. Check for resource contention

## Best Practices

1. **Always test in non-production first**: Validate tests in staging before production
2. **Coordinate with operations**: Inform team before running production tests
3. **Monitor during tests**: Watch metrics in real-time
4. **Start small**: Begin with baseline test, then increase load
5. **Document results**: Save reports and analysis for comparison
6. **Test regularly**: Run load tests after major changes
7. **Analyze failures**: Investigate all failures, even if rate is low
8. **Validate auto-scaling**: Confirm instance count changes in Azure

## Continuous Integration

### GitHub Actions Example

```yaml
name: Load Tests

on:
  schedule:
    - cron: "0 2 * * 0" # Weekly on Sunday at 2 AM
  workflow_dispatch:

jobs:
  load-test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3

      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: "3.11"

      - name: Install dependencies
        run: |
          pip install locust

      - name: Run load tests
        run: |
          python tests/load/run_load_tests.py target \
            --host ${{ secrets.STAGING_URL }}

      - name: Analyze results
        run: |
          python tests/load/analyze_results.py \
            tests/load/results/target_load_*_stats.csv

      - name: Upload results
        uses: actions/upload-artifact@v3
        with:
          name: load-test-results
          path: tests/load/results/
```

## References

- [Locust Documentation](https://docs.locust.io/)
- [Azure App Service Auto-Scaling](https://docs.microsoft.com/en-us/azure/app-service/manage-scale-up)
- [Azure Application Insights](https://docs.microsoft.com/en-us/azure/azure-monitor/app/app-insights-overview)
- [Performance Testing Best Practices](https://docs.microsoft.com/en-us/azure/architecture/best-practices/performance-testing)

## Support

For issues or questions:

1. Check the troubleshooting section above
2. Review Locust documentation
3. Check Application Insights for errors
4. Contact the development team
