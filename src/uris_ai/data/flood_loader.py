"""
Historical Flood Data Loader.
Loads and parses historical flood data with validation and normalization.
"""

import logging
import csv
import json
from datetime import datetime, date
from typing import List, Optional, Union
from pathlib import Path

from .integrator import DataIntegrator, DataFetchError
from .models import FloodEvent, FloodEventBatch
from .schemas import FloodEventSchema

logger = logging.getLogger(__name__)


class HistoricalFloodLoader(DataIntegrator):
    """
    Loader for historical flood data.
    
    Features:
    - Load from CSV, JSON, or database
    - Data validation and normalization
    - Error handling for malformed data
    """

    def __init__(self, data_source: Optional[str] = None) -> None:
        """
        Initialize Historical Flood Loader.
        
        Args:
            data_source: Path to data source (file or database connection string)
        """
        super().__init__()
        self.data_source = data_source
        self.schema = FloodEventSchema()

    def fetch_flood_history(
        self, region_ids: List[int], start_date: date, end_date: date
    ) -> FloodEventBatch:
        """
        Load historical flood data for specified regions and date range.
        
        Args:
            region_ids: List of region IDs
            start_date: Start date for historical data
            end_date: End date for historical data
            
        Returns:
            FloodEventBatch containing historical flood events
            
        Raises:
            DataFetchError: If data loading fails
        """
        logger.info(
            f"Loading flood history for {len(region_ids)} regions "
            f"from {start_date} to {end_date}"
        )

        try:
            # Load data based on source type
            if self.data_source:
                flood_events = self._load_from_file(
                    region_ids, start_date, end_date
                )
            else:
                # Load from database
                flood_events = self._load_from_database(
                    region_ids, start_date, end_date
                )

            # Validate and normalize data
            validated_events = self._validate_and_normalize(flood_events)

            batch = FloodEventBatch(
                data=validated_events,
                timestamp=datetime.utcnow(),
                source=self.data_source or "database",
            )

            logger.info(
                f"Successfully loaded {len(validated_events)} flood events"
            )

            return batch

        except Exception as e:
            logger.error(f"Failed to load flood history: {e}")
            raise DataFetchError(f"Failed to load flood history: {e}")

    def _load_from_file(
        self, region_ids: List[int], start_date: date, end_date: date
    ) -> List[FloodEvent]:
        """
        Load flood data from file (CSV or JSON).
        
        Args:
            region_ids: List of region IDs to filter
            start_date: Start date filter
            end_date: End date filter
            
        Returns:
            List of FloodEvent objects
        """
        if not self.data_source:
            raise DataFetchError("No data source specified")

        file_path = Path(self.data_source)

        if not file_path.exists():
            raise DataFetchError(f"Data source file not found: {self.data_source}")

        # Determine file type and load accordingly
        if file_path.suffix.lower() == ".csv":
            return self._load_from_csv(file_path, region_ids, start_date, end_date)
        elif file_path.suffix.lower() == ".json":
            return self._load_from_json(file_path, region_ids, start_date, end_date)
        else:
            raise DataFetchError(
                f"Unsupported file format: {file_path.suffix}. "
                "Supported formats: .csv, .json"
            )

    def _load_from_csv(
        self,
        file_path: Path,
        region_ids: List[int],
        start_date: date,
        end_date: date,
    ) -> List[FloodEvent]:
        """Load flood data from CSV file."""
        flood_events: List[FloodEvent] = []

        with open(file_path, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)

            for row in reader:
                try:
                    # Parse region_id
                    region_id = int(row["region_id"])

                    # Filter by region_ids
                    if region_id not in region_ids:
                        continue

                    # Parse date
                    event_date = self._parse_date(row["date"])

                    # Filter by date range
                    if not (start_date <= event_date.date() <= end_date):
                        continue

                    # Parse other fields
                    severity = int(row["severity"])
                    water_level = (
                        float(row["water_level"]) if row.get("water_level") else None
                    )
                    duration_hours = (
                        int(row["duration_hours"]) if row.get("duration_hours") else None
                    )
                    affected_area_km2 = (
                        float(row["affected_area_km2"])
                        if row.get("affected_area_km2")
                        else None
                    )

                    flood_event = FloodEvent(
                        region_id=region_id,
                        date=event_date,
                        severity=severity,
                        water_level=water_level,
                        duration_hours=duration_hours,
                        affected_area_km2=affected_area_km2,
                    )

                    flood_events.append(flood_event)

                except (KeyError, ValueError) as e:
                    logger.warning(f"Skipping malformed row in CSV: {e}")
                    continue

        return flood_events

    def _load_from_json(
        self,
        file_path: Path,
        region_ids: List[int],
        start_date: date,
        end_date: date,
    ) -> List[FloodEvent]:
        """Load flood data from JSON file."""
        flood_events: List[FloodEvent] = []

        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        # Handle different JSON structures
        if isinstance(data, list):
            events_data = data
        elif isinstance(data, dict) and "events" in data:
            events_data = data["events"]
        else:
            raise DataFetchError("Invalid JSON structure")

        for event_data in events_data:
            try:
                # Parse region_id
                region_id = int(event_data["region_id"])

                # Filter by region_ids
                if region_id not in region_ids:
                    continue

                # Parse date
                event_date = self._parse_date(event_data["date"])

                # Filter by date range
                if not (start_date <= event_date.date() <= end_date):
                    continue

                # Parse other fields
                severity = int(event_data["severity"])
                water_level = event_data.get("water_level")
                if water_level is not None:
                    water_level = float(water_level)

                duration_hours = event_data.get("duration_hours")
                if duration_hours is not None:
                    duration_hours = int(duration_hours)

                affected_area_km2 = event_data.get("affected_area_km2")
                if affected_area_km2 is not None:
                    affected_area_km2 = float(affected_area_km2)

                flood_event = FloodEvent(
                    region_id=region_id,
                    date=event_date,
                    severity=severity,
                    water_level=water_level,
                    duration_hours=duration_hours,
                    affected_area_km2=affected_area_km2,
                )

                flood_events.append(flood_event)

            except (KeyError, ValueError) as e:
                logger.warning(f"Skipping malformed event in JSON: {e}")
                continue

        return flood_events

    def _load_from_database(
        self, region_ids: List[int], start_date: date, end_date: date
    ) -> List[FloodEvent]:
        """
        Load flood data from database.
        
        Args:
            region_ids: List of region IDs to filter
            start_date: Start date filter
            end_date: End date filter
            
        Returns:
            List of FloodEvent objects
        """
        from ..models.database import get_db
        from ..models.database import FloodEvent as FloodEventModel

        flood_events: List[FloodEvent] = []

        try:
            db = next(get_db())

            # Query flood events
            query = db.query(FloodEventModel).filter(
                FloodEventModel.region_id.in_(region_ids),
                FloodEventModel.date >= start_date,
                FloodEventModel.date <= end_date,
            )

            for event_model in query.all():
                flood_event = FloodEvent(
                    region_id=event_model.region_id,
                    date=event_model.date,
                    severity=event_model.severity,
                    water_level=event_model.water_level,
                    duration_hours=event_model.duration_hours,
                    affected_area_km2=event_model.affected_area_km2,
                )
                flood_events.append(flood_event)

        except Exception as e:
            logger.error(f"Database error loading flood history: {e}")
            raise DataFetchError(f"Database error: {e}")

        return flood_events

    def _validate_and_normalize(
        self, flood_events: List[FloodEvent]
    ) -> List[FloodEvent]:
        """
        Validate and normalize flood event data.
        
        Args:
            flood_events: List of flood events to validate
            
        Returns:
            List of validated and normalized flood events
        """
        validated_events: List[FloodEvent] = []

        for event in flood_events:
            # Validate event
            validation_result = self.schema.validate(event)

            if not validation_result.valid:
                logger.warning(
                    f"Skipping invalid flood event for region {event.region_id}: "
                    f"{validation_result.errors}"
                )
                continue

            # Normalize data
            normalized_event = self._normalize_event(event)
            validated_events.append(normalized_event)

        return validated_events

    def _normalize_event(self, event: FloodEvent) -> FloodEvent:
        """
        Normalize flood event data.
        
        Args:
            event: Flood event to normalize
            
        Returns:
            Normalized flood event
        """
        # Ensure severity is within valid range
        severity = max(1, min(4, event.severity))

        # Ensure non-negative values for optional fields
        water_level = event.water_level
        if water_level is not None and water_level < 0:
            water_level = 0

        duration_hours = event.duration_hours
        if duration_hours is not None and duration_hours < 0:
            duration_hours = 0

        affected_area_km2 = event.affected_area_km2
        if affected_area_km2 is not None and affected_area_km2 < 0:
            affected_area_km2 = 0

        return FloodEvent(
            region_id=event.region_id,
            date=event.date,
            severity=severity,
            water_level=water_level,
            duration_hours=duration_hours,
            affected_area_km2=affected_area_km2,
        )

    def _parse_date(self, date_str: Union[str, datetime]) -> datetime:
        """
        Parse date string to datetime object.
        
        Args:
            date_str: Date string or datetime object
            
        Returns:
            datetime object
        """
        if isinstance(date_str, datetime):
            return date_str

        # Try different date formats
        formats = [
            "%Y-%m-%d %H:%M:%S",
            "%Y-%m-%d",
            "%d/%m/%Y",
            "%d-%m-%Y",
            "%Y/%m/%d",
        ]

        for fmt in formats:
            try:
                return datetime.strptime(date_str, fmt)
            except ValueError:
                continue

        # Try ISO format
        try:
            return datetime.fromisoformat(date_str.replace("Z", "+00:00"))
        except ValueError:
            pass

        raise ValueError(f"Unable to parse date: {date_str}")

    def fetch_weather_data(self, region_ids: List[int]):
        """Not implemented in HistoricalFloodLoader."""
        raise NotImplementedError(
            "fetch_weather_data not implemented in HistoricalFloodLoader"
        )

    def fetch_osm_data(self, region_ids: List[int]):
        """Not implemented in HistoricalFloodLoader."""
        raise NotImplementedError(
            "fetch_osm_data not implemented in HistoricalFloodLoader"
        )
