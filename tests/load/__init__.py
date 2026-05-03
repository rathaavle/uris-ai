"""
Load testing package for URIS-AI.

This package contains Locust-based load tests to verify performance requirements:
- Requirement 8.1: Response time ≤5 seconds for 95% of requests
- Requirement 8.2: System should handle 500 concurrent users
- Requirement 8.3: Auto-scaling should activate when concurrent users exceed 500

Usage:
    # Run load tests
    locust -f tests/load/locustfile.py --host http://localhost:8000

    # Or use the test runner
    python tests/load/run_load_tests.py target --host http://localhost:8000

Requirements: 8.1, 8.2, 8.3
"""

__version__ = "1.0.0"
