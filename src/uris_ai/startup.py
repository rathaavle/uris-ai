"""
Application startup tasks for URIS-AI.

Handles initialization tasks that should run when the application starts,
including cache warming and database optimization.

Requirements: 8.1
"""

import logging
from typing import Optional

from sqlalchemy.orm import Session

from uris_ai.database.db_utils import create_performance_indexes
from uris_ai.services.cache_service import CacheService

logger = logging.getLogger(__name__)


def initialize_performance_optimizations(
    db_session: Session,
    cache_service: Optional[CacheService] = None,
    create_indexes: bool = True,
    warm_cache: bool = True
) -> dict:
    """
    Initialize performance optimizations on application startup.
    
    This function should be called when the application starts to:
    1. Create performance indexes in the database
    2. Warm the cache with frequently accessed data
    
    Requirements: 8.1
    
    Args:
        db_session: SQLAlchemy database session
        cache_service: CacheService instance (creates new if None)
        create_indexes: Whether to create performance indexes
        warm_cache: Whether to warm the cache
        
    Returns:
        Dictionary with initialization results
    """
    results = {
        "success": True,
        "indexes": None,
        "cache": None,
        "errors": []
    }
    
    logger.info("Starting performance optimization initialization...")
    
    # Create performance indexes
    if create_indexes:
        try:
            logger.info("Creating performance indexes...")
            index_results = create_performance_indexes(db_session)
            results["indexes"] = index_results
            
            if index_results["created"]:
                logger.info(f"Created {len(index_results['created'])} new indexes")
            if index_results["already_exists"]:
                logger.info(f"{len(index_results['already_exists'])} indexes already exist")
            if index_results["failed"]:
                logger.warning(f"Failed to create {len(index_results['failed'])} indexes")
                results["errors"].extend(index_results["failed"])
                
        except Exception as e:
            logger.error(f"Failed to create performance indexes: {e}")
            results["errors"].append({"indexes": str(e)})
            results["success"] = False
    
    # Warm cache
    if warm_cache:
        try:
            logger.info("Warming cache with frequently accessed data...")
            
            if cache_service is None:
                cache_service = CacheService()
            
            if not cache_service.is_available:
                logger.warning("Cache service not available, skipping cache warming")
                results["cache"] = {
                    "success": False,
                    "error": "Cache service not available"
                }
            else:
                cache_results = cache_service.warm_all_caches(db_session)
                results["cache"] = cache_results
                
                if cache_results["success"]:
                    logger.info(
                        f"Cache warming completed: {cache_results['total_regions_warmed']} operations"
                    )
                else:
                    logger.warning("Cache warming completed with errors")
                    results["errors"].extend(cache_results.get("errors", []))
                    
        except Exception as e:
            logger.error(f"Failed to warm cache: {e}")
            results["errors"].append({"cache": str(e)})
            results["success"] = False
    
    if results["success"]:
        logger.info("Performance optimization initialization completed successfully")
    else:
        logger.warning(
            f"Performance optimization initialization completed with {len(results['errors'])} errors"
        )
    
    return results


def startup_event_handler(db_session: Session) -> None:
    """
    FastAPI startup event handler.
    
    This function is called by FastAPI when the application starts.
    It initializes performance optimizations.
    
    Args:
        db_session: SQLAlchemy database session
    """
    logger.info("Application startup: Initializing performance optimizations")
    
    try:
        results = initialize_performance_optimizations(
            db_session=db_session,
            create_indexes=True,
            warm_cache=True
        )
        
        if not results["success"]:
            logger.warning(
                f"Startup completed with errors: {len(results['errors'])} issues"
            )
        else:
            logger.info("Application startup completed successfully")
            
    except Exception as e:
        logger.error(f"Startup event handler failed: {e}")
        # Don't raise - allow application to start even if optimization fails


def get_startup_status(db_session: Session) -> dict:
    """
    Get the status of startup optimizations.
    
    This can be used in health check endpoints to verify that
    performance optimizations are in place.
    
    Args:
        db_session: SQLAlchemy database session
        
    Returns:
        Dictionary with optimization status
    """
    from uris_ai.database.db_utils import get_index_usage_stats
    
    status = {
        "indexes": {
            "available": False,
            "count": 0
        },
        "cache": {
            "available": False,
            "stats": {}
        }
    }
    
    # Check indexes
    try:
        index_stats = get_index_usage_stats(db_session)
        status["indexes"]["available"] = True
        status["indexes"]["count"] = len(index_stats)
    except Exception as e:
        logger.error(f"Failed to get index stats: {e}")
    
    # Check cache
    try:
        cache = CacheService()
        if cache.is_available:
            status["cache"]["available"] = True
            status["cache"]["stats"] = cache.get_cache_stats()
    except Exception as e:
        logger.error(f"Failed to get cache stats: {e}")
    
    return status
