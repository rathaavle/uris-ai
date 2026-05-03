#!/usr/bin/env python3
"""
Data migration script for URIS-AI system.

This script handles schema updates and data transformations when the database
schema changes. It provides a framework for versioned migrations.

Requirements: 7.1

Usage:
    python scripts/migrate_data.py [--version VERSION] [--dry-run]

Options:
    --version VERSION    Target migration version (default: latest)
    --dry-run           Show what would be done without making changes
"""

import argparse
import logging
import sys
from datetime import datetime
from pathlib import Path
from typing import Callable, Dict, List, Optional

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from sqlalchemy import text
from sqlalchemy.orm import Session

from uris_ai.config import settings
from uris_ai.models.database import Base
from uris_ai.models.db_utils import create_db_engine, create_session_factory

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


class Migration:
    """Represents a single migration."""
    
    def __init__(
        self,
        version: str,
        description: str,
        upgrade_func: Callable[[Session], None],
        downgrade_func: Optional[Callable[[Session], None]] = None,
    ):
        """
        Initialize a migration.
        
        Args:
            version: Migration version (e.g., "1.0.0", "1.1.0")
            description: Human-readable description of the migration
            upgrade_func: Function to apply the migration
            downgrade_func: Optional function to rollback the migration
        """
        self.version = version
        self.description = description
        self.upgrade_func = upgrade_func
        self.downgrade_func = downgrade_func
    
    def apply(self, session: Session, dry_run: bool = False) -> None:
        """
        Apply the migration.
        
        Args:
            session: Database session
            dry_run: If True, log what would be done without making changes
        """
        logger.info(f"Applying migration {self.version}: {self.description}")
        
        if dry_run:
            logger.info(f"[DRY RUN] Would apply migration {self.version}")
            return
        
        self.upgrade_func(session)
        self._record_migration(session)
        session.commit()
        
        logger.info(f"Successfully applied migration {self.version}")
    
    def rollback(self, session: Session, dry_run: bool = False) -> None:
        """
        Rollback the migration.
        
        Args:
            session: Database session
            dry_run: If True, log what would be done without making changes
        """
        if self.downgrade_func is None:
            raise ValueError(f"Migration {self.version} does not support rollback")
        
        logger.info(f"Rolling back migration {self.version}: {self.description}")
        
        if dry_run:
            logger.info(f"[DRY RUN] Would rollback migration {self.version}")
            return
        
        self.downgrade_func(session)
        self._remove_migration_record(session)
        session.commit()
        
        logger.info(f"Successfully rolled back migration {self.version}")
    
    def _record_migration(self, session: Session) -> None:
        """Record that this migration has been applied."""
        self._ensure_migration_table(session)
        
        query = text("""
            INSERT INTO schema_migrations (version, description, applied_at)
            VALUES (:version, :description, :applied_at)
        """)
        
        session.execute(
            query,
            {
                "version": self.version,
                "description": self.description,
                "applied_at": datetime.utcnow(),
            },
        )
    
    def _remove_migration_record(self, session: Session) -> None:
        """Remove the record of this migration."""
        query = text("DELETE FROM schema_migrations WHERE version = :version")
        session.execute(query, {"version": self.version})
    
    def _ensure_migration_table(self, session: Session) -> None:
        """Ensure the schema_migrations table exists."""
        engine = session.get_bind()
        dialect_name = engine.dialect.name
        
        if dialect_name == "sqlite":
            # SQLite syntax
            query = text("""
                CREATE TABLE IF NOT EXISTS schema_migrations (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    version VARCHAR(50) NOT NULL UNIQUE,
                    description VARCHAR(255) NOT NULL,
                    applied_at DATETIME NOT NULL
                )
            """)
        else:
            # SQL Server syntax
            query = text("""
                IF NOT EXISTS (SELECT * FROM sys.tables WHERE name = 'schema_migrations')
                BEGIN
                    CREATE TABLE schema_migrations (
                        id INT IDENTITY(1,1) PRIMARY KEY,
                        version VARCHAR(50) NOT NULL UNIQUE,
                        description VARCHAR(255) NOT NULL,
                        applied_at DATETIME NOT NULL
                    )
                END
            """)
        
        session.execute(query)
        session.commit()


# ============================================================================
# Migration Definitions
# ============================================================================

def migration_1_0_0_upgrade(session: Session) -> None:
    """
    Initial schema - baseline migration.
    
    This migration represents the initial database schema.
    """
    logger.info("Creating initial database schema...")
    
    # Create all tables using SQLAlchemy models
    engine = session.get_bind()
    Base.metadata.create_all(bind=engine)


def migration_1_1_0_upgrade(session: Session) -> None:
    """
    Add indexes for performance optimization.
    
    This migration adds additional indexes to improve query performance.
    """
    logger.info("Adding performance indexes...")
    
    engine = session.get_bind()
    dialect_name = engine.dialect.name
    
    # Add index on regions.name for faster lookups
    try:
        if dialect_name == "sqlite":
            session.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_regions_name ON regions(name)
            """))
        else:
            session.execute(text("""
                IF NOT EXISTS (
                    SELECT * FROM sys.indexes 
                    WHERE name = 'idx_regions_name' AND object_id = OBJECT_ID('regions')
                )
                BEGIN
                    CREATE INDEX idx_regions_name ON regions(name)
                END
            """))
    except Exception as e:
        logger.warning(f"Could not create index idx_regions_name: {e}")
    
    # Add composite index on weather_data for common queries
    try:
        if dialect_name == "sqlite":
            session.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_weather_region_date ON weather_data(region_id, date)
            """))
        else:
            session.execute(text("""
                IF NOT EXISTS (
                    SELECT * FROM sys.indexes 
                    WHERE name = 'idx_weather_region_date' AND object_id = OBJECT_ID('weather_data')
                )
                BEGIN
                    CREATE INDEX idx_weather_region_date ON weather_data(region_id, date)
                END
            """))
    except Exception as e:
        logger.warning(f"Could not create index idx_weather_region_date: {e}")


def migration_1_1_0_downgrade(session: Session) -> None:
    """Rollback migration 1.1.0 - remove added indexes."""
    logger.info("Removing performance indexes...")
    
    try:
        session.execute(text("DROP INDEX IF EXISTS idx_regions_name ON regions"))
    except Exception as e:
        logger.warning(f"Could not drop index idx_regions_name: {e}")
    
    try:
        session.execute(text("DROP INDEX IF EXISTS idx_weather_region_date ON weather_data"))
    except Exception as e:
        logger.warning(f"Could not drop index idx_weather_region_date: {e}")


def migration_1_2_0_upgrade(session: Session) -> None:
    """
    Add audit columns to critical tables.
    
    This migration adds created_by and updated_by columns for audit trail.
    """
    logger.info("Adding audit columns...")
    
    engine = session.get_bind()
    dialect_name = engine.dialect.name
    
    tables_to_update = ["regions", "public_facilities", "roads"]
    
    for table in tables_to_update:
        try:
            if dialect_name == "sqlite":
                # SQLite: Check if columns exist using PRAGMA
                result = session.execute(text(f"PRAGMA table_info({table})"))
                columns = [row[1] for row in result]
                
                if "created_by" not in columns:
                    session.execute(text(f"ALTER TABLE {table} ADD COLUMN created_by VARCHAR(100)"))
                    logger.info(f"Added created_by column to {table}")
                
                if "updated_by" not in columns:
                    session.execute(text(f"ALTER TABLE {table} ADD COLUMN updated_by VARCHAR(100)"))
                    logger.info(f"Added updated_by column to {table}")
            else:
                # SQL Server: Check if columns exist
                check_query = text(f"""
                    SELECT COUNT(*) as cnt
                    FROM sys.columns 
                    WHERE object_id = OBJECT_ID('{table}') 
                    AND name IN ('created_by', 'updated_by')
                """)
                result = session.execute(check_query).fetchone()
                
                if result.cnt == 0:
                    # Add columns
                    session.execute(text(f"""
                        ALTER TABLE {table}
                        ADD created_by VARCHAR(100) NULL,
                            updated_by VARCHAR(100) NULL
                    """))
                    logger.info(f"Added audit columns to {table}")
                else:
                    logger.info(f"Audit columns already exist in {table}")
                    
        except Exception as e:
            logger.warning(f"Could not add audit columns to {table}: {e}")


def migration_1_2_0_downgrade(session: Session) -> None:
    """Rollback migration 1.2.0 - remove audit columns."""
    logger.info("Removing audit columns...")
    
    engine = session.get_bind()
    dialect_name = engine.dialect.name
    
    tables_to_update = ["regions", "public_facilities", "roads"]
    
    for table in tables_to_update:
        try:
            if dialect_name == "sqlite":
                # SQLite doesn't support DROP COLUMN easily, skip for tests
                logger.warning(f"SQLite doesn't support DROP COLUMN for {table}, skipping")
            else:
                session.execute(text(f"""
                    ALTER TABLE {table}
                    DROP COLUMN IF EXISTS created_by, updated_by
                """))
                logger.info(f"Removed audit columns from {table}")
        except Exception as e:
            logger.warning(f"Could not remove audit columns from {table}: {e}")


def migration_1_3_0_upgrade(session: Session) -> None:
    """
    Transform legacy flood severity data.
    
    This migration updates flood severity values to ensure consistency.
    Converts any out-of-range severity values to valid range (1-4).
    """
    logger.info("Transforming flood severity data...")
    
    try:
        # Check for any invalid severity values
        check_query = text("""
            SELECT COUNT(*) as cnt
            FROM flood_events
            WHERE severity < 1 OR severity > 4
        """)
        result = session.execute(check_query).fetchone()
        
        if result.cnt > 0:
            logger.info(f"Found {result.cnt} flood events with invalid severity")
            
            # Normalize severity values
            session.execute(text("""
                UPDATE flood_events
                SET severity = CASE
                    WHEN severity < 1 THEN 1
                    WHEN severity > 4 THEN 4
                    ELSE severity
                END
                WHERE severity < 1 OR severity > 4
            """))
            
            logger.info(f"Normalized {result.cnt} flood event severity values")
        else:
            logger.info("All flood event severity values are valid")
            
    except Exception as e:
        logger.error(f"Error transforming flood severity data: {e}")
        raise


# ============================================================================
# Migration Registry
# ============================================================================

MIGRATIONS: List[Migration] = [
    Migration(
        version="1.0.0",
        description="Initial database schema",
        upgrade_func=migration_1_0_0_upgrade,
    ),
    Migration(
        version="1.1.0",
        description="Add performance indexes",
        upgrade_func=migration_1_1_0_upgrade,
        downgrade_func=migration_1_1_0_downgrade,
    ),
    Migration(
        version="1.2.0",
        description="Add audit columns",
        upgrade_func=migration_1_2_0_upgrade,
        downgrade_func=migration_1_2_0_downgrade,
    ),
    Migration(
        version="1.3.0",
        description="Transform legacy flood severity data",
        upgrade_func=migration_1_3_0_upgrade,
    ),
]


# ============================================================================
# Migration Management
# ============================================================================

def get_applied_migrations(session: Session) -> List[str]:
    """
    Get list of applied migration versions.
    
    Args:
        session: Database session
        
    Returns:
        List of applied migration versions
    """
    # Ensure migration table exists
    Migration("0.0.0", "dummy", lambda s: None)._ensure_migration_table(session)
    
    query = text("SELECT version FROM schema_migrations ORDER BY applied_at")
    result = session.execute(query)
    
    return [row.version for row in result]


def get_pending_migrations(session: Session, target_version: Optional[str] = None) -> List[Migration]:
    """
    Get list of pending migrations to apply.
    
    Args:
        session: Database session
        target_version: Target version to migrate to (None = latest)
        
    Returns:
        List of pending migrations
    """
    applied = get_applied_migrations(session)
    
    pending = []
    for migration in MIGRATIONS:
        if migration.version not in applied:
            pending.append(migration)
            
            # Stop if we've reached the target version
            if target_version and migration.version == target_version:
                break
    
    return pending


def apply_migrations(
    session: Session,
    target_version: Optional[str] = None,
    dry_run: bool = False,
) -> None:
    """
    Apply pending migrations.
    
    Args:
        session: Database session
        target_version: Target version to migrate to (None = latest)
        dry_run: If True, show what would be done without making changes
    """
    pending = get_pending_migrations(session, target_version)
    
    if not pending:
        logger.info("No pending migrations to apply")
        return
    
    logger.info(f"Found {len(pending)} pending migration(s)")
    
    for migration in pending:
        migration.apply(session, dry_run=dry_run)
    
    if not dry_run:
        logger.info("All migrations applied successfully")


def rollback_migration(
    session: Session,
    version: str,
    dry_run: bool = False,
) -> None:
    """
    Rollback a specific migration.
    
    Args:
        session: Database session
        version: Version to rollback
        dry_run: If True, show what would be done without making changes
    """
    # Find the migration
    migration = None
    for m in MIGRATIONS:
        if m.version == version:
            migration = m
            break
    
    if migration is None:
        raise ValueError(f"Migration version {version} not found")
    
    # Check if it's applied
    applied = get_applied_migrations(session)
    if version not in applied:
        logger.warning(f"Migration {version} is not applied")
        return
    
    migration.rollback(session, dry_run=dry_run)


def show_migration_status(session: Session) -> None:
    """
    Show the status of all migrations.
    
    Args:
        session: Database session
    """
    applied = get_applied_migrations(session)
    
    logger.info("Migration Status:")
    logger.info("-" * 80)
    
    for migration in MIGRATIONS:
        status = "✓ Applied" if migration.version in applied else "✗ Pending"
        logger.info(f"{status:12} | {migration.version:10} | {migration.description}")
    
    logger.info("-" * 80)


def main():
    """Main function to run data migrations."""
    parser = argparse.ArgumentParser(description="Run data migrations for URIS-AI system")
    parser.add_argument(
        "--version",
        type=str,
        help="Target migration version (default: latest)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be done without making changes",
    )
    parser.add_argument(
        "--rollback",
        type=str,
        help="Rollback a specific migration version",
    )
    parser.add_argument(
        "--status",
        action="store_true",
        help="Show migration status",
    )
    args = parser.parse_args()
    
    try:
        # Create database engine and session
        logger.info("Connecting to database...")
        engine = create_db_engine(settings.azure_sql_connection_string)
        session_factory = create_session_factory(engine)
        session = session_factory()
        
        try:
            if args.status:
                # Show migration status
                show_migration_status(session)
            elif args.rollback:
                # Rollback a migration
                rollback_migration(session, args.rollback, dry_run=args.dry_run)
            else:
                # Apply migrations
                apply_migrations(session, target_version=args.version, dry_run=args.dry_run)
            
        finally:
            session.close()
            
    except Exception as e:
        logger.error(f"Error during migration: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
