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

    # ------------------------------------------------------------------
    # Cache warming strategies
    # ------------------------------------------------------------------

    def warm_risk_scores_cache(self, db_session) -> dict:
        """
        Warm cache with all region risk scores.
        
        This preloads frequently accessed risk score data into cache
        to improve response times for initial requests.
        
        Requirements: 8.1
        
        Args:
            db_session: SQLAlchemy database session
            
        Returns:
            Dictionary with warming results
        """
        from uris_ai.models.database import Region, RiskScore
        from uris_ai.ml.flood_risk_engine import FloodRiskEngine
        
        results = {
            "success": True,
            "regions_warmed": 0,
            "errors": []
        }
        
        try:
            # Get all regions
            regions = db_session.query(Region).all()
            flood_engine = FloodRiskEngine()
            
            all_risk_scores = []
            
            for region in regions:
                try:
                    # Get latest risk score for each region
                    latest = (
                        db_session.query(RiskScore)
                        .filter(RiskScore.region_id == region.region_id)
                        .order_by(RiskScore.date.desc())
                        .first()
                    )
                    
                    if latest:
                        risk_data = {
                            "region_id": latest.region_id,
                            "region_name": region.name,
                            "flood_risk": latest.flood_risk,
                            "traffic_impact": latest.traffic_impact,
                            "service_access": latest.service_access,
                            "urban_risk_score": latest.urban_risk_score,
                            "risk_category": flood_engine.get_risk_category(
                                latest.urban_risk_score
                            ).value,
                            "calculated_at": latest.date.isoformat(),
                        }
                        
                        # Cache individual region risk score
                        self.set_risk_score(region.region_id, risk_data)
                        all_risk_scores.append(risk_data)
                        results["regions_warmed"] += 1
                        
                except Exception as e:
                    logger.warning(f"Failed to warm cache for region {region.region_id}: {e}")
                    results["errors"].append({
                        "region_id": region.region_id,
                        "error": str(e)
                    })
            
            # Cache all regions risk scores
            if all_risk_scores:
                from datetime import datetime, timezone
                all_data = {
                    "regions": all_risk_scores,
                    "total": len(all_risk_scores),
                    "updated_at": datetime.now(timezone.utc).isoformat()
                }
                self.set_all_risk_scores(all_data)
            
            logger.info(f"Cache warming completed: {results['regions_warmed']} regions")
            
        except Exception as e:
            logger.error(f"Cache warming failed: {e}")
            results["success"] = False
            results["errors"].append({"general": str(e)})
        
        return results

    def warm_recommendations_cache(self, db_session) -> dict:
        """
        Warm cache with active recommendations for all regions.
        
        Requirements: 8.1
        
        Args:
            db_session: SQLAlchemy database session
            
        Returns:
            Dictionary with warming results
        """
        from uris_ai.models.database import Region, Recommendation
        
        results = {
            "success": True,
            "regions_warmed": 0,
            "errors": []
        }
        
        try:
            # Get all regions with active recommendations
            regions = db_session.query(Region).all()
            
            for region in regions:
                try:
                    # Get active recommendations for region
                    recommendations = (
                        db_session.query(Recommendation)
                        .filter(
                            Recommendation.region_id == region.region_id,
                            Recommendation.is_active == True
                        )
                        .order_by(Recommendation.created_at.desc())
                        .limit(10)
                        .all()
                    )
                    
                    if recommendations:
                        rec_data = [
                            {
                                "id": rec.id,
                                "region_id": rec.region_id,
                                "recommendation_type": rec.recommendation_type,
                                "description": rec.description,
                                "urgency_level": rec.urgency_level,
                                "created_at": rec.created_at.isoformat(),
                                "expires_at": rec.expires_at.isoformat() if rec.expires_at else None,
                                "is_active": rec.is_active
                            }
                            for rec in recommendations
                        ]
                        
                        # Cache recommendations
                        self.set_recommendations(region.region_id, rec_data)
                        results["regions_warmed"] += 1
                        
                except Exception as e:
                    logger.warning(f"Failed to warm recommendations cache for region {region.region_id}: {e}")
                    results["errors"].append({
                        "region_id": region.region_id,
                        "error": str(e)
                    })
            
            logger.info(f"Recommendations cache warming completed: {results['regions_warmed']} regions")
            
        except Exception as e:
            logger.error(f"Recommendations cache warming failed: {e}")
            results["success"] = False
            results["errors"].append({"general": str(e)})
        
        return results

    def warm_all_caches(self, db_session) -> dict:
        """
        Warm all caches with frequently accessed data.
        
        This should be called on application startup or after
        cache invalidation to ensure optimal performance.
        
        Requirements: 8.1
        
        Args:
            db_session: SQLAlchemy database session
            
        Returns:
            Dictionary with combined warming results
        """
        logger.info("Starting cache warming for all data...")
        
        risk_results = self.warm_risk_scores_cache(db_session)
        rec_results = self.warm_recommendations_cache(db_session)
        
        combined_results = {
            "success": risk_results["success"] and rec_results["success"],
            "risk_scores": risk_results,
            "recommendations": rec_results,
            "total_regions_warmed": risk_results["regions_warmed"] + rec_results["regions_warmed"]
        }
        
        logger.info(f"Cache warming completed: {combined_results['total_regions_warmed']} total operations")
        
        return combined_results

    def get_cache_stats(self) -> dict:
        """
        Get cache statistics and health information.
        
        Returns:
            Dictionary with cache statistics
        """
        if self._client is None:
            return {
                "available": False,
                "error": "Redis client not connected"
            }
        
        try:
            info = self._client.info()
            
            return {
                "available": True,
                "connected_clients": info.get("connected_clients", 0),
                "used_memory": info.get("used_memory_human", "N/A"),
                "total_keys": self._client.dbsize(),
                "hit_rate": self._calculate_hit_rate(info),
                "uptime_seconds": info.get("uptime_in_seconds", 0)
            }
        except Exception as e:
            logger.error(f"Failed to get cache stats: {e}")
            return {
                "available": False,
                "error": str(e)
            }

    def _calculate_hit_rate(self, info: dict) -> float:
        """Calculate cache hit rate from Redis info."""
        hits = info.get("keyspace_hits", 0)
        misses = info.get("keyspace_misses", 0)
        total = hits + misses
        
        if total == 0:
            return 0.0
        
        return round((hits / total) * 100, 2)
