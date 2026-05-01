# Property-Based Tests for URIS-AI

## Overview

This document describes the property-based testing (PBT) implementation for the URIS-AI system. Property-based tests validate universal correctness properties that should hold for all possible inputs, providing stronger guarantees than example-based unit tests.

## What is Property-Based Testing?

Property-based testing is a testing methodology where you define **properties** (universal rules) that should always be true for your code, and then automatically generate hundreds of test cases to verify those properties. Instead of writing specific examples, you describe the general behavior your code should exhibit.

### Example

**Unit Test (Example-Based):**

```python
def test_rainfall_validation():
    assert validate({"rainfall": 50}).valid == True
    assert validate({"rainfall": -10}).valid == False
```

**Property Test:**

```python
@given(rainfall=st.floats(min_value=0, max_value=500))
def test_valid_rainfall_always_passes(rainfall):
    # For ANY valid rainfall value, validation should pass
    assert validate({"rainfall": rainfall}).valid == True
```

The property test automatically generates 100+ different rainfall values and verifies the property holds for all of them.

## Property 7: Data Validation Rejection of Invalid Data

**Feature:** uris-ai  
**Validates:** Requirements 7.4  
**File:** `tests/test_data_validator_properties.py`

### Property Statement

_For any data that does not conform to the defined schema (missing required fields, invalid data types, out-of-range values), the validation function must reject the data and return validation errors._

**Formal Invariant:**

```
∀ data ∉ schema: validate(data, schema).valid = false
```

### Sub-Properties Tested

#### 7.1: Valid Data Should Always Pass Validation

**Invariant:** `∀ data ∈ valid_schema: validate(data).valid = true`

Tests that all data conforming to the schema is accepted:

- `test_property_valid_weather_data_passes` - 100 examples
- `test_property_valid_flood_event_passes` - 100 examples
- `test_property_valid_osm_data_passes` - 100 examples

#### 7.2: Invalid Data (Missing Fields) Should Always Fail

**Invariant:** `∀ data ∉ schema (missing fields): validate(data).valid = false`

Tests that data with missing required fields is rejected:

- `test_property_weather_missing_fields_fails` - 100 examples
- `test_property_flood_event_missing_fields_fails` - 100 examples
- `test_property_osm_missing_fields_fails` - 100 examples

#### 7.3: Invalid Data (Out of Range) Should Always Fail

**Invariant:** `∀ data ∉ schema (out of range): validate(data).valid = false`

Tests that data with out-of-range values is rejected:

- `test_property_weather_out_of_range_fails` - 100 examples
  - Rainfall: must be 0-500 mm
  - Humidity: must be 0-100%
  - Temperature: must be 15-40°C
  - Wind speed: must be 0-100 km/h
- `test_property_flood_event_out_of_range_fails` - 100 examples
  - Severity: must be 1-4
- `test_property_osm_out_of_range_fails` - 100 examples
  - Latitude: must be -90 to 90
  - Longitude: must be -180 to 180

#### 7.4: Invalid Data (Wrong Types) Should Always Fail

**Invariant:** `∀ data ∉ schema (wrong types): validate(data).valid = false`

Tests that data with incorrect data types is rejected:

- `test_property_weather_wrong_types_fails` - 100 examples
  - region_id must be integer
  - rainfall, humidity, temperature must be numbers

#### 7.5: Validation Result Should Always Include Error Details

**Invariant:** `∀ data ∉ schema: len(validate(data).errors) > 0`

Tests that invalid data always produces detailed error messages:

- `test_property_invalid_data_has_error_details` - 100 examples

#### 7.6: Validation Should Be Deterministic

**Invariant:** `∀ data: validate(data) = validate(data)`

Tests that validating the same data multiple times produces consistent results:

- `test_property_validation_is_deterministic` - 100 examples

#### 7.7: Batch Validation Consistency

**Invariant:** `batch_validate(data_list).valid_count = sum(validate(d).valid for d in data_list)`

Tests that batch validation is consistent with individual validation:

- `test_property_batch_validation_consistency` - 50 examples

#### 7.8: Validator Should Never Crash

**Invariant:** `∀ data: validate(data) returns ValidationResult`

Tests that the validator handles any input gracefully without crashing:

- `test_property_validator_does_not_crash` - 100 examples

## Test Data Generation Strategies

### Weather Data Strategies

**Valid Weather Data:**

- region_id: 1-10000
- date: 2020-01-01 to 2030-12-31
- rainfall: 0-500 mm
- humidity: 0-100%
- temperature: 15-40°C
- wind_speed: 0-100 km/h (optional)

**Invalid Weather Data:**

- Missing fields: Randomly removes one required field
- Out of range: Generates values outside valid ranges
- Wrong types: Replaces numeric fields with strings

### Flood Event Data Strategies

**Valid Flood Event Data:**

- region_id: 1-10000
- date: 2020-01-01 to 2030-12-31
- severity: 1-4
- water_level: 0-1000 cm (optional)
- duration_hours: 0-1000 hours (optional)
- affected_area_km2: 0-10000 km² (optional)

**Invalid Flood Event Data:**

- Missing fields: Randomly removes one required field
- Out of range: severity outside 1-4

### OSM Data Strategies

**Valid OSM Data:**

- roads: List of 0-5 roads with osm_id, road_type, length_km
- facilities: List of 0-5 facilities with osm_id, name, facility_type, latitude, longitude

**Invalid OSM Data:**

- Missing fields: Removes required fields from facilities
- Out of range: Coordinates outside valid ranges

## Running the Tests

### Run All Property Tests

```bash
pytest tests/test_data_validator_properties.py -v
```

### Run Specific Property Test

```bash
pytest tests/test_data_validator_properties.py::TestDataValidatorProperties::test_property_valid_weather_data_passes -v
```

### Run with More Examples

```bash
pytest tests/test_data_validator_properties.py --hypothesis-profile=more-examples
```

### Run with Specific Seed (for reproducibility)

```bash
pytest tests/test_data_validator_properties.py --hypothesis-seed=12345
```

## Test Configuration

Property tests are configured with:

- **max_examples=100**: Each property is tested with 100 randomly generated examples
- **suppress_health_check=[HealthCheck.too_slow]**: For OSM data generation (complex nested structures)

## Coverage

The property tests provide comprehensive coverage of:

- ✅ All three data types (weather, flood events, OSM data)
- ✅ All validation rules (required fields, data types, ranges)
- ✅ Edge cases (boundary values, missing fields, wrong types)
- ✅ Batch validation consistency
- ✅ Error message quality
- ✅ Deterministic behavior
- ✅ Robustness (no crashes on any input)

## Integration with CI/CD

Property tests are integrated into the CI/CD pipeline:

1. Run on every commit (pre-commit hook)
2. Run in CI pipeline before deployment
3. Must pass before merging to main branch

## Benefits of Property-Based Testing

1. **Broader Coverage**: Tests 100+ cases automatically vs. handful of manual examples
2. **Edge Case Discovery**: Finds corner cases developers might not think of
3. **Regression Prevention**: Catches bugs when code changes
4. **Documentation**: Properties serve as executable specifications
5. **Confidence**: Provides mathematical guarantees about code behavior

## Maintenance

When updating validation schemas:

1. Update the corresponding strategy in `test_data_validator_properties.py`
2. Run property tests to verify changes don't break invariants
3. Add new property tests for new validation rules

## References

- [Hypothesis Documentation](https://hypothesis.readthedocs.io/)
- [Property-Based Testing Guide](https://hypothesis.works/articles/what-is-property-based-testing/)
- URIS-AI Design Document: Section "Correctness Properties"
- URIS-AI Requirements: Section 7.4 "Data Validation"
