"""
Schema definitions for data validation.
Defines validation rules for weather, flood, and OSM data.
"""

from abc import ABC, abstractmethod
from typing import Any, List, Dict
from datetime import datetime

from .models import ValidationResult, WeatherData, FloodEvent


class Schema(ABC):
    """Abstract base class for data schemas."""

    @abstractmethod
    def validate(self, data: Any) -> ValidationResult:
        """
        Validate data against this schema.
        
        Args:
            data: Data to validate
            
        Returns:
            ValidationResult with validation status and errors
        """
        pass


class WeatherDataSchema(Schema):
    """Schema for validating weather data."""

    def validate(self, data: Any) -> ValidationResult:
        """Validate weather data."""
        errors: List[str] = []
        warnings: List[str] = []

        # Check if data is WeatherData instance or dict
        if isinstance(data, WeatherData):
            data_dict = {
                "region_id": data.region_id,
                "date": data.date,
                "rainfall": data.rainfall,
                "humidity": data.humidity,
                "temperature": data.temperature,
                "wind_speed": data.wind_speed,
            }
        elif isinstance(data, dict):
            data_dict = data
        else:
            return ValidationResult(
                valid=False,
                errors=["Data must be WeatherData instance or dict"],
                warnings=[],
                data_type="weather",
            )

        # Validate required fields
        required_fields = ["region_id", "date", "rainfall", "humidity", "temperature"]
        for field in required_fields:
            if field not in data_dict or data_dict[field] is None:
                errors.append(f"Missing required field: {field}")

        if errors:
            return ValidationResult(
                valid=False, errors=errors, warnings=warnings, data_type="weather"
            )

        # Validate data types
        if not isinstance(data_dict["region_id"], int):
            errors.append("region_id must be an integer")

        if not isinstance(data_dict["date"], (datetime, str)):
            errors.append("date must be datetime or string")

        # Validate ranges
        rainfall = data_dict.get("rainfall")
        if rainfall is not None:
            if not isinstance(rainfall, (int, float)):
                errors.append("rainfall must be a number")
            elif rainfall < 0 or rainfall > 500:
                errors.append("rainfall must be between 0 and 500 mm")

        humidity = data_dict.get("humidity")
        if humidity is not None:
            if not isinstance(humidity, (int, float)):
                errors.append("humidity must be a number")
            elif humidity < 0 or humidity > 100:
                errors.append("humidity must be between 0 and 100%")

        temperature = data_dict.get("temperature")
        if temperature is not None:
            if not isinstance(temperature, (int, float)):
                errors.append("temperature must be a number")
            elif temperature < 15 or temperature > 40:
                errors.append("temperature must be between 15 and 40°C")

        wind_speed = data_dict.get("wind_speed")
        if wind_speed is not None:
            if not isinstance(wind_speed, (int, float)):
                errors.append("wind_speed must be a number")
            elif wind_speed < 0 or wind_speed > 100:
                errors.append("wind_speed must be between 0 and 100 km/h")

        return ValidationResult(
            valid=len(errors) == 0,
            errors=errors,
            warnings=warnings,
            data_type="weather",
        )


class FloodEventSchema(Schema):
    """Schema for validating flood event data."""

    def validate(self, data: Any) -> ValidationResult:
        """Validate flood event data."""
        errors: List[str] = []
        warnings: List[str] = []

        # Check if data is FloodEvent instance or dict
        if isinstance(data, FloodEvent):
            data_dict = {
                "region_id": data.region_id,
                "date": data.date,
                "severity": data.severity,
                "water_level": data.water_level,
                "duration_hours": data.duration_hours,
                "affected_area_km2": data.affected_area_km2,
            }
        elif isinstance(data, dict):
            data_dict = data
        else:
            return ValidationResult(
                valid=False,
                errors=["Data must be FloodEvent instance or dict"],
                warnings=[],
                data_type="flood_event",
            )

        # Validate required fields
        required_fields = ["region_id", "date", "severity"]
        for field in required_fields:
            if field not in data_dict or data_dict[field] is None:
                errors.append(f"Missing required field: {field}")

        if errors:
            return ValidationResult(
                valid=False, errors=errors, warnings=warnings, data_type="flood_event"
            )

        # Validate data types
        if not isinstance(data_dict["region_id"], int):
            errors.append("region_id must be an integer")

        if not isinstance(data_dict["date"], (datetime, str)):
            errors.append("date must be datetime or string")

        # Validate severity range
        severity = data_dict.get("severity")
        if severity is not None:
            if not isinstance(severity, int):
                errors.append("severity must be an integer")
            elif severity < 1 or severity > 4:
                errors.append("severity must be between 1 and 4")

        # Validate optional fields
        water_level = data_dict.get("water_level")
        if water_level is not None:
            if not isinstance(water_level, (int, float)):
                errors.append("water_level must be a number")
            elif water_level < 0:
                errors.append("water_level must be non-negative")

        duration_hours = data_dict.get("duration_hours")
        if duration_hours is not None:
            if not isinstance(duration_hours, int):
                errors.append("duration_hours must be an integer")
            elif duration_hours < 0:
                errors.append("duration_hours must be non-negative")

        affected_area_km2 = data_dict.get("affected_area_km2")
        if affected_area_km2 is not None:
            if not isinstance(affected_area_km2, (int, float)):
                errors.append("affected_area_km2 must be a number")
            elif affected_area_km2 < 0:
                errors.append("affected_area_km2 must be non-negative")

        return ValidationResult(
            valid=len(errors) == 0,
            errors=errors,
            warnings=warnings,
            data_type="flood_event",
        )


class OSMDataSchema(Schema):
    """Schema for validating OSM data."""

    def validate(self, data: Any) -> ValidationResult:
        """Validate OSM data (roads and facilities)."""
        errors: List[str] = []
        warnings: List[str] = []

        if not isinstance(data, dict):
            return ValidationResult(
                valid=False,
                errors=["OSM data must be a dictionary"],
                warnings=[],
                data_type="osm_data",
            )

        # Validate roads
        if "roads" in data:
            if not isinstance(data["roads"], list):
                errors.append("roads must be a list")
            else:
                for i, road in enumerate(data["roads"]):
                    if not isinstance(road, dict):
                        errors.append(f"Road {i} must be a dictionary")
                        continue

                    # Check required road fields
                    if "osm_id" not in road:
                        errors.append(f"Road {i} missing osm_id")
                    if "road_type" not in road:
                        errors.append(f"Road {i} missing road_type")
                    if "length_km" not in road:
                        errors.append(f"Road {i} missing length_km")

        # Validate facilities
        if "facilities" in data:
            if not isinstance(data["facilities"], list):
                errors.append("facilities must be a list")
            else:
                for i, facility in enumerate(data["facilities"]):
                    if not isinstance(facility, dict):
                        errors.append(f"Facility {i} must be a dictionary")
                        continue

                    # Check required facility fields
                    required = ["osm_id", "name", "facility_type", "latitude", "longitude"]
                    for field in required:
                        if field not in facility:
                            errors.append(f"Facility {i} missing {field}")

                    # Validate coordinates
                    if "latitude" in facility:
                        lat = facility["latitude"]
                        if not isinstance(lat, (int, float)) or lat < -90 or lat > 90:
                            errors.append(f"Facility {i} has invalid latitude")

                    if "longitude" in facility:
                        lon = facility["longitude"]
                        if not isinstance(lon, (int, float)) or lon < -180 or lon > 180:
                            errors.append(f"Facility {i} has invalid longitude")

        return ValidationResult(
            valid=len(errors) == 0,
            errors=errors,
            warnings=warnings,
            data_type="osm_data",
        )
