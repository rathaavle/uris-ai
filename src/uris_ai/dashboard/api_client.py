"""
API client for URIS-AI Streamlit dashboard.

Provides typed methods to call the FastAPI backend.
All methods return None (or empty structures) on error so the UI
can degrade gracefully without crashing.
"""

from __future__ import annotations

import logging
from datetime import datetime
from typing import Any, Dict, List, Optional

import requests

logger = logging.getLogger(__name__)

# Default backend URL – can be overridden via environment variable
DEFAULT_API_URL = "http://localhost:8000"


class APIClient:
    """Thin HTTP client that wraps the URIS-AI FastAPI backend."""

    def __init__(self, base_url: str = DEFAULT_API_URL, timeout: int = 10) -> None:
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self._token: Optional[str] = None

    # ------------------------------------------------------------------
    # Auth helpers
    # ------------------------------------------------------------------

    def set_token(self, token: str) -> None:
        """Store a JWT access token for subsequent requests."""
        self._token = token

    def clear_token(self) -> None:
        """Remove the stored JWT token (logout)."""
        self._token = None

    @property
    def _headers(self) -> Dict[str, str]:
        headers: Dict[str, str] = {"Content-Type": "application/json"}
        if self._token:
            headers["Authorization"] = f"Bearer {self._token}"
        return headers

    def _get(self, path: str, params: Optional[Dict[str, Any]] = None) -> Optional[Any]:
        """Perform a GET request and return parsed JSON, or None on error."""
        url = f"{self.base_url}{path}"
        try:
            resp = requests.get(url, headers=self._headers, params=params, timeout=self.timeout)
            resp.raise_for_status()
            return resp.json()
        except requests.exceptions.ConnectionError:
            logger.warning("Cannot connect to API at %s", url)
            return None
        except requests.exceptions.Timeout:
            logger.warning("Request timed out: %s", url)
            return None
        except requests.exceptions.HTTPError as exc:
            logger.warning("HTTP error %s for %s: %s", exc.response.status_code, url, exc)
            return None
        except Exception as exc:
            logger.error("Unexpected error calling %s: %s", url, exc)
            return None

    def _post(self, path: str, payload: Dict[str, Any]) -> Optional[Any]:
        """Perform a POST request and return parsed JSON, or None on error."""
        url = f"{self.base_url}{path}"
        try:
            resp = requests.post(
                url, headers=self._headers, json=payload, timeout=self.timeout
            )
            resp.raise_for_status()
            return resp.json()
        except requests.exceptions.ConnectionError:
            logger.warning("Cannot connect to API at %s", url)
            return None
        except requests.exceptions.Timeout:
            logger.warning("Request timed out: %s", url)
            return None
        except requests.exceptions.HTTPError as exc:
            logger.warning("HTTP error %s for %s: %s", exc.response.status_code, url, exc)
            return None
        except Exception as exc:
            logger.error("Unexpected error calling %s: %s", url, exc)
            return None

    # ------------------------------------------------------------------
    # Authentication
    # ------------------------------------------------------------------

    def login(self, username: str, password: str) -> Optional[Dict[str, Any]]:
        """
        Authenticate a user.

        Returns token response dict on success, None on failure.
        """
        return self._post("/auth/login", {"username": username, "password": password})

    def logout(self) -> bool:
        """Log out the current user. Returns True on success."""
        result = self._post("/auth/logout", {})
        self.clear_token()
        return result is not None

    def get_current_user(self) -> Optional[Dict[str, Any]]:
        """Return the current authenticated user's profile."""
        return self._get("/users/me")

    # ------------------------------------------------------------------
    # Risk data
    # ------------------------------------------------------------------

    def get_all_regions_risk(self) -> Optional[Dict[str, Any]]:
        """
        Fetch Urban Risk Scores for all regions.

        Returns AllRegionsRiskResponse dict or None.
        """
        return self._get("/regions/risk")

    def get_region_risk(self, region_id: int) -> Optional[Dict[str, Any]]:
        """Fetch risk score for a single region."""
        return self._get(f"/regions/{region_id}/risk")

    def get_risk_trend(self, region_id: int, hours: int = 24) -> Optional[Dict[str, Any]]:
        """Fetch risk trend for a region over the last *hours* hours."""
        return self._get(f"/regions/{region_id}/risk/trend", params={"hours": hours})

    # ------------------------------------------------------------------
    # Recommendations
    # ------------------------------------------------------------------

    def get_recommendations(self, region_id: int) -> Optional[Dict[str, Any]]:
        """Fetch recommendations for a region."""
        return self._get(f"/regions/{region_id}/recommendations")

    def find_safe_route(
        self,
        origin_lat: float,
        origin_lon: float,
        dest_lat: float,
        dest_lon: float,
    ) -> Optional[Dict[str, Any]]:
        """Request a safe route between two coordinates."""
        payload = {
            "origin": {"latitude": origin_lat, "longitude": origin_lon},
            "destination": {"latitude": dest_lat, "longitude": dest_lon},
        }
        return self._post("/routes/safe", payload)

    # ------------------------------------------------------------------
    # Health
    # ------------------------------------------------------------------

    def health_check(self) -> bool:
        """Return True if the backend is reachable and healthy."""
        result = self._get("/health")
        return result is not None and result.get("status") == "healthy"


# ---------------------------------------------------------------------------
# Mock / demo data helpers (used when backend is unavailable)
# ---------------------------------------------------------------------------

DEMO_REGIONS: List[Dict[str, Any]] = [
    {
        "region_id": 1,
        "region_name": "Penjaringan",
        "latitude": -6.1174,
        "longitude": 106.7942,
        "flood_risk": 82.0,
        "traffic_impact": 75.0,
        "service_access": 60.0,
        "urban_risk_score": 75.5,
        "risk_category": "KRITIS",
        "calculated_at": datetime.now().isoformat(),
    },
    {
        "region_id": 2,
        "region_name": "Pluit",
        "latitude": -6.1244,
        "longitude": 106.7997,
        "flood_risk": 70.0,
        "traffic_impact": 65.0,
        "service_access": 55.0,
        "urban_risk_score": 65.0,
        "risk_category": "TINGGI",
        "calculated_at": datetime.now().isoformat(),
    },
    {
        "region_id": 3,
        "region_name": "Gambir",
        "latitude": -6.1701,
        "longitude": 106.8186,
        "flood_risk": 40.0,
        "traffic_impact": 35.0,
        "service_access": 30.0,
        "urban_risk_score": 37.0,
        "risk_category": "SEDANG",
        "calculated_at": datetime.now().isoformat(),
    },
    {
        "region_id": 4,
        "region_name": "Menteng",
        "latitude": -6.1944,
        "longitude": 106.8294,
        "flood_risk": 20.0,
        "traffic_impact": 15.0,
        "service_access": 10.0,
        "urban_risk_score": 16.5,
        "risk_category": "RENDAH",
        "calculated_at": datetime.now().isoformat(),
    },
    {
        "region_id": 5,
        "region_name": "Cengkareng",
        "latitude": -6.1481,
        "longitude": 106.7397,
        "flood_risk": 55.0,
        "traffic_impact": 50.0,
        "service_access": 45.0,
        "urban_risk_score": 51.5,
        "risk_category": "TINGGI",
        "calculated_at": datetime.now().isoformat(),
    },
    {
        "region_id": 6,
        "region_name": "Kebayoran Baru",
        "latitude": -6.2441,
        "longitude": 106.7971,
        "flood_risk": 15.0,
        "traffic_impact": 20.0,
        "service_access": 12.0,
        "urban_risk_score": 15.6,
        "risk_category": "RENDAH",
        "calculated_at": datetime.now().isoformat(),
    },
]

DEMO_RECOMMENDATIONS: List[Dict[str, Any]] = [
    {
        "id": 1,
        "region_id": 1,
        "type": "alert",
        "description": "Wilayah Penjaringan mengalami risiko banjir kritis. Segera evakuasi warga di zona rawan.",
        "urgency": "Segera",
        "created_at": datetime.now().isoformat(),
        "expires_at": None,
    },
    {
        "id": 2,
        "region_id": 1,
        "type": "route",
        "description": "Gunakan Jl. Pluit Selatan Raya sebagai rute alternatif menuju RS Pluit.",
        "urgency": "Waspada",
        "created_at": datetime.now().isoformat(),
        "expires_at": None,
    },
    {
        "id": 3,
        "region_id": 1,
        "type": "service",
        "description": "RS Pluit berpotensi overload. Pertimbangkan RS Sumber Waras (3.2 km) sebagai alternatif.",
        "urgency": "Waspada",
        "created_at": datetime.now().isoformat(),
        "expires_at": None,
    },
]

DEMO_TREND: List[Dict[str, Any]] = [
    {"date": "2024-01-01T00:00:00", "urban_risk_score": 45.0},
    {"date": "2024-01-01T01:00:00", "urban_risk_score": 50.0},
    {"date": "2024-01-01T02:00:00", "urban_risk_score": 55.0},
    {"date": "2024-01-01T03:00:00", "urban_risk_score": 62.0},
    {"date": "2024-01-01T04:00:00", "urban_risk_score": 70.0},
    {"date": "2024-01-01T05:00:00", "urban_risk_score": 75.5},
]
