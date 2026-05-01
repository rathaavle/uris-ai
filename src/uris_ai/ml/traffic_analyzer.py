"""
Traffic Analyzer - Component for analyzing flood impact on traffic conditions.

This module implements the Traffic_Analyzer component that estimates the impact
of flooding on road networks and traffic conditions.

Requirements: 2.1, 2.2, 2.3, 2.4
"""

from dataclasses import dataclass
from datetime import datetime, timezone
from enum import Enum
from typing import Dict, List, Optional
import logging

from sqlalchemy.orm import Session

from src.uris_ai.models.database import Road, Region
from src.uris_ai.ml.flood_risk_engine import FloodRiskPrediction, RiskCategory

# Configure logging
logger = logging.getLogger(__name__)


class CongestionLevel(str, Enum):
    """Traffic congestion level classification."""
    SEDANG = "SEDANG"
    PARAH = "PARAH"
    TIDAK_DAPAT_DILALUI = "TIDAK_DAPAT_DILALUI"


@dataclass
class TrafficImpact:
    """
    Result of traffic impact analysis.
    
    Attributes:
        region_id: ID of the analyzed region
        affected_roads: List of road IDs that are affected by flooding
        congestion_levels: Mapping of road_id to congestion level
        is_isolated: Whether the region is isolated (all main roads impassable)
        timestamp: When the analysis was performed
    """
    region_id: int
    affected_roads: List[int]
    congestion_levels: Dict[int, CongestionLevel]
    is_isolated: bool
    timestamp: datetime


class TrafficAnalyzer:
    """
    Component for analyzing flood impact on traffic conditions.
    
    This class analyzes how flooding affects road networks and estimates
    congestion levels and regional isolation.
    
    Requirements: 2.1, 2.2, 2.3, 2.4
    """

    def __init__(self, db_session: Session):
        """
        Initialize the Traffic Analyzer.
        
        Args:
            db_session: SQLAlchemy database session for querying road data
        """
        self.db_session = db_session
        logger.info("TrafficAnalyzer initialized")

    def analyze_traffic_impact(
        self,
        region_id: int,
        flood_risk: FloodRiskPrediction
    ) -> TrafficImpact:
        """
        Analyze the impact of flooding on traffic in a region.
        
        This method estimates how flooding affects traffic conditions by:
        1. Identifying affected roads based on flood risk level
        2. Estimating congestion levels for each affected road
        3. Checking if the region is isolated
        
        Args:
            region_id: ID of the region to analyze
            flood_risk: Flood risk prediction from Flood_Risk_Engine
            
        Returns:
            TrafficImpact object with analysis results
            
        Requirements: 2.1, 2.3
        """
        logger.debug(f"Analyzing traffic impact for region {region_id}, "
                    f"flood risk: {flood_risk.category.value}")
        
        # Get affected roads based on flood risk
        affected_roads = self.get_affected_roads(region_id, flood_risk)
        
        # Estimate congestion level for each affected road
        congestion_levels = {}
        for road in affected_roads:
            level = self.estimate_congestion_level(road.id, flood_risk)
            congestion_levels[road.id] = level
        
        # Check if region is isolated
        is_isolated = self.check_region_isolation(region_id, congestion_levels)
        
        impact = TrafficImpact(
            region_id=region_id,
            affected_roads=[road.id for road in affected_roads],
            congestion_levels=congestion_levels,
            is_isolated=is_isolated,
            timestamp=datetime.now(timezone.utc)
        )
        
        logger.info(
            f"Traffic impact analysis complete for region {region_id}: "
            f"{len(affected_roads)} roads affected, isolated={is_isolated}"
        )
        
        return impact

    def get_affected_roads(
        self,
        region_id: int,
        flood_risk: FloodRiskPrediction
    ) -> List[Road]:
        """
        Get list of roads affected by flooding in a region.
        
        Roads are considered affected if the flood risk is HIGH or CRITICAL.
        For lower risk levels, no roads are considered affected.
        
        Args:
            region_id: ID of the region
            flood_risk: Flood risk prediction
            
        Returns:
            List of Road objects that are affected
            
        Requirements: 2.1
        """
        # Only consider roads affected if risk is HIGH or CRITICAL
        if flood_risk.category not in [RiskCategory.TINGGI, RiskCategory.KRITIS]:
            logger.debug(f"Region {region_id} has {flood_risk.category.value} risk, "
                        "no roads affected")
            return []
        
        # Query all roads in the region
        roads = self.db_session.query(Road).filter(
            Road.region_id == region_id
        ).all()
        
        logger.debug(f"Found {len(roads)} roads in region {region_id}")
        
        return roads

    def estimate_congestion_level(
        self,
        road_id: int,
        flood_risk: FloodRiskPrediction
    ) -> CongestionLevel:
        """
        Estimate congestion level for a specific road.
        
        Congestion level is estimated based on flood risk severity:
        - TINGGI (HIGH) risk → SEDANG congestion
        - KRITIS (CRITICAL) risk with score < 90 → PARAH congestion
        - KRITIS (CRITICAL) risk with score >= 90 → TIDAK_DAPAT_DILALUI
        
        Args:
            road_id: ID of the road
            flood_risk: Flood risk prediction
            
        Returns:
            CongestionLevel enum value
            
        Requirements: 2.2
        """
        # Get road details
        road = self.db_session.query(Road).filter(Road.id == road_id).first()
        
        if road is None:
            logger.warning(f"Road {road_id} not found, defaulting to SEDANG")
            return CongestionLevel.SEDANG
        
        # Estimate congestion based on flood risk
        if flood_risk.category == RiskCategory.TINGGI:
            level = CongestionLevel.SEDANG
        elif flood_risk.category == RiskCategory.KRITIS:
            # For critical risk, severity depends on exact score
            if flood_risk.risk_score >= 90:
                level = CongestionLevel.TIDAK_DAPAT_DILALUI
            else:
                level = CongestionLevel.PARAH
        else:
            # For RENDAH or SEDANG risk, no significant congestion
            level = CongestionLevel.SEDANG
        
        logger.debug(f"Road {road_id} ({road.road_name}): "
                    f"flood_risk={flood_risk.risk_score:.1f}, "
                    f"congestion={level.value}")
        
        return level

    def check_region_isolation(
        self,
        region_id: int,
        congestion_levels: Optional[Dict[int, CongestionLevel]] = None
    ) -> bool:
        """
        Check if a region is isolated (all main roads impassable).
        
        A region is considered isolated if ALL main roads (is_main_road=True)
        are impassable (congestion level = TIDAK_DAPAT_DILALUI).
        
        Args:
            region_id: ID of the region to check
            congestion_levels: Optional dict of road_id to congestion level.
                             If not provided, will query current state.
            
        Returns:
            True if region is isolated, False otherwise
            
        Requirements: 2.4
        """
        # Get all main roads in the region
        main_roads = self.db_session.query(Road).filter(
            Road.region_id == region_id,
            Road.is_main_road == True
        ).all()
        
        if not main_roads:
            logger.debug(f"Region {region_id} has no main roads, not isolated")
            return False
        
        logger.debug(f"Region {region_id} has {len(main_roads)} main roads")
        
        # Check if all main roads are impassable
        if congestion_levels is None:
            # If no congestion data provided, region is not isolated
            return False
        
        impassable_count = 0
        for road in main_roads:
            level = congestion_levels.get(road.id)
            if level == CongestionLevel.TIDAK_DAPAT_DILALUI:
                impassable_count += 1
        
        is_isolated = (impassable_count == len(main_roads) and len(main_roads) > 0)
        
        logger.info(
            f"Region {region_id} isolation check: "
            f"{impassable_count}/{len(main_roads)} main roads impassable, "
            f"isolated={is_isolated}"
        )
        
        return is_isolated
