"""
Unit tests for Risk Scoring Engine.

This module contains unit tests for the Risk_Scoring_Engine class,
covering URS calculation, batch calculation, and risk history persistence.

Requirements: 4.1, 4.2, 4.4
"""

from datetime import datetime, timedelta
from unittest.mock import Mock

import pytest
from sqlalchemy.orm import Session

from src.uris_ai.ml.risk_scoring_engine import (
    RiskScoringEngine,
    RiskScorePoint
)
from uris_ai.models.database import RiskScore, Region


class TestRiskScoringEngineBasic:
    """Basic unit tests for Risk Scoring Engine."""

    def test_calculate_urban_risk_score_default_weights(self):
        """
        Test URS calculation with default weights.
        
        Requirements: 4.1
        """
        engine = RiskScoringEngine()
        
        # Test with typical values
        urs = engine.calculate_urban_risk_score(
            flood_risk=60.0,
            traffic_impact=40.0,
            service_accessibility=30.0
        )
        
        # Expected: 0.5*60 + 0.3*40 + 0.2*30 = 30 + 12 + 6 = 48
        expected = 48.0
        assert abs(urs - expected) < 0.01
        assert 0 <= urs <= 100

    def test_calculate_urban_risk_score_custom_weights(self):
        """
        Test URS calculation with custom weights.
        
        Requirements: 4.1
        """
        engine = RiskScoringEngine()
        
        # Custom weights: equal weighting
        custom_weights = {
            'flood': 1/3,
            'traffic': 1/3,
            'service': 1/3
        }
        
        urs = engine.calculate_urban_risk_score(
            flood_risk=60.0,
            traffic_impact=30.0,
            service_accessibility=90.0,
            weights=custom_weights
        )
        
        # Expected: (60 + 30 + 90) / 3 = 60
        expected = 60.0
        assert abs(urs - expected) < 0.01

    def test_calculate_urban_risk_score_boundary_values(self):
        """
        Test URS calculation with boundary values.
        
        Requirements: 4.1
        """
        engine = RiskScoringEngine()
        
        # All zeros
        urs_min = engine.calculate_urban_risk_score(
            flood_risk=0.0,
            traffic_impact=0.0,
            service_accessibility=0.0
        )
        assert urs_min == 0.0
        
        # All 100s
        urs_max = engine.calculate_urban_risk_score(
            flood_risk=100.0,
            traffic_impact=100.0,
            service_accessibility=100.0
        )
        assert abs(urs_max - 100.0) < 0.01

    def test_calculate_urban_risk_score_invalid_flood_risk(self):
        """
        Test that invalid flood_risk values are rejected.
        
        Requirements: 4.1
        """
        engine = RiskScoringEngine()
        
        # Negative value
        with pytest.raises(ValueError, match="flood_risk must be in"):
            engine.calculate_urban_risk_score(
                flood_risk=-10.0,
                traffic_impact=50.0,
                service_accessibility=50.0
            )
        
        # Value > 100
        with pytest.raises(ValueError, match="flood_risk must be in"):
            engine.calculate_urban_risk_score(
                flood_risk=150.0,
                traffic_impact=50.0,
                service_accessibility=50.0
            )

    def test_calculate_urban_risk_score_invalid_traffic_impact(self):
        """
        Test that invalid traffic_impact values are rejected.
        
        Requirements: 4.1
        """
        engine = RiskScoringEngine()
        
        with pytest.raises(ValueError, match="traffic_impact must be in"):
            engine.calculate_urban_risk_score(
                flood_risk=50.0,
                traffic_impact=-5.0,
                service_accessibility=50.0
            )

    def test_calculate_urban_risk_score_invalid_service_accessibility(self):
        """
        Test that invalid service_accessibility values are rejected.
        
        Requirements: 4.1
        """
        engine = RiskScoringEngine()
        
        with pytest.raises(ValueError, match="service_accessibility must be in"):
            engine.calculate_urban_risk_score(
                flood_risk=50.0,
                traffic_impact=50.0,
                service_accessibility=120.0
            )

    def test_calculate_urban_risk_score_invalid_weights_sum(self):
        """
        Test that weights not summing to 1.0 are rejected.
        
        Requirements: 4.1
        """
        engine = RiskScoringEngine()
        
        # Weights sum to 1.5
        with pytest.raises(ValueError, match="Weights must sum to 1.0"):
            engine.calculate_urban_risk_score(
                flood_risk=50.0,
                traffic_impact=50.0,
                service_accessibility=50.0,
                weights={'flood': 0.5, 'traffic': 0.5, 'service': 0.5}
            )

    def test_calculate_urban_risk_score_various_combinations(self):
        """
        Test URS calculation with various input combinations.
        
        Requirements: 4.1
        """
        engine = RiskScoringEngine()
        
        # High flood, low traffic, medium service
        urs1 = engine.calculate_urban_risk_score(
            flood_risk=90.0,
            traffic_impact=20.0,
            service_accessibility=50.0
        )
        # Expected: 0.5*90 + 0.3*20 + 0.2*50 = 45 + 6 + 10 = 61
        assert abs(urs1 - 61.0) < 0.01
        
        # Low flood, high traffic, low service
        urs2 = engine.calculate_urban_risk_score(
            flood_risk=10.0,
            traffic_impact=80.0,
            service_accessibility=15.0
        )
        # Expected: 0.5*10 + 0.3*80 + 0.2*15 = 5 + 24 + 3 = 32
        assert abs(urs2 - 32.0) < 0.01


class TestRiskScoringEngineBatchCalculation:
    """Unit tests for batch calculation functionality."""

    def test_batch_calculate_single_region(self, db_session: Session):
        """
        Test batch calculation for a single region.
        
        Requirements: 4.2
        """
        # Create test region
        region = Region(
            region_id=1,
            name="Test Region",
            latitude=-6.2,
            longitude=106.8,
            elevation=10.0
        )
        db_session.add(region)
        
        # Create risk score record
        risk_score = RiskScore(
            region_id=1,
            date=datetime.utcnow(),
            flood_risk=70.0,
            traffic_impact=50.0,
            service_access=30.0,
            urban_risk_score=0.0  # Will be recalculated
        )
        db_session.add(risk_score)
        db_session.commit()
        
        # Create engine with db_session
        engine = RiskScoringEngine(db_session=db_session)
        
        # Batch calculate
        results = engine.batch_calculate([1])
        
        # Verify results
        assert 1 in results
        expected_urs = 0.5 * 70.0 + 0.3 * 50.0 + 0.2 * 30.0  # 35 + 15 + 6 = 56
        assert abs(results[1] - expected_urs) < 0.01

    def test_batch_calculate_multiple_regions(self, db_session: Session):
        """
        Test batch calculation for multiple regions.
        
        Requirements: 4.2
        """
        # Create test regions
        for i in range(1, 4):
            region = Region(
                region_id=i,
                name=f"Region {i}",
                latitude=-6.2,
                longitude=106.8,
                elevation=10.0
            )
            db_session.add(region)
            
            # Create risk score with different values
            risk_score = RiskScore(
                region_id=i,
                date=datetime.utcnow(),
                flood_risk=float(i * 20),
                traffic_impact=float(i * 15),
                service_access=float(i * 10),
                urban_risk_score=0.0
            )
            db_session.add(risk_score)
        
        db_session.commit()
        
        # Create engine
        engine = RiskScoringEngine(db_session=db_session)
        
        # Batch calculate
        results = engine.batch_calculate([1, 2, 3])
        
        # Verify all regions processed
        assert len(results) == 3
        assert all(region_id in results for region_id in [1, 2, 3])
        
        # Verify each result is in valid range
        for urs in results.values():
            assert 0 <= urs <= 100

    def test_batch_calculate_no_data_raises_error(self, db_session: Session):
        """
        Test that batch_calculate raises error when no data exists.
        
        Requirements: 4.2
        """
        engine = RiskScoringEngine(db_session=db_session)
        
        with pytest.raises(ValueError, match="No risk data found"):
            engine.batch_calculate([999])

    def test_batch_calculate_without_db_session_raises_error(self):
        """
        Test that batch_calculate requires db_session.
        
        Requirements: 4.2
        """
        engine = RiskScoringEngine()  # No db_session
        
        with pytest.raises(RuntimeError, match="Database session required"):
            engine.batch_calculate([1])

    def test_batch_calculate_uses_latest_data(self, db_session: Session):
        """
        Test that batch_calculate uses the most recent risk score.
        
        Requirements: 4.2
        """
        # Create test region
        region = Region(
            region_id=1,
            name="Test Region",
            latitude=-6.2,
            longitude=106.8
        )
        db_session.add(region)
        
        # Create older risk score
        old_score = RiskScore(
            region_id=1,
            date=datetime.utcnow() - timedelta(hours=2),
            flood_risk=30.0,
            traffic_impact=30.0,
            service_access=30.0,
            urban_risk_score=30.0
        )
        db_session.add(old_score)
        
        # Create newer risk score
        new_score = RiskScore(
            region_id=1,
            date=datetime.utcnow(),
            flood_risk=80.0,
            traffic_impact=60.0,
            service_access=40.0,
            urban_risk_score=0.0
        )
        db_session.add(new_score)
        db_session.commit()
        
        # Create engine
        engine = RiskScoringEngine(db_session=db_session)
        
        # Batch calculate
        results = engine.batch_calculate([1])
        
        # Should use new_score values
        expected_urs = 0.5 * 80.0 + 0.3 * 60.0 + 0.2 * 40.0  # 40 + 18 + 8 = 66
        assert abs(results[1] - expected_urs) < 0.01


class TestRiskScoringEngineRiskTrend:
    """Unit tests for risk trend functionality."""

    def test_get_risk_trend_24_hours(self, db_session: Session):
        """
        Test getting risk trend for 24 hours.
        
        Requirements: 4.4
        """
        # Create test region
        region = Region(
            region_id=1,
            name="Test Region",
            latitude=-6.2,
            longitude=106.8
        )
        db_session.add(region)
        
        # Create risk scores over 24 hours
        now = datetime.utcnow()
        for i in range(24):
            score = RiskScore(
                region_id=1,
                date=now - timedelta(hours=23-i),
                flood_risk=float(50 + i),
                traffic_impact=50.0,
                service_access=50.0,
                urban_risk_score=float(50 + i * 0.5)
            )
            db_session.add(score)
        
        db_session.commit()
        
        # Create engine
        engine = RiskScoringEngine(db_session=db_session)
        
        # Get trend
        trend = engine.get_risk_trend(region_id=1, hours=24)
        
        # Verify
        assert len(trend) == 24
        assert all(isinstance(point, RiskScorePoint) for point in trend)
        assert all(point.region_id == 1 for point in trend)
        
        # Verify ordered by date (oldest first)
        dates = [point.date for point in trend]
        assert dates == sorted(dates)

    def test_get_risk_trend_custom_hours(self, db_session: Session):
        """
        Test getting risk trend for custom time window.
        
        Requirements: 4.4
        """
        # Create test region
        region = Region(
            region_id=1,
            name="Test Region",
            latitude=-6.2,
            longitude=106.8
        )
        db_session.add(region)
        
        # Create risk scores over 48 hours
        now = datetime.utcnow()
        for i in range(48):
            score = RiskScore(
                region_id=1,
                date=now - timedelta(hours=47-i),
                flood_risk=50.0,
                traffic_impact=50.0,
                service_access=50.0,
                urban_risk_score=50.0
            )
            db_session.add(score)
        
        db_session.commit()
        
        # Create engine
        engine = RiskScoringEngine(db_session=db_session)
        
        # Get trend for last 12 hours
        trend = engine.get_risk_trend(region_id=1, hours=12)
        
        # Should return approximately 12 records (within time window)
        assert len(trend) <= 13  # Allow for timing variations
        assert len(trend) >= 11

    def test_get_risk_trend_no_data(self, db_session: Session):
        """
        Test getting risk trend when no data exists.
        
        Requirements: 4.4
        """
        engine = RiskScoringEngine(db_session=db_session)
        
        # Get trend for non-existent region
        trend = engine.get_risk_trend(region_id=999, hours=24)
        
        # Should return empty list
        assert trend == []

    def test_get_risk_trend_without_db_session_raises_error(self):
        """
        Test that get_risk_trend requires db_session.
        
        Requirements: 4.4
        """
        engine = RiskScoringEngine()  # No db_session
        
        with pytest.raises(RuntimeError, match="Database session required"):
            engine.get_risk_trend(region_id=1, hours=24)

    def test_get_risk_trend_negative_hours_raises_error(self, db_session: Session):
        """
        Test that negative hours value is rejected.
        
        Requirements: 4.4
        """
        engine = RiskScoringEngine(db_session=db_session)
        
        with pytest.raises(ValueError, match="hours must be non-negative"):
            engine.get_risk_trend(region_id=1, hours=-5)


class TestRiskScoringEngineRiskHistory:
    """Unit tests for risk history persistence."""

    def test_save_risk_history_basic(self, db_session: Session):
        """
        Test saving risk history to database.
        
        Requirements: 4.4
        """
        # Create test region
        region = Region(
            region_id=1,
            name="Test Region",
            latitude=-6.2,
            longitude=106.8
        )
        db_session.add(region)
        db_session.commit()
        
        # Create engine
        engine = RiskScoringEngine(db_session=db_session)
        
        # Save risk history
        engine.save_risk_history(
            region_id=1,
            score=65.0,
            flood_risk=70.0,
            traffic_impact=60.0,
            service_access=50.0
        )
        
        # Verify saved
        saved = db_session.query(RiskScore).filter_by(region_id=1).first()
        assert saved is not None
        assert saved.urban_risk_score == 65.0
        assert saved.flood_risk == 70.0
        assert saved.traffic_impact == 60.0
        assert saved.service_access == 50.0

    def test_save_risk_history_with_custom_date(self, db_session: Session):
        """
        Test saving risk history with custom date.
        
        Requirements: 4.4
        """
        # Create test region
        region = Region(
            region_id=1,
            name="Test Region",
            latitude=-6.2,
            longitude=106.8
        )
        db_session.add(region)
        db_session.commit()
        
        # Create engine
        engine = RiskScoringEngine(db_session=db_session)
        
        # Custom date
        custom_date = datetime(2024, 1, 15, 10, 30, 0)
        
        # Save risk history
        engine.save_risk_history(
            region_id=1,
            score=55.0,
            flood_risk=60.0,
            traffic_impact=50.0,
            service_access=40.0,
            date=custom_date
        )
        
        # Verify saved with custom date
        saved = db_session.query(RiskScore).filter_by(region_id=1).first()
        assert saved is not None
        assert saved.date == custom_date

    def test_save_risk_history_multiple_records(self, db_session: Session):
        """
        Test saving multiple risk history records.
        
        Requirements: 4.4
        """
        # Create test region
        region = Region(
            region_id=1,
            name="Test Region",
            latitude=-6.2,
            longitude=106.8
        )
        db_session.add(region)
        db_session.commit()
        
        # Create engine
        engine = RiskScoringEngine(db_session=db_session)
        
        # Save multiple records
        for i in range(5):
            engine.save_risk_history(
                region_id=1,
                score=float(50 + i * 10),
                flood_risk=float(50 + i * 10),
                traffic_impact=50.0,
                service_access=50.0,
                date=datetime.utcnow() - timedelta(hours=4-i)
            )
        
        # Verify all saved
        saved_records = db_session.query(RiskScore).filter_by(region_id=1).all()
        assert len(saved_records) == 5

    def test_save_risk_history_invalid_score_raises_error(self, db_session: Session):
        """
        Test that invalid score values are rejected.
        
        Requirements: 4.4
        """
        engine = RiskScoringEngine(db_session=db_session)
        
        # Negative score
        with pytest.raises(ValueError, match="score must be in"):
            engine.save_risk_history(
                region_id=1,
                score=-10.0,
                flood_risk=50.0,
                traffic_impact=50.0,
                service_access=50.0
            )
        
        # Score > 100
        with pytest.raises(ValueError, match="score must be in"):
            engine.save_risk_history(
                region_id=1,
                score=150.0,
                flood_risk=50.0,
                traffic_impact=50.0,
                service_access=50.0
            )

    def test_save_risk_history_without_db_session_raises_error(self):
        """
        Test that save_risk_history requires db_session.
        
        Requirements: 4.4
        """
        engine = RiskScoringEngine()  # No db_session
        
        with pytest.raises(RuntimeError, match="Database session required"):
            engine.save_risk_history(
                region_id=1,
                score=50.0,
                flood_risk=50.0,
                traffic_impact=50.0,
                service_access=50.0
            )


class TestRiskScoringEngineIntegration:
    """Integration tests combining multiple features."""

    def test_calculate_and_save_workflow(self, db_session: Session):
        """
        Test complete workflow: calculate URS and save to history.
        
        Requirements: 4.1, 4.4
        """
        # Create test region
        region = Region(
            region_id=1,
            name="Test Region",
            latitude=-6.2,
            longitude=106.8
        )
        db_session.add(region)
        db_session.commit()
        
        # Create engine
        engine = RiskScoringEngine(db_session=db_session)
        
        # Calculate URS
        urs = engine.calculate_urban_risk_score(
            flood_risk=75.0,
            traffic_impact=55.0,
            service_accessibility=45.0
        )
        
        # Save to history
        engine.save_risk_history(
            region_id=1,
            score=urs,
            flood_risk=75.0,
            traffic_impact=55.0,
            service_access=45.0
        )
        
        # Verify saved correctly
        saved = db_session.query(RiskScore).filter_by(region_id=1).first()
        assert saved is not None
        assert abs(saved.urban_risk_score - urs) < 0.01

    def test_batch_calculate_and_retrieve_trend(self, db_session: Session):
        """
        Test workflow: batch calculate and retrieve trend.
        
        Requirements: 4.2, 4.4
        """
        # Create test regions
        for i in range(1, 3):
            region = Region(
                region_id=i,
                name=f"Region {i}",
                latitude=-6.2,
                longitude=106.8
            )
            db_session.add(region)
            
            # Create historical data
            for j in range(5):
                score = RiskScore(
                    region_id=i,
                    date=datetime.utcnow() - timedelta(hours=4-j),
                    flood_risk=float(50 + j * 5),
                    traffic_impact=50.0,
                    service_access=50.0,
                    urban_risk_score=float(50 + j * 2)
                )
                db_session.add(score)
        
        db_session.commit()
        
        # Create engine
        engine = RiskScoringEngine(db_session=db_session)
        
        # Batch calculate
        results = engine.batch_calculate([1, 2])
        assert len(results) == 2
        
        # Get trend for region 1
        trend = engine.get_risk_trend(region_id=1, hours=5)
        assert len(trend) == 5
        assert all(point.region_id == 1 for point in trend)
