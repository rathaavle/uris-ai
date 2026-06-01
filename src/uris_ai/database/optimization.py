"""
Database utility functions for performance optimization.

Provides utilities for query optimization, index management,
and database performance monitoring.

Requirements: 8.1
"""

import logging
from typing import List, Dict, Any
from sqlalchemy import text
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)


def create_performance_indexes(db_session: Session) -> Dict[str, Any]:
    """
    Create additional performance indexes for frequently accessed queries.
    
    This function adds indexes that are not part of the base schema but
    improve query performance for common access patterns.
    
    Requirements: 8.1
    
    Args:
        db_session: SQLAlchemy database session
        
    Returns:
        Dictionary with results of index creation operations
    """
    results = {
        "created": [],
        "failed": [],
        "already_exists": []
    }
    
    # Index definitions for performance optimization
    indexes = [
        # Weather data - frequently queried by date range
        {
            "name": "idx_weather_date_desc",
            "table": "weather_data",
            "columns": "date DESC",
            "reason": "Optimize latest weather data queries"
        },
        # Flood events - frequently queried by severity
        {
            "name": "idx_flood_severity",
            "table": "flood_events",
            "columns": "severity",
            "reason": "Optimize queries filtering by severity level"
        },
        # Risk scores - frequently queried by date range for trends
        {
            "name": "idx_risk_date_desc",
            "table": "risk_scores",
            "columns": "date DESC",
            "reason": "Optimize latest risk score queries"
        },
        # Risk scores - composite index for region + date range queries
        {
            "name": "idx_risk_region_date_desc",
            "table": "risk_scores",
            "columns": "region_id, date DESC",
            "reason": "Optimize region-specific trend queries"
        },
        # Recommendations - frequently queried by active status and urgency
        {
            "name": "idx_recommendations_active_urgency",
            "table": "recommendations",
            "columns": "is_active, urgency_level",
            "reason": "Optimize active recommendations queries"
        },
        # Recommendations - frequently queried by expiration
        {
            "name": "idx_recommendations_expires",
            "table": "recommendations",
            "columns": "expires_at",
            "reason": "Optimize expired recommendations cleanup"
        },
        # Public facilities - spatial queries by coordinates
        {
            "name": "idx_facilities_coords",
            "table": "public_facilities",
            "columns": "latitude, longitude",
            "reason": "Optimize spatial proximity queries"
        },
        # Public facilities - frequently queried by operational status
        {
            "name": "idx_facilities_operational",
            "table": "public_facilities",
            "columns": "is_operational",
            "reason": "Optimize operational facilities queries"
        },
        # Roads - frequently queried by main road status
        {
            "name": "idx_roads_main",
            "table": "roads",
            "columns": "is_main_road",
            "reason": "Optimize main road queries"
        },
        # Users - frequently queried by active status
        {
            "name": "idx_users_active",
            "table": "users",
            "columns": "is_active",
            "reason": "Optimize active users queries"
        }
    ]
    
    for idx in indexes:
        try:
            # Check if index already exists
            check_query = text(f"""
                SELECT COUNT(*) as cnt
                FROM sys.indexes
                WHERE name = :index_name
            """)
            result = db_session.execute(check_query, {"index_name": idx["name"]}).fetchone()
            
            if result and result[0] > 0:
                logger.info(f"Index {idx['name']} already exists, skipping")
                results["already_exists"].append(idx["name"])
                continue
            
            # Create index
            create_query = text(f"""
                CREATE INDEX {idx['name']}
                ON {idx['table']} ({idx['columns']})
            """)
            db_session.execute(create_query)
            db_session.commit()
            
            logger.info(f"Created index {idx['name']} on {idx['table']} - {idx['reason']}")
            results["created"].append({
                "name": idx["name"],
                "table": idx["table"],
                "reason": idx["reason"]
            })
            
        except Exception as e:
            logger.error(f"Failed to create index {idx['name']}: {e}")
            results["failed"].append({
                "name": idx["name"],
                "error": str(e)
            })
            db_session.rollback()
    
    return results


def analyze_query_performance(db_session: Session, query_text: str) -> Dict[str, Any]:
    """
    Analyze query execution plan for performance insights.
    
    Args:
        db_session: SQLAlchemy database session
        query_text: SQL query to analyze
        
    Returns:
        Dictionary with query execution plan details
    """
    try:
        # Get execution plan
        explain_query = text(f"SET SHOWPLAN_TEXT ON; {query_text}; SET SHOWPLAN_TEXT OFF;")
        result = db_session.execute(explain_query)
        
        plan = []
        for row in result:
            plan.append(str(row))
        
        return {
            "success": True,
            "plan": plan
        }
    except Exception as e:
        logger.error(f"Failed to analyze query: {e}")
        return {
            "success": False,
            "error": str(e)
        }


def get_slow_queries(db_session: Session, min_duration_ms: int = 1000) -> List[Dict[str, Any]]:
    """
    Retrieve slow queries from SQL Server query store.
    
    Args:
        db_session: SQLAlchemy database session
        min_duration_ms: Minimum query duration in milliseconds
        
    Returns:
        List of slow queries with execution statistics
    """
    try:
        query = text("""
            SELECT TOP 20
                q.query_id,
                qt.query_sql_text,
                rs.avg_duration / 1000.0 as avg_duration_ms,
                rs.max_duration / 1000.0 as max_duration_ms,
                rs.count_executions,
                rs.last_execution_time
            FROM sys.query_store_query q
            JOIN sys.query_store_query_text qt ON q.query_text_id = qt.query_text_id
            JOIN sys.query_store_plan p ON q.query_id = p.query_id
            JOIN sys.query_store_runtime_stats rs ON p.plan_id = rs.plan_id
            WHERE rs.avg_duration / 1000.0 > :min_duration
            ORDER BY rs.avg_duration DESC
        """)
        
        result = db_session.execute(query, {"min_duration": min_duration_ms})
        
        slow_queries = []
        for row in result:
            slow_queries.append({
                "query_id": row[0],
                "query_text": row[1],
                "avg_duration_ms": float(row[2]),
                "max_duration_ms": float(row[3]),
                "execution_count": row[4],
                "last_execution": row[5]
            })
        
        return slow_queries
        
    except Exception as e:
        logger.error(f"Failed to retrieve slow queries: {e}")
        return []


def optimize_table_statistics(db_session: Session, table_name: str) -> bool:
    """
    Update statistics for a table to improve query optimizer decisions.
    
    Args:
        db_session: SQLAlchemy database session
        table_name: Name of the table to update statistics for
        
    Returns:
        True if successful, False otherwise
    """
    try:
        query = text(f"UPDATE STATISTICS {table_name} WITH FULLSCAN")
        db_session.execute(query)
        db_session.commit()
        
        logger.info(f"Updated statistics for table {table_name}")
        return True
        
    except Exception as e:
        logger.error(f"Failed to update statistics for {table_name}: {e}")
        db_session.rollback()
        return False


def get_index_usage_stats(db_session: Session) -> List[Dict[str, Any]]:
    """
    Get index usage statistics to identify unused or underutilized indexes.
    
    Args:
        db_session: SQLAlchemy database session
        
    Returns:
        List of indexes with usage statistics
    """
    try:
        query = text("""
            SELECT 
                OBJECT_NAME(s.object_id) as table_name,
                i.name as index_name,
                s.user_seeks,
                s.user_scans,
                s.user_lookups,
                s.user_updates,
                s.last_user_seek,
                s.last_user_scan
            FROM sys.dm_db_index_usage_stats s
            JOIN sys.indexes i ON s.object_id = i.object_id AND s.index_id = i.index_id
            WHERE OBJECTPROPERTY(s.object_id, 'IsUserTable') = 1
            ORDER BY s.user_seeks + s.user_scans + s.user_lookups DESC
        """)
        
        result = db_session.execute(query)
        
        stats = []
        for row in result:
            stats.append({
                "table_name": row[0],
                "index_name": row[1],
                "user_seeks": row[2],
                "user_scans": row[3],
                "user_lookups": row[4],
                "user_updates": row[5],
                "last_user_seek": row[6],
                "last_user_scan": row[7]
            })
        
        return stats
        
    except Exception as e:
        logger.error(f"Failed to retrieve index usage stats: {e}")
        return []
