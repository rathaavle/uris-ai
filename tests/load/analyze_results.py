#!/usr/bin/env python3
"""
Load test results analyzer for URIS-AI.

Analyzes Locust CSV output files and validates performance requirements:
- Requirement 8.1: Response time ≤5 seconds for 95% of requests
- Requirement 8.2: System should handle 500 concurrent users
- Requirement 8.3: Auto-scaling behavior

Usage:
    python tests/load/analyze_results.py tests/load/results/target_load_20240101_120000_stats.csv

Requirements: 8.1, 8.2, 8.3
"""

import argparse
import csv
import sys
from pathlib import Path
from typing import Dict, List, Tuple


class LoadTestAnalyzer:
    """Analyzer for Locust load test results."""
    
    def __init__(self, stats_file: Path):
        """
        Initialize analyzer with stats CSV file.
        
        Args:
            stats_file: Path to Locust stats CSV file
        """
        self.stats_file = stats_file
        self.stats: List[Dict] = []
        self.load_stats()
    
    def load_stats(self):
        """Load statistics from CSV file."""
        if not self.stats_file.exists():
            raise FileNotFoundError(f"Stats file not found: {self.stats_file}")
        
        with open(self.stats_file, 'r') as f:
            reader = csv.DictReader(f)
            self.stats = list(reader)
        
        if not self.stats:
            raise ValueError("Stats file is empty")
    
    def get_aggregated_stats(self) -> Dict:
        """
        Get aggregated statistics across all endpoints.
        
        Returns:
            Dictionary with aggregated metrics
        """
        # Find the "Aggregated" row which contains overall stats
        for row in self.stats:
            if row.get('Name') == 'Aggregated':
                return {
                    'total_requests': int(row.get('Request Count', 0)),
                    'total_failures': int(row.get('Failure Count', 0)),
                    'failure_rate': float(row.get('Failure Count', 0)) / max(int(row.get('Request Count', 1)), 1),
                    'avg_response_time': float(row.get('Average Response Time', 0)),
                    'median_response_time': float(row.get('Median Response Time', 0)),
                    'min_response_time': float(row.get('Min Response Time', 0)),
                    'max_response_time': float(row.get('Max Response Time', 0)),
                    'p50': float(row.get('50%', 0)),
                    'p66': float(row.get('66%', 0)),
                    'p75': float(row.get('75%', 0)),
                    'p80': float(row.get('80%', 0)),
                    'p90': float(row.get('90%', 0)),
                    'p95': float(row.get('95%', 0)),
                    'p98': float(row.get('98%', 0)),
                    'p99': float(row.get('99%', 0)),
                    'p100': float(row.get('100%', 0)),
                    'requests_per_second': float(row.get('Requests/s', 0)),
                }
        
        raise ValueError("No aggregated statistics found in CSV")
    
    def get_endpoint_stats(self) -> List[Dict]:
        """
        Get statistics for individual endpoints.
        
        Returns:
            List of dictionaries with per-endpoint metrics
        """
        endpoint_stats = []
        
        for row in self.stats:
            name = row.get('Name', '')
            if name and name != 'Aggregated':
                endpoint_stats.append({
                    'name': name,
                    'method': row.get('Type', 'GET'),
                    'total_requests': int(row.get('Request Count', 0)),
                    'total_failures': int(row.get('Failure Count', 0)),
                    'failure_rate': float(row.get('Failure Count', 0)) / max(int(row.get('Request Count', 1)), 1),
                    'avg_response_time': float(row.get('Average Response Time', 0)),
                    'median_response_time': float(row.get('Median Response Time', 0)),
                    'p95': float(row.get('95%', 0)),
                    'p99': float(row.get('99%', 0)),
                    'max_response_time': float(row.get('Max Response Time', 0)),
                    'requests_per_second': float(row.get('Requests/s', 0)),
                })
        
        return endpoint_stats
    
    def validate_requirement_8_1(self, stats: Dict) -> Tuple[bool, str]:
        """
        Validate Requirement 8.1: Response time ≤5 seconds for 95% of requests.
        
        Args:
            stats: Aggregated statistics dictionary
        
        Returns:
            Tuple of (passed, message)
        """
        p95_ms = stats['p95']
        p95_seconds = p95_ms / 1000
        threshold_seconds = 5.0
        
        passed = p95_seconds <= threshold_seconds
        
        message = (
            f"Requirement 8.1 - Response time ≤5s for 95% of requests: "
            f"{'✓ PASS' if passed else '✗ FAIL'}\n"
            f"  95th percentile: {p95_ms:.2f}ms ({p95_seconds:.2f}s)\n"
            f"  Threshold: {threshold_seconds * 1000:.0f}ms ({threshold_seconds:.0f}s)\n"
            f"  Margin: {(threshold_seconds - p95_seconds):.2f}s"
        )
        
        return passed, message
    
    def validate_requirement_8_2(self, stats: Dict, target_users: int = 500) -> Tuple[bool, str]:
        """
        Validate Requirement 8.2: System should handle 500 concurrent users.
        
        This is validated by checking if the system maintained acceptable
        performance (Requirement 8.1) under the target load.
        
        Args:
            stats: Aggregated statistics dictionary
            target_users: Target number of concurrent users
        
        Returns:
            Tuple of (passed, message)
        """
        # Requirement 8.2 is met if Requirement 8.1 is met under target load
        req_8_1_passed, _ = self.validate_requirement_8_1(stats)
        
        failure_rate = stats['failure_rate']
        acceptable_failure_rate = 0.01  # 1% failure rate threshold
        
        passed = req_8_1_passed and failure_rate <= acceptable_failure_rate
        
        message = (
            f"Requirement 8.2 - Handle {target_users} concurrent users: "
            f"{'✓ PASS' if passed else '✗ FAIL'}\n"
            f"  Total requests: {stats['total_requests']}\n"
            f"  Total failures: {stats['total_failures']}\n"
            f"  Failure rate: {failure_rate * 100:.2f}%\n"
            f"  Acceptable failure rate: {acceptable_failure_rate * 100:.2f}%\n"
            f"  Performance SLA met: {'Yes' if req_8_1_passed else 'No'}"
        )
        
        return passed, message
    
    def analyze_auto_scaling(self, stats: Dict) -> str:
        """
        Analyze auto-scaling behavior (Requirement 8.3).
        
        Note: This requires monitoring data from Azure to fully validate.
        This analysis provides indicators based on performance metrics.
        
        Args:
            stats: Aggregated statistics dictionary
        
        Returns:
            Analysis message
        """
        p95_ms = stats['p95']
        p99_ms = stats['p99']
        max_ms = stats['max_response_time']
        
        # Indicators of effective auto-scaling:
        # - P95 and P99 remain close (consistent performance)
        # - Max response time is not excessively high
        p95_p99_ratio = p99_ms / p95_ms if p95_ms > 0 else float('inf')
        p99_max_ratio = max_ms / p99_ms if p99_ms > 0 else float('inf')
        
        message = (
            f"Requirement 8.3 - Auto-scaling analysis:\n"
            f"  95th percentile: {p95_ms:.2f}ms\n"
            f"  99th percentile: {p99_ms:.2f}ms\n"
            f"  Max response time: {max_ms:.2f}ms\n"
            f"  P99/P95 ratio: {p95_p99_ratio:.2f}x\n"
            f"  Max/P99 ratio: {p99_max_ratio:.2f}x\n"
            f"\n"
            f"  Performance consistency: "
        )
        
        if p95_p99_ratio < 2.0:
            message += "✓ Excellent (P99/P95 < 2x)\n"
        elif p95_p99_ratio < 3.0:
            message += "✓ Good (P99/P95 < 3x)\n"
        else:
            message += "⚠ Variable (P99/P95 ≥ 3x - may indicate scaling delays)\n"
        
        message += (
            f"\n"
            f"  Note: Full validation of auto-scaling requires Azure monitoring data\n"
            f"  to confirm instance count changes and scaling trigger events."
        )
        
        return message
    
    def generate_report(self):
        """Generate comprehensive analysis report."""
        print("=" * 80)
        print("URIS-AI Load Test Results Analysis")
        print("=" * 80)
        print(f"Stats file: {self.stats_file}")
        print("=" * 80)
        
        # Get aggregated stats
        agg_stats = self.get_aggregated_stats()
        
        # Overall statistics
        print("\nOverall Statistics:")
        print(f"  Total Requests: {agg_stats['total_requests']:,}")
        print(f"  Total Failures: {agg_stats['total_failures']:,}")
        print(f"  Failure Rate: {agg_stats['failure_rate'] * 100:.2f}%")
        print(f"  Requests/Second: {agg_stats['requests_per_second']:.2f}")
        print(f"\nResponse Time Statistics:")
        print(f"  Average: {agg_stats['avg_response_time']:.2f}ms")
        print(f"  Median (P50): {agg_stats['median_response_time']:.2f}ms")
        print(f"  P75: {agg_stats['p75']:.2f}ms")
        print(f"  P90: {agg_stats['p90']:.2f}ms")
        print(f"  P95: {agg_stats['p95']:.2f}ms")
        print(f"  P99: {agg_stats['p99']:.2f}ms")
        print(f"  Max: {agg_stats['max_response_time']:.2f}ms")
        
        # Requirement validation
        print("\n" + "=" * 80)
        print("Requirement Validation")
        print("=" * 80)
        
        req_8_1_passed, req_8_1_msg = self.validate_requirement_8_1(agg_stats)
        print(f"\n{req_8_1_msg}")
        
        req_8_2_passed, req_8_2_msg = self.validate_requirement_8_2(agg_stats)
        print(f"\n{req_8_2_msg}")
        
        req_8_3_msg = self.analyze_auto_scaling(agg_stats)
        print(f"\n{req_8_3_msg}")
        
        # Per-endpoint statistics
        endpoint_stats = self.get_endpoint_stats()
        if endpoint_stats:
            print("\n" + "=" * 80)
            print("Per-Endpoint Statistics")
            print("=" * 80)
            
            for ep in endpoint_stats:
                print(f"\n{ep['method']} {ep['name']}:")
                print(f"  Requests: {ep['total_requests']:,}")
                print(f"  Failures: {ep['total_failures']:,} ({ep['failure_rate'] * 100:.2f}%)")
                print(f"  Avg Response Time: {ep['avg_response_time']:.2f}ms")
                print(f"  P95: {ep['p95']:.2f}ms")
                print(f"  P99: {ep['p99']:.2f}ms")
                print(f"  Max: {ep['max_response_time']:.2f}ms")
                print(f"  RPS: {ep['requests_per_second']:.2f}")
                
                # Flag slow endpoints
                if ep['p95'] > 5000:
                    print(f"  ⚠ WARNING: P95 exceeds 5s SLA")
        
        # Summary
        print("\n" + "=" * 80)
        print("Summary")
        print("=" * 80)
        
        all_passed = req_8_1_passed and req_8_2_passed
        
        if all_passed:
            print("✓ All performance requirements validated successfully")
        else:
            print("✗ Some performance requirements not met")
            if not req_8_1_passed:
                print("  - Requirement 8.1 (response time SLA) not met")
            if not req_8_2_passed:
                print("  - Requirement 8.2 (concurrent users) not met")
        
        print("=" * 80)
        
        return all_passed


def main():
    """Main entry point for results analyzer."""
    parser = argparse.ArgumentParser(
        description="Analyze URIS-AI load test results",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    
    parser.add_argument(
        "stats_file",
        type=Path,
        help="Path to Locust stats CSV file",
    )
    
    args = parser.parse_args()
    
    try:
        analyzer = LoadTestAnalyzer(args.stats_file)
        all_passed = analyzer.generate_report()
        sys.exit(0 if all_passed else 1)
    except Exception as e:
        print(f"Error analyzing results: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
