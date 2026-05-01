"""
Base DataIntegrator class for data ingestion.
Provides abstract interface for fetching, validating, and storing data.
"""

from abc import ABC, abstractmethod
from datetime import date, datetime
from typing import List, Any, Optional
import logging
from azure.storage.blob import BlobServiceClient
from azure.core.exceptions import AzureError

from ..config import settings
from .models import (
    WeatherDataBatch,
    FloodEventBatch,
    OSMDataBatch,
    ValidationResult,
    StorageResult,
    DataType,
)
from .schemas import Schema

logger = logging.getLogger(__name__)


class DataIntegrator(ABC):
    """
    Base class for data integration from external sources.
    
    Responsibilities:
    - Fetch data from external APIs
    - Validate data against schemas
    - Store raw data to Azure Blob Storage
    """

    def __init__(self) -> None:
        """Initialize DataIntegrator with Azure Blob Storage client."""
        self._blob_service_client: Optional[BlobServiceClient] = None
        self._setup_blob_storage()

    def _setup_blob_storage(self) -> None:
        """Setup Azure Blob Storage client."""
        try:
            # Only initialize if connection string is available
            if hasattr(settings, 'azure_storage_connection_string') and settings.azure_storage_connection_string:
                self._blob_service_client = BlobServiceClient.from_connection_string(
                    settings.azure_storage_connection_string
                )
                logger.info("Azure Blob Storage client initialized successfully")
            else:
                logger.warning("Azure Blob Storage connection string not configured")
                self._blob_service_client = None
        except Exception as e:
            logger.warning(f"Failed to initialize Azure Blob Storage client: {e}")
            self._blob_service_client = None

    @abstractmethod
    def fetch_weather_data(self, region_ids: List[int]) -> WeatherDataBatch:
        """
        Fetch weather data for specified regions.
        
        Args:
            region_ids: List of region IDs to fetch weather data for
            
        Returns:
            WeatherDataBatch containing weather data for all regions
            
        Raises:
            DataFetchError: If data fetching fails
        """
        pass

    @abstractmethod
    def fetch_flood_history(
        self, region_ids: List[int], start_date: date, end_date: date
    ) -> FloodEventBatch:
        """
        Fetch historical flood data for specified regions and date range.
        
        Args:
            region_ids: List of region IDs
            start_date: Start date for historical data
            end_date: End date for historical data
            
        Returns:
            FloodEventBatch containing historical flood events
            
        Raises:
            DataFetchError: If data fetching fails
        """
        pass

    @abstractmethod
    def fetch_osm_data(self, region_ids: List[int]) -> OSMDataBatch:
        """
        Fetch OpenStreetMap data (roads and facilities) for specified regions.
        
        Args:
            region_ids: List of region IDs
            
        Returns:
            OSMDataBatch containing roads and facilities data
            
        Raises:
            DataFetchError: If data fetching fails
        """
        pass

    def validate_data(self, data: Any, schema: Schema) -> ValidationResult:
        """
        Validate data against specified schema.
        
        Args:
            data: Data to validate
            schema: Schema to validate against
            
        Returns:
            ValidationResult with validation status and errors
        """
        return schema.validate(data)

    def store_raw_data(
        self, data: Any, data_type: str, metadata: Optional[dict] = None
    ) -> StorageResult:
        """
        Store raw data to Azure Blob Storage.
        
        Args:
            data: Data to store (will be serialized to JSON)
            data_type: Type of data (weather/flood_history/osm_data)
            metadata: Optional metadata to attach to blob
            
        Returns:
            StorageResult with storage status and blob information
            
        Raises:
            StorageError: If storage operation fails
        """
        import json
        from datetime import datetime

        if self._blob_service_client is None:
            raise RuntimeError("Blob storage client not initialized")

        try:
            # Generate blob name with timestamp
            timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
            blob_name = f"{data_type}/{timestamp}.json"

            # Serialize data to JSON
            if hasattr(data, "__dict__"):
                # Handle dataclass objects
                json_data = json.dumps(data, default=lambda o: o.__dict__, indent=2)
            else:
                json_data = json.dumps(data, indent=2)

            # Get blob client
            container_name = settings.azure_storage_container_raw_data
            blob_client = self._blob_service_client.get_blob_client(
                container=container_name, blob=blob_name
            )

            # Upload data
            blob_client.upload_blob(
                json_data, overwrite=True, metadata=metadata or {}
            )

            # Get blob properties
            properties = blob_client.get_blob_properties()
            blob_url = blob_client.url

            logger.info(
                f"Successfully stored {data_type} data to blob: {blob_name}"
            )

            return StorageResult(
                success=True,
                blob_url=blob_url,
                blob_name=blob_name,
                size_bytes=properties.size,
                timestamp=datetime.utcnow(),
            )

        except AzureError as e:
            logger.error(f"Azure storage error: {e}")
            return StorageResult(
                success=False,
                blob_url="",
                blob_name=blob_name,
                size_bytes=0,
                timestamp=datetime.utcnow(),
                error_message=str(e),
            )
        except Exception as e:
            logger.error(f"Unexpected error storing data: {e}")
            return StorageResult(
                success=False,
                blob_url="",
                blob_name="",
                size_bytes=0,
                timestamp=datetime.utcnow(),
                error_message=str(e),
            )


class DataFetchError(Exception):
    """Exception raised when data fetching fails."""
    pass


class StorageError(Exception):
    """Exception raised when storage operation fails."""
    pass
