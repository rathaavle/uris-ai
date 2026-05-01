"""
Property-based tests for Service Accessibility Module.

This module contains property tests that validate universal correctness
properties of the service accessibility system.

Requirements: 3.2
"""

import pytest
from hypothesis import given, strategies as st, assume
from unittest.mock import Mock
import math

from src.uris_ai.ml.service_accessibility import ServiceAccessibilityModule
from src.uris_ai.models.database import PublicFacility


# Custom strategies for generating test data
@st.composite
def facility_with_alternatives(draw):
    """
    Generate a facility with potential alternatives.
    
    Returns a tuple of (facility, alternatives, expected_within_radius)
    """
    # Generate main facility coordinates
    # Use realistic lat/lon ranges for Jakarta/Jawa Barat
    facility_lat = draw(st.floats(min_value=-7.0, max_value=-6.0))
    facility_lon = draw(st.floats(min_value=106.0, max_value=108.0))
    facility_type = draw(st.sampled_from(["hospital", "clinic", "school", "government"]))
    
    # Create main facility
    facility = PublicFacility(
        id=1,
        region_id=1,
        name="Main Facility",
        type=facility_type,
        latitude=facility_lat,
        longitude=facility_lon,
        capacity=100,
        is_operational=False  # Affected facility
    )
    
    # Generate 1-10 alternative facilities
    num_alternatives = draw(st.integers(min_value=1, max_value=10))
    alternatives = []
    expected_within_radius = []
    
    for i in range(num_alternatives):
        # Generate distance in km (0-20 km range)
        distance_km = draw(st.floats(min_value=0.1, max_value=20.0))
        
        # Generate random bearing (0-360 degrees)
        bearing = draw(st.floats(min_value=0.0, max_value=360.0))
        
        # Calculate lat/lon at given distance and bearing
        alt_lat, alt_lon = _calculate_destination_point(
            facility_lat, facility_lon, distance_km, bearing
        )
        
        alt = PublicFacility(
            id=i + 2,
            region_id=2,
            name=f"Alternative {i+1}",
            type=facility_type,
            latitude=alt_lat,
            longitude=alt_lon,
            capacity=100,
            is_operational=True
        )
        alternatives.append(alt)
        
        # Track which alternatives should be within 10km radius
        if distance_km <= 10.0:
            expected_within_radius.append(alt)
    
    return facility, alternatives, expected_within_radius


def _calculate_destination_point(lat: float, lon: float, distance_km: float, bearing_deg: float):
    """
    Calculate destination point given distance and bearing from start point.
    
    Args:
        lat: Starting latitude (degrees)
        lon: Starting longitude (degrees)
        distance_km: Distance in kilometers
        bearing_deg: Bearing in degrees (0-360)
        
    Returns:
        Tuple of (destination_lat, destination_lon)
    """
    R = 6371.0  # Earth's radius in km
    
    lat_rad = math.radians(lat)
    lon_rad = math.radians(lon)
    bearing_rad = math.radians(bearing_deg)
    
    # Calculate destination point
    dest_lat_rad = math.asin(
        math.sin(lat_rad) * math.cos(distance_km / R) +
        math.cos(lat_rad) * math.sin(distance_km / R) * math.cos(bearing_rad)
    )
    
    dest_lon_rad = lon_rad + math.atan2(
        math.sin(bearing_rad) * math.sin(distance_km / R) * math.cos(lat_rad),
        math.cos(distance_km / R) - math.sin(lat_rad) * math.sin(dest_lat_rad)
    )
    
    return math.degrees(dest_lat_rad), math.degrees(dest_lon_rad)


def _calculate_haversine_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Calculate Haversine distance between two points."""
    R = 6371.0
    
    lat1_rad = math.radians(lat1)
    lon1_rad = math.radians(lon1)
    lat2_rad = math.radians(lat2)
    lon2_rad = math.radians(lon2)
    
    dlat = lat2_rad - lat1_rad
    dlon = lon2_rad - lon1_rad
    
    a = (math.sin(dlat / 2) ** 2 +
         math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(dlon / 2) ** 2)
    c = 2 * math.asin(math.sqrt(a))
    
    return R * c


class TestServiceAccessibilityProperties:
    """Property-based tests for Service Accessibility Module."""

    @given(config=facility_with_alternatives())
    def test_alternative_facility_radius_constraint(self, config):
        """
        **Property 3: Alternative Facility Radius Constraint**
        
        **Validates: Requirements 3.2**
        
        For every disrupted public facility, all recommended alternative facilities
        must be within a maximum radius of 10 km from the original facility.
        
        Invariant: ∀ alt ∈ alternatives: distance(facility, alt) ≤ 10km
        
        This property ensures that:
        1. All returned alternatives are within the 10km radius
        2. No alternatives outside the radius are returned
        3. The distance calculation is accurate (Haversine formula)
        """
        facility, all_alternatives, expected_within_radius = config
        
        # Setup mock database session
        mock_db_session = Mock()
        
        # Mock the query for the original facility
        mock_facility_query = Mock()
        mock_facility_query.filter.return_value.first.return_value = facility
        
        # Mock the query for alternative facilities
        mock_alternatives_query = Mock()
        mock_alternatives_query.filter.return_value.all.return_value = all_alternatives
        
        # Setup query mock to return different results based on call
        call_count = [0]
        def mock_query(model):
            call_count[0] += 1
            if call_count[0] == 1:
                return mock_facility_query
            else:
                return mock_alternatives_query
        
        mock_db_session.query = mock_query
        
        # Create module
        module = ServiceAccessibilityModule(mock_db_session)
        
        # Find alternatives with 10km radius
        alternatives = module.find_alternative_facilities(
            facility.id,
            radius_km=10.0
        )
        
        # Verify all returned alternatives are within 10km
        for alt in alternatives:
            distance = _calculate_haversine_distance(
                facility.latitude,
                facility.longitude,
                alt.latitude,
                alt.longitude
            )
            
            assert distance <= 10.0, (
                f"Alternative facility {alt.id} is outside 10km radius:\n"
                f"  Facility: ({facility.latitude}, {facility.longitude})\n"
                f"  Alternative: ({alt.latitude}, {alt.longitude})\n"
                f"  Distance: {distance:.2f} km\n"
                f"  Maximum allowed: 10.0 km"
            )
        
        # Verify no alternatives outside 10km are returned
        returned_ids = {alt.id for alt in alternatives}
        for alt in all_alternatives:
            distance = _calculate_haversine_distance(
                facility.latitude,
                facility.longitude,
                alt.latitude,
                alt.longitude
            )
            
            if distance > 10.0:
                assert alt.id not in returned_ids, (
                    f"Alternative facility {alt.id} outside 10km was incorrectly returned:\n"
                    f"  Distance: {distance:.2f} km\n"
                    f"  Maximum allowed: 10.0 km"
                )

    @given(
        facility_lat=st.floats(min_value=-7.0, max_value=-6.0),
        facility_lon=st.floats(min_value=106.0, max_value=108.0),
        radius_km=st.floats(min_value=1.0, max_value=20.0)
    )
    def test_custom_radius_constraint(self, facility_lat, facility_lon, radius_km):
        """
        Test that custom radius values are respected.
        
        **Validates: Requirements 3.2**
        """
        facility_type = "hospital"
        
        # Create main facility
        facility = PublicFacility(
            id=1,
            region_id=1,
            name="Main Facility",
            type=facility_type,
            latitude=facility_lat,
            longitude=facility_lon,
            capacity=100,
            is_operational=False
        )
        
        # Create alternatives at various distances
        alternatives = []
        for i, distance in enumerate([radius_km * 0.5, radius_km * 0.9, radius_km * 1.1, radius_km * 1.5]):
            alt_lat, alt_lon = _calculate_destination_point(
                facility_lat, facility_lon, distance, 45.0 * i
            )
            
            alt = PublicFacility(
                id=i + 2,
                region_id=2,
                name=f"Alternative {i+1}",
                type=facility_type,
                latitude=alt_lat,
                longitude=alt_lon,
                capacity=100,
                is_operational=True
            )
            alternatives.append(alt)
        
        # Setup mock
        mock_db_session = Mock()
        mock_facility_query = Mock()
        mock_facility_query.filter.return_value.first.return_value = facility
        mock_alternatives_query = Mock()
        mock_alternatives_query.filter.return_value.all.return_value = alternatives
        
        call_count = [0]
        def mock_query(model):
            call_count[0] += 1
            if call_count[0] == 1:
                return mock_facility_query
            else:
                return mock_alternatives_query
        
        mock_db_session.query = mock_query
        
        # Create module
        module = ServiceAccessibilityModule(mock_db_session)
        
        # Find alternatives with custom radius
        results = module.find_alternative_facilities(facility.id, radius_km=radius_km)
        
        # Verify all results are within custom radius
        for alt in results:
            distance = _calculate_haversine_distance(
                facility.latitude,
                facility.longitude,
                alt.latitude,
                alt.longitude
            )
            
            assert distance <= radius_km, (
                f"Alternative outside custom radius {radius_km:.2f} km:\n"
                f"  Distance: {distance:.2f} km"
            )

    @given(
        num_same_type=st.integers(min_value=1, max_value=5),
        num_different_type=st.integers(min_value=1, max_value=5)
    )
    def test_only_same_type_facilities_returned(self, num_same_type, num_different_type):
        """
        Test that only facilities of the same type are returned as alternatives.
        
        **Validates: Requirements 3.2**
        """
        facility_lat = -6.5
        facility_lon = 106.8
        facility_type = "hospital"
        
        # Create main facility
        facility = PublicFacility(
            id=1,
            region_id=1,
            name="Main Hospital",
            type=facility_type,
            latitude=facility_lat,
            longitude=facility_lon,
            capacity=100,
            is_operational=False
        )
        
        # Create alternatives of same type (within radius)
        same_type_alternatives = []
        for i in range(num_same_type):
            alt_lat, alt_lon = _calculate_destination_point(
                facility_lat, facility_lon, 5.0, 45.0 * i
            )
            
            alt = PublicFacility(
                id=i + 2,
                region_id=2,
                name=f"Hospital {i+1}",
                type=facility_type,
                latitude=alt_lat,
                longitude=alt_lon,
                capacity=100,
                is_operational=True
            )
            same_type_alternatives.append(alt)
        
        # Create alternatives of different type (within radius)
        different_type_alternatives = []
        for i in range(num_different_type):
            alt_lat, alt_lon = _calculate_destination_point(
                facility_lat, facility_lon, 5.0, 180.0 + 45.0 * i
            )
            
            alt = PublicFacility(
                id=num_same_type + i + 2,
                region_id=2,
                name=f"School {i+1}",
                type="school",  # Different type
                latitude=alt_lat,
                longitude=alt_lon,
                capacity=100,
                is_operational=True
            )
            different_type_alternatives.append(alt)
        
        # Setup mock - only return same type facilities
        mock_db_session = Mock()
        mock_facility_query = Mock()
        mock_facility_query.filter.return_value.first.return_value = facility
        mock_alternatives_query = Mock()
        mock_alternatives_query.filter.return_value.all.return_value = same_type_alternatives
        
        call_count = [0]
        def mock_query(model):
            call_count[0] += 1
            if call_count[0] == 1:
                return mock_facility_query
            else:
                return mock_alternatives_query
        
        mock_db_session.query = mock_query
        
        # Create module
        module = ServiceAccessibilityModule(mock_db_session)
        
        # Find alternatives
        results = module.find_alternative_facilities(facility.id, radius_km=10.0)
        
        # Verify all results are of the same type
        for alt in results:
            assert alt.type == facility_type, (
                f"Alternative facility has wrong type:\n"
                f"  Expected: {facility_type}\n"
                f"  Got: {alt.type}"
            )

    @given(config=facility_with_alternatives())
    def test_non_operational_facilities_excluded(self, config):
        """
        Test that non-operational facilities are not returned as alternatives.
        
        **Validates: Requirements 3.2**
        """
        facility, all_alternatives, _ = config
        
        # Mark some alternatives as non-operational
        for i, alt in enumerate(all_alternatives):
            if i % 2 == 0:
                alt.is_operational = False
        
        # Setup mock
        mock_db_session = Mock()
        mock_facility_query = Mock()
        mock_facility_query.filter.return_value.first.return_value = facility
        
        # Filter to only operational facilities (simulating database query)
        operational_alternatives = [alt for alt in all_alternatives if alt.is_operational]
        mock_alternatives_query = Mock()
        mock_alternatives_query.filter.return_value.all.return_value = operational_alternatives
        
        call_count = [0]
        def mock_query(model):
            call_count[0] += 1
            if call_count[0] == 1:
                return mock_facility_query
            else:
                return mock_alternatives_query
        
        mock_db_session.query = mock_query
        
        # Create module
        module = ServiceAccessibilityModule(mock_db_session)
        
        # Find alternatives
        results = module.find_alternative_facilities(facility.id, radius_km=10.0)
        
        # Verify all results are operational
        for alt in results:
            assert alt.is_operational is True, (
                f"Non-operational facility {alt.id} was returned as alternative"
            )

    @given(config=facility_with_alternatives())
    def test_original_facility_excluded_from_alternatives(self, config):
        """
        Test that the original facility is not included in its own alternatives.
        
        **Validates: Requirements 3.2**
        """
        facility, all_alternatives, _ = config
        
        # Setup mock
        mock_db_session = Mock()
        mock_facility_query = Mock()
        mock_facility_query.filter.return_value.first.return_value = facility
        mock_alternatives_query = Mock()
        mock_alternatives_query.filter.return_value.all.return_value = all_alternatives
        
        call_count = [0]
        def mock_query(model):
            call_count[0] += 1
            if call_count[0] == 1:
                return mock_facility_query
            else:
                return mock_alternatives_query
        
        mock_db_session.query = mock_query
        
        # Create module
        module = ServiceAccessibilityModule(mock_db_session)
        
        # Find alternatives
        results = module.find_alternative_facilities(facility.id, radius_km=10.0)
        
        # Verify original facility is not in results
        result_ids = {alt.id for alt in results}
        assert facility.id not in result_ids, (
            f"Original facility {facility.id} was included in its own alternatives"
        )

    def test_no_alternatives_when_facility_not_found(self):
        """
        Test that empty list is returned when facility is not found.
        
        **Validates: Requirements 3.2**
        """
        # Setup mock with no facility found
        mock_db_session = Mock()
        mock_query = Mock()
        mock_query.filter.return_value.first.return_value = None
        mock_db_session.query.return_value = mock_query
        
        # Create module
        module = ServiceAccessibilityModule(mock_db_session)
        
        # Find alternatives for non-existent facility
        results = module.find_alternative_facilities(999, radius_km=10.0)
        
        # Verify empty list returned
        assert results == [], (
            "Non-empty list returned for non-existent facility"
        )

    @given(
        facility_lat=st.floats(min_value=-7.0, max_value=-6.0),
        facility_lon=st.floats(min_value=106.0, max_value=108.0)
    )
    def test_haversine_distance_symmetry(self, facility_lat, facility_lon):
        """
        Test that Haversine distance calculation is symmetric.
        
        distance(A, B) should equal distance(B, A)
        
        **Validates: Requirements 3.2**
        """
        # Create two facilities
        facility1 = PublicFacility(
            id=1,
            region_id=1,
            name="Facility 1",
            type="hospital",
            latitude=facility_lat,
            longitude=facility_lon,
            capacity=100,
            is_operational=True
        )
        
        # Create second facility at some distance
        alt_lat, alt_lon = _calculate_destination_point(
            facility_lat, facility_lon, 5.0, 45.0
        )
        
        facility2 = PublicFacility(
            id=2,
            region_id=2,
            name="Facility 2",
            type="hospital",
            latitude=alt_lat,
            longitude=alt_lon,
            capacity=100,
            is_operational=True
        )
        
        # Calculate distances both ways
        distance_1_to_2 = _calculate_haversine_distance(
            facility1.latitude, facility1.longitude,
            facility2.latitude, facility2.longitude
        )
        
        distance_2_to_1 = _calculate_haversine_distance(
            facility2.latitude, facility2.longitude,
            facility1.latitude, facility1.longitude
        )
        
        # Verify symmetry (allow small floating point error)
        assert abs(distance_1_to_2 - distance_2_to_1) < 0.001, (
            f"Haversine distance not symmetric:\n"
            f"  Distance 1->2: {distance_1_to_2:.6f} km\n"
            f"  Distance 2->1: {distance_2_to_1:.6f} km"
        )
