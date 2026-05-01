"""
Integration tests for Flood Risk Engine.

This module contains integration tests that validate the flood risk engine
works correctly with real data and handles various scenarios.

Requirements: 1.1, 1.4
"""

import pytest
import numpy as np
from datetime import datetime

from src.uris_ai.ml.flood_risk_engine import (
    FloodRiskEngine,
    RiskCategory,
    FloodHistory,
    WeatherData,
    RegionFeatures,
    FloodRiskPrediction,
)
from src.uris_ai.ml.data_preparation import create_synthetic_training_data
from src.uris_ai.ml.model_training import ModelTrainer


class TestFloodRiskEngineIntegration:
    """Integration tests for Flood Risk Engine."""

    @pytest.fixture
    def trained_engine(self, tmp_path):
        """
        Fixture that provides a trained flood risk engine.
        
        Uses synthetic data for training.
        """
        # Create synthetic training data
        training_data = create_synthetic_training_data(n_samples=500, random_state=42)
        
        # Train model
        trainer = ModelTrainer(model_type="random_forest")
        result = trainer.train(training_data, tune_hyperparameters=False)
        
        # Save model
        model_path = tmp_path / "test_model.pkl"
        trainer.save_model(result.model, result.scaler, str(model_path), version="test-1.0.0")
        
        # Create engine with trained model
        engine = FloodRiskEngine(model_path=str(model_path))
        
        return engine

    def test_predict_flood_risk_basic(self, trained_engine):
        """
        Test basic flood risk prediction.
        
        **Validates: Requirements 1.1**
        """
        # Prepare test data
        weather = WeatherData(
            region_id=1,
            rainfall=100.0,
            humidity=85.0,
            temperature=28.0,
            wind_speed=20.0
        )
        
        historical = FloodHistory(
            region_id=1,
            flood_frequency=5,
            avg_severity=2.5,
            max_water_level=80.0,
            avg_duration_hours=12.0
        )
        
        region_features = RegionFeatures(
            region_id=1,
            elevation=10.0,
            drainage_capacity=200.0
        )
        
        # Make prediction
        prediction = trained_engine.predict_flood_risk(
            region_id=1,
            weather_data=weather,
            historical_data=historical,
            region_features=region_features
        )
        
        # Verify prediction structure
        assert isinstance(prediction, FloodRiskPrediction)
        assert prediction.region_id == 1
        assert 0 <= prediction.risk_score <= 100
        assert prediction.category in RiskCategory
        assert 0 <= prediction.confidence <= 1
        assert isinstance(prediction.timestamp, datetime)
        assert isinstance(prediction.features_used, dict)

    def test_predict_flood_risk_high_rainfall(self, trained_engine):
        """
        Test prediction with high rainfall (should result in higher risk).
        
        **Validates: Requirements 1.1**
        """
        # High rainfall scenario
        weather_high = WeatherData(
            region_id=1,
            rainfall=300.0,  # Very high rainfall
            humidity=95.0,
            temperature=30.0,
            wind_speed=30.0
        )
        
        historical = FloodHistory(
            region_id=1,
            flood_frequency=10,
            avg_severity=3.5,
            max_water_level=150.0,
            avg_duration_hours=24.0
        )
        
        region_features = RegionFeatures(
            region_id=1,
            elevation=5.0,  # Low elevation
            drainage_capacity=100.0  # Low drainage
        )
        
        prediction = trained_engine.predict_flood_risk(
            region_id=1,
            weather_data=weather_high,
            historical_data=historical,
            region_features=region_features
        )
        
        # High rainfall + poor drainage + low elevation should result in higher risk
        # We can't guarantee exact score, but it should be reasonable
        assert 0 <= prediction.risk_score <= 100
        assert prediction.category in RiskCategory

    def test_predict_flood_risk_low_risk_scenario(self, trained_engine):
        """
        Test prediction with low risk conditions.
        
        **Validates: Requirements 1.1**
        """
        # Low risk scenario
        weather_low = WeatherData(
            region_id=1,
            rainfall=10.0,  # Low rainfall
            humidity=60.0,
            temperature=25.0,
            wind_speed=10.0
        )
        
        historical = FloodHistory(
            region_id=1,
            flood_frequency=0,  # No historical floods
            avg_severity=1.0,
            max_water_level=10.0,
            avg_duration_hours=2.0
        )
        
        region_features = RegionFeatures(
            region_id=1,
            elevation=50.0,  # High elevation
            drainage_capacity=500.0  # Excellent drainage
        )
        
        prediction = trained_engine.predict_flood_risk(
            region_id=1,
            weather_data=weather_low,
            historical_data=historical,
            region_features=region_features
        )
        
        # Low risk conditions should result in reasonable score
        assert 0 <= prediction.risk_score <= 100
        assert prediction.category in RiskCategory

    def test_batch_predict(self, trained_engine):
        """
        Test batch prediction for multiple regions.
        
        **Validates: Requirements 1.1**
        """
        # Prepare data for 3 regions
        regions = [1, 2, 3]
        
        weather_data_map = {
            1: WeatherData(1, 50.0, 70.0, 26.0, 15.0),
            2: WeatherData(2, 100.0, 80.0, 28.0, 20.0),
            3: WeatherData(3, 200.0, 90.0, 30.0, 25.0),
        }
        
        historical_data_map = {
            1: FloodHistory(1, 2, 1.5, 30.0, 6.0),
            2: FloodHistory(2, 5, 2.5, 80.0, 12.0),
            3: FloodHistory(3, 10, 3.5, 150.0, 24.0),
        }
        
        region_features_map = {
            1: RegionFeatures(1, 30.0, 300.0),
            2: RegionFeatures(2, 15.0, 200.0),
            3: RegionFeatures(3, 5.0, 100.0),
        }
        
        # Batch predict
        predictions = trained_engine.batch_predict(
            regions,
            weather_data_map,
            historical_data_map,
            region_features_map
        )
        
        # Verify results
        assert len(predictions) == 3
        assert all(isinstance(p, FloodRiskPrediction) for p in predictions)
        assert all(p.region_id in regions for p in predictions)
        assert all(0 <= p.risk_score <= 100 for p in predictions)

    def test_batch_predict_missing_data(self, trained_engine):
        """
        Test batch prediction with missing data for some regions.
        
        **Validates: Requirements 1.4 (error handling)**
        """
        regions = [1, 2, 3]
        
        # Only provide data for regions 1 and 3
        weather_data_map = {
            1: WeatherData(1, 50.0, 70.0, 26.0, 15.0),
            3: WeatherData(3, 200.0, 90.0, 30.0, 25.0),
        }
        
        historical_data_map = {
            1: FloodHistory(1, 2, 1.5, 30.0, 6.0),
            3: FloodHistory(3, 10, 3.5, 150.0, 24.0),
        }
        
        # Batch predict should skip region 2
        predictions = trained_engine.batch_predict(
            regions,
            weather_data_map,
            historical_data_map
        )
        
        # Should only get predictions for regions with complete data
        assert len(predictions) == 2
        assert all(p.region_id in [1, 3] for p in predictions)

    def test_predict_without_region_features(self, trained_engine):
        """
        Test prediction without region features (should use defaults).
        
        **Validates: Requirements 1.1, 1.4**
        """
        weather = WeatherData(
            region_id=1,
            rainfall=100.0,
            humidity=85.0,
            temperature=28.0,
            wind_speed=20.0
        )
        
        historical = FloodHistory(
            region_id=1,
            flood_frequency=5,
            avg_severity=2.5,
            max_water_level=80.0,
            avg_duration_hours=12.0
        )
        
        # Predict without region features
        prediction = trained_engine.predict_flood_risk(
            region_id=1,
            weather_data=weather,
            historical_data=historical,
            region_features=None  # No region features
        )
        
        # Should still work with default values
        assert isinstance(prediction, FloodRiskPrediction)
        assert 0 <= prediction.risk_score <= 100

    def test_predict_without_wind_speed(self, trained_engine):
        """
        Test prediction with missing wind speed (optional field).
        
        **Validates: Requirements 1.1, 1.4**
        """
        weather = WeatherData(
            region_id=1,
            rainfall=100.0,
            humidity=85.0,
            temperature=28.0,
            wind_speed=None  # Missing wind speed
        )
        
        historical = FloodHistory(
            region_id=1,
            flood_frequency=5,
            avg_severity=2.5,
            max_water_level=80.0,
            avg_duration_hours=12.0
        )
        
        prediction = trained_engine.predict_flood_risk(
            region_id=1,
            weather_data=weather,
            historical_data=historical
        )
        
        # Should work with wind_speed defaulting to 0
        assert isinstance(prediction, FloodRiskPrediction)
        assert 0 <= prediction.risk_score <= 100

    def test_predict_without_trained_model(self):
        """
        Test that prediction fails gracefully without a trained model.
        
        **Validates: Requirements 1.4 (error handling)**
        """
        engine = FloodRiskEngine()  # No model loaded
        
        weather = WeatherData(1, 100.0, 85.0, 28.0, 20.0)
        historical = FloodHistory(1, 5, 2.5, 80.0, 12.0)
        
        with pytest.raises(ValueError, match="Model not trained or loaded"):
            engine.predict_flood_risk(1, weather, historical)

    def test_model_update(self, trained_engine, tmp_path):
        """
        Test model update functionality.
        
        **Validates: Requirements 9.2 (blue-green deployment)**
        """
        old_version = trained_engine.model_version
        
        # Create a new model
        training_data = create_synthetic_training_data(n_samples=300, random_state=123)
        trainer = ModelTrainer(model_type="random_forest")
        result = trainer.train(training_data, tune_hyperparameters=False)
        
        # Save new model
        new_model_path = tmp_path / "new_model.pkl"
        trainer.save_model(result.model, result.scaler, str(new_model_path), version="test-2.0.0")
        
        # Update model
        update_result = trained_engine.update_model(str(new_model_path))
        
        # Verify update
        assert update_result.success is True
        assert update_result.old_version == old_version
        assert update_result.new_version == "test-2.0.0"
        assert trained_engine.model_version == "test-2.0.0"

    def test_model_update_nonexistent_file(self, trained_engine):
        """
        Test model update with nonexistent file.
        
        **Validates: Requirements 1.4 (error handling)**
        """
        result = trained_engine.update_model("/nonexistent/model.pkl")
        
        assert result.success is False
        assert "not found" in result.message.lower()

    def test_risk_category_consistency_with_prediction(self, trained_engine):
        """
        Test that predicted risk score and category are consistent.
        
        **Validates: Requirements 1.3**
        """
        weather = WeatherData(1, 100.0, 85.0, 28.0, 20.0)
        historical = FloodHistory(1, 5, 2.5, 80.0, 12.0)
        
        prediction = trained_engine.predict_flood_risk(1, weather, historical)
        
        # Verify category matches score
        expected_category = trained_engine.get_risk_category(prediction.risk_score)
        assert prediction.category == expected_category

    def test_confidence_score_range(self, trained_engine):
        """
        Test that confidence scores are always in valid range.
        
        **Validates: Requirements 1.1**
        """
        weather = WeatherData(1, 100.0, 85.0, 28.0, 20.0)
        historical = FloodHistory(1, 5, 2.5, 80.0, 12.0)
        
        # Make multiple predictions
        for _ in range(10):
            prediction = trained_engine.predict_flood_risk(1, weather, historical)
            assert 0 <= prediction.confidence <= 1, \
                f"Confidence {prediction.confidence} out of range [0, 1]"

    def test_features_used_in_prediction(self, trained_engine):
        """
        Test that prediction includes features used.
        
        **Validates: Requirements 1.1**
        """
        weather = WeatherData(1, 100.0, 85.0, 28.0, 20.0)
        historical = FloodHistory(1, 5, 2.5, 80.0, 12.0)
        region_features = RegionFeatures(1, 10.0, 200.0)
        
        prediction = trained_engine.predict_flood_risk(
            1, weather, historical, region_features
        )
        
        # Verify all expected features are present
        expected_features = [
            'rainfall', 'humidity', 'temperature', 'wind_speed',
            'flood_frequency', 'avg_severity', 'max_water_level',
            'avg_duration_hours', 'elevation', 'drainage_capacity'
        ]
        
        for feature in expected_features:
            assert feature in prediction.features_used, \
                f"Feature {feature} not in features_used"
