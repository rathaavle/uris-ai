"""
Unit tests for Recommendation Engine.

This module contains unit tests for the Recommendation_Engine component,
testing recommendation generation, safe route finding, and urgency classification.

Requirements: 5.1, 5.2, 5.4, 5.5
"""

import pytest
from datetime import datetime, timezone
from unittest.mock import Mock, MagicMock

from src.uris_ai.ml.recommendation_engine import (
    RecommendationEngine,
    RecommendationItem,
    RecommendationType,
    RouteRecommendation,
    UrgencyLevel,
    Coordinate,
    RISK_SCORE_THRESHOLD,
)
from src.uris_ai.ml.flood_risk_engine import RiskCategory
from src.uris_ai.ml.service_accessibility import AccessibilityReport
from src.uris_ai.models.database import Region


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def engine():
    """RecommendationEngine with no DB session."""
    return RecommendationEngine()


@pytest.fixture
def engine_with_risk_map():
    """RecommendationEngine pre-loaded with a simple risk map."""
    risk_map = {
        1: 20.0,   # RENDAH
        2: 40.0,   # SEDANG
        3: 60.0,   # TINGGI  (blocked)
        4: 85.0,   # KRITIS  (blocked)
        5: 30.0,   # SEDANG
    }
    return RecommendationEngine(risk_map=risk_map)


@pytest.fixture
def simple_graph():
    """Simple adjacency graph: 1-2-5 (safe chain), 3 and 4 are blocked."""
    return {
        1: [2, 3],
        2: [1, 5, 3],
        3: [1, 2, 4],
        4: [3],
        5: [2],
    }


@pytest.fixture
def simple_coords():
    """Coordinates for the simple graph."""
    return {
        1: Coordinate(latitude=-6.10, longitude=106.80),
        2: Coordinate(latitude=-6.20, longitude=106.90),
        3: Coordinate(latitude=-6.30, longitude=107.00),
        4: Coordinate(latitude=-6.40, longitude=107.10),
        5: Coordinate(latitude=-6.25, longitude=106.95),
    }


@pytest.fixture
def sample_accessibility_report():
    """Sample AccessibilityReport with overload warnings."""
    return AccessibilityReport(
        region_id=1,
        affected_facilities=[10, 11],
        alternative_facilities={10: [20, 21], 11: [22]},
        overload_warnings=[20],
        timestamp=datetime.now(timezone.utc),
    )


# ---------------------------------------------------------------------------
# Tests: generate_recommendations
# ---------------------------------------------------------------------------

class TestGenerateRecommendations:
    """Unit tests for generate_recommendations method."""

    def test_no_recommendations_below_threshold(self, engine):
        """
        No recommendations generated when URS <= threshold (70).

        Requirements: 5.1
        """
        result = engine.generate_recommendations(
            region_id=1,
            urban_risk_score=RISK_SCORE_THRESHOLD,
        )
        assert result == []

    def test_no_recommendations_well_below_threshold(self, engine):
        """
        No recommendations for low-risk regions.

        Requirements: 5.1
        """
        result = engine.generate_recommendations(
            region_id=1,
            urban_risk_score=30.0,
        )
        assert result == []

    def test_recommendations_generated_above_threshold(self, engine):
        """
        At least one recommendation generated when URS > 70.

        Requirements: 5.1
        """
        result = engine.generate_recommendations(
            region_id=1,
            urban_risk_score=75.0,
        )
        assert len(result) >= 1

    def test_alert_recommendation_always_present_above_threshold(self, engine):
        """
        An ALERT recommendation is always generated when URS > threshold.

        Requirements: 5.1
        """
        result = engine.generate_recommendations(
            region_id=1,
            urban_risk_score=80.0,
        )
        types = [r.type for r in result]
        assert RecommendationType.ALERT in types

    def test_service_recommendation_when_overload_warnings(
        self, engine, sample_accessibility_report
    ):
        """
        A SERVICE recommendation is generated when there are overload warnings.

        Requirements: 5.3
        """
        result = engine.generate_recommendations(
            region_id=1,
            urban_risk_score=80.0,
            accessibility_report=sample_accessibility_report,
        )
        types = [r.type for r in result]
        assert RecommendationType.SERVICE in types

    def test_no_service_recommendation_without_overload(self, engine):
        """
        No SERVICE recommendation when there are no overload warnings.

        Requirements: 5.3
        """
        report = AccessibilityReport(
            region_id=1,
            affected_facilities=[10],
            alternative_facilities={10: [20]},
            overload_warnings=[],  # no overloads
            timestamp=datetime.now(timezone.utc),
        )
        result = engine.generate_recommendations(
            region_id=1,
            urban_risk_score=80.0,
            accessibility_report=report,
        )
        types = [r.type for r in result]
        assert RecommendationType.SERVICE not in types

    def test_route_recommendation_for_critical_risk(self, engine):
        """
        A ROUTE recommendation is generated for KRITIS (score > 75).

        Requirements: 5.1
        """
        result = engine.generate_recommendations(
            region_id=1,
            urban_risk_score=90.0,
        )
        types = [r.type for r in result]
        assert RecommendationType.ROUTE in types

    def test_no_route_recommendation_for_high_risk_below_critical(self, engine):
        """
        No ROUTE recommendation for TINGGI risk (score 71-75).

        Requirements: 5.1
        """
        result = engine.generate_recommendations(
            region_id=1,
            urban_risk_score=73.0,
        )
        types = [r.type for r in result]
        assert RecommendationType.ROUTE not in types

    def test_recommendation_region_id_matches(self, engine):
        """
        All recommendations reference the correct region_id.

        Requirements: 5.1
        """
        region_id = 42
        result = engine.generate_recommendations(
            region_id=region_id,
            urban_risk_score=80.0,
        )
        for rec in result:
            assert rec.region_id == region_id

    def test_recommendation_has_description(self, engine):
        """
        All recommendations have a non-empty description.

        Requirements: 5.1
        """
        result = engine.generate_recommendations(
            region_id=1,
            urban_risk_score=80.0,
        )
        for rec in result:
            assert isinstance(rec.description, str)
            assert len(rec.description) > 0

    def test_recommendation_has_urgency(self, engine):
        """
        All recommendations have a valid urgency level.

        Requirements: 5.1
        """
        result = engine.generate_recommendations(
            region_id=1,
            urban_risk_score=80.0,
        )
        for rec in result:
            assert rec.urgency in UrgencyLevel

    def test_recommendation_has_timestamps(self, engine):
        """
        All recommendations have created_at and expires_at timestamps.

        Requirements: 5.1
        """
        result = engine.generate_recommendations(
            region_id=1,
            urban_risk_score=80.0,
        )
        for rec in result:
            assert isinstance(rec.created_at, datetime)
            assert rec.expires_at is None or isinstance(rec.expires_at, datetime)

    def test_invalid_risk_score_raises(self, engine):
        """
        Invalid urban_risk_score raises ValueError.

        Requirements: 5.1
        """
        with pytest.raises(ValueError):
            engine.generate_recommendations(region_id=1, urban_risk_score=-1.0)

        with pytest.raises(ValueError):
            engine.generate_recommendations(region_id=1, urban_risk_score=101.0)

    def test_urgency_segera_for_extreme_critical(self, engine):
        """
        Extreme KRITIS score (> 90) produces SEGERA urgency.

        Requirements: 5.4
        """
        result = engine.generate_recommendations(
            region_id=1,
            urban_risk_score=95.0,
        )
        alert_recs = [r for r in result if r.type == RecommendationType.ALERT]
        assert len(alert_recs) >= 1
        assert alert_recs[0].urgency == UrgencyLevel.SEGERA

    def test_urgency_waspada_for_kritis(self, engine):
        """
        KRITIS score (76-90) produces WASPADA urgency.

        Requirements: 5.4
        """
        result = engine.generate_recommendations(
            region_id=1,
            urban_risk_score=80.0,
        )
        alert_recs = [r for r in result if r.type == RecommendationType.ALERT]
        assert len(alert_recs) >= 1
        assert alert_recs[0].urgency == UrgencyLevel.WASPADA

    def test_urgency_siaga_for_tinggi(self, engine):
        """
        TINGGI score (71-75) produces SIAGA urgency.

        Requirements: 5.4
        """
        result = engine.generate_recommendations(
            region_id=1,
            urban_risk_score=73.0,
        )
        alert_recs = [r for r in result if r.type == RecommendationType.ALERT]
        assert len(alert_recs) >= 1
        assert alert_recs[0].urgency == UrgencyLevel.SIAGA


# ---------------------------------------------------------------------------
# Tests: find_safe_route
# ---------------------------------------------------------------------------

class TestFindSafeRoute:
    """Unit tests for find_safe_route method."""

    def test_safe_route_found_between_safe_regions(
        self, engine_with_risk_map, simple_graph, simple_coords
    ):
        """
        A safe route is found when origin and destination are safe regions
        connected through safe intermediate regions.

        Requirements: 5.2
        """
        result = engine_with_risk_map.find_safe_route(
            origin=simple_coords[1],
            destination=simple_coords[5],
            region_graph=simple_graph,
            region_coordinates=simple_coords,
        )

        assert result.is_safe is True
        assert len(result.route_region_ids) >= 1

    def test_safe_route_avoids_high_risk_regions(
        self, engine_with_risk_map, simple_graph, simple_coords
    ):
        """
        The returned safe route does not pass through TINGGI or KRITIS regions.

        Requirements: 5.2
        """
        result = engine_with_risk_map.find_safe_route(
            origin=simple_coords[1],
            destination=simple_coords[5],
            region_graph=simple_graph,
            region_coordinates=simple_coords,
        )

        if result.is_safe:
            for region_id in result.route_region_ids:
                score = engine_with_risk_map._risk_map.get(region_id, 0.0)
                category = engine_with_risk_map._score_to_category(score)
                assert category not in {RiskCategory.TINGGI, RiskCategory.KRITIS}, (
                    f"Route passes through high-risk region {region_id} "
                    f"(score={score}, category={category.value})"
                )

    def test_no_safe_route_when_destination_blocked(self, simple_coords):
        """
        Returns is_safe=False when destination region is high-risk.

        Requirements: 5.2
        """
        risk_map = {1: 20.0, 2: 85.0}  # destination (2) is KRITIS
        graph = {1: [2], 2: [1]}
        engine = RecommendationEngine(risk_map=risk_map)

        result = engine.find_safe_route(
            origin=simple_coords[1],
            destination=simple_coords[2],
            region_graph=graph,
            region_coordinates={
                1: simple_coords[1],
                2: simple_coords[2],
            },
        )

        assert result.is_safe is False

    def test_no_safe_route_provides_reason(self):
        """
        When no safe route exists, a non-empty reason is provided.

        Requirements: 5.5
        """
        risk_map = {1: 80.0, 2: 85.0}
        graph = {1: [2], 2: [1]}
        coords = {
            1: Coordinate(latitude=-6.1, longitude=106.8),
            2: Coordinate(latitude=-6.2, longitude=106.9),
        }
        engine = RecommendationEngine(risk_map=risk_map)

        result = engine.find_safe_route(
            origin=coords[1],
            destination=coords[2],
            region_graph=graph,
            region_coordinates=coords,
        )

        assert result.is_safe is False
        assert result.no_safe_route_reason is not None
        assert len(result.no_safe_route_reason) > 0

    def test_route_result_contains_origin_and_destination_regions(
        self, engine_with_risk_map, simple_graph, simple_coords
    ):
        """
        A safe route starts at the origin region and ends at the destination region.

        Requirements: 5.2
        """
        result = engine_with_risk_map.find_safe_route(
            origin=simple_coords[1],
            destination=simple_coords[5],
            region_graph=simple_graph,
            region_coordinates=simple_coords,
        )

        if result.is_safe and len(result.route_region_ids) > 0:
            assert result.route_region_ids[0] == 1
            assert result.route_region_ids[-1] == 5

    def test_empty_graph_returns_unsafe(self):
        """
        An empty region graph returns is_safe=False with an explanation.

        Requirements: 5.2, 5.5
        """
        engine = RecommendationEngine(risk_map={})

        result = engine.find_safe_route(
            origin=Coordinate(latitude=-6.1, longitude=106.8),
            destination=Coordinate(latitude=-6.2, longitude=106.9),
            region_graph={},
            region_coordinates={},
        )

        assert result.is_safe is False
        assert result.no_safe_route_reason is not None

    def test_same_origin_destination_safe(self):
        """
        Same origin and destination in a safe region returns a single-region route.

        Requirements: 5.2
        """
        risk_map = {1: 20.0}
        graph = {1: []}
        coords = {1: Coordinate(latitude=-6.2, longitude=106.8)}
        engine = RecommendationEngine(risk_map=risk_map)

        result = engine.find_safe_route(
            origin=coords[1],
            destination=coords[1],
            region_graph=graph,
            region_coordinates=coords,
        )

        assert result.is_safe is True
        assert result.route_region_ids == [1]

    def test_route_result_is_route_recommendation_type(
        self, engine_with_risk_map, simple_graph, simple_coords
    ):
        """
        find_safe_route always returns a RouteRecommendation instance.

        Requirements: 5.2
        """
        result = engine_with_risk_map.find_safe_route(
            origin=simple_coords[1],
            destination=simple_coords[5],
            region_graph=simple_graph,
            region_coordinates=simple_coords,
        )
        assert isinstance(result, RouteRecommendation)

    def test_avoided_regions_populated_in_safe_route(
        self, engine_with_risk_map, simple_graph, simple_coords
    ):
        """
        The avoided_regions set is populated with high-risk region IDs.

        Requirements: 5.2
        """
        result = engine_with_risk_map.find_safe_route(
            origin=simple_coords[1],
            destination=simple_coords[5],
            region_graph=simple_graph,
            region_coordinates=simple_coords,
        )

        # Regions 3 (TINGGI) and 4 (KRITIS) should be in avoided_regions
        assert 3 in result.avoided_regions
        assert 4 in result.avoided_regions

    def test_update_risk_map(self):
        """
        update_risk_map correctly updates the internal risk map.

        Requirements: 5.2
        """
        engine = RecommendationEngine(risk_map={1: 20.0})
        assert engine._risk_map == {1: 20.0}

        engine.update_risk_map({1: 85.0, 2: 30.0})
        assert engine._risk_map == {1: 85.0, 2: 30.0}


# ---------------------------------------------------------------------------
# Tests: classify_urgency
# ---------------------------------------------------------------------------

class TestClassifyUrgency:
    """Unit tests for classify_urgency method."""

    def test_zero_hours_is_segera(self, engine):
        """0 hours → SEGERA. Requirements: 5.4"""
        assert engine.classify_urgency(0.0) == UrgencyLevel.SEGERA

    def test_one_hour_is_segera(self, engine):
        """1 hour (inclusive) → SEGERA. Requirements: 5.4"""
        assert engine.classify_urgency(1.0) == UrgencyLevel.SEGERA

    def test_just_above_one_hour_is_waspada(self, engine):
        """Just above 1 hour → WASPADA. Requirements: 5.4"""
        assert engine.classify_urgency(1.001) == UrgencyLevel.WASPADA

    def test_three_hours_is_waspada(self, engine):
        """3 hours → WASPADA. Requirements: 5.4"""
        assert engine.classify_urgency(3.0) == UrgencyLevel.WASPADA

    def test_six_hours_is_waspada(self, engine):
        """6 hours (inclusive) → WASPADA. Requirements: 5.4"""
        assert engine.classify_urgency(6.0) == UrgencyLevel.WASPADA

    def test_just_above_six_hours_is_siaga(self, engine):
        """Just above 6 hours → SIAGA. Requirements: 5.4"""
        assert engine.classify_urgency(6.001) == UrgencyLevel.SIAGA

    def test_twelve_hours_is_siaga(self, engine):
        """12 hours → SIAGA. Requirements: 5.4"""
        assert engine.classify_urgency(12.0) == UrgencyLevel.SIAGA

    def test_twenty_four_hours_is_siaga(self, engine):
        """24 hours → SIAGA. Requirements: 5.4"""
        assert engine.classify_urgency(24.0) == UrgencyLevel.SIAGA

    def test_beyond_twenty_four_hours_is_siaga(self, engine):
        """Beyond 24 hours → SIAGA. Requirements: 5.4"""
        assert engine.classify_urgency(48.0) == UrgencyLevel.SIAGA

    def test_negative_hours_raises_value_error(self, engine):
        """Negative time_to_impact raises ValueError. Requirements: 5.4"""
        with pytest.raises(ValueError, match="non-negative"):
            engine.classify_urgency(-1.0)

    def test_returns_urgency_level_enum(self, engine):
        """classify_urgency always returns a UrgencyLevel enum. Requirements: 5.4"""
        for hours in [0.0, 0.5, 1.0, 2.0, 6.0, 10.0, 24.0, 100.0]:
            result = engine.classify_urgency(hours)
            assert isinstance(result, UrgencyLevel)


# ---------------------------------------------------------------------------
# Tests: RecommendationItem and RouteRecommendation dataclasses
# ---------------------------------------------------------------------------

class TestDataclasses:
    """Tests for RecommendationItem and RouteRecommendation dataclasses."""

    def test_recommendation_item_creation(self):
        """RecommendationItem can be created with required fields."""
        now = datetime.now(timezone.utc)
        rec = RecommendationItem(
            region_id=1,
            type=RecommendationType.ALERT,
            description="Test alert",
            urgency=UrgencyLevel.SEGERA,
            created_at=now,
        )
        assert rec.region_id == 1
        assert rec.type == RecommendationType.ALERT
        assert rec.description == "Test alert"
        assert rec.urgency == UrgencyLevel.SEGERA
        assert rec.created_at == now
        assert rec.expires_at is None
        assert rec.metadata == {}

    def test_route_recommendation_creation(self):
        """RouteRecommendation can be created with required fields."""
        origin = Coordinate(latitude=-6.1, longitude=106.8)
        dest = Coordinate(latitude=-6.2, longitude=106.9)
        route = RouteRecommendation(
            origin=origin,
            destination=dest,
            route_region_ids=[1, 2, 5],
            is_safe=True,
        )
        assert route.origin == origin
        assert route.destination == dest
        assert route.route_region_ids == [1, 2, 5]
        assert route.is_safe is True
        assert route.avoided_regions == set()
        assert route.no_safe_route_reason is None
        assert route.estimated_recovery_hours is None

    def test_recommendation_type_values(self):
        """RecommendationType enum has correct values."""
        assert RecommendationType.ROUTE.value == "route"
        assert RecommendationType.ALERT.value == "alert"
        assert RecommendationType.SERVICE.value == "service"

    def test_urgency_level_values(self):
        """UrgencyLevel enum has correct Bahasa Indonesia values."""
        assert UrgencyLevel.SEGERA.value == "Segera"
        assert UrgencyLevel.WASPADA.value == "Waspada"
        assert UrgencyLevel.SIAGA.value == "Siaga"


# ---------------------------------------------------------------------------
# Tests: DB-backed generate_recommendations persistence
# ---------------------------------------------------------------------------

class TestRecommendationEngineWithDB:
    """Tests for RecommendationEngine with a mocked database session."""

    @pytest.fixture
    def mock_db_session(self):
        return Mock()

    def test_engine_initializes_with_db_session(self, mock_db_session):
        """Engine can be initialized with a DB session."""
        engine = RecommendationEngine(db_session=mock_db_session)
        assert engine.db_session == mock_db_session

    def test_generate_recommendations_does_not_require_db(self):
        """
        generate_recommendations works without a DB session.

        Requirements: 5.1
        """
        engine = RecommendationEngine()  # no db_session
        result = engine.generate_recommendations(
            region_id=1,
            urban_risk_score=80.0,
        )
        assert isinstance(result, list)
        assert len(result) >= 1
