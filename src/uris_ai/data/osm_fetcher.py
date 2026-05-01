"""
OpenStreetMap Data Fetcher.
Fetches road and facility data from OpenStreetMap API (Overpass API).
"""

import logging
import time
from datetime import datetime
from typing import List, Dict, Any, Optional
import requests
from requests.exceptions import RequestException

from ..config import settings
from .integrator import DataIntegrator, DataFetchError
from .models import OSMDataBatch, OSMRoad, OSMFacility
from .schemas import OSMDataSchema

logger = logging.getLogger(__name__)


class OSMDataFetcher(DataIntegrator):
    """
    Fetcher for OpenStreetMap data (roads and facilities).
    
    Features:
    - Fetch roads and facilities from Overpass API
    - Parse and transform OSM data to internal format
    - Retry mechanism for API failures
    """

    def __init__(
        self,
        api_url: Optional[str] = None,
        max_retries: int = 3,
        initial_backoff: float = 1.0,
    ) -> None:
        """
        Initialize OSM Data Fetcher.
        
        Args:
            api_url: Overpass API URL (defaults to settings)
            max_retries: Maximum number of retry attempts
            initial_backoff: Initial backoff time in seconds
        """
        super().__init__()
        self.api_url = api_url or settings.osm_api_url
        self.max_retries = max_retries
        self.initial_backoff = initial_backoff
        self.schema = OSMDataSchema()

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
        logger.info(f"Fetching OSM data for {len(region_ids)} regions")

        all_roads: List[OSMRoad] = []
        all_facilities: List[OSMFacility] = []

        # For each region, fetch roads and facilities
        for region_id in region_ids:
            try:
                # Get region bounding box from database
                bbox = self._get_region_bbox(region_id)

                # Fetch roads
                roads = self._fetch_roads(bbox)
                all_roads.extend(roads)

                # Fetch facilities
                facilities = self._fetch_facilities(bbox)
                all_facilities.extend(facilities)

                logger.info(
                    f"Fetched {len(roads)} roads and {len(facilities)} facilities "
                    f"for region {region_id}"
                )

            except Exception as e:
                logger.error(f"Failed to fetch OSM data for region {region_id}: {e}")
                # Continue with other regions
                continue

        if not all_roads and not all_facilities:
            raise DataFetchError(
                f"Failed to fetch OSM data for any of the {len(region_ids)} regions"
            )

        # Validate data
        osm_data = {"roads": [self._road_to_dict(r) for r in all_roads], "facilities": [self._facility_to_dict(f) for f in all_facilities]}
        validation_result = self.schema.validate(osm_data)

        if not validation_result.valid:
            logger.warning(f"OSM data validation warnings: {validation_result.errors}")

        batch = OSMDataBatch(
            roads=all_roads,
            facilities=all_facilities,
            timestamp=datetime.utcnow(),
            source=self.api_url,
        )

        logger.info(
            f"Successfully fetched {len(all_roads)} roads and "
            f"{len(all_facilities)} facilities"
        )

        return batch

    def _get_region_bbox(self, region_id: int) -> Dict[str, float]:
        """
        Get bounding box for a region from database.
        
        Args:
            region_id: Region ID
            
        Returns:
            Dictionary with bbox coordinates (south, west, north, east)
        """
        from ..models.database import get_db
        from ..models.database import Region

        try:
            db = next(get_db())
            region = db.query(Region).filter(Region.region_id == region_id).first()

            if not region:
                raise DataFetchError(f"Region {region_id} not found in database")

            # Calculate bounding box around region center
            # Approximate: 0.1 degree ~ 11 km
            bbox_size = 0.05  # ~5.5 km radius

            return {
                "south": region.latitude - bbox_size,
                "west": region.longitude - bbox_size,
                "north": region.latitude + bbox_size,
                "east": region.longitude + bbox_size,
            }

        except Exception as e:
            logger.error(f"Failed to get bbox for region {region_id}: {e}")
            raise DataFetchError(f"Failed to get region bbox: {e}")

    def _fetch_roads(self, bbox: Dict[str, float]) -> List[OSMRoad]:
        """
        Fetch roads from Overpass API for given bounding box.
        
        Args:
            bbox: Bounding box coordinates
            
        Returns:
            List of OSMRoad objects
        """
        # Construct Overpass QL query for roads
        query = f"""
        [out:json][timeout:25];
        (
          way["highway"~"primary|secondary|tertiary"]
            ({bbox['south']},{bbox['west']},{bbox['north']},{bbox['east']});
        );
        out geom;
        """

        # Execute query with retry
        response_data = self._execute_overpass_query(query)

        # Parse roads from response
        roads: List[OSMRoad] = []

        for element in response_data.get("elements", []):
            if element.get("type") != "way":
                continue

            try:
                road = self._parse_road_element(element)
                roads.append(road)
            except Exception as e:
                logger.warning(f"Failed to parse road element: {e}")
                continue

        return roads

    def _fetch_facilities(self, bbox: Dict[str, float]) -> List[OSMFacility]:
        """
        Fetch public facilities from Overpass API for given bounding box.
        
        Args:
            bbox: Bounding box coordinates
            
        Returns:
            List of OSMFacility objects
        """
        # Construct Overpass QL query for facilities
        query = f"""
        [out:json][timeout:25];
        (
          node["amenity"~"hospital|clinic|school|government"]
            ({bbox['south']},{bbox['west']},{bbox['north']},{bbox['east']});
          way["amenity"~"hospital|clinic|school|government"]
            ({bbox['south']},{bbox['west']},{bbox['north']},{bbox['east']});
        );
        out center;
        """

        # Execute query with retry
        response_data = self._execute_overpass_query(query)

        # Parse facilities from response
        facilities: List[OSMFacility] = []

        for element in response_data.get("elements", []):
            try:
                facility = self._parse_facility_element(element)
                if facility:
                    facilities.append(facility)
            except Exception as e:
                logger.warning(f"Failed to parse facility element: {e}")
                continue

        return facilities

    def _execute_overpass_query(self, query: str) -> Dict[str, Any]:
        """
        Execute Overpass API query with retry mechanism.
        
        Args:
            query: Overpass QL query string
            
        Returns:
            Parsed JSON response
            
        Raises:
            DataFetchError: If query fails after all retries
        """
        last_exception: Optional[Exception] = None

        for attempt in range(self.max_retries):
            try:
                # Apply backoff
                if attempt > 0:
                    backoff_time = self.initial_backoff * (2 ** (attempt - 1))
                    logger.info(
                        f"Retry attempt {attempt + 1}/{self.max_retries} "
                        f"after {backoff_time}s backoff"
                    )
                    time.sleep(backoff_time)

                # Make request
                response = requests.post(
                    self.api_url,
                    data={"data": query},
                    timeout=30,  # 30 second timeout
                )

                response.raise_for_status()
                return response.json()

            except RequestException as e:
                last_exception = e
                logger.warning(
                    f"Overpass API request failed "
                    f"(attempt {attempt + 1}/{self.max_retries}): {e}"
                )
            except Exception as e:
                last_exception = e
                logger.error(f"Unexpected error in Overpass query: {e}")
                break

        # All retries exhausted
        error_msg = f"Failed to execute Overpass query after {self.max_retries} attempts"
        if last_exception:
            error_msg += f": {last_exception}"

        raise DataFetchError(error_msg)

    def _parse_road_element(self, element: Dict[str, Any]) -> OSMRoad:
        """
        Parse OSM road element to OSMRoad object.
        
        Args:
            element: OSM element from Overpass API response
            
        Returns:
            OSMRoad object
        """
        osm_id = str(element["id"])
        tags = element.get("tags", {})

        name = tags.get("name")
        road_type = tags.get("highway", "unknown")

        # Calculate road length from geometry
        geometry = element.get("geometry", [])
        length_km = self._calculate_road_length(geometry)

        # Create GeoJSON geometry
        geojson_geometry = {
            "type": "LineString",
            "coordinates": [[node["lon"], node["lat"]] for node in geometry],
        }

        return OSMRoad(
            osm_id=osm_id,
            name=name,
            road_type=road_type,
            length_km=length_km,
            geometry=geojson_geometry,
        )

    def _parse_facility_element(self, element: Dict[str, Any]) -> Optional[OSMFacility]:
        """
        Parse OSM facility element to OSMFacility object.
        
        Args:
            element: OSM element from Overpass API response
            
        Returns:
            OSMFacility object or None if parsing fails
        """
        osm_id = str(element["id"])
        tags = element.get("tags", {})

        # Get facility name
        name = tags.get("name")
        if not name:
            # Skip facilities without names
            return None

        # Determine facility type
        amenity = tags.get("amenity", "unknown")
        facility_type = self._map_amenity_to_facility_type(amenity)

        # Get coordinates
        if element["type"] == "node":
            latitude = element["lat"]
            longitude = element["lon"]
        elif "center" in element:
            latitude = element["center"]["lat"]
            longitude = element["center"]["lon"]
        else:
            # Skip if no coordinates available
            return None

        return OSMFacility(
            osm_id=osm_id,
            name=name,
            facility_type=facility_type,
            latitude=latitude,
            longitude=longitude,
            tags=tags,
        )

    def _map_amenity_to_facility_type(self, amenity: str) -> str:
        """
        Map OSM amenity tag to internal facility type.
        
        Args:
            amenity: OSM amenity tag value
            
        Returns:
            Internal facility type
        """
        mapping = {
            "hospital": "hospital",
            "clinic": "clinic",
            "doctors": "clinic",
            "school": "school",
            "university": "school",
            "college": "school",
            "townhall": "government",
            "public_building": "government",
            "government": "government",
        }

        return mapping.get(amenity, "other")

    def _calculate_road_length(self, geometry: List[Dict[str, float]]) -> float:
        """
        Calculate road length from geometry coordinates.
        
        Args:
            geometry: List of coordinate points
            
        Returns:
            Length in kilometers
        """
        if len(geometry) < 2:
            return 0.0

        from math import radians, sin, cos, sqrt, atan2

        total_length = 0.0
        earth_radius_km = 6371.0

        for i in range(len(geometry) - 1):
            lat1 = radians(geometry[i]["lat"])
            lon1 = radians(geometry[i]["lon"])
            lat2 = radians(geometry[i + 1]["lat"])
            lon2 = radians(geometry[i + 1]["lon"])

            # Haversine formula
            dlat = lat2 - lat1
            dlon = lon2 - lon1

            a = sin(dlat / 2) ** 2 + cos(lat1) * cos(lat2) * sin(dlon / 2) ** 2
            c = 2 * atan2(sqrt(a), sqrt(1 - a))

            distance = earth_radius_km * c
            total_length += distance

        return total_length

    def _road_to_dict(self, road: OSMRoad) -> Dict[str, Any]:
        """Convert OSMRoad to dictionary for validation."""
        return {
            "osm_id": road.osm_id,
            "name": road.name,
            "road_type": road.road_type,
            "length_km": road.length_km,
            "geometry": road.geometry,
        }

    def _facility_to_dict(self, facility: OSMFacility) -> Dict[str, Any]:
        """Convert OSMFacility to dictionary for validation."""
        return {
            "osm_id": facility.osm_id,
            "name": facility.name,
            "facility_type": facility.facility_type,
            "latitude": facility.latitude,
            "longitude": facility.longitude,
            "tags": facility.tags,
        }

    def fetch_weather_data(self, region_ids: List[int]):
        """Not implemented in OSMDataFetcher."""
        raise NotImplementedError("fetch_weather_data not implemented in OSMDataFetcher")

    def fetch_flood_history(self, region_ids: List[int], start_date, end_date):
        """Not implemented in OSMDataFetcher."""
        raise NotImplementedError("fetch_flood_history not implemented in OSMDataFetcher")
