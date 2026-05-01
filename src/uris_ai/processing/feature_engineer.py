"""
Feature_Engineer component for ML feature engineering.

Creates features for machine learning models including rolling averages,
lag features, and temporal feature extraction.
Requirements: 1.2
"""

from typing import List, Optional, Dict, Any
import pandas as pd
import numpy as np
from dataclasses import dataclass
from datetime import datetime


@dataclass
class FeatureEngineeringResult:
    """Result of feature engineering operation."""
    features: pd.DataFrame
    feature_names: List[str]
    original_columns: List[str]
    new_columns: List[str]
    rows_processed: int


class FeatureEngineer:
    """
    Feature engineering component for URIS-AI ML models.
    
    Provides functionality for:
    - Rolling averages and statistics
    - Lag features for time-series
    - Temporal feature extraction (hour, day, month, etc.)
    - Interaction features
    
    Requirements: 1.2
    """

    def __init__(self):
        """Initialize FeatureEngineer."""
        pass

    def create_rolling_features(
        self,
        data: pd.DataFrame,
        columns: List[str],
        windows: List[int],
        functions: Optional[List[str]] = None,
        min_periods: Optional[int] = None,
    ) -> FeatureEngineeringResult:
        """
        Create rolling window features.
        
        Args:
            data: Input DataFrame (should be sorted by time)
            columns: Columns to create rolling features for
            windows: List of window sizes (e.g., [3, 7, 14] for 3-day, 7-day, 14-day)
            functions: List of aggregation functions ('mean', 'std', 'min', 'max', 'sum')
                      Default: ['mean']
            min_periods: Minimum number of observations required (default: window size)
            
        Returns:
            FeatureEngineeringResult with rolling features
        """
        if functions is None:
            functions = ['mean']

        features = data.copy()
        original_columns = features.columns.tolist()
        new_columns = []

        for col in columns:
            if col not in features.columns:
                continue

            for window in windows:
                for func in functions:
                    feature_name = f"{col}_rolling_{window}_{func}"
                    
                    if func == 'mean':
                        features[feature_name] = features[col].rolling(
                            window=window, min_periods=min_periods or window
                        ).mean()
                    elif func == 'std':
                        features[feature_name] = features[col].rolling(
                            window=window, min_periods=min_periods or window
                        ).std()
                    elif func == 'min':
                        features[feature_name] = features[col].rolling(
                            window=window, min_periods=min_periods or window
                        ).min()
                    elif func == 'max':
                        features[feature_name] = features[col].rolling(
                            window=window, min_periods=min_periods or window
                        ).max()
                    elif func == 'sum':
                        features[feature_name] = features[col].rolling(
                            window=window, min_periods=min_periods or window
                        ).sum()
                    
                    new_columns.append(feature_name)

        return FeatureEngineeringResult(
            features=features,
            feature_names=features.columns.tolist(),
            original_columns=original_columns,
            new_columns=new_columns,
            rows_processed=len(features),
        )

    def create_lag_features(
        self,
        data: pd.DataFrame,
        columns: List[str],
        lags: List[int],
        group_by: Optional[str] = None,
    ) -> FeatureEngineeringResult:
        """
        Create lag features for time-series data.
        
        Args:
            data: Input DataFrame (should be sorted by time)
            columns: Columns to create lag features for
            lags: List of lag periods (e.g., [1, 2, 7] for 1-day, 2-day, 7-day lags)
            group_by: Column to group by (e.g., 'region_id') for per-group lags
            
        Returns:
            FeatureEngineeringResult with lag features
        """
        features = data.copy()
        original_columns = features.columns.tolist()
        new_columns = []

        for col in columns:
            if col not in features.columns:
                continue

            for lag in lags:
                feature_name = f"{col}_lag_{lag}"
                
                if group_by and group_by in features.columns:
                    # Create lag within each group
                    features[feature_name] = features.groupby(group_by)[col].shift(lag)
                else:
                    # Create lag across entire dataset
                    features[feature_name] = features[col].shift(lag)
                
                new_columns.append(feature_name)

        return FeatureEngineeringResult(
            features=features,
            feature_names=features.columns.tolist(),
            original_columns=original_columns,
            new_columns=new_columns,
            rows_processed=len(features),
        )

    def create_temporal_features(
        self,
        data: pd.DataFrame,
        date_column: str = "date",
        features: Optional[List[str]] = None,
    ) -> FeatureEngineeringResult:
        """
        Extract temporal features from datetime column.
        
        Args:
            data: Input DataFrame
            date_column: Name of the datetime column
            features: List of features to extract. Options:
                     'hour', 'day', 'day_of_week', 'day_of_year',
                     'week', 'month', 'quarter', 'year',
                     'is_weekend', 'is_month_start', 'is_month_end'
                     Default: ['hour', 'day', 'month', 'day_of_week']
            
        Returns:
            FeatureEngineeringResult with temporal features
        """
        if features is None:
            features = ['hour', 'day', 'month', 'day_of_week']

        result = data.copy()
        original_columns = result.columns.tolist()
        new_columns = []

        if date_column not in result.columns:
            return FeatureEngineeringResult(
                features=result,
                feature_names=result.columns.tolist(),
                original_columns=original_columns,
                new_columns=[],
                rows_processed=len(result),
            )

        # Ensure datetime type
        result[date_column] = pd.to_datetime(result[date_column])
        dt = result[date_column].dt

        # Extract requested features
        if 'hour' in features:
            result['hour'] = dt.hour
            new_columns.append('hour')
        
        if 'day' in features:
            result['day'] = dt.day
            new_columns.append('day')
        
        if 'day_of_week' in features:
            result['day_of_week'] = dt.dayofweek
            new_columns.append('day_of_week')
        
        if 'day_of_year' in features:
            result['day_of_year'] = dt.dayofyear
            new_columns.append('day_of_year')
        
        if 'week' in features:
            result['week'] = dt.isocalendar().week
            new_columns.append('week')
        
        if 'month' in features:
            result['month'] = dt.month
            new_columns.append('month')
        
        if 'quarter' in features:
            result['quarter'] = dt.quarter
            new_columns.append('quarter')
        
        if 'year' in features:
            result['year'] = dt.year
            new_columns.append('year')
        
        if 'is_weekend' in features:
            result['is_weekend'] = (dt.dayofweek >= 5).astype(int)
            new_columns.append('is_weekend')
        
        if 'is_month_start' in features:
            result['is_month_start'] = dt.is_month_start.astype(int)
            new_columns.append('is_month_start')
        
        if 'is_month_end' in features:
            result['is_month_end'] = dt.is_month_end.astype(int)
            new_columns.append('is_month_end')

        return FeatureEngineeringResult(
            features=result,
            feature_names=result.columns.tolist(),
            original_columns=original_columns,
            new_columns=new_columns,
            rows_processed=len(result),
        )

    def create_interaction_features(
        self,
        data: pd.DataFrame,
        column_pairs: List[tuple],
        operations: Optional[List[str]] = None,
    ) -> FeatureEngineeringResult:
        """
        Create interaction features between column pairs.
        
        Args:
            data: Input DataFrame
            column_pairs: List of column pairs to create interactions for
                         e.g., [('rainfall', 'humidity'), ('temperature', 'wind_speed')]
            operations: List of operations ('multiply', 'add', 'subtract', 'divide', 'ratio')
                       Default: ['multiply']
            
        Returns:
            FeatureEngineeringResult with interaction features
        """
        if operations is None:
            operations = ['multiply']

        features = data.copy()
        original_columns = features.columns.tolist()
        new_columns = []

        for col1, col2 in column_pairs:
            if col1 not in features.columns or col2 not in features.columns:
                continue

            for op in operations:
                if op == 'multiply':
                    feature_name = f"{col1}_x_{col2}"
                    features[feature_name] = features[col1] * features[col2]
                    new_columns.append(feature_name)
                    
                elif op == 'add':
                    feature_name = f"{col1}_plus_{col2}"
                    features[feature_name] = features[col1] + features[col2]
                    new_columns.append(feature_name)
                    
                elif op == 'subtract':
                    feature_name = f"{col1}_minus_{col2}"
                    features[feature_name] = features[col1] - features[col2]
                    new_columns.append(feature_name)
                    
                elif op == 'divide':
                    feature_name = f"{col1}_div_{col2}"
                    # Avoid division by zero
                    features[feature_name] = features[col1] / features[col2].replace(0, np.nan)
                    new_columns.append(feature_name)
                    
                elif op == 'ratio':
                    feature_name = f"{col1}_ratio_{col2}"
                    # Ratio with safe division
                    total = features[col1] + features[col2]
                    features[feature_name] = features[col1] / total.replace(0, np.nan)
                    new_columns.append(feature_name)

        return FeatureEngineeringResult(
            features=features,
            feature_names=features.columns.tolist(),
            original_columns=original_columns,
            new_columns=new_columns,
            rows_processed=len(features),
        )

    def create_aggregated_features(
        self,
        data: pd.DataFrame,
        group_by: str,
        columns: List[str],
        functions: Optional[List[str]] = None,
    ) -> FeatureEngineeringResult:
        """
        Create aggregated features by group.
        
        Args:
            data: Input DataFrame
            group_by: Column to group by (e.g., 'region_id')
            columns: Columns to aggregate
            functions: List of aggregation functions ('mean', 'std', 'min', 'max', 'count')
                      Default: ['mean', 'std']
            
        Returns:
            FeatureEngineeringResult with aggregated features
        """
        if functions is None:
            functions = ['mean', 'std']

        features = data.copy()
        original_columns = features.columns.tolist()
        new_columns = []

        if group_by not in features.columns:
            return FeatureEngineeringResult(
                features=features,
                feature_names=features.columns.tolist(),
                original_columns=original_columns,
                new_columns=[],
                rows_processed=len(features),
            )

        for col in columns:
            if col not in features.columns:
                continue

            for func in functions:
                feature_name = f"{col}_{group_by}_{func}"
                
                if func == 'mean':
                    agg_values = features.groupby(group_by)[col].transform('mean')
                elif func == 'std':
                    agg_values = features.groupby(group_by)[col].transform('std')
                elif func == 'min':
                    agg_values = features.groupby(group_by)[col].transform('min')
                elif func == 'max':
                    agg_values = features.groupby(group_by)[col].transform('max')
                elif func == 'count':
                    agg_values = features.groupby(group_by)[col].transform('count')
                else:
                    continue
                
                features[feature_name] = agg_values
                new_columns.append(feature_name)

        return FeatureEngineeringResult(
            features=features,
            feature_names=features.columns.tolist(),
            original_columns=original_columns,
            new_columns=new_columns,
            rows_processed=len(features),
        )

    def create_cumulative_features(
        self,
        data: pd.DataFrame,
        columns: List[str],
        group_by: Optional[str] = None,
    ) -> FeatureEngineeringResult:
        """
        Create cumulative sum features.
        
        Args:
            data: Input DataFrame (should be sorted by time)
            columns: Columns to create cumulative features for
            group_by: Column to group by for per-group cumulative sums
            
        Returns:
            FeatureEngineeringResult with cumulative features
        """
        features = data.copy()
        original_columns = features.columns.tolist()
        new_columns = []

        for col in columns:
            if col not in features.columns:
                continue

            feature_name = f"{col}_cumsum"
            
            if group_by and group_by in features.columns:
                features[feature_name] = features.groupby(group_by)[col].cumsum()
            else:
                features[feature_name] = features[col].cumsum()
            
            new_columns.append(feature_name)

        return FeatureEngineeringResult(
            features=features,
            feature_names=features.columns.tolist(),
            original_columns=original_columns,
            new_columns=new_columns,
            rows_processed=len(features),
        )
