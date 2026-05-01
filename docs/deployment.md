# URIS-AI Deployment Guide

This guide covers the deployment process for URIS-AI to Azure cloud infrastructure.

## Prerequisites

- Azure CLI installed and configured
- Terraform installed (>= 1.0)
- Azure subscription with appropriate permissions
- Python 3.11+ installed
- Poetry package manager installed

## Infrastructure Setup

### 1. Initial Azure Setup

Login to Azure:

```bash
az login
```

Set your subscription:

```bash
az account set --subscription <subscription-id>
```

### 2. Configure Terraform Variables

Copy the example variables file:

```bash
cd infrastructure/terraform
cp terraform.tfvars.example terraform.tfvars
```

Edit `terraform.tfvars` with your values:

```hcl
resource_group_name = "uris-ai-rg"
location            = "southeastasia"
environment         = "dev"
sql_admin_username  = "sqladmin"
sql_admin_password  = "YourSecurePassword123!"
```

### 3. Deploy Infrastructure

Run the setup script:

```bash
./scripts/setup_azure.sh
```

This script will:

- Initialize Terraform
- Validate configuration
- Plan deployment
- Apply infrastructure changes
- Generate `.env` file with configuration

### 4. Manual Configuration

After infrastructure deployment, update the following in `.env`:

- `AZURE_SQL_PASSWORD`: Your SQL Server password
- `WEATHER_API_KEY`: Your weather API key
- `SECRET_KEY`: Generate a secure secret key

## Application Deployment

### Staging Deployment

Deploy to staging environment:

```bash
./scripts/deploy_staging.sh
```

This deploys to:

- API: `https://uris-ai-api-staging.azurewebsites.net`
- Dashboard: `https://uris-ai-dashboard-staging.azurewebsites.net`

### Production Deployment

Deploy to production using blue-green deployment:

```bash
./scripts/deploy_production.sh
```

This process:

1. Deploys to green slot
2. Runs smoke tests
3. Swaps slots (blue → green)
4. Monitors production
5. Allows rollback if needed

## CI/CD Pipeline

The project uses GitHub Actions for automated CI/CD.

### Pipeline Stages

1. **Build and Test**
   - Lint code (Ruff)
   - Type check (mypy)
   - Run unit tests
   - Generate coverage report

2. **Security Scan**
   - Run Trivy vulnerability scanner
   - Upload results to GitHub Security

3. **Deploy to Staging** (on `develop` branch)
   - Deploy API and Dashboard
   - Run E2E tests

4. **Deploy to Production** (on `main` branch)
   - Blue-green deployment
   - Smoke tests
   - Automatic slot swap

### Required Secrets

Configure these secrets in GitHub repository settings:

- `AZURE_CREDENTIALS`: Azure service principal credentials

```json
{
  "clientId": "<client-id>",
  "clientSecret": "<client-secret>",
  "subscriptionId": "<subscription-id>",
  "tenantId": "<tenant-id>"
}
```

## Monitoring

### Application Insights

Monitor application performance:

```bash
az monitor app-insights component show \
  --resource-group uris-ai-rg \
  --app uris-ai-appinsights
```

### Logs

View application logs:

```bash
az webapp log tail \
  --resource-group uris-ai-rg \
  --name uris-ai-api-production
```

## Rollback

### Manual Rollback

If issues occur after deployment, rollback to previous version:

```bash
az webapp deployment slot swap \
  --resource-group uris-ai-rg \
  --name uris-ai-api-production \
  --slot green \
  --target-slot production
```

### Automatic Rollback

The deployment script includes health checks and will prompt for rollback if production health check fails.

## Scaling

### Manual Scaling

Scale App Service:

```bash
az appservice plan update \
  --resource-group uris-ai-rg \
  --name uris-ai-asp-production \
  --sku P1V2 \
  --number-of-workers 3
```

### Auto-scaling

Configure auto-scaling rules:

```bash
az monitor autoscale create \
  --resource-group uris-ai-rg \
  --resource uris-ai-asp-production \
  --resource-type Microsoft.Web/serverfarms \
  --name autoscale-rules \
  --min-count 2 \
  --max-count 10 \
  --count 2
```

## Troubleshooting

### Deployment Fails

1. Check Azure CLI login: `az account show`
2. Verify Terraform state: `terraform show`
3. Check App Service logs: `az webapp log tail`

### Application Not Starting

1. Check environment variables in App Service
2. Verify database connection string
3. Check Application Insights for errors

### Database Connection Issues

1. Verify SQL Server firewall rules
2. Check connection string format
3. Ensure App Service has network access

## Best Practices

1. **Always test in staging first**
2. **Use blue-green deployment for production**
3. **Monitor application after deployment**
4. **Keep secrets in Azure Key Vault**
5. **Enable Application Insights**
6. **Configure auto-scaling for production**
7. **Regular backups of database**
8. **Use managed identities when possible**

## Support

For deployment issues, contact the DevOps team or open an issue in the repository.
