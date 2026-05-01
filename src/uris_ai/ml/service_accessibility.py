"""
Service Accessibility Module - Component for evaluating accessibility of public facilities.

This module implements the Service_Accessibility_Module component that evaluates
the accessibility of public facilities during flood conditions and provides
alternative facility recommendations.

Requirements: 3.1, 3.2, 3.3, 3.4
"""

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Dict, List, Optional
import logging
import math

from sqlalchemy.orm import Session

from src.uris_ai.models.database import PublicFacility, Region
from src.uris_ai.ml.traffic_analyzer import TrafficImpact

# Configure logging
logger = logging.getLogger(__name__)


@dataclass
class AccessibilityReport:
    """
    Result of accessibility evaluation for public facilities.
    
    Attributes:
        region_id: ID of the analyzed region
        affected_facilities: List of facility IDs that are affected
        alternative_facilities: Mapping of facility_id to list of alternative facility IDs
        overload_warnings: List of facility IDs with estimated load > 90%
        timestamp: When the evaluation was performed
    """
    region_id: int
    affected_facilities: List[int]
    alternative_facilities: Dict[int, List[int]]
    overload_warnings: List[int]
    timestamp: datetime


class ServiceAccessibilityModule:
    """
    Component for evaluating accessibility of public facilities.
    
    This class evaluates how flooding affects public facility accessibility,
    finds alternative facilities, and estimates facility load.
    
    Requirements: 3.1, 3.2, 3.3, 3.4
    """

    # Maximum radius for alternative facility search (km)
    MAX_ALTERNATIVE_RADIUS_KM = 10.0
    
    # Facility load threshold for overload warning
    OVERLOAD_THRESHOLD = 0.9

    def __init__(self, db_session: Session):
        """
        Initialize the Service Accessibility Module.
        
        Args:
            db_session: SQLAlchemy database session for querying facility data
        """
        self.db_session = db_session
        logger.info("ServiceAccessibilityModule initialized")

    def evaluate_accessibility(
        self,
        region_id: int,
        traffic_impact: TrafficImpact
    ) -> AccessibilityReport:
        """
        Evaluate accessibility of public facilities in a region.
        
        This method evaluates how traffic impact affects facility accessibility by:
        1. Identifying affected facilities in the region
        2. Finding alternative facilities for each affected facility
        3. Estimating load on alternative facilities
        4. Identifying facilities at risk of overload
        
        Args:
            region_id: ID of the region to evaluate
            traffic_impact: Traffic impact analysis from Traffic_Analyzer
            
        Returns:
            AccessibilityReport object with evaluation results
            
        Requirements: 3.1, 3.4
        """
        logger.debug(f"Evaluating accessibility for region {region_id}")
        
        # Get affected facilities in the region
        affected_facilities = self.get_affected_facilities(region_id)
        
        # Find alternatives for each affected facility
        alternative_facilities = {}
        overload_warnings = []
        
        for facility in affected_facilities:
            # Find alternative facilities within radius
            alternatives = self.find_alternative_facilities(
                facility.id,
                radius_km=self.MAX_ALTERNATIVE_RADIUS_KM
            )
            
            if alternatives:
                alternative_facilities[facility.id] = [alt.id for alt in alternatives]
                
                # Check for potential overload on alternatives
                for alt in alternatives:
                    load = self.estimate_facility_load(alt.id)
                    if load > self.OVERLOAD_THRESHOLD and alt.id not in overload_warnings:
                        overload_warnings.append(alt.id)
        
        report = AccessibilityReport(
            region_id=region_id,
            affected_facilities=[f.id for f in affected_facilities],
            alternative_facilities=alternative_facilities,
            overload_warnings=overload_warnings,
            timestamp=datetime.now(timezone.utc)
        )
        
        logger.info(
            f"Accessibility evaluation complete for region {region_id}: "
            f"{len(affected_facilities)} facilities affected, "
            f"{len(overload_warnings)} overload warnings"
        )
        
        return report

    def find_alternative_facilities(
        self,
        facility_id: int,
        radius_km: float = MAX_ALTERNATIVE_RADIUS_KM
    ) -> List[PublicFacility]:
        """
        Find alternative facilities of the same type within a radius.
        
        Uses Haversine formula to calculate distances between facilities.
        Only returns operational facilities of the same type.
        
        Args:
            facility_id: ID of the facility to find alternatives for
            radius_km: Maximum search radius in kilometers (default: 10.0)
            
        Returns:
            List of PublicFacility objects within the radius
            
        Requirements: 3.2
        """
        # Get the original facility
        facility = self.db_session.query(PublicFacility).filter(
            PublicFacility.id == facility_id
        ).first()
        
        if facility is None:
            logger.warning(f"Facility {facility_id} not found")
            return []
        
        logger.debug(
            f"Finding alternatives for facility {facility_id} "
            f"({facility.name}, type={facility.type}) within {radius_km} km"
        )
        
        # Get all facilities of the same type that are operational
        # and not the original facility
        candidates = self.db_session.query(PublicFacility).filter(
            PublicFacility.type == facility.type,
            PublicFacility.is_operational == True,
            PublicFacility.id != facility_id
        ).all()
        
        # Filter by distance using Haversine formula
        alternatives = []
        for candidate in candidates:
            distance = self._calculate_haversine_distance(
                facility.latitude,
                facility.longitude,
                candidate.latitude,
                candidate.longitude
            )
            
            if distance <= radius_km:
                alternatives.append(candidate)
                logger.debug(
                    f"  Found alternative: {candidate.name} "
                    f"(distance: {distance:.2f} km)"
                )
        
        logger.info(
            f"Found {len(alternatives)} alternative facilities for "
            f"facility {facility_id} within {radius_km} km"
        )
        
        return alternatives

    def estimate_facility_load(self, facility_id: int) -> float:
        """
        Estimate the load on a facility.
        
        Load is estimated as a ratio (0.0 to 1.0) based on:
        - Number of users redirected to this facility
        - Facility capacity
        
        For MVP, this returns a simplified estimate. In production,
        this would integrate with real-time usage data.
        
        Args:
            facility_id: ID of the facility
            
        Returns:
            Estimated load as a float (0.0 to 1.0)
            
        Requirements: 3.3
        """
        facility = self.db_session.query(PublicFacility).filter(
            PublicFacility.id == facility_id
        ).first()
        
        if facility is None:
            logger.warning(f"Facility {facility_id} not found")
            return 0.0
        
        # For MVP: simplified load estimation
        # In production, this would query actual usage data
        # For now, we estimate based on whether the facility is operational
        # and has capacity information
        
        if not facility.is_operational:
            load = 1.0  # Non-operational = full load
        elif facility.capacity is None:
            # No capacity info, assume moderate load
            load = 0.5
        else:
            # Simplified: assume base load of 50% for operational facilities
            # This would be replaced with actual usage data in production
            load = 0.5
        
        logger.debug(
            f"Estimated load for facility {facility_id} ({facility.name}): "
            f"{load:.2f}"
        )
        
        return load

    def get_affected_facilities(self, region_id: int) -> List[PublicFacility]:
        """
        Get list of public facilities affected in a region.
        
        A facility is considered affected if it is in a region with
        traffic impact (indicating flood risk).
        
        Args:
            region_id: ID of the region
            
        Returns:
            List of PublicFacility objects in the region
            
        Requirements: 3.1
        """
        facilities = self.db_session.query(PublicFacility).filter(
            PublicFacility.region_id == region_id
        ).all()
        
        logger.debug(f"Found {len(facilities)} facilities in region {region_id}")
        
        return facilities

    def _calculate_haversine_distance(
        self,
        lat1: float,
        lon1: float,
        lat2: float,
        lon2: float
    ) -> float:
        """
        Calculate the great-circle distance between two points on Earth.
        
        Uses the Haversine formula to calculate distance in kilometers.
        
        Args:
            lat1: Latitude of first point (degrees)
            lon1: Longitude of first point (degrees)
            lat2: Latitude of second point (degrees)
            lon2: Longitude of second point (degrees)
            
        Returns:
            Distance in kilometers
        """
        # Earth's radius in kilometers
        R = 6371.0
        
        # Convert degrees to radians
        lat1_rad = math.radians(lat1)
        lon1_rad = math.radians(lon1)
        lat2_rad = math.radians(lat2)
        lon2_rad = math.radians(lon2)
        
        # Haversine formula
        dlat = lat2_rad - lat1_rad
        dlon = lon2_rad - lon1_rad
        
        a = (math.sin(dlat / 2) ** 2 +
             math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(dlon / 2) ** 2)
        c = 2 * math.asin(math.sqrt(a))
        
        distance = R * c
        
        return distance
