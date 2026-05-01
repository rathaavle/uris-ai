"""
Weather API Connector for fetching weather data.
Integrates with BMKG API or equivalent weather API with retry mechanism.
"""

import logging
import time
from datetime import datetime
from typing import List, Optional
import requests
from requests.exceptions import RequestException, Timeout, ConnectionError

from ..config import settings
from .integrator import DataIntegrator, DataFetchError
from .models import WeatherData, WeatherDataBatch
from .schemas import WeatherDataSchema

logger = logging.getLogger(__name__)


class WeatherAPIConnector(DataIntegrator):
    """
    Connector for fetching weather data from external API.
    
    Features:
    - Retry mechanism with exponential backoff
    - Data validation before returning
    - Error handling and logging
    """

    def __init__(
        self,
        api_url: Optional[str] = None,
        api_key: Optional[str] = None,
        max_retries: int = 3,
        initial_backoff: float = 1.0,
    ) -> None:
        """
        Initialize Weather API Connector.
        
        Args:
            api_url: Weather API URL (defaults to settings)
            api_key: API key for authentication (defaults to settings)
            max_retries: Maximum number of retry attempts
            initial_backoff: Initial backoff time in seconds
        """
        super().__init__()
        self.api_url = api_url or settings.weather_api_url
        self.api_key = api_key or settings.weather_api_key
        self.max_retries = max_retries
        self.initial_backoff = initial_backoff
        self.schema = WeatherDataSchema()

    def fetch_weather_data(self, region_ids: List[int]) -> WeatherDataBatch:
        """
        Fetch weather data for specified regions with retry mechanism.
        
        Args:
            region_ids: List of region IDs to fetch weather data for
            
        Returns:
            WeatherDataBatch containing weather data for all regions
            
        Raises:
            DataFetchError: If data fetching fails after all retries
        """
        logger.info(f"Fetching weather data for {len(region_ids)} regions")

        weather_data_list: List[WeatherData] = []

        for region_id in region_ids:
            try:
                weather_data = self._fetch_weather_for_region(region_id)
                weather_data_list.append(weather_data)
            except DataFetchError as e:
                logger.error(f"Failed to fetch weather data for region {region_id}: {e}")
                # Continue with other regions instead of failing completely
                continue

        if not weather_data_list:
            raise DataFetchError(
                f"Failed to fetch weather data for any of the {len(region_ids)} regions"
            )

        batch = WeatherDataBatch(
            data=weather_data_list,
            timestamp=datetime.utcnow(),
            source=self.api_url,
        )

        logger.info(
            f"Successfully fetched weather data for {len(weather_data_list)} regions"
        )

        return batch

    def _fetch_weather_for_region(self, region_id: int) -> WeatherData:
        """
        Fetch weather data for a single region with exponential backoff retry.
        
        Args:
            region_id: Region ID to fetch weather data for
            
        Returns:
            WeatherData for the region
            
        Raises:
            DataFetchError: If fetching fails after all retries
        """
        last_exception: Optional[Exception] = None

        for attempt in range(self.max_retries):
            try:
                # Calculate backoff time with exponential increase
                if attempt > 0:
                    backoff_time = self.initial_backoff * (2 ** (attempt - 1))
                    logger.info(
                        f"Retry attempt {attempt + 1}/{self.max_retries} "
                        f"for region {region_id} after {backoff_time}s backoff"
                    )
                    time.sleep(backoff_time)

                # Make API request
                weather_data = self._make_api_request(region_id)

                # Validate data
                validation_result = self.schema.validate(weather_data)
                if not validation_result.valid:
                    logger.warning(
                        f"Weather data validation failed for region {region_id}: "
                        f"{validation_result.errors}"
                    )
                    raise DataFetchError(
                        f"Invalid weather data: {', '.join(validation_result.errors)}"
                    )

                logger.info(f"Successfully fetched weather data for region {region_id}")
                return weather_data

            except (RequestException, Timeout, ConnectionError) as e:
                last_exception = e
                logger.warning(
                    f"Network error fetching weather data for region {region_id} "
                    f"(attempt {attempt + 1}/{self.max_retries}): {e}"
                )
            except Exception as e:
                last_exception = e
                logger.error(
                    f"Unexpected error fetching weather data for region {region_id}: {e}"
                )
                # Retry on all exceptions to allow recovery from transient errors

        # All retries exhausted
        error_msg = (
            f"Failed to fetch weather data for region {region_id} "
            f"after {self.max_retries} attempts"
        )
        if last_exception:
            error_msg += f": {last_exception}"

        raise DataFetchError(error_msg)

    def _make_api_request(self, region_id: int) -> WeatherData:
        """
        Make actual API request to fetch weather data.
        
        Args:
            region_id: Region ID to fetch data for
            
        Returns:
            WeatherData object
            
        Raises:
            RequestException: If API request fails
        """
        # Prepare request parameters
        params = {"region_id": region_id}
        headers = {}

        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"

        # Make request with timeout
        response = requests.get(
            self.api_url,
            params=params,
            headers=headers,
            timeout=10,  # 10 second timeout
        )

        # Check response status
        response.raise_for_status()

        # Parse response
        data = response.json()

        # Transform API response to WeatherData
        # Note: This is a generic implementation. Actual transformation
        # depends on the specific API response format
        weather_data = self._transform_api_response(region_id, data)

        return weather_data

    def _transform_api_response(self, region_id: int, api_data: dict) -> WeatherData:
        """
        Transform API response to WeatherData object.
        
        Args:
            region_id: Region ID
            api_data: Raw API response data
            
        Returns:
            WeatherData object
        """
        # This is a generic transformation. Adjust based on actual API format.
        # Example assumes API returns data in a specific format.

        # Handle different possible API response formats
        if "data" in api_data:
            data = api_data["data"]
        else:
            data = api_data

        # Extract weather parameters with fallbacks
        rainfall = float(data.get("rainfall", data.get("curah_hujan", 0)))
        humidity = float(data.get("humidity", data.get("kelembaban", 0)))
        temperature = float(data.get("temperature", data.get("suhu", 25)))
        wind_speed = data.get("wind_speed", data.get("kecepatan_angin"))

        if wind_speed is not None:
            wind_speed = float(wind_speed)

        # Parse date
        date_str = data.get("date", data.get("tanggal"))
        if date_str:
            try:
                date = datetime.fromisoformat(date_str.replace("Z", "+00:00"))
            except (ValueError, AttributeError):
                date = datetime.utcnow()
        else:
            date = datetime.utcnow()

        return WeatherData(
            region_id=region_id,
            date=date,
            rainfall=rainfall,
            humidity=humidity,
            temperature=temperature,
            wind_speed=wind_speed,
        )

    def fetch_flood_history(
        self, region_ids: List[int], start_date, end_date
    ):
        """Not implemented in WeatherAPIConnector."""
        raise NotImplementedError(
            "fetch_flood_history not implemented in WeatherAPIConnector"
        )

    def fetch_osm_data(self, region_ids: List[int]):
        """Not implemented in WeatherAPIConnector."""
        raise NotImplementedError("fetch_osm_data not implemented in WeatherAPIConnector")
