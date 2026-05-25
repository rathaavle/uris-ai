"""
Risk router for URIS-AI API.

Provides endpoints for Urban Risk Score data and trends.

Requirements: 4.2, 4.4
"""

import logging
from datetime import datetime, timezone
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from uris_ai.api.dependencies import get_db
from uris_ai.api.schemas import (
    AllRegionsRiskResponse,
    RiskScoreResponse,
    RiskTrendPoint,
    RiskTrendResponse,
)
from uris_ai.models.database import Region, RiskScore
from uris_ai.ml.flood_risk_engine import FloodRiskEngine
from uris_ai.ml.risk_scoring_engine import RiskScoringEngine
from uris_ai.services.cache_service import CacheService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/regions", tags=["Risk"])

# Shared engine instances (stateless, safe to reuse)
_flood_risk_engine = FloodRiskEngine()


def _get_risk_category(score: float) -> str:
    """Convert numeric score to category label."""
    return _flood_risk_engine.get_risk_category(score).value


def _row_to_risk_response(score_row: RiskScore, region_name: Optional[str]) -> RiskScoreResponse:
    """Convert a RiskScore ORM row to a RiskScoreResponse schema."""
    return RiskScoreResponse(
        region_id=score_row.region_id,
        region_name=region_name,
        flood_risk=score_row.flood_risk,
        traffic_impact=score_row.traffic_impact,
        service_access=score_row.service_access,
        urban_risk_score=score_row.urban_risk_score,
        risk_category=_get_risk_category(score_row.urban_risk_score),
        calculated_at=score_row.date,
    )


@router.get(
    "/{region_id}/risk",
    response_model=RiskScoreResponse,
    summary="Skor risiko untuk satu wilayah",
    description="Kembalikan Urban Risk Score terbaru untuk wilayah yang ditentukan.",
)
async def get_region_risk(
    region_id: int,
    db: Session = Depends(get_db),
    cache: CacheService = Depends(lambda: CacheService()),
) -> RiskScoreResponse:
    """
    Get the latest Urban Risk Score for a specific region.

    Requirements: 4.2
    """
    # Try cache first
    cached = cache.get_risk_score(region_id)
    if cached is not None:
        logger.debug(f"Cache hit for risk score region {region_id}")
        return RiskScoreResponse(**cached)

    # Verify region exists
    region = db.query(Region).filter(Region.region_id == region_id).first()
    if region is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Wilayah dengan ID {region_id} tidak ditemukan",
        )

    # Get latest risk score
    latest = (
        db.query(RiskScore)
        .filter(RiskScore.region_id == region_id)
        .order_by(RiskScore.date.desc())
        .first()
    )

    if latest is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Belum ada data risiko untuk wilayah {region_id}",
        )

    response = _row_to_risk_response(latest, region.name)

    # Store in cache
    cache.set_risk_score(region_id, response.model_dump(mode="json"))

    return response


@router.get(
    "/risk",
    response_model=AllRegionsRiskResponse,
    summary="Skor risiko semua wilayah",
    description="Kembalikan Urban Risk Score terbaru untuk semua wilayah.",
)
async def get_all_regions_risk(
    db: Session = Depends(get_db),
    cache: CacheService = Depends(lambda: CacheService()),
) -> AllRegionsRiskResponse:
    """
    Get the latest Urban Risk Score for all regions.

    Requirements: 4.2
    """
    # Try cache first
    cached = cache.get_all_risk_scores()
    if cached is not None:
        logger.debug("Cache hit for all regions risk scores")
        return AllRegionsRiskResponse(**cached)

    # Get all regions
    regions = db.query(Region).all()
    region_map = {r.region_id: r.name for r in regions}

    # Ambil semua risk score terbaru dalam SATU query pakai subquery
    from sqlalchemy import func
    subq = (
        db.query(
            RiskScore.region_id,
            func.max(RiskScore.date).label("max_date")
        )
        .group_by(RiskScore.region_id)
        .subquery()
    )
    latest_scores = (
        db.query(RiskScore)
        .join(subq, (RiskScore.region_id == subq.c.region_id) & (RiskScore.date == subq.c.max_date))
        .all()
    )

    results: List[RiskScoreResponse] = [
        _row_to_risk_response(score, region_map.get(score.region_id))
        for score in latest_scores
    ]

    response = AllRegionsRiskResponse(
        regions=results,
        total=len(results),
        updated_at=datetime.now(timezone.utc),
    )

    # Store in cache
    cache.set_all_risk_scores(response.model_dump(mode="json"))

    return response


@router.get(
    "/{region_id}/risk/trend",
    response_model=RiskTrendResponse,
    summary="Tren risiko wilayah",
    description="Kembalikan tren Urban Risk Score untuk wilayah dalam rentang waktu tertentu.",
)
async def get_region_risk_trend(
    region_id: int,
    hours: int = Query(default=24, ge=1, le=168, description="Rentang waktu dalam jam (1-168)"),
    db: Session = Depends(get_db),
    cache: CacheService = Depends(lambda: CacheService()),
) -> RiskTrendResponse:
    """
    Get the Urban Risk Score trend for a region over the past N hours.

    Requirements: 4.4
    """
    # Try cache first
    cached = cache.get_risk_trend(region_id, hours)
    if cached is not None:
        logger.debug(f"Cache hit for risk trend region {region_id} ({hours}h)")
        return RiskTrendResponse(**cached)

    # Verify region exists
    region = db.query(Region).filter(Region.region_id == region_id).first()
    if region is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Wilayah dengan ID {region_id} tidak ditemukan",
        )

    # Use RiskScoringEngine to get trend data
    engine = RiskScoringEngine(db_session=db)
    trend_points = engine.get_risk_trend(region_id=region_id, hours=hours)

    trend = [
        RiskTrendPoint(date=p.date, urban_risk_score=p.urban_risk_score)
        for p in trend_points
    ]

    response = RiskTrendResponse(
        region_id=region_id,
        region_name=region.name,
        hours=hours,
        trend=trend,
    )

    # Store in cache
    cache.set_risk_trend(region_id, hours, response.model_dump(mode="json"))

    return response
