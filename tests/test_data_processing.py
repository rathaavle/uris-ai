"""
Unit tests for Data Processing Layer.

Tests all components: DataCleaner, RegionIntegrator, FeatureEngineer,
and DataTransformer.

Requirements: 7.1, 1.2
"""

import pytest
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

from src.uris_ai.processing import (
    DataCleaner,
    RegionIntegrator,
    FeatureEngineer,
    DataTransformer,
)
from src.uris_ai.processing.data_cleaner import (
    ImputationStrategy,
    OutlierMethod,
)
from src.uris_ai.processing.data_transformer import (
    NormalizationMethod,
    EncodingMethod,
)


# ============================================================================
# DataCleaner Tests
# ============================================================================


class TestDataCleaner:
    """Test DataCleaner component."""

    def test_clean_with_missing_values_median(self):
        """Test cleaning data with missing values using median strategy."""
        data = pd.DataFrame({
            'region_id': [1, 2, 3, 4, 5],
            'rainfall': [10.0, np.nan, 30.0, 40.0, 50.0],
            'temperature': [25.0, 26.0, np.nan, 28.0, 29.0],
        })

        cleaner = DataCleaner(missing_value_strategy=ImputationStrategy.MEDIAN)
        result = cleaner.clean(data, handle_missing=True, remove_outliers=False)

        # Check that missing values are filled
        assert result.cleaned_data['rainfall'].isnull().sum() == 0
        assert result.cleaned_data['temperature'].isnull().sum() == 0
        
        # Check median imputation
        assert result.cleaned_data['rainfall'].iloc[1] == 35.0  # Median of [10, 30, 40, 50]
        assert result.missing_values_handled == 2

    def test_clean_with_missing_values_mean(self):
        """Test cleaning data with missing values using mean strategy."""
        data = pd.DataFrame({
            'region_id': [1, 2, 3],
            'rainfall': [10.0, np.nan, 30.0],
        })

        cleaner = DataCleaner(missing_value_strategy=ImputationStrategy.MEAN)
        result = cleaner.clean(data, handle_missing=True, remove_outliers=False)

        # Mean of [10, 30] = 20
        assert result.cleaned_data['rainfall'].iloc[1] == 20.0
        assert result.missing_values_handled == 1

    def test_remove_outliers_iqr(self):
        """Test outlier removal using IQR method."""
        data = pd.DataFrame({
            'region_id': [1, 2, 3, 4, 5, 6, 7],
            'rainfall': [10.0, 12.0, 15.0, 18.0, 20.0, 22.0, 100.0],  # 100 is outlier
        })

        cleaner = DataCleaner(outlier_method=OutlierMethod.IQR, outlier_threshold=1.5)
        result = cleaner.clean(data, handle_missing=False, remove_outliers=True)

        # Outlier should be removed
        assert len(result.cleaned_data) < len(data)
        assert 100.0 not in result.cleaned_data['rainfall'].values
        assert result.outliers_removed > 0

    def test_remove_outliers_zscore(self):
        """Test outlier removal using Z-score method."""
        data = pd.DataFrame({
            'region_id': list(range(1, 11)),
            'rainfall': [10, 12, 15, 18, 20, 22, 25, 28, 30, 1000],  # 1000 is extreme outlier
        })

        cleaner = DataCleaner(outlier_method=OutlierMethod.Z_SCORE, outlier_threshold=2.5)
        result = cleaner.clean(
            data,
            columns_to_clean=['rainfall'],  # Only clean rainfall column
            handle_missing=False,
            remove_outliers=True
        )

        # Outlier should be removed
        assert len(result.cleaned_data) < len(data)
        assert result.outliers_removed > 0

    def test_clean_empty_dataframe(self):
        """Test cleaning empty DataFrame."""
        data = pd.DataFrame()

        cleaner = DataCleaner()
        result = cleaner.clean(data)

        assert result.cleaned_data.empty
        assert result.missing_values_handled == 0
        assert result.outliers_removed == 0

    def test_get_missing_value_summary(self):
        """Test getting missing value summary."""
        data = pd.DataFrame({
            'col1': [1, 2, np.nan, 4],
            'col2': [np.nan, np.nan, 3, 4],
            'col3': [1, 2, 3, 4],
        })

        cleaner = DataCleaner()
        summary = cleaner.get_missing_value_summary(data)

        assert len(summary) == 2  # Only col1 and col2 have missing values
        assert 'col2' in summary['column'].values
        assert summary[summary['column'] == 'col2']['missing_count'].values[0] == 2

    def test_detect_outliers(self):
        """Test outlier detection without removal."""
        data = pd.DataFrame({
            'rainfall': [10, 12, 15, 18, 20, 22, 25, 28, 30, 200],
        })

        cleaner = DataCleaner(outlier_method=OutlierMethod.IQR)
        outliers = cleaner.detect_outliers(data)

        assert 'rainfall' in outliers
        assert len(outliers['rainfall']) > 0


# ============================================================================
# RegionIntegrator Tests
# ============================================================================


class TestRegionIntegrator:
    """Test RegionIntegrator component."""

    def test_integrate_by_region_inner(self):
        """Test integrating datasets by region with inner join."""
        weather = pd.DataFrame({
            'region_id': [1, 2, 3],
            'rainfall': [10.0, 20.0, 30.0],
        })

        flood = pd.DataFrame({
            'region_id': [1, 2, 4],
            'severity': [2, 3, 4],
        })

        integrator = RegionIntegrator()
        result = integrator.integrate_by_region(
            {'weather': weather, 'flood': flood},
            how='inner'
        )

        # Inner join should only include regions 1 and 2
        assert len(result.integrated_data) == 2
        assert result.regions_processed == 2
        assert 'rainfall' in result.integrated_data.columns
        assert 'severity' in result.integrated_data.columns

    def test_integrate_by_region_outer(self):
        """Test integrating datasets by region with outer join."""
        weather = pd.DataFrame({
            'region_id': [1, 2],
            'rainfall': [10.0, 20.0],
        })

        flood = pd.DataFrame({
            'region_id': [2, 3],
            'severity': [3, 4],
        })

        integrator = RegionIntegrator()
        result = integrator.integrate_by_region(
            {'weather': weather, 'flood': flood},
            how='outer'
        )

        # Outer join should include all regions
        assert len(result.integrated_data) == 3
        assert result.regions_processed == 3

    def test_integrate_temporal(self):
        """Test temporal integration with region and time alignment."""
        weather = pd.DataFrame({
            'region_id': [1, 1, 2],
            'date': pd.to_datetime(['2024-01-01', '2024-01-02', '2024-01-01']),
            'rainfall': [10.0, 20.0, 15.0],
        })

        flood = pd.DataFrame({
            'region_id': [1, 2],
            'date': pd.to_datetime(['2024-01-01', '2024-01-01']),
            'severity': [2, 3],
        })

        integrator = RegionIntegrator()
        result = integrator.integrate_temporal(
            {'weather': weather, 'flood': flood},
            how='inner'
        )

        # Should match on both region_id and date
        assert len(result.integrated_data) == 2
        assert 'rainfall' in result.integrated_data.columns
        assert 'severity' in result.integrated_data.columns

    def test_spatial_join(self):
        """Test spatial join based on coordinates."""
        facilities = pd.DataFrame({
            'name': ['Hospital A', 'Hospital B'],
            'latitude': [-6.2, -6.3],
            'longitude': [106.8, 106.9],
        })

        regions = pd.DataFrame({
            'region_id': [1, 2],
            'latitude': [-6.21, -6.5],
            'longitude': [106.81, 107.0],
        })

        integrator = RegionIntegrator()
        result = integrator.spatial_join(
            facilities,
            regions,
            radius_km=10.0,
            how='inner'
        )

        # Should find matches within 10km
        assert len(result.integrated_data) > 0
        assert 'distance_km' in result.integrated_data.columns

    def test_aggregate_by_region(self):
        """Test aggregating data by region."""
        data = pd.DataFrame({
            'region_id': [1, 1, 2, 2, 3],
            'rainfall': [10.0, 20.0, 15.0, 25.0, 30.0],
            'temperature': [25.0, 26.0, 27.0, 28.0, 29.0],
        })

        integrator = RegionIntegrator()
        aggregated = integrator.aggregate_by_region(
            data,
            aggregations={'rainfall': 'mean', 'temperature': 'max'}
        )

        assert len(aggregated) == 3  # 3 unique regions
        assert aggregated[aggregated['region_id'] == 1]['rainfall'].values[0] == 15.0


# ============================================================================
# FeatureEngineer Tests
# ============================================================================


class TestFeatureEngineer:
    """Test FeatureEngineer component."""

    def test_create_rolling_features(self):
        """Test creating rolling window features."""
        data = pd.DataFrame({
            'region_id': [1] * 10,
            'rainfall': [10, 12, 15, 18, 20, 22, 25, 28, 30, 32],
        })

        engineer = FeatureEngineer()
        result = engineer.create_rolling_features(
            data,
            columns=['rainfall'],
            windows=[3],
            functions=['mean', 'max']
        )

        assert 'rainfall_rolling_3_mean' in result.features.columns
        assert 'rainfall_rolling_3_max' in result.features.columns
        assert len(result.new_columns) == 2

    def test_create_lag_features(self):
        """Test creating lag features."""
        data = pd.DataFrame({
            'region_id': [1, 1, 1, 2, 2, 2],
            'rainfall': [10, 20, 30, 15, 25, 35],
        })

        engineer = FeatureEngineer()
        result = engineer.create_lag_features(
            data,
            columns=['rainfall'],
            lags=[1, 2],
            group_by='region_id'
        )

        assert 'rainfall_lag_1' in result.features.columns
        assert 'rainfall_lag_2' in result.features.columns
        
        # Check lag values for region 1
        assert pd.isna(result.features.iloc[0]['rainfall_lag_1'])  # First row has no lag
        assert result.features.iloc[1]['rainfall_lag_1'] == 10  # Second row lags first

    def test_create_temporal_features(self):
        """Test extracting temporal features from datetime."""
        dates = pd.date_range('2024-01-01', periods=5, freq='D')
        data = pd.DataFrame({
            'date': dates,
            'value': [1, 2, 3, 4, 5],
        })

        engineer = FeatureEngineer()
        result = engineer.create_temporal_features(
            data,
            date_column='date',
            features=['day', 'month', 'day_of_week', 'is_weekend']
        )

        assert 'day' in result.features.columns
        assert 'month' in result.features.columns
        assert 'day_of_week' in result.features.columns
        assert 'is_weekend' in result.features.columns
        
        # Check values
        assert result.features['month'].iloc[0] == 1
        assert result.features['day'].iloc[0] == 1

    def test_create_interaction_features(self):
        """Test creating interaction features."""
        data = pd.DataFrame({
            'rainfall': [10, 20, 30],
            'humidity': [70, 80, 90],
        })

        engineer = FeatureEngineer()
        result = engineer.create_interaction_features(
            data,
            column_pairs=[('rainfall', 'humidity')],
            operations=['multiply', 'add']
        )

        assert 'rainfall_x_humidity' in result.features.columns
        assert 'rainfall_plus_humidity' in result.features.columns
        
        # Check multiplication
        assert result.features['rainfall_x_humidity'].iloc[0] == 700

    def test_create_aggregated_features(self):
        """Test creating aggregated features by group."""
        data = pd.DataFrame({
            'region_id': [1, 1, 2, 2, 3],
            'rainfall': [10, 20, 15, 25, 30],
        })

        engineer = FeatureEngineer()
        result = engineer.create_aggregated_features(
            data,
            group_by='region_id',
            columns=['rainfall'],
            functions=['mean', 'std']
        )

        assert 'rainfall_region_id_mean' in result.features.columns
        assert 'rainfall_region_id_std' in result.features.columns
        
        # Check mean for region 1
        region_1_mean = result.features[result.features['region_id'] == 1]['rainfall_region_id_mean'].iloc[0]
        assert region_1_mean == 15.0

    def test_create_cumulative_features(self):
        """Test creating cumulative sum features."""
        data = pd.DataFrame({
            'region_id': [1, 1, 1, 2, 2],
            'rainfall': [10, 20, 30, 15, 25],
        })

        engineer = FeatureEngineer()
        result = engineer.create_cumulative_features(
            data,
            columns=['rainfall'],
            group_by='region_id'
        )

        assert 'rainfall_cumsum' in result.features.columns
        
        # Check cumulative sum for region 1
        assert result.features.iloc[0]['rainfall_cumsum'] == 10
        assert result.features.iloc[1]['rainfall_cumsum'] == 30
        assert result.features.iloc[2]['rainfall_cumsum'] == 60


# ============================================================================
# DataTransformer Tests
# ============================================================================


class TestDataTransformer:
    """Test DataTransformer component."""

    def test_normalize_min_max(self):
        """Test min-max normalization."""
        data = pd.DataFrame({
            'rainfall': [0, 50, 100],
            'temperature': [20, 25, 30],
        })

        transformer = DataTransformer()
        result = transformer.normalize(
            data,
            method=NormalizationMethod.MIN_MAX,
            feature_range=(0, 1)
        )

        # Check normalization
        assert result.transformed_data['rainfall'].min() == 0.0
        assert result.transformed_data['rainfall'].max() == 1.0
        assert result.transformed_data['rainfall'].iloc[1] == 0.5

    def test_normalize_z_score(self):
        """Test z-score normalization."""
        data = pd.DataFrame({
            'rainfall': [10, 20, 30, 40, 50],
        })

        transformer = DataTransformer()
        result = transformer.normalize(
            data,
            method=NormalizationMethod.Z_SCORE
        )

        # Check that mean is approximately 0 and std is approximately 1
        # Note: StandardScaler uses ddof=0, pandas std() uses ddof=1
        assert abs(result.transformed_data['rainfall'].mean()) < 1e-10
        assert abs(result.transformed_data['rainfall'].std(ddof=0) - 1.0) < 1e-10

    def test_encode_categorical_label(self):
        """Test label encoding."""
        data = pd.DataFrame({
            'category': ['low', 'medium', 'high', 'low', 'high'],
        })

        transformer = DataTransformer()
        result = transformer.encode_categorical(
            data,
            method=EncodingMethod.LABEL
        )

        # Check that categories are encoded as integers
        assert result.transformed_data['category'].dtype in [np.int32, np.int64]
        assert len(result.transformed_data['category'].unique()) == 3

    def test_encode_categorical_one_hot(self):
        """Test one-hot encoding."""
        data = pd.DataFrame({
            'category': ['low', 'medium', 'high'],
        })

        transformer = DataTransformer()
        result = transformer.encode_categorical(
            data,
            method=EncodingMethod.ONE_HOT
        )

        # Check that one-hot columns are created
        assert 'category_low' in result.transformed_data.columns or \
               'category_medium' in result.transformed_data.columns
        assert 'category' not in result.transformed_data.columns

    def test_inverse_normalize(self):
        """Test inverse normalization."""
        data = pd.DataFrame({
            'rainfall': [0, 50, 100],
        })

        transformer = DataTransformer()
        
        # Normalize
        result = transformer.normalize(data, method=NormalizationMethod.MIN_MAX)
        
        # Inverse normalize
        original = transformer.inverse_normalize(result.transformed_data)

        # Check that values are restored
        assert np.allclose(original['rainfall'].values, data['rainfall'].values)

    def test_fit_and_transform(self):
        """Test fitting and transforming with separate datasets."""
        train_data = pd.DataFrame({
            'rainfall': [0, 50, 100],
        })

        test_data = pd.DataFrame({
            'rainfall': [25, 75],
        })

        transformer = DataTransformer()
        
        # Fit on train data
        transformer.fit_normalize(train_data, method=NormalizationMethod.MIN_MAX)
        
        # Transform test data
        transformed = transformer.transform_with_fitted(test_data)

        # Check that test data is transformed using train statistics
        assert 0 <= transformed['rainfall'].iloc[0] <= 1
        assert 0 <= transformed['rainfall'].iloc[1] <= 1

    def test_get_transformation_info(self):
        """Test getting transformation information."""
        data = pd.DataFrame({
            'rainfall': [0, 50, 100],
            'category': ['low', 'high', 'medium'],
        })

        transformer = DataTransformer()
        transformer.normalize(data, columns=['rainfall'])
        transformer.encode_categorical(data, columns=['category'])

        info = transformer.get_transformation_info()

        assert 'rainfall' in info['scalers']
        assert 'category' in info['encoders']
        assert info['num_scalers'] == 1
        assert info['num_encoders'] == 1

    def test_reset_transformers(self):
        """Test resetting transformers."""
        data = pd.DataFrame({
            'rainfall': [0, 50, 100],
        })

        transformer = DataTransformer()
        transformer.normalize(data)

        assert len(transformer._scalers) > 0

        transformer.reset_transformers()

        assert len(transformer._scalers) == 0
        assert len(transformer._encoders) == 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
