"""
Unit tests for Data Schemas (validation logic only).
These tests don't require Azure configuration.
"""

import pytest
from datetime import datetime

# Import directly from schema module to avoid config loading
import sys
sys.path.insert(0, 'src')

from uris_ai.data.schemas import WeatherDataSchema, FloodEventSchema, OSMDataSchema
from uris_ai.data.models import WeatherData, FloodEvent


class TestWeatherDataSchema:
    """Test WeatherDataSchema validation."""

    def test_valid_weather_data(self):
        """Test validation of valid weather data."""
        schema = WeatherDataSchema()
        data = {
            "region_id": 1,
            "date": datetime.now(),
            "rainfall": 50.0,
            "humidity": 80.0,
            "temperature": 28.0,
            "wind_speed": 15.0,
        }

        result = schema.validate(data)

        assert result.valid is True
        assert len(result.errors) == 0

    def test_missing_required_field(self):
        """Test validation fails when required field is missing."""
        schema = WeatherDataSchema()
        data = {
            "region_id": 1,
            "date": datetime.now(),
            "rainfall": 50.0,
            # Missing humidity and temperature
        }

        result = schema.validate(data)

        assert result.valid is False
        assert any("humidity" in error for error in result.errors)
        assert any("temperature" in error for error in result.errors)

    def test_rainfall_out_of_range(self):
        """Test validation fails when rainfall is out of range."""
        schema = WeatherDataSchema()
        data = {
            "region_id": 1,
            "date": datetime.now(),
            "rainfall": 600.0,  # > 500
            "humidity": 80.0,
            "temperature": 28.0,
        }

        result = schema.validate(data)

        assert result.valid is False
        assert any("rainfall" in error for error in result.errors)

    def test_negative_rainfall(self):
        """Test validation fails for negative rainfall."""
        schema = WeatherDataSchema()
        data = {
            "region_id": 1,
            "date": datetime.now(),
            "rainfall": -10.0,
            "humidity": 80.0,
            "temperature": 28.0,
        }

        result = schema.validate(data)

        assert result.valid is False
        assert any("rainfall" in error for error in result.errors)

    def test_humidity_out_of_range(self):
        """Test validation fails when humidity is out of range."""
        schema = WeatherDataSchema()
        data = {
            "region_id": 1,
            "date": datetime.now(),
            "rainfall": 50.0,
            "humidity": 150.0,  # > 100
            "temperature": 28.0,
        }

        result = schema.validate(data)

        assert result.valid is False
        assert any("humidity" in error for error in result.errors)

    def test_temperature_out_of_range(self):
        """Test validation fails when temperature is out of range."""
        schema = WeatherDataSchema()
        data = {
            "region_id": 1,
            "date": datetime.now(),
            "rainfall": 50.0,
            "humidity": 80.0,
            "temperature": 50.0,  # > 40
        }

        result = schema.validate(data)

        assert result.valid is False
        assert any("temperature" in error for error in result.errors)

    def test_optional_wind_speed(self):
        """Test that wind_speed is optional."""
        schema = WeatherDataSchema()
        data = {
            "region_id": 1,
            "date": datetime.now(),
            "rainfall": 50.0,
            "humidity": 80.0,
            "temperature": 28.0,
            # wind_speed is optional
        }

        result = schema.validate(data)

        assert result.valid is True

    def test_validate_weather_data_object(self):
        """Test validation of WeatherData object."""
        schema = WeatherDataSchema()
        weather = WeatherData(
            region_id=1,
            date=datetime.now(),
            rainfall=50.0,
            humidity=80.0,
            temperature=28.0,
            wind_speed=15.0,
        )

        result = schema.validate(weather)

        assert result.valid is True


class TestFloodEventSchema:
    """Test FloodEventSchema validation."""

    def test_valid_flood_event(self):
        """Test validation of valid flood event."""
        schema = FloodEventSchema()
        data = {
            "region_id": 1,
            "date": datetime.now(),
            "severity": 3,
            "water_level": 50.0,
            "duration_hours": 6,
            "affected_area_km2": 2.5,
        }

        result = schema.validate(data)

        assert result.valid is True
        assert len(result.errors) == 0

    def test_missing_required_field(self):
        """Test validation fails when required field is missing."""
        schema = FloodEventSchema()
        data = {
            "region_id": 1,
            "date": datetime.now(),
            # Missing severity
        }

        result = schema.validate(data)

        assert result.valid is False
        assert any("severity" in error for error in result.errors)

    def test_severity_out_of_range_low(self):
        """Test validation fails when severity is too low."""
        schema = FloodEventSchema()
        data = {
            "region_id": 1,
            "date": datetime.now(),
            "severity": 0,  # < 1
        }

        result = schema.validate(data)

        assert result.valid is False
        assert any("severity" in error for error in result.errors)

    def test_severity_out_of_range_high(self):
        """Test validation fails when severity is too high."""
        schema = FloodEventSchema()
        data = {
            "region_id": 1,
            "date": datetime.now(),
            "severity": 5,  # > 4
        }

        result = schema.validate(data)

        assert result.valid is False
        assert any("severity" in error for error in result.errors)

    def test_negative_water_level(self):
        """Test validation fails for negative water level."""
        schema = FloodEventSchema()
        data = {
            "region_id": 1,
            "date": datetime.now(),
            "severity": 2,
            "water_level": -10.0,
        }

        result = schema.validate(data)

        assert result.valid is False
        assert any("water_level" in error for error in result.errors)

    def test_optional_fields(self):
        """Test that optional fields are truly optional."""
        schema = FloodEventSchema()
        data = {
            "region_id": 1,
            "date": datetime.now(),
            "severity": 2,
            # All other fields are optional
        }

        result = schema.validate(data)

        assert result.valid is True

    def test_validate_flood_event_object(self):
        """Test validation of FloodEvent object."""
        schema = FloodEventSchema()
        event = FloodEvent(
            region_id=1,
            date=datetime.now(),
            severity=3,
            water_level=50.0,
            duration_hours=6,
            affected_area_km2=2.5,
        )

        result = schema.validate(event)

        assert result.valid is True


class TestOSMDataSchema:
    """Test OSMDataSchema validation."""

    def test_valid_osm_data(self):
        """Test validation of valid OSM data."""
        schema = OSMDataSchema()
        data = {
            "roads": [
                {
                    "osm_id": "123",
                    "road_type": "primary",
                    "length_km": 5.0,
                }
            ],
            "facilities": [
                {
                    "osm_id": "456",
                    "name": "Hospital A",
                    "facility_type": "hospital",
                    "latitude": -6.2,
                    "longitude": 106.8,
                }
            ],
        }

        result = schema.validate(data)

        assert result.valid is True
        assert len(result.errors) == 0

    def test_empty_osm_data(self):
        """Test validation of empty OSM data."""
        schema = OSMDataSchema()
        data = {
            "roads": [],
            "facilities": [],
        }

        result = schema.validate(data)

        assert result.valid is True

    def test_missing_road_fields(self):
        """Test validation fails when road fields are missing."""
        schema = OSMDataSchema()
        data = {
            "roads": [
                {
                    "osm_id": "123",
                    # Missing road_type and length_km
                }
            ],
        }

        result = schema.validate(data)

        assert result.valid is False
        assert any("road_type" in error for error in result.errors)
        assert any("length_km" in error for error in result.errors)

    def test_invalid_facility_coordinates(self):
        """Test validation fails for invalid coordinates."""
        schema = OSMDataSchema()
        data = {
            "facilities": [
                {
                    "osm_id": "456",
                    "name": "Hospital A",
                    "facility_type": "hospital",
                    "latitude": 100.0,  # > 90
                    "longitude": 200.0,  # > 180
                }
            ],
        }

        result = schema.validate(data)

        assert result.valid is False
        assert any("latitude" in error for error in result.errors)
        assert any("longitude" in error for error in result.errors)

    def test_missing_facility_fields(self):
        """Test validation fails when facility fields are missing."""
        schema = OSMDataSchema()
        data = {
            "facilities": [
                {
                    "osm_id": "456",
                    # Missing name, facility_type, latitude, longitude
                }
            ],
        }

        result = schema.validate(data)

        assert result.valid is False
        assert any("name" in error for error in result.errors)
        assert any("facility_type" in error for error in result.errors)
        assert any("latitude" in error for error in result.errors)
        assert any("longitude" in error for error in result.errors)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
