"""
Unit tests for Service Accessibility Module.

This module contains unit tests for the Service_Accessibility_Module component
that evaluates accessibility of public facilities during flood conditions.

Requirements: 3.1, 3.2, 3.3
"""

import pytest
from datetime import datetime, timezone
from unittest.mock import Mock, MagicMock

from src.uris_ai.ml.service_accessibility import (
    ServiceAccessibilityModule,
    AccessibilityReport
)
from src.uris_ai.ml.traffic_analyzer import TrafficImpact, CongestionLevel
from src.uris_ai.models.database import PublicFacility, Region


class TestServiceAccessibilityModule:
    """Unit tests for Service Accessibility Module."""

    @pytest.fixture
    def mock_db_session(self):
        """Create a mock database session."""
        return Mock()

    @pytest.fixture
    def module(self, mock_db_session):
        """Create a ServiceAccessibilityModule instance."""
        return ServiceAccessibilityModule(mock_db_session)

    @pytest.fixture
    def sample_facility(self):
        """Create a sample facility."""
        return PublicFacility(
            id=1,
            region_id=1,
            name="Main Hospital",
            type="hospital",
            latitude=-6.2,
            longitude=106.8,
            capacity=100,
            is_operational=True
        )

    @pytest.fixture
    def sample_traffic_impact(self):
        """Create a sample traffic impact."""
        return TrafficImpact(
            region_id=1,
            affected_roads=[1, 2, 3],
            congestion_levels={
                1: CongestionLevel.PARAH,
                2: CongestionLevel.TIDAK_DAPAT_DILALUI,
                3: CongestionLevel.SEDANG
            },
            is_isolated=False,
            timestamp=datetime.now(timezone.utc)
        )

    # ========================================================================
    # Tests for evaluate_accessibility
    # ========================================================================

    def test_evaluate_accessibility_basic(self, module, mock_db_session, sample_traffic_impact):
        """
        Test basic accessibility evaluation.
        
        Requirements: 3.1
        """
        # Create sample facilities
        facilities = [
            PublicFacility(
                id=1,
                region_id=1,
                name="Hospital A",
                type="hospital",
                latitude=-6.2,
                longitude=106.8,
                capacity=100,
                is_operational=True
            ),
            PublicFacility(
                id=2,
                region_id=1,
                name="Hospital B",
                type="hospital",
                latitude=-6.3,
                longitude=106.9,
                capacity=100,
                is_operational=True
            )
        ]
        
        # Setup mock to handle multiple query calls
        call_count = [0]
        def mock_query_side_effect(model):
            call_count[0] += 1
            mock_query = Mock()
            
            if call_count[0] == 1:
                # First call: get_affected_facilities
                mock_query.filter.return_value.all.return_value = facilities
            else:
                # Subsequent calls: find_alternative_facilities (return empty)
                if call_count[0] % 2 == 0:
                    # Get facility by id
                    mock_query.filter.return_value.first.return_value = facilities[0] if call_count[0] == 2 else facilities[1]
                else:
                    # Get alternatives (empty)
                    mock_query.filter.return_value.all.return_value = []
            
            return mock_query
        
        mock_db_session.query.side_effect = mock_query_side_effect
        
        # Evaluate accessibility
        report = module.evaluate_accessibility(1, sample_traffic_impact)
        
        # Verify report structure
        assert isinstance(report, AccessibilityReport)
        assert report.region_id == 1
        assert len(report.affected_facilities) == 2
        assert 1 in report.affected_facilities
        assert 2 in report.affected_facilities
        assert isinstance(report.timestamp, datetime)

    def test_evaluate_accessibility_with_alternatives(self, module, mock_db_session, sample_traffic_impact):
        """
        Test accessibility evaluation finds alternatives.
        
        Requirements: 3.1, 3.2
        """
        # Create affected facility
        affected_facility = PublicFacility(
            id=1,
            region_id=1,
            name="Hospital A",
            type="hospital",
            latitude=-6.2,
            longitude=106.8,
            capacity=100,
            is_operational=True
        )
        
        # Create alternative facility (within 10km)
        alternative_facility = PublicFacility(
            id=2,
            region_id=2,
            name="Hospital B",
            type="hospital",
            latitude=-6.25,  # ~5.5 km away
            longitude=106.85,
            capacity=100,
            is_operational=True
        )
        
        # Setup mock to return facilities
        call_count = [0]
        def mock_query_side_effect(model):
            call_count[0] += 1
            mock_query = Mock()
            
            if call_count[0] == 1:
                # First call: get_affected_facilities
                mock_query.filter.return_value.all.return_value = [affected_facility]
            elif call_count[0] % 2 == 0:
                # Even calls: get facility by id
                mock_query.filter.return_value.first.return_value = affected_facility
            else:
                # Odd calls: get alternatives
                mock_query.filter.return_value.all.return_value = [alternative_facility]
            
            return mock_query
        
        mock_db_session.query.side_effect = mock_query_side_effect
        
        # Evaluate accessibility
        report = module.evaluate_accessibility(1, sample_traffic_impact)
        
        # Verify alternatives found
        assert 1 in report.alternative_facilities
        assert 2 in report.alternative_facilities[1]

    def test_evaluate_accessibility_detects_overload(self, module, mock_db_session, sample_traffic_impact):
        """
        Test that accessibility evaluation detects potential overload.
        
        Requirements: 3.1, 3.3
        """
        # Create affected facility
        affected_facility = PublicFacility(
            id=1,
            region_id=1,
            name="Hospital A",
            type="hospital",
            latitude=-6.2,
            longitude=106.8,
            capacity=100,
            is_operational=True
        )
        
        # Create alternative facility (non-operational = high load)
        alternative_facility = PublicFacility(
            id=2,
            region_id=2,
            name="Hospital B",
            type="hospital",
            latitude=-6.25,
            longitude=106.85,
            capacity=100,
            is_operational=False  # Non-operational = 100% load
        )
        
        # Setup mock
        call_count = [0]
        def mock_query_side_effect(model):
            call_count[0] += 1
            mock_query = Mock()
            
            if call_count[0] == 1:
                # get_affected_facilities
                mock_query.filter.return_value.all.return_value = [affected_facility]
            elif call_count[0] % 3 == 2:
                # get facility by id (for find_alternative_facilities)
                mock_query.filter.return_value.first.return_value = affected_facility
            elif call_count[0] % 3 == 0:
                # get alternatives
                mock_query.filter.return_value.all.return_value = [alternative_facility]
            else:
                # get facility by id (for estimate_facility_load)
                mock_query.filter.return_value.first.return_value = alternative_facility
            
            return mock_query
        
        mock_db_session.query.side_effect = mock_query_side_effect
        
        # Evaluate accessibility
        report = module.evaluate_accessibility(1, sample_traffic_impact)
        
        # Verify overload warning
        assert 2 in report.overload_warnings

    def test_evaluate_accessibility_no_facilities(self, module, mock_db_session, sample_traffic_impact):
        """
        Test accessibility evaluation with no facilities in region.
        
        Requirements: 3.1
        """
        # Mock empty facility list
        mock_query = Mock()
        mock_query.filter.return_value.all.return_value = []
        mock_db_session.query.return_value = mock_query
        
        # Evaluate accessibility
        report = module.evaluate_accessibility(1, sample_traffic_impact)
        
        # Verify empty report
        assert len(report.affected_facilities) == 0
        assert len(report.alternative_facilities) == 0
        assert len(report.overload_warnings) == 0

    # ========================================================================
    # Tests for find_alternative_facilities
    # ========================================================================

    def test_find_alternative_facilities_basic(self, module, mock_db_session, sample_facility):
        """
        Test finding alternative facilities within radius.
        
        Requirements: 3.2
        """
        # Create alternative facilities
        alternatives = [
            PublicFacility(
                id=2,
                region_id=2,
                name="Hospital B",
                type="hospital",
                latitude=-6.25,  # ~5.5 km away
                longitude=106.85,
                capacity=100,
                is_operational=True
            ),
            PublicFacility(
                id=3,
                region_id=3,
                name="Hospital C",
                type="hospital",
                latitude=-6.22,  # ~2.5 km away
                longitude=106.82,
                capacity=100,
                is_operational=True
            )
        ]
        
        # Setup mock
        call_count = [0]
        def mock_query_side_effect(model):
            call_count[0] += 1
            mock_query = Mock()
            
            if call_count[0] == 1:
                # Get original facility
                mock_query.filter.return_value.first.return_value = sample_facility
            else:
                # Get alternatives
                mock_query.filter.return_value.all.return_value = alternatives
            
            return mock_query
        
        mock_db_session.query.side_effect = mock_query_side_effect
        
        # Find alternatives
        results = module.find_alternative_facilities(1, radius_km=10.0)
        
        # Verify results
        assert len(results) == 2
        assert all(alt.type == "hospital" for alt in results)

    def test_find_alternative_facilities_filters_by_distance(self, module, mock_db_session, sample_facility):
        """
        Test that alternatives outside radius are filtered out.
        
        Requirements: 3.2
        """
        # Create alternatives at various distances
        alternatives = [
            PublicFacility(
                id=2,
                region_id=2,
                name="Hospital B",
                type="hospital",
                latitude=-6.22,  # ~2.5 km away
                longitude=106.82,
                capacity=100,
                is_operational=True
            ),
            PublicFacility(
                id=3,
                region_id=3,
                name="Hospital C",
                type="hospital",
                latitude=-6.5,  # ~33 km away (outside radius)
                longitude=107.0,
                capacity=100,
                is_operational=True
            )
        ]
        
        # Setup mock
        call_count = [0]
        def mock_query_side_effect(model):
            call_count[0] += 1
            mock_query = Mock()
            
            if call_count[0] == 1:
                mock_query.filter.return_value.first.return_value = sample_facility
            else:
                mock_query.filter.return_value.all.return_value = alternatives
            
            return mock_query
        
        mock_db_session.query.side_effect = mock_query_side_effect
        
        # Find alternatives within 10km
        results = module.find_alternative_facilities(1, radius_km=10.0)
        
        # Verify only nearby facility returned
        assert len(results) == 1
        assert results[0].id == 2

    def test_find_alternative_facilities_same_type_only(self, module, mock_db_session, sample_facility):
        """
        Test that only facilities of same type are returned.
        
        Requirements: 3.2
        """
        # Create alternatives of different types
        alternatives = [
            PublicFacility(
                id=2,
                region_id=2,
                name="Hospital B",
                type="hospital",
                latitude=-6.22,
                longitude=106.82,
                capacity=100,
                is_operational=True
            )
        ]
        
        # Setup mock (database already filters by type)
        call_count = [0]
        def mock_query_side_effect(model):
            call_count[0] += 1
            mock_query = Mock()
            
            if call_count[0] == 1:
                mock_query.filter.return_value.first.return_value = sample_facility
            else:
                mock_query.filter.return_value.all.return_value = alternatives
            
            return mock_query
        
        mock_db_session.query.side_effect = mock_query_side_effect
        
        # Find alternatives
        results = module.find_alternative_facilities(1, radius_km=10.0)
        
        # Verify all same type
        assert all(alt.type == sample_facility.type for alt in results)

    def test_find_alternative_facilities_operational_only(self, module, mock_db_session, sample_facility):
        """
        Test that only operational facilities are returned.
        
        Requirements: 3.2
        """
        # Create operational alternatives (database filters non-operational)
        alternatives = [
            PublicFacility(
                id=2,
                region_id=2,
                name="Hospital B",
                type="hospital",
                latitude=-6.22,
                longitude=106.82,
                capacity=100,
                is_operational=True
            )
        ]
        
        # Setup mock
        call_count = [0]
        def mock_query_side_effect(model):
            call_count[0] += 1
            mock_query = Mock()
            
            if call_count[0] == 1:
                mock_query.filter.return_value.first.return_value = sample_facility
            else:
                mock_query.filter.return_value.all.return_value = alternatives
            
            return mock_query
        
        mock_db_session.query.side_effect = mock_query_side_effect
        
        # Find alternatives
        results = module.find_alternative_facilities(1, radius_km=10.0)
        
        # Verify all operational
        assert all(alt.is_operational for alt in results)

    def test_find_alternative_facilities_excludes_original(self, module, mock_db_session, sample_facility):
        """
        Test that original facility is excluded from alternatives.
        
        Requirements: 3.2
        """
        # Create alternatives (database already excludes original)
        alternatives = [
            PublicFacility(
                id=2,
                region_id=2,
                name="Hospital B",
                type="hospital",
                latitude=-6.22,
                longitude=106.82,
                capacity=100,
                is_operational=True
            )
        ]
        
        # Setup mock
        call_count = [0]
        def mock_query_side_effect(model):
            call_count[0] += 1
            mock_query = Mock()
            
            if call_count[0] == 1:
                mock_query.filter.return_value.first.return_value = sample_facility
            else:
                mock_query.filter.return_value.all.return_value = alternatives
            
            return mock_query
        
        mock_db_session.query.side_effect = mock_query_side_effect
        
        # Find alternatives
        results = module.find_alternative_facilities(1, radius_km=10.0)
        
        # Verify original not in results
        assert all(alt.id != sample_facility.id for alt in results)

    def test_find_alternative_facilities_not_found(self, module, mock_db_session):
        """
        Test finding alternatives for non-existent facility.
        
        Requirements: 3.2
        """
        # Mock facility not found
        mock_query = Mock()
        mock_query.filter.return_value.first.return_value = None
        mock_db_session.query.return_value = mock_query
        
        # Find alternatives
        results = module.find_alternative_facilities(999, radius_km=10.0)
        
        # Verify empty list
        assert results == []

    # ========================================================================
    # Tests for estimate_facility_load
    # ========================================================================

    def test_estimate_facility_load_operational(self, module, mock_db_session, sample_facility):
        """
        Test load estimation for operational facility.
        
        Requirements: 3.3
        """
        # Mock facility query
        mock_query = Mock()
        mock_query.filter.return_value.first.return_value = sample_facility
        mock_db_session.query.return_value = mock_query
        
        # Estimate load
        load = module.estimate_facility_load(1)
        
        # Verify load is reasonable
        assert 0.0 <= load <= 1.0
        assert load == 0.5  # Default for operational with capacity

    def test_estimate_facility_load_non_operational(self, module, mock_db_session):
        """
        Test load estimation for non-operational facility.
        
        Requirements: 3.3
        """
        # Create non-operational facility
        facility = PublicFacility(
            id=1,
            region_id=1,
            name="Hospital A",
            type="hospital",
            latitude=-6.2,
            longitude=106.8,
            capacity=100,
            is_operational=False
        )
        
        # Mock facility query
        mock_query = Mock()
        mock_query.filter.return_value.first.return_value = facility
        mock_db_session.query.return_value = mock_query
        
        # Estimate load
        load = module.estimate_facility_load(1)
        
        # Verify full load
        assert load == 1.0

    def test_estimate_facility_load_no_capacity(self, module, mock_db_session):
        """
        Test load estimation for facility without capacity info.
        
        Requirements: 3.3
        """
        # Create facility without capacity
        facility = PublicFacility(
            id=1,
            region_id=1,
            name="Hospital A",
            type="hospital",
            latitude=-6.2,
            longitude=106.8,
            capacity=None,
            is_operational=True
        )
        
        # Mock facility query
        mock_query = Mock()
        mock_query.filter.return_value.first.return_value = facility
        mock_db_session.query.return_value = mock_query
        
        # Estimate load
        load = module.estimate_facility_load(1)
        
        # Verify moderate load
        assert load == 0.5

    def test_estimate_facility_load_not_found(self, module, mock_db_session):
        """
        Test load estimation for non-existent facility.
        
        Requirements: 3.3
        """
        # Mock facility not found
        mock_query = Mock()
        mock_query.filter.return_value.first.return_value = None
        mock_db_session.query.return_value = mock_query
        
        # Estimate load
        load = module.estimate_facility_load(999)
        
        # Verify zero load
        assert load == 0.0

    # ========================================================================
    # Tests for get_affected_facilities
    # ========================================================================

    def test_get_affected_facilities_basic(self, module, mock_db_session):
        """
        Test getting affected facilities in a region.
        
        Requirements: 3.1
        """
        # Create sample facilities
        facilities = [
            PublicFacility(
                id=1,
                region_id=1,
                name="Hospital A",
                type="hospital",
                latitude=-6.2,
                longitude=106.8,
                capacity=100,
                is_operational=True
            ),
            PublicFacility(
                id=2,
                region_id=1,
                name="School A",
                type="school",
                latitude=-6.3,
                longitude=106.9,
                capacity=200,
                is_operational=True
            )
        ]
        
        # Mock query
        mock_query = Mock()
        mock_query.filter.return_value.all.return_value = facilities
        mock_db_session.query.return_value = mock_query
        
        # Get affected facilities
        results = module.get_affected_facilities(1)
        
        # Verify results
        assert len(results) == 2
        assert all(f.region_id == 1 for f in results)

    def test_get_affected_facilities_empty(self, module, mock_db_session):
        """
        Test getting affected facilities when none exist.
        
        Requirements: 3.1
        """
        # Mock empty query
        mock_query = Mock()
        mock_query.filter.return_value.all.return_value = []
        mock_db_session.query.return_value = mock_query
        
        # Get affected facilities
        results = module.get_affected_facilities(1)
        
        # Verify empty list
        assert results == []

    # ========================================================================
    # Tests for Haversine distance calculation
    # ========================================================================

    def test_haversine_distance_zero(self, module):
        """Test Haversine distance between same point is zero."""
        distance = module._calculate_haversine_distance(-6.2, 106.8, -6.2, 106.8)
        assert distance == 0.0

    def test_haversine_distance_known_value(self, module):
        """Test Haversine distance with known values."""
        # Distance from Jakarta (-6.2, 106.8) to Bandung (-6.9, 107.6)
        # Should be approximately 115-120 km
        distance = module._calculate_haversine_distance(-6.2, 106.8, -6.9, 107.6)
        assert 115 <= distance <= 120

    def test_haversine_distance_symmetry(self, module):
        """Test that Haversine distance is symmetric."""
        distance1 = module._calculate_haversine_distance(-6.2, 106.8, -6.3, 106.9)
        distance2 = module._calculate_haversine_distance(-6.3, 106.9, -6.2, 106.8)
        assert abs(distance1 - distance2) < 0.001

    def test_haversine_distance_positive(self, module):
        """Test that Haversine distance is always positive."""
        distance = module._calculate_haversine_distance(-6.2, 106.8, -6.5, 107.0)
        assert distance > 0
