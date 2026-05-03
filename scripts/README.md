# URIS-AI Scripts

This directory contains scripts for deploying, managing, and maintaining URIS-AI infrastructure, applications, and data.

## Scripts Overview

### Data Management

#### `seed_data.py`

Seeds initial data into the database including regions, historical flood events, roads, and public facilities.

**Usage:**

```bash
# Seed data (idempotent - safe to run multiple times)
python scripts/seed_data.py

# Drop existing data and reseed (WARNING: destructive)
python scripts/seed_data.py --drop-existing
```

**What it does:**

1. Connects to Azure SQL Database
2. Creates database schema if it doesn't exist
3. Seeds regions data for Jakarta and Jawa Barat (25 regions)
4. Seeds historical flood events for the past 2 years
5. Seeds road network data (3-7 roads per region)
6. Seeds public facilities (hospitals, clinics, schools, government offices)

**Data Seeded:**

- **Regions:** 15 regions in Jakarta, 10 regions in Jawa Barat
- **Flood Events:** Historical data for past 2 years with realistic patterns
- **Roads:** Primary, secondary, tertiary, and residential roads
- **Facilities:** Hospitals, clinics (puskesmas), schools, government offices

**Features:**

- Idempotent: Can be run multiple times safely (checks for existing data)
- Realistic data: Uses actual region names and coordinates
- Seasonal patterns: Flood events concentrated in rainy season (Nov-Mar)
- Proper logging: Detailed logs of all operations
- Error handling: Graceful handling of database errors

**Requirements:** 7.1

#### `migrate_data.py`

Handles database schema migrations and data transformations.

**Usage:**

```bash
# Show migration status
python scripts/migrate_data.py --status

# Apply all pending migrations
python scripts/migrate_data.py

# Apply migrations up to a specific version
python scripts/migrate_data.py --version 1.2.0

# Dry run (show what would be done)
python scripts/migrate_data.py --dry-run

# Rollback a specific migration
python scripts/migrate_data.py --rollback 1.2.0
```

**Available Migrations:**

1. **1.0.0** - Initial database schema
2. **1.1.0** - Add performance indexes
3. **1.2.0** - Add audit columns (created_by, updated_by)
4. **1.3.0** - Transform legacy flood severity data

**Features:**

- Versioned migrations: Track which migrations have been applied
- Rollback support: Undo migrations when supported
- Dry run mode: Preview changes without applying them
- Migration history: Tracks when migrations were applied
- Idempotent: Safe to run multiple times

**Adding New Migrations:**

1. Define upgrade function: `def migration_X_Y_Z_upgrade(session: Session)`
2. Define downgrade function (optional): `def migration_X_Y_Z_downgrade(session: Session)`
3. Add to MIGRATIONS list:
   ```python
   Migration(
       version="X.Y.Z",
       description="Description of changes",
       upgrade_func=migration_X_Y_Z_upgrade,
       downgrade_func=migration_X_Y_Z_downgrade,
   )
   ```

**Requirements:** 7.1

### Infrastructure Setup

#### `setup_azure.sh`

Sets up Azure infrastructure using Terraform.

**Usage:**

```bash
./scripts/setup_azure.sh
```

**Prerequisites:**

- Azure CLI installed and logged in
- Terraform installed
- `terraform.tfvars` file configured

**What it does:**

1. Validates Azure login
2. Initializes Terraform
3. Plans infrastructure changes
4. Applies Terraform configuration
5. Generates `.env` file with outputs

### Blue-Green Deployment

#### `blue_green_deploy.sh`

Implements zero-downtime blue-green deployment with automatic rollback.

**Usage:**

```bash
# Production deployment
export RESOURCE_GROUP="uris-ai-rg"
export ENVIRONMENT="production"
./scripts/blue_green_deploy.sh

# Staging deployment
export ENVIRONMENT="staging"
./scripts/blue_green_deploy.sh
```

**Environment Variables:**

- `RESOURCE_GROUP`: Azure resource group (default: uris-ai-rg)
- `ENVIRONMENT`: Target environment (default: production)
- `SLOT_NAME`: Deployment slot name (default: green)
- `ROLLBACK_ENABLED`: Enable automatic rollback (default: true)

**What it does:**

1. Checks prerequisites
2. Creates deployment slots if needed
3. Builds application package
4. Deploys to green slot
5. Runs smoke tests
6. Swaps slots (blue-green deployment)
7. Monitors production
8. Automatically rolls back if issues detected

**Requirements:** 9.2, 9.4

### Rollback

#### `rollback_deployment.sh`

Quickly rolls back to the previous version.

**Usage:**

```bash
export RESOURCE_GROUP="uris-ai-rg"
export ENVIRONMENT="production"
./scripts/rollback_deployment.sh
```

**Environment Variables:**

- `RESOURCE_GROUP`: Azure resource group (default: uris-ai-rg)
- `ENVIRONMENT`: Target environment (default: production)
- `SLOT_NAME`: Deployment slot name (default: green)

**What it does:**

1. Confirms rollback with user
2. Swaps slots back to previous version
3. Verifies health after rollback

**Requirements:** 9.2, 9.4

### Smoke Tests

#### `run_smoke_tests.sh`

Runs comprehensive smoke tests against a deployed environment.

**Usage:**

```bash
# Test local environment
export SMOKE_TEST_API_URL="http://localhost:8000"
./scripts/run_smoke_tests.sh

# Test green slot
export SMOKE_TEST_API_URL="https://uris-ai-api-production-green.azurewebsites.net"
./scripts/run_smoke_tests.sh

# Test production
export SMOKE_TEST_API_URL="https://uris-ai-api-production.azurewebsites.net"
./scripts/run_smoke_tests.sh
```

**Environment Variables:**

- `SMOKE_TEST_API_URL`: API endpoint to test (default: http://localhost:8000)
- `SMOKE_TEST_TIMEOUT`: Request timeout in seconds (default: 30)
- `SMOKE_TEST_MAX_RETRIES`: Maximum retry attempts (default: 3)
- `SMOKE_TEST_RETRY_DELAY`: Delay between retries in seconds (default: 5)

**What it does:**

1. Waits for API to be ready
2. Runs comprehensive smoke tests
3. Validates critical endpoints
4. Checks database connectivity
5. Verifies external service connectivity
6. Generates test report

**Requirements:** 9.2

### Legacy Deployment Scripts

#### `deploy_staging.sh`

Simple deployment to staging environment (legacy).

**Usage:**

```bash
./scripts/deploy_staging.sh
```

**Note:** Consider using `blue_green_deploy.sh` with `ENVIRONMENT=staging` instead.

#### `deploy_production.sh`

Production deployment with basic blue-green support (legacy).

**Usage:**

```bash
./scripts/deploy_production.sh
```

**Note:** Use `blue_green_deploy.sh` for production deployments instead.

## Deployment Workflow

### Initial Setup

1. **Configure Terraform variables:**

   ```bash
   cd infrastructure/terraform
   cp terraform.tfvars.example terraform.tfvars
   # Edit terraform.tfvars with your values
   ```

2. **Setup Azure infrastructure:**

   ```bash
   ./scripts/setup_azure.sh
   ```

3. **Configure environment variables:**

   ```bash
   # Edit .env file generated by setup_azure.sh
   # Add missing values (SQL password, API keys, etc.)
   ```

4. **Initialize database schema and seed data:**

   ```bash
   # Run migrations to create schema
   python scripts/migrate_data.py

   # Seed initial data
   python scripts/seed_data.py
   ```

### Data Management Workflow

#### Initial Database Setup

```bash
# 1. Check migration status
python scripts/migrate_data.py --status

# 2. Apply all migrations
python scripts/migrate_data.py

# 3. Seed initial data
python scripts/seed_data.py
```

#### Updating Database Schema

```bash
# 1. Preview changes (dry run)
python scripts/migrate_data.py --dry-run

# 2. Apply migrations
python scripts/migrate_data.py

# 3. Verify migration status
python scripts/migrate_data.py --status
```

#### Resetting Database (Development Only)

```bash
# WARNING: This will delete all data!
python scripts/seed_data.py --drop-existing
```

#### Rolling Back Migrations

```bash
# Rollback a specific migration
python scripts/migrate_data.py --rollback 1.2.0

# Verify rollback
python scripts/migrate_data.py --status
```

### Development Deployment

```bash
# Deploy to development environment
export ENVIRONMENT="dev"
export RESOURCE_GROUP="uris-ai-rg"
./scripts/blue_green_deploy.sh
```

### Staging Deployment

```bash
# Deploy to staging environment
export ENVIRONMENT="staging"
export RESOURCE_GROUP="uris-ai-rg"
./scripts/blue_green_deploy.sh
```

### Production Deployment

```bash
# Deploy to production with blue-green deployment
export ENVIRONMENT="production"
export RESOURCE_GROUP="uris-ai-rg"
export ROLLBACK_ENABLED="true"
./scripts/blue_green_deploy.sh
```

### Rollback

```bash
# Rollback production deployment
export ENVIRONMENT="production"
export RESOURCE_GROUP="uris-ai-rg"
./scripts/rollback_deployment.sh
```

## Smoke Tests

Smoke tests validate critical functionality after deployment:

### Test Categories

1. **Critical Endpoints**
   - Root endpoint
   - Health checks
   - API documentation

2. **Database Connectivity**
   - Connection validation
   - Query performance

3. **External Services**
   - Cache connectivity
   - Monitoring connectivity

4. **Authentication**
   - Login endpoint
   - Register endpoint

5. **Core Functionality**
   - Risk assessment
   - Recommendations

6. **Performance**
   - Response times
   - Health check latency

7. **Security**
   - HTTPS enforcement
   - CORS configuration

### Running Tests

```bash
# Run all smoke tests
./scripts/run_smoke_tests.sh

# Run specific test class
pytest tests/smoke/test_deployment_smoke.py::TestCriticalEndpoints -v

# Run with custom configuration
export SMOKE_TEST_API_URL="https://your-api.azurewebsites.net"
export SMOKE_TEST_TIMEOUT="60"
./scripts/run_smoke_tests.sh
```

## Troubleshooting

### Data Seeding Issues

**Problem:** Cannot connect to database

**Solutions:**

1. Verify database connection string in `.env` file
2. Check Azure SQL firewall rules: `az sql server firewall-rule list`
3. Test connection: `sqlcmd -S <server>.database.windows.net -d <database> -U <username> -P <password>`
4. Verify VPN/network connectivity

**Problem:** Data already exists error

**Solutions:**

1. Script is idempotent - it will skip existing data
2. To reseed, use `--drop-existing` flag (WARNING: destructive)
3. Check logs to see which data was skipped

**Problem:** Foreign key constraint errors

**Solutions:**

1. Ensure migrations have been applied: `python scripts/migrate_data.py --status`
2. Check that regions are seeded before other data
3. Verify database schema matches models

### Migration Issues

**Problem:** Migration fails to apply

**Solutions:**

1. Check database connection
2. Review migration logs for specific errors
3. Verify database user has sufficient permissions
4. Try dry run first: `python scripts/migrate_data.py --dry-run`

**Problem:** Cannot rollback migration

**Solutions:**

1. Check if migration supports rollback (has downgrade function)
2. Verify migration was actually applied: `python scripts/migrate_data.py --status`
3. Review migration code for issues

**Problem:** Schema_migrations table doesn't exist

**Solutions:**

1. Table is created automatically on first run
2. Verify database user has CREATE TABLE permission
3. Run initial migration: `python scripts/migrate_data.py --version 1.0.0`

### Deployment Fails

**Problem:** Deployment script fails during execution

**Solutions:**

1. Check Azure CLI login: `az account show`
2. Verify resource group exists: `az group show --name uris-ai-rg`
3. Check app service status: `az webapp show --name uris-ai-api-production --resource-group uris-ai-rg`
4. Review deployment logs: `az webapp log tail --name uris-ai-api-production --resource-group uris-ai-rg`

### Smoke Tests Fail

**Problem:** Smoke tests fail on green slot

**Solutions:**

1. Check application logs
2. Verify database connectivity
3. Test endpoints manually: `curl https://your-api.azurewebsites.net/health`
4. Check Application Insights for errors

### Slot Swap Fails

**Problem:** Cannot swap deployment slots

**Solutions:**

1. Verify slot exists: `az webapp deployment slot list --name uris-ai-api-production --resource-group uris-ai-rg`
2. Check for resource locks
3. Verify permissions
4. Try manual swap in Azure Portal

### Automatic Rollback Triggered

**Problem:** Deployment automatically rolls back

**Solutions:**

1. Review deployment logs
2. Check Application Insights
3. Investigate health check failures
4. Fix issues and redeploy

## Best Practices

1. **Always test locally first**
   - Run full test suite
   - Verify smoke tests pass
   - Check for breaking changes

2. **Use staging environment**
   - Deploy to staging first
   - Validate functionality
   - Run smoke tests

3. **Monitor deployments**
   - Watch Application Insights
   - Check health endpoints
   - Monitor error rates

4. **Keep rollback ready**
   - Know how to rollback
   - Test rollback procedure
   - Document rollback steps

5. **Communicate deployments**
   - Notify team before deployment
   - Update status channels
   - Document any issues

## Security Considerations

1. **Secrets Management**
   - Never commit secrets to version control
   - Use Azure Key Vault for secrets
   - Rotate secrets regularly

2. **Access Control**
   - Limit deployment permissions
   - Use service principals for CI/CD
   - Enable audit logging

3. **Network Security**
   - Use HTTPS for all endpoints
   - Configure firewall rules
   - Enable DDoS protection

## CI/CD Integration

These scripts can be integrated into CI/CD pipelines:

### GitHub Actions

```yaml
- name: Deploy to Production
  env:
    RESOURCE_GROUP: uris-ai-rg
    ENVIRONMENT: production
  run: ./scripts/blue_green_deploy.sh
```

### Azure DevOps

```yaml
- script: ./scripts/blue_green_deploy.sh
  env:
    RESOURCE_GROUP: uris-ai-rg
    ENVIRONMENT: production
  displayName: "Deploy to Production"
```

## Support

For issues or questions:

1. Check script logs
2. Review Azure Portal
3. Check Application Insights
4. Consult documentation
5. Contact development team

## References

- [Blue-Green Deployment Guide](../docs/blue_green_deployment.md)
- [Azure App Service Documentation](https://docs.microsoft.com/en-us/azure/app-service/)
- [Terraform Azure Provider](https://registry.terraform.io/providers/hashicorp/azurerm/latest/docs)
