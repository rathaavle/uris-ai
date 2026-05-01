"""
Risk Scoring Engine for URIS-AI.

This module implements the Risk_Scoring_Engine class that calculates
Urban Risk Score (URS) by integrating flood risk, traffic impact,
and service accessibility scores.

Requirements: 4.1, 4.2, 4.4
"""

from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Dict, List, Optional

from sqlalchemy.orm import Session

from uris_ai.models.database import RiskScore


@dataclass
class RiskScorePoint:
    """
    Data structure for a single risk score point in time series.
    
    Attributes:
        region_id: ID of the region
        date: Timestamp of the risk score
        urban_risk_score: The calculated URS value (0-100)
        timestamp: When this record was created
    """
    region_id: int
    date: datetime
    urban_risk_score: float
    timestamp: datetime


class RiskScoringEngine:
    """
    Engine for calculating Urban Risk Score (URS).
    
    The URS is a weighted combination of:
    - Flood risk score (0-100)
    - Traffic impact score (0-100)
    - Service accessibility score (0-100)
    
    Default weights: flood=0.5, traffic=0.3, service=0.2
    
    Requirements: 4.1, 4.2, 4.4
    """
    
    # Default weights for URS calculation
    DEFAULT_WEIGHTS = {
        'flood': 0.5,
        'traffic': 0.3,
        'service': 0.2
    }
    
    def __init__(self, db_session: Optional[Session] = None):
        """
        Initialize the Risk Scoring Engine.
        
        Args:
            db_session: SQLAlchemy database session for persistence operations
        """
        self.db_session = db_session
    
    def calculate_urban_risk_score(
        self,
        flood_risk: float,
        traffic_impact: float,
        service_accessibility: float,
        weights: Optional[Dict[str, float]] = None
    ) -> float:
        """
        Calculate Urban Risk Score from component scores.
        
        Formula: URS = (w_flood × flood_risk) + (w_traffic × traffic_impact) + 
                       (w_service × service_accessibility)
        
        Args:
            flood_risk: Flood risk score (0-100)
            traffic_impact: Traffic impact score (0-100)
            service_accessibility: Service accessibility score (0-100)
            weights: Optional custom weights dict with keys 'flood', 'traffic', 'service'
                    If None, uses DEFAULT_WEIGHTS
        
        Returns:
            Urban Risk Score (0-100)
        
        Raises:
            ValueError: If input scores are out of range [0, 100]
            ValueError: If weights don't sum to 1.0 (within tolerance)
        
        Requirements: 4.1
        """
        # Validate input scores
        if not (0 <= flood_risk <= 100):
            raise ValueError(f"flood_risk must be in [0, 100], got {flood_risk}")
        if not (0 <= traffic_impact <= 100):
            raise ValueError(f"traffic_impact must be in [0, 100], got {traffic_impact}")
        if not (0 <= service_accessibility <= 100):
            raise ValueError(
                f"service_accessibility must be in [0, 100], got {service_accessibility}"
            )
        
        # Use default weights if not provided
        if weights is None:
            weights = self.DEFAULT_WEIGHTS.copy()
        
        # Validate weights
        w_flood = weights.get('flood', 0.0)
        w_traffic = weights.get('traffic', 0.0)
        w_service = weights.get('service', 0.0)
        
        weight_sum = w_flood + w_traffic + w_service
        if abs(weight_sum - 1.0) > 0.001:  # Tolerance for floating point
            raise ValueError(
                f"Weights must sum to 1.0, got {weight_sum} "
                f"(flood={w_flood}, traffic={w_traffic}, service={w_service})"
            )
        
        # Calculate weighted sum
        urs = (
            w_flood * flood_risk +
            w_traffic * traffic_impact +
            w_service * service_accessibility
        )
        
        # Ensure result is in valid range (handle floating point edge cases)
        urs = max(0.0, min(100.0, urs))
        
        return urs
    
    def batch_calculate(self, regions: List[int]) -> Dict[int, float]:
        """
        Calculate URS for multiple regions.
        
        Retrieves the latest risk component scores from the database
        and calculates URS for each region.
        
        Args:
            regions: List of region IDs to calculate URS for
        
        Returns:
            Dictionary mapping region_id to urban_risk_score
        
        Raises:
            RuntimeError: If db_session is not configured
            ValueError: If no risk data found for a region
        
        Requirements: 4.2
        """
        if self.db_session is None:
            raise RuntimeError(
                "Database session required for batch_calculate. "
                "Initialize RiskScoringEngine with db_session."
            )
        
        results = {}
        
        for region_id in regions:
            # Get the latest risk score record for this region
            latest_score = (
                self.db_session.query(RiskScore)
                .filter(RiskScore.region_id == region_id)
                .order_by(RiskScore.date.desc())
                .first()
            )
            
            if latest_score is None:
                raise ValueError(
                    f"No risk data found for region {region_id}. "
                    "Ensure risk components are calculated first."
                )
            
            # Calculate URS using the stored component scores
            urs = self.calculate_urban_risk_score(
                flood_risk=latest_score.flood_risk,
                traffic_impact=latest_score.traffic_impact,
                service_accessibility=latest_score.service_access
            )
            
            results[region_id] = urs
        
        return results
    
    def get_risk_trend(
        self,
        region_id: int,
        hours: int = 24
    ) -> List[RiskScorePoint]:
        """
        Get historical risk score trend for a region.
        
        Retrieves risk scores from the past N hours for trend analysis.
        
        Args:
            region_id: ID of the region
            hours: Number of hours to look back (default: 24)
        
        Returns:
            List of RiskScorePoint objects, ordered by date (oldest first)
        
        Raises:
            RuntimeError: If db_session is not configured
            ValueError: If hours is negative
        
        Requirements: 4.4
        """
        if self.db_session is None:
            raise RuntimeError(
                "Database session required for get_risk_trend. "
                "Initialize RiskScoringEngine with db_session."
            )
        
        if hours < 0:
            raise ValueError(f"hours must be non-negative, got {hours}")
        
        # Calculate cutoff time
        cutoff_time = datetime.utcnow() - timedelta(hours=hours)
        
        # Query risk scores within the time window
        risk_scores = (
            self.db_session.query(RiskScore)
            .filter(
                RiskScore.region_id == region_id,
                RiskScore.date >= cutoff_time
            )
            .order_by(RiskScore.date.asc())
            .all()
        )
        
        # Convert to RiskScorePoint objects
        trend = [
            RiskScorePoint(
                region_id=score.region_id,
                date=score.date,
                urban_risk_score=score.urban_risk_score,
                timestamp=score.created_at
            )
            for score in risk_scores
        ]
        
        return trend
    
    def save_risk_history(
        self,
        region_id: int,
        score: float,
        flood_risk: float,
        traffic_impact: float,
        service_access: float,
        date: Optional[datetime] = None
    ) -> None:
        """
        Save risk score to database for historical tracking.
        
        Args:
            region_id: ID of the region
            score: Urban Risk Score to save (0-100)
            flood_risk: Flood risk component score (0-100)
            traffic_impact: Traffic impact component score (0-100)
            service_access: Service accessibility component score (0-100)
            date: Timestamp for the score (default: current time)
        
        Raises:
            RuntimeError: If db_session is not configured
            ValueError: If scores are out of valid range
        
        Requirements: 4.4
        """
        if self.db_session is None:
            raise RuntimeError(
                "Database session required for save_risk_history. "
                "Initialize RiskScoringEngine with db_session."
            )
        
        # Validate scores
        if not (0 <= score <= 100):
            raise ValueError(f"score must be in [0, 100], got {score}")
        if not (0 <= flood_risk <= 100):
            raise ValueError(f"flood_risk must be in [0, 100], got {flood_risk}")
        if not (0 <= traffic_impact <= 100):
            raise ValueError(f"traffic_impact must be in [0, 100], got {traffic_impact}")
        if not (0 <= service_access <= 100):
            raise ValueError(f"service_access must be in [0, 100], got {service_access}")
        
        # Use current time if not provided
        if date is None:
            date = datetime.utcnow()
        
        # Create new risk score record
        risk_score = RiskScore(
            region_id=region_id,
            date=date,
            flood_risk=flood_risk,
            traffic_impact=traffic_impact,
            service_access=service_access,
            urban_risk_score=score,
            created_at=datetime.utcnow()
        )
        
        # Save to database
        self.db_session.add(risk_score)
        self.db_session.commit()
