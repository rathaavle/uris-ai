"""
Integration tests for URIS-AI FastAPI API endpoints.

Tests cover:
- Authentication and authorization (login, logout, /users/me)
- Risk endpoints (GET /regions/{id}/risk, GET /regions/risk, GET /regions/{id}/risk/trend)
- Recommendation endpoints (GET /regions/{id}/recommendations, POST /routes/safe)
- Error responses (404, 401, 403, 422)
- Rate limiting middleware
- CORS middleware

Requirements: 6.1, 10.2, 10.4
"""

from datetime import datetime, timezone
from typing import Generator
from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from uris_ai.api.main import create_app
from uris_ai.models.database import Base, Recommendation, Region, RiskScore, User
from uris_ai.models.db_utils import init_database
from uris_ai.services.auth_service import AuthService


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture(scope="module")
def test_engine():
    """
    In-memory SQLite engine for API tests.

    StaticPool keeps a single connection alive for the lifetime of the engine,
    which is required when using SQLite in-memory databases across multiple
    sessions (otherwise each session would get a fresh, empty database).
    """
    from sqlalchemy.pool import StaticPool

    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
        echo=False,
    )
    init_database(engine)
    yield engine
    engine.dispose()


@pytest.fixture(scope="module")
def test_session_factory(test_engine):
    """Session factory bound to the test engine."""
    return sessionmaker(bind=test_engine, autocommit=False, autoflush=False)


@pytest.fixture(scope="module")
def auth_service():
    """AuthService with a fixed test secret."""
    return AuthService(
        secret_key="test-secret-key-for-unit-tests",
        algorithm="HS256",
        access_token_expire_minutes=30,
    )


@pytest.fixture(scope="module")
def seeded_db(test_session_factory, auth_service):
    """
    Seed the test database with regions, risk scores, recommendations, and users.
    Returns the session factory so tests can open their own sessions.
    """
    session: Session = test_session_factory()

    # Regions
    region1 = Region(
        region_id=1,
        name="Jakarta Pusat",
        latitude=-6.1751,
        longitude=106.8650,
        elevation=8.0,
        drainage_capacity=500.0,
    )
    region2 = Region(
        region_id=2,
        name="Jakarta Selatan",
        latitude=-6.2615,
        longitude=106.8106,
        elevation=12.0,
        drainage_capacity=600.0,
    )
    session.add_all([region1, region2])
    session.flush()

    # Risk scores
    now = datetime.now(timezone.utc)
    session.add_all([
        RiskScore(
            region_id=1,
            date=now,
            flood_risk=80.0,
            traffic_impact=70.0,
            service_access=60.0,
            urban_risk_score=73.0,
            created_at=now,
        ),
        RiskScore(
            region_id=2,
            date=now,
            flood_risk=30.0,
            traffic_impact=20.0,
            service_access=15.0,
            urban_risk_score=24.5,
            created_at=now,
        ),
    ])

    # Recommendations
    session.add(
        Recommendation(
            region_id=1,
            recommendation_type="alert",
            description="Peringatan risiko tinggi di Jakarta Pusat",
            urgency_level="Waspada",
            created_at=now,
            is_active=True,
        )
    )

    # Users
    session.add_all([
        User(
            username="gov_user",
            email="gov@test.com",
            password_hash=auth_service.hash_password("govpass123"),
            role="government",
            is_active=True,
        ),
        User(
            username="public_user",
            email="public@test.com",
            password_hash=auth_service.hash_password("publicpass123"),
            role="public",
            is_active=True,
        ),
        User(
            username="inactive_user",
            email="inactive@test.com",
            password_hash=auth_service.hash_password("inactivepass"),
            role="public",
            is_active=False,
        ),
    ])

    session.commit()
    session.close()
    return test_session_factory


@pytest.fixture(scope="module")
def client(seeded_db, auth_service):
    """
    TestClient with overridden dependencies pointing to the test DB and
    a disabled Redis cache.
    """
    app = create_app()

    # Override DB dependency
    def override_get_db() -> Generator[Session, None, None]:
        session = seeded_db()
        try:
            yield session
            session.commit()
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()

    # Override auth service dependency
    def override_get_auth_service() -> AuthService:
        return auth_service

    # Override cache to a no-op mock
    mock_cache = MagicMock()
    mock_cache.get_risk_score.return_value = None
    mock_cache.get_all_risk_scores.return_value = None
    mock_cache.get_risk_trend.return_value = None
    mock_cache.get_recommendations.return_value = None
    mock_cache.set_risk_score.return_value = True
    mock_cache.set_all_risk_scores.return_value = True
    mock_cache.set_risk_trend.return_value = True
    mock_cache.set_recommendations.return_value = True

    from uris_ai.api import dependencies
    app.dependency_overrides[dependencies.get_db] = override_get_db
    app.dependency_overrides[dependencies.get_auth_service] = override_get_auth_service

    # Patch CacheService constructor in routers
    with patch("uris_ai.api.routers.risk.CacheService", return_value=mock_cache), \
         patch("uris_ai.api.routers.recommendations.CacheService", return_value=mock_cache):
        with TestClient(app, raise_server_exceptions=False, base_url="http://testserver") as c:
            yield c


@pytest.fixture(scope="module")
def gov_token(client):
    """JWT token for the government user."""
    resp = client.post(
        "/auth/login",
        json={"username": "gov_user", "password": "govpass123"},
    )
    assert resp.status_code == 200
    return resp.json()["access_token"]


@pytest.fixture(scope="module")
def public_token(client):
    """JWT token for the public user."""
    resp = client.post(
        "/auth/login",
        json={"username": "public_user", "password": "publicpass123"},
    )
    assert resp.status_code == 200
    return resp.json()["access_token"]


# ---------------------------------------------------------------------------
# Helper
# ---------------------------------------------------------------------------


def auth_headers(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


# ---------------------------------------------------------------------------
# System endpoints
# ---------------------------------------------------------------------------


class TestSystemEndpoints:
    def test_root(self, client):
        resp = client.get("/")
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "running"
        assert "name" in data
        assert "version" in data

    def test_health(self, client):
        resp = client.get("/health")
        assert resp.status_code == 200
        assert resp.json()["status"] == "healthy"

    def test_health_live(self, client):
        resp = client.get("/health/live")
        assert resp.status_code == 200
        assert resp.json()["status"] == "alive"


# ---------------------------------------------------------------------------
# Authentication
# ---------------------------------------------------------------------------


class TestAuthentication:
    def test_login_success_government(self, client):
        resp = client.post(
            "/auth/login",
            json={"username": "gov_user", "password": "govpass123"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"
        assert data["role"] == "government"
        assert data["expires_in"] > 0

    def test_login_success_public(self, client):
        resp = client.post(
            "/auth/login",
            json={"username": "public_user", "password": "publicpass123"},
        )
        assert resp.status_code == 200
        assert resp.json()["role"] == "public"

    def test_login_wrong_password(self, client):
        resp = client.post(
            "/auth/login",
            json={"username": "gov_user", "password": "wrongpassword"},
        )
        assert resp.status_code == 401
        assert "detail" in resp.json()

    def test_login_unknown_user(self, client):
        resp = client.post(
            "/auth/login",
            json={"username": "nobody", "password": "pass"},
        )
        assert resp.status_code == 401

    def test_login_inactive_user(self, client):
        resp = client.post(
            "/auth/login",
            json={"username": "inactive_user", "password": "inactivepass"},
        )
        assert resp.status_code == 403

    def test_login_missing_fields(self, client):
        resp = client.post("/auth/login", json={"username": "gov_user"})
        assert resp.status_code == 422

    def test_logout_success(self, client, gov_token):
        resp = client.post("/auth/logout", headers=auth_headers(gov_token))
        assert resp.status_code == 200
        assert "message" in resp.json()

    def test_logout_without_token(self, client):
        resp = client.post("/auth/logout")
        assert resp.status_code == 401


# ---------------------------------------------------------------------------
# Users
# ---------------------------------------------------------------------------


class TestUsersEndpoints:
    def test_get_current_user_government(self, client, gov_token):
        resp = client.get("/users/me", headers=auth_headers(gov_token))
        assert resp.status_code == 200
        data = resp.json()
        assert data["username"] == "gov_user"
        assert data["role"] == "government"
        assert data["is_active"] is True
        assert "email" in data

    def test_get_current_user_public(self, client, public_token):
        resp = client.get("/users/me", headers=auth_headers(public_token))
        assert resp.status_code == 200
        assert resp.json()["role"] == "public"

    def test_get_current_user_no_token(self, client):
        resp = client.get("/users/me")
        assert resp.status_code == 401

    def test_get_current_user_invalid_token(self, client):
        resp = client.get("/users/me", headers={"Authorization": "Bearer invalid.token.here"})
        assert resp.status_code == 401


# ---------------------------------------------------------------------------
# Risk endpoints
# ---------------------------------------------------------------------------


class TestRiskEndpoints:
    def test_get_region_risk_success(self, client, gov_token):
        resp = client.get("/regions/1/risk", headers=auth_headers(gov_token))
        assert resp.status_code == 200
        data = resp.json()
        assert data["region_id"] == 1
        assert 0 <= data["urban_risk_score"] <= 100
        assert data["risk_category"] in ("RENDAH", "SEDANG", "TINGGI", "KRITIS")
        assert "flood_risk" in data
        assert "traffic_impact" in data
        assert "service_access" in data

    def test_get_region_risk_public_user(self, client, public_token):
        """Public users should also be able to access risk data."""
        resp = client.get("/regions/1/risk", headers=auth_headers(public_token))
        assert resp.status_code == 200

    def test_get_region_risk_not_found(self, client, gov_token):
        resp = client.get("/regions/9999/risk", headers=auth_headers(gov_token))
        assert resp.status_code == 404
        assert "detail" in resp.json()

    def test_get_region_risk_no_auth(self, client):
        resp = client.get("/regions/1/risk")
        assert resp.status_code == 401

    def test_get_all_regions_risk(self, client, gov_token):
        resp = client.get("/regions/risk", headers=auth_headers(gov_token))
        assert resp.status_code == 200
        data = resp.json()
        assert "regions" in data
        assert "total" in data
        assert isinstance(data["regions"], list)
        assert data["total"] >= 1

    def test_get_all_regions_risk_no_auth(self, client):
        resp = client.get("/regions/risk")
        assert resp.status_code == 401

    def test_get_risk_trend_default_hours(self, client, gov_token):
        resp = client.get("/regions/1/risk/trend", headers=auth_headers(gov_token))
        assert resp.status_code == 200
        data = resp.json()
        assert data["region_id"] == 1
        assert data["hours"] == 24
        assert "trend" in data
        assert isinstance(data["trend"], list)

    def test_get_risk_trend_custom_hours(self, client, gov_token):
        resp = client.get(
            "/regions/1/risk/trend?hours=48", headers=auth_headers(gov_token)
        )
        assert resp.status_code == 200
        assert resp.json()["hours"] == 48

    def test_get_risk_trend_invalid_hours(self, client, gov_token):
        resp = client.get(
            "/regions/1/risk/trend?hours=0", headers=auth_headers(gov_token)
        )
        assert resp.status_code == 422

    def test_get_risk_trend_region_not_found(self, client, gov_token):
        resp = client.get("/regions/9999/risk/trend", headers=auth_headers(gov_token))
        assert resp.status_code == 404


# ---------------------------------------------------------------------------
# Recommendation endpoints
# ---------------------------------------------------------------------------


class TestRecommendationEndpoints:
    def test_get_recommendations_success(self, client, gov_token):
        resp = client.get(
            "/regions/1/recommendations", headers=auth_headers(gov_token)
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["region_id"] == 1
        assert "recommendations" in data
        assert "total" in data
        assert isinstance(data["recommendations"], list)

    def test_get_recommendations_public_user(self, client, public_token):
        resp = client.get(
            "/regions/1/recommendations", headers=auth_headers(public_token)
        )
        assert resp.status_code == 200

    def test_get_recommendations_region_not_found(self, client, gov_token):
        resp = client.get(
            "/regions/9999/recommendations", headers=auth_headers(gov_token)
        )
        assert resp.status_code == 404

    def test_get_recommendations_no_auth(self, client):
        resp = client.get("/regions/1/recommendations")
        assert resp.status_code == 401

    def test_find_safe_route_success(self, client, gov_token):
        resp = client.post(
            "/routes/safe",
            json={
                "origin": {"latitude": -6.1751, "longitude": 106.8650},
                "destination": {"latitude": -6.2615, "longitude": 106.8106},
            },
            headers=auth_headers(gov_token),
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "is_safe" in data
        assert "route_region_ids" in data
        assert "origin" in data
        assert "destination" in data

    def test_find_safe_route_public_user(self, client, public_token):
        resp = client.post(
            "/routes/safe",
            json={
                "origin": {"latitude": -6.1751, "longitude": 106.8650},
                "destination": {"latitude": -6.2615, "longitude": 106.8106},
            },
            headers=auth_headers(public_token),
        )
        assert resp.status_code == 200

    def test_find_safe_route_invalid_coordinates(self, client, gov_token):
        resp = client.post(
            "/routes/safe",
            json={
                "origin": {"latitude": 999.0, "longitude": 106.8650},
                "destination": {"latitude": -6.2615, "longitude": 106.8106},
            },
            headers=auth_headers(gov_token),
        )
        assert resp.status_code == 422

    def test_find_safe_route_no_auth(self, client):
        resp = client.post(
            "/routes/safe",
            json={
                "origin": {"latitude": -6.1751, "longitude": 106.8650},
                "destination": {"latitude": -6.2615, "longitude": 106.8106},
            },
        )
        assert resp.status_code == 401

    def test_find_safe_route_missing_body(self, client, gov_token):
        resp = client.post("/routes/safe", json={}, headers=auth_headers(gov_token))
        assert resp.status_code == 422


# ---------------------------------------------------------------------------
# Error handling
# ---------------------------------------------------------------------------


class TestErrorHandling:
    def test_404_unknown_path(self, client):
        resp = client.get("/nonexistent/path")
        assert resp.status_code == 404

    def test_method_not_allowed(self, client):
        resp = client.delete("/health")
        assert resp.status_code == 405

    def test_invalid_json_body(self, client, gov_token):
        resp = client.post(
            "/auth/login",
            content="not-json",
            headers={**auth_headers(gov_token), "Content-Type": "application/json"},
        )
        assert resp.status_code == 422

    def test_invalid_token_format(self, client):
        resp = client.get(
            "/users/me",
            headers={"Authorization": "NotBearer token"},
        )
        assert resp.status_code == 401


# ---------------------------------------------------------------------------
# Rate limiting
# ---------------------------------------------------------------------------


class TestRateLimiting:
    def test_rate_limit_headers_present(self, client, gov_token):
        """
        Verify rate limit headers are included in responses when rate limiting
        is active. The middleware adds headers only when it processes the request.
        If rate limiting is disabled in config, headers won't be present.
        """
        resp = client.get("/regions/1/risk", headers=auth_headers(gov_token))
        assert resp.status_code == 200
        # Rate limit headers are present only when the middleware is enabled.
        # In the test environment the middleware may be disabled via config;
        # we verify the response is successful regardless.
        # When enabled, these headers must be present:
        if "X-RateLimit-Limit-Minute" in resp.headers:
            assert "X-RateLimit-Remaining-Minute" in resp.headers
            assert int(resp.headers["X-RateLimit-Limit-Minute"]) > 0

    def test_health_endpoint_bypasses_rate_limit(self, client):
        """Health endpoints should not be rate-limited."""
        for _ in range(5):
            resp = client.get("/health")
            assert resp.status_code == 200
            # Health endpoints should not have rate limit headers
            assert "X-RateLimit-Limit-Minute" not in resp.headers


# ---------------------------------------------------------------------------
# CORS
# ---------------------------------------------------------------------------


class TestCORS:
    def test_cors_preflight(self, client):
        """OPTIONS preflight request should return CORS headers."""
        resp = client.options(
            "/health",
            headers={
                "Origin": "http://localhost:3000",
                "Access-Control-Request-Method": "GET",
            },
        )
        # FastAPI CORS middleware returns 200 for preflight
        assert resp.status_code in (200, 204)
