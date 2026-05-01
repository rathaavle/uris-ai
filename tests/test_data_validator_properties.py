"""
Property-Based Tests for Data Validator.

Feature: uris-ai, Property 7: Data Validation Rejection of Invalid Data
Validates: Requirements 7.4

This module tests that the Data_Validator correctly rejects invalid data
according to schema definitions using property-based testing with Hypothesis.
"""

import pytest
from hypothesis import given, strategies as st, assume, settings, HealthCheck
from datetime import datetime, timedelta
from typing import Any, Dict

from src.uris_ai.data.validator import DataValidator
from src.uris_ai.data.models import DataType, WeatherData, FloodEvent


# ============================================================================
# Hypothesis Strategies for Generating Test Data
# ============================================================================

@st.composite
def valid_weather_data(draw):
    """Generate valid weather data."""
    return {
        "region_id": draw(st.integers(min_value=1, max_value=10000)),
        "date": draw(st.datetimes(
            min_value=datetime(2020, 1, 1),
            max_value=datetime(2030, 12, 31)
        )),
        "rainfall": draw(st.floats(min_value=0, max_value=500)),
        "humidity": draw(st.floats(min_value=0, max_value=100)),
        "temperature": draw(st.floats(min_value=15, max_value=40)),
        "wind_speed": draw(st.one_of(
            st.none(),
            st.floats(min_value=0, max_value=100)
        )),
    }


@st.composite
def invalid_weather_data_missing_fields(draw):
    """Generate weather data with missing required fields."""
    # Start with valid data
    data = {
        "region_id": draw(st.integers(min_value=1, max_value=10000)),
        "date": draw(st.datetimes(
            min_value=datetime(2020, 1, 1),
            max_value=datetime(2030, 12, 31)
        )),
        "rainfall": draw(st.floats(min_value=0, max_value=500)),
        "humidity": draw(st.floats(min_value=0, max_value=100)),
        "temperature": draw(st.floats(min_value=15, max_value=40)),
    }
    
    # Remove at least one required field
    required_fields = ["region_id", "date", "rainfall", "humidity", "temperature"]
    field_to_remove = draw(st.sampled_from(required_fields))
    del data[field_to_remove]
    
    return data


@st.composite
def invalid_weather_data_out_of_range(draw):
    """Generate weather data with out-of-range values."""
    field_to_invalidate = draw(st.sampled_from([
        "rainfall", "humidity", "temperature", "wind_speed"
    ]))
    
    data = {
        "region_id": draw(st.integers(min_value=1, max_value=10000)),
        "date": draw(st.datetimes(
            min_value=datetime(2020, 1, 1),
            max_value=datetime(2030, 12, 31)
        )),
        "rainfall": draw(st.floats(min_value=0, max_value=500)),
        "humidity": draw(st.floats(min_value=0, max_value=100)),
        "temperature": draw(st.floats(min_value=15, max_value=40)),
    }
    
    # Invalidate the chosen field
    if field_to_invalidate == "rainfall":
        data["rainfall"] = draw(st.one_of(
            st.floats(min_value=-1000, max_value=-0.1),
            st.floats(min_value=500.1, max_value=10000)
        ))
    elif field_to_invalidate == "humidity":
        data["humidity"] = draw(st.one_of(
            st.floats(min_value=-100, max_value=-0.1),
            st.floats(min_value=100.1, max_value=200)
        ))
    elif field_to_invalidate == "temperature":
        data["temperature"] = draw(st.one_of(
            st.floats(min_value=-50, max_value=14.9),
            st.floats(min_value=40.1, max_value=100)
        ))
    elif field_to_invalidate == "wind_speed":
        data["wind_speed"] = draw(st.one_of(
            st.floats(min_value=-100, max_value=-0.1),
            st.floats(min_value=100.1, max_value=500)
        ))
    
    return data


@st.composite
def invalid_weather_data_wrong_types(draw):
    """Generate weather data with wrong data types."""
    field_to_invalidate = draw(st.sampled_from([
        "region_id", "rainfall", "humidity", "temperature"
    ]))
    
    data = {
        "region_id": draw(st.integers(min_value=1, max_value=10000)),
        "date": draw(st.datetimes(
            min_value=datetime(2020, 1, 1),
            max_value=datetime(2030, 12, 31)
        )),
        "rainfall": draw(st.floats(min_value=0, max_value=500)),
        "humidity": draw(st.floats(min_value=0, max_value=100)),
        "temperature": draw(st.floats(min_value=15, max_value=40)),
    }
    
    # Invalidate the chosen field with wrong type
    if field_to_invalidate == "region_id":
        data["region_id"] = draw(st.text(min_size=1, max_size=10))
    elif field_to_invalidate == "rainfall":
        data["rainfall"] = draw(st.text(min_size=1, max_size=10))
    elif field_to_invalidate == "humidity":
        data["humidity"] = draw(st.text(min_size=1, max_size=10))
    elif field_to_invalidate == "temperature":
        data["temperature"] = draw(st.text(min_size=1, max_size=10))
    
    return data


@st.composite
def valid_flood_event_data(draw):
    """Generate valid flood event data."""
    return {
        "region_id": draw(st.integers(min_value=1, max_value=10000)),
        "date": draw(st.datetimes(
            min_value=datetime(2020, 1, 1),
            max_value=datetime(2030, 12, 31)
        )),
        "severity": draw(st.integers(min_value=1, max_value=4)),
        "water_level": draw(st.one_of(
            st.none(),
            st.floats(min_value=0, max_value=1000)
        )),
        "duration_hours": draw(st.one_of(
            st.none(),
            st.integers(min_value=0, max_value=1000)
        )),
        "affected_area_km2": draw(st.one_of(
            st.none(),
            st.floats(min_value=0, max_value=10000)
        )),
    }


@st.composite
def invalid_flood_event_data_missing_fields(draw):
    """Generate flood event data with missing required fields."""
    data = {
        "region_id": draw(st.integers(min_value=1, max_value=10000)),
        "date": draw(st.datetimes(
            min_value=datetime(2020, 1, 1),
            max_value=datetime(2030, 12, 31)
        )),
        "severity": draw(st.integers(min_value=1, max_value=4)),
    }
    
    # Remove at least one required field
    required_fields = ["region_id", "date", "severity"]
    field_to_remove = draw(st.sampled_from(required_fields))
    del data[field_to_remove]
    
    return data


@st.composite
def invalid_flood_event_data_out_of_range(draw):
    """Generate flood event data with out-of-range severity."""
    data = {
        "region_id": draw(st.integers(min_value=1, max_value=10000)),
        "date": draw(st.datetimes(
            min_value=datetime(2020, 1, 1),
            max_value=datetime(2030, 12, 31)
        )),
        "severity": draw(st.one_of(
            st.integers(min_value=-100, max_value=0),
            st.integers(min_value=5, max_value=100)
        )),
    }
    
    return data


@st.composite
def valid_osm_data(draw):
    """Generate valid OSM data."""
    num_roads = draw(st.integers(min_value=0, max_value=5))
    num_facilities = draw(st.integers(min_value=0, max_value=5))
    
    roads = []
    for _ in range(num_roads):
        roads.append({
            "osm_id": draw(st.text(min_size=1, max_size=20)),
            "road_type": draw(st.sampled_from(["primary", "secondary", "tertiary"])),
            "length_km": draw(st.floats(min_value=0.1, max_value=100)),
        })
    
    facilities = []
    for _ in range(num_facilities):
        facilities.append({
            "osm_id": draw(st.text(min_size=1, max_size=20)),
            "name": draw(st.text(min_size=1, max_size=50)),
            "facility_type": draw(st.sampled_from(["hospital", "clinic", "school", "government"])),
            "latitude": draw(st.floats(min_value=-90, max_value=90)),
            "longitude": draw(st.floats(min_value=-180, max_value=180)),
        })
    
    return {
        "roads": roads,
        "facilities": facilities,
    }


@st.composite
def invalid_osm_data_missing_fields(draw):
    """Generate OSM data with missing required fields."""
    # Generate one facility with missing field
    facility = {
        "osm_id": draw(st.text(min_size=1, max_size=20)),
        "name": draw(st.text(min_size=1, max_size=50)),
        "facility_type": draw(st.sampled_from(["hospital", "clinic", "school", "government"])),
        "latitude": draw(st.floats(min_value=-90, max_value=90)),
        "longitude": draw(st.floats(min_value=-180, max_value=180)),
    }
    
    # Remove a required field
    required_fields = ["osm_id", "name", "facility_type", "latitude", "longitude"]
    field_to_remove = draw(st.sampled_from(required_fields))
    del facility[field_to_remove]
    
    return {
        "roads": [],
        "facilities": [facility],
    }


@st.composite
def invalid_osm_data_out_of_range(draw):
    """Generate OSM data with out-of-range coordinates."""
    # Generate one facility with invalid coordinates
    coord_to_invalidate = draw(st.sampled_from(["latitude", "longitude"]))
    
    facility = {
        "osm_id": draw(st.text(min_size=1, max_size=20)),
        "name": draw(st.text(min_size=1, max_size=50)),
        "facility_type": draw(st.sampled_from(["hospital", "clinic", "school", "government"])),
        "latitude": draw(st.floats(min_value=-90, max_value=90)),
        "longitude": draw(st.floats(min_value=-180, max_value=180)),
    }
    
    if coord_to_invalidate == "latitude":
        facility["latitude"] = draw(st.one_of(
            st.floats(min_value=-1000, max_value=-90.1),
            st.floats(min_value=90.1, max_value=1000)
        ))
    else:
        facility["longitude"] = draw(st.one_of(
            st.floats(min_value=-1000, max_value=-180.1),
            st.floats(min_value=180.1, max_value=1000)
        ))
    
    return {
        "roads": [],
        "facilities": [facility],
    }


# ============================================================================
# Property Tests
# ============================================================================

class TestDataValidatorProperties:
    """
    Property-based tests for Data Validator.
    
    Feature: uris-ai, Property 7: Data Validation Rejection of Invalid Data
    Validates: Requirements 7.4
    """

    # ========================================================================
    # Property 7.1: Valid Data Should Always Pass Validation
    # ========================================================================

    @given(data=valid_weather_data())
    @settings(max_examples=100)
    def test_property_valid_weather_data_passes(self, data):
        """
        Property: For any valid weather data, validation should pass.
        
        Invariant: ∀ data ∈ valid_schema: validate(data).valid = true
        """
        validator = DataValidator()
        result = validator.validate_weather(data)
        
        assert result.valid is True, (
            f"Valid weather data should pass validation. "
            f"Data: {data}, Errors: {result.errors}"
        )

    @given(data=valid_flood_event_data())
    @settings(max_examples=100)
    def test_property_valid_flood_event_passes(self, data):
        """
        Property: For any valid flood event data, validation should pass.
        
        Invariant: ∀ data ∈ valid_schema: validate(data).valid = true
        """
        validator = DataValidator()
        result = validator.validate_flood_event(data)
        
        assert result.valid is True, (
            f"Valid flood event data should pass validation. "
            f"Data: {data}, Errors: {result.errors}"
        )

    @given(data=valid_osm_data())
    @settings(max_examples=100, suppress_health_check=[HealthCheck.too_slow])
    def test_property_valid_osm_data_passes(self, data):
        """
        Property: For any valid OSM data, validation should pass.
        
        Invariant: ∀ data ∈ valid_schema: validate(data).valid = true
        """
        validator = DataValidator()
        result = validator.validate_osm_data(data)
        
        assert result.valid is True, (
            f"Valid OSM data should pass validation. "
            f"Data: {data}, Errors: {result.errors}"
        )

    # ========================================================================
    # Property 7.2: Invalid Data (Missing Fields) Should Always Fail
    # ========================================================================

    @given(data=invalid_weather_data_missing_fields())
    @settings(max_examples=100)
    def test_property_weather_missing_fields_fails(self, data):
        """
        Property: For any weather data with missing required fields,
        validation should fail.
        
        Invariant: ∀ data ∉ schema (missing fields): validate(data).valid = false
        """
        validator = DataValidator()
        result = validator.validate_weather(data)
        
        assert result.valid is False, (
            f"Weather data with missing fields should fail validation. "
            f"Data: {data}"
        )
        assert len(result.errors) > 0, (
            "Validation should return error messages for missing fields"
        )
        assert any("Missing required field" in error for error in result.errors), (
            f"Error should mention missing field. Errors: {result.errors}"
        )

    @given(data=invalid_flood_event_data_missing_fields())
    @settings(max_examples=100)
    def test_property_flood_event_missing_fields_fails(self, data):
        """
        Property: For any flood event data with missing required fields,
        validation should fail.
        
        Invariant: ∀ data ∉ schema (missing fields): validate(data).valid = false
        """
        validator = DataValidator()
        result = validator.validate_flood_event(data)
        
        assert result.valid is False, (
            f"Flood event data with missing fields should fail validation. "
            f"Data: {data}"
        )
        assert len(result.errors) > 0
        assert any("Missing required field" in error for error in result.errors)

    @given(data=invalid_osm_data_missing_fields())
    @settings(max_examples=100)
    def test_property_osm_missing_fields_fails(self, data):
        """
        Property: For any OSM data with missing required fields,
        validation should fail.
        
        Invariant: ∀ data ∉ schema (missing fields): validate(data).valid = false
        """
        validator = DataValidator()
        result = validator.validate_osm_data(data)
        
        assert result.valid is False, (
            f"OSM data with missing fields should fail validation. "
            f"Data: {data}"
        )
        assert len(result.errors) > 0
        assert any("missing" in error.lower() for error in result.errors)

    # ========================================================================
    # Property 7.3: Invalid Data (Out of Range) Should Always Fail
    # ========================================================================

    @given(data=invalid_weather_data_out_of_range())
    @settings(max_examples=100)
    def test_property_weather_out_of_range_fails(self, data):
        """
        Property: For any weather data with out-of-range values,
        validation should fail.
        
        Invariant: ∀ data ∉ schema (out of range): validate(data).valid = false
        """
        validator = DataValidator()
        result = validator.validate_weather(data)
        
        assert result.valid is False, (
            f"Weather data with out-of-range values should fail validation. "
            f"Data: {data}"
        )
        assert len(result.errors) > 0
        assert any("between" in error.lower() or "must be" in error.lower() 
                   for error in result.errors), (
            f"Error should mention range constraint. Errors: {result.errors}"
        )

    @given(data=invalid_flood_event_data_out_of_range())
    @settings(max_examples=100)
    def test_property_flood_event_out_of_range_fails(self, data):
        """
        Property: For any flood event data with out-of-range severity,
        validation should fail.
        
        Invariant: ∀ data ∉ schema (out of range): validate(data).valid = false
        """
        validator = DataValidator()
        result = validator.validate_flood_event(data)
        
        assert result.valid is False, (
            f"Flood event data with out-of-range severity should fail validation. "
            f"Data: {data}"
        )
        assert len(result.errors) > 0
        assert any("between" in error.lower() for error in result.errors)

    @given(data=invalid_osm_data_out_of_range())
    @settings(max_examples=100)
    def test_property_osm_out_of_range_fails(self, data):
        """
        Property: For any OSM data with out-of-range coordinates,
        validation should fail.
        
        Invariant: ∀ data ∉ schema (out of range): validate(data).valid = false
        """
        validator = DataValidator()
        result = validator.validate_osm_data(data)
        
        assert result.valid is False, (
            f"OSM data with out-of-range coordinates should fail validation. "
            f"Data: {data}"
        )
        assert len(result.errors) > 0
        assert any("invalid" in error.lower() for error in result.errors)

    # ========================================================================
    # Property 7.4: Invalid Data (Wrong Types) Should Always Fail
    # ========================================================================

    @given(data=invalid_weather_data_wrong_types())
    @settings(max_examples=100)
    def test_property_weather_wrong_types_fails(self, data):
        """
        Property: For any weather data with wrong data types,
        validation should fail.
        
        Invariant: ∀ data ∉ schema (wrong types): validate(data).valid = false
        """
        validator = DataValidator()
        result = validator.validate_weather(data)
        
        assert result.valid is False, (
            f"Weather data with wrong types should fail validation. "
            f"Data: {data}"
        )
        assert len(result.errors) > 0
        assert any("must be" in error.lower() for error in result.errors), (
            f"Error should mention type constraint. Errors: {result.errors}"
        )

    # ========================================================================
    # Property 7.5: Validation Result Should Always Include Error Details
    # ========================================================================

    @given(data=st.one_of(
        invalid_weather_data_missing_fields(),
        invalid_weather_data_out_of_range(),
        invalid_weather_data_wrong_types()
    ))
    @settings(max_examples=100)
    def test_property_invalid_data_has_error_details(self, data):
        """
        Property: For any invalid data, validation result should include
        detailed error messages.
        
        Invariant: ∀ data ∉ schema: len(validate(data).errors) > 0
        """
        validator = DataValidator()
        result = validator.validate_weather(data)
        
        assert result.valid is False
        assert len(result.errors) > 0, (
            "Invalid data should produce at least one error message"
        )
        assert all(isinstance(error, str) for error in result.errors), (
            "All errors should be strings"
        )
        assert all(len(error) > 0 for error in result.errors), (
            "All error messages should be non-empty"
        )

    # ========================================================================
    # Property 7.6: Validation Should Be Deterministic
    # ========================================================================

    @given(data=st.one_of(
        valid_weather_data(),
        invalid_weather_data_missing_fields(),
        invalid_weather_data_out_of_range()
    ))
    @settings(max_examples=100)
    def test_property_validation_is_deterministic(self, data):
        """
        Property: Validating the same data multiple times should always
        produce the same result.
        
        Invariant: ∀ data: validate(data) = validate(data)
        """
        validator = DataValidator()
        
        result1 = validator.validate_weather(data)
        result2 = validator.validate_weather(data)
        
        assert result1.valid == result2.valid, (
            "Validation should be deterministic"
        )
        assert result1.errors == result2.errors, (
            "Error messages should be consistent"
        )

    # ========================================================================
    # Property 7.7: Batch Validation Consistency
    # ========================================================================

    @given(data_list=st.lists(
        st.one_of(valid_weather_data(), invalid_weather_data_missing_fields()),
        min_size=1,
        max_size=10
    ))
    @settings(max_examples=50)
    def test_property_batch_validation_consistency(self, data_list):
        """
        Property: Batch validation should produce results consistent with
        individual validation.
        
        Invariant: batch_validate(data_list).valid_count = 
                   sum(validate(d).valid for d in data_list)
        """
        validator = DataValidator()
        
        # Individual validation
        individual_results = [
            validator.validate_weather(data) for data in data_list
        ]
        expected_valid = sum(1 for r in individual_results if r.valid)
        expected_invalid = sum(1 for r in individual_results if not r.valid)
        
        # Batch validation
        batch_result = validator.validate_batch(data_list, DataType.WEATHER)
        
        assert batch_result["total"] == len(data_list)
        assert batch_result["valid"] == expected_valid, (
            f"Batch validation should count {expected_valid} valid items, "
            f"but got {batch_result['valid']}"
        )
        assert batch_result["invalid"] == expected_invalid, (
            f"Batch validation should count {expected_invalid} invalid items, "
            f"but got {batch_result['invalid']}"
        )

    # ========================================================================
    # Property 7.8: Non-Empty Data Should Not Crash Validator
    # ========================================================================

    @given(data=st.dictionaries(
        keys=st.text(min_size=1, max_size=20),
        values=st.one_of(
            st.none(),
            st.booleans(),
            st.integers(),
            st.floats(allow_nan=False, allow_infinity=False),
            st.text(),
        ),
        min_size=1,
        max_size=10
    ))
    @settings(max_examples=100)
    def test_property_validator_does_not_crash(self, data):
        """
        Property: Validator should never crash, regardless of input.
        It should always return a ValidationResult.
        
        Invariant: ∀ data: validate(data) returns ValidationResult
        """
        validator = DataValidator()
        
        try:
            result = validator.validate_weather(data)
            
            # Should always return ValidationResult
            assert hasattr(result, 'valid')
            assert hasattr(result, 'errors')
            assert hasattr(result, 'warnings')
            assert isinstance(result.valid, bool)
            assert isinstance(result.errors, list)
            assert isinstance(result.warnings, list)
        except Exception as e:
            pytest.fail(
                f"Validator should not crash on any input. "
                f"Data: {data}, Exception: {e}"
            )
