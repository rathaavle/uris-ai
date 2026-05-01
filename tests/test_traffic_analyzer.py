"""
Unit tests for Traffic Analyzer.

This module contains unit tests for the Traffic_Analyzer component,
testing traffic impact calculation and congestion level estimation.

Requirements: 2.1, 2.2, 2.3, 2.4
"""

import pytest
from datetime import datetime, timezone
from unittest.mock import Mock, MagicMock

from src.uris_ai.ml.traffic_analyzer import (
    TrafficAnalyzer,
    TrafficImpact,
    CongestionLevel
)
from src.uris_ai.ml.flood_risk_engine import (
    FloodRiskPrediction,
    RiskCategory
)
from src.uris_ai.models.database import Road, Region


class TestTrafficAnalyzer:
    """Unit tests for TrafficAnalyzer class."""

    @pytest.fixture
    def mock_db_session(self):
        """Create a mock database session."""
        return Mock()

    @pytest.fixture
    def analyzer(self, mock_db_session):
        """Create a TrafficAnalyzer instance with mock session."""
        return TrafficAnalyzer(mock_db_session)

    @pytest.fixture
    def sample_flood_risk_high(self):
        """Create a sample HIGH flood risk prediction."""
        return FloodRiskPrediction(
            region_id=1,
            risk_score=60.0,
            category=RiskCategory.TINGGI,
            confidence=0.85,
            timestamp=datetime.now(timezone.utc),
            features_used={}
        )

    @pytest.fixture
    def sample_flood_risk_critical(self):
        """Create a sample CRITICAL flood risk prediction."""
        return FloodRiskPrediction(
            region_id=1,
            risk_score=85.0,
            category=RiskCategory.KRITIS,
            confidence=0.90,
            timestamp=datetime.now(timezone.utc),
            features_used={}
        )

    @pytest.fixture
    def sample_flood_risk_critical_extreme(self):
        """Create a sample CRITICAL flood risk prediction with extreme score."""
        return FloodRiskPrediction(
            region_id=1,
            risk_score=95.0,
            category=RiskCategory.KRITIS,
            confidence=0.95,
            timestamp=datetime.now(timezone.utc),
            features_used={}
        )

    @pytest.fixture
    def sample_flood_risk_low(self):
        """Create a sample LOW flood risk prediction."""
        return FloodRiskPrediction(
            region_id=1,
            risk_score=15.0,
            category=RiskCategory.RENDAH,
            confidence=0.80,
            timestamp=datetime.now(timezone.utc),
            features_used={}
        )

    @pytest.fixture
    def sample_roads(self):
        """Create sample road objects."""
        return [
            Road(
                id=1,
                region_id=1,
                road_name="Jalan Utama 1",
                road_type="primary",
                road_density=5.0,
                length_km=10.0,
                is_main_road=True
            ),
            Road(
                id=2,
                region_id=1,
                road_name="Jalan Utama 2",
                road_type="primary",
                road_density=4.5,
                length_km=8.0,
                is_main_road=True
            ),
            Road(
                id=3,
                region_id=1,
                road_name="Jalan Sekunder",
                road_type="secondary",
                road_density=3.0,
                length_km=5.0,
                is_main_road=False
            )
        ]

    def test_initialization(self, mock_db_session):
        """Test TrafficAnalyzer initialization."""
        analyzer = TrafficAnalyzer(mock_db_session)
        assert analyzer.db_session == mock_db_session

    def test_get_affected_roads_high_risk(
        self,
        analyzer,
        mock_db_session,
        sample_flood_risk_high,
        sample_roads
    ):
        """
        Test get_affected_roads returns roads for HIGH risk.
        
        Requirements: 2.1
        """
        # Setup mock query
        mock_query = Mock()
        mock_query.filter.return_value.all.return_value = sample_roads
        mock_db_session.query.return_value = mock_query

        # Call method
        affected = analyzer.get_affected_roads(1, sample_flood_risk_high)

        # Verify
        assert len(affected) == 3
        assert all(isinstance(road, Road) for road in affected)
        mock_db_session.query.assert_called_once()

    def test_get_affected_roads_critical_risk(
        self,
        analyzer,
        mock_db_session,
        sample_flood_risk_critical,
        sample_roads
    ):
        """
        Test get_affected_roads returns roads for CRITICAL risk.
        
        Requirements: 2.1
        """
        # Setup mock query
        mock_query = Mock()
        mock_query.filter.return_value.all.return_value = sample_roads
        mock_db_session.query.return_value = mock_query

        # Call method
        affected = analyzer.get_affected_roads(1, sample_flood_risk_critical)

        # Verify
        assert len(affected) == 3

    def test_get_affected_roads_low_risk(
        self,
        analyzer,
        sample_flood_risk_low
    ):
        """
        Test get_affected_roads returns empty list for LOW risk.
        
        Requirements: 2.1
        """
        # Call method
        affected = analyzer.get_affected_roads(1, sample_flood_risk_low)

        # Verify - no roads affected for low risk
        assert len(affected) == 0

    def test_estimate_congestion_level_high_risk(
        self,
        analyzer,
        mock_db_session,
        sample_flood_risk_high,
        sample_roads
    ):
        """
        Test congestion level estimation for HIGH risk.
        
        Requirements: 2.2
        """
        # Setup mock query
        mock_query = Mock()
        mock_query.filter.return_value.first.return_value = sample_roads[0]
        mock_db_session.query.return_value = mock_query

        # Call method
        level = analyzer.estimate_congestion_level(1, sample_flood_risk_high)

        # Verify - HIGH risk should result in SEDANG congestion
        assert level == CongestionLevel.SEDANG

    def test_estimate_congestion_level_critical_risk(
        self,
        analyzer,
        mock_db_session,
        sample_flood_risk_critical,
        sample_roads
    ):
        """
        Test congestion level estimation for CRITICAL risk (score < 90).
        
        Requirements: 2.2
        """
        # Setup mock query
        mock_query = Mock()
        mock_query.filter.return_value.first.return_value = sample_roads[0]
        mock_db_session.query.return_value = mock_query

        # Call method
        level = analyzer.estimate_congestion_level(1, sample_flood_risk_critical)

        # Verify - CRITICAL risk with score < 90 should result in PARAH
        assert level == CongestionLevel.PARAH

    def test_estimate_congestion_level_critical_extreme(
        self,
        analyzer,
        mock_db_session,
        sample_flood_risk_critical_extreme,
        sample_roads
    ):
        """
        Test congestion level estimation for extreme CRITICAL risk (score >= 90).
        
        Requirements: 2.2
        """
        # Setup mock query
        mock_query = Mock()
        mock_query.filter.return_value.first.return_value = sample_roads[0]
        mock_db_session.query.return_value = mock_query

        # Call method
        level = analyzer.estimate_congestion_level(
            1,
            sample_flood_risk_critical_extreme
        )

        # Verify - CRITICAL risk with score >= 90 should be impassable
        assert level == CongestionLevel.TIDAK_DAPAT_DILALUI

    def test_estimate_congestion_level_road_not_found(
        self,
        analyzer,
        mock_db_session,
        sample_flood_risk_high
    ):
        """
        Test congestion level estimation when road is not found.
        
        Requirements: 2.2
        """
        # Setup mock query to return None
        mock_query = Mock()
        mock_query.filter.return_value.first.return_value = None
        mock_db_session.query.return_value = mock_query

        # Call method
        level = analyzer.estimate_congestion_level(999, sample_flood_risk_high)

        # Verify - should default to SEDANG
        assert level == CongestionLevel.SEDANG

    def test_check_region_isolation_all_main_roads_impassable(
        self,
        analyzer,
        mock_db_session,
        sample_roads
    ):
        """
        Test region isolation when all main roads are impassable.
        
        Requirements: 2.4
        """
        # Setup mock query to return only main roads
        main_roads = [r for r in sample_roads if r.is_main_road]
        mock_query = Mock()
        mock_query.filter.return_value.all.return_value = main_roads
        mock_db_session.query.return_value = mock_query

        # Create congestion levels where all main roads are impassable
        congestion_levels = {
            1: CongestionLevel.TIDAK_DAPAT_DILALUI,
            2: CongestionLevel.TIDAK_DAPAT_DILALUI,
            3: CongestionLevel.SEDANG  # Secondary road, not main
        }

        # Call method
        is_isolated = analyzer.check_region_isolation(1, congestion_levels)

        # Verify - region should be isolated
        assert is_isolated is True

    def test_check_region_isolation_some_main_roads_passable(
        self,
        analyzer,
        mock_db_session,
        sample_roads
    ):
        """
        Test region isolation when some main roads are still passable.
        
        Requirements: 2.4
        """
        # Setup mock query to return only main roads
        main_roads = [r for r in sample_roads if r.is_main_road]
        mock_query = Mock()
        mock_query.filter.return_value.all.return_value = main_roads
        mock_db_session.query.return_value = mock_query

        # Create congestion levels where one main road is still passable
        congestion_levels = {
            1: CongestionLevel.TIDAK_DAPAT_DILALUI,
            2: CongestionLevel.PARAH,  # Still passable
            3: CongestionLevel.SEDANG
        }

        # Call method
        is_isolated = analyzer.check_region_isolation(1, congestion_levels)

        # Verify - region should NOT be isolated
        assert is_isolated is False

    def test_check_region_isolation_no_main_roads(
        self,
        analyzer,
        mock_db_session
    ):
        """
        Test region isolation when there are no main roads.
        
        Requirements: 2.4
        """
        # Setup mock query to return empty list
        mock_query = Mock()
        mock_query.filter.return_value.all.return_value = []
        mock_db_session.query.return_value = mock_query

        # Call method
        is_isolated = analyzer.check_region_isolation(1, {})

        # Verify - region should NOT be isolated if no main roads
        assert is_isolated is False

    def test_check_region_isolation_no_congestion_data(
        self,
        analyzer,
        mock_db_session,
        sample_roads
    ):
        """
        Test region isolation when no congestion data is provided.
        
        Requirements: 2.4
        """
        # Setup mock query
        main_roads = [r for r in sample_roads if r.is_main_road]
        mock_query = Mock()
        mock_query.filter.return_value.all.return_value = main_roads
        mock_db_session.query.return_value = mock_query

        # Call method without congestion data
        is_isolated = analyzer.check_region_isolation(1, None)

        # Verify - should return False when no data
        assert is_isolated is False

    def test_analyze_traffic_impact_high_risk(
        self,
        analyzer,
        mock_db_session,
        sample_flood_risk_high,
        sample_roads
    ):
        """
        Test full traffic impact analysis for HIGH risk.
        
        Requirements: 2.1, 2.3
        """
        # Setup mock queries
        mock_query_roads = Mock()
        mock_query_roads.filter.return_value.all.return_value = sample_roads
        
        mock_query_road = Mock()
        mock_query_road.filter.return_value.first.side_effect = sample_roads
        
        mock_query_main = Mock()
        main_roads = [r for r in sample_roads if r.is_main_road]
        mock_query_main.filter.return_value.all.return_value = main_roads
        
        # Configure mock to return different queries
        mock_db_session.query.side_effect = [
            mock_query_roads,  # get_affected_roads
            mock_query_road,   # estimate_congestion_level for road 1
            mock_query_road,   # estimate_congestion_level for road 2
            mock_query_road,   # estimate_congestion_level for road 3
            mock_query_main    # check_region_isolation
        ]

        # Call method
        impact = analyzer.analyze_traffic_impact(1, sample_flood_risk_high)

        # Verify
        assert isinstance(impact, TrafficImpact)
        assert impact.region_id == 1
        assert len(impact.affected_roads) == 3
        assert len(impact.congestion_levels) == 3
        assert impact.is_isolated is False  # SEDANG congestion, not isolated
        assert isinstance(impact.timestamp, datetime)

    def test_analyze_traffic_impact_critical_risk_isolated(
        self,
        analyzer,
        mock_db_session,
        sample_flood_risk_critical_extreme,
        sample_roads
    ):
        """
        Test traffic impact analysis for CRITICAL risk resulting in isolation.
        
        Requirements: 2.1, 2.3, 2.4
        """
        # Setup mock queries
        mock_query_roads = Mock()
        mock_query_roads.filter.return_value.all.return_value = sample_roads
        
        mock_query_road = Mock()
        mock_query_road.filter.return_value.first.side_effect = sample_roads
        
        mock_query_main = Mock()
        main_roads = [r for r in sample_roads if r.is_main_road]
        mock_query_main.filter.return_value.all.return_value = main_roads
        
        # Configure mock to return different queries
        mock_db_session.query.side_effect = [
            mock_query_roads,  # get_affected_roads
            mock_query_road,   # estimate_congestion_level for road 1
            mock_query_road,   # estimate_congestion_level for road 2
            mock_query_road,   # estimate_congestion_level for road 3
            mock_query_main    # check_region_isolation
        ]

        # Call method
        impact = analyzer.analyze_traffic_impact(
            1,
            sample_flood_risk_critical_extreme
        )

        # Verify
        assert isinstance(impact, TrafficImpact)
        assert impact.region_id == 1
        assert len(impact.affected_roads) == 3
        # All roads should be TIDAK_DAPAT_DILALUI with score >= 90
        assert all(
            level == CongestionLevel.TIDAK_DAPAT_DILALUI
            for level in impact.congestion_levels.values()
        )
        assert impact.is_isolated is True  # All main roads impassable

    def test_analyze_traffic_impact_low_risk(
        self,
        analyzer,
        mock_db_session,
        sample_flood_risk_low,
        sample_roads
    ):
        """
        Test traffic impact analysis for LOW risk (no impact).
        
        Requirements: 2.1, 2.3
        """
        # Setup mock query for check_region_isolation
        mock_query_main = Mock()
        main_roads = [r for r in sample_roads if r.is_main_road]
        mock_query_main.filter.return_value.all.return_value = main_roads
        mock_db_session.query.return_value = mock_query_main

        # Call method
        impact = analyzer.analyze_traffic_impact(1, sample_flood_risk_low)

        # Verify - no roads affected for low risk
        assert isinstance(impact, TrafficImpact)
        assert impact.region_id == 1
        assert len(impact.affected_roads) == 0
        assert len(impact.congestion_levels) == 0
        assert impact.is_isolated is False


class TestCongestionLevel:
    """Test CongestionLevel enum."""

    def test_congestion_level_values(self):
        """Test that CongestionLevel has correct values."""
        assert CongestionLevel.SEDANG.value == "SEDANG"
        assert CongestionLevel.PARAH.value == "PARAH"
        assert CongestionLevel.TIDAK_DAPAT_DILALUI.value == "TIDAK_DAPAT_DILALUI"

    def test_congestion_level_membership(self):
        """Test CongestionLevel enum membership."""
        assert CongestionLevel.SEDANG in CongestionLevel
        assert CongestionLevel.PARAH in CongestionLevel
        assert CongestionLevel.TIDAK_DAPAT_DILALUI in CongestionLevel


class TestTrafficImpact:
    """Test TrafficImpact dataclass."""

    def test_traffic_impact_creation(self):
        """Test TrafficImpact dataclass creation."""
        timestamp = datetime.now(timezone.utc)
        impact = TrafficImpact(
            region_id=1,
            affected_roads=[1, 2, 3],
            congestion_levels={
                1: CongestionLevel.SEDANG,
                2: CongestionLevel.PARAH,
                3: CongestionLevel.TIDAK_DAPAT_DILALUI
            },
            is_isolated=False,
            timestamp=timestamp
        )

        assert impact.region_id == 1
        assert impact.affected_roads == [1, 2, 3]
        assert len(impact.congestion_levels) == 3
        assert impact.is_isolated is False
        assert impact.timestamp == timestamp
