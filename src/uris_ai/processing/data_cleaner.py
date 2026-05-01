"""
Data_Cleaner component for data cleaning operations.

Handles missing values, outlier detection, and data quality improvements.
Requirements: 7.1
"""

from typing import Dict, List, Optional, Tuple, Any
import pandas as pd
import numpy as np
from dataclasses import dataclass
from enum import Enum


class ImputationStrategy(str, Enum):
    """Strategy for handling missing values."""
    MEAN = "mean"
    MEDIAN = "median"
    MODE = "mode"
    FORWARD_FILL = "ffill"
    BACKWARD_FILL = "bfill"
    DROP = "drop"
    CONSTANT = "constant"


class OutlierMethod(str, Enum):
    """Method for outlier detection."""
    IQR = "iqr"  # Interquartile Range
    Z_SCORE = "z_score"  # Standard deviation based
    ISOLATION_FOREST = "isolation_forest"  # ML-based


@dataclass
class CleaningResult:
    """Result of data cleaning operation."""
    cleaned_data: pd.DataFrame
    missing_values_handled: int
    outliers_removed: int
    rows_before: int
    rows_after: int
    columns_cleaned: List[str]
    cleaning_report: Dict[str, Any]


class DataCleaner:
    """
    Data cleaning component for URIS-AI.
    
    Provides functionality for:
    - Handling missing values with various strategies
    - Outlier detection and removal
    - Data quality validation
    
    Requirements: 7.1
    """

    def __init__(
        self,
        missing_value_strategy: ImputationStrategy = ImputationStrategy.MEDIAN,
        outlier_method: OutlierMethod = OutlierMethod.IQR,
        outlier_threshold: float = 1.5,
    ):
        """
        Initialize DataCleaner.
        
        Args:
            missing_value_strategy: Strategy for handling missing values
            outlier_method: Method for outlier detection
            outlier_threshold: Threshold for outlier detection
                - For IQR: multiplier for IQR (default 1.5)
                - For Z_SCORE: number of standard deviations (default 3.0)
        """
        self.missing_value_strategy = missing_value_strategy
        self.outlier_method = outlier_method
        self.outlier_threshold = outlier_threshold

    def clean(
        self,
        data: pd.DataFrame,
        columns_to_clean: Optional[List[str]] = None,
        handle_missing: bool = True,
        remove_outliers: bool = True,
    ) -> CleaningResult:
        """
        Clean data by handling missing values and removing outliers.
        
        Args:
            data: Input DataFrame to clean
            columns_to_clean: Specific columns to clean (None = all numeric columns)
            handle_missing: Whether to handle missing values
            remove_outliers: Whether to remove outliers
            
        Returns:
            CleaningResult with cleaned data and statistics
        """
        if data.empty:
            return CleaningResult(
                cleaned_data=data.copy(),
                missing_values_handled=0,
                outliers_removed=0,
                rows_before=0,
                rows_after=0,
                columns_cleaned=[],
                cleaning_report={},
            )

        rows_before = len(data)
        cleaned_data = data.copy()
        
        # Determine columns to clean
        if columns_to_clean is None:
            columns_to_clean = cleaned_data.select_dtypes(include=[np.number]).columns.tolist()
        
        missing_count = 0
        outlier_count = 0
        report = {}

        # Handle missing values
        if handle_missing:
            missing_count, cleaned_data = self._handle_missing_values(
                cleaned_data, columns_to_clean
            )
            report["missing_values"] = missing_count

        # Remove outliers
        if remove_outliers:
            outlier_count, cleaned_data = self._remove_outliers(
                cleaned_data, columns_to_clean
            )
            report["outliers_removed"] = outlier_count

        rows_after = len(cleaned_data)

        return CleaningResult(
            cleaned_data=cleaned_data,
            missing_values_handled=missing_count,
            outliers_removed=outlier_count,
            rows_before=rows_before,
            rows_after=rows_after,
            columns_cleaned=columns_to_clean,
            cleaning_report=report,
        )

    def _handle_missing_values(
        self, data: pd.DataFrame, columns: List[str]
    ) -> Tuple[int, pd.DataFrame]:
        """
        Handle missing values in specified columns.
        
        Args:
            data: DataFrame with missing values
            columns: Columns to process
            
        Returns:
            Tuple of (count of missing values handled, cleaned DataFrame)
        """
        missing_count = data[columns].isnull().sum().sum()
        
        if missing_count == 0:
            return 0, data

        cleaned = data.copy()

        if self.missing_value_strategy == ImputationStrategy.MEAN:
            for col in columns:
                if cleaned[col].isnull().any():
                    cleaned[col] = cleaned[col].fillna(cleaned[col].mean())
                    
        elif self.missing_value_strategy == ImputationStrategy.MEDIAN:
            for col in columns:
                if cleaned[col].isnull().any():
                    cleaned[col] = cleaned[col].fillna(cleaned[col].median())
                    
        elif self.missing_value_strategy == ImputationStrategy.MODE:
            for col in columns:
                if cleaned[col].isnull().any():
                    mode_val = cleaned[col].mode()
                    if len(mode_val) > 0:
                        cleaned[col] = cleaned[col].fillna(mode_val[0])
                        
        elif self.missing_value_strategy == ImputationStrategy.FORWARD_FILL:
            cleaned[columns] = cleaned[columns].fillna(method='ffill')
            
        elif self.missing_value_strategy == ImputationStrategy.BACKWARD_FILL:
            cleaned[columns] = cleaned[columns].fillna(method='bfill')
            
        elif self.missing_value_strategy == ImputationStrategy.DROP:
            cleaned = cleaned.dropna(subset=columns)

        return missing_count, cleaned

    def _remove_outliers(
        self, data: pd.DataFrame, columns: List[str]
    ) -> Tuple[int, pd.DataFrame]:
        """
        Remove outliers from specified columns.
        
        Args:
            data: DataFrame with potential outliers
            columns: Columns to check for outliers
            
        Returns:
            Tuple of (count of outliers removed, cleaned DataFrame)
        """
        if data.empty:
            return 0, data

        cleaned = data.copy()
        initial_rows = len(cleaned)

        if self.outlier_method == OutlierMethod.IQR:
            cleaned = self._remove_outliers_iqr(cleaned, columns)
            
        elif self.outlier_method == OutlierMethod.Z_SCORE:
            cleaned = self._remove_outliers_zscore(cleaned, columns)
            
        elif self.outlier_method == OutlierMethod.ISOLATION_FOREST:
            cleaned = self._remove_outliers_isolation_forest(cleaned, columns)

        outliers_removed = initial_rows - len(cleaned)
        return outliers_removed, cleaned

    def _remove_outliers_iqr(
        self, data: pd.DataFrame, columns: List[str]
    ) -> pd.DataFrame:
        """
        Remove outliers using Interquartile Range (IQR) method.
        
        Args:
            data: Input DataFrame
            columns: Columns to check
            
        Returns:
            DataFrame with outliers removed
        """
        cleaned = data.copy()
        
        for col in columns:
            if col not in cleaned.columns:
                continue
                
            Q1 = cleaned[col].quantile(0.25)
            Q3 = cleaned[col].quantile(0.75)
            IQR = Q3 - Q1
            
            lower_bound = Q1 - self.outlier_threshold * IQR
            upper_bound = Q3 + self.outlier_threshold * IQR
            
            # Filter out outliers
            cleaned = cleaned[
                (cleaned[col] >= lower_bound) & (cleaned[col] <= upper_bound)
            ]
        
        return cleaned

    def _remove_outliers_zscore(
        self, data: pd.DataFrame, columns: List[str]
    ) -> pd.DataFrame:
        """
        Remove outliers using Z-score method.
        
        Args:
            data: Input DataFrame
            columns: Columns to check
            
        Returns:
            DataFrame with outliers removed
        """
        cleaned = data.copy()
        mask = pd.Series([True] * len(cleaned), index=cleaned.index)
        
        for col in columns:
            if col not in cleaned.columns:
                continue
                
            mean = cleaned[col].mean()
            std = cleaned[col].std()
            
            if std == 0:
                continue
            
            z_scores = np.abs((cleaned[col] - mean) / std)
            mask = mask & (z_scores <= self.outlier_threshold)
        
        cleaned = cleaned[mask]
        return cleaned

    def _remove_outliers_isolation_forest(
        self, data: pd.DataFrame, columns: List[str]
    ) -> pd.DataFrame:
        """
        Remove outliers using Isolation Forest algorithm.
        
        Args:
            data: Input DataFrame
            columns: Columns to check
            
        Returns:
            DataFrame with outliers removed
        """
        from sklearn.ensemble import IsolationForest
        
        cleaned = data.copy()
        
        # Select only the columns to check
        X = cleaned[columns].values
        
        # Fit Isolation Forest
        iso_forest = IsolationForest(
            contamination=0.1,  # Assume 10% outliers
            random_state=42
        )
        predictions = iso_forest.fit_predict(X)
        
        # Keep only inliers (prediction == 1)
        cleaned = cleaned[predictions == 1]
        
        return cleaned

    def get_missing_value_summary(self, data: pd.DataFrame) -> pd.DataFrame:
        """
        Get summary of missing values in DataFrame.
        
        Args:
            data: Input DataFrame
            
        Returns:
            DataFrame with missing value statistics per column
        """
        missing_count = data.isnull().sum()
        missing_percent = (missing_count / len(data)) * 100
        
        summary = pd.DataFrame({
            'column': missing_count.index,
            'missing_count': missing_count.values,
            'missing_percent': missing_percent.values
        })
        
        return summary[summary['missing_count'] > 0].sort_values(
            'missing_count', ascending=False
        )

    def detect_outliers(
        self, data: pd.DataFrame, columns: Optional[List[str]] = None
    ) -> Dict[str, List[int]]:
        """
        Detect outliers without removing them.
        
        Args:
            data: Input DataFrame
            columns: Columns to check (None = all numeric columns)
            
        Returns:
            Dictionary mapping column names to lists of outlier indices
        """
        if columns is None:
            columns = data.select_dtypes(include=[np.number]).columns.tolist()
        
        outliers = {}
        
        for col in columns:
            if col not in data.columns:
                continue
            
            if self.outlier_method == OutlierMethod.IQR:
                Q1 = data[col].quantile(0.25)
                Q3 = data[col].quantile(0.75)
                IQR = Q3 - Q1
                
                lower_bound = Q1 - self.outlier_threshold * IQR
                upper_bound = Q3 + self.outlier_threshold * IQR
                
                outlier_mask = (data[col] < lower_bound) | (data[col] > upper_bound)
                outliers[col] = data[outlier_mask].index.tolist()
                
            elif self.outlier_method == OutlierMethod.Z_SCORE:
                mean = data[col].mean()
                std = data[col].std()
                
                if std > 0:
                    z_scores = np.abs((data[col] - mean) / std)
                    outlier_mask = z_scores > self.outlier_threshold
                    outliers[col] = data[outlier_mask].index.tolist()
        
        return {k: v for k, v in outliers.items() if len(v) > 0}
