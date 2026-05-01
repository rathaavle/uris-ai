"""
Region_Integrator component for data integration.

Integrates data from multiple sources based on region_id and performs
spatial joins for geographic data.
Requirements: 7.1
"""

from typing import List, Optional, Dict, Any
import pandas as pd
import numpy as np
from dataclasses import dataclass
from datetime import datetime


@dataclass
class IntegrationResult:
    """Result of data integration operation."""
    integrated_data: pd.DataFrame
    sources_integrated: List[str]
    regions_processed: int
    rows_integrated: int
    integration_method: str
    timestamp: datetime


class RegionIntegrator:
    """
    Region-based data integration component for URIS-AI.
    
    Provides functionality for:
    - Merging data from multiple sources based on region_id
    - Spatial joins for geographic data
    - Temporal alignment of time-series data
    
    Requirements: 7.1
    """

    def __init__(self):
        """Initialize RegionIntegrator."""
        pass

    def integrate_by_region(
        self,
        datasets: Dict[str, pd.DataFrame],
        region_column: str = "region_id",
        how: str = "inner",
        suffixes: Optional[tuple] = None,
    ) -> IntegrationResult:
        """
        Integrate multiple datasets based on region_id.
        
        Args:
            datasets: Dictionary mapping source names to DataFrames
            region_column: Name of the region identifier column
            how: Type of join ('inner', 'outer', 'left', 'right')
            suffixes: Suffixes for overlapping column names
            
        Returns:
            IntegrationResult with integrated data and metadata
        """
        if not datasets:
            return IntegrationResult(
                integrated_data=pd.DataFrame(),
                sources_integrated=[],
                regions_processed=0,
                rows_integrated=0,
                integration_method=how,
                timestamp=datetime.now(),
            )

        if suffixes is None:
            suffixes = ("_x", "_y")

        # Start with the first dataset
        source_names = list(datasets.keys())
        integrated = datasets[source_names[0]].copy()
        
        # Merge with remaining datasets
        for source_name in source_names[1:]:
            df = datasets[source_name]
            
            # Merge on region_id
            integrated = pd.merge(
                integrated,
                df,
                on=region_column,
                how=how,
                suffixes=suffixes,
            )

        regions_processed = integrated[region_column].nunique() if region_column in integrated.columns else 0

        return IntegrationResult(
            integrated_data=integrated,
            sources_integrated=source_names,
            regions_processed=regions_processed,
            rows_integrated=len(integrated),
            integration_method=how,
            timestamp=datetime.now(),
        )

    def integrate_temporal(
        self,
        datasets: Dict[str, pd.DataFrame],
        region_column: str = "region_id",
        time_column: str = "date",
        how: str = "inner",
    ) -> IntegrationResult:
        """
        Integrate datasets with temporal alignment.
        
        Merges datasets based on both region_id and timestamp,
        ensuring temporal consistency.
        
        Args:
            datasets: Dictionary mapping source names to DataFrames
            region_column: Name of the region identifier column
            time_column: Name of the timestamp column
            how: Type of join ('inner', 'outer', 'left', 'right')
            
        Returns:
            IntegrationResult with temporally aligned data
        """
        if not datasets:
            return IntegrationResult(
                integrated_data=pd.DataFrame(),
                sources_integrated=[],
                regions_processed=0,
                rows_integrated=0,
                integration_method=f"temporal_{how}",
                timestamp=datetime.now(),
            )

        source_names = list(datasets.keys())
        integrated = datasets[source_names[0]].copy()
        
        # Ensure time column is datetime
        if time_column in integrated.columns:
            integrated[time_column] = pd.to_datetime(integrated[time_column])
        
        # Merge with remaining datasets on both region and time
        for source_name in source_names[1:]:
            df = datasets[source_name].copy()
            
            if time_column in df.columns:
                df[time_column] = pd.to_datetime(df[time_column])
            
            integrated = pd.merge(
                integrated,
                df,
                on=[region_column, time_column],
                how=how,
                suffixes=("", f"_{source_name}"),
            )

        regions_processed = integrated[region_column].nunique() if region_column in integrated.columns else 0

        return IntegrationResult(
            integrated_data=integrated,
            sources_integrated=source_names,
            regions_processed=regions_processed,
            rows_integrated=len(integrated),
            integration_method=f"temporal_{how}",
            timestamp=datetime.now(),
        )

    def spatial_join(
        self,
        left_data: pd.DataFrame,
        right_data: pd.DataFrame,
        left_lat: str = "latitude",
        left_lon: str = "longitude",
        right_lat: str = "latitude",
        right_lon: str = "longitude",
        radius_km: float = 1.0,
        how: str = "inner",
    ) -> IntegrationResult:
        """
        Perform spatial join based on geographic proximity.
        
        Joins two datasets based on distance between coordinates.
        Points within the specified radius are considered matches.
        
        Args:
            left_data: Left DataFrame with coordinates
            right_data: Right DataFrame with coordinates
            left_lat: Latitude column name in left DataFrame
            left_lon: Longitude column name in left DataFrame
            right_lat: Latitude column name in right DataFrame
            right_lon: Longitude column name in right DataFrame
            radius_km: Maximum distance in kilometers for a match
            how: Type of join ('inner', 'left')
            
        Returns:
            IntegrationResult with spatially joined data
        """
        if left_data.empty or right_data.empty:
            return IntegrationResult(
                integrated_data=pd.DataFrame(),
                sources_integrated=["left", "right"],
                regions_processed=0,
                rows_integrated=0,
                integration_method=f"spatial_{how}",
                timestamp=datetime.now(),
            )

        # Create result list
        results = []
        
        for left_idx, left_row in left_data.iterrows():
            left_lat_val = left_row[left_lat]
            left_lon_val = left_row[left_lon]
            
            # Find all right rows within radius
            matches = []
            for right_idx, right_row in right_data.iterrows():
                right_lat_val = right_row[right_lat]
                right_lon_val = right_row[right_lon]
                
                distance = self._haversine_distance(
                    left_lat_val, left_lon_val,
                    right_lat_val, right_lon_val
                )
                
                if distance <= radius_km:
                    matches.append((right_idx, distance))
            
            if matches:
                # Take the closest match
                closest_idx, distance = min(matches, key=lambda x: x[1])
                
                # Combine rows
                combined = pd.concat([
                    left_row.to_frame().T.reset_index(drop=True),
                    right_data.loc[[closest_idx]].reset_index(drop=True).add_suffix('_right')
                ], axis=1)
                combined['distance_km'] = distance
                results.append(combined)
                
            elif how == "left":
                # Include left row even without match
                combined = left_row.to_frame().T.reset_index(drop=True)
                combined['distance_km'] = np.nan
                results.append(combined)
        
        if results:
            integrated = pd.concat(results, ignore_index=True)
        else:
            integrated = pd.DataFrame()

        return IntegrationResult(
            integrated_data=integrated,
            sources_integrated=["left", "right"],
            regions_processed=0,  # Not region-based
            rows_integrated=len(integrated),
            integration_method=f"spatial_{how}",
            timestamp=datetime.now(),
        )

    def aggregate_by_region(
        self,
        data: pd.DataFrame,
        region_column: str = "region_id",
        aggregations: Optional[Dict[str, str]] = None,
    ) -> pd.DataFrame:
        """
        Aggregate data by region.
        
        Args:
            data: Input DataFrame
            region_column: Name of the region identifier column
            aggregations: Dictionary mapping column names to aggregation functions
                         (e.g., {'rainfall': 'mean', 'temperature': 'max'})
                         If None, uses mean for all numeric columns
            
        Returns:
            DataFrame with aggregated data per region
        """
        if data.empty or region_column not in data.columns:
            return pd.DataFrame()

        if aggregations is None:
            # Default: mean for all numeric columns
            numeric_cols = data.select_dtypes(include=[np.number]).columns.tolist()
            if region_column in numeric_cols:
                numeric_cols.remove(region_column)
            aggregations = {col: 'mean' for col in numeric_cols}

        aggregated = data.groupby(region_column).agg(aggregations).reset_index()
        
        return aggregated

    def _haversine_distance(
        self, lat1: float, lon1: float, lat2: float, lon2: float
    ) -> float:
        """
        Calculate the great circle distance between two points on Earth.
        
        Uses the Haversine formula to calculate distance in kilometers.
        
        Args:
            lat1: Latitude of first point (degrees)
            lon1: Longitude of first point (degrees)
            lat2: Latitude of second point (degrees)
            lon2: Longitude of second point (degrees)
            
        Returns:
            Distance in kilometers
        """
        # Convert to radians
        lat1_rad = np.radians(lat1)
        lon1_rad = np.radians(lon1)
        lat2_rad = np.radians(lat2)
        lon2_rad = np.radians(lon2)
        
        # Haversine formula
        dlat = lat2_rad - lat1_rad
        dlon = lon2_rad - lon1_rad
        
        a = np.sin(dlat / 2)**2 + np.cos(lat1_rad) * np.cos(lat2_rad) * np.sin(dlon / 2)**2
        c = 2 * np.arcsin(np.sqrt(a))
        
        # Earth radius in kilometers
        r = 6371.0
        
        return c * r

    def join_with_region_metadata(
        self,
        data: pd.DataFrame,
        region_metadata: pd.DataFrame,
        region_column: str = "region_id",
        how: str = "left",
    ) -> pd.DataFrame:
        """
        Join data with region metadata (elevation, drainage capacity, etc.).
        
        Args:
            data: Input DataFrame with region_id
            region_metadata: DataFrame with region metadata
            region_column: Name of the region identifier column
            how: Type of join
            
        Returns:
            DataFrame with region metadata added
        """
        if data.empty or region_metadata.empty:
            return data.copy()

        joined = pd.merge(
            data,
            region_metadata,
            on=region_column,
            how=how,
            suffixes=("", "_metadata"),
        )
        
        return joined
