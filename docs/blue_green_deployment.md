# Blue-Green Deployment Guide

## Overview

URIS-AI implements blue-green deployment strategy to achieve zero-downtime deployments and enable quick rollbacks in case of issues. This document describes the deployment process, architecture, and operational procedures.

**Requirements**: 9.1, 9.2, 9.4

## Architecture

### Blue-Green Deployment Concept

Blue-green deployment maintains two identical production environments:

- **Blue Environment**: Currently serving production traffic
- **Green Environment**: Staging environment for new deployments

During deployment:

1. New version is deployed to the green environment
2. Smoke tests validate the green environment
3. Traffic is switched from blue to green
4. Blue environment becomes the new green (for next deployment or rollback)

### Azure Implementation

URIS-AI uses Azure App Service deployment slots to implement blue-green deployment:

- **Production Slot**: The blue environment (currently serving traffic)
- **Green Slot**: The staging environment (for new deployments)
- **Traffic Manager**: Provides automatic failover capability
- **Application Insights**: Monitors both environments

## Infrastructure Setup

### Prerequisites

1. Azure CLI installed and configured
2. Terraform installed (>= 1.0)
3. Appropriate Azure permissions
4. Python 3.11+ for smoke tests

### Enable Blue-Green Deployment

Edit `infrastructure/terraform/terraform.tfvars`:

```hcl
environment         = "production"
enable_blue_green   = true
deployment_slot_name = "green"
```

Apply Terraform configuration:

```bash
cd infrastructure/terraform
terraform init
terraform plan
terraform apply
```

This creates:

- Production app services (blue environment)
- Green deployment slots
- Traffic Manager profile
- Application Insights
- Health check endpoints

## Deployment Process

### Automated Deployment

Use the blue-green deployment script:

```bash
# Set environment variables
export RESOURCE_GROUP="uris-ai-rg"
export ENVIRONMENT="production"
export SLOT_NAME="green"

# Run deployment
./scripts/blue_green_deploy.sh
```

### Deployment Steps

The script performs the following steps:

1. **Prerequisites Check**
   - Verifies Azure CLI is installed
   - Confirms Azure login status
   - Validates environment configuration

2. **Deployment Slot Creation**
   - Creates green slot if it doesn't exist
   - Copies configuration from production

3. **Application Build**
   - Builds application package
   - Creates deployment artifacts

4. **Green Deployment**
   - Deploys new version to green slot
   - Waits for deployment to complete

5. **Smoke Tests**
   - Runs comprehensive smoke tests on green slot
   - Validates critical endpoints
   - Checks database connectivity
   - Verifies external service connectivity
   - Aborts deployment if tests fail

6. **Slot Swap**
   - Swaps green and blue slots
   - Traffic switches to new version
   - Previous version remains in green slot

7. **Production Monitoring**
   - Monitors production for 60 seconds
   - Performs health checks every 10 seconds
   - Triggers automatic rollback if issues detected

8. **Dashboard Deployment**
   - Deploys dashboard after API is stable
   - Performs health checks
   - Swaps dashboard slots

### Manual Deployment Steps

If you need to deploy manually:

```bash
# 1. Create deployment slot
az webapp deployment slot create \
    --resource-group uris-ai-rg \
    --name uris-ai-api-production \
    --slot green \
    --configuration-source uris-ai-api-production

# 2. Deploy to green slot
cd src
zip -r ../api.zip .
cd ..

az webapp deployment source config-zip \
    --resource-group uris-ai-rg \
    --name uris-ai-api-production \
    --slot green \
    --src api.zip

# 3. Run smoke tests
export SMOKE_TEST_API_URL="https://uris-ai-api-production-green.azurewebsites.net"
./scripts/run_smoke_tests.sh

# 4. Swap slots
az webapp deployment slot swap \
    --resource-group uris-ai-rg \
    --name uris-ai-api-production \
    --slot green \
    --target-slot production
```

## Smoke Tests

### Test Categories

Smoke tests validate:

1. **Critical Endpoints**
   - Root endpoint (`/`)
   - Health check (`/health`)
   - Readiness check (`/health/ready`)
   - Liveness check (`/health/live`)
   - API documentation (`/docs`)

2. **Database Connectivity**
   - Database connection
   - Query performance

3. **External Services**
   - Cache (Redis) connectivity
   - Monitoring (Application Insights) connectivity

4. **Authentication**
   - Login endpoint accessibility
   - Register endpoint accessibility

5. **Core Functionality**
   - Risk assessment endpoints
   - Recommendation endpoints

6. **Performance**
   - Response time requirements
   - Health check latency

7. **Security**
   - HTTPS enforcement
   - CORS configuration

### Running Smoke Tests

```bash
# Against local environment
export SMOKE_TEST_API_URL="http://localhost:8000"
./scripts/run_smoke_tests.sh

# Against green slot
export SMOKE_TEST_API_URL="https://uris-ai-api-production-green.azurewebsites.net"
./scripts/run_smoke_tests.sh

# Against production
export SMOKE_TEST_API_URL="https://uris-ai-api-production.azurewebsites.net"
./scripts/run_smoke_tests.sh
```

### Test Configuration

Environment variables:

- `SMOKE_TEST_API_URL`: API endpoint to test
- `SMOKE_TEST_TIMEOUT`: Request timeout in seconds (default: 30)
- `SMOKE_TEST_MAX_RETRIES`: Maximum retry attempts (default: 3)
- `SMOKE_TEST_RETRY_DELAY`: Delay between retries in seconds (default: 5)

## Rollback Procedures

### Automatic Rollback

The deployment script includes automatic rollback:

- Monitors production for 60 seconds after swap
- Performs health checks every 10 seconds
- Automatically rolls back if 3 consecutive health checks fail
- Enabled by default (`ROLLBACK_ENABLED=true`)

### Manual Rollback

If you need to rollback manually:

```bash
# Using rollback script
export RESOURCE_GROUP="uris-ai-rg"
export ENVIRONMENT="production"
./scripts/rollback_deployment.sh

# Or using Azure CLI directly
az webapp deployment slot swap \
    --resource-group uris-ai-rg \
    --name uris-ai-api-production \
    --slot green \
    --target-slot production
```

### Rollback Time

- **Target**: < 2 minutes (Requirement 9.4)
- **Typical**: 30-60 seconds
- **Process**: Slot swap + health verification

## Monitoring and Alerting

### Health Checks

Three types of health checks:

1. **Liveness** (`/health/live`)
   - Confirms process is alive
   - Used by Kubernetes/Azure for restart decisions
   - Should always return 200

2. **Readiness** (`/health/ready`)
   - Verifies dependent services
   - Checks database, cache, monitoring
   - Used for traffic routing decisions

3. **Health** (`/health`)
   - Basic health indicator
   - Quick response for load balancers

### Traffic Manager

Traffic Manager provides automatic failover:

- Monitors `/health/ready` endpoint
- Checks every 30 seconds
- Timeout: 10 seconds
- Tolerates 3 failures before failover
- **Failover time**: < 2 minutes (Requirement 9.4)

### Application Insights

Monitors:

- Request rates and response times
- Error rates and exceptions
- Dependency health (database, cache)
- Custom events (deployments, rollbacks)

## Best Practices

### Pre-Deployment

1. **Test Locally**
   - Run full test suite
   - Verify smoke tests pass locally
   - Check for breaking changes

2. **Review Changes**
   - Review code changes
   - Check database migrations
   - Verify configuration changes

3. **Backup**
   - Backup database if needed
   - Document current version
   - Prepare rollback plan

### During Deployment

1. **Monitor Closely**
   - Watch deployment logs
   - Monitor Application Insights
   - Check health endpoints

2. **Validate Thoroughly**
   - Wait for smoke tests to complete
   - Verify critical functionality
   - Check performance metrics

3. **Communicate**
   - Notify team of deployment
   - Update status channels
   - Document any issues

### Post-Deployment

1. **Monitor Production**
   - Watch for errors
   - Check performance metrics
   - Verify user traffic

2. **Validate Functionality**
   - Test critical user flows
   - Verify integrations
   - Check data processing

3. **Document**
   - Record deployment time
   - Note any issues
   - Update runbooks

## Troubleshooting

### Deployment Fails at Smoke Tests

**Symptoms**: Smoke tests fail on green slot

**Solutions**:

1. Check green slot logs: `az webapp log tail --name uris-ai-api-production --slot green`
2. Verify configuration: Check app settings in Azure Portal
3. Test manually: `curl https://uris-ai-api-production-green.azurewebsites.net/health`
4. Check dependencies: Verify database and cache connectivity

### Slot Swap Fails

**Symptoms**: Error during slot swap

**Solutions**:

1. Check slot status: `az webapp deployment slot list --name uris-ai-api-production`
2. Verify permissions: Ensure sufficient Azure permissions
3. Check for locks: Remove any resource locks
4. Retry: Sometimes transient Azure issues resolve on retry

### Production Health Checks Fail After Swap

**Symptoms**: Health checks fail after successful swap

**Solutions**:

1. Check Application Insights for errors
2. Verify database connectivity
3. Check external service status
4. Rollback immediately: `./scripts/rollback_deployment.sh`

### Automatic Rollback Triggered

**Symptoms**: Deployment rolls back automatically

**Solutions**:

1. Review deployment logs
2. Check Application Insights for errors
3. Investigate health check failures
4. Fix issues and redeploy

## Configuration Reference

### Environment Variables

Deployment script:

- `RESOURCE_GROUP`: Azure resource group name
- `ENVIRONMENT`: Environment name (dev, staging, production)
- `API_APP_NAME`: API app service name
- `DASHBOARD_APP_NAME`: Dashboard app service name
- `SLOT_NAME`: Deployment slot name (default: green)
- `ROLLBACK_ENABLED`: Enable automatic rollback (default: true)

Smoke tests:

- `SMOKE_TEST_API_URL`: API endpoint to test
- `SMOKE_TEST_TIMEOUT`: Request timeout (default: 30)
- `SMOKE_TEST_MAX_RETRIES`: Retry attempts (default: 3)
- `SMOKE_TEST_RETRY_DELAY`: Retry delay (default: 5)

### Terraform Variables

```hcl
variable "enable_blue_green" {
  description = "Enable blue-green deployment slots"
  type        = bool
  default     = false
}

variable "deployment_slot_name" {
  description = "Name of the deployment slot"
  type        = string
  default     = "green"
}
```

## Security Considerations

1. **Secrets Management**
   - Use Azure Key Vault for secrets
   - Never commit secrets to version control
   - Rotate secrets regularly

2. **Access Control**
   - Limit deployment permissions
   - Use service principals for CI/CD
   - Enable audit logging

3. **Network Security**
   - Use HTTPS for all endpoints
   - Configure firewall rules
   - Enable DDoS protection

4. **Monitoring**
   - Enable Application Insights
   - Set up alerts for failures
   - Monitor security events

## CI/CD Integration

### GitHub Actions Example

```yaml
name: Deploy to Production

on:
  push:
    branches: [main]

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2

      - name: Azure Login
        uses: azure/login@v1
        with:
          creds: ${{ secrets.AZURE_CREDENTIALS }}

      - name: Run Blue-Green Deployment
        env:
          RESOURCE_GROUP: uris-ai-rg
          ENVIRONMENT: production
        run: ./scripts/blue_green_deploy.sh
```

### Azure DevOps Example

```yaml
trigger:
  branches:
    include:
      - main

pool:
  vmImage: "ubuntu-latest"

steps:
  - task: AzureCLI@2
    inputs:
      azureSubscription: "URIS-AI-Production"
      scriptType: "bash"
      scriptLocation: "scriptPath"
      scriptPath: "./scripts/blue_green_deploy.sh"
    env:
      RESOURCE_GROUP: "uris-ai-rg"
      ENVIRONMENT: "production"
```

## Support

For issues or questions:

1. Check Application Insights logs
2. Review deployment logs
3. Consult this documentation
4. Contact the development team

## References

- [Azure App Service Deployment Slots](https://docs.microsoft.com/en-us/azure/app-service/deploy-staging-slots)
- [Azure Traffic Manager](https://docs.microsoft.com/en-us/azure/traffic-manager/)
- [Blue-Green Deployment Pattern](https://martinfowler.com/bliki/BlueGreenDeployment.html)
