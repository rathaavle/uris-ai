# URIS-AI Quick Start Guide

Get URIS-AI up and running in minutes!

## Prerequisites

- Python 3.11+
- Poetry
- Azure CLI
- Terraform
- Azure subscription

## Quick Setup (5 minutes)

### 1. Install Dependencies

```bash
# Install Python dependencies
poetry install

# Activate virtual environment
poetry shell
```

### 2. Configure Environment

```bash
# Copy environment template
cp .env.example .env

# Edit .env with your Azure credentials
# Minimum required:
# - AZURE_SUBSCRIPTION_ID
# - AZURE_TENANT_ID
# - SECRET_KEY (generate with: openssl rand -hex 32)
```

### 3. Run Locally (Without Azure)

```bash
# Terminal 1: Run API
poetry run uvicorn uris_ai.api.main:app --reload

# Terminal 2: Run Dashboard
poetry run streamlit run src/uris_ai/dashboard/app.py
```

Access:

- API: http://localhost:8000
- API Docs: http://localhost:8000/docs
- Dashboard: http://localhost:8501

## Azure Deployment (15 minutes)

### 1. Login to Azure

```bash
az login
az account set --subscription <your-subscription-id>
```

### 2. Configure Terraform

```bash
cd infrastructure/terraform
cp terraform.tfvars.example terraform.tfvars

# Edit terraform.tfvars:
# - resource_group_name
# - location
# - environment
# - sql_admin_username
# - sql_admin_password
```

### 3. Deploy Infrastructure

```bash
# Make scripts executable (Unix/Linux/Mac)
chmod +x scripts/*.sh

# Run setup script
./scripts/setup_azure.sh
```

This will:

- Create Azure resources
- Configure services
- Generate .env file

### 4. Verify Deployment

```bash
# Check resources
az resource list --resource-group uris-ai-rg --output table

# Test API
curl https://uris-ai-api-dev.azurewebsites.net/health
```

## Development Workflow

### Run Tests

```bash
# All tests
poetry run pytest

# With coverage
poetry run pytest --cov=src/uris_ai --cov-report=html

# Specific test
poetry run pytest tests/test_config.py -v
```

### Code Quality

```bash
# Format code
poetry run black src/ tests/

# Lint code
poetry run ruff check src/ tests/

# Type check
poetry run mypy src/
```

### Deploy to Staging

```bash
./scripts/deploy_staging.sh
```

### Deploy to Production

```bash
./scripts/deploy_production.sh
```

## Common Commands

```bash
# Start API server
poetry run uvicorn uris_ai.api.main:app --reload

# Start dashboard
poetry run streamlit run src/uris_ai/dashboard/app.py

# Run tests
poetry run pytest

# Format code
poetry run black src/ tests/

# Check Azure resources
az resource list --resource-group uris-ai-rg --output table

# View API logs
az webapp log tail --resource-group uris-ai-rg --name uris-ai-api-dev
```

## Troubleshooting

### Poetry Issues

```bash
poetry cache clear pypi --all
poetry install --no-cache
```

### Azure Login Issues

```bash
az account clear
az login
```

### Port Already in Use

```bash
# Windows
netstat -ano | findstr :8000
taskkill /PID <PID> /F

# Unix/Linux/Mac
lsof -i :8000
kill -9 <PID>
```

## Next Steps

1. ✅ Project setup complete
2. 📖 Read [Architecture Documentation](docs/architecture.md)
3. 🔧 Implement database schema (Task 2)
4. 📊 Implement data ingestion (Task 3)
5. 🤖 Implement ML models (Tasks 6-12)
6. 🎨 Implement dashboard (Task 15)

## Getting Help

- 📚 Check [docs/](docs/) folder
- 🐛 Open an issue on GitHub
- 💬 Contact the development team

## Resources

- [Full Setup Guide](docs/setup.md)
- [Deployment Guide](docs/deployment.md)
- [Architecture Overview](docs/architecture.md)
- [Contributing Guidelines](CONTRIBUTING.md)

---

**Ready to build?** Start with Task 2: Database Schema Implementation! 🚀
