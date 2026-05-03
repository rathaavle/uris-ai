# URIS-AI Developer Documentation

**Urban Risk Intelligence System for Flood-Aware Mobility and Public Service Optimization**

**Version:** 1.0.0  
**Last Updated:** January 20, 2024

---

## Table of Contents

1. [Architecture Overview](#architecture-overview)
2. [Setup Instructions](#setup-instructions)
3. [Development Workflow](#development-workflow)
4. [Project Structure](#project-structure)
5. [Core Components](#core-components)
6. [Testing Strategy](#testing-strategy)
7. [Deployment Guide](#deployment-guide)
8. [API Reference](#api-reference)
9. [Contributing Guidelines](#contributing-guidelines)

**Requirements:** 9.1

---

## Architecture Overview

### System Architecture

URIS-AI uses a layered architecture deployed on Microsoft Azure:

```
┌─────────────────────────────────────────────────────────────┐
│                    Presentation Layer                        │
│              (Streamlit Dashboard + Azure Maps)              │
└─────────────────────────────────────────────────────────────┘
                              ↕
┌─────────────────────────────────────────────────────────────┐
│                     Application Layer                        │
│         (FastAPI + Business Logic + Cache Manager)           │
└─────────────────────────────────────────────────────────────┐
                              ↕
┌─────────────────────────────────────────────────────────────┐
│                      AI/ML Layer                             │
│    (Flood Risk + Traffic + Accessibility + Scoring)          │
└─────────────────────────────────────────────────────────────┘
                              ↕
┌─────────────────────────────────────────────────────────────┐
│                  Data Processing Layer                       │
│         (Cleaning + Integration + Feature Engineering)       │
└─────────────────────────────────────────────────────────────┘
                              ↕
┌─────────────────────────────────────────────────────────────┐
│                   Data Ingestion Layer                       │
│        (API Connectors + Validators + Schedulers)            │
└─────────────────────────────────────────────────────────────┘
                              ↕
┌─────────────────────────────────────────────────────────────┐
│                      Data Storage                            │
│         (Azure Blob Storage + Azure SQL Database)            │
└─────────────────────────────────────────────────────────────┘
```

### Technology Stack

**Backend:**

- Python 3.11+
- FastAPI (REST API framework)
- SQLAlchemy (ORM)
- Pydantic (data validation)
- Uvicorn (ASGI server)

**Frontend:**

- Streamlit (dashboard framework)
- Plotly (interactive charts)
- Folium/Azure Maps (map visualization)

**Database:**

- Azure SQL Database (operational data)
- Azure Blob Storage (raw data, models)

**Caching:**

- Azure Cache for Redis

**ML/AI:**

- scikit-learn (ML models)
- TensorFlow (deep learning, optional)
- Azure Machine Learning (model deployment)

**Testing:**

- pytest (unit & integration tests)
- Hypothesis (property-based testing)
- pytest-cov (coverage reporting)

**Infrastructure:**

- Terraform (Infrastructure as Code)
- Azure App Service (hosting)
- Azure Key Vault (secrets management)
- Azure Application Insights (monitoring)

**CI/CD:**

- GitHub Actions
- Azure DevOps (optional)

### Key Design Principles

1. **Modularity** - Independent, loosely coupled components
2. **Scalability** - Horizontal and vertical scaling support
3. **Resilience** - Graceful degradation and error handling
4. **Real-time** - Sub-60 second data processing
5. **Security** - Defense in depth, least privilege

---

## Setup Instructions

### Prerequisites

**Required Software:**

1. **Python 3.11+**

   ```bash
   python --version  # Should be 3.11 or higher
   ```

2. **Poetry** (dependency management)

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
   # macOS
   brew install terraform

   # Windows
   winget install Hashicorp.Terraform
   ```

5. **Git**
   ```bash
   git --version
   ```

**Azure Requirements:**

- Active Azure subscription
- Permissions to create resources
- Service principal for CI/CD (optional)

### Local Development Setup

**1. Clone Repository**

```bash
git clone https://github.com/your-org/uris-ai.git
cd uris-ai
```

**2. Install Dependencies**

```bash
# Install Python dependencies
poetry install

# Activate virtual environment
poetry shell
```

**3. Configure Environment**

```bash
# Copy example environment file
cp .env.example .env

# Edit .env with your configuration
nano .env
```

**Required Environment Variables:**

```bash
# Azure Configuration
AZURE_SUBSCRIPTION_ID=your-subscription-id
AZURE_TENANT_ID=your-tenant-id
AZURE_SQL_CONNECTION_STRING=your-connection-string
AZURE_STORAGE_CONNECTION_STRING=your-storage-connection-string
AZURE_KEY_VAULT_URL=https://your-keyvault.vault.azure.net/

# Application Configuration
SECRET_KEY=your-secret-key-min-32-chars
APP_NAME=URIS-AI
APP_VERSION=1.0.0
ENVIRONMENT=development

# API Configuration
API_HOST=0.0.0.0
API_PORT=8000
API_RELOAD=true
API_WORKERS=1

# Database Configuration
DATABASE_URL=postgresql://user:pass@localhost/uris_ai

# Redis Configuration
REDIS_URL=redis://localhost:6379/0

# External APIs
WEATHER_API_KEY=your-weather-api-key
WEATHER_API_URL=https://api.weather.com

# Security
ENABLE_RATE_LIMITING=true
RATE_LIMIT_PER_MINUTE=60
RATE_LIMIT_PER_HOUR=1000
ENFORCE_HTTPS=false  # Set to true in production

# Monitoring
APPLICATIONINSIGHTS_CONNECTION_STRING=your-app-insights-connection-string
```

**4. Run Tests**

```bash
# Run all tests
poetry run pytest

# Run with coverage
poetry run pytest --cov=src/uris_ai --cov-report=html

# Run specific test file
poetry run pytest tests/test_config.py -v

# Run property-based tests
poetry run pytest tests/property/ -v
```

**5. Run API Server**

```bash
# Development mode with auto-reload
poetry run uvicorn uris_ai.api.main:app --reload --host 0.0.0.0 --port 8000

# Or using the main script
poetry run python -m uris_ai.api.main
```

API will be available at:

- **API:** http://localhost:8000
- **Swagger UI:** http://localhost:8000/docs
- **ReDoc:** http://localhost:8000/redoc
- **OpenAPI JSON:** http://localhost:8000/openapi.json

**6. Run Dashboard**

```bash
poetry run streamlit run src/uris_ai/dashboard/app.py
```

Dashboard will be available at: http://localhost:8501

**7. Run Database Migrations**

```bash
# Create migration
poetry run alembic revision --autogenerate -m "Description"

# Apply migrations
poetry run alembic upgrade head

# Rollback migration
poetry run alembic downgrade -1
```

---

## Development Workflow

### Branch Strategy

We use **Git Flow**:

- `main` - Production-ready code
- `develop` - Integration branch for features
- `feature/*` - New features
- `bugfix/*` - Bug fixes
- `hotfix/*` - Emergency production fixes
- `release/*` - Release preparation

### Creating a Feature

**1. Create Feature Branch**

```bash
git checkout develop
git pull origin develop
git checkout -b feature/your-feature-name
```

**2. Make Changes**

```bash
# Edit code
# Write tests
# Run tests
poetry run pytest

# Format code
poetry run black src/ tests/

# Lint code
poetry run ruff check src/ tests/

# Type check
poetry run mypy src/
```

**3. Commit Changes**

Follow [Conventional Commits](https://www.conventionalcommits.org/):

```bash
git add .
git commit -m "feat: add flood risk prediction endpoint"
```

**Commit Types:**

- `feat:` - New feature
- `fix:` - Bug fix
- `docs:` - Documentation changes
- `style:` - Code style changes (formatting)
- `refactor:` - Code refactoring
- `test:` - Adding or updating tests
- `chore:` - Maintenance tasks

**4. Push and Create PR**

```bash
git push origin feature/your-feature-name
```

Then create a Pull Request on GitHub targeting `develop` branch.

### Code Review Process

1. **Automated Checks** - CI pipeline runs tests, linting, type checking
2. **Peer Review** - At least one approval required
3. **Security Review** - For security-sensitive changes
4. **Merge** - Squash and merge to `develop`

### Code Quality Standards

**Formatting:**

```bash
# Format with Black
poetry run black src/ tests/

# Check formatting
poetry run black --check src/ tests/
```

**Linting:**

```bash
# Lint with Ruff
poetry run ruff check src/ tests/

# Auto-fix issues
poetry run ruff check --fix src/ tests/
```

**Type Checking:**

```bash
# Type check with mypy
poetry run mypy src/

# Strict mode
poetry run mypy --strict src/
```

**Testing:**

```bash
# Run all tests
poetry run pytest

# Run with coverage (minimum 80%)
poetry run pytest --cov=src/uris_ai --cov-report=term --cov-fail-under=80

# Run specific test
poetry run pytest tests/test_flood_risk_engine.py::test_predict_flood_risk -v
```

---

## Project Structure

```
uris-ai/
├── .github/
│   └── workflows/          # GitHub Actions CI/CD
├── .kiro/
│   └── specs/              # Feature specifications
├── data/
│   ├── raw/                # Raw data from external sources
│   └── processed/          # Processed data
├── docs/                   # Documentation
│   ├── api_documentation.md
│   ├── user_guide.md
│   ├── developer_documentation.md
│   ├── operations_runbook.md
│   ├── architecture.md
│   ├── setup.md
│   └── deployment.md
├── infrastructure/
│   └── terraform/          # Infrastructure as Code
│       ├── main.tf
│       ├── variables.tf
│       └── outputs.tf
├── logs/                   # Application logs
├── models/                 # Trained ML models
├── scripts/                # Deployment and utility scripts
│   ├── setup_azure.sh
│   ├── deploy_staging.sh
│   ├── deploy_production.sh
│   ├── blue_green_deploy.sh
│   ├── rollback_deployment.sh
│   ├── seed_data.py
│   └── migrate_data.py
├── src/
│   └── uris_ai/
│       ├── api/            # FastAPI application
│       │   ├── routers/    # API route handlers
│       │   │   ├── auth.py
│       │   │   ├── users.py
│       │   │   ├── risk.py
│       │   │   └── recommendations.py
│       │   ├── main.py     # FastAPI app factory
│       │   ├── dependencies.py
│       │   ├── middleware.py
│       │   └── schemas.py  # Pydantic models
│       ├── dashboard/      # Streamlit dashboard
│       │   ├── components/ # UI components
│       │   │   ├── filters.py
│       │   │   ├── map_visualizer.py
│       │   │   ├── risk_dashboard.py
│       │   │   ├── recommendation_panel.py
│       │   │   └── user_interface.py
│       │   └── app.py      # Main dashboard app
│       ├── data/           # Data ingestion & processing
│       │   ├── integrators/
│       │   │   ├── weather_api_connector.py
│       │   │   ├── historical_flood_loader.py
│       │   │   └── osm_data_fetcher.py
│       │   ├── processors/
│       │   │   ├── data_cleaner.py
│       │   │   ├── data_transformer.py
│       │   │   ├── feature_engineer.py
│       │   │   └── region_integrator.py
│       │   └── validators/
│       │       └── data_validator.py
│       ├── ml/             # ML/AI models
│       │   ├── flood_risk_engine.py
│       │   ├── traffic_analyzer.py
│       │   ├── service_accessibility_module.py
│       │   ├── risk_scoring_engine.py
│       │   └── recommendation_engine.py
│       ├── models/         # Database models
│       │   ├── database.py # SQLAlchemy models
│       │   └── db_utils.py
│       ├── services/       # Business logic services
│       │   ├── auth_service.py
│       │   ├── cache_service.py
│       │   └── key_vault_service.py
│       ├── utils/          # Utility modules
│       │   ├── logging_config.py
│       │   ├── monitoring.py
│       │   └── alerting.py
│       ├── config.py       # Configuration management
│       ├── startup.py      # Startup optimization
│       └── __init__.py
├── tests/                  # Test suite
│   ├── unit/               # Unit tests
│   ├── integration/        # Integration tests
│   ├── property/           # Property-based tests
│   └── conftest.py         # Pytest fixtures
├── .env.example            # Example environment variables
├── .gitignore
├── pyproject.toml          # Poetry configuration
├── README.md
└── LICENSE
```

---

## Core Components

### 1. Data Ingestion Layer

**Location:** `src/uris_ai/data/integrators/`

**Components:**

- **WeatherAPIConnector** - Fetches weather data from BMKG or equivalent API
- **HistoricalFloodLoader** - Loads historical flood data
- **OSMDataFetcher** - Fetches road and facility data from OpenStreetMap

**Example Usage:**

```python
from uris_ai.data.integrators import WeatherAPIConnector

connector = WeatherAPIConnector(api_key="your-api-key")
weather_data = await connector.fetch_weather_data(region_id=3174010)
```

### 2. Data Processing Layer

**Location:** `src/uris_ai/data/processors/`

**Components:**

- **DataCleaner** - Handles missing values, outliers
- **DataTransformer** - Normalization, encoding
- **FeatureEngineer** - Creates ML features
- **RegionIntegrator** - Integrates multi-source data by region

**Example Usage:**

```python
from uris_ai.data.processors import DataCleaner

cleaner = DataCleaner()
cleaned_data = cleaner.clean(raw_data)
```

### 3. AI/ML Layer

**Location:** `src/uris_ai/ml/`

**Components:**

- **FloodRiskEngine** - Predicts flood risk (0-100)
- **TrafficAnalyzer** - Analyzes traffic impact
- **ServiceAccessibilityModule** - Evaluates facility accessibility
- **RiskScoringEngine** - Calculates Urban Risk Score
- **RecommendationEngine** - Generates action recommendations

**Example Usage:**

```python
from uris_ai.ml import FloodRiskEngine

engine = FloodRiskEngine()
risk_score = engine.predict_flood_risk(
    region_id=3174010,
    weather_data=weather_data
)
print(f"Flood Risk: {risk_score}")  # 75.5
```

### 4. Application Layer

**Location:** `src/uris_ai/api/`

**Components:**

- **FastAPI App** - REST API server
- **Routers** - Endpoint handlers (auth, users, risk, recommendations)
- **Middleware** - Rate limiting, logging, HTTPS redirect
- **Dependencies** - Dependency injection (DB, auth, cache)

**Example Usage:**

```python
from fastapi import FastAPI, Depends
from uris_ai.api.dependencies import get_current_user

app = FastAPI()

@app.get("/protected")
async def protected_route(user = Depends(get_current_user)):
    return {"message": f"Hello {user.username}"}
```

### 5. Presentation Layer

**Location:** `src/uris_ai/dashboard/`

**Components:**

- **MapVisualizer** - Interactive map with risk visualization
- **RiskDashboard** - Risk score display and trends
- **RecommendationPanel** - Action recommendations
- **Filters** - Time, region, category filters

**Example Usage:**

```python
import streamlit as st
from uris_ai.dashboard.components import MapVisualizer

st.title("URIS-AI Dashboard")
map_viz = MapVisualizer()
map_viz.render(risk_data=risk_data)
```

---

## Testing Strategy

### Test Types

**1. Unit Tests** (`tests/unit/`)

Test individual functions and classes in isolation.

```python
# tests/unit/test_flood_risk_engine.py
import pytest
from uris_ai.ml import FloodRiskEngine

def test_get_risk_category():
    engine = FloodRiskEngine()

    assert engine.get_risk_category(25.0).value == "RENDAH"
    assert engine.get_risk_category(45.0).value == "SEDANG"
    assert engine.get_risk_category(75.0).value == "TINGGI"
    assert engine.get_risk_category(95.0).value == "KRITIS"
```

**2. Integration Tests** (`tests/integration/`)

Test interactions between components.

```python
# tests/integration/test_api_endpoints.py
import pytest
from fastapi.testclient import TestClient
from uris_ai.api.main import app

client = TestClient(app)

def test_get_region_risk(auth_token):
    response = client.get(
        "/regions/3174010/risk",
        headers={"Authorization": f"Bearer {auth_token}"}
    )
    assert response.status_code == 200
    data = response.json()
    assert "urban_risk_score" in data
    assert 0 <= data["urban_risk_score"] <= 100
```

**3. Property-Based Tests** (`tests/property/`)

Test universal properties using Hypothesis.

```python
# tests/property/test_risk_scoring.py
from hypothesis import given, strategies as st
from uris_ai.ml import RiskScoringEngine

@given(
    flood_risk=st.floats(min_value=0, max_value=100),
    traffic_impact=st.floats(min_value=0, max_value=100),
    service_access=st.floats(min_value=0, max_value=100),
)
def test_urban_risk_score_bounds(flood_risk, traffic_impact, service_access):
    """Urban Risk Score should always be between 0 and 100."""
    engine = RiskScoringEngine()
    urs = engine.calculate_urban_risk_score(
        flood_risk=flood_risk,
        traffic_impact=traffic_impact,
        service_access=service_access,
    )
    assert 0 <= urs <= 100
```

### Running Tests

```bash
# Run all tests
poetry run pytest

# Run specific test type
poetry run pytest tests/unit/
poetry run pytest tests/integration/
poetry run pytest tests/property/

# Run with coverage
poetry run pytest --cov=src/uris_ai --cov-report=html

# Run specific test
poetry run pytest tests/unit/test_flood_risk_engine.py::test_get_risk_category -v

# Run tests matching pattern
poetry run pytest -k "test_risk" -v

# Run with verbose output
poetry run pytest -vv

# Run with print statements
poetry run pytest -s
```

### Test Fixtures

Common fixtures are defined in `tests/conftest.py`:

```python
# tests/conftest.py
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

@pytest.fixture
def db_session():
    """Provide a test database session."""
    engine = create_engine("sqlite:///:memory:")
    Session = sessionmaker(bind=engine)
    session = Session()
    yield session
    session.close()

@pytest.fixture
def auth_token():
    """Provide a test authentication token."""
    from uris_ai.services.auth_service import AuthService
    auth = AuthService()
    return auth.create_access_token(subject="testuser", role="government")
```

---

## Deployment Guide

### Deployment Environments

1. **Development** - Local development environment
2. **Staging** - Pre-production testing environment
3. **Production** - Live production environment

### Infrastructure Deployment

**1. Configure Terraform**

```bash
cd infrastructure/terraform
cp terraform.tfvars.example terraform.tfvars
nano terraform.tfvars
```

**2. Deploy Infrastructure**

```bash
# Using setup script (recommended)
./scripts/setup_azure.sh

# Or manually
cd infrastructure/terraform
terraform init
terraform plan -out=tfplan
terraform apply tfplan
```

### Application Deployment

**Staging Deployment:**

```bash
./scripts/deploy_staging.sh
```

**Production Deployment (Blue-Green):**

```bash
./scripts/deploy_production.sh
```

This script:

1. Deploys to green slot
2. Runs smoke tests
3. Swaps slots (blue → green)
4. Monitors production
5. Allows rollback if needed

**Manual Rollback:**

```bash
./scripts/rollback_deployment.sh
```

### CI/CD Pipeline

The project uses GitHub Actions for automated CI/CD.

**Pipeline Stages:**

1. **Build & Test** - Lint, type check, run tests
2. **Security Scan** - Vulnerability scanning
3. **Deploy to Staging** - On `develop` branch
4. **Deploy to Production** - On `main` branch

**Required GitHub Secrets:**

- `AZURE_CREDENTIALS` - Azure service principal credentials
- `AZURE_SQL_PASSWORD` - SQL Server password
- `SECRET_KEY` - Application secret key
- `WEATHER_API_KEY` - Weather API key

---

## API Reference

See [API Documentation](api_documentation.md) for complete API reference.

**Quick Reference:**

- `POST /auth/login` - User login
- `POST /auth/logout` - User logout
- `GET /users/me` - Get current user
- `GET /regions/{region_id}/risk` - Get risk score
- `GET /regions/risk` - Get all risk scores
- `GET /regions/{region_id}/risk/trend` - Get risk trend
- `GET /regions/{region_id}/recommendations` - Get recommendations
- `POST /routes/safe` - Find safe route
- `GET /health` - Health check
- `GET /health/ready` - Readiness check
- `GET /health/live` - Liveness check

---

## Contributing Guidelines

### Code Style

- Follow PEP 8 style guide
- Use Black for formatting
- Use Ruff for linting
- Use mypy for type checking
- Write docstrings for all public functions/classes

### Documentation

- Update documentation for new features
- Add docstrings with examples
- Update API documentation
- Add inline comments for complex logic

### Testing

- Write tests for all new code
- Maintain minimum 80% code coverage
- Include unit, integration, and property-based tests
- Test edge cases and error conditions

### Pull Requests

- Create feature branch from `develop`
- Write clear commit messages
- Include tests and documentation
- Request review from team members
- Address review feedback promptly

### Security

- Never commit secrets or credentials
- Use Azure Key Vault for secrets
- Follow OWASP security guidelines
- Report security issues privately

---

## Additional Resources

- **Architecture:** [architecture.md](architecture.md)
- **Setup Guide:** [setup.md](setup.md)
- **Deployment Guide:** [deployment.md](deployment.md)
- **API Documentation:** [api_documentation.md](api_documentation.md)
- **User Guide:** [user_guide.md](user_guide.md)
- **Operations Runbook:** [operations_runbook.md](operations_runbook.md)

---

## Support

For development questions or issues:

- **Email:** dev-team@uris-ai.go.id
- **Slack:** #uris-ai-dev
- **GitHub Issues:** https://github.com/your-org/uris-ai/issues

---

**Happy Coding!** 🚀
