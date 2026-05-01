"""
Pydantic schemas for URIS-AI API request and response models.

All API input/output is validated through these schemas.
Requirements: 6.1, 6.4, 10.2
"""

from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, EmailStr, Field, field_validator


# ---------------------------------------------------------------------------
# Auth schemas
# ---------------------------------------------------------------------------


class LoginRequest(BaseModel):
    """Request body for POST /auth/login."""

    username: str = Field(..., min_length=1, max_length=100, description="Username")
    password: str = Field(..., min_length=1, description="Password")


class TokenResponse(BaseModel):
    """Response body for successful authentication."""

    access_token: str = Field(..., description="JWT access token")
    token_type: str = Field(default="bearer", description="Token type")
    expires_in: int = Field(..., description="Token expiration in seconds")
    role: str = Field(..., description="User role")


class LogoutResponse(BaseModel):
    """Response body for POST /auth/logout."""

    message: str = Field(default="Berhasil logout")


# ---------------------------------------------------------------------------
# User schemas
# ---------------------------------------------------------------------------


class UserResponse(BaseModel):
    """Response body for GET /users/me."""

    id: int
    username: str
    email: str
    role: str
    created_at: datetime
    last_login: Optional[datetime] = None
    is_active: bool

    model_config = {"from_attributes": True}


# ---------------------------------------------------------------------------
# Risk schemas
# ---------------------------------------------------------------------------


class RiskScoreResponse(BaseModel):
    """Risk score data for a single region."""

    region_id: int = Field(..., description="ID wilayah")
    region_name: Optional[str] = Field(None, description="Nama wilayah")
    flood_risk: float = Field(..., ge=0, le=100, description="Skor risiko banjir (0-100)")
    traffic_impact: float = Field(
        ..., ge=0, le=100, description="Skor dampak lalu lintas (0-100)"
    )
    service_access: float = Field(
        ..., ge=0, le=100, description="Skor aksesibilitas layanan (0-100)"
    )
    urban_risk_score: float = Field(
        ..., ge=0, le=100, description="Urban Risk Score terpadu (0-100)"
    )
    risk_category: str = Field(..., description="Kategori risiko: RENDAH/SEDANG/TINGGI/KRITIS")
    calculated_at: datetime = Field(..., description="Waktu perhitungan")

    model_config = {"from_attributes": True}


class AllRegionsRiskResponse(BaseModel):
    """Risk scores for all regions."""

    regions: List[RiskScoreResponse]
    total: int = Field(..., description="Total jumlah wilayah")
    updated_at: datetime = Field(..., description="Waktu pembaruan terakhir")


class RiskTrendPoint(BaseModel):
    """A single point in a risk trend time series."""

    date: datetime
    urban_risk_score: float = Field(..., ge=0, le=100)


class RiskTrendResponse(BaseModel):
    """Risk trend data for a region."""

    region_id: int
    region_name: Optional[str] = None
    hours: int = Field(..., description="Rentang waktu dalam jam")
    trend: List[RiskTrendPoint]


# ---------------------------------------------------------------------------
# Recommendation schemas
# ---------------------------------------------------------------------------


class RecommendationResponse(BaseModel):
    """A single recommendation item."""

    id: Optional[int] = None
    region_id: int
    type: str = Field(..., description="Tipe: route/alert/service")
    description: str
    urgency: str = Field(..., description="Urgensi: Segera/Waspada/Siaga")
    created_at: datetime
    expires_at: Optional[datetime] = None
    metadata: Optional[Dict[str, Any]] = None

    model_config = {"from_attributes": True}


class RegionRecommendationsResponse(BaseModel):
    """All recommendations for a region."""

    region_id: int
    region_name: Optional[str] = None
    recommendations: List[RecommendationResponse]
    total: int


# ---------------------------------------------------------------------------
# Route schemas
# ---------------------------------------------------------------------------


class CoordinateInput(BaseModel):
    """Geographic coordinate input."""

    latitude: float = Field(..., ge=-90, le=90, description="Latitude")
    longitude: float = Field(..., ge=-180, le=180, description="Longitude")


class SafeRouteRequest(BaseModel):
    """Request body for POST /routes/safe."""

    origin: CoordinateInput = Field(..., description="Titik asal")
    destination: CoordinateInput = Field(..., description="Titik tujuan")


class SafeRouteResponse(BaseModel):
    """Response body for POST /routes/safe."""

    origin: CoordinateInput
    destination: CoordinateInput
    is_safe: bool = Field(..., description="Apakah rute aman ditemukan")
    route_region_ids: List[int] = Field(
        default_factory=list, description="Daftar ID wilayah yang dilalui"
    )
    avoided_regions: List[int] = Field(
        default_factory=list, description="Wilayah berisiko tinggi yang dihindari"
    )
    no_safe_route_reason: Optional[str] = Field(
        None, description="Alasan jika tidak ada rute aman"
    )
    estimated_recovery_hours: Optional[float] = Field(
        None, description="Estimasi jam pemulihan"
    )


# ---------------------------------------------------------------------------
# Error schemas
# ---------------------------------------------------------------------------


class ErrorResponse(BaseModel):
    """Standard error response."""

    detail: str
    code: Optional[str] = None
