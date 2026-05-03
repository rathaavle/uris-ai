# Load Test Results

This directory contains output from Locust load tests.

## File Types

### CSV Files

- `*_stats.csv`: Aggregated statistics per endpoint
  - Request counts, failure counts
  - Response time percentiles (P50, P95, P99, etc.)
  - Requests per second

- `*_stats_history.csv`: Time-series data
  - Timestamp for each data point
  - Request counts and response times over time
  - Useful for identifying performance trends during test

- `*_failures.csv`: Failed request details
  - Error messages
  - Occurrence counts
  - Useful for debugging issues

### HTML Reports

- `*_report.html`: Interactive HTML report
  - Charts showing response times over time
  - Request distribution
  - Failure statistics
  - Open in browser for visual analysis

### Log Files

- `*.log`: Detailed execution logs
  - Locust startup and configuration
  - Request/response details
  - Errors and warnings
  - Test lifecycle events

## Naming Convention

Files are named with the pattern:

```
{test_name}_{timestamp}_{file_type}.{extension}
```

Examples:

- `baseline_20240115_143022_stats.csv`
- `target_load_20240115_150000_report.html`
- `stress_20240115_160000.log`

## Retention

Results are not committed to git (see `.gitignore`).

Recommended retention:

- Keep recent results (last 30 days) for comparison
- Archive important baseline and milestone results
- Delete old results to save disk space

## Analysis

Use the analysis script to validate requirements:

```bash
python tests/load/analyze_results.py results/target_load_20240115_150000_stats.csv
```

## Sharing Results

To share results with team:

1. Upload to Azure Blob Storage
2. Share via team collaboration tools
3. Include in performance reports
4. Attach to deployment documentation
