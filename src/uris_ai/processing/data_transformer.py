"""
Data_Transformer component for data normalization and encoding.

Provides normalization (min-max, z-score) and categorical encoding
for machine learning pipelines.
Requirements: 1.2
"""

from typing import List, Optional, Dict, Any, Tuple
import pandas as pd
import numpy as np
from dataclasses import dataclass
from enum import Enum
from sklearn.preprocessing import (
    MinMaxScaler,
    StandardScaler,
    LabelEncoder,
    OneHotEncoder,
)


class NormalizationMethod(str, Enum):
    """Normalization methods."""
    MIN_MAX = "min_max"
    Z_SCORE = "z_score"
    ROBUST = "robust"


class EncodingMethod(str, Enum):
    """Categorical encoding methods."""
    LABEL = "label"
    ONE_HOT = "one_hot"
    ORDINAL = "ordinal"


@dataclass
class TransformationResult:
    """Result of data transformation operation."""
    transformed_data: pd.DataFrame
    transformers: Dict[str, Any]
    columns_transformed: List[str]
    transformation_type: str
    rows_processed: int


class DataTransformer:
    """
    Data transformation component for URIS-AI.
    
    Provides functionality for:
    - Normalization (min-max, z-score, robust scaling)
    - Categorical encoding (label, one-hot, ordinal)
    - Feature scaling for ML models
    
    Requirements: 1.2
    """

    def __init__(self):
        """Initialize DataTransformer."""
        self._scalers: Dict[str, Any] = {}
        self._encoders: Dict[str, Any] = {}

    def normalize(
        self,
        data: pd.DataFrame,
        columns: Optional[List[str]] = None,
        method: NormalizationMethod = NormalizationMethod.MIN_MAX,
        feature_range: Tuple[float, float] = (0, 1),
    ) -> TransformationResult:
        """
        Normalize numeric columns.
        
        Args:
            data: Input DataFrame
            columns: Columns to normalize (None = all numeric columns)
            method: Normalization method
            feature_range: Range for min-max scaling (default: 0 to 1)
            
        Returns:
            TransformationResult with normalized data and fitted scalers
        """
        if data.empty:
            return TransformationResult(
                transformed_data=data.copy(),
                transformers={},
                columns_transformed=[],
                transformation_type=f"normalize_{method.value}",
                rows_processed=0,
            )

        transformed = data.copy()
        
        # Determine columns to normalize
        if columns is None:
            columns = transformed.select_dtypes(include=[np.number]).columns.tolist()
        
        scalers = {}

        for col in columns:
            if col not in transformed.columns:
                continue

            # Create and fit scaler
            if method == NormalizationMethod.MIN_MAX:
                scaler = MinMaxScaler(feature_range=feature_range)
            elif method == NormalizationMethod.Z_SCORE:
                scaler = StandardScaler()
            elif method == NormalizationMethod.ROBUST:
                from sklearn.preprocessing import RobustScaler
                scaler = RobustScaler()
            else:
                continue

            # Fit and transform
            values = transformed[[col]].values
            transformed[col] = scaler.fit_transform(values).flatten()
            scalers[col] = scaler

        self._scalers.update(scalers)

        return TransformationResult(
            transformed_data=transformed,
            transformers=scalers,
            columns_transformed=columns,
            transformation_type=f"normalize_{method.value}",
            rows_processed=len(transformed),
        )

    def encode_categorical(
        self,
        data: pd.DataFrame,
        columns: Optional[List[str]] = None,
        method: EncodingMethod = EncodingMethod.ONE_HOT,
        drop_first: bool = False,
    ) -> TransformationResult:
        """
        Encode categorical columns.
        
        Args:
            data: Input DataFrame
            columns: Columns to encode (None = all object/category columns)
            method: Encoding method
            drop_first: Whether to drop first category in one-hot encoding
            
        Returns:
            TransformationResult with encoded data and fitted encoders
        """
        if data.empty:
            return TransformationResult(
                transformed_data=data.copy(),
                transformers={},
                columns_transformed=[],
                transformation_type=f"encode_{method.value}",
                rows_processed=0,
            )

        transformed = data.copy()
        
        # Determine columns to encode
        if columns is None:
            columns = transformed.select_dtypes(include=['object', 'category']).columns.tolist()
        
        encoders = {}
        encoded_columns = []

        if method == EncodingMethod.LABEL:
            for col in columns:
                if col not in transformed.columns:
                    continue

                encoder = LabelEncoder()
                transformed[col] = encoder.fit_transform(transformed[col].astype(str))
                encoders[col] = encoder
                encoded_columns.append(col)

        elif method == EncodingMethod.ONE_HOT:
            # Use pandas get_dummies for one-hot encoding
            for col in columns:
                if col not in transformed.columns:
                    continue

                # Create dummy variables
                dummies = pd.get_dummies(
                    transformed[col],
                    prefix=col,
                    drop_first=drop_first
                )
                
                # Drop original column and add dummies
                transformed = transformed.drop(columns=[col])
                transformed = pd.concat([transformed, dummies], axis=1)
                
                # Store column names for reference
                encoders[col] = {
                    'type': 'one_hot',
                    'columns': dummies.columns.tolist(),
                    'drop_first': drop_first
                }
                encoded_columns.append(col)

        elif method == EncodingMethod.ORDINAL:
            # Ordinal encoding (similar to label but preserves order)
            for col in columns:
                if col not in transformed.columns:
                    continue

                # Get unique values and create mapping
                unique_values = transformed[col].unique()
                mapping = {val: idx for idx, val in enumerate(sorted(unique_values))}
                
                transformed[col] = transformed[col].map(mapping)
                encoders[col] = {'mapping': mapping}
                encoded_columns.append(col)

        self._encoders.update(encoders)

        return TransformationResult(
            transformed_data=transformed,
            transformers=encoders,
            columns_transformed=encoded_columns,
            transformation_type=f"encode_{method.value}",
            rows_processed=len(transformed),
        )

    def inverse_normalize(
        self,
        data: pd.DataFrame,
        columns: Optional[List[str]] = None,
    ) -> pd.DataFrame:
        """
        Inverse transform normalized data back to original scale.
        
        Args:
            data: Normalized DataFrame
            columns: Columns to inverse transform (None = all stored scalers)
            
        Returns:
            DataFrame with original scale
        """
        if not self._scalers:
            return data.copy()

        transformed = data.copy()
        
        if columns is None:
            columns = list(self._scalers.keys())

        for col in columns:
            if col not in transformed.columns or col not in self._scalers:
                continue

            scaler = self._scalers[col]
            values = transformed[[col]].values
            transformed[col] = scaler.inverse_transform(values).flatten()

        return transformed

    def inverse_encode(
        self,
        data: pd.DataFrame,
        columns: Optional[List[str]] = None,
    ) -> pd.DataFrame:
        """
        Inverse transform encoded data back to original categories.
        
        Args:
            data: Encoded DataFrame
            columns: Columns to inverse transform (None = all stored encoders)
            
        Returns:
            DataFrame with original categories
        """
        if not self._encoders:
            return data.copy()

        transformed = data.copy()
        
        if columns is None:
            columns = list(self._encoders.keys())

        for col in columns:
            if col not in self._encoders:
                continue

            encoder = self._encoders[col]
            
            # Handle label encoding
            if isinstance(encoder, LabelEncoder):
                if col in transformed.columns:
                    transformed[col] = encoder.inverse_transform(transformed[col].astype(int))
            
            # Handle ordinal encoding
            elif isinstance(encoder, dict) and 'mapping' in encoder:
                if col in transformed.columns:
                    inverse_mapping = {v: k for k, v in encoder['mapping'].items()}
                    transformed[col] = transformed[col].map(inverse_mapping)

        return transformed

    def fit_normalize(
        self,
        data: pd.DataFrame,
        columns: Optional[List[str]] = None,
        method: NormalizationMethod = NormalizationMethod.MIN_MAX,
    ) -> Dict[str, Any]:
        """
        Fit normalization scalers without transforming data.
        
        Args:
            data: Input DataFrame
            columns: Columns to fit scalers for
            method: Normalization method
            
        Returns:
            Dictionary of fitted scalers
        """
        if data.empty:
            return {}

        if columns is None:
            columns = data.select_dtypes(include=[np.number]).columns.tolist()
        
        scalers = {}

        for col in columns:
            if col not in data.columns:
                continue

            if method == NormalizationMethod.MIN_MAX:
                scaler = MinMaxScaler()
            elif method == NormalizationMethod.Z_SCORE:
                scaler = StandardScaler()
            elif method == NormalizationMethod.ROBUST:
                from sklearn.preprocessing import RobustScaler
                scaler = RobustScaler()
            else:
                continue

            scaler.fit(data[[col]].values)
            scalers[col] = scaler

        self._scalers.update(scalers)
        return scalers

    def transform_with_fitted(
        self,
        data: pd.DataFrame,
        columns: Optional[List[str]] = None,
    ) -> pd.DataFrame:
        """
        Transform data using previously fitted scalers.
        
        Args:
            data: Input DataFrame
            columns: Columns to transform (None = all fitted scalers)
            
        Returns:
            Transformed DataFrame
        """
        if not self._scalers:
            return data.copy()

        transformed = data.copy()
        
        if columns is None:
            columns = list(self._scalers.keys())

        for col in columns:
            if col not in transformed.columns or col not in self._scalers:
                continue

            scaler = self._scalers[col]
            values = transformed[[col]].values
            transformed[col] = scaler.transform(values).flatten()

        return transformed

    def get_scaler(self, column: str) -> Optional[Any]:
        """
        Get fitted scaler for a specific column.
        
        Args:
            column: Column name
            
        Returns:
            Fitted scaler or None if not found
        """
        return self._scalers.get(column)

    def get_encoder(self, column: str) -> Optional[Any]:
        """
        Get fitted encoder for a specific column.
        
        Args:
            column: Column name
            
        Returns:
            Fitted encoder or None if not found
        """
        return self._encoders.get(column)

    def reset_transformers(self):
        """Reset all fitted transformers."""
        self._scalers = {}
        self._encoders = {}

    def get_transformation_info(self) -> Dict[str, Any]:
        """
        Get information about fitted transformers.
        
        Returns:
            Dictionary with transformation information
        """
        return {
            'scalers': list(self._scalers.keys()),
            'encoders': list(self._encoders.keys()),
            'num_scalers': len(self._scalers),
            'num_encoders': len(self._encoders),
        }
