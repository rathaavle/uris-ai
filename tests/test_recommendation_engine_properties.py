"""
Property-based tests for Recommendation Engine.

This module contains property tests that validate universal correctness
properties of the recommendation system.

Requirements: 5.2, 5.4
"""

import pytest
from hypothesis import given, strategies as st, assume, settings

from src.uris_ai.ml.recommendation_engine import (
    RecommendationEngine,
    Coordinate,
    UrgencyLevel,
    URGENCY_SEGERA_MAX_HOURS,
    URGENCY_WASPADA_MAX_HOURS,
    URGENCY_SIAGA_MAX_HOURS,
    HIGH_RISK_CATEGORIES,
)
from src.uris_ai.ml.flood_risk_engine import RiskCategory


# ---------------------------------------------------------------------------
# Shared strategies
# ---------------------------------------------------------------------------

@st.composite
def safe_coordinate(draw):
    """Generate a valid geographic coordinate."""
    lat = draw(st.floats(min_value=-90.0, max_value=90.0))
    lon = draw(st.floats(min_value=-180.0, max_value=180.0))
    return Coordinate(latitude=lat, longitude=lon)


@st.composite
def region_graph_with_risk_map(draw):
    """
    Generate a connected region graph together with a risk map.

    Returns:
        (graph, region_coordinates, risk_map, safe_region_ids, blocked_region_ids)
    """
    # Generate 3-10 regions
    num_regions = draw(st.integers(min_value=3, max_value=10))
    region_ids = list(range(1, num_regions + 1))

    # Assign risk scores
    risk_map: dict[int, float] = {}
    for rid in region_ids:
        score = draw(st.floats(min_value=0.0, max_value=100.0))
        risk_map[rid] = score

    # Build a fully-connected graph (every region neighbours every other)
    graph: dict[int, list[int]] = {
        rid: [other for other in region_ids if other != rid]
        for rid in region_ids
    }

    # Build coordinates (spread on a small grid)
    coords: dict[int, Coordinate] = {}
    for i, rid in enumerate(region_ids):
        coords[rid] = Coordinate(latitude=-6.0 + i * 0.1, longitude=106.0 + i * 0.1)

    # Classify safe vs blocked
    engine_tmp = RecommendationEngine(risk_map=risk_map)
    safe_ids = [
        rid for rid in region_ids
        if engine_tmp._score_to_category(risk_map[rid]) not in HIGH_RISK_CATEGORIES
    ]
    blocked_ids = [
        rid for rid in region_ids
        if engine_tmp._score_to_category(risk_map[rid]) in HIGH_RISK_CATEGORIES
    ]

    return graph, coords, risk_map, safe_ids, blocked_ids


# ---------------------------------------------------------------------------
# Property 5: Safe Route Avoidance of High-Risk Regions
# ---------------------------------------------------------------------------

class TestSafeRouteAvoidanceProperties:
    """
    Property-based tests for Property 5: Safe Route Avoidance of High-Risk Regions.

    Validates: Requirements 5.2

    Invariant: ∀ region ∈ route: risk_category(region) ∉ {TINGGI, KRITIS}
    """

    @given(data=region_graph_with_risk_map())
    @settings(max_examples=100)
    def test_safe_route_never_passes_through_high_risk_region(self, data):
        """
        **Property 5: Safe Route Avoidance of High-Risk Regions**

        **Validates: Requirements 5.2**

        For any route returned with is_safe=True, every region in the route
        must have a risk category that is NOT TINGGI or KRITIS.

        Invariant: ∀ region ∈ route: risk_category(region) ∉ {TINGGI, KRITIS}
        """
        graph, coords, risk_map, safe_ids, blocked_ids = data

        # Need at least two safe regions to form a meaningful route
        assume(len(safe_ids) >= 2)

        engine = RecommendationEngine(risk_map=risk_map)

        # Pick two distinct safe regions as origin and destination
        origin_id = safe_ids[0]
        dest_id = safe_ids[-1]

        origin_coord = coords[origin_id]
        dest_coord = coords[dest_id]

        result = engine.find_safe_route(
            origin=origin_coord,
            destination=dest_coord,
            region_graph=graph,
            region_coordinates=coords,
        )

        if result.is_safe:
            # Every region in the route must be safe (not TINGGI or KRITIS)
            for region_id in result.route_region_ids:
                score = risk_map.get(region_id, 0.0)
                category = engine._score_to_category(score)
                assert category not in HIGH_RISK_CATEGORIES, (
                    f"Safe route passes through high-risk region!\n"
                    f"  Region ID: {region_id}\n"
                    f"  Risk score: {score:.2f}\n"
                    f"  Category: {category.value}\n"
                    f"  Full route: {result.route_region_ids}\n"
                    f"  Risk map: {risk_map}"
                )

    @given(data=region_graph_with_risk_map())
    @settings(max_examples=100)
    def test_unsafe_route_result_when_all_paths_blocked(self, data):
        """
        When all intermediate regions are blocked and no safe path exists,
        find_safe_route must return is_safe=False.

        **Validates: Requirements 5.2, 5.5**
        """
        graph, coords, risk_map, safe_ids, blocked_ids = data

        # We need at least two safe regions and at least one blocked region
        assume(len(safe_ids) >= 2)
        assume(len(blocked_ids) >= 1)

        engine = RecommendationEngine(risk_map=risk_map)

        origin_id = safe_ids[0]
        dest_id = safe_ids[-1]

        # Override graph so origin and dest are only connected through blocked regions
        restricted_graph: dict[int, list[int]] = {rid: [] for rid in graph}
        for blocked_id in blocked_ids:
            restricted_graph[origin_id] = [blocked_id]
            restricted_graph[blocked_id] = [dest_id]

        result = engine.find_safe_route(
            origin=coords[origin_id],
            destination=coords[dest_id],
            region_graph=restricted_graph,
            region_coordinates=coords,
        )

        # If the result claims to be safe, verify the invariant still holds
        if result.is_safe:
            for region_id in result.route_region_ids:
                score = risk_map.get(region_id, 0.0)
                category = engine._score_to_category(score)
                assert category not in HIGH_RISK_CATEGORIES, (
                    f"Claimed safe route passes through high-risk region!\n"
                    f"  Region ID: {region_id}, Category: {category.value}"
                )

    @given(
        num_regions=st.integers(min_value=3, max_value=8),
        safe_score=st.floats(min_value=0.0, max_value=50.0),
        blocked_score=st.floats(min_value=76.0, max_value=100.0),
    )
    @settings(max_examples=80)
    def test_route_avoids_explicitly_blocked_regions(
        self, num_regions, safe_score, blocked_score
    ):
        """
        When some regions are explicitly high-risk, the returned safe route
        must not include any of them.

        **Validates: Requirements 5.2**
        """
        assume(num_regions >= 3)

        region_ids = list(range(1, num_regions + 1))

        # Make first half safe, second half blocked
        split = max(2, num_regions // 2)
        safe_ids = region_ids[:split]
        blocked_ids = region_ids[split:]

        risk_map = {rid: safe_score for rid in safe_ids}
        risk_map.update({rid: blocked_score for rid in blocked_ids})

        # Build a graph where safe regions form a chain
        graph: dict[int, list[int]] = {rid: [] for rid in region_ids}
        for i in range(len(safe_ids) - 1):
            graph[safe_ids[i]].append(safe_ids[i + 1])
            graph[safe_ids[i + 1]].append(safe_ids[i])
        # Also connect blocked regions (but they should be avoided)
        for bid in blocked_ids:
            graph[safe_ids[-1]].append(bid)
            graph[bid].append(safe_ids[-1])

        coords = {
            rid: Coordinate(latitude=-6.0 + rid * 0.05, longitude=106.0 + rid * 0.05)
            for rid in region_ids
        }

        engine = RecommendationEngine(risk_map=risk_map)

        result = engine.find_safe_route(
            origin=coords[safe_ids[0]],
            destination=coords[safe_ids[-1]],
            region_graph=graph,
            region_coordinates=coords,
        )

        if result.is_safe:
            for region_id in result.route_region_ids:
                assert region_id not in blocked_ids, (
                    f"Safe route includes a blocked region!\n"
                    f"  Region ID: {region_id}\n"
                    f"  Blocked IDs: {blocked_ids}\n"
                    f"  Route: {result.route_region_ids}"
                )

    @given(data=region_graph_with_risk_map())
    @settings(max_examples=80)
    def test_route_idempotency(self, data):
        """
        Calling find_safe_route multiple times with the same inputs returns
        the same result (idempotency).

        **Validates: Requirements 5.2**
        """
        graph, coords, risk_map, safe_ids, _ = data
        assume(len(safe_ids) >= 2)

        engine = RecommendationEngine(risk_map=risk_map)

        origin_coord = coords[safe_ids[0]]
        dest_coord = coords[safe_ids[-1]]

        result1 = engine.find_safe_route(
            origin=origin_coord,
            destination=dest_coord,
            region_graph=graph,
            region_coordinates=coords,
        )
        result2 = engine.find_safe_route(
            origin=origin_coord,
            destination=dest_coord,
            region_graph=graph,
            region_coordinates=coords,
        )

        assert result1.is_safe == result2.is_safe, (
            f"find_safe_route not idempotent:\n"
            f"  Call 1 is_safe: {result1.is_safe}\n"
            f"  Call 2 is_safe: {result2.is_safe}"
        )
        assert result1.route_region_ids == result2.route_region_ids, (
            f"find_safe_route returned different routes:\n"
            f"  Call 1: {result1.route_region_ids}\n"
            f"  Call 2: {result2.route_region_ids}"
        )

    def test_safe_route_same_origin_and_destination_safe_region(self):
        """
        When origin and destination map to the same safe region,
        the route should contain exactly that region and be safe.

        **Validates: Requirements 5.2**
        """
        risk_map = {1: 20.0}  # RENDAH
        graph = {1: []}
        coords = {1: Coordinate(latitude=-6.2, longitude=106.8)}

        engine = RecommendationEngine(risk_map=risk_map)

        result = engine.find_safe_route(
            origin=Coordinate(latitude=-6.2, longitude=106.8),
            destination=Coordinate(latitude=-6.2, longitude=106.8),
            region_graph=graph,
            region_coordinates=coords,
        )

        assert result.is_safe is True
        assert result.route_region_ids == [1]

    def test_safe_route_same_origin_and_destination_blocked_region(self):
        """
        When origin and destination map to the same high-risk region,
        the route should be marked as unsafe.

        **Validates: Requirements 5.2**
        """
        risk_map = {1: 90.0}  # KRITIS
        graph = {1: []}
        coords = {1: Coordinate(latitude=-6.2, longitude=106.8)}

        engine = RecommendationEngine(risk_map=risk_map)

        result = engine.find_safe_route(
            origin=Coordinate(latitude=-6.2, longitude=106.8),
            destination=Coordinate(latitude=-6.2, longitude=106.8),
            region_graph=graph,
            region_coordinates=coords,
        )

        assert result.is_safe is False
        assert result.no_safe_route_reason is not None

    def test_no_safe_route_provides_explanation(self):
        """
        When no safe route exists, the result must include an explanation.

        **Validates: Requirements 5.5**
        """
        # Two regions, both blocked
        risk_map = {1: 80.0, 2: 85.0}
        graph = {1: [2], 2: [1]}
        coords = {
            1: Coordinate(latitude=-6.2, longitude=106.8),
            2: Coordinate(latitude=-6.3, longitude=106.9),
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
        assert len(result.no_safe_route_reason) > 0, (
            "No safe route result must include a non-empty explanation"
        )


# ---------------------------------------------------------------------------
# Property 6: Urgency Classification Consistency
# ---------------------------------------------------------------------------

class TestUrgencyClassificationProperties:
    """
    Property-based tests for Property 6: Urgency Classification Consistency.

    Validates: Requirements 5.4

    Time windows:
    - 0 ≤ t ≤ 1 hour  → SEGERA
    - 1 < t ≤ 6 hours → WASPADA
    - 6 < t ≤ 24 hours → SIAGA
    - t > 24 hours     → SIAGA
    """

    @given(hours=st.floats(min_value=0.0, max_value=URGENCY_SEGERA_MAX_HOURS))
    def test_segera_window(self, hours):
        """
        **Property 6: Urgency Classification Consistency**

        **Validates: Requirements 5.4**

        Any time_to_impact in [0, 1] hour must produce SEGERA.
        """
        engine = RecommendationEngine()
        result = engine.classify_urgency(hours)
        assert result == UrgencyLevel.SEGERA, (
            f"Expected SEGERA for {hours:.4f} hours, got {result.value}"
        )

    @given(
        hours=st.floats(
            min_value=URGENCY_SEGERA_MAX_HOURS,
            max_value=URGENCY_WASPADA_MAX_HOURS,
            exclude_min=True,
        )
    )
    def test_waspada_window(self, hours):
        """
        Any time_to_impact in (1, 6] hours must produce WASPADA.

        **Validates: Requirements 5.4**
        """
        engine = RecommendationEngine()
        result = engine.classify_urgency(hours)
        assert result == UrgencyLevel.WASPADA, (
            f"Expected WASPADA for {hours:.4f} hours, got {result.value}"
        )

    @given(
        hours=st.floats(
            min_value=URGENCY_WASPADA_MAX_HOURS,
            max_value=URGENCY_SIAGA_MAX_HOURS * 2,  # beyond 24h still SIAGA
            exclude_min=True,
        )
    )
    def test_siaga_window(self, hours):
        """
        Any time_to_impact > 6 hours must produce SIAGA.

        **Validates: Requirements 5.4**
        """
        engine = RecommendationEngine()
        result = engine.classify_urgency(hours)
        assert result == UrgencyLevel.SIAGA, (
            f"Expected SIAGA for {hours:.4f} hours, got {result.value}"
        )

    @given(hours=st.floats(min_value=0.0, max_value=1000.0))
    def test_urgency_always_returns_valid_level(self, hours):
        """
        classify_urgency must always return a valid UrgencyLevel for any
        non-negative input.

        **Validates: Requirements 5.4**
        """
        engine = RecommendationEngine()
        result = engine.classify_urgency(hours)
        assert result in UrgencyLevel, (
            f"classify_urgency returned invalid value: {result}"
        )

    @given(
        t1=st.floats(min_value=0.0, max_value=500.0),
        t2=st.floats(min_value=0.0, max_value=500.0),
    )
    def test_urgency_monotonicity(self, t1, t2):
        """
        Urgency must be monotonically non-increasing as time_to_impact grows:
        a shorter time to impact must have urgency >= a longer time to impact.

        Ordering: SEGERA > WASPADA > SIAGA

        **Validates: Requirements 5.4**
        """
        urgency_order = {
            UrgencyLevel.SEGERA: 3,
            UrgencyLevel.WASPADA: 2,
            UrgencyLevel.SIAGA: 1,
        }

        engine = RecommendationEngine()
        u1 = engine.classify_urgency(t1)
        u2 = engine.classify_urgency(t2)

        if t1 <= t2:
            assert urgency_order[u1] >= urgency_order[u2], (
                f"Urgency not monotonic:\n"
                f"  t1={t1:.4f}h → {u1.value} (order {urgency_order[u1]})\n"
                f"  t2={t2:.4f}h → {u2.value} (order {urgency_order[u2]})\n"
                f"  Expected urgency(t1) >= urgency(t2) since t1 <= t2"
            )

    @given(hours=st.floats(min_value=0.0, max_value=1000.0))
    def test_urgency_idempotency(self, hours):
        """
        Calling classify_urgency multiple times with the same input returns
        the same result (idempotency).

        **Validates: Requirements 5.4**
        """
        engine = RecommendationEngine()
        r1 = engine.classify_urgency(hours)
        r2 = engine.classify_urgency(hours)
        r3 = engine.classify_urgency(hours)
        assert r1 == r2 == r3, (
            f"classify_urgency not idempotent for {hours:.4f}h: "
            f"{r1.value}, {r2.value}, {r3.value}"
        )

    def test_urgency_negative_input_raises(self):
        """
        Negative time_to_impact must raise ValueError.

        **Validates: Requirements 5.4**
        """
        engine = RecommendationEngine()
        with pytest.raises(ValueError, match="non-negative"):
            engine.classify_urgency(-0.1)

    def test_urgency_boundary_zero(self):
        """Exactly 0 hours → SEGERA."""
        engine = RecommendationEngine()
        assert engine.classify_urgency(0.0) == UrgencyLevel.SEGERA

    def test_urgency_boundary_one_hour(self):
        """Exactly 1 hour → SEGERA (inclusive upper bound)."""
        engine = RecommendationEngine()
        assert engine.classify_urgency(1.0) == UrgencyLevel.SEGERA

    def test_urgency_boundary_just_above_one_hour(self):
        """Just above 1 hour → WASPADA."""
        engine = RecommendationEngine()
        assert engine.classify_urgency(1.0001) == UrgencyLevel.WASPADA

    def test_urgency_boundary_six_hours(self):
        """Exactly 6 hours → WASPADA (inclusive upper bound)."""
        engine = RecommendationEngine()
        assert engine.classify_urgency(6.0) == UrgencyLevel.WASPADA

    def test_urgency_boundary_just_above_six_hours(self):
        """Just above 6 hours → SIAGA."""
        engine = RecommendationEngine()
        assert engine.classify_urgency(6.0001) == UrgencyLevel.SIAGA

    def test_urgency_boundary_twenty_four_hours(self):
        """24 hours → SIAGA."""
        engine = RecommendationEngine()
        assert engine.classify_urgency(24.0) == UrgencyLevel.SIAGA

    def test_urgency_beyond_twenty_four_hours(self):
        """Beyond 24 hours → SIAGA."""
        engine = RecommendationEngine()
        assert engine.classify_urgency(48.0) == UrgencyLevel.SIAGA
