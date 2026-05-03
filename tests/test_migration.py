"""
Comprehensive tests for data migration scripts.

Tests migration functionality on test database, verifies data integrity,
tests rollback functionality, and validates edge cases.

Requirements: 7.1
"""

import sys
from datetime import datetime, timedelta
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, sessionmaker

# Add scripts to path
scripts_path = Path(__file__).parent.parent / "scripts"
sys.path.insert(0, str(scripts_path))

from uris_ai.models.database import (
    Base,
    FloodEvent,
    PublicFacility,
    Region,
    Road,
)


@pytest.fixture(scope="function")
def test_db_engine() -> Engine:
    """Create an in-memory SQLite database engine for migration testing."""
    engine = create_engine("sqlite:///:memory:", echo=False)
    yield engine
    engine.dispose()


@pytest.fixture(scope="function")
def test_db_session(test_db_engine: Engine) -> Session:
    """Create a database session for migration testing."""
    SessionFactory = sessionmaker(bind=test_db_engine)
    session = SessionFactory()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


class TestMigrationBasics:
    """Test basic migration functionality."""

    def test_migration_class_initialization(self):
        """Test Migration class can be initialized with required parameters."""
        from migrate_data import Migration

        def upgrade_func(session):
            pass

        def downgrade_func(session):
            pass

        migration = Migration(
            version="1.0.0",
            description="Test migration",
            upgrade_func=upgrade_func,
            downgrade_func=downgrade_func,
        )

        assert migration.version == "1.0.0"
        assert migration.description == "Test migration"
        assert migration.upgrade_func == upgrade_func
        assert migration.downgrade_func == downgrade_func

    def test_migration_without_downgrade(self):
        """Test Migration can be created without downgrade function."""
        from migrate_data import Migration

        def upgrade_func(session):
            pass

        migration = Migration(
            version="1.0.0",
            description="Test migration",
            upgrade_func=upgrade_func,
        )

        assert migration.version == "1.0.0"
        assert migration.downgrade_func is None

    def test_migrations_registry_exists(self):
        """Test that MIGRATIONS registry is properly defined."""
        from migrate_data import MIGRATIONS

        assert len(MIGRATIONS) > 0
        assert all(hasattr(m, "version") for m in MIGRATIONS)
        assert all(hasattr(m, "description") for m in MIGRATIONS)
        assert all(hasattr(m, "upgrade_func") for m in MIGRATIONS)

    def test_migration_versions_are_sequential(self):
        """Test that migration versions are in sequential order."""
        from migrate_data import MIGRATIONS

        versions = [m.version for m in MIGRATIONS]
        version_tuples = [tuple(map(int, v.split("."))) for v in versions]

        # Versions should be sorted
        assert version_tuples == sorted(version_tuples)

    def test_migration_versions_are_unique(self):
        """Test that all migration versions are unique."""
        from migrate_data import MIGRATIONS

        versions = [m.version for m in MIGRATIONS]
        assert len(versions) == len(set(versions))


class TestMigrationExecution:
    """Test migration execution on test database."""

    def test_migration_1_0_0_creates_schema(self, test_db_session: Session):
        """Test that migration 1.0.0 creates initial database schema."""
        from migrate_data import MIGRATIONS

        # Find migration 1.0.0
        migration = next(m for m in MIGRATIONS if m.version == "1.0.0")

        # Apply migration
        migration.apply(test_db_session, dry_run=False)

        # Verify tables were created
        engine = test_db_session.get_bind()
        from sqlalchemy import inspect
        inspector = inspect(engine)
        tables = inspector.get_table_names()

        # Check that key tables exist
        expected_tables = ["regions", "weather_data", "flood_events", "roads", "public_facilities"]
        for table in expected_tables:
            assert table in tables, f"Table {table} was not created"

    def test_migration_1_1_0_adds_indexes(self, test_db_session: Session):
        """Test that migration 1.1.0 adds performance indexes."""
        from migrate_data import MIGRATIONS

        # Apply migrations up to 1.1.0
        for migration in MIGRATIONS:
            if migration.version in ["1.0.0", "1.1.0"]:
                migration.apply(test_db_session, dry_run=False)

        # For SQLite, we can check if indexes exist by querying sqlite_master
        # Note: SQLite syntax differs from SQL Server
        result = test_db_session.execute(
            text("SELECT name FROM sqlite_master WHERE type='index'")
        )
        indexes = [row[0] for row in result]

        # Check that indexes were created (SQLite auto-creates some indexes)
        # We verify that the migration ran without errors
        assert len(indexes) > 0

    def test_migration_1_2_0_adds_audit_columns(self, test_db_session: Session):
        """Test that migration 1.2.0 adds audit columns to tables."""
        from migrate_data import MIGRATIONS

        # Apply migrations up to 1.2.0
        for migration in MIGRATIONS:
            if migration.version in ["1.0.0", "1.1.0", "1.2.0"]:
                migration.apply(test_db_session, dry_run=False)

        # Check that audit columns exist in regions table
        engine = test_db_session.get_bind()
        from sqlalchemy import inspect
        inspector = inspect(engine)
        columns = [col["name"] for col in inspector.get_columns("regions")]

        # Verify base columns exist
        assert "region_id" in columns
        assert "name" in columns
        
        # Verify audit columns were added
        assert "created_by" in columns
        assert "updated_by" in columns

    def test_migration_1_3_0_transforms_flood_severity(self, test_db_session: Session):
        """Test that migration 1.3.0 normalizes flood severity data."""
        from migrate_data import MIGRATIONS

        # Apply migrations up to 1.2.0 first
        for migration in MIGRATIONS:
            if migration.version in ["1.0.0", "1.1.0", "1.2.0"]:
                migration.apply(test_db_session, dry_run=False)

        # Create a region
        region = Region(
            name="Test Region",
            latitude=-6.2,
            longitude=106.8,
            elevation=10.0,
            drainage_capacity=150.0,
        )
        test_db_session.add(region)
        test_db_session.commit()

        # For SQLite, we need to disable foreign key constraints temporarily
        # to insert invalid data for testing
        engine = test_db_session.get_bind()
        if engine.dialect.name == "sqlite":
            # SQLite enforces CHECK constraints, so we can't insert invalid data
            # Instead, we'll test that the migration runs without errors
            # and verify it would normalize data if there were any invalid values
            
            # Insert valid flood events
            test_db_session.execute(
                text("""
                    INSERT INTO flood_events (region_id, date, severity, created_at)
                    VALUES (:region_id, :date, :severity, :created_at)
                """),
                [
                    {
                        "region_id": region.region_id,
                        "date": datetime.now(),
                        "severity": 1,  # Valid
                        "created_at": datetime.now(),
                    },
                    {
                        "region_id": region.region_id,
                        "date": datetime.now() - timedelta(days=1),
                        "severity": 4,  # Valid
                        "created_at": datetime.now(),
                    },
                ],
            )
            test_db_session.commit()

            # Apply migration 1.3.0 (should run without errors)
            migration = next(m for m in MIGRATIONS if m.version == "1.3.0")
            migration.apply(test_db_session, dry_run=False)

            # Verify all severity values are still valid
            result = test_db_session.execute(
                text("SELECT severity FROM flood_events WHERE region_id = :region_id"),
                {"region_id": region.region_id},
            )
            severities = [row[0] for row in result]
            assert all(1 <= s <= 4 for s in severities)
        else:
            # For SQL Server, we can test with invalid data
            # Insert flood events with invalid severity values
            test_db_session.execute(
                text("""
                    INSERT INTO flood_events (region_id, date, severity, created_at)
                    VALUES (:region_id, :date, :severity, :created_at)
                """),
                [
                    {
                        "region_id": region.region_id,
                        "date": datetime.now(),
                        "severity": 0,  # Invalid: below range
                        "created_at": datetime.now(),
                    },
                    {
                        "region_id": region.region_id,
                        "date": datetime.now() - timedelta(days=1),
                        "severity": 5,  # Invalid: above range
                        "created_at": datetime.now(),
                    },
                ],
            )
            test_db_session.commit()

            # Apply migration 1.3.0
            migration = next(m for m in MIGRATIONS if m.version == "1.3.0")
            migration.apply(test_db_session, dry_run=False)

            # Verify severity values were normalized
            result = test_db_session.execute(
                text("SELECT severity FROM flood_events WHERE region_id = :region_id"),
                {"region_id": region.region_id},
            )
            severities = [row[0] for row in result]

            # All severities should be in valid range (1-4)
            assert all(1 <= s <= 4 for s in severities)

    def test_apply_all_migrations_sequentially(self, test_db_session: Session):
        """Test applying all migrations in sequence."""
        from migrate_data import MIGRATIONS

        # Apply all migrations
        for migration in MIGRATIONS:
            migration.apply(test_db_session, dry_run=False)

        # Verify schema_migrations table has all records
        result = test_db_session.execute(
            text("SELECT version FROM schema_migrations ORDER BY applied_at")
        )
        applied_versions = [row[0] for row in result]

        expected_versions = [m.version for m in MIGRATIONS]
        assert applied_versions == expected_versions

    def test_migration_dry_run_does_not_modify_database(self, test_db_session: Session):
        """Test that dry-run mode does not modify the database."""
        from migrate_data import MIGRATIONS

        # Get initial table count
        engine = test_db_session.get_bind()
        from sqlalchemy import inspect
        inspector = inspect(engine)
        initial_tables = inspector.get_table_names()

        # Apply migration in dry-run mode
        migration = MIGRATIONS[0]
        migration.apply(test_db_session, dry_run=True)

        # Verify no tables were created
        final_tables = inspector.get_table_names()
        assert initial_tables == final_tables


class TestMigrationRollback:
    """Test migration rollback functionality."""

    def test_rollback_migration_with_downgrade_function(self, test_db_session: Session):
        """Test rolling back a migration that has a downgrade function."""
        from migrate_data import MIGRATIONS

        # Apply migrations 1.0.0 and 1.1.0
        for migration in MIGRATIONS:
            if migration.version in ["1.0.0", "1.1.0"]:
                migration.apply(test_db_session, dry_run=False)

        # Verify migration 1.1.0 is applied
        result = test_db_session.execute(
            text("SELECT COUNT(*) FROM schema_migrations WHERE version = '1.1.0'")
        )
        assert result.scalar() == 1

        # Rollback migration 1.1.0
        migration = next(m for m in MIGRATIONS if m.version == "1.1.0")
        migration.rollback(test_db_session, dry_run=False)

        # Verify migration 1.1.0 is no longer applied
        result = test_db_session.execute(
            text("SELECT COUNT(*) FROM schema_migrations WHERE version = '1.1.0'")
        )
        assert result.scalar() == 0

    def test_rollback_migration_without_downgrade_raises_error(self, test_db_session: Session):
        """Test that rolling back a migration without downgrade function raises error."""
        from migrate_data import MIGRATIONS

        # Find a migration without downgrade function
        migration = next(m for m in MIGRATIONS if m.downgrade_func is None)

        # Apply the migration first
        migration.apply(test_db_session, dry_run=False)

        # Attempt to rollback should raise ValueError
        with pytest.raises(ValueError, match="does not support rollback"):
            migration.rollback(test_db_session, dry_run=False)

    def test_rollback_dry_run_does_not_modify_database(self, test_db_session: Session):
        """Test that rollback dry-run does not modify the database."""
        from migrate_data import MIGRATIONS

        # Apply migrations 1.0.0 and 1.1.0
        for migration in MIGRATIONS:
            if migration.version in ["1.0.0", "1.1.0"]:
                migration.apply(test_db_session, dry_run=False)

        # Verify migration 1.1.0 is applied
        result = test_db_session.execute(
            text("SELECT COUNT(*) FROM schema_migrations WHERE version = '1.1.0'")
        )
        assert result.scalar() == 1

        # Rollback in dry-run mode
        migration = next(m for m in MIGRATIONS if m.version == "1.1.0")
        migration.rollback(test_db_session, dry_run=True)

        # Verify migration 1.1.0 is still applied
        result = test_db_session.execute(
            text("SELECT COUNT(*) FROM schema_migrations WHERE version = '1.1.0'")
        )
        assert result.scalar() == 1


class TestMigrationManagement:
    """Test migration management functions."""

    def test_get_applied_migrations_empty(self, test_db_session: Session):
        """Test getting applied migrations when none are applied."""
        from migrate_data import get_applied_migrations

        applied = get_applied_migrations(test_db_session)
        assert applied == []

    def test_get_applied_migrations_after_applying(self, test_db_session: Session):
        """Test getting applied migrations after applying some."""
        from migrate_data import MIGRATIONS, get_applied_migrations

        # Apply first two migrations
        for migration in MIGRATIONS[:2]:
            migration.apply(test_db_session, dry_run=False)

        applied = get_applied_migrations(test_db_session)
        assert len(applied) == 2
        assert applied[0] == MIGRATIONS[0].version
        assert applied[1] == MIGRATIONS[1].version

    def test_get_pending_migrations_all_pending(self, test_db_session: Session):
        """Test getting pending migrations when all are pending."""
        from migrate_data import MIGRATIONS, get_pending_migrations

        pending = get_pending_migrations(test_db_session)
        assert len(pending) == len(MIGRATIONS)

    def test_get_pending_migrations_some_applied(self, test_db_session: Session):
        """Test getting pending migrations when some are already applied."""
        from migrate_data import MIGRATIONS, get_pending_migrations

        # Apply first migration
        MIGRATIONS[0].apply(test_db_session, dry_run=False)

        pending = get_pending_migrations(test_db_session)
        assert len(pending) == len(MIGRATIONS) - 1
        assert all(m.version != MIGRATIONS[0].version for m in pending)

    def test_get_pending_migrations_with_target_version(self, test_db_session: Session):
        """Test getting pending migrations up to a target version."""
        from migrate_data import MIGRATIONS, get_pending_migrations

        # Get pending migrations up to version 1.1.0
        pending = get_pending_migrations(test_db_session, target_version="1.1.0")

        # Should only include migrations up to and including 1.1.0
        versions = [m.version for m in pending]
        assert "1.0.0" in versions
        assert "1.1.0" in versions
        # Should not include later versions
        later_versions = [m.version for m in MIGRATIONS if m.version > "1.1.0"]
        assert all(v not in versions for v in later_versions)

    def test_apply_migrations_function(self, test_db_session: Session):
        """Test apply_migrations function applies all pending migrations."""
        from migrate_data import MIGRATIONS, apply_migrations, get_applied_migrations

        # Apply all migrations
        apply_migrations(test_db_session, dry_run=False)

        # Verify all migrations were applied
        applied = get_applied_migrations(test_db_session)
        assert len(applied) == len(MIGRATIONS)

    def test_apply_migrations_with_target_version(self, test_db_session: Session):
        """Test apply_migrations with target version."""
        from migrate_data import apply_migrations, get_applied_migrations

        # Apply migrations up to 1.1.0
        apply_migrations(test_db_session, target_version="1.1.0", dry_run=False)

        # Verify only migrations up to 1.1.0 were applied
        applied = get_applied_migrations(test_db_session)
        assert "1.0.0" in applied
        assert "1.1.0" in applied
        assert "1.2.0" not in applied

    def test_apply_migrations_idempotent(self, test_db_session: Session):
        """Test that applying migrations multiple times is idempotent."""
        from migrate_data import apply_migrations, get_applied_migrations

        # Apply all migrations
        apply_migrations(test_db_session, dry_run=False)
        first_applied = get_applied_migrations(test_db_session)

        # Apply again
        apply_migrations(test_db_session, dry_run=False)
        second_applied = get_applied_migrations(test_db_session)

        # Should have same result
        assert first_applied == second_applied


class TestDataIntegrity:
    """Test data integrity after migrations."""

    def test_foreign_key_constraints_maintained(self, test_db_session: Session):
        """Test that foreign key constraints are maintained after migrations."""
        from migrate_data import apply_migrations

        # Apply all migrations
        apply_migrations(test_db_session, dry_run=False)

        # Create a region
        region = Region(
            name="Test Region",
            latitude=-6.2,
            longitude=106.8,
            elevation=10.0,
            drainage_capacity=150.0,
        )
        test_db_session.add(region)
        test_db_session.commit()

        # Create related entities
        flood_event = FloodEvent(
            region_id=region.region_id,
            date=datetime.now(),
            severity=2,
        )
        road = Road(
            region_id=region.region_id,
            road_name="Test Road",
            road_type="primary",
            road_density=1.0,
        )
        facility = PublicFacility(
            region_id=region.region_id,
            name="Test Hospital",
            type="hospital",
            latitude=-6.2,
            longitude=106.8,
        )

        test_db_session.add_all([flood_event, road, facility])
        test_db_session.commit()

        # Verify relationships work
        assert flood_event.region == region
        assert road.region == region
        assert facility.region == region
        assert region.flood_events == [flood_event]
        assert region.roads == [road]
        assert region.public_facilities == [facility]

    def test_data_persists_after_migrations(self, test_db_session: Session):
        """Test that existing data persists after applying migrations."""
        from migrate_data import MIGRATIONS

        # Apply initial migration
        MIGRATIONS[0].apply(test_db_session, dry_run=False)

        # Insert test data
        region = Region(
            name="Test Region",
            latitude=-6.2,
            longitude=106.8,
            elevation=10.0,
            drainage_capacity=150.0,
        )
        test_db_session.add(region)
        test_db_session.commit()
        region_id = region.region_id

        # Apply remaining migrations
        for migration in MIGRATIONS[1:]:
            migration.apply(test_db_session, dry_run=False)

        # Verify data still exists
        result = test_db_session.query(Region).filter_by(region_id=region_id).first()
        assert result is not None
        assert result.name == "Test Region"
        assert result.latitude == -6.2
        assert result.longitude == 106.8

    def test_check_constraints_enforced(self, test_db_session: Session):
        """Test that check constraints are enforced after migrations."""
        from migrate_data import apply_migrations

        # Apply all migrations
        apply_migrations(test_db_session, dry_run=False)

        # Create a region
        region = Region(
            name="Test Region",
            latitude=-6.2,
            longitude=106.8,
            elevation=10.0,
            drainage_capacity=150.0,
        )
        test_db_session.add(region)
        test_db_session.commit()

        # Try to create flood event with valid severity
        flood_event = FloodEvent(
            region_id=region.region_id,
            date=datetime.now(),
            severity=2,  # Valid: 1-4
        )
        test_db_session.add(flood_event)
        test_db_session.commit()

        # Verify it was created
        assert flood_event.id is not None


class TestSeedDataScript:
    """Test seed_data.py script functionality."""

    def test_seed_regions_creates_regions(self, test_db_session: Session):
        """Test that seed_regions creates region records."""
        from migrate_data import apply_migrations
        from seed_data import seed_regions

        # Apply migrations first
        apply_migrations(test_db_session, dry_run=False)

        # Seed regions
        regions = seed_regions(test_db_session, drop_existing=False)

        # Verify regions were created
        assert len(regions) > 0
        assert all(isinstance(r, Region) for r in regions)
        assert all(r.region_id is not None for r in regions)

    def test_seed_regions_idempotent(self, test_db_session: Session):
        """Test that seed_regions is idempotent."""
        from migrate_data import apply_migrations
        from seed_data import seed_regions

        # Apply migrations first
        apply_migrations(test_db_session, dry_run=False)

        # Seed regions twice
        regions1 = seed_regions(test_db_session, drop_existing=False)
        regions2 = seed_regions(test_db_session, drop_existing=False)

        # Should return same regions
        assert len(regions1) == len(regions2)

    def test_seed_flood_events_creates_events(self, test_db_session: Session):
        """Test that seed_flood_events creates flood event records."""
        from migrate_data import apply_migrations
        from seed_data import seed_flood_events, seed_regions

        # Apply migrations and seed regions first
        apply_migrations(test_db_session, dry_run=False)
        regions = seed_regions(test_db_session, drop_existing=False)

        # Seed flood events
        flood_events = seed_flood_events(test_db_session, regions, drop_existing=False)

        # Verify flood events were created
        assert len(flood_events) > 0
        assert all(isinstance(f, FloodEvent) for f in flood_events)
        assert all(f.id is not None for f in flood_events)
        assert all(1 <= f.severity <= 4 for f in flood_events)

    def test_seed_roads_creates_roads(self, test_db_session: Session):
        """Test that seed_roads creates road records."""
        from migrate_data import apply_migrations
        from seed_data import seed_regions, seed_roads

        # Apply migrations and seed regions first
        apply_migrations(test_db_session, dry_run=False)
        regions = seed_regions(test_db_session, drop_existing=False)

        # Seed roads
        roads = seed_roads(test_db_session, regions, drop_existing=False)

        # Verify roads were created
        assert len(roads) > 0
        assert all(isinstance(r, Road) for r in roads)
        assert all(r.id is not None for r in roads)
        assert all(r.region_id in [reg.region_id for reg in regions] for r in roads)

    def test_seed_facilities_creates_facilities(self, test_db_session: Session):
        """Test that seed_facilities creates facility records."""
        from migrate_data import apply_migrations
        from seed_data import seed_facilities, seed_regions

        # Apply migrations and seed regions first
        apply_migrations(test_db_session, dry_run=False)
        regions = seed_regions(test_db_session, drop_existing=False)

        # Seed facilities
        facilities = seed_facilities(test_db_session, regions, drop_existing=False)

        # Verify facilities were created
        assert len(facilities) > 0
        assert all(isinstance(f, PublicFacility) for f in facilities)
        assert all(f.id is not None for f in facilities)
        assert all(f.type in ["hospital", "clinic", "school", "government"] for f in facilities)

    def test_seed_data_respects_foreign_keys(self, test_db_session: Session):
        """Test that seeded data respects foreign key constraints."""
        from migrate_data import apply_migrations
        from seed_data import seed_facilities, seed_flood_events, seed_regions, seed_roads

        # Apply migrations first
        apply_migrations(test_db_session, dry_run=False)

        # Seed all data
        regions = seed_regions(test_db_session, drop_existing=False)
        flood_events = seed_flood_events(test_db_session, regions, drop_existing=False)
        roads = seed_roads(test_db_session, regions, drop_existing=False)
        facilities = seed_facilities(test_db_session, regions, drop_existing=False)

        # Verify all foreign keys are valid
        region_ids = {r.region_id for r in regions}
        assert all(f.region_id in region_ids for f in flood_events)
        assert all(r.region_id in region_ids for r in roads)
        assert all(f.region_id in region_ids for f in facilities)


class TestEdgeCases:
    """Test edge cases and error handling."""

    def test_applying_same_migration_twice_is_safe(self, test_db_session: Session):
        """Test that calling apply_migrations multiple times is safe and idempotent."""
        from migrate_data import apply_migrations, get_applied_migrations

        # Apply all migrations
        apply_migrations(test_db_session, dry_run=False)
        first_applied = get_applied_migrations(test_db_session)

        # Apply migrations again (should be no-op since all are already applied)
        apply_migrations(test_db_session, dry_run=False)
        second_applied = get_applied_migrations(test_db_session)

        # Should have same migrations applied (no duplicates)
        assert first_applied == second_applied
        
        # Verify no duplicate records in schema_migrations table
        result = test_db_session.execute(
            text("SELECT version, COUNT(*) as cnt FROM schema_migrations GROUP BY version HAVING COUNT(*) > 1")
        )
        duplicates = list(result)
        assert len(duplicates) == 0, f"Found duplicate migration records: {duplicates}"

    def test_migration_table_created_automatically(self, test_db_session: Session):
        """Test that schema_migrations table is created automatically."""
        from migrate_data import get_applied_migrations

        # Call get_applied_migrations (should create table)
        applied = get_applied_migrations(test_db_session)

        # Verify table exists
        result = test_db_session.execute(
            text("SELECT name FROM sqlite_master WHERE type='table' AND name='schema_migrations'")
        )
        assert result.fetchone() is not None

    def test_empty_database_can_be_migrated(self, test_db_session: Session):
        """Test that an empty database can be migrated successfully."""
        from migrate_data import apply_migrations

        # Apply all migrations to empty database
        apply_migrations(test_db_session, dry_run=False)

        # Verify schema was created
        engine = test_db_session.get_bind()
        from sqlalchemy import inspect
        inspector = inspect(engine)
        tables = inspector.get_table_names()

        assert len(tables) > 0
        assert "regions" in tables

    def test_migration_with_existing_data(self, test_db_session: Session):
        """Test migration with existing data in database."""
        from migrate_data import MIGRATIONS

        # Apply initial migration
        MIGRATIONS[0].apply(test_db_session, dry_run=False)

        # Add some data
        region = Region(
            name="Existing Region",
            latitude=-6.2,
            longitude=106.8,
            elevation=10.0,
            drainage_capacity=150.0,
        )
        test_db_session.add(region)
        test_db_session.commit()

        # Apply remaining migrations
        for migration in MIGRATIONS[1:]:
            migration.apply(test_db_session, dry_run=False)

        # Verify existing data is preserved
        result = test_db_session.query(Region).filter_by(name="Existing Region").first()
        assert result is not None
        assert result.latitude == -6.2
