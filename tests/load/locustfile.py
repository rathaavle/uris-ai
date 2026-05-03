"""
Locust load testing for URIS-AI API.

This file contains load test scenarios to verify performance requirements:
- Requirement 8.1: Response time ≤5 seconds for 95% of requests
- Requirement 8.2: System should handle 500 concurrent users
- Requirement 8.3: Auto-scaling should activate when concurrent users exceed 500

Usage:
    # Run with web UI
    locust -f tests/load/locustfile.py --host=http://localhost:8000

    # Run headless with 500 users
    locust -f tests/load/locustfile.py --host=http://localhost:8000 \
           --users 500 --spawn-rate 10 --run-time 10m --headless

    # Run against production
    locust -f tests/load/locustfile.py \
           --host=https://uris-ai-api-production.azurewebsites.net \
           --users 500 --spawn-rate 10 --run-time 10m --headless

Requirements: 8.1, 8.2, 8.3
"""

import json
import logging
import random
from typing import Any, Dict, Optional

from locust import HttpUser, TaskSet, between, events, task
from locust.runners import MasterRunner, WorkerRunner

logger = logging.getLogger(__name__)


# Test data configuration
TEST_REGIONS = list(range(1, 11))  # Region IDs 1-10
TEST_HOURS = [6, 12, 24, 48, 72, 168]  # Hours for trend queries
TEST_COORDINATES = [
    # Jakarta coordinates
    {"latitude": -6.2088, "longitude": 106.8456},
    {"latitude": -6.1751, "longitude": 106.8650},
    {"latitude": -6.2297, "longitude": 106.8177},
    {"latitude": -6.1944, "longitude": 106.8229},
    # Jawa Barat coordinates
    {"latitude": -6.9175, "longitude": 107.6191},
    {"latitude": -6.8915, "longitude": 107.6107},
    {"latitude": -6.9389, "longitude": 107.6333},
]

# Authentication credentials for load testing
# In production, use dedicated test accounts
TEST_USERS = [
    {"username": "test_user_1", "password": "test_password_1"},
    {"username": "test_user_2", "password": "test_password_2"},
    {"username": "test_user_3", "password": "test_password_3"},
]


class URISAITaskSet(TaskSet):
    """
    Task set for URIS-AI load testing.
    
    Simulates realistic user behavior with weighted task distribution:
    - 40% viewing all region risk scores (most common operation)
    - 25% viewing individual region risk scores
    - 15% viewing risk trends
    - 10% viewing recommendations
    - 10% finding safe routes
    """

    def on_start(self):
        """
        Called when a simulated user starts.
        Performs login to obtain authentication token.
        """
        self.token: Optional[str] = None
        self.login()

    def login(self):
        """
        Authenticate and obtain JWT token.
        
        Requirements: 10.2
        """
        # Select random test user
        user_creds = random.choice(TEST_USERS)
        
        response = self.client.post(
            "/auth/login",
            json=user_creds,
            name="/auth/login",
            catch_response=True,
        )
        
        if response.status_code == 200:
            data = response.json()
            self.token = data.get("access_token")
            response.success()
            logger.debug(f"Login successful for user {user_creds['username']}")
        else:
            response.failure(f"Login failed: {response.status_code}")
            logger.error(f"Login failed for user {user_creds['username']}: {response.text}")

    def get_headers(self) -> Dict[str, str]:
        """Get headers with authentication token."""
        if self.token:
            return {"Authorization": f"Bearer {self.token}"}
        return {}

    @task(40)
    def get_all_regions_risk(self):
        """
        Get risk scores for all regions.
        
        This is the most common operation - users checking overall risk status.
        
        Requirements: 4.2, 8.1
        """
        with self.client.get(
            "/regions/risk",
            headers=self.get_headers(),
            name="/regions/risk",
            catch_response=True,
        ) as response:
            if response.status_code == 200:
                data = response.json()
                if "regions" in data and "total" in data:
                    response.success()
                else:
                    response.failure("Invalid response structure")
            elif response.status_code == 401:
                # Token expired, re-login
                self.login()
                response.failure("Authentication required - re-logging in")
            else:
                response.failure(f"Failed with status {response.status_code}")

    @task(25)
    def get_region_risk(self):
        """
        Get risk score for a specific region.
        
        Users drilling down into specific region details.
        
        Requirements: 4.2, 8.1
        """
        region_id = random.choice(TEST_REGIONS)
        
        with self.client.get(
            f"/regions/{region_id}/risk",
            headers=self.get_headers(),
            name="/regions/{region_id}/risk",
            catch_response=True,
        ) as response:
            if response.status_code == 200:
                data = response.json()
                if "urban_risk_score" in data and "risk_category" in data:
                    response.success()
                else:
                    response.failure("Invalid response structure")
            elif response.status_code == 401:
                self.login()
                response.failure("Authentication required - re-logging in")
            elif response.status_code == 404:
                response.failure(f"Region {region_id} not found")
            else:
                response.failure(f"Failed with status {response.status_code}")

    @task(15)
    def get_risk_trend(self):
        """
        Get risk trend for a region over time.
        
        Users analyzing historical risk patterns.
        
        Requirements: 4.4, 8.1
        """
        region_id = random.choice(TEST_REGIONS)
        hours = random.choice(TEST_HOURS)
        
        with self.client.get(
            f"/regions/{region_id}/risk/trend?hours={hours}",
            headers=self.get_headers(),
            name="/regions/{region_id}/risk/trend",
            catch_response=True,
        ) as response:
            if response.status_code == 200:
                data = response.json()
                if "trend" in data and "region_id" in data:
                    response.success()
                else:
                    response.failure("Invalid response structure")
            elif response.status_code == 401:
                self.login()
                response.failure("Authentication required - re-logging in")
            elif response.status_code == 404:
                response.failure(f"Region {region_id} not found")
            else:
                response.failure(f"Failed with status {response.status_code}")

    @task(10)
    def get_recommendations(self):
        """
        Get recommendations for a region.
        
        Users checking actionable recommendations.
        
        Requirements: 5.1, 8.1
        """
        region_id = random.choice(TEST_REGIONS)
        
        with self.client.get(
            f"/regions/{region_id}/recommendations",
            headers=self.get_headers(),
            name="/regions/{region_id}/recommendations",
            catch_response=True,
        ) as response:
            if response.status_code == 200:
                data = response.json()
                if "recommendations" in data and "total" in data:
                    response.success()
                else:
                    response.failure("Invalid response structure")
            elif response.status_code == 401:
                self.login()
                response.failure("Authentication required - re-logging in")
            elif response.status_code == 404:
                response.failure(f"Region {region_id} not found")
            else:
                response.failure(f"Failed with status {response.status_code}")

    @task(10)
    def find_safe_route(self):
        """
        Find safe route between two points.
        
        Users planning safe travel routes.
        
        Requirements: 5.2, 8.1
        """
        origin = random.choice(TEST_COORDINATES)
        destination = random.choice(TEST_COORDINATES)
        
        # Ensure origin and destination are different
        while origin == destination:
            destination = random.choice(TEST_COORDINATES)
        
        payload = {
            "origin": origin,
            "destination": destination,
        }
        
        with self.client.post(
            "/routes/safe",
            headers=self.get_headers(),
            json=payload,
            name="/routes/safe",
            catch_response=True,
        ) as response:
            if response.status_code == 200:
                data = response.json()
                if "is_safe" in data and "origin" in data and "destination" in data:
                    response.success()
                else:
                    response.failure("Invalid response structure")
            elif response.status_code == 401:
                self.login()
                response.failure("Authentication required - re-logging in")
            else:
                response.failure(f"Failed with status {response.status_code}")


class URISAIUser(HttpUser):
    """
    Simulated user for URIS-AI load testing.
    
    Configuration:
    - wait_time: Random wait between 1-3 seconds between tasks (realistic user behavior)
    - tasks: URISAITaskSet containing all user actions
    
    Requirements: 8.1, 8.2, 8.3
    """
    tasks = [URISAITaskSet]
    wait_time = between(1, 3)  # Wait 1-3 seconds between tasks


# Event handlers for test lifecycle and reporting

@events.test_start.add_listener
def on_test_start(environment, **kwargs):
    """
    Called when the load test starts.
    
    Logs test configuration and requirements being validated.
    """
    logger.info("=" * 80)
    logger.info("URIS-AI Load Test Starting")
    logger.info("=" * 80)
    logger.info("Performance Requirements:")
    logger.info("  - Requirement 8.1: Response time ≤5 seconds for 95% of requests")
    logger.info("  - Requirement 8.2: Handle 500 concurrent users")
    logger.info("  - Requirement 8.3: Auto-scaling when users exceed 500")
    logger.info("=" * 80)
    
    if isinstance(environment.runner, MasterRunner):
        logger.info("Running in distributed mode (master)")
    elif isinstance(environment.runner, WorkerRunner):
        logger.info("Running in distributed mode (worker)")
    else:
        logger.info("Running in standalone mode")


@events.test_stop.add_listener
def on_test_stop(environment, **kwargs):
    """
    Called when the load test stops.
    
    Analyzes results and validates performance requirements.
    """
    logger.info("=" * 80)
    logger.info("URIS-AI Load Test Completed")
    logger.info("=" * 80)
    
    stats = environment.stats
    
    # Analyze overall statistics
    logger.info("Overall Statistics:")
    logger.info(f"  Total Requests: {stats.total.num_requests}")
    logger.info(f"  Total Failures: {stats.total.num_failures}")
    logger.info(f"  Failure Rate: {stats.total.fail_ratio * 100:.2f}%")
    logger.info(f"  Average Response Time: {stats.total.avg_response_time:.2f}ms")
    logger.info(f"  Median Response Time: {stats.total.median_response_time:.2f}ms")
    logger.info(f"  95th Percentile: {stats.total.get_response_time_percentile(0.95):.2f}ms")
    logger.info(f"  99th Percentile: {stats.total.get_response_time_percentile(0.99):.2f}ms")
    logger.info(f"  Max Response Time: {stats.total.max_response_time:.2f}ms")
    logger.info(f"  Requests per Second: {stats.total.total_rps:.2f}")
    
    # Validate Requirement 8.1: Response time ≤5 seconds for 95% of requests
    p95_response_time = stats.total.get_response_time_percentile(0.95)
    requirement_8_1_met = p95_response_time <= 5000  # 5 seconds = 5000ms
    
    logger.info("=" * 80)
    logger.info("Requirement Validation:")
    logger.info(f"  Requirement 8.1 (95th percentile ≤5s): {'✓ PASS' if requirement_8_1_met else '✗ FAIL'}")
    logger.info(f"    - 95th percentile: {p95_response_time:.2f}ms ({p95_response_time/1000:.2f}s)")
    logger.info(f"    - Threshold: 5000ms (5s)")
    
    # Log per-endpoint statistics
    logger.info("=" * 80)
    logger.info("Per-Endpoint Statistics:")
    for entry in stats.entries.values():
        if entry.num_requests > 0:
            logger.info(f"  {entry.name}:")
            logger.info(f"    - Requests: {entry.num_requests}")
            logger.info(f"    - Failures: {entry.num_failures} ({entry.fail_ratio * 100:.2f}%)")
            logger.info(f"    - Avg Response Time: {entry.avg_response_time:.2f}ms")
            logger.info(f"    - 95th Percentile: {entry.get_response_time_percentile(0.95):.2f}ms")
    
    logger.info("=" * 80)


@events.request.add_listener
def on_request(request_type, name, response_time, response_length, exception, context, **kwargs):
    """
    Called for each request.
    
    Logs slow requests that exceed the 5-second SLA.
    """
    if response_time > 5000:  # 5 seconds
        logger.warning(
            f"Slow request detected: {request_type} {name} took {response_time:.2f}ms "
            f"(exceeds 5s SLA)"
        )
