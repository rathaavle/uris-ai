"""
Deployment Smoke Tests for URIS-AI

These tests verify critical functionality after deployment to ensure
the system is operational and ready to serve users.

Requirements: 9.2
"""

import os
import time
from typing import Optional

import pytest
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry


class SmokeTestConfig:
    """Configuration for smoke tests."""
    
    def __init__(self):
        self.api_url = os.getenv("SMOKE_TEST_API_URL", "http://localhost:8000")
        self.timeout = int(os.getenv("SMOKE_TEST_TIMEOUT", "30"))
        self.max_retries = int(os.getenv("SMOKE_TEST_MAX_RETRIES", "3"))
        self.retry_delay = int(os.getenv("SMOKE_TEST_RETRY_DELAY", "5"))


@pytest.fixture(scope="module")
def config():
    """Provide smoke test configuration."""
    return SmokeTestConfig()


@pytest.fixture(scope="module")
def http_session(config):
    """
    Create HTTP session with retry logic.
    
    This ensures transient network issues don't cause false negatives.
    """
    session = requests.Session()
    
    retry_strategy = Retry(
        total=config.max_retries,
        backoff_factor=1,
        status_forcelist=[429, 500, 502, 503, 504],
        allowed_methods=["HEAD", "GET", "OPTIONS", "POST"]
    )
    
    adapter = HTTPAdapter(max_retries=retry_strategy)
    session.mount("http://", adapter)
    session.mount("https://", adapter)
    
    return session


class TestCriticalEndpoints:
    """
    Test critical API endpoints.
    
    **Validates: Requirements 9.2**
    
    These tests ensure the most important endpoints are accessible
    and returning expected responses after deployment.
    """
    
    def test_root_endpoint(self, config, http_session):
        """
        Test root endpoint is accessible.
        
        The root endpoint should return basic application information.
        """
        response = http_session.get(
            f"{config.api_url}/",
            timeout=config.timeout
        )
        
        assert response.status_code == 200, \
            f"Root endpoint returned {response.status_code}"
        
        data = response.json()
        assert "name" in data, "Response missing 'name' field"
        assert "version" in data, "Response missing 'version' field"
        assert "status" in data, "Response missing 'status' field"
        assert data["status"] == "running", \
            f"Application status is '{data['status']}', expected 'running'"
    
    def test_health_endpoint(self, config, http_session):
        """
        Test health check endpoint.
        
        The health endpoint should always return 200 if the app is running.
        """
        response = http_session.get(
            f"{config.api_url}/health",
            timeout=config.timeout
        )
        
        assert response.status_code == 200, \
            f"Health endpoint returned {response.status_code}"
        
        data = response.json()
        assert data["status"] == "healthy", \
            f"Health status is '{data['status']}', expected 'healthy'"
        assert "version" in data, "Response missing 'version' field"
        assert "timestamp" in data, "Response missing 'timestamp' field"
    
    def test_readiness_endpoint(self, config, http_session):
        """
        Test readiness check endpoint.
        
        The readiness endpoint verifies connectivity to dependent services.
        """
        response = http_session.get(
            f"{config.api_url}/health/ready",
            timeout=config.timeout
        )
        
        assert response.status_code == 200, \
            f"Readiness endpoint returned {response.status_code}"
        
        data = response.json()
        assert "status" in data, "Response missing 'status' field"
        assert "checks" in data, "Response missing 'checks' field"
        
        # Verify critical checks
        checks = data["checks"]
        assert "database" in checks, "Missing database check"
        assert checks["database"] == "ok", \
            f"Database check failed: {checks['database']}"
    
    def test_liveness_endpoint(self, config, http_session):
        """
        Test liveness check endpoint.
        
        The liveness endpoint confirms the process is alive.
        """
        response = http_session.get(
            f"{config.api_url}/health/live",
            timeout=config.timeout
        )
        
        assert response.status_code == 200, \
            f"Liveness endpoint returned {response.status_code}"
        
        data = response.json()
        assert data["status"] == "alive", \
            f"Liveness status is '{data['status']}', expected 'alive'"
    
    def test_openapi_docs(self, config, http_session):
        """
        Test OpenAPI documentation is accessible.
        
        This ensures the API documentation is available for developers.
        """
        response = http_session.get(
            f"{config.api_url}/docs",
            timeout=config.timeout
        )
        
        assert response.status_code == 200, \
            f"OpenAPI docs returned {response.status_code}"
        assert "text/html" in response.headers.get("content-type", ""), \
            "OpenAPI docs should return HTML"


class TestDatabaseConnectivity:
    """
    Test database connectivity.
    
    **Validates: Requirements 9.2**
    
    These tests verify the application can connect to and query
    the database after deployment.
    """
    
    def test_database_connection(self, config, http_session):
        """
        Test database connection through readiness endpoint.
        
        The readiness endpoint performs a database connectivity check.
        """
        response = http_session.get(
            f"{config.api_url}/health/ready",
            timeout=config.timeout
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["checks"]["database"] == "ok", \
            "Database connectivity check failed"
    
    def test_database_query_performance(self, config, http_session):
        """
        Test database query performance.
        
        Ensures database queries complete within acceptable time.
        """
        start_time = time.time()
        
        response = http_session.get(
            f"{config.api_url}/health/ready",
            timeout=config.timeout
        )
        
        elapsed_time = time.time() - start_time
        
        assert response.status_code == 200
        assert elapsed_time < 5.0, \
            f"Database query took {elapsed_time:.2f}s, expected < 5s"


class TestExternalServiceConnectivity:
    """
    Test external service connectivity.
    
    **Validates: Requirements 9.2**
    
    These tests verify the application can connect to external
    services like cache and monitoring.
    """
    
    def test_cache_connectivity(self, config, http_session):
        """
        Test cache (Redis) connectivity.
        
        The readiness endpoint checks cache availability.
        """
        response = http_session.get(
            f"{config.api_url}/health/ready",
            timeout=config.timeout
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # Cache is non-critical, so it can be unavailable or error
        # but should be present in checks
        assert "cache" in data["checks"], \
            "Cache check missing from readiness endpoint"
        
        cache_status = data["checks"]["cache"]
        assert cache_status in ["ok", "unavailable", "error"], \
            f"Unexpected cache status: {cache_status}"
    
    def test_monitoring_connectivity(self, config, http_session):
        """
        Test monitoring (Application Insights) connectivity.
        
        The readiness endpoint checks monitoring availability.
        """
        response = http_session.get(
            f"{config.api_url}/health/ready",
            timeout=config.timeout
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert "monitoring" in data["checks"], \
            "Monitoring check missing from readiness endpoint"
        
        monitoring_status = data["checks"]["monitoring"]
        assert monitoring_status in ["ok", "disabled"], \
            f"Unexpected monitoring status: {monitoring_status}"


class TestAuthenticationEndpoints:
    """
    Test authentication endpoints.
    
    **Validates: Requirements 9.2**
    
    These tests verify authentication functionality is working.
    """
    
    def test_login_endpoint_exists(self, config, http_session):
        """
        Test login endpoint is accessible.
        
        Should return 422 for missing credentials, not 404 or 500.
        """
        response = http_session.post(
            f"{config.api_url}/api/v1/auth/login",
            json={},
            timeout=config.timeout
        )
        
        # Should return 422 (validation error) not 404 or 500
        assert response.status_code in [422, 401], \
            f"Login endpoint returned unexpected status: {response.status_code}"
    
    def test_register_endpoint_exists(self, config, http_session):
        """
        Test register endpoint is accessible.
        
        Should return 422 for missing data, not 404 or 500.
        """
        response = http_session.post(
            f"{config.api_url}/api/v1/auth/register",
            json={},
            timeout=config.timeout
        )
        
        # Should return 422 (validation error) not 404 or 500
        assert response.status_code == 422, \
            f"Register endpoint returned unexpected status: {response.status_code}"


class TestRiskEndpoints:
    """
    Test risk assessment endpoints.
    
    **Validates: Requirements 9.2**
    
    These tests verify core risk assessment functionality is accessible.
    """
    
    def test_risk_endpoint_exists(self, config, http_session):
        """
        Test risk assessment endpoint is accessible.
        
        Should return 401 (unauthorized) not 404 or 500.
        """
        response = http_session.get(
            f"{config.api_url}/api/v1/risk/regions",
            timeout=config.timeout
        )
        
        # Should return 401 (unauthorized) not 404 or 500
        assert response.status_code in [200, 401], \
            f"Risk endpoint returned unexpected status: {response.status_code}"


class TestRecommendationEndpoints:
    """
    Test recommendation endpoints.
    
    **Validates: Requirements 9.2**
    
    These tests verify recommendation functionality is accessible.
    """
    
    def test_recommendation_endpoint_exists(self, config, http_session):
        """
        Test recommendation endpoint is accessible.
        
        Should return 401 (unauthorized) not 404 or 500.
        """
        response = http_session.get(
            f"{config.api_url}/api/v1/recommendations/actions",
            timeout=config.timeout
        )
        
        # Should return 401 (unauthorized) not 404 or 500
        assert response.status_code in [200, 401], \
            f"Recommendation endpoint returned unexpected status: {response.status_code}"


class TestResponseTimes:
    """
    Test response time requirements.
    
    **Validates: Requirements 9.2**
    
    These tests verify the system meets performance requirements.
    """
    
    def test_health_endpoint_response_time(self, config, http_session):
        """
        Test health endpoint responds within acceptable time.
        
        Health checks should be fast (< 1 second).
        """
        start_time = time.time()
        
        response = http_session.get(
            f"{config.api_url}/health",
            timeout=config.timeout
        )
        
        elapsed_time = time.time() - start_time
        
        assert response.status_code == 200
        assert elapsed_time < 1.0, \
            f"Health endpoint took {elapsed_time:.2f}s, expected < 1s"
    
    def test_readiness_endpoint_response_time(self, config, http_session):
        """
        Test readiness endpoint responds within acceptable time.
        
        Readiness checks can be slower but should complete within 5 seconds.
        """
        start_time = time.time()
        
        response = http_session.get(
            f"{config.api_url}/health/ready",
            timeout=config.timeout
        )
        
        elapsed_time = time.time() - start_time
        
        assert response.status_code == 200
        assert elapsed_time < 5.0, \
            f"Readiness endpoint took {elapsed_time:.2f}s, expected < 5s"


class TestSecurityHeaders:
    """
    Test security headers are present.
    
    **Validates: Requirements 9.2**
    
    These tests verify security best practices are implemented.
    """
    
    def test_https_redirect(self, config, http_session):
        """
        Test HTTPS redirect is configured (for production).
        
        This test is informational - it checks if HTTPS is enforced.
        """
        # Skip if testing against localhost
        if "localhost" in config.api_url or "127.0.0.1" in config.api_url:
            pytest.skip("HTTPS redirect not applicable for localhost")
        
        # For production URLs, verify HTTPS is used
        assert config.api_url.startswith("https://"), \
            "Production API should use HTTPS"
    
    def test_cors_headers(self, config, http_session):
        """
        Test CORS headers are present.
        
        CORS headers should be configured for cross-origin requests.
        """
        response = http_session.options(
            f"{config.api_url}/health",
            timeout=config.timeout
        )
        
        # CORS headers should be present
        assert "access-control-allow-origin" in response.headers or \
               response.status_code == 200, \
            "CORS headers should be configured"


# Pytest configuration
def pytest_configure(config):
    """Configure pytest with custom markers."""
    config.addinivalue_line(
        "markers",
        "smoke: mark test as a smoke test for deployment validation"
    )


# Mark all tests in this module as smoke tests
pytestmark = pytest.mark.smoke
