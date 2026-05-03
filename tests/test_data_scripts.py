"""
Tests for data seeding and migration scripts.

These tests verify that the data management scripts work correctly.
"""

import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

# Add scripts to path
scripts_path = Path(__file__).parent.parent / "scripts"
sys.path.insert(0, str(scripts_path))


class TestSeedDataScript:
    """Tests for seed_data.py script."""
    
    def test_get_jakarta_regions(self):
        """Test that Jakarta regions data is valid."""
        from seed_data import get_jakarta_regions
        
        regions = get_jakarta_regions()
        
        # Should have multiple regions
        assert len(regions) > 0
        
        # Each region should have required fields
        for region in regions:
            assert "name" in region
            assert "latitude" in region
            assert "longitude" in region
            assert "elevation" in region
            assert "drainage_capacity" in region
            
            # Validate data types
            assert isinstance(region["name"], str)
            assert isinstance(region["latitude"], float)
            assert isinstance(region["longitude"], float)
            assert isinstance(region["elevation"], float)
            assert isinstance(region["drainage_capacity"], float)
            
            # Validate ranges
            assert -90 <= region["latitude"] <= 90
            assert -180 <= region["longitude"] <= 180
            assert region["elevation"] >= 0
            assert region["drainage_capacity"] > 0
    
    def test_get_jabar_regions(self):
        """Test that Jawa Barat regions data is valid."""
        from seed_data import get_jabar_regions
        
        regions = get_jabar_regions()
        
        # Should have multiple regions
        assert len(regions) > 0
        
        # Each region should have required fields
        for region in regions:
            assert "name" in region
            assert "latitude" in region
            assert "longitude" in region
            assert "elevation" in region
            assert "drainage_capacity" in region
    
    def test_seed_regions_idempotent(self):
        """Test that seed_regions is idempotent."""
        from seed_data import seed_regions
        from uris_ai.models.database import Region
        
        # Mock session
        mock_session = MagicMock()
        mock_session.query.return_value.count.return_value = 5  # Existing regions
        mock_session.query.return_value.all.return_value = [
            Region(region_id=1, name="Test", latitude=0.0, longitude=0.0)
        ]
        
        # Should skip seeding if regions exist
        result = seed_regions(mock_session, drop_existing=False)
        
        # Should return existing regions
        assert len(result) == 1
        
        # Should not add new regions
        mock_session.add.assert_not_called()


class TestMigrateDataScript:
    """Tests for migrate_data.py script."""
    
    def test_migration_class(self):
        """Test Migration class initialization."""
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
    
    def test_migrations_list(self):
        """Test that MIGRATIONS list is properly defined."""
        from migrate_data import MIGRATIONS
        
        # Should have at least one migration
        assert len(MIGRATIONS) > 0
        
        # Each migration should have required attributes
        for migration in MIGRATIONS:
            assert hasattr(migration, "version")
            assert hasattr(migration, "description")
            assert hasattr(migration, "upgrade_func")
            
            # Version should be in semantic versioning format
            parts = migration.version.split(".")
            assert len(parts) == 3
            assert all(part.isdigit() for part in parts)
    
    def test_get_pending_migrations(self):
        """Test get_pending_migrations function."""
        from migrate_data import get_pending_migrations, MIGRATIONS
        
        # Mock session
        mock_session = MagicMock()
        
        # Mock no applied migrations
        with patch("migrate_data.get_applied_migrations", return_value=[]):
            pending = get_pending_migrations(mock_session)
            
            # All migrations should be pending
            assert len(pending) == len(MIGRATIONS)
        
        # Mock some applied migrations
        with patch("migrate_data.get_applied_migrations", return_value=["1.0.0"]):
            pending = get_pending_migrations(mock_session)
            
            # Should have fewer pending migrations
            assert len(pending) < len(MIGRATIONS)
            
            # First migration should not be in pending
            assert all(m.version != "1.0.0" for m in pending)
    
    def test_migration_versioning(self):
        """Test that migration versions are sequential."""
        from migrate_data import MIGRATIONS
        
        versions = [m.version for m in MIGRATIONS]
        
        # Convert to tuples for comparison
        version_tuples = [tuple(map(int, v.split("."))) for v in versions]
        
        # Should be sorted
        assert version_tuples == sorted(version_tuples)


class TestScriptIntegration:
    """Integration tests for scripts."""
    
    def test_seed_data_imports(self):
        """Test that seed_data.py can be imported."""
        import seed_data
        
        # Should have main function
        assert hasattr(seed_data, "main")
        
        # Should have seeding functions
        assert hasattr(seed_data, "seed_regions")
        assert hasattr(seed_data, "seed_flood_events")
        assert hasattr(seed_data, "seed_roads")
        assert hasattr(seed_data, "seed_facilities")
    
    def test_migrate_data_imports(self):
        """Test that migrate_data.py can be imported."""
        import migrate_data
        
        # Should have main function
        assert hasattr(migrate_data, "main")
        
        # Should have migration functions
        assert hasattr(migrate_data, "apply_migrations")
        assert hasattr(migrate_data, "rollback_migration")
        assert hasattr(migrate_data, "show_migration_status")
