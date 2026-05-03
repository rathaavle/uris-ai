"""
Unit tests for database utility functions.

Tests database query optimization utilities including index creation,
query performance analysis, and statistics optimization.

Requirements: 8.1
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from sqlalchemy.orm import Session

from uris_ai.database.db_utils import (
    create_performance_indexes,
    analyze_query_performance,
    get_slow_queries,
    optimize_table_statistics,
    get_index_usage_stats,
)


class TestCreatePerformanceIndexes:
    """Tests for create_performance_indexes function."""

    def test_create_indexes_success(self):
        """Test successful index creation."""
        # Arrange
        mock_session = Mock(spec=Session)
        mock_result = Mock()
        mock_result.__getitem__ = Mock(return_value=0)  # Index doesn't exist
        mock_session.execute.return_value.fetchone.return_value = mock_result

        # Act
        results = create_performance_indexes(mock_session)

        # Assert
        assert "created" in results
        assert "failed" in results
        assert "already_exists" in results
        assert isinstance(results["created"], list)
        assert isinstance(results["failed"], list)
        assert isinstance(results["already_exists"], list)

    def test_create_indexes_already_exists(self):
        """Test handling of already existing indexes."""
        # Arrange
        mock_session = Mock(spec=Session)
        mock_result = Mock()
        mock_result.__getitem__ = Mock(return_value=1)  # Index exists
        mock_session.execute.return_value.fetchone.return_value = mock_result

        # Act
        results = create_performance_indexes(mock_session)

        # Assert
        assert len(results["already_exists"]) > 0
        assert len(results["created"]) == 0

    def test_create_indexes_failure(self):
        """Test handling of index creation failures."""
        # Arrange
        mock_session = Mock(spec=Session)
        mock_session.execute.side_effect = Exception("Database error")

        # Act
        results = create_performance_indexes(mock_session)

        # Assert
        assert len(results["failed"]) > 0
        mock_session.rollback.assert_called()


class TestAnalyzeQueryPerformance:
    """Tests for analyze_query_performance function."""

    def test_analyze_query_success(self):
        """Test successful query analysis."""
        # Arrange
        mock_session = Mock(spec=Session)
        mock_result = [("Query plan line 1",), ("Query plan line 2",)]
        mock_session.execute.return_value = mock_result
        query = "SELECT * FROM regions"

        # Act
        result = analyze_query_performance(mock_session, query)

        # Assert
        assert result["success"] is True
        assert "plan" in result
        assert isinstance(result["plan"], list)

    def test_analyze_query_failure(self):
        """Test handling of query analysis failures."""
        # Arrange
        mock_session = Mock(spec=Session)
        mock_session.execute.side_effect = Exception("Analysis error")
        query = "INVALID QUERY"

        # Act
        result = analyze_query_performance(mock_session, query)

        # Assert
        assert result["success"] is False
        assert "error" in result


class TestGetSlowQueries:
    """Tests for get_slow_queries function."""

    def test_get_slow_queries_success(self):
        """Test successful retrieval of slow queries."""
        # Arrange
        mock_session = Mock(spec=Session)
        mock_result = [
            (1, "SELECT * FROM risk_scores", 1500.0, 2000.0, 100, "2024-01-01"),
            (2, "SELECT * FROM weather_data", 1200.0, 1800.0, 50, "2024-01-02"),
        ]
        mock_session.execute.return_value = mock_result

        # Act
        result = get_slow_queries(mock_session, min_duration_ms=1000)

        # Assert
        assert isinstance(result, list)
        assert len(result) == 2
        assert result[0]["query_id"] == 1
        assert result[0]["avg_duration_ms"] == 1500.0

    def test_get_slow_queries_empty(self):
        """Test when no slow queries are found."""
        # Arrange
        mock_session = Mock(spec=Session)
        mock_session.execute.return_value = []

        # Act
        result = get_slow_queries(mock_session, min_duration_ms=1000)

        # Assert
        assert isinstance(result, list)
        assert len(result) == 0

    def test_get_slow_queries_failure(self):
        """Test handling of query retrieval failures."""
        # Arrange
        mock_session = Mock(spec=Session)
        mock_session.execute.side_effect = Exception("Query error")

        # Act
        result = get_slow_queries(mock_session, min_duration_ms=1000)

        # Assert
        assert isinstance(result, list)
        assert len(result) == 0


class TestOptimizeTableStatistics:
    """Tests for optimize_table_statistics function."""

    def test_optimize_statistics_success(self):
        """Test successful statistics optimization."""
        # Arrange
        mock_session = Mock(spec=Session)
        table_name = "risk_scores"

        # Act
        result = optimize_table_statistics(mock_session, table_name)

        # Assert
        assert result is True
        mock_session.execute.assert_called_once()
        mock_session.commit.assert_called_once()

    def test_optimize_statistics_failure(self):
        """Test handling of statistics optimization failures."""
        # Arrange
        mock_session = Mock(spec=Session)
        mock_session.execute.side_effect = Exception("Statistics error")
        table_name = "invalid_table"

        # Act
        result = optimize_table_statistics(mock_session, table_name)

        # Assert
        assert result is False
        mock_session.rollback.assert_called_once()


class TestGetIndexUsageStats:
    """Tests for get_index_usage_stats function."""

    def test_get_index_stats_success(self):
        """Test successful retrieval of index usage statistics."""
        # Arrange
        mock_session = Mock(spec=Session)
        mock_result = [
            ("risk_scores", "idx_risk_region_date", 1000, 500, 200, 50, "2024-01-01", "2024-01-02"),
            ("weather_data", "idx_weather_region_date", 800, 300, 100, 30, "2024-01-01", "2024-01-02"),
        ]
        mock_session.execute.return_value = mock_result

        # Act
        result = get_index_usage_stats(mock_session)

        # Assert
        assert isinstance(result, list)
        assert len(result) == 2
        assert result[0]["table_name"] == "risk_scores"
        assert result[0]["index_name"] == "idx_risk_region_date"
        assert result[0]["user_seeks"] == 1000

    def test_get_index_stats_empty(self):
        """Test when no index statistics are found."""
        # Arrange
        mock_session = Mock(spec=Session)
        mock_session.execute.return_value = []

        # Act
        result = get_index_usage_stats(mock_session)

        # Assert
        assert isinstance(result, list)
        assert len(result) == 0

    def test_get_index_stats_failure(self):
        """Test handling of index statistics retrieval failures."""
        # Arrange
        mock_session = Mock(spec=Session)
        mock_session.execute.side_effect = Exception("Stats error")

        # Act
        result = get_index_usage_stats(mock_session)

        # Assert
        assert isinstance(result, list)
        assert len(result) == 0


class TestIndexCreationDetails:
    """Tests for specific index creation scenarios."""

    def test_all_expected_indexes_defined(self):
        """Test that all expected performance indexes are defined."""
        # Arrange
        mock_session = Mock(spec=Session)
        mock_result = Mock()
        mock_result.__getitem__ = Mock(return_value=0)
        mock_session.execute.return_value.fetchone.return_value = mock_result

        # Act
        results = create_performance_indexes(mock_session)

        # Assert
        # Verify that key indexes are created
        created_names = [idx["name"] for idx in results["created"]]
        
        # Check for critical indexes
        expected_indexes = [
            "idx_weather_date_desc",
            "idx_flood_severity",
            "idx_risk_date_desc",
            "idx_risk_region_date_desc",
            "idx_recommendations_active_urgency",
            "idx_facilities_coords",
            "idx_roads_main",
        ]
        
        for expected in expected_indexes:
            assert expected in created_names, f"Expected index {expected} not found"

    def test_index_creation_with_reason(self):
        """Test that indexes are created with proper reasoning."""
        # Arrange
        mock_session = Mock(spec=Session)
        mock_result = Mock()
        mock_result.__getitem__ = Mock(return_value=0)
        mock_session.execute.return_value.fetchone.return_value = mock_result

        # Act
        results = create_performance_indexes(mock_session)

        # Assert
        for idx in results["created"]:
            assert "name" in idx
            assert "table" in idx
            assert "reason" in idx
            assert len(idx["reason"]) > 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
