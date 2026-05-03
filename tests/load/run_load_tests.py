#!/usr/bin/env python3
"""
Load test runner script for URIS-AI.

This script provides convenient commands to run different load test scenarios:
- Baseline test: 100 users to establish baseline performance
- Target load test: 500 users to verify Requirement 8.2
- Stress test: 750 users to verify auto-scaling (Requirement 8.3)
- Spike test: Rapid increase to 500 users to test scaling response

Usage:
    python tests/load/run_load_tests.py baseline --host http://localhost:8000
    python tests/load/run_load_tests.py target --host http://localhost:8000
    python tests/load/run_load_tests.py stress --host http://localhost:8000
    python tests/load/run_load_tests.py spike --host http://localhost:8000
    python tests/load/run_load_tests.py all --host http://localhost:8000

Requirements: 8.1, 8.2, 8.3
"""

import argparse
import os
import subprocess
import sys
from datetime import datetime
from pathlib import Path


def ensure_results_directory():
    """Create results directory if it doesn't exist."""
    results_dir = Path("tests/load/results")
    results_dir.mkdir(parents=True, exist_ok=True)
    return results_dir


def run_locust_test(
    host: str,
    users: int,
    spawn_rate: int,
    run_time: str,
    test_name: str,
    description: str,
):
    """
    Run a Locust load test with specified parameters.
    
    Args:
        host: Target host URL
        users: Number of concurrent users
        spawn_rate: Users spawned per second
        run_time: Test duration (e.g., "10m", "1h")
        test_name: Name for output files
        description: Test description for logging
    """
    results_dir = ensure_results_directory()
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # Output file paths
    csv_prefix = results_dir / f"{test_name}_{timestamp}"
    html_report = results_dir / f"{test_name}_{timestamp}_report.html"
    log_file = results_dir / f"{test_name}_{timestamp}.log"
    
    print("=" * 80)
    print(f"Running Load Test: {test_name}")
    print("=" * 80)
    print(f"Description: {description}")
    print(f"Host: {host}")
    print(f"Users: {users}")
    print(f"Spawn Rate: {spawn_rate} users/second")
    print(f"Duration: {run_time}")
    print(f"Results: {csv_prefix}_stats.csv")
    print(f"Report: {html_report}")
    print(f"Log: {log_file}")
    print("=" * 80)
    
    # Build Locust command
    cmd = [
        "locust",
        "-f", "tests/load/locustfile.py",
        "--host", host,
        "--users", str(users),
        "--spawn-rate", str(spawn_rate),
        "--run-time", run_time,
        "--headless",
        "--csv", str(csv_prefix),
        "--csv-full-history",
        "--html", str(html_report),
        "--loglevel", "INFO",
        "--logfile", str(log_file),
    ]
    
    # Run the test
    try:
        result = subprocess.run(cmd, check=True)
        print("\n" + "=" * 80)
        print(f"✓ Test '{test_name}' completed successfully")
        print(f"  Results saved to: {results_dir}")
        print("=" * 80 + "\n")
        return True
    except subprocess.CalledProcessError as e:
        print("\n" + "=" * 80)
        print(f"✗ Test '{test_name}' failed with exit code {e.returncode}")
        print("=" * 80 + "\n")
        return False
    except KeyboardInterrupt:
        print("\n" + "=" * 80)
        print(f"Test '{test_name}' interrupted by user")
        print("=" * 80 + "\n")
        return False


def baseline_test(host: str):
    """
    Run baseline test with 100 users.
    
    Establishes baseline performance metrics under normal load.
    
    Requirements: 8.1
    """
    return run_locust_test(
        host=host,
        users=100,
        spawn_rate=5,
        run_time="5m",
        test_name="baseline",
        description="Baseline test with 100 users to establish performance baseline",
    )


def target_load_test(host: str):
    """
    Run target load test with 500 users.
    
    Verifies Requirement 8.2: System should handle 500 concurrent users.
    
    Requirements: 8.1, 8.2
    """
    return run_locust_test(
        host=host,
        users=500,
        spawn_rate=10,
        run_time="10m",
        test_name="target_load",
        description="Target load test with 500 users (Requirement 8.2)",
    )


def stress_test(host: str):
    """
    Run stress test with 750 users.
    
    Verifies Requirement 8.3: Auto-scaling should activate when users exceed 500.
    
    Requirements: 8.1, 8.3
    """
    return run_locust_test(
        host=host,
        users=750,
        spawn_rate=10,
        run_time="15m",
        test_name="stress",
        description="Stress test with 750 users to verify auto-scaling (Requirement 8.3)",
    )


def spike_test(host: str):
    """
    Run spike test with rapid increase to 500 users.
    
    Tests system response to sudden traffic spikes.
    
    Requirements: 8.1, 8.2, 8.3
    """
    return run_locust_test(
        host=host,
        users=500,
        spawn_rate=50,  # Rapid spawn rate
        run_time="10m",
        test_name="spike",
        description="Spike test with rapid increase to 500 users",
    )


def run_all_tests(host: str):
    """
    Run all load test scenarios in sequence.
    
    Requirements: 8.1, 8.2, 8.3
    """
    tests = [
        ("Baseline", baseline_test),
        ("Target Load", target_load_test),
        ("Stress", stress_test),
        ("Spike", spike_test),
    ]
    
    results = {}
    
    print("\n" + "=" * 80)
    print("Running All Load Test Scenarios")
    print("=" * 80 + "\n")
    
    for test_name, test_func in tests:
        print(f"\nStarting {test_name} test...\n")
        success = test_func(host)
        results[test_name] = success
        
        if not success:
            print(f"\n⚠ {test_name} test failed. Continuing with remaining tests...\n")
    
    # Print summary
    print("\n" + "=" * 80)
    print("Load Test Summary")
    print("=" * 80)
    for test_name, success in results.items():
        status = "✓ PASS" if success else "✗ FAIL"
        print(f"  {test_name}: {status}")
    print("=" * 80 + "\n")
    
    # Return overall success
    return all(results.values())


def main():
    """Main entry point for load test runner."""
    parser = argparse.ArgumentParser(
        description="Run URIS-AI load tests",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Run baseline test against local server
  python tests/load/run_load_tests.py baseline --host http://localhost:8000
  
  # Run target load test against staging
  python tests/load/run_load_tests.py target --host https://uris-ai-staging.azurewebsites.net
  
  # Run all tests against production
  python tests/load/run_load_tests.py all --host https://uris-ai-production.azurewebsites.net
        """,
    )
    
    parser.add_argument(
        "scenario",
        choices=["baseline", "target", "stress", "spike", "all"],
        help="Load test scenario to run",
    )
    
    parser.add_argument(
        "--host",
        required=True,
        help="Target host URL (e.g., http://localhost:8000)",
    )
    
    args = parser.parse_args()
    
    # Validate host URL
    if not args.host.startswith(("http://", "https://")):
        print("Error: Host must start with http:// or https://")
        sys.exit(1)
    
    # Run selected scenario
    scenarios = {
        "baseline": baseline_test,
        "target": target_load_test,
        "stress": stress_test,
        "spike": spike_test,
        "all": run_all_tests,
    }
    
    test_func = scenarios[args.scenario]
    success = test_func(args.host)
    
    # Exit with appropriate code
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
