# URIS-AI Setup Guide

This guide will help you set up the URIS-AI development environment and deploy to Azure.

## Prerequisites

### Required Software

1. **Python 3.11 or higher**

   ```bash
   python --version
   ```

2. **Poetry** (Python package manager)

   ```bash
   curl -sSL https://install.python-poetry.org | python3 -
   ```

3. **Azure CLI**

   ```bash
   # Windows
   winget install Microsoft.AzureCLI

   # macOS
   brew install azure-cli

   # Linux
   curl -sL https://aka.ms/InstallAzureCLIDeb | sudo bash
   ```

4. **Terraform** (>= 1.0)

   ```bash
   # Windows
   winget install Hashicorp.Terraform

   # macOS
   brew install terraform

   # Linux
   wget https://releases.hashicorp.com/terraform/1.6.0/terraform_1.6.0_linux_amd64.zip
   unzip terraform_1.6.0_linux_amd64.zip
   sudo mv terraform /usr/local/bin/
   ```

5. **Git**
   ```bash
   git --version
   ```

### Azure Requirements

- Active Azure subscription
- Permissions to create resources
- Service principal for CI/CD (optional)

## Local Development Setup

### 1. Clone Repository

```bash
git clone <repository-url>
cd uris-ai
```

### 2. Install Dependencies

```bash
# Install Python dependencies
poetry install

# Activate virtual environment
poetry shell
```

### 3. Configure Environment

```bash
# Copy example environment file
cp .env.example .env

# Edit .env with your configuration
# You can use any text editor
nano .env
```

Required environment variables:

- `AZURE_SUBSCRIPTION_ID`
- `AZURE_TENANT_ID`
- `AZURE_SQL_CONNECTION_STRING`
- `AZURE_STORAGE_CONNECTION_STRING`
- `SECRET_KEY`

### 4. Run Tests

```bash
# Run all tests
poetry run pytest

# Run with coverage
poetry run pytest --cov=src/uris_ai --cov-report=html

# Run specific test
poetry run pytest tests/test_config.py -v
```

### 5. Run API Server

```bash
# Development mode with auto-reload
poetry run uvicorn uris_ai.api.main:app --reload

# Or using the main script
poetry run python -m uris_ai.api.main
```

API will be available at:

- API: http://localhost:8000
- Docs: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

### 6. Run Dashboard

```bash
poetry run streamlit run src/uris_ai/dashboard/app.py
```

Dashboard will be available at: http://localhost:8501

## Azure Infrastructure Setup

### 1. Login to Azure

```bash
az login
```

### 2. Set Subscription

```bash
# List subscriptions
az account list --output table

# Set active subscription
az account set --subscription <subscription-id>
```

### 3. Configure Terraform

```bash
cd infrastructure/terraform

# Copy example variables
cp terraform.tfvars.example terraform.tfvars

# Edit terraform.tfvars
nano terraform.tfvars
```

Required variables:

```hcl
resource_group_name = "uris-ai-rg"
location            = "southeastasia"
environment         = "dev"
sql_admin_username  = "sqladmin"
sql_admin_password  = "YourSecurePassword123!"
```

### 4. Deploy Infrastructure

Option A: Using setup script (recommended)

```bash
./scripts/setup_azure.sh
```

Option B: Manual Terraform commands

```bash
cd infrastructure/terraform

# Initialize Terraform
terraform init

# Plan deployment
terraform plan -out=tfplan

# Apply deployment
terraform apply tfplan
```

### 5. Verify Deployment

```bash
# Check resource group
az group show --name uris-ai-rg

# List resources
az resource list --resource-group uris-ai-rg --output table

# Test API endpoint
curl https://uris-ai-api-dev.azurewebsites.net/health
```

## Database Setup

### 1. Connect to Azure SQL Database

```bash
# Using Azure CLI
az sql db show-connection-string \
  --server uris-ai-sql-server-dev \
  --name uris-ai-db \
  --client sqlcmd
```

### 2. Run Database Migrations

```bash
# TODO: Add migration commands when database schema is implemented
# Example:
# poetry run alembic upgrade head
```

## Development Workflow

### 1. Create Feature Branch

```bash
git checkout -b feature/your-feature-name
```

### 2. Make Changes

```bash
# Edit code
# Run tests
poetry run pytest

# Format code
poetry run black src/ tests/

# Lint code
poetry run ruff check src/ tests/

# Type check
poetry run mypy src/
```

### 3. Commit Changes

```bash
git add .
git commit -m "feat: your feature description"
```

### 4. Push and Create PR

```bash
git push origin feature/your-feature-name
```

Then create a Pull Request on GitHub.

## Troubleshooting

### Poetry Installation Issues

```bash
# Clear cache
poetry cache clear pypi --all

# Reinstall dependencies
poetry install --no-cache
```

### Azure CLI Login Issues

```bash
# Clear cached credentials
az account clear

# Login again
az login
```

### Terraform State Issues

```bash
# Refresh state
terraform refresh

# If state is corrupted, you may need to import resources
terraform import azurerm_resource_group.main /subscriptions/<sub-id>/resourceGroups/uris-ai-rg
```

### Database Connection Issues

1. Check firewall rules in Azure Portal
2. Verify connection string in .env
3. Ensure your IP is whitelisted

### Port Already in Use

```bash
# Find process using port 8000
lsof -i :8000

# Kill process
kill -9 <PID>
```

## Next Steps

1. Review [Architecture Documentation](architecture.md)
2. Read [API Documentation](api.md)
3. Check [Deployment Guide](deployment.md)
4. Explore [User Guide](user-guide.md)

## Getting Help

- Check documentation in `docs/` folder
- Open an issue on GitHub
- Contact the development team

## Useful Commands

```bash
# Run API server
poetry run uvicorn uris_ai.api.main:app --reload

# Run dashboard
poetry run streamlit run src/uris_ai/dashboard/app.py

# Run tests
poetry run pytest

# Format code
poetry run black src/ tests/

# Lint code
poetry run ruff check src/ tests/

# Type check
poetry run mypy src/

# Deploy to staging
./scripts/deploy_staging.sh

# Deploy to production
./scripts/deploy_production.sh
```
