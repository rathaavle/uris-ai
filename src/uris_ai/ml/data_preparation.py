"""
Data preparation module for ML model training.

This module handles loading, preprocessing, and splitting data for training
the flood risk prediction model.

Requirements: 1.2, 1.5
"""

from dataclasses import dataclass
from typing import Tuple, Optional, List
import logging

import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sqlalchemy.orm import Session

from ..models.database import Region, WeatherData as DBWeatherData, FloodEvent

# Configure logging
logger = logging.getLogger(__name__)


@dataclass
class TrainingData:
    """Container for training data splits."""
    X_train: np.ndarray
    X_val: np.ndarray
    X_test: np.ndarray
    y_train: np.ndarray
    y_val: np.ndarray
    y_test: np.ndarray
    scaler: StandardScaler
    feature_names: List[str]


class DataPreparation:
    """
    Data preparation for flood risk model training.
    
    This class handles:
    - Loading data from database
    - Feature engineering
    - Data preprocessing
    - Train/validation/test split
    
    Requirements: 1.2, 1.5
    """

    def __init__(self, db_session: Session):
        """
        Initialize data preparation.
        
        Args:
            db_session: SQLAlchemy database session
        """
        self.db_session = db_session
        self.feature_names = [
            'rainfall', 'humidity', 'temperature', 'wind_speed',
            'flood_frequency', 'avg_severity', 'max_water_level',
            'avg_duration_hours', 'elevation', 'drainage_capacity'
        ]

    def load_and_prepare_data(
        self,
        test_size: float = 0.2,
        val_size: float = 0.1,
        random_state: int = 42
    ) -> TrainingData:
        """
        Load data from database and prepare for training.
        
        This method:
        1. Loads weather, flood, and region data from database
        2. Combines data and engineers features
        3. Splits into train/validation/test sets
        4. Normalizes features
        
        Args:
            test_size: Proportion of data for test set (default: 0.2)
            val_size: Proportion of training data for validation (default: 0.1)
            random_state: Random seed for reproducibility
            
        Returns:
            TrainingData with train/val/test splits and scaler
            
        Requirements: 1.2, 1.5
        """
        logger.info("Loading data from database...")
        
        # Load data
        df = self._load_data_from_db()
        
        if df.empty:
            raise ValueError("No data loaded from database")
        
        logger.info(f"Loaded {len(df)} records")
        
        # Engineer features
        df = self._engineer_features(df)
        
        # Prepare features and target
        X, y = self._prepare_features_and_target(df)
        
        # Split data
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=test_size, random_state=random_state
        )
        
        X_train, X_val, y_train, y_val = train_test_split(
            X_train, y_train, test_size=val_size, random_state=random_state
        )
        
        logger.info(
            f"Data split: train={len(X_train)}, val={len(X_val)}, test={len(X_test)}"
        )
        
        # Normalize features
        scaler = StandardScaler()
        X_train = scaler.fit_transform(X_train)
        X_val = scaler.transform(X_val)
        X_test = scaler.transform(X_test)
        
        return TrainingData(
            X_train=X_train,
            X_val=X_val,
            X_test=X_test,
            y_train=y_train,
            y_val=y_val,
            y_test=y_test,
            scaler=scaler,
            feature_names=self.feature_names
        )

    def _load_data_from_db(self) -> pd.DataFrame:
        """
        Load data from database and combine into a single DataFrame.
        
        Returns:
            DataFrame with combined weather, flood, and region data
        """
        # Query weather data with region information
        query = """
        SELECT 
            w.region_id,
            w.date,
            w.rainfall,
            w.humidity,
            w.temperature,
            w.wind_speed,
            r.elevation,
            r.drainage_capacity
        FROM weather_data w
        JOIN regions r ON w.region_id = r.region_id
        ORDER BY w.region_id, w.date
        """
        
        weather_df = pd.read_sql(query, self.db_session.bind)
        
        # Query flood events
        flood_query = """
        SELECT 
            region_id,
            date,
            severity,
            water_level,
            duration_hours
        FROM flood_events
        ORDER BY region_id, date
        """
        
        flood_df = pd.read_sql(flood_query, self.db_session.bind)
        
        # Combine data
        # For each weather record, we need to determine if a flood occurred
        # within a reasonable time window (e.g., 24 hours)
        
        combined_data = []
        
        for _, weather_row in weather_df.iterrows():
            region_id = weather_row['region_id']
            weather_date = pd.to_datetime(weather_row['date'])
            
            # Find floods in this region within 24 hours after this weather reading
            region_floods = flood_df[flood_df['region_id'] == region_id].copy()
            region_floods['date'] = pd.to_datetime(region_floods['date'])
            
            # Check if flood occurred within 24 hours
            time_diff = (region_floods['date'] - weather_date).dt.total_seconds() / 3600
            recent_floods = region_floods[(time_diff >= 0) & (time_diff <= 24)]
            
            # Calculate target (risk score based on flood occurrence)
            if len(recent_floods) > 0:
                # Flood occurred - calculate risk score based on severity
                max_severity = recent_floods['severity'].max()
                risk_score = self._severity_to_risk_score(max_severity)
            else:
                # No flood - low risk score
                risk_score = np.random.uniform(0, 25)  # Random low score
            
            # Add row to combined data
            row = weather_row.to_dict()
            row['risk_score'] = risk_score
            combined_data.append(row)
        
        df = pd.DataFrame(combined_data)
        
        return df

    def _engineer_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Engineer features from raw data.
        
        This includes:
        - Historical flood statistics per region
        - Rolling averages
        - Lag features
        
        Args:
            df: Raw data DataFrame
            
        Returns:
            DataFrame with engineered features
        """
        # Calculate historical flood statistics per region
        flood_stats = self._calculate_flood_statistics()
        
        # Merge flood statistics
        df = df.merge(flood_stats, on='region_id', how='left')
        
        # Fill missing values
        df['wind_speed'] = df['wind_speed'].fillna(0)
        df['flood_frequency'] = df['flood_frequency'].fillna(0)
        df['avg_severity'] = df['avg_severity'].fillna(1)
        df['max_water_level'] = df['max_water_level'].fillna(0)
        df['avg_duration_hours'] = df['avg_duration_hours'].fillna(0)
        df['elevation'] = df['elevation'].fillna(0)
        df['drainage_capacity'] = df['drainage_capacity'].fillna(100)
        
        return df

    def _calculate_flood_statistics(self) -> pd.DataFrame:
        """
        Calculate historical flood statistics per region.
        
        Returns:
            DataFrame with flood statistics per region
        """
        query = """
        SELECT 
            region_id,
            COUNT(*) as flood_frequency,
            AVG(severity) as avg_severity,
            MAX(water_level) as max_water_level,
            AVG(duration_hours) as avg_duration_hours
        FROM flood_events
        GROUP BY region_id
        """
        
        stats_df = pd.read_sql(query, self.db_session.bind)
        
        return stats_df

    def _prepare_features_and_target(
        self,
        df: pd.DataFrame
    ) -> Tuple[np.ndarray, np.ndarray]:
        """
        Prepare feature matrix and target vector.
        
        Args:
            df: DataFrame with all features and target
            
        Returns:
            Tuple of (X, y) where X is feature matrix and y is target vector
        """
        # Select features
        X = df[self.feature_names].values
        
        # Target is risk_score
        y = df['risk_score'].values
        
        return X, y

    def _severity_to_risk_score(self, severity: int) -> float:
        """
        Convert flood severity to risk score.
        
        Severity mapping:
        1 (Rendah) -> 20-40
        2 (Sedang) -> 40-60
        3 (Tinggi) -> 60-80
        4 (Kritis) -> 80-100
        
        Args:
            severity: Flood severity (1-4)
            
        Returns:
            Risk score (0-100)
        """
        severity_ranges = {
            1: (20, 40),
            2: (40, 60),
            3: (60, 80),
            4: (80, 100)
        }
        
        min_score, max_score = severity_ranges.get(severity, (0, 25))
        return np.random.uniform(min_score, max_score)


def create_synthetic_training_data(
    n_samples: int = 1000,
    random_state: int = 42
) -> TrainingData:
    """
    Create synthetic training data for testing and development.
    
    This function generates synthetic data when real data is not available.
    
    Args:
        n_samples: Number of samples to generate
        random_state: Random seed for reproducibility
        
    Returns:
        TrainingData with synthetic train/val/test splits
    """
    np.random.seed(random_state)
    
    # Generate features
    rainfall = np.random.uniform(0, 500, n_samples)
    humidity = np.random.uniform(40, 100, n_samples)
    temperature = np.random.uniform(20, 35, n_samples)
    wind_speed = np.random.uniform(0, 50, n_samples)
    flood_frequency = np.random.randint(0, 20, n_samples)
    avg_severity = np.random.uniform(1, 4, n_samples)
    max_water_level = np.random.uniform(0, 200, n_samples)
    avg_duration_hours = np.random.uniform(0, 48, n_samples)
    elevation = np.random.uniform(-5, 100, n_samples)
    drainage_capacity = np.random.uniform(50, 500, n_samples)
    
    # Generate target with some correlation to features
    risk_score = (
        rainfall * 0.15 +
        humidity * 0.1 +
        flood_frequency * 2.0 +
        avg_severity * 5.0 +
        max_water_level * 0.1 -
        elevation * 0.2 -
        drainage_capacity * 0.05 +
        np.random.normal(0, 10, n_samples)
    )
    
    # Clamp to [0, 100]
    risk_score = np.clip(risk_score, 0, 100)
    
    # Combine features
    X = np.column_stack([
        rainfall, humidity, temperature, wind_speed,
        flood_frequency, avg_severity, max_water_level,
        avg_duration_hours, elevation, drainage_capacity
    ])
    
    # Split data
    X_train, X_test, y_train, y_test = train_test_split(
        X, risk_score, test_size=0.2, random_state=random_state
    )
    
    X_train, X_val, y_train, y_val = train_test_split(
        X_train, y_train, test_size=0.1, random_state=random_state
    )
    
    # Normalize
    scaler = StandardScaler()
    X_train = scaler.fit_transform(X_train)
    X_val = scaler.transform(X_val)
    X_test = scaler.transform(X_test)
    
    feature_names = [
        'rainfall', 'humidity', 'temperature', 'wind_speed',
        'flood_frequency', 'avg_severity', 'max_water_level',
        'avg_duration_hours', 'elevation', 'drainage_capacity'
    ]
    
    logger.info(f"Created synthetic training data: {n_samples} samples")
    
    return TrainingData(
        X_train=X_train,
        X_val=X_val,
        X_test=X_test,
        y_train=y_train,
        y_val=y_val,
        y_test=y_test,
        scaler=scaler,
        feature_names=feature_names
    )
