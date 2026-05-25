"""
Comprehensive End-to-End Integration Tests for URIS-AI.

Tests the full pipeline across all components together, covering complete
user scenarios from requirements 1.1, 2.1, 3.1, 4.1, 5.1, and 6.1.

Requirements: 1.1, 2.1, 3.1, 4.1, 5.1, 6.1
"""

from datetime import datetime, timezone
from typing import Generator
from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from uris_ai.api.main import create_app
from uris_ai.models.database import (
    Base,
    PublicFacility,
    Recommendation,
    Region,
    RiskScore,
    Road,
    User,
)
from uris_ai.models.db_utils import init_database
from uris_ai.services.auth_service import AuthService
from src.uris_ai.ml.flood_risk_engine import (
    FloodHistory,
    FloodRiskEngine,
    FloodRiskPrediction,
    RegionFeatures,
    RiskCategory,
    WeatherData,
)
from src.uris_ai.ml.traffic_analyzer import CongestionLevel, TrafficAnalyzer, TrafficImpact
from src.uris_ai.ml.service_accessibility import AccessibilityReport, ServiceAccessibilityModule
from uris_ai.ml.risk_scoring_engine import RiskScoringEngine
from src.uris_ai.ml.recommendation_engine import (
    Coordinate,
    RecommendationEngine,
    RecommendationItem,
    RouteRecommendation,
    UrgencyLevel,
)
from src.uris_ai.ml.data_preparation import create_synthetic_training_data
from src.uris_ai.ml.model_training import ModelTrainer

pytestmark = pytest.mark.integration
