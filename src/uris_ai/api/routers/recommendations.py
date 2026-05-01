"""
Recommendations router for URIS-AI API.

Provides endpoints for recommendations and safe route finding.

Requirements: 5.1, 5.2
"""

import logging
from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from uris_ai.api.dependencies import get_current_active_user, get_db
from uris_ai.api.schemas import (
    CoordinateInput,
    RecommendationResponse,
    RegionRecommendationsResponse,
    SafeRouteRequest,
    SafeRouteResponse,
)
from uris_ai.models.database import Recommendation, Region, RiskScore, User
from uris_ai.ml.recommendation_engine import Coordinate, RecommendationEngine
from uris_ai.services.cache_service import CacheService

logger = logging.getLogger(__name__)

router = APIRouter(tags=["Recommendations"])


def _build_risk_map(db: Session) -> dict:
    """Build a region_id → urban_risk_score map from the latest DB records."""
    # Subquery: latest risk score date per region
    from sqlalchemy import func

    subq = (
        db.query(
            RiskScore.region_id,
            func.max(RiskScore.date).label("max_date"),
        )
        .group_by(RiskScore.region_id)
        .subquery()
    )

    rows = (
        db.query(RiskScore)
        .join(
            subq,
            (RiskScore.region_id == subq.c.region_id)
            & (RiskScore.date == subq.c.max_date),
        )
        .all()
    )

    return {row.region_id: row.urban_risk_score for row in rows}


@router.get(
    "/regions/{region_id}/recommendations",
    response_model=RegionRecommendationsResponse,
    summary="Rekomendasi untuk wilayah",
    description="Kembalikan daftar rekomendasi aktif untuk wilayah yang ditentukan.",
)
async def get_region_recommendations(
    region_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
    cache: CacheService = Depends(lambda: CacheService()),
) -> RegionRecommendationsResponse:
    """
    Get active recommendations for a specific region.

    Requirements: 5.1
    """
    # Try cache first
    cached = cache.get_recommendations(region_id)
    if cached is not None:
        logger.debug(f"Cache hit for recommendations region {region_id}")
        return RegionRecommendationsResponse(**cached)

    # Verify region exists
    region = db.query(Region).filter(Region.region_id == region_id).first()
    if region is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Wilayah dengan ID {region_id} tidak ditemukan",
        )

    # Get active recommendations from DB
    recs = (
        db.query(Recommendation)
        .filter(
            Recommendation.region_id == region_id,
            Recommendation.is_active == True,
        )
        .order_by(Recommendation.created_at.desc())
        .all()
    )

    rec_responses: List[RecommendationResponse] = [
        RecommendationResponse(
            id=r.id,
            region_id=r.region_id,
            type=r.recommendation_type,
            description=r.description,
            urgency=r.urgency_level,
            created_at=r.created_at,
            expires_at=r.expires_at,
        )
        for r in recs
    ]

    response = RegionRecommendationsResponse(
        region_id=region_id,
        region_name=region.name,
        recommendations=rec_responses,
        total=len(rec_responses),
    )

    # Store in cache
    cache.set_recommendations(region_id, response.model_dump(mode="json"))

    return response


@router.post(
    "/routes/safe",
    response_model=SafeRouteResponse,
    summary="Cari rute aman",
    description=(
        "Temukan rute aman dari titik asal ke tujuan yang menghindari "
        "wilayah dengan risiko Tinggi atau Kritis."
    ),
)
async def find_safe_route(
    request: SafeRouteRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> SafeRouteResponse:
    """
    Find a safe route from origin to destination avoiding high-risk regions.

    Requirements: 5.2
    """
    # Build current risk map
    risk_map = _build_risk_map(db)

    # Initialise engine with current risk data
    engine = RecommendationEngine(db_session=db, risk_map=risk_map)

    origin = Coordinate(
        latitude=request.origin.latitude,
        longitude=request.origin.longitude,
    )
    destination = Coordinate(
        latitude=request.destination.latitude,
        longitude=request.destination.longitude,
    )

    route_result = engine.find_safe_route(origin=origin, destination=destination)

    return SafeRouteResponse(
        origin=CoordinateInput(
            latitude=route_result.origin.latitude,
            longitude=route_result.origin.longitude,
        ),
        destination=CoordinateInput(
            latitude=route_result.destination.latitude,
            longitude=route_result.destination.longitude,
        ),
        is_safe=route_result.is_safe,
        route_region_ids=route_result.route_region_ids,
        avoided_regions=list(route_result.avoided_regions),
        no_safe_route_reason=route_result.no_safe_route_reason,
        estimated_recovery_hours=route_result.estimated_recovery_hours,
    )
