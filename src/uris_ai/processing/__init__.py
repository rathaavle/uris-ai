"""
Data Processing Layer for URIS-AI.

This module provides data cleaning, integration, feature engineering,
and transformation capabilities for the URIS-AI system.

Components:
- Data_Cleaner: Handles missing values and outlier detection/removal
- Region_Integrator: Integrates data from multiple sources based on region_id
- Feature_Engineer: Creates ML features (rolling averages, lag features)
- Data_Transformer: Normalization and categorical encoding

Requirements: 7.1, 1.2
"""

from .data_cleaner import DataCleaner
from .region_integrator import RegionIntegrator
from .feature_engineer import FeatureEngineer
from .data_transformer import DataTransformer

__all__ = [
    "DataCleaner",
    "RegionIntegrator",
    "FeatureEngineer",
    "DataTransformer",
]
