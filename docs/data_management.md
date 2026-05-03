# Data Management Guide

This guide covers data seeding and migration operations for the URIS-AI system.

## Overview

URIS-AI provides two main scripts for data management:

1. **seed_data.py** - Seeds initial data into the database
2. **migrate_data.py** - Manages database schema migrations and data transformations

## Prerequisites

- Python 3.11 or higher
- Azure SQL Database configured
- Environment variables set in `.env` file
- Database connection string configured

## Data Seeding

### Quick Start

```bash
# Seed initial data (safe, idempotent)
python scripts/seed_data.py
```

### What Gets Seeded

The seeding script populates the following data:

#### 1. Regions (25 total)

**Jakarta (15 regions):**

- Menteng, Tanah Abang, Kemayoran (Jakarta Pusat)
- Kelapa Gading, Penjaringan, Pademangan (Jakarta Utara)
- Kebayoran Baru, Tebet, Cilandak (Jakarta Selatan)
- Cengkareng, Kebon Jeruk, Grogol Petamburan (Jakarta Barat)
- Matraman, Jatinegara, Cakung (Jakarta Timur)

**Jawa Barat (10 regions):**

- Bandung Wetan, Cicendo, Coblong (Kota Bandung)
- Bogor Tengah, Bogor Utara, Tanah Sareal (Kota Bogor)
- Bekasi Timur, Bekasi Barat, Pondok Gede (Kota Bekasi)
- Depok (Kota Depok)

Each region includes:

- Name (kelurahan/kecamatan level)
- Coordinates (latitude, longitude)
- Elevation (meters above sea level)
- Drainage capacity (mm/hour)

#### 2. Historical Flood Events

- **Time Period:** Past 2 years
- **Pattern:** Concentrated in rainy season (November-March)
- **Severity Levels:** 1 (Rendah), 2 (Sedang), 3 (Tinggi), 4 (Kritis)
- **Additional Data:** Water level, duration, affected area

**Flood-Prone Regions:**

- Regions with elevation < 20m and drainage capacity < 150 mm/hour
- Higher probability of floods during rainy season (20% daily)

#### 3. Road Network

- **Roads per Region:** 3-7 roads
- **Road Types:** Primary, secondary, tertiary, residential
- **Data Included:** Name, type, density, length, main road flag

**Road Characteristics:**

- Primary roads: 0.8-1.5 density, 5-15 km length
- Secondary roads: 0.6-1.2 density, 3-10 km length
- Tertiary roads: 0.4-0.9 density, 2-7 km length
- Residential roads: 0.2-0.6 density, 0.5-3 km length

#### 4. Public Facilities

- **Facilities per Region:** 4-8 facilities
- **Types:** Hospital, clinic (puskesmas), school, government office
- **Data Included:** Name, type, coordinates, capacity, operational status

**Facility Capacities:**

- Hospitals: 100-500 beds
- Clinics: 20-100 patients
- Schools: 200-1000 students
- Government offices: 50-200 staff

### Advanced Usage

#### Drop and Reseed (Development Only)

```bash
# WARNING: This deletes all existing data!
python scripts/seed_data.py --drop-existing
```

**Use Cases:**

- Resetting development database
- Testing with fresh data
- Recovering from data corruption

**⚠️ Warning:** Never use `--drop-existing` in production!

#### Checking Seeded Data

```bash
# Connect to database and verify
sqlcmd -S <server>.database.windows.net -d <database> -U <username> -P <password>

# Check region count
SELECT COUNT(*) FROM regions;

# Check flood events
SELECT COUNT(*) FROM flood_events;

# Check roads
SELECT COUNT(*) FROM roads;

# Check facilities
SELECT COUNT(*) FROM public_facilities;
```

### Idempotency

The seeding script is idempotent, meaning:

- ✅ Safe to run multiple times
- ✅ Checks for existing data before inserting
- ✅ Skips data that already exists
- ✅ Logs what was skipped vs. inserted

Example output:

```
INFO - Seeding regions data...
INFO - Found 25 existing regions. Skipping region seeding.
INFO - Seeding flood events data...
INFO - Found 150 existing flood events. Skipping flood event seeding.
```

## Database Migrations

### Quick Start

```bash
# Check migration status
python scripts/migrate_data.py --status

# Apply all pending migrations
python scripts/migrate_data.py
```

### Available Migrations

#### 1.0.0 - Initial Schema

Creates the base database schema with all tables:

- regions
- weather_data
- flood_events
- roads
- public_facilities
- risk_scores
- recommendations
- users

#### 1.1.0 - Performance Indexes

Adds indexes for query optimization:

- `idx_regions_name` on regions(name)
- `idx_weather_region_date` on weather_data(region_id, date)

**Rollback:** Supported

#### 1.2.0 - Audit Columns

Adds audit trail columns to critical tables:

- `created_by` VARCHAR(100)
- `updated_by` VARCHAR(100)

**Tables Updated:** regions, public_facilities, roads

**Rollback:** Supported

#### 1.3.0 - Flood Severity Normalization

Transforms legacy flood severity data:

- Ensures all severity values are in range 1-4
- Normalizes out-of-range values

**Rollback:** Not supported (data transformation)

### Migration Commands

#### Show Status

```bash
python scripts/migrate_data.py --status
```

Output:

```
Migration Status:
--------------------------------------------------------------------------------
✓ Applied    | 1.0.0      | Initial database schema
✓ Applied    | 1.1.0      | Add performance indexes
✗ Pending    | 1.2.0      | Add audit columns
✗ Pending    | 1.3.0      | Transform legacy flood severity data
--------------------------------------------------------------------------------
```

#### Apply Migrations

```bash
# Apply all pending migrations
python scripts/migrate_data.py

# Apply up to specific version
python scripts/migrate_data.py --version 1.2.0
```

#### Dry Run

Preview changes without applying:

```bash
python scripts/migrate_data.py --dry-run
```

Output:

```
INFO - Found 2 pending migration(s)
INFO - [DRY RUN] Would apply migration 1.2.0
INFO - [DRY RUN] Would apply migration 1.3.0
```

#### Rollback

```bash
# Rollback a specific migration
python scripts/migrate_data.py --rollback 1.2.0

# Verify rollback
python scripts/migrate_data.py --status
```

**Note:** Only migrations with downgrade functions support rollback.

### Migration Tracking

Migrations are tracked in the `schema_migrations` table:

```sql
CREATE TABLE schema_migrations (
    id INT IDENTITY(1,1) PRIMARY KEY,
    version VARCHAR(50) NOT NULL UNIQUE,
    description VARCHAR(255) NOT NULL,
    applied_at DATETIME NOT NULL
)
```

Query migration history:

```sql
SELECT * FROM schema_migrations ORDER BY applied_at;
```

### Creating New Migrations

#### Step 1: Define Upgrade Function

```python
def migration_1_4_0_upgrade(session: Session) -> None:
    """
    Add new column to regions table.
    """
    logger.info("Adding population column to regions...")

    session.execute(text("""
        ALTER TABLE regions
        ADD population INT NULL
    """))
```

#### Step 2: Define Downgrade Function (Optional)

```python
def migration_1_4_0_downgrade(session: Session) -> None:
    """
    Remove population column from regions table.
    """
    logger.info("Removing population column from regions...")

    session.execute(text("""
        ALTER TABLE regions
        DROP COLUMN population
    """))
```

#### Step 3: Register Migration

```python
MIGRATIONS.append(
    Migration(
        version="1.4.0",
        description="Add population data to regions",
        upgrade_func=migration_1_4_0_upgrade,
        downgrade_func=migration_1_4_0_downgrade,
    )
)
```

#### Step 4: Test Migration

```bash
# Test with dry run
python scripts/migrate_data.py --dry-run

# Apply migration
python scripts/migrate_data.py --version 1.4.0

# Verify
python scripts/migrate_data.py --status
```

## Common Workflows

### Initial Setup (New Environment)

```bash
# 1. Apply all migrations
python scripts/migrate_data.py

# 2. Seed initial data
python scripts/seed_data.py

# 3. Verify data
python scripts/migrate_data.py --status
```

### Schema Update (Existing Environment)

```bash
# 1. Check current status
python scripts/migrate_data.py --status

# 2. Preview changes
python scripts/migrate_data.py --dry-run

# 3. Apply migrations
python scripts/migrate_data.py

# 4. Verify
python scripts/migrate_data.py --status
```

### Development Reset

```bash
# 1. Drop and reseed data
python scripts/seed_data.py --drop-existing

# 2. Verify
python scripts/migrate_data.py --status
```

### Production Deployment

```bash
# 1. Backup database first!
az sql db export --resource-group <rg> --server <server> --name <db> \
  --storage-key <key> --storage-key-type StorageAccessKey \
  --storage-uri https://<account>.blob.core.windows.net/backups/backup.bacpac

# 2. Test migrations in staging
python scripts/migrate_data.py --dry-run

# 3. Apply migrations
python scripts/migrate_data.py

# 4. Verify
python scripts/migrate_data.py --status

# 5. Seed data if needed (first deployment only)
python scripts/seed_data.py
```

## Troubleshooting

### Connection Issues

**Problem:** Cannot connect to database

**Solutions:**

1. Check `.env` file has correct connection string
2. Verify Azure SQL firewall rules allow your IP
3. Test connection: `sqlcmd -S <server> -d <db> -U <user> -P <pass>`
4. Check VPN/network connectivity

### Permission Issues

**Problem:** Permission denied errors

**Solutions:**

1. Verify database user has required permissions:
   - CREATE TABLE
   - ALTER TABLE
   - INSERT, UPDATE, DELETE
   - CREATE INDEX
2. Use admin account for migrations
3. Grant permissions: `GRANT ALTER ON SCHEMA::dbo TO <user>`

### Data Conflicts

**Problem:** Foreign key constraint violations

**Solutions:**

1. Ensure migrations are applied before seeding
2. Check seed order: regions → flood_events/roads/facilities
3. Verify referential integrity

### Migration Failures

**Problem:** Migration fails mid-execution

**Solutions:**

1. Check migration logs for specific error
2. Verify SQL syntax for target database (Azure SQL)
3. Test migration in development first
4. Use transactions to ensure atomicity

### Rollback Issues

**Problem:** Cannot rollback migration

**Solutions:**

1. Check if migration supports rollback (has downgrade function)
2. Verify migration was actually applied
3. Manual rollback: write SQL to undo changes
4. Restore from backup if necessary

## Best Practices

### Development

1. **Always test locally first**
   - Run migrations in development
   - Verify data integrity
   - Test rollback if supported

2. **Use dry run**
   - Preview changes before applying
   - Catch issues early
   - Understand impact

3. **Version control**
   - Commit migration code
   - Document changes
   - Review before merging

### Production

1. **Backup first**
   - Always backup before migrations
   - Test restore procedure
   - Keep multiple backups

2. **Test in staging**
   - Apply migrations to staging first
   - Verify application works
   - Run full test suite

3. **Monitor after deployment**
   - Watch application logs
   - Check database performance
   - Monitor error rates

4. **Have rollback plan**
   - Know how to rollback
   - Test rollback procedure
   - Document rollback steps

### Data Seeding

1. **Use idempotent scripts**
   - Safe to run multiple times
   - Check before inserting
   - Log operations

2. **Realistic data**
   - Use actual region names
   - Follow real patterns
   - Maintain referential integrity

3. **Document data sources**
   - Note where data comes from
   - Document assumptions
   - Keep data updated

## Security Considerations

### Connection Strings

- Never commit connection strings to version control
- Use environment variables
- Rotate credentials regularly
- Use Azure Key Vault in production

### Data Privacy

- Seed scripts use synthetic data only
- No real personal information
- Follow data protection regulations
- Audit data access

### Access Control

- Limit migration permissions
- Use service accounts for automation
- Enable audit logging
- Review access regularly

## Performance Tips

### Seeding Large Datasets

```python
# Batch inserts for better performance
session.bulk_insert_mappings(Region, regions_data)
session.commit()
```

### Migration Performance

```python
# Create indexes after bulk inserts
session.execute(text("CREATE INDEX idx_name ON table(column)"))
```

### Monitoring

```bash
# Check migration duration
python scripts/migrate_data.py 2>&1 | grep "Successfully applied"
```

## References

- [SQLAlchemy Documentation](https://docs.sqlalchemy.org/)
- [Azure SQL Database](https://docs.microsoft.com/en-us/azure/azure-sql/)
- [Database Migration Best Practices](https://www.liquibase.org/get-started/best-practices)

## Support

For issues or questions:

1. Check script logs
2. Review this documentation
3. Test in development environment
4. Contact development team

## Requirements

**Requirements 7.1:** Data Integration and Storage

- Integrates data from multiple sources
- Stores in unified repository
- Maintains data quality and consistency
