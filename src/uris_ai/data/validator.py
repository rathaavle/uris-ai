"""
Data Validator with comprehensive schema validation.
Validates data from all sources before processing or storage.
"""

import logging
from typing import Any, Dict, Type
from enum import Enum

from .models import ValidationResult, DataType
from .schemas import Schema, WeatherDataSchema, FloodEventSchema, OSMDataSchema

logger = logging.getLogger(__name__)


class DataValidator:
    """
    Comprehensive data validator for all data types.
    
    Features:
    - Schema-based validation for all data types
    - Extensible schema registry
    - Detailed error reporting
    """

    def __init__(self) -> None:
        """Initialize Data Validator with schema registry."""
        self._schema_registry: Dict[str, Schema] = {
            DataType.WEATHER: WeatherDataSchema(),
            DataType.FLOOD_HISTORY: FloodEventSchema(),
            DataType.OSM_DATA: OSMDataSchema(),
        }

    def register_schema(self, data_type: str, schema: Schema) -> None:
        """
        Register a new schema for a data type.
        
        Args:
            data_type: Type of data
            schema: Schema instance for validation
        """
        self._schema_registry[data_type] = schema
        logger.info(f"Registered schema for data type: {data_type}")

    def validate(self, data: Any, data_type: str) -> ValidationResult:
        """
        Validate data against registered schema.
        
        Args:
            data: Data to validate
            data_type: Type of data (must be registered)
            
        Returns:
            ValidationResult with validation status and errors
            
        Raises:
            ValueError: If data_type is not registered
        """
        if data_type not in self._schema_registry:
            raise ValueError(
                f"No schema registered for data type: {data_type}. "
                f"Available types: {list(self._schema_registry.keys())}"
            )

        schema = self._schema_registry[data_type]
        result = schema.validate(data)

        if not result.valid:
            logger.warning(
                f"Validation failed for {data_type}: {result.errors}"
            )
        else:
            logger.debug(f"Validation passed for {data_type}")

        return result

    def validate_weather(self, data: Any) -> ValidationResult:
        """
        Validate weather data.
        
        Args:
            data: Weather data to validate
            
        Returns:
            ValidationResult
        """
        return self.validate(data, DataType.WEATHER)

    def validate_flood_event(self, data: Any) -> ValidationResult:
        """
        Validate flood event data.
        
        Args:
            data: Flood event data to validate
            
        Returns:
            ValidationResult
        """
        return self.validate(data, DataType.FLOOD_HISTORY)

    def validate_osm_data(self, data: Any) -> ValidationResult:
        """
        Validate OSM data.
        
        Args:
            data: OSM data to validate
            
        Returns:
            ValidationResult
        """
        return self.validate(data, DataType.OSM_DATA)

    def validate_batch(
        self, data_list: list, data_type: str
    ) -> Dict[str, Any]:
        """
        Validate a batch of data items.
        
        Args:
            data_list: List of data items to validate
            data_type: Type of data
            
        Returns:
            Dictionary with validation summary:
            - total: Total number of items
            - valid: Number of valid items
            - invalid: Number of invalid items
            - errors: List of error messages
        """
        total = len(data_list)
        valid_count = 0
        invalid_count = 0
        all_errors = []

        for i, data in enumerate(data_list):
            result = self.validate(data, data_type)

            if result.valid:
                valid_count += 1
            else:
                invalid_count += 1
                all_errors.append(f"Item {i}: {', '.join(result.errors)}")

        summary = {
            "total": total,
            "valid": valid_count,
            "invalid": invalid_count,
            "errors": all_errors,
            "success_rate": valid_count / total if total > 0 else 0.0,
        }

        logger.info(
            f"Batch validation for {data_type}: "
            f"{valid_count}/{total} valid ({summary['success_rate']:.1%})"
        )

        return summary

    def get_registered_types(self) -> list:
        """
        Get list of registered data types.
        
        Returns:
            List of registered data type names
        """
        return list(self._schema_registry.keys())


# Global validator instance
_validator_instance = None


def get_validator() -> DataValidator:
    """
    Get global DataValidator instance (singleton pattern).
    
    Returns:
        DataValidator instance
    """
    global _validator_instance

    if _validator_instance is None:
        _validator_instance = DataValidator()

    return _validator_instance
