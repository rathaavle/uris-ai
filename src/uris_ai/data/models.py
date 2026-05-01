"""
Data models for the Data Ingestion Layer.
Defines data structures for weather, flood, OSM data, and validation results.
"""

from dataclasses import dataclass
from datetime import datetime
from typing import List, Optional, Dict, Any
from enum import Enum


class DataType(str, Enum):
    """Types of data that can be ingested."""
    WEATHER = "weather"
    FLOOD_HISTORY = "flood_history"
    OSM_DATA = "osm_data"


@dataclass
class WeatherData:
    """Weather data for a specific region."""
    region_id: int
    date: datetime
    rainfall: float  # mm, range: 0-500
    humidity: float  # %, range: 0-100
    temperature: float  # °C, range: 15-40
    wind_speed: Optional[float] = None  # km/h, range: 0-100


@dataclass
class WeatherDataBatch:
    """Batch of weather data for multiple regions."""
    data: List[WeatherData]
    timestamp: datetime
    source: str


@dataclass
class FloodEvent:
    """Historical flood event data."""
    region_id: int
    date: datetime
    severity: int  # 1=Rendah, 2=Sedang, 3=Tinggi, 4=Kritis
    water_level: Optional[float] = None  # cm
    duration_hours: Optional[int] = None
    affected_area_km2: Optional[float] = None


@dataclass
class FloodEventBatch:
    """Batch of flood event data."""
    data: List[FloodEvent]
    timestamp: datetime
    source: str


@dataclass
class OSMRoad:
    """Road data from OpenStreetMap."""
    osm_id: str
    name: Optional[str]
    road_type: str  # primary/secondary/tertiary
    length_km: float
    geometry: Dict[str, Any]  # GeoJSON geometry


@dataclass
class OSMFacility:
    """Public facility data from OpenStreetMap."""
    osm_id: str
    name: str
    facility_type: str  # hospital/clinic/school/government
    latitude: float
    longitude: float
    tags: Dict[str, str]


@dataclass
class OSMDataBatch:
    """Batch of OSM data (roads and facilities)."""
    roads: List[OSMRoad]
    facilities: List[OSMFacility]
    timestamp: datetime
    source: str


@dataclass
class ValidationResult:
    """Result of data validation."""
    valid: bool
    errors: List[str]
    warnings: List[str]
    data_type: str


@dataclass
class StorageResult:
    """Result of storing data to Azure Blob Storage."""
    success: bool
    blob_url: str
    blob_name: str
    size_bytes: int
    timestamp: datetime
    error_message: Optional[str] = None
