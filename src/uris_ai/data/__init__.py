"""Data ingestion and processing module."""

from .models import (
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
)
from .integrator import DataIntegrator, DataFetchError, StorageError
from .weather_connector import WeatherAPIConnector
from .flood_loader import HistoricalFloodLoader
from .osm_fetcher import OSMDataFetcher
from .validator import DataValidator, get_validator
from .schemas import Schema, WeatherDataSchema, FloodEventSchema, OSMDataSchema

__all__ = [
    # Models
    "DataType",
    "WeatherData",
    "WeatherDataBatch",
    "FloodEvent",
    "FloodEventBatch",
    "OSMRoad",
    "OSMFacility",
    "OSMDataBatch",
    "ValidationResult",
    "StorageResult",
    # Base classes
    "DataIntegrator",
    "DataFetchError",
    "StorageError",
    # Connectors
    "WeatherAPIConnector",
    "HistoricalFloodLoader",
    "OSMDataFetcher",
    # Validation
    "DataValidator",
    "get_validator",
    "Schema",
    "WeatherDataSchema",
    "FloodEventSchema",
    "OSMDataSchema",
]
