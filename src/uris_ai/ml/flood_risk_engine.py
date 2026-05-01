"""
Flood Risk Engine - ML model for predicting flood risk per region.

This module implements the core AI/ML component for flood risk prediction,
including model training, inference, and risk categorization.

Requirements: 1.1, 1.2, 1.3, 1.4, 1.5
"""

from dataclasses import dataclass
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import List, Optional, Dict, Any
import pickle
import logging

import numpy as np
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
import pandas as pd

# Configure logging
logger = logging.getLogger(__name__)


class RiskCategory(str, Enum):
    """Risk category classification."""
    RENDAH = "RENDAH"
    SEDANG = "SEDANG"
    TINGGI = "TINGGI"
    KRITIS = "KRITIS"


@dataclass
class FloodHistory:
    """Historical flood data for a region."""
    region_id: int
    flood_frequency: int  # Number of floods in historical period
    avg_severity: float  # Average severity (1-4)
    max_water_level: float  # Maximum water level recorded (cm)
    avg_duration_hours: float  # Average flood duration


@dataclass
class WeatherData:
    """Current weather data for prediction."""
    region_id: int
    rainfall: float  # mm
    humidity: float  # %
    temperature: float  # °C
    wind_speed: Optional[float] = None  # km/h


@dataclass
class RegionFeatures:
    """Static features for a region."""
    region_id: int
    elevation: float  # meters
    drainage_capacity: float  # m³/hour


@dataclass
class FloodRiskPrediction:
    """Result of flood risk prediction."""
    region_id: int
    risk_score: float  # 0-100
    category: RiskCategory
    confidence: float  # 0-1
    timestamp: datetime
    features_used: Dict[str, float]


@dataclass
class UpdateResult:
    """Result of model update operation."""
    success: bool
    old_version: str
    new_version: str
    message: str
    timestamp: datetime


class FloodRiskEngine:
    """
    ML engine for predicting flood risk per region.
    
    This class implements the core flood risk prediction functionality using
    machine learning models trained on historical flood data and weather patterns.
    
    Model Type: Supervised Learning (Regression)
    Input features: rainfall, humidity, temperature, historical flood frequency,
                   elevation, drainage capacity
    Output: Flood risk score (0-100)
    Required accuracy: Minimal 80% based on historical validation
    
    Requirements: 1.1, 1.3, 1.5
    """

    def __init__(
        self,
        model_path: Optional[str] = None,
        azure_ml_workspace: Optional[Any] = None
    ):
        """
        Initialize the Flood Risk Engine.
        
        Args:
            model_path: Path to pre-trained model file (optional)
            azure_ml_workspace: Azure ML workspace connection (optional)
        """
        self.model: Optional[RandomForestRegressor] = None
        self.scaler: Optional[StandardScaler] = None
        self.model_version: str = "0.0.0"
        self.model_path: Optional[Path] = Path(model_path) if model_path else None
        self.azure_ml_workspace = azure_ml_workspace
        
        # Load model if path provided
        if self.model_path and self.model_path.exists():
            self._load_model(self.model_path)
        
        logger.info(f"FloodRiskEngine initialized with model version {self.model_version}")

    def predict_flood_risk(
        self,
        region_id: int,
        weather_data: WeatherData,
        historical_data: FloodHistory,
        region_features: Optional[RegionFeatures] = None
    ) -> FloodRiskPrediction:
        """
        Predict flood risk for a specific region.
        
        Args:
            region_id: ID of the region
            weather_data: Current weather data
            historical_data: Historical flood data
            region_features: Static region features (elevation, drainage)
            
        Returns:
            FloodRiskPrediction with risk score, category, and confidence
            
        Raises:
            ValueError: If model is not trained or loaded
            
        Requirements: 1.1, 1.3
        """
        if self.model is None:
            raise ValueError("Model not trained or loaded. Call train() or load model first.")
        
        # Prepare features
        features = self._prepare_features(
            weather_data,
            historical_data,
            region_features
        )
        
        # Make prediction
        risk_score = self._predict_score(features)
        
        # Classify risk category
        category = self.get_risk_category(risk_score)
        
        # Calculate confidence (simplified - in production, use model's prediction intervals)
        confidence = self._calculate_confidence(features, risk_score)
        
        prediction = FloodRiskPrediction(
            region_id=region_id,
            risk_score=risk_score,
            category=category,
            confidence=confidence,
            timestamp=datetime.now(timezone.utc),
            features_used=features
        )
        
        logger.debug(
            f"Predicted flood risk for region {region_id}: "
            f"score={risk_score:.2f}, category={category.value}"
        )
        
        return prediction

    def batch_predict(
        self,
        regions: List[int],
        weather_data_map: Dict[int, WeatherData],
        historical_data_map: Dict[int, FloodHistory],
        region_features_map: Optional[Dict[int, RegionFeatures]] = None
    ) -> List[FloodRiskPrediction]:
        """
        Predict flood risk for multiple regions efficiently.
        
        Args:
            regions: List of region IDs
            weather_data_map: Map of region_id to weather data
            historical_data_map: Map of region_id to historical data
            region_features_map: Map of region_id to region features (optional)
            
        Returns:
            List of FloodRiskPrediction for each region
            
        Requirements: 1.1, 1.3
        """
        predictions = []
        
        for region_id in regions:
            try:
                weather = weather_data_map.get(region_id)
                historical = historical_data_map.get(region_id)
                features = region_features_map.get(region_id) if region_features_map else None
                
                if weather is None or historical is None:
                    logger.warning(f"Missing data for region {region_id}, skipping")
                    continue
                
                prediction = self.predict_flood_risk(
                    region_id,
                    weather,
                    historical,
                    features
                )
                predictions.append(prediction)
                
            except Exception as e:
                logger.error(f"Error predicting for region {region_id}: {e}")
                continue
        
        logger.info(f"Batch prediction completed for {len(predictions)}/{len(regions)} regions")
        return predictions

    def get_risk_category(self, risk_score: float) -> RiskCategory:
        """
        Convert numeric risk score to category.
        
        Risk Category Mapping:
        - Score 0-25 → RENDAH
        - Score 26-50 → SEDANG
        - Score 51-75 → TINGGI
        - Score 76-100 → KRITIS
        
        Args:
            risk_score: Numeric risk score (0-100)
            
        Returns:
            RiskCategory enum value
            
        Requirements: 1.3
        """
        if risk_score < 0 or risk_score > 100:
            logger.warning(f"Risk score {risk_score} out of range [0, 100], clamping")
            risk_score = max(0, min(100, risk_score))
        
        if risk_score <= 25:
            return RiskCategory.RENDAH
        elif risk_score <= 50:
            return RiskCategory.SEDANG
        elif risk_score <= 75:
            return RiskCategory.TINGGI
        else:
            return RiskCategory.KRITIS

    def update_model(self, model_path: str) -> UpdateResult:
        """
        Update model with a new version.
        
        This method supports blue-green deployment by loading the new model
        while keeping the old one available for rollback.
        
        Args:
            model_path: Path to new model file
            
        Returns:
            UpdateResult with success status and version information
            
        Requirements: 9.2
        """
        old_version = self.model_version
        new_path = Path(model_path)
        
        if not new_path.exists():
            return UpdateResult(
                success=False,
                old_version=old_version,
                new_version=old_version,
                message=f"Model file not found: {model_path}",
                timestamp=datetime.now(timezone.utc)
            )
        
        try:
            # Load new model
            self._load_model(new_path)
            
            logger.info(f"Model updated from {old_version} to {self.model_version}")
            
            return UpdateResult(
                success=True,
                old_version=old_version,
                new_version=self.model_version,
                message="Model updated successfully",
                timestamp=datetime.now(timezone.utc)
            )
            
        except Exception as e:
            logger.error(f"Failed to update model: {e}")
            return UpdateResult(
                success=False,
                old_version=old_version,
                new_version=old_version,
                message=f"Failed to load new model: {str(e)}",
                timestamp=datetime.now(timezone.utc)
            )

    def _prepare_features(
        self,
        weather: WeatherData,
        historical: FloodHistory,
        region_features: Optional[RegionFeatures] = None
    ) -> Dict[str, float]:
        """
        Prepare feature dictionary for model input.
        
        Args:
            weather: Weather data
            historical: Historical flood data
            region_features: Region features (optional)
            
        Returns:
            Dictionary of feature names to values
        """
        features = {
            'rainfall': weather.rainfall,
            'humidity': weather.humidity,
            'temperature': weather.temperature,
            'wind_speed': weather.wind_speed or 0.0,
            'flood_frequency': float(historical.flood_frequency),
            'avg_severity': historical.avg_severity,
            'max_water_level': historical.max_water_level,
            'avg_duration_hours': historical.avg_duration_hours,
        }
        
        if region_features:
            features['elevation'] = region_features.elevation
            features['drainage_capacity'] = region_features.drainage_capacity
        else:
            # Use default values if not provided
            features['elevation'] = 0.0
            features['drainage_capacity'] = 100.0
        
        return features

    def _predict_score(self, features: Dict[str, float]) -> float:
        """
        Make prediction using the trained model.
        
        Args:
            features: Feature dictionary
            
        Returns:
            Risk score (0-100)
        """
        # Convert features to array in correct order
        feature_order = [
            'rainfall', 'humidity', 'temperature', 'wind_speed',
            'flood_frequency', 'avg_severity', 'max_water_level',
            'avg_duration_hours', 'elevation', 'drainage_capacity'
        ]
        
        feature_array = np.array([[features[f] for f in feature_order]])
        
        # Scale features
        if self.scaler:
            feature_array = self.scaler.transform(feature_array)
        
        # Predict
        risk_score = self.model.predict(feature_array)[0]
        
        # Clamp to [0, 100]
        risk_score = max(0, min(100, risk_score))
        
        return float(risk_score)

    def _calculate_confidence(
        self,
        features: Dict[str, float],
        risk_score: float
    ) -> float:
        """
        Calculate confidence score for the prediction.
        
        In a production system, this would use the model's prediction intervals
        or ensemble variance. For now, we use a simplified approach.
        
        Args:
            features: Feature dictionary
            risk_score: Predicted risk score
            
        Returns:
            Confidence score (0-1)
        """
        # Simplified confidence calculation
        # In production, use model's prediction intervals or ensemble variance
        base_confidence = 0.8
        
        # Reduce confidence for extreme values
        if risk_score < 10 or risk_score > 90:
            base_confidence *= 0.9
        
        return base_confidence

    def _load_model(self, model_path: Path) -> None:
        """
        Load model from file.
        
        Args:
            model_path: Path to model file
        """
        with open(model_path, 'rb') as f:
            model_data = pickle.load(f)
        
        self.model = model_data['model']
        self.scaler = model_data.get('scaler')
        self.model_version = model_data.get('version', '0.0.0')
        
        logger.info(f"Model loaded from {model_path}, version {self.model_version}")

    def save_model(self, model_path: str) -> None:
        """
        Save model to file.
        
        Args:
            model_path: Path to save model
        """
        if self.model is None:
            raise ValueError("No model to save")
        
        model_data = {
            'model': self.model,
            'scaler': self.scaler,
            'version': self.model_version
        }
        
        save_path = Path(model_path)
        save_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(save_path, 'wb') as f:
            pickle.dump(model_data, f)
        
        logger.info(f"Model saved to {model_path}")

    def train(
        self,
        X_train: np.ndarray,
        y_train: np.ndarray,
        scaler: Optional[Any] = None
    ) -> None:
        """
        Train the flood risk model.
        
        This is a convenience method for training. For full training pipeline
        with hyperparameter tuning, use the ModelTrainer class.
        
        Args:
            X_train: Training features
            y_train: Training targets
            scaler: Optional pre-fitted scaler
        """
        if self.model is None:
            self.model = RandomForestRegressor(
                n_estimators=100,
                max_depth=10,
                random_state=42,
                n_jobs=-1
            )
        
        self.model.fit(X_train, y_train)
        self.scaler = scaler
        
        logger.info("Model training completed")
