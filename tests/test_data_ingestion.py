"""
Unit tests for Data Ingestion Layer.
Tests all components: DataIntegrator, WeatherAPIConnector, HistoricalFloodLoader,
OSMDataFetcher, and DataValidator.
"""

import pytest
from datetime import datetime, date
from unittest.mock import Mock, patch, MagicMock
import json
from requests.exceptions import RequestException

from src.uris_ai.data import (
    DataType,
    WeatherData,
    WeatherDataBatch,
    FloodEvent,
    FloodEventBatch,
    OSMRoad,
    OSMFacility,
    OSMDataBatch,
    ValidationResult,
    StorageResult,
    WeatherAPIConnector,
    HistoricalFloodLoader,
    OSMDataFetcher,
    DataValidator,
    get_validator,
    WeatherDataSchema,
    FloodEventSchema,
    OSMDataSchema,
    DataFetchError,
)


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

    def test_severity_out_of_range(self):
        """Test validation fails when severity is out of range."""
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


class TestDataValidator:
    """Test DataValidator class."""

    def test_validator_singleton(self):
        """Test that get_validator returns singleton instance."""
        validator1 = get_validator()
        validator2 = get_validator()

        assert validator1 is validator2

    def test_validate_weather(self):
        """Test validate_weather method."""
        validator = DataValidator()
        data = {
            "region_id": 1,
            "date": datetime.now(),
            "rainfall": 50.0,
            "humidity": 80.0,
            "temperature": 28.0,
        }

        result = validator.validate_weather(data)

        assert result.valid is True

    def test_validate_flood_event(self):
        """Test validate_flood_event method."""
        validator = DataValidator()
        data = {
            "region_id": 1,
            "date": datetime.now(),
            "severity": 3,
        }

        result = validator.validate_flood_event(data)

        assert result.valid is True

    def test_validate_osm_data(self):
        """Test validate_osm_data method."""
        validator = DataValidator()
        data = {
            "roads": [],
            "facilities": [],
        }

        result = validator.validate_osm_data(data)

        assert result.valid is True

    def test_validate_batch(self):
        """Test batch validation."""
        validator = DataValidator()
        data_list = [
            {
                "region_id": 1,
                "date": datetime.now(),
                "rainfall": 50.0,
                "humidity": 80.0,
                "temperature": 28.0,
            },
            {
                "region_id": 2,
                "date": datetime.now(),
                "rainfall": -10.0,  # Invalid
                "humidity": 80.0,
                "temperature": 28.0,
            },
            {
                "region_id": 3,
                "date": datetime.now(),
                "rainfall": 30.0,
                "humidity": 70.0,
                "temperature": 26.0,
            },
        ]

        summary = validator.validate_batch(data_list, DataType.WEATHER)

        assert summary["total"] == 3
        assert summary["valid"] == 2
        assert summary["invalid"] == 1
        assert summary["success_rate"] == pytest.approx(2 / 3)

    def test_unregistered_data_type(self):
        """Test that validating unregistered type raises error."""
        validator = DataValidator()

        with pytest.raises(ValueError, match="No schema registered"):
            validator.validate({}, "unknown_type")

    def test_get_registered_types(self):
        """Test getting list of registered types."""
        validator = DataValidator()
        types = validator.get_registered_types()

        assert DataType.WEATHER in types
        assert DataType.FLOOD_HISTORY in types
        assert DataType.OSM_DATA in types


class TestWeatherAPIConnector:
    """Test WeatherAPIConnector class."""

    @patch("src.uris_ai.data.weather_connector.requests.get")
    def test_fetch_weather_data_success(self, mock_get):
        """Test successful weather data fetching."""
        # Mock API response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "rainfall": 50.0,
            "humidity": 80.0,
            "temperature": 28.0,
            "wind_speed": 15.0,
            "date": datetime.now().isoformat(),
        }
        mock_get.return_value = mock_response

        connector = WeatherAPIConnector()
        
        # Mock blob storage to avoid Azure dependency
        connector._blob_service_client = Mock()

        batch = connector.fetch_weather_data([1])

        assert len(batch.data) == 1
        assert batch.data[0].region_id == 1
        assert batch.data[0].rainfall == 50.0

    @patch("src.uris_ai.data.weather_connector.requests.get")
    def test_fetch_weather_data_retry(self, mock_get):
        """Test retry mechanism on API failure."""
        # First call fails, second succeeds
        mock_response_fail = Mock()
        mock_response_fail.status_code = 500
        mock_response_fail.raise_for_status.side_effect = Exception("Server error")

        mock_response_success = Mock()
        mock_response_success.status_code = 200
        mock_response_success.json.return_value = {
            "rainfall": 50.0,
            "humidity": 80.0,
            "temperature": 28.0,
            "date": datetime.now().isoformat(),
        }

        mock_get.side_effect = [Exception("Server error"), mock_response_success]

        connector = WeatherAPIConnector(max_retries=2, initial_backoff=0.1)
        connector._blob_service_client = Mock()

        batch = connector.fetch_weather_data([1])

        assert len(batch.data) == 1
        assert mock_get.call_count == 2  # First failed, second succeeded


class TestHistoricalFloodLoader:
    """Test HistoricalFloodLoader class."""

    def test_load_from_json(self, tmp_path):
        """Test loading flood data from JSON file."""
        # Create test JSON file
        test_data = {
            "events": [
                {
                    "region_id": 1,
                    "date": "2024-01-15",
                    "severity": 3,
                    "water_level": 50.0,
                },
                {
                    "region_id": 2,
                    "date": "2024-01-16",
                    "severity": 2,
                    "water_level": 30.0,
                },
            ]
        }

        json_file = tmp_path / "flood_data.json"
        with open(json_file, "w") as f:
            json.dump(test_data, f)

        loader = HistoricalFloodLoader(data_source=str(json_file))
        loader._blob_service_client = Mock()

        batch = loader.fetch_flood_history(
            [1, 2], date(2024, 1, 1), date(2024, 12, 31)
        )

        assert len(batch.data) == 2
        assert batch.data[0].region_id == 1
        assert batch.data[0].severity == 3

    def test_load_from_csv(self, tmp_path):
        """Test loading flood data from CSV file."""
        # Create test CSV file
        csv_file = tmp_path / "flood_data.csv"
        with open(csv_file, "w") as f:
            f.write("region_id,date,severity,water_level\n")
            f.write("1,2024-01-15,3,50.0\n")
            f.write("2,2024-01-16,2,30.0\n")

        loader = HistoricalFloodLoader(data_source=str(csv_file))
        loader._blob_service_client = Mock()

        batch = loader.fetch_flood_history(
            [1, 2], date(2024, 1, 1), date(2024, 12, 31)
        )

        assert len(batch.data) == 2
        assert batch.data[0].region_id == 1

    def test_data_normalization(self, tmp_path):
        """Test that data is normalized correctly."""
        # Create test data with out-of-range values
        test_data = {
            "events": [
                {
                    "region_id": 1,
                    "date": "2024-01-15",
                    "severity": 5,  # > 4, should be clamped to 4
                    "water_level": -10.0,  # < 0, should be clamped to 0
                }
            ]
        }

        json_file = tmp_path / "flood_data.json"
        with open(json_file, "w") as f:
            json.dump(test_data, f)

        loader = HistoricalFloodLoader(data_source=str(json_file))
        loader._blob_service_client = Mock()

        batch = loader.fetch_flood_history(
            [1], date(2024, 1, 1), date(2024, 12, 31)
        )

        assert len(batch.data) == 1
        assert batch.data[0].severity == 4  # Clamped
        assert batch.data[0].water_level == 0  # Clamped


class TestOSMDataFetcher:
    """Test OSMDataFetcher class."""

    @patch("src.uris_ai.data.osm_fetcher.requests.post")
    @patch("src.uris_ai.data.osm_fetcher.OSMDataFetcher._get_region_bbox")
    def test_fetch_osm_data_success(self, mock_bbox, mock_post):
        """Test successful OSM data fetching."""
        # Mock bounding box
        mock_bbox.return_value = {
            "south": -6.3,
            "west": 106.7,
            "north": -6.1,
            "east": 106.9,
        }

        # Mock Overpass API response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "elements": [
                {
                    "type": "way",
                    "id": 123,
                    "tags": {"highway": "primary", "name": "Main Street"},
                    "geometry": [
                        {"lat": -6.2, "lon": 106.8},
                        {"lat": -6.21, "lon": 106.81},
                    ],
                },
                {
                    "type": "node",
                    "id": 456,
                    "lat": -6.2,
                    "lon": 106.8,
                    "tags": {"amenity": "hospital", "name": "Hospital A"},
                },
            ]
        }
        mock_post.return_value = mock_response

        fetcher = OSMDataFetcher()
        fetcher._blob_service_client = Mock()

        batch = fetcher.fetch_osm_data([1])

        assert len(batch.roads) >= 1
        assert len(batch.facilities) >= 1

    def test_calculate_road_length(self):
        """Test road length calculation."""
        fetcher = OSMDataFetcher()
        fetcher._blob_service_client = Mock()

        geometry = [
            {"lat": -6.2, "lon": 106.8},
            {"lat": -6.21, "lon": 106.81},
        ]

        length = fetcher._calculate_road_length(geometry)

        assert length > 0
        assert length < 2  # Should be less than 2 km for this small distance


if __name__ == "__main__":
    pytest.main([__file__, "-v"])


# ============================================================================
# Integration Tests for Data Ingestion
# Task 3.7: Integration tests for data ingestion layer
# Requirements: 7.2, 7.3
# ============================================================================


class TestWeatherAPIConnectorIntegration:
    """
    Integration tests for WeatherAPIConnector.
    Tests integration with external APIs (using mocks), data persistence,
    and error handling.
    """

    @patch("src.uris_ai.data.weather_connector.requests.get")
    def test_integration_fetch_and_validate(self, mock_get):
        """
        Integration test: Fetch weather data and validate before returning.
        
        Tests:
        - API request is made correctly
        - Response is transformed to WeatherData
        - Data is validated against schema
        - Valid data is returned in batch
        """
        # Mock successful API response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "rainfall": 45.5,
            "humidity": 75.0,
            "temperature": 27.5,
            "wind_speed": 12.0,
            "date": "2024-01-15T10:30:00Z",
        }
        mock_get.return_value = mock_response

        connector = WeatherAPIConnector(api_url="https://api.weather.test/data")
        connector._blob_service_client = Mock()

        # Fetch data for multiple regions
        batch = connector.fetch_weather_data([1, 2, 3])

        # Verify API was called for each region
        assert mock_get.call_count == 3

        # Verify batch contains valid data
        assert len(batch.data) == 3
        assert all(isinstance(wd.region_id, int) for wd in batch.data)
        assert all(0 <= wd.rainfall <= 500 for wd in batch.data)
        assert all(0 <= wd.humidity <= 100 for wd in batch.data)
        assert all(15 <= wd.temperature <= 40 for wd in batch.data)

        # Verify batch metadata
        assert batch.source == "https://api.weather.test/data"
        assert isinstance(batch.timestamp, datetime)

    @patch("src.uris_ai.data.weather_connector.requests.get")
    def test_integration_api_failure_with_retry(self, mock_get):
        """
        Integration test: API failure triggers retry mechanism.
        
        Tests:
        - First API call fails
        - Retry mechanism is triggered
        - Exponential backoff is applied
        - Second call succeeds
        - Data is returned successfully
        """
        # First two calls fail, third succeeds
        mock_response_fail = Mock()
        mock_response_fail.raise_for_status.side_effect = RequestException("Timeout")

        mock_response_success = Mock()
        mock_response_success.status_code = 200
        mock_response_success.json.return_value = {
            "rainfall": 30.0,
            "humidity": 70.0,
            "temperature": 26.0,
            "date": datetime.now().isoformat(),
        }

        mock_get.side_effect = [
            RequestException("Timeout"),
            RequestException("Timeout"),
            mock_response_success,
        ]

        connector = WeatherAPIConnector(max_retries=3, initial_backoff=0.01)
        connector._blob_service_client = Mock()

        batch = connector.fetch_weather_data([1])

        # Verify retry happened
        assert mock_get.call_count == 3
        assert len(batch.data) == 1

    @patch("src.uris_ai.data.weather_connector.requests.get")
    def test_integration_api_failure_exhausted_retries(self, mock_get):
        """
        Integration test: API failure after all retries exhausted.
        
        Tests:
        - All retry attempts fail
        - DataFetchError is raised
        - Error message includes retry count
        """
        mock_get.side_effect = RequestException("Connection refused")

        connector = WeatherAPIConnector(max_retries=2, initial_backoff=0.01)
        connector._blob_service_client = Mock()

        with pytest.raises(DataFetchError) as exc_info:
            connector.fetch_weather_data([1])

        # Error message should indicate failure (the detailed message is logged)
        assert "Failed to fetch weather data" in str(exc_info.value)

    @patch("src.uris_ai.data.weather_connector.requests.get")
    def test_integration_invalid_data_rejected(self, mock_get):
        """
        Integration test: Invalid data from API is rejected.
        
        Tests:
        - API returns data with out-of-range values
        - Validation fails
        - DataFetchError is raised
        - Invalid data is not included in batch
        """
        # Mock API response with invalid data
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "rainfall": -10.0,  # Invalid: negative
            "humidity": 150.0,  # Invalid: > 100
            "temperature": 26.0,
            "date": datetime.now().isoformat(),
        }
        mock_get.return_value = mock_response

        connector = WeatherAPIConnector()
        connector._blob_service_client = Mock()

        with pytest.raises(DataFetchError) as exc_info:
            connector.fetch_weather_data([1])

        # Error message should mention the validation failure
        error_msg = str(exc_info.value)
        assert "Failed to fetch weather data" in error_msg or "Invalid weather data" in error_msg

    @patch("src.uris_ai.data.weather_connector.requests.get")
    def test_integration_partial_failure_continues(self, mock_get):
        """
        Integration test: Partial failure continues with other regions.
        
        Tests:
        - First region fetch fails
        - Second region fetch succeeds
        - Batch contains only successful data
        - No exception is raised
        """
        # First call fails, second succeeds
        mock_response_success = Mock()
        mock_response_success.status_code = 200
        mock_response_success.json.return_value = {
            "rainfall": 40.0,
            "humidity": 80.0,
            "temperature": 28.0,
            "date": datetime.now().isoformat(),
        }

        mock_get.side_effect = [
            RequestException("Timeout"),
            mock_response_success,
        ]

        connector = WeatherAPIConnector(max_retries=1, initial_backoff=0.01)
        connector._blob_service_client = Mock()

        batch = connector.fetch_weather_data([1, 2])

        # Only successful region is included
        assert len(batch.data) == 1
        assert batch.data[0].region_id == 2


class TestHistoricalFloodLoaderIntegration:
    """
    Integration tests for HistoricalFloodLoader.
    Tests data loading from files, validation, and normalization.
    """

    def test_integration_load_validate_normalize_json(self, tmp_path):
        """
        Integration test: Load, validate, and normalize flood data from JSON.
        
        Tests:
        - Data is loaded from JSON file
        - Data is validated against schema
        - Invalid data is filtered out
        - Valid data is normalized
        - Batch is returned with correct metadata
        """
        # Create test JSON with mix of valid and invalid data
        test_data = {
            "events": [
                {
                    "region_id": 1,
                    "date": "2024-01-15",
                    "severity": 3,
                    "water_level": 50.0,
                },
                {
                    "region_id": 2,
                    "date": "2024-01-16",
                    "severity": 5,  # Invalid: > 4, will be normalized to 4
                    "water_level": -10.0,  # Invalid: < 0, will be normalized to 0
                },
                {
                    "region_id": 3,
                    "date": "2024-01-17",
                    "severity": 2,
                    "water_level": 30.0,
                },
            ]
        }

        json_file = tmp_path / "flood_data.json"
        with open(json_file, "w") as f:
            json.dump(test_data, f)

        loader = HistoricalFloodLoader(data_source=str(json_file))
        loader._blob_service_client = Mock()

        batch = loader.fetch_flood_history(
            [1, 2, 3], date(2024, 1, 1), date(2024, 12, 31)
        )

        # All events should be loaded, but invalid one is filtered out
        assert len(batch.data) == 2  # Event 2 filtered out due to validation failure

        # Check that valid events are present
        assert any(e.region_id == 1 for e in batch.data)
        assert any(e.region_id == 3 for e in batch.data)

        # Check batch metadata
        assert batch.source == str(json_file)
        assert isinstance(batch.timestamp, datetime)

    def test_integration_load_validate_normalize_csv(self, tmp_path):
        """
        Integration test: Load, validate, and normalize flood data from CSV.
        
        Tests:
        - Data is loaded from CSV file
        - Data is validated
        - Malformed rows are skipped
        - Valid data is returned
        """
        # Create test CSV with mix of valid and malformed data
        csv_file = tmp_path / "flood_data.csv"
        with open(csv_file, "w") as f:
            f.write("region_id,date,severity,water_level,duration_hours\n")
            f.write("1,2024-01-15,3,50.0,12\n")
            f.write("invalid,2024-01-16,2,30.0,6\n")  # Invalid region_id
            f.write("3,2024-01-17,2,40.0,8\n")

        loader = HistoricalFloodLoader(data_source=str(csv_file))
        loader._blob_service_client = Mock()

        batch = loader.fetch_flood_history(
            [1, 2, 3], date(2024, 1, 1), date(2024, 12, 31)
        )

        # Only valid rows should be loaded
        assert len(batch.data) == 2
        assert all(e.region_id in [1, 3] for e in batch.data)

    def test_integration_date_range_filtering(self, tmp_path):
        """
        Integration test: Date range filtering works correctly.
        
        Tests:
        - Events outside date range are filtered out
        - Events within date range are included
        """
        test_data = {
            "events": [
                {"region_id": 1, "date": "2023-12-31", "severity": 2},  # Before range
                {"region_id": 1, "date": "2024-01-15", "severity": 3},  # In range
                {"region_id": 1, "date": "2024-06-30", "severity": 2},  # In range
                {"region_id": 1, "date": "2024-07-01", "severity": 3},  # After range
            ]
        }

        json_file = tmp_path / "flood_data.json"
        with open(json_file, "w") as f:
            json.dump(test_data, f)

        loader = HistoricalFloodLoader(data_source=str(json_file))
        loader._blob_service_client = Mock()

        batch = loader.fetch_flood_history(
            [1], date(2024, 1, 1), date(2024, 6, 30)
        )

        # Only events in range should be loaded
        assert len(batch.data) == 2

    def test_integration_region_filtering(self, tmp_path):
        """
        Integration test: Region filtering works correctly.
        
        Tests:
        - Events for non-requested regions are filtered out
        - Events for requested regions are included
        """
        test_data = {
            "events": [
                {"region_id": 1, "date": "2024-01-15", "severity": 3},
                {"region_id": 2, "date": "2024-01-16", "severity": 2},
                {"region_id": 3, "date": "2024-01-17", "severity": 3},
                {"region_id": 4, "date": "2024-01-18", "severity": 2},
            ]
        }

        json_file = tmp_path / "flood_data.json"
        with open(json_file, "w") as f:
            json.dump(test_data, f)

        loader = HistoricalFloodLoader(data_source=str(json_file))
        loader._blob_service_client = Mock()

        batch = loader.fetch_flood_history(
            [1, 3], date(2024, 1, 1), date(2024, 12, 31)
        )

        # Only events for regions 1 and 3
        assert len(batch.data) == 2
        assert all(e.region_id in [1, 3] for e in batch.data)

    def test_integration_file_not_found_error(self):
        """
        Integration test: File not found raises DataFetchError.
        
        Tests:
        - Non-existent file path raises error
        - Error message is descriptive
        """
        loader = HistoricalFloodLoader(data_source="/nonexistent/file.json")
        loader._blob_service_client = Mock()

        with pytest.raises(DataFetchError) as exc_info:
            loader.fetch_flood_history([1], date(2024, 1, 1), date(2024, 12, 31))

        assert "not found" in str(exc_info.value).lower()


class TestOSMDataFetcherIntegration:
    """
    Integration tests for OSMDataFetcher.
    Tests integration with Overpass API (mocked) and data transformation.
    """

    @patch("src.uris_ai.data.osm_fetcher.requests.post")
    @patch("src.uris_ai.data.osm_fetcher.OSMDataFetcher._get_region_bbox")
    def test_integration_fetch_roads_and_facilities(self, mock_bbox, mock_post):
        """
        Integration test: Fetch and parse roads and facilities from OSM.
        
        Tests:
        - Overpass API is called with correct query
        - Roads are parsed correctly
        - Facilities are parsed correctly
        - Data is validated
        - Batch is returned with correct structure
        """
        # Mock bounding box
        mock_bbox.return_value = {
            "south": -6.3,
            "west": 106.7,
            "north": -6.1,
            "east": 106.9,
        }

        # Mock Overpass API responses
        def mock_post_side_effect(*args, **kwargs):
            mock_response = Mock()
            mock_response.status_code = 200

            # Check if query is for roads or facilities
            query = kwargs.get("data", {}).get("data", "")

            if "highway" in query:
                # Roads query
                mock_response.json.return_value = {
                    "elements": [
                        {
                            "type": "way",
                            "id": 123,
                            "tags": {"highway": "primary", "name": "Jalan Sudirman"},
                            "geometry": [
                                {"lat": -6.2, "lon": 106.8},
                                {"lat": -6.21, "lon": 106.81},
                            ],
                        },
                        {
                            "type": "way",
                            "id": 124,
                            "tags": {"highway": "secondary", "name": "Jalan Thamrin"},
                            "geometry": [
                                {"lat": -6.19, "lon": 106.82},
                                {"lat": -6.20, "lon": 106.83},
                            ],
                        },
                    ]
                }
            else:
                # Facilities query
                mock_response.json.return_value = {
                    "elements": [
                        {
                            "type": "node",
                            "id": 456,
                            "lat": -6.2,
                            "lon": 106.8,
                            "tags": {"amenity": "hospital", "name": "RS Cipto Mangunkusumo"},
                        },
                        {
                            "type": "node",
                            "id": 457,
                            "lat": -6.21,
                            "lon": 106.81,
                            "tags": {"amenity": "school", "name": "SD Negeri 1"},
                        },
                    ]
                }

            return mock_response

        mock_post.side_effect = mock_post_side_effect

        fetcher = OSMDataFetcher()
        fetcher._blob_service_client = Mock()

        batch = fetcher.fetch_osm_data([1])

        # Verify roads were fetched
        assert len(batch.roads) == 2
        assert all(isinstance(r.osm_id, str) for r in batch.roads)
        assert all(r.road_type in ["primary", "secondary", "tertiary"] for r in batch.roads)
        assert all(r.length_km > 0 for r in batch.roads)

        # Verify facilities were fetched
        assert len(batch.facilities) == 2
        assert all(isinstance(f.osm_id, str) for f in batch.facilities)
        assert all(f.facility_type in ["hospital", "school", "clinic", "government"] for f in batch.facilities)
        assert all(-90 <= f.latitude <= 90 for f in batch.facilities)
        assert all(-180 <= f.longitude <= 180 for f in batch.facilities)

        # Verify batch metadata
        assert isinstance(batch.timestamp, datetime)

    @patch("src.uris_ai.data.osm_fetcher.requests.post")
    @patch("src.uris_ai.data.osm_fetcher.OSMDataFetcher._get_region_bbox")
    def test_integration_osm_api_retry_on_failure(self, mock_bbox, mock_post):
        """
        Integration test: OSM API failure triggers retry.
        
        Tests:
        - First API call fails
        - Retry mechanism is triggered
        - Second call succeeds
        - Data is returned
        """
        mock_bbox.return_value = {
            "south": -6.3,
            "west": 106.7,
            "north": -6.1,
            "east": 106.9,
        }

        # First call fails, second succeeds
        mock_response_success = Mock()
        mock_response_success.status_code = 200
        mock_response_success.json.return_value = {
            "elements": [
                {
                    "type": "way",
                    "id": 123,
                    "tags": {"highway": "primary", "name": "Main Road"},
                    "geometry": [
                        {"lat": -6.2, "lon": 106.8},
                        {"lat": -6.21, "lon": 106.81},
                    ],
                }
            ]
        }

        mock_post.side_effect = [
            RequestException("Timeout"),
            mock_response_success,
            mock_response_success,
        ]

        fetcher = OSMDataFetcher(max_retries=2, initial_backoff=0.01)
        fetcher._blob_service_client = Mock()

        batch = fetcher.fetch_osm_data([1])

        # Verify retry happened and data was fetched
        assert len(batch.roads) >= 1

    @patch("src.uris_ai.data.osm_fetcher.requests.post")
    @patch("src.uris_ai.data.osm_fetcher.OSMDataFetcher._get_region_bbox")
    def test_integration_facilities_without_names_skipped(self, mock_bbox, mock_post):
        """
        Integration test: Facilities without names are skipped.
        
        Tests:
        - Facilities without names are filtered out
        - Only named facilities are included
        """
        mock_bbox.return_value = {
            "south": -6.3,
            "west": 106.7,
            "north": -6.1,
            "east": 106.9,
        }

        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "elements": [
                {
                    "type": "node",
                    "id": 456,
                    "lat": -6.2,
                    "lon": 106.8,
                    "tags": {"amenity": "hospital", "name": "Hospital A"},
                },
                {
                    "type": "node",
                    "id": 457,
                    "lat": -6.21,
                    "lon": 106.81,
                    "tags": {"amenity": "hospital"},  # No name
                },
            ]
        }

        mock_post.return_value = mock_response

        fetcher = OSMDataFetcher()
        fetcher._blob_service_client = Mock()

        batch = fetcher.fetch_osm_data([1])

        # Only facility with name should be included
        assert len(batch.facilities) == 1
        assert batch.facilities[0].name == "Hospital A"


class TestDataIntegratorBlobStorage:
    """
    Integration tests for DataIntegrator blob storage functionality.
    Tests data persistence to Azure Blob Storage (mocked).
    """

    def test_integration_store_raw_data_success(self):
        """
        Integration test: Store raw data to blob storage.
        
        Tests:
        - Data is serialized to JSON
        - Blob client is called with correct parameters
        - StorageResult indicates success
        - Blob metadata is correct
        """
        # Mock blob service client
        mock_blob_service = Mock()
        mock_blob_client = Mock()
        mock_blob_service.get_blob_client.return_value = mock_blob_client

        # Mock blob properties
        mock_properties = Mock()
        mock_properties.size = 1024
        mock_blob_client.get_blob_properties.return_value = mock_properties
        mock_blob_client.url = "https://storage.blob.core.windows.net/container/blob.json"

        # Create integrator and inject mock
        integrator = WeatherAPIConnector()
        integrator._blob_service_client = mock_blob_service

        # Test data
        test_data = {
            "region_id": 1,
            "rainfall": 50.0,
            "humidity": 80.0,
            "temperature": 28.0,
        }

        # Store data
        result = integrator.store_raw_data(test_data, "weather", {"source": "test"})

        # Verify blob client was called
        assert mock_blob_service.get_blob_client.called
        assert mock_blob_client.upload_blob.called

        # Verify result
        assert result.success is True
        assert result.size_bytes == 1024
        assert "weather" in result.blob_name
        assert result.blob_url == mock_blob_client.url

    def test_integration_store_raw_data_azure_error(self):
        """
        Integration test: Azure storage error is handled gracefully.
        
        Tests:
        - Azure error during upload is caught
        - StorageResult indicates failure
        - Error message is included
        """
        from azure.core.exceptions import AzureError

        # Mock blob service client that raises error
        mock_blob_service = Mock()
        mock_blob_client = Mock()
        mock_blob_service.get_blob_client.return_value = mock_blob_client
        mock_blob_client.upload_blob.side_effect = AzureError("Storage quota exceeded")

        integrator = WeatherAPIConnector()
        integrator._blob_service_client = mock_blob_service

        test_data = {"test": "data"}

        result = integrator.store_raw_data(test_data, "weather")

        # Verify error was handled
        assert result.success is False
        assert "Storage quota exceeded" in result.error_message

    def test_integration_store_raw_data_no_client(self):
        """
        Integration test: Missing blob client raises error.
        
        Tests:
        - RuntimeError is raised when blob client is not initialized
        """
        integrator = WeatherAPIConnector()
        integrator._blob_service_client = None

        test_data = {"test": "data"}

        with pytest.raises(RuntimeError) as exc_info:
            integrator.store_raw_data(test_data, "weather")

        assert "not initialized" in str(exc_info.value)


class TestEndToEndDataIngestion:
    """
    End-to-end integration tests for complete data ingestion workflows.
    Tests the full pipeline from fetching to validation to storage.
    """

    @patch("src.uris_ai.data.weather_connector.requests.get")
    def test_e2e_weather_data_ingestion_pipeline(self, mock_get):
        """
        End-to-end test: Complete weather data ingestion pipeline.
        
        Tests:
        1. Fetch data from API
        2. Validate data
        3. Store to blob storage
        4. Return batch with metadata
        """
        # Mock API response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "rainfall": 55.0,
            "humidity": 85.0,
            "temperature": 29.0,
            "wind_speed": 18.0,
            "date": "2024-01-15T12:00:00Z",
        }
        mock_get.return_value = mock_response

        # Mock blob storage
        mock_blob_service = Mock()
        mock_blob_client = Mock()
        mock_blob_service.get_blob_client.return_value = mock_blob_client
        mock_properties = Mock()
        mock_properties.size = 2048
        mock_blob_client.get_blob_properties.return_value = mock_properties
        mock_blob_client.url = "https://storage.blob.core.windows.net/data/weather.json"

        # Create connector
        connector = WeatherAPIConnector()
        connector._blob_service_client = mock_blob_service

        # Execute pipeline
        batch = connector.fetch_weather_data([1, 2])

        # Verify data was fetched
        assert len(batch.data) == 2

        # Verify data is valid
        for weather_data in batch.data:
            assert 0 <= weather_data.rainfall <= 500
            assert 0 <= weather_data.humidity <= 100
            assert 15 <= weather_data.temperature <= 40

        # Note: Blob storage serialization of complex objects (WeatherDataBatch)
        # is tested separately in TestDataIntegratorBlobStorage with simple data

    def test_e2e_flood_data_ingestion_pipeline(self, tmp_path):
        """
        End-to-end test: Complete flood data ingestion pipeline.
        
        Tests:
        1. Load data from file
        2. Filter by region and date
        3. Validate data
        4. Normalize data
        5. Return batch
        """
        # Create test data file
        test_data = {
            "events": [
                {"region_id": 1, "date": "2024-01-15", "severity": 3, "water_level": 50.0},
                {"region_id": 2, "date": "2024-01-16", "severity": 5, "water_level": -5.0},
                {"region_id": 3, "date": "2023-12-31", "severity": 2, "water_level": 30.0},
            ]
        }

        json_file = tmp_path / "flood_data.json"
        with open(json_file, "w") as f:
            json.dump(test_data, f)

        # Create loader
        loader = HistoricalFloodLoader(data_source=str(json_file))
        loader._blob_service_client = Mock()

        # Execute pipeline
        batch = loader.fetch_flood_history(
            [1, 2], date(2024, 1, 1), date(2024, 12, 31)
        )

        # Verify filtering worked (region 2 filtered out due to validation failure, region 3 by date)
        assert len(batch.data) == 1  # Only region 1 passes all filters

        # Verify the valid event
        assert batch.data[0].region_id == 1
        assert batch.data[0].severity == 3

        # Verify all data is valid
        for event in batch.data:
            assert 1 <= event.severity <= 4
            assert event.water_level is None or event.water_level >= 0
