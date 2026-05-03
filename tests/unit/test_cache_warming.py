"""
Unit tests for cache warming functionality.

Tests cache warming strategies for risk scores and recommendations.

Requirements: 8.1
"""

import pytest
from datetime import datetime, timezone
from unittest.mock import Mock, patch, MagicMock

from uris_ai.services.cache_service import CacheService
from uris_ai.models.database import Region, RiskScore, Recommendation


class TestCacheWarming:
    """Tests for cache warming functionality."""

    @pytest.fixture
    def mock_db_session(self):
        """Create a mock database session."""
        return Mock()

    @pytest.fixture
    def mock_redis_client(self):
        """Create a mock Redis client."""
        client = Mock()
        client.ping.return_value = True
        client.info.return_value = {
            "connected_clients": 5,
            "used_memory_human": "1.5M",
            "keyspace_hits": 100,
            "keyspace_misses": 20,
            "uptime_in_seconds": 3600
        }
        client.dbsize.return_value = 50
        return client

    @pytest.fixture
    def cache_service(self, mock_redis_client):
        """Create a CacheService instance with mock Redis client."""
        return CacheService(redis_client=mock_redis_client)

    def test_warm_risk_scores_cache_success(self, cache_service, mock_db_session):
        """Test successful warming of risk scores cache."""
        # Arrange
        mock_regions = [
            Mock(region_id=1, name="Region 1"),
            Mock(region_id=2, name="Region 2"),
        ]
        
        mock_risk_scores = [
            Mock(
                region_id=1,
                flood_risk=50.0,
                traffic_impact=30.0,
                service_access=20.0,
                urban_risk_score=40.0,
                date=datetime.now(timezone.utc)
            ),
            Mock(
                region_id=2,
                flood_risk=70.0,
                traffic_impact=50.0,
                service_access=40.0,
                urban_risk_score=60.0,
                date=datetime.now(timezone.utc)
            ),
        ]
        
        # Mock query chain
        mock_query = Mock()
        mock_query.all.return_value = mock_regions
        mock_query.filter.return_value = mock_query
        mock_query.order_by.return_value = mock_query
        mock_query.first.side_effect = mock_risk_scores
        
        mock_db_session.query.return_value = mock_query

        # Act
        with patch('uris_ai.ml.flood_risk_engine.FloodRiskEngine') as mock_engine:
            mock_engine.return_value.get_risk_category.return_value = Mock(value="Medium")
            results = cache_service.warm_risk_scores_cache(mock_db_session)

        # Assert
        assert results["success"] is True
        assert results["regions_warmed"] == 2
        assert len(results["errors"]) == 0

    def test_warm_risk_scores_cache_no_data(self, cache_service, mock_db_session):
        """Test warming cache when no risk score data exists."""
        # Arrange
        mock_regions = [Mock(region_id=1, name="Region 1")]
        
        mock_query = Mock()
        mock_query.all.return_value = mock_regions
        mock_query.filter.return_value = mock_query
        mock_query.order_by.return_value = mock_query
        mock_query.first.return_value = None  # No risk score data
        
        mock_db_session.query.return_value = mock_query

        # Act
        with patch('uris_ai.ml.flood_risk_engine.FloodRiskEngine'):
            results = cache_service.warm_risk_scores_cache(mock_db_session)

        # Assert
        assert results["success"] is True
        assert results["regions_warmed"] == 0

    def test_warm_risk_scores_cache_partial_failure(self, cache_service, mock_db_session):
        """Test warming cache with partial failures."""
        # Arrange
        mock_regions = [
            Mock(region_id=1, name="Region 1"),
            Mock(region_id=2, name="Region 2"),
        ]
        
        mock_risk_score = Mock(
            region_id=1,
            flood_risk=50.0,
            traffic_impact=30.0,
            service_access=20.0,
            urban_risk_score=40.0,
            date=datetime.now(timezone.utc)
        )
        
        mock_query = Mock()
        mock_query.all.return_value = mock_regions
        mock_query.filter.return_value = mock_query
        mock_query.order_by.return_value = mock_query
        mock_query.first.side_effect = [mock_risk_score, Exception("Database error")]
        
        mock_db_session.query.return_value = mock_query

        # Act
        with patch('uris_ai.ml.flood_risk_engine.FloodRiskEngine') as mock_engine:
            mock_engine.return_value.get_risk_category.return_value = Mock(value="Medium")
            results = cache_service.warm_risk_scores_cache(mock_db_session)

        # Assert
        assert results["success"] is True
        assert results["regions_warmed"] == 1
        assert len(results["errors"]) == 1

    def test_warm_recommendations_cache_success(self, cache_service, mock_db_session):
        """Test successful warming of recommendations cache."""
        # Arrange
        mock_regions = [
            Mock(region_id=1, name="Region 1"),
            Mock(region_id=2, name="Region 2"),
        ]
        
        mock_recommendations = [
            Mock(
                id=1,
                region_id=1,
                recommendation_type="evacuation",
                description="Evacuate immediately",
                urgency_level="critical",
                created_at=datetime.now(timezone.utc),
                expires_at=None,
                is_active=True
            ),
        ]
        
        mock_query = Mock()
        mock_query.all.side_effect = [mock_regions, mock_recommendations, []]
        mock_query.filter.return_value = mock_query
        mock_query.order_by.return_value = mock_query
        mock_query.limit.return_value = mock_query
        
        mock_db_session.query.return_value = mock_query

        # Act
        results = cache_service.warm_recommendations_cache(mock_db_session)

        # Assert
        assert results["success"] is True
        assert results["regions_warmed"] == 1
        assert len(results["errors"]) == 0

    def test_warm_all_caches_success(self, cache_service, mock_db_session):
        """Test warming all caches successfully."""
        # Arrange
        mock_regions = [Mock(region_id=1, name="Region 1")]
        mock_query = Mock()
        mock_query.all.return_value = mock_regions
        mock_query.filter.return_value = mock_query
        mock_query.order_by.return_value = mock_query
        mock_query.first.return_value = None
        mock_query.limit.return_value = mock_query
        
        mock_db_session.query.return_value = mock_query

        # Act
        with patch('uris_ai.ml.flood_risk_engine.FloodRiskEngine'):
            results = cache_service.warm_all_caches(mock_db_session)

        # Assert
        assert "success" in results
        assert "risk_scores" in results
        assert "recommendations" in results
        assert "total_regions_warmed" in results

    def test_get_cache_stats_success(self, cache_service):
        """Test successful retrieval of cache statistics."""
        # Act
        stats = cache_service.get_cache_stats()

        # Assert
        assert stats["available"] is True
        assert "connected_clients" in stats
        assert "used_memory" in stats
        assert "total_keys" in stats
        assert "hit_rate" in stats
        assert stats["hit_rate"] > 0

    def test_get_cache_stats_unavailable(self):
        """Test cache statistics when Redis is unavailable."""
        # Arrange
        cache_service = CacheService(redis_client=None)

        # Act
        stats = cache_service.get_cache_stats()

        # Assert
        assert stats["available"] is False
        assert "error" in stats

    def test_calculate_hit_rate(self, cache_service):
        """Test cache hit rate calculation."""
        # Arrange
        info = {
            "keyspace_hits": 80,
            "keyspace_misses": 20
        }

        # Act
        hit_rate = cache_service._calculate_hit_rate(info)

        # Assert
        assert hit_rate == 80.0

    def test_calculate_hit_rate_no_requests(self, cache_service):
        """Test cache hit rate calculation with no requests."""
        # Arrange
        info = {
            "keyspace_hits": 0,
            "keyspace_misses": 0
        }

        # Act
        hit_rate = cache_service._calculate_hit_rate(info)

        # Assert
        assert hit_rate == 0.0


class TestCacheInvalidation:
    """Tests for cache invalidation functionality."""

    @pytest.fixture
    def mock_redis_client(self):
        """Create a mock Redis client."""
        client = Mock()
        client.ping.return_value = True
        client.delete.return_value = 1
        client.scan_iter.return_value = ["risk:trend:1:24h", "risk:trend:1:48h"]
        return client

    @pytest.fixture
    def cache_service(self, mock_redis_client):
        """Create a CacheService instance with mock Redis client."""
        return CacheService(redis_client=mock_redis_client)

    def test_invalidate_region_cache(self, cache_service, mock_redis_client):
        """Test invalidation of region-specific cache."""
        # Act
        cache_service.invalidate_region_cache(region_id=1)

        # Assert
        # Verify that delete was called for region-specific keys
        assert mock_redis_client.delete.call_count >= 3
        # Verify that pattern delete was called for trend data
        mock_redis_client.scan_iter.assert_called()

    def test_delete_pattern(self, cache_service, mock_redis_client):
        """Test deletion of keys matching a pattern."""
        # Act
        count = cache_service.delete_pattern("risk:trend:*")

        # Assert
        assert count > 0
        mock_redis_client.scan_iter.assert_called_with("risk:trend:*")
        mock_redis_client.delete.assert_called()


class TestCacheDomainHelpers:
    """Tests for domain-specific cache helper methods."""

    @pytest.fixture
    def mock_redis_client(self):
        """Create a mock Redis client."""
        client = Mock()
        client.ping.return_value = True
        client.get.return_value = '{"region_id": 1, "urban_risk_score": 50.0}'
        client.setex.return_value = True
        return client

    @pytest.fixture
    def cache_service(self, mock_redis_client):
        """Create a CacheService instance with mock Redis client."""
        return CacheService(redis_client=mock_redis_client)

    def test_get_risk_score(self, cache_service):
        """Test getting cached risk score."""
        # Act
        result = cache_service.get_risk_score(region_id=1)

        # Assert
        assert result is not None
        assert result["region_id"] == 1

    def test_set_risk_score(self, cache_service):
        """Test setting cached risk score."""
        # Arrange
        data = {"region_id": 1, "urban_risk_score": 50.0}

        # Act
        result = cache_service.set_risk_score(region_id=1, data=data)

        # Assert
        assert result is True

    def test_get_recommendations(self, cache_service, mock_redis_client):
        """Test getting cached recommendations."""
        # Arrange
        mock_redis_client.get.return_value = '[{"id": 1, "description": "Test"}]'

        # Act
        result = cache_service.get_recommendations(region_id=1)

        # Assert
        assert result is not None
        assert isinstance(result, list)

    def test_set_recommendations(self, cache_service):
        """Test setting cached recommendations."""
        # Arrange
        data = [{"id": 1, "description": "Test recommendation"}]

        # Act
        result = cache_service.set_recommendations(region_id=1, data=data)

        # Assert
        assert result is True


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
