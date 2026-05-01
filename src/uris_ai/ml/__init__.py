"""
AI/ML Layer for URIS-AI.

This module contains machine learning models and engines for flood risk prediction,
traffic analysis, service accessibility evaluation, risk scoring, and recommendations.
"""

from .flood_risk_engine import (
    FloodRiskEngine,
    RiskCategory,
    FloodHistory,
    WeatherData,
    RegionFeatures,
    FloodRiskPrediction,
    UpdateResult,
)
from .risk_scoring_engine import (
    RiskScoringEngine,
    RiskScorePoint,
)
from .recommendation_engine import (
    RecommendationEngine,
    RecommendationItem,
    RecommendationType,
    RouteRecommendation,
    UrgencyLevel,
    Coordinate,
)

__all__ = [
    "FloodRiskEngine",
    "RiskCategory",
    "FloodHistory",
    "WeatherData",
    "RegionFeatures",
    "FloodRiskPrediction",
    "UpdateResult",
    "RiskScoringEngine",
    "RiskScorePoint",
    "RecommendationEngine",
    "RecommendationItem",
    "RecommendationType",
    "RouteRecommendation",
    "UrgencyLevel",
    "Coordinate",
]
