# URIS-AI

**Urban Risk Intelligence System for Flood-Aware Mobility and Public Service Optimization**

_From Data to Decision for Smarter Urban Resilience_

## Overview

URIS-AI adalah sistem berbasis cloud yang mengintegrasikan data multi-sumber untuk memprediksi dan menganalisis risiko urban secara komprehensif. Sistem ini menggunakan arsitektur modular berbasis Azure untuk memproses data cuaca, historis banjir, jaringan transportasi, dan fasilitas publik, kemudian menyajikan hasil analisis melalui dashboard interaktif.

## Features

- **Prediksi Risiko Banjir**: Prediksi risiko banjir per wilayah menggunakan AI/ML
- **Analisis Dampak Lalu Lintas**: Analisis dampak banjir terhadap kondisi lalu lintas
- **Aksesibilitas Layanan Publik**: Monitoring aksesibilitas fasilitas publik saat banjir
- **Urban Risk Score**: Skor risiko terpadu untuk prioritisasi alokasi sumber daya
- **Sistem Rekomendasi**: Rekomendasi tindakan dan rute alternatif
- **Dashboard Interaktif**: Visualisasi peta interaktif dengan real-time updates

## Technology Stack

- **Backend**: Python 3.11+, FastAPI
- **Frontend**: Streamlit
- **Database**: Azure SQL Database
- **Storage**: Azure Blob Storage
- **ML**: Azure Machine Learning, scikit-learn
- **Testing**: pytest, Hypothesis (property-based testing)
- **Cloud**: Microsoft Azure

## Project Structure

```
uris-ai/
├── src/
│   └── uris_ai/
│       ├── api/              # FastAPI application
│       ├── dashboard/        # Streamlit dashboard
│       ├── data/             # Data ingestion and processing
│       ├── ml/               # ML models and engines
│       ├── models/           # Database models
│       ├── services/         # Business logic services
│       └── utils/            # Utility functions
├── tests/                    # Test files
├── infrastructure/           # Infrastructure as Code (Terraform/ARM)
├── .github/workflows/        # CI/CD pipelines
├── docs/                     # Documentation
└── scripts/                  # Utility scripts
```

## Prerequisites

- Python 3.11 or higher
- Poetry (Python package manager)
- Azure CLI
- Azure subscription

## Installation

### 1. Clone the repository

```bash
git clone <repository-url>
cd uris-ai
```

### 2. Install dependencies

```bash
poetry install
```

### 3. Configure environment variables

Copy the example environment file and configure your settings:

```bash
cp .env.example .env
```

Edit `.env` with your Azure credentials and configuration.

### 4. Setup Azure resources

```bash
# Login to Azure
az login

# Run infrastructure setup script
./scripts/setup_azure.sh
```

## Development

### Running the API server

```bash
poetry run uvicorn uris_ai.api.main:app --reload
```

The API will be available at `http://localhost:8000`

API documentation: `http://localhost:8000/docs`

### Running the Dashboard

```bash
poetry run streamlit run src/uris_ai/dashboard/app.py
```

The dashboard will be available at `http://localhost:8501`

### Running tests

```bash
# Run all tests
poetry run pytest

# Run with coverage
poetry run pytest --cov=src/uris_ai --cov-report=html

# Run specific test file
poetry run pytest tests/test_flood_risk_engine.py

# Run property-based tests
poetry run pytest tests/property/ -v
```

### Code formatting and linting

```bash
# Format code with Black
poetry run black src/ tests/

# Lint with Ruff
poetry run ruff check src/ tests/

# Type checking with mypy
poetry run mypy src/
```

## Deployment

### Azure Deployment

The project uses blue-green deployment strategy for zero-downtime updates.

```bash
# Deploy to staging
./scripts/deploy_staging.sh

# Deploy to production
./scripts/deploy_production.sh
```

### CI/CD Pipeline

The project uses GitHub Actions for CI/CD:

- **Build**: Compile and package
- **Test**: Run unit tests, property tests, and integration tests
- **Security Scan**: Run security scans
- **Deploy to Staging**: Deploy to staging environment
- **E2E Tests**: Run end-to-end tests
- **Deploy to Production**: Blue-green deployment

## Configuration

### Environment Variables

Key environment variables (see `.env.example` for full list):

- `AZURE_SUBSCRIPTION_ID`: Azure subscription ID
- `AZURE_RESOURCE_GROUP`: Resource group name
- `AZURE_SQL_CONNECTION_STRING`: SQL Database connection string
- `AZURE_STORAGE_CONNECTION_STRING`: Blob Storage connection string
- `AZURE_KEY_VAULT_URL`: Key Vault URL
- `WEATHER_API_KEY`: Weather API key
- `REDIS_URL`: Redis cache URL

### Azure Resources

Required Azure resources:

- Resource Group
- App Service (API)
- App Service (Dashboard)
- Azure SQL Database
- Azure Blob Storage
- Azure Cache for Redis
- Azure Key Vault
- Azure Machine Learning Workspace
- Azure Active Directory

## Monitoring

The system uses Azure Application Insights for monitoring:

- Application metrics (request rate, response time, error rate)
- Infrastructure metrics (CPU, memory, disk, network)
- Business metrics (active users, predictions generated)
- Alerting for critical issues

## Security

- Role-Based Access Control (RBAC) with 3 roles
- Azure Active Directory for authentication
- TLS 1.2+ for all communication
- Azure Key Vault for secrets management
- Input validation and sanitization

## Documentation

- [Architecture Overview](docs/architecture.md)
- [API Documentation](docs/api.md)
- [User Guide](docs/user-guide.md)
- [Developer Guide](docs/developer-guide.md)
- [Deployment Guide](docs/deployment.md)

## Contributing

Please read [CONTRIBUTING.md](CONTRIBUTING.md) for details on our code of conduct and the process for submitting pull requests.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Support

For support, please contact the URIS-AI team or open an issue in the repository.
