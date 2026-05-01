"""
Cache service for URIS-AI using Redis (Azure Cache for Redis).

Provides caching for frequently accessed data such as risk scores,
recommendations, and region information.

Requirements: 8.1
"""

import json
import logging
from typing import Any, Optional

import redis

from uris_ai.config import settings

logger = logging.getLogger(__name__)

# Cache TTL constants (seconds)
CACHE_TTL_RISK_SCORE = 300       # 5 minutes — risk scores update frequently
CACHE_TTL_RECOMMENDATIONS = 300  # 5 minutes
CACHE_TTL_REGION_LIST = 3600     # 1 hour — region list rarely changes
CACHE_TTL_USER_INFO = 600        # 10 minutes


class CacheService:
    """
    Service for caching data using Redis.

    Wraps the Redis client with typed helpers for common URIS-AI
    cache operations and a graceful fallback when Redis is unavailable.

    Requirements: 8.1
    """

    def __init__(self, redis_client: Optional[redis.Redis] = None):
        """
        Initialize the CacheService.

        Args:
            redis_client: Pre-configured Redis client. If None, a client is
                          created from application settings.
        """
        if redis_client is not None:
            self._client: Optional[redis.Redis] = redis_client
        else:
            self._client = self._create_client()

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _create_client(self) -> Optional[redis.Redis]:
        """Create a Redis client from application settings."""
        try:
            client = redis.Redis(
                host=settings.redis_host,
                port=settings.redis_port,
                password=settings.redis_password,
                ssl=True,
                decode_responses=True,
                socket_connect_timeout=5,
                socket_timeout=5,
            )
            # Verify connectivity
            client.ping()
            logger.info(
                f"Redis connected: {settings.redis_host}:{settings.redis_port}"
            )
            return client
        except Exception as exc:
            logger.warning(
                f"Redis connection failed, caching disabled: {exc}"
            )
            return None

    @property
    def is_available(self) -> bool:
        """Return True if the Redis client is connected."""
        return self._client is not None

    def _safe_get(self, key: str) -> Optional[str]:
        """Get a value from Redis, returning None on any error."""
        if self._client is None:
            return None
        try:
            return self._client.get(key)  # type: ignore[return-value]
        except Exception as exc:
            logger.warning(f"Cache GET error for key '{key}': {exc}")
            return None

    def _safe_set(self, key: str, value: str, ttl: int) -> bool:
        """Set a value in Redis, returning False on any error."""
        if self._client is None:
            return False
        try:
            self._client.setex(key, ttl, value)
            return True
        except Exception as exc:
            logger.warning(f"Cache SET error for key '{key}': {exc}")
            return False

    def _safe_delete(self, key: str) -> bool:
        """Delete a key from Redis, returning False on any error."""
        if self._client is None:
            return False
        try:
            self._client.delete(key)
            return True
        except Exception as exc:
            logger.warning(f"Cache DELETE error for key '{key}': {exc}")
            return False

    # ------------------------------------------------------------------
    # Generic get / set / delete
    # ------------------------------------------------------------------

    def get(self, key: str) -> Optional[Any]:
        """
        Retrieve a cached value by key.

        Args:
            key: Cache key

        Returns:
            Deserialized value, or None if not found / unavailable
        """
        raw = self._safe_get(key)
        if raw is None:
            return None
        try:
            return json.loads(raw)
        except (json.JSONDecodeError, TypeError):
            return raw

    def set(self, key: str, value: Any, ttl: int = 300) -> bool:
        """
        Store a value in the cache.

        Args:
            key: Cache key
            value: Value to cache (must be JSON-serialisable)
            ttl: Time-to-live in seconds (default: 300)

        Returns:
            True if stored successfully, False otherwise
        """
        try:
            serialised = json.dumps(value, default=str)
        except (TypeError, ValueError) as exc:
            logger.warning(f"Cache serialisation error for key '{key}': {exc}")
            return False
        return self._safe_set(key, serialised, ttl)

    def delete(self, key: str) -> bool:
        """
        Remove a key from the cache.

        Args:
            key: Cache key to remove

        Returns:
            True if deleted, False otherwise
        """
        return self._safe_delete(key)

    def delete_pattern(self, pattern: str) -> int:
        """
        Delete all keys matching a pattern.

        Args:
            pattern: Redis glob pattern (e.g. "risk:region:*")

        Returns:
            Number of keys deleted
        """
        if self._client is None:
            return 0
        try:
            keys = list(self._client.scan_iter(pattern))
            if keys:
                return self._client.delete(*keys)
            return 0
        except Exception as exc:
            logger.warning(f"Cache DELETE PATTERN error for '{pattern}': {exc}")
            return 0

    # ------------------------------------------------------------------
    # Domain-specific helpers
    # ------------------------------------------------------------------

    def get_risk_score(self, region_id: int) -> Optional[Any]:
        """Get cached risk score for a region."""
        return self.get(f"risk:region:{region_id}")

    def set_risk_score(self, region_id: int, data: Any) -> bool:
        """Cache risk score for a region."""
        return self.set(f"risk:region:{region_id}", data, CACHE_TTL_RISK_SCORE)

    def get_all_risk_scores(self) -> Optional[Any]:
        """Get cached risk scores for all regions."""
        return self.get("risk:all_regions")

    def set_all_risk_scores(self, data: Any) -> bool:
        """Cache risk scores for all regions."""
        return self.set("risk:all_regions", data, CACHE_TTL_RISK_SCORE)

    def get_risk_trend(self, region_id: int, hours: int) -> Optional[Any]:
        """Get cached risk trend for a region."""
        return self.get(f"risk:trend:{region_id}:{hours}h")

    def set_risk_trend(self, region_id: int, hours: int, data: Any) -> bool:
        """Cache risk trend for a region."""
        return self.set(f"risk:trend:{region_id}:{hours}h", data, CACHE_TTL_RISK_SCORE)

    def get_recommendations(self, region_id: int) -> Optional[Any]:
        """Get cached recommendations for a region."""
        return self.get(f"recommendations:region:{region_id}")

    def set_recommendations(self, region_id: int, data: Any) -> bool:
        """Cache recommendations for a region."""
        return self.set(
            f"recommendations:region:{region_id}", data, CACHE_TTL_RECOMMENDATIONS
        )

    def invalidate_region_cache(self, region_id: int) -> None:
        """Invalidate all cached data for a specific region."""
        self.delete(f"risk:region:{region_id}")
        self.delete(f"recommendations:region:{region_id}")
        self.delete_pattern(f"risk:trend:{region_id}:*")
        self.delete("risk:all_regions")
        logger.debug(f"Cache invalidated for region {region_id}")
