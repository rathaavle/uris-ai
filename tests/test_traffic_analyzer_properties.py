"""
Property-based tests for Traffic Analyzer.

This module contains property tests that validate universal correctness
properties of the traffic analysis system.

Requirements: 2.4
"""

import pytest
from hypothesis import given, strategies as st, assume
from unittest.mock import Mock

from src.uris_ai.ml.traffic_analyzer import (
    TrafficAnalyzer,
    CongestionLevel
)
from src.uris_ai.models.database import Road


# Custom strategies for generating test data
@st.composite
def road_configuration(draw):
    """
    Generate a road configuration for a region.
    
    Returns a tuple of (main_roads, secondary_roads, congestion_levels)
    """
    # Generate 1-10 main roads
    num_main_roads = draw(st.integers(min_value=1, max_value=10))
    
    # Generate 0-10 secondary roads
    num_secondary_roads = draw(st.integers(min_value=0, max_value=10))
    
    # Create main roads
    main_roads = []
    for i in range(num_main_roads):
        road = Road(
            id=i + 1,
            region_id=1,
            road_name=f"Main Road {i+1}",
            road_type="primary",
            road_density=5.0,
            length_km=10.0,
            is_main_road=True
        )
        main_roads.append(road)
    
    # Create secondary roads
    secondary_roads = []
    for i in range(num_secondary_roads):
        road = Road(
            id=num_main_roads + i + 1,
            region_id=1,
            road_name=f"Secondary Road {i+1}",
            road_type="secondary",
            road_density=3.0,
            length_km=5.0,
            is_main_road=False
        )
        secondary_roads.append(road)
    
    # Generate congestion levels for all roads
    all_roads = main_roads + secondary_roads
    congestion_levels = {}
    
    for road in all_roads:
        level = draw(st.sampled_from([
            CongestionLevel.SEDANG,
            CongestionLevel.PARAH,
            CongestionLevel.TIDAK_DAPAT_DILALUI
        ]))
        congestion_levels[road.id] = level
    
    return main_roads, secondary_roads, congestion_levels


class TestTrafficAnalyzerProperties:
    """Property-based tests for Traffic Analyzer."""

    @given(config=road_configuration())
    def test_region_isolation_detection_property(self, config):
        """
        **Property 2: Region Isolation Detection**
        
        **Validates: Requirements 2.4**
        
        For any region with road configuration, if all main roads
        (is_main_road=true) are impassable (congestion level = TIDAK_DAPAT_DILALUI),
        then the region must be classified as isolated (is_isolated=true).
        
        Invariant: is_isolated = true ↔ ∀ road ∈ main_roads: road.passable = false
        
        This property ensures that:
        1. A region is isolated if and only if ALL main roads are impassable
        2. Secondary roads do not affect isolation status
        3. The detection is consistent across all possible road configurations
        """
        main_roads, secondary_roads, congestion_levels = config
        
        # Setup mock database session
        mock_db_session = Mock()
        mock_query = Mock()
        mock_query.filter.return_value.all.return_value = main_roads
        mock_db_session.query.return_value = mock_query
        
        # Create analyzer
        analyzer = TrafficAnalyzer(mock_db_session)
        
        # Check isolation
        is_isolated = analyzer.check_region_isolation(1, congestion_levels)
        
        # Calculate expected isolation status
        # A region is isolated if ALL main roads are impassable
        all_main_roads_impassable = all(
            congestion_levels.get(road.id) == CongestionLevel.TIDAK_DAPAT_DILALUI
            for road in main_roads
        )
        
        # Verify the invariant
        assert is_isolated == all_main_roads_impassable, (
            f"Region isolation detection failed:\n"
            f"  Main roads: {len(main_roads)}\n"
            f"  Secondary roads: {len(secondary_roads)}\n"
            f"  All main roads impassable: {all_main_roads_impassable}\n"
            f"  Detected as isolated: {is_isolated}\n"
            f"  Congestion levels: {congestion_levels}"
        )

    @given(
        num_main_roads=st.integers(min_value=1, max_value=10),
        num_impassable=st.integers(min_value=0, max_value=10)
    )
    def test_partial_isolation_not_detected(self, num_main_roads, num_impassable):
        """
        Test that partial isolation (some but not all main roads impassable)
        is NOT detected as full isolation.
        
        **Validates: Requirements 2.4**
        """
        assume(0 < num_impassable < num_main_roads)  # Partial isolation only
        
        # Create main roads
        main_roads = []
        congestion_levels = {}
        
        for i in range(num_main_roads):
            road = Road(
                id=i + 1,
                region_id=1,
                road_name=f"Main Road {i+1}",
                road_type="primary",
                road_density=5.0,
                length_km=10.0,
                is_main_road=True
            )
            main_roads.append(road)
            
            # Make first num_impassable roads impassable, rest passable
            if i < num_impassable:
                congestion_levels[road.id] = CongestionLevel.TIDAK_DAPAT_DILALUI
            else:
                congestion_levels[road.id] = CongestionLevel.SEDANG
        
        # Setup mock
        mock_db_session = Mock()
        mock_query = Mock()
        mock_query.filter.return_value.all.return_value = main_roads
        mock_db_session.query.return_value = mock_query
        
        # Create analyzer
        analyzer = TrafficAnalyzer(mock_db_session)
        
        # Check isolation
        is_isolated = analyzer.check_region_isolation(1, congestion_levels)
        
        # Verify NOT isolated (since not all main roads are impassable)
        assert is_isolated is False, (
            f"Partial isolation incorrectly detected as full isolation:\n"
            f"  Total main roads: {num_main_roads}\n"
            f"  Impassable roads: {num_impassable}\n"
            f"  Should NOT be isolated, but detected as: {is_isolated}"
        )

    @given(num_main_roads=st.integers(min_value=1, max_value=10))
    def test_full_isolation_always_detected(self, num_main_roads):
        """
        Test that full isolation (all main roads impassable) is always detected.
        
        **Validates: Requirements 2.4**
        """
        # Create main roads, all impassable
        main_roads = []
        congestion_levels = {}
        
        for i in range(num_main_roads):
            road = Road(
                id=i + 1,
                region_id=1,
                road_name=f"Main Road {i+1}",
                road_type="primary",
                road_density=5.0,
                length_km=10.0,
                is_main_road=True
            )
            main_roads.append(road)
            congestion_levels[road.id] = CongestionLevel.TIDAK_DAPAT_DILALUI
        
        # Setup mock
        mock_db_session = Mock()
        mock_query = Mock()
        mock_query.filter.return_value.all.return_value = main_roads
        mock_db_session.query.return_value = mock_query
        
        # Create analyzer
        analyzer = TrafficAnalyzer(mock_db_session)
        
        # Check isolation
        is_isolated = analyzer.check_region_isolation(1, congestion_levels)
        
        # Verify isolated
        assert is_isolated is True, (
            f"Full isolation not detected:\n"
            f"  Total main roads: {num_main_roads}\n"
            f"  All roads impassable, but detected as: {is_isolated}"
        )

    @given(
        num_main_roads=st.integers(min_value=1, max_value=10),
        num_secondary_roads=st.integers(min_value=1, max_value=10)
    )
    def test_secondary_roads_do_not_affect_isolation(
        self,
        num_main_roads,
        num_secondary_roads
    ):
        """
        Test that secondary roads (is_main_road=False) do not affect
        isolation detection.
        
        **Validates: Requirements 2.4**
        """
        # Create main roads (all impassable)
        main_roads = []
        congestion_levels = {}
        
        for i in range(num_main_roads):
            road = Road(
                id=i + 1,
                region_id=1,
                road_name=f"Main Road {i+1}",
                road_type="primary",
                road_density=5.0,
                length_km=10.0,
                is_main_road=True
            )
            main_roads.append(road)
            congestion_levels[road.id] = CongestionLevel.TIDAK_DAPAT_DILALUI
        
        # Create secondary roads (all passable)
        for i in range(num_secondary_roads):
            road_id = num_main_roads + i + 1
            congestion_levels[road_id] = CongestionLevel.SEDANG
        
        # Setup mock
        mock_db_session = Mock()
        mock_query = Mock()
        mock_query.filter.return_value.all.return_value = main_roads
        mock_db_session.query.return_value = mock_query
        
        # Create analyzer
        analyzer = TrafficAnalyzer(mock_db_session)
        
        # Check isolation
        is_isolated = analyzer.check_region_isolation(1, congestion_levels)
        
        # Verify isolated (secondary roads should not matter)
        assert is_isolated is True, (
            f"Secondary roads affected isolation detection:\n"
            f"  Main roads: {num_main_roads} (all impassable)\n"
            f"  Secondary roads: {num_secondary_roads} (all passable)\n"
            f"  Should be isolated, but detected as: {is_isolated}"
        )

    def test_no_main_roads_not_isolated(self):
        """
        Test that a region with no main roads is not considered isolated.
        
        **Validates: Requirements 2.4**
        """
        # Setup mock with no main roads
        mock_db_session = Mock()
        mock_query = Mock()
        mock_query.filter.return_value.all.return_value = []
        mock_db_session.query.return_value = mock_query
        
        # Create analyzer
        analyzer = TrafficAnalyzer(mock_db_session)
        
        # Check isolation
        is_isolated = analyzer.check_region_isolation(1, {})
        
        # Verify NOT isolated
        assert is_isolated is False, (
            "Region with no main roads should not be isolated"
        )

    @given(
        num_main_roads=st.integers(min_value=1, max_value=10),
        passable_level=st.sampled_from([
            CongestionLevel.SEDANG,
            CongestionLevel.PARAH
        ])
    )
    def test_passable_roads_prevent_isolation(self, num_main_roads, passable_level):
        """
        Test that any passable main road (SEDANG or PARAH) prevents isolation,
        even if other main roads are impassable.
        
        **Validates: Requirements 2.4**
        """
        # Create main roads
        main_roads = []
        congestion_levels = {}
        
        for i in range(num_main_roads):
            road = Road(
                id=i + 1,
                region_id=1,
                road_name=f"Main Road {i+1}",
                road_type="primary",
                road_density=5.0,
                length_km=10.0,
                is_main_road=True
            )
            main_roads.append(road)
            
            # Make all roads impassable except the last one
            if i < num_main_roads - 1:
                congestion_levels[road.id] = CongestionLevel.TIDAK_DAPAT_DILALUI
            else:
                congestion_levels[road.id] = passable_level
        
        # Setup mock
        mock_db_session = Mock()
        mock_query = Mock()
        mock_query.filter.return_value.all.return_value = main_roads
        mock_db_session.query.return_value = mock_query
        
        # Create analyzer
        analyzer = TrafficAnalyzer(mock_db_session)
        
        # Check isolation
        is_isolated = analyzer.check_region_isolation(1, congestion_levels)
        
        # Verify NOT isolated (one passable road prevents isolation)
        assert is_isolated is False, (
            f"One passable road should prevent isolation:\n"
            f"  Total main roads: {num_main_roads}\n"
            f"  Last road level: {passable_level.value}\n"
            f"  Should NOT be isolated, but detected as: {is_isolated}"
        )

    @given(config=road_configuration())
    def test_isolation_idempotency(self, config):
        """
        Test that calling check_region_isolation multiple times with the same
        configuration returns the same result (idempotency).
        
        **Validates: Requirements 2.4**
        """
        main_roads, secondary_roads, congestion_levels = config
        
        # Setup mock
        mock_db_session = Mock()
        mock_query = Mock()
        mock_query.filter.return_value.all.return_value = main_roads
        mock_db_session.query.return_value = mock_query
        
        # Create analyzer
        analyzer = TrafficAnalyzer(mock_db_session)
        
        # Check isolation multiple times
        result1 = analyzer.check_region_isolation(1, congestion_levels)
        result2 = analyzer.check_region_isolation(1, congestion_levels)
        result3 = analyzer.check_region_isolation(1, congestion_levels)
        
        # Verify idempotency
        assert result1 == result2 == result3, (
            f"check_region_isolation not idempotent:\n"
            f"  Result 1: {result1}\n"
            f"  Result 2: {result2}\n"
            f"  Result 3: {result3}"
        )
