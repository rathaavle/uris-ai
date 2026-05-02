"""
End-to-end tests for URIS-AI dashboard components.

Tests pure Python logic of each component without calling any st.* functions.
Covers: APIClient, filter logic, map visualizer, risk dashboard helpers,
user interface / RBAC, and demo data structure.

Requirements: 6.1, 6.2, 6.6
"""

from __future__ import annotations

import sys
from typing import Any, Dict, List
from unittest.mock import MagicMock, Mock, patch

import pytest
import requests

# ---------------------------------------------------------------------------
# Stub out streamlit before any dashboard module is imported so that
# modules that do `import streamlit as st` at module level don't fail.
# ---------------------------------------------------------------------------

_st_stub = MagicMock()
_st_stub.session_state = {}
sys.modules.setdefault("streamlit", _st_stub)
sys.modules.setdefault("streamlit_folium", MagicMock())

# Now safe to import dashboard modules
from uris_ai.dashboard.api_client import (  # noqa: E402
    APIClient,
    DEMO_REGIONS,
    DEMO_RECOMMENDATIONS,
    DEMO_TREND,
)
from uris_ai.dashboard.components.filters import (  # noqa: E402
    RISK_CATEGORIES,
    apply_risk_category_filter,
    get_filter_values,
)
from uris_ai.dashboard.components.map_visualizer import (  # noqa: E402
    RISK_COLORS,
    _urs_to_category,
    _urs_to_color,
    build_risk_map,
)
from uris_ai.dashboard.components.risk_dashboard import (  # noqa: E402
    _build_trend_chart,
    _build_urs_gauge,
    _urs_to_category as risk_urs_to_category,
)
from uris_ai.dashboard.components.user_interface import (  # noqa: E402
    ROLES,
    can_access_page,
)


# ===========================================================================
# Helpers
# ===========================================================================


def _make_response(json_data: Any, status_code: int = 200) -> Mock:
    """Build a mock requests.Response."""
    resp = Mock()
    resp.status_code = status_code
    resp.json.return_value = json_data
    if status_code >= 400:
        http_err = requests.exceptions.HTTPError(response=resp)
        resp.raise_for_status.side_effect = http_err
    else:
        resp.raise_for_status.return_value = None
    return resp


# ===========================================================================
# Fixtures
# ===========================================================================


@pytest.fixture()
def api_client() -> APIClient:
    """Return an APIClient pointed at a dummy base URL."""
    return APIClient(base_url="http://testserver", timeout=5)


@pytest.fixture()
def sample_regions() -> List[Dict[str, Any]]:
    """Return a small list of region dicts for filter / map tests."""
    return [
        {
            "region_id": 1,
            "region_name": "Alpha",
            "latitude": -6.1,
            "longitude": 106.8,
            "urban_risk_score": 20.0,
            "risk_category": "RENDAH",
        },
        {
            "region_id": 2,
            "region_name": "Beta",
            "latitude": -6.2,
            "longitude": 106.9,
            "urban_risk_score": 40.0,
            "risk_category": "SEDANG",
        },
        {
            "region_id": 3,
            "region_name": "Gamma",
            "latitude": -6.3,
            "longitude": 107.0,
            "urban_risk_score": 60.0,
            "risk_category": "TINGGI",
        },
        {
            "region_id": 4,
            "region_name": "Delta",
            "latitude": -6.4,
            "longitude": 107.1,
            "urban_risk_score": 80.0,
            "risk_category": "KRITIS",
        },
    ]


@pytest.fixture()
def clean_session_state():
    """Provide a clean, isolated session_state dict for each test."""
    state: Dict[str, Any] = {}
    with patch(
        "uris_ai.dashboard.components.user_interface.st.session_state", state
    ):
        yield state


# ===========================================================================
# 1. APIClient tests
# ===========================================================================


class TestAPIClientLogin:
    """Tests for APIClient.login()."""

    def test_api_client_login_success(self, api_client: APIClient) -> None:
        """POST /auth/login returns a token dict on success (HTTP 200)."""
        payload = {"access_token": "tok123", "token_type": "bearer", "role": "government"}
        with patch("requests.post", return_value=_make_response(payload, 200)):
            result = api_client.login("admin", "secret")
        assert result is not None
        assert result["access_token"] == "tok123"
        assert result["role"] == "government"

    def test_api_client_login_failure(self, api_client: APIClient) -> None:
        """POST /auth/login returns None when the server responds with HTTP 401."""
        with patch(
            "requests.post",
            return_value=_make_response({"detail": "Incorrect credentials"}, 401),
        ):
            result = api_client.login("bad_user", "wrong_pass")
        assert result is None


class TestAPIClientRiskEndpoints:
    """Tests for risk-data endpoints."""

    def test_api_client_get_all_regions_risk(self, api_client: APIClient) -> None:
        """GET /regions/risk returns the regions payload."""
        payload = {"regions": [{"region_id": 1, "urban_risk_score": 55.0}]}
        with patch("requests.get", return_value=_make_response(payload)):
            result = api_client.get_all_regions_risk()
        assert result is not None
        assert "regions" in result
        assert result["regions"][0]["region_id"] == 1

    def test_api_client_get_region_risk(self, api_client: APIClient) -> None:
        """GET /regions/1/risk returns a single region dict."""
        payload = {"region_id": 1, "urban_risk_score": 72.0, "risk_category": "TINGGI"}
        with patch("requests.get", return_value=_make_response(payload)):
            result = api_client.get_region_risk(1)
        assert result is not None
        assert result["region_id"] == 1
        assert result["risk_category"] == "TINGGI"

    def test_api_client_get_risk_trend(self, api_client: APIClient) -> None:
        """GET /regions/1/risk/trend returns a trend payload."""
        payload = {
            "region_id": 1,
            "trend": [
                {"date": "2024-01-01T00:00:00", "urban_risk_score": 45.0},
                {"date": "2024-01-01T01:00:00", "urban_risk_score": 50.0},
            ],
        }
        with patch("requests.get", return_value=_make_response(payload)):
            result = api_client.get_risk_trend(1, hours=24)
        assert result is not None
        assert "trend" in result
        assert len(result["trend"]) == 2

    def test_api_client_get_recommendations(self, api_client: APIClient) -> None:
        """GET /regions/1/recommendations returns a recommendations payload."""
        payload = {
            "region_id": 1,
            "recommendations": [{"id": 1, "urgency": "Segera", "description": "Evakuasi!"}],
        }
        with patch("requests.get", return_value=_make_response(payload)):
            result = api_client.get_recommendations(1)
        assert result is not None
        assert "recommendations" in result
        assert result["recommendations"][0]["urgency"] == "Segera"

    def test_api_client_find_safe_route(self, api_client: APIClient) -> None:
        """POST /routes/safe returns a route result."""
        payload = {
            "is_safe": True,
            "route_region_ids": [3, 4],
            "avoided_regions": [1, 2],
            "origin": {"latitude": -6.1, "longitude": 106.8},
            "destination": {"latitude": -6.2, "longitude": 106.9},
        }
        with patch("requests.post", return_value=_make_response(payload)):
            result = api_client.find_safe_route(-6.1, 106.8, -6.2, 106.9)
        assert result is not None
        assert result["is_safe"] is True
        assert 1 in result["avoided_regions"]


class TestAPIClientErrorHandling:
    """Tests for graceful error handling in APIClient."""

    def test_api_client_connection_error(self, api_client: APIClient) -> None:
        """Returns None when a ConnectionError is raised (backend unreachable)."""
        with patch(
            "requests.get", side_effect=requests.exceptions.ConnectionError("unreachable")
        ):
            result = api_client.get_all_regions_risk()
        assert result is None

    def test_api_client_health_check_healthy(self, api_client: APIClient) -> None:
        """GET /health returns True when the backend reports status=healthy."""
        payload = {"status": "healthy", "version": "1.0.0"}
        with patch("requests.get", return_value=_make_response(payload)):
            assert api_client.health_check() is True

    def test_api_client_health_check_unhealthy(self, api_client: APIClient) -> None:
        """health_check() returns False when the request raises a ConnectionError."""
        with patch(
            "requests.get", side_effect=requests.exceptions.ConnectionError("down")
        ):
            assert api_client.health_check() is False


# ===========================================================================
# 2. Filter logic tests
# ===========================================================================


class TestApplyRiskCategoryFilter:
    """Tests for apply_risk_category_filter()."""

    def test_apply_risk_category_filter_all(
        self, sample_regions: List[Dict[str, Any]]
    ) -> None:
        """Returns all regions when all four categories are selected."""
        result = apply_risk_category_filter(sample_regions, list(RISK_CATEGORIES))
        assert len(result) == len(sample_regions)

    def test_apply_risk_category_filter_single(
        self, sample_regions: List[Dict[str, Any]]
    ) -> None:
        """Returns only regions matching the single selected category."""
        result = apply_risk_category_filter(sample_regions, ["TINGGI"])
        assert all(r["risk_category"] == "TINGGI" for r in result)
        assert len(result) == 1

    def test_apply_risk_category_filter_empty(
        self, sample_regions: List[Dict[str, Any]]
    ) -> None:
        """Returns all regions when the selected_categories list is empty."""
        result = apply_risk_category_filter(sample_regions, [])
        assert len(result) == len(sample_regions)

    def test_apply_risk_category_filter_multiple(
        self, sample_regions: List[Dict[str, Any]]
    ) -> None:
        """Returns only regions whose category is in the selected set."""
        result = apply_risk_category_filter(sample_regions, ["RENDAH", "KRITIS"])
        categories = {r["risk_category"] for r in result}
        assert categories == {"RENDAH", "KRITIS"}
        assert len(result) == 2


# ===========================================================================
# 3. Map visualizer tests
# ===========================================================================


class TestBuildRiskMap:
    """Tests for build_risk_map()."""

    def test_build_risk_map_returns_folium_map(
        self, sample_regions: List[Dict[str, Any]]
    ) -> None:
        """build_risk_map() returns a folium.Map instance."""
        import folium

        m = build_risk_map(sample_regions)
        assert isinstance(m, folium.Map)

    def test_build_risk_map_with_regions(
        self, sample_regions: List[Dict[str, Any]]
    ) -> None:
        """Map contains CircleMarker children for each region with lat/lon."""
        import folium

        m = build_risk_map(sample_regions)
        markers = [
            child
            for child in m._children.values()
            if isinstance(child, folium.CircleMarker)
        ]
        assert len(markers) == len(sample_regions)

    def test_build_risk_map_empty_regions(self) -> None:
        """build_risk_map() handles an empty regions list without error."""
        import folium

        m = build_risk_map([])
        assert isinstance(m, folium.Map)

    def test_build_risk_map_skips_regions_without_coordinates(self) -> None:
        """Regions missing lat/lon are silently skipped."""
        import folium

        regions = [
            {"region_id": 1, "urban_risk_score": 30.0},  # no lat/lon
            {
                "region_id": 2,
                "latitude": -6.2,
                "longitude": 106.9,
                "urban_risk_score": 40.0,
            },
        ]
        m = build_risk_map(regions)
        markers = [
            child
            for child in m._children.values()
            if isinstance(child, folium.CircleMarker)
        ]
        assert len(markers) == 1


class TestUrsToColor:
    """Tests for _urs_to_color()."""

    def test_urs_to_color_rendah(self) -> None:
        """URS 0–25 maps to the RENDAH (green) colour."""
        assert _urs_to_color(0) == RISK_COLORS["RENDAH"]
        assert _urs_to_color(25) == RISK_COLORS["RENDAH"]

    def test_urs_to_color_sedang(self) -> None:
        """URS 26–50 maps to the SEDANG (orange) colour."""
        assert _urs_to_color(26) == RISK_COLORS["SEDANG"]
        assert _urs_to_color(50) == RISK_COLORS["SEDANG"]

    def test_urs_to_color_tinggi(self) -> None:
        """URS 51–75 maps to the TINGGI (red) colour."""
        assert _urs_to_color(51) == RISK_COLORS["TINGGI"]
        assert _urs_to_color(75) == RISK_COLORS["TINGGI"]

    def test_urs_to_color_kritis(self) -> None:
        """URS 76–100 maps to the KRITIS (purple) colour."""
        assert _urs_to_color(76) == RISK_COLORS["KRITIS"]
        assert _urs_to_color(100) == RISK_COLORS["KRITIS"]


class TestUrsToCategoryBoundaries:
    """Tests for _urs_to_category() boundary values."""

    @pytest.mark.parametrize(
        "urs, expected",
        [
            (0, "RENDAH"),
            (25, "RENDAH"),
            (26, "SEDANG"),
            (50, "SEDANG"),
            (51, "TINGGI"),
            (75, "TINGGI"),
            (76, "KRITIS"),
            (100, "KRITIS"),
        ],
    )
    def test_urs_to_category_boundaries(self, urs: float, expected: str) -> None:
        """_urs_to_category() returns the correct category at every boundary value."""
        assert _urs_to_category(urs) == expected


# ===========================================================================
# 4. Risk dashboard tests
# ===========================================================================


class TestBuildUrsGauge:
    """Tests for _build_urs_gauge()."""

    def test_build_urs_gauge_returns_figure(self) -> None:
        """_build_urs_gauge() returns a plotly Figure."""
        import plotly.graph_objects as go

        fig = _build_urs_gauge(55.0, "TINGGI")
        assert isinstance(fig, go.Figure)

    def test_build_urs_gauge_value_range(self) -> None:
        """The gauge indicator value matches the URS passed in."""
        for urs in [0.0, 25.0, 50.0, 75.0, 100.0]:
            fig = _build_urs_gauge(urs, risk_urs_to_category(urs))
            indicator = fig.data[0]
            assert indicator.value == urs


class TestBuildTrendChart:
    """Tests for _build_trend_chart()."""

    def test_build_trend_chart_with_data(self) -> None:
        """Returns a Figure with at least one trace when trend data is provided."""
        import plotly.graph_objects as go

        trend = [
            {"date": "2024-01-01T00:00:00", "urban_risk_score": 45.0},
            {"date": "2024-01-01T01:00:00", "urban_risk_score": 55.0},
        ]
        fig = _build_trend_chart(trend, "Test Region")
        assert isinstance(fig, go.Figure)
        assert len(fig.data) >= 1

    def test_build_trend_chart_empty(self) -> None:
        """Returns a Figure (with no scatter traces) when trend_data is empty."""
        import plotly.graph_objects as go

        fig = _build_trend_chart([], "Empty Region")
        assert isinstance(fig, go.Figure)
        # No scatter traces for empty data
        scatter_traces = [t for t in fig.data if hasattr(t, "x") and t.x]
        assert len(scatter_traces) == 0


# ===========================================================================
# 5. User interface / RBAC tests
# ===========================================================================


class TestCanAccessPage:
    """Tests for can_access_page() with various session states."""

    def test_can_access_page_unauthenticated(self, clean_session_state: Dict) -> None:
        """Unauthenticated users (role=None) can only access 'Peta Risiko'."""
        clean_session_state["role"] = None
        assert can_access_page("Peta Risiko") is True
        assert can_access_page("Rekomendasi") is False
        assert can_access_page("Analitik") is False

    def test_can_access_page_public_role(self, clean_session_state: Dict) -> None:
        """Public role can access map and route navigation only."""
        clean_session_state["role"] = "public"
        assert can_access_page("Peta Risiko") is True
        assert can_access_page("Navigasi Rute") is True
        assert can_access_page("Rekomendasi") is False
        assert can_access_page("Analitik") is False

    def test_can_access_page_facility_manager(self, clean_session_state: Dict) -> None:
        """Facility manager can access recommendations but not analytics."""
        clean_session_state["role"] = "facility_manager"
        assert can_access_page("Peta Risiko") is True
        assert can_access_page("Rekomendasi") is True
        assert can_access_page("Detail Wilayah") is True
        assert can_access_page("Analitik") is False

    def test_can_access_page_government(self, clean_session_state: Dict) -> None:
        """Government role can access all pages including analytics."""
        clean_session_state["role"] = "government"
        for page in ["Peta Risiko", "Detail Wilayah", "Rekomendasi", "Analitik", "Navigasi Rute"]:
            assert can_access_page(page) is True

    def test_roles_have_three_entries(self) -> None:
        """ROLES dict contains exactly 3 role keys."""
        assert len(ROLES) == 3
        assert set(ROLES.keys()) == {"public", "facility_manager", "government"}

    def test_public_role_cannot_access_analytics(self, clean_session_state: Dict) -> None:
        """'Analitik' is a government-only page; public role must be blocked."""
        clean_session_state["role"] = "public"
        assert can_access_page("Analitik") is False


# ===========================================================================
# 6. Demo data structure tests
# ===========================================================================


class TestDemoDataStructure:
    """Tests that demo data constants have the expected shape."""

    REQUIRED_REGION_FIELDS = {
        "region_id",
        "region_name",
        "latitude",
        "longitude",
        "flood_risk",
        "traffic_impact",
        "service_access",
        "urban_risk_score",
        "risk_category",
        "calculated_at",
    }

    REQUIRED_RECOMMENDATION_FIELDS = {
        "id",
        "region_id",
        "type",
        "description",
        "urgency",
        "created_at",
    }

    REQUIRED_TREND_FIELDS = {"date", "urban_risk_score"}

    def test_demo_regions_structure(self) -> None:
        """All demo regions contain the required fields with non-None values."""
        assert len(DEMO_REGIONS) > 0, "DEMO_REGIONS must not be empty"
        for region in DEMO_REGIONS:
            missing = self.REQUIRED_REGION_FIELDS - region.keys()
            assert not missing, (
                f"Region {region.get('region_id')} missing fields: {missing}"
            )
            assert region["risk_category"] in RISK_CATEGORIES, (
                f"Invalid risk_category '{region['risk_category']}' in region "
                f"{region['region_id']}"
            )

    def test_demo_recommendations_structure(self) -> None:
        """All demo recommendations contain the required fields."""
        assert len(DEMO_RECOMMENDATIONS) > 0, "DEMO_RECOMMENDATIONS must not be empty"
        for rec in DEMO_RECOMMENDATIONS:
            missing = self.REQUIRED_RECOMMENDATION_FIELDS - rec.keys()
            assert not missing, (
                f"Recommendation {rec.get('id')} missing fields: {missing}"
            )

    def test_demo_trend_structure(self) -> None:
        """All demo trend points have 'date' and 'urban_risk_score' fields."""
        assert len(DEMO_TREND) > 0, "DEMO_TREND must not be empty"
        for point in DEMO_TREND:
            missing = self.REQUIRED_TREND_FIELDS - point.keys()
            assert not missing, f"Trend point missing fields: {missing}"
            score = point["urban_risk_score"]
            assert 0.0 <= float(score) <= 100.0, (
                f"urban_risk_score {score} is out of range [0, 100]"
            )
