# Load Testing Quick Start Guide

Get started with URIS-AI load testing in 5 minutes.

## Prerequisites

1. **Install dependencies**:

   ```bash
   pip install locust
   # Or if using Poetry:
   poetry install --with dev
   ```

2. **Start the API server**:

   ```bash
   # In one terminal
   python -m uvicorn uris_ai.api.main:app --host 0.0.0.0 --port 8000
   ```

3. **Setup test users**:
   ```bash
   # In another terminal
   python tests/load/setup_test_users.py
   ```

## Run Your First Load Test

### Option 1: Quick Test (Recommended for first time)

Run a baseline test with 100 users:

```bash
python tests/load/run_load_tests.py baseline --host http://localhost:8000
```

This will:

- Run for 5 minutes
- Simulate 100 concurrent users
- Generate results in `tests/load/results/`

### Option 2: Target Load Test (500 users)

Verify Requirement 8.2:

```bash
python tests/load/run_load_tests.py target --host http://localhost:8000
```

This will:

- Run for 10 minutes
- Simulate 500 concurrent users
- Validate response time SLA (Requirement 8.1)

### Option 3: Interactive Mode

Start Locust with web UI:

```bash
locust -f tests/load/locustfile.py --host http://localhost:8000
```

Then:

1. Open http://localhost:8089 in your browser
2. Enter number of users: `100`
3. Enter spawn rate: `5`
4. Click "Start swarming"

## View Results

### Analyze Results

```bash
# Find the latest stats file
ls -lt tests/load/results/*_stats.csv | head -1

# Analyze it
python tests/load/analyze_results.py tests/load/results/baseline_YYYYMMDD_HHMMSS_stats.csv
```

### View HTML Report

Open the HTML report in your browser:

```bash
# On macOS
open tests/load/results/baseline_YYYYMMDD_HHMMSS_report.html

# On Linux
xdg-open tests/load/results/baseline_YYYYMMDD_HHMMSS_report.html

# On Windows
start tests/load/results/baseline_YYYYMMDD_HHMMSS_report.html
```

## What to Look For

### ✓ Good Performance

- P95 response time < 5 seconds
- Failure rate < 1%
- Consistent response times (P99/P95 ratio < 3x)

### ✗ Performance Issues

- P95 response time > 5 seconds → Check database queries, cache hit rate
- High failure rate → Check logs for errors
- Inconsistent response times → Check for resource contention

## Next Steps

1. **Run all test scenarios**:

   ```bash
   python tests/load/run_load_tests.py all --host http://localhost:8000
   ```

2. **Test against staging**:

   ```bash
   python tests/load/run_load_tests.py target --host https://uris-ai-staging.azurewebsites.net
   ```

3. **Monitor in Azure**:
   - Open Azure Portal
   - Navigate to Application Insights
   - View live metrics during test

4. **Read full documentation**:
   - See `tests/load/README.md` for detailed guide
   - See `docs/performance_optimization.md` for optimization tips

## Troubleshooting

### "Connection refused"

Make sure the API server is running:

```bash
python -m uvicorn uris_ai.api.main:app --host 0.0.0.0 --port 8000
```

### "Authentication failed"

Run the test user setup script:

```bash
python tests/load/setup_test_users.py
```

### "No module named 'locust'"

Install Locust:

```bash
pip install locust
```

### High failure rate

Check the API logs for errors and ensure:

- Database is accessible
- Redis cache is running
- All required services are up

## Common Commands

```bash
# Quick baseline test
python tests/load/run_load_tests.py baseline --host http://localhost:8000

# Full target load test
python tests/load/run_load_tests.py target --host http://localhost:8000

# Stress test with auto-scaling
python tests/load/run_load_tests.py stress --host http://localhost:8000

# Analyze results
python tests/load/analyze_results.py tests/load/results/*_stats.csv

# Setup test users
python tests/load/setup_test_users.py
```

## Getting Help

- Read `tests/load/README.md` for comprehensive documentation
- Check Locust docs: https://docs.locust.io/
- Review Application Insights for detailed metrics
- Contact the development team for support
