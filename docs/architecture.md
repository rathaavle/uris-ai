# URIS-AI Architecture Overview

## System Architecture

URIS-AI uses a layered architecture deployed on Microsoft Azure cloud platform.

### High-Level Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Presentation Layer                        │
│              (Streamlit Dashboard + Azure Maps)              │
└─────────────────────────────────────────────────────────────┘
                              ↕
┌─────────────────────────────────────────────────────────────┐
│                     Application Layer                        │
│         (API Endpoints + Business Logic Services)            │
└─────────────────────────────────────────────────────────────┘
                              ↕
┌─────────────────────────────────────────────────────────────┐
│                      AI/ML Layer                             │
│    (Flood Prediction + Risk Scoring + Recommendation)        │
└─────────────────────────────────────────────────────────────┘
                              ↕
┌─────────────────────────────────────────────────────────────┐
│                  Data Processing Layer                       │
│         (Cleaning + Integration + Feature Engineering)       │
└─────────────────────────────────────────────────────────────┘
                              ↕
┌─────────────────────────────────────────────────────────────┐
│                   Data Ingestion Layer                       │
│        (API Connectors + Data Validators + Schedulers)       │
└─────────────────────────────────────────────────────────────┘
                              ↕
┌─────────────────────────────────────────────────────────────┐
│                      Data Storage                            │
│         (Azure Blob Storage + Azure SQL Database)            │
└─────────────────────────────────────────────────────────────┘
```

## Azure Services

### Core Services

1. **Azure App Service**
   - Hosts FastAPI backend
   - Hosts Streamlit dashboard
   - Auto-scaling enabled
   - Blue-green deployment support

2. **Azure SQL Database**
   - Stores operational data
   - Automated backups
   - Geo-replication for HA

3. **Azure Blob Storage**
   - Raw data storage
   - Processed data storage
   - Model artifacts storage

4. **Azure Cache for Redis**
   - API response caching
   - Session management
   - Real-time data caching

5. **Azure Key Vault**
   - Secrets management
   - Connection strings
   - API keys

6. **Azure Machine Learning**
   - Model training
   - Model deployment
   - Model versioning

7. **Azure Active Directory**
   - User authentication
   - Role-based access control
   - SSO integration

8. **Azure Application Insights**
   - Application monitoring
   - Performance metrics
   - Error tracking

## Component Architecture

### Data Ingestion Layer

**Components:**

- Weather API Connector
- Historical Flood Loader
- OSM Data Fetcher
- Data Validator

**Responsibilities:**

- Fetch data from external sources
- Validate data format
- Store raw data in Blob Storage
- Schedule periodic updates

### Data Processing Layer

**Components:**

- Data Cleaner
- Region Integrator
- Feature Engineer
- Data Transformer

**Responsibilities:**

- Clean and normalize data
- Integrate multi-source data
- Generate ML features
- Transform data for analysis

### AI/ML Layer

**Components:**

- Flood Risk Engine
- Traffic Analyzer
- Service Accessibility Module
- Risk Scoring Engine
- Recommendation Engine

**Responsibilities:**

- Predict flood risk
- Analyze traffic impact
- Evaluate service accessibility
- Calculate Urban Risk Score
- Generate recommendations

### Application Layer

**Components:**

- FastAPI REST API
- Business Logic Services
- Cache Manager
- Authentication Service

**Responsibilities:**

- Expose REST endpoints
- Implement business logic
- Manage caching
- Handle authentication

### Presentation Layer

**Components:**

- Streamlit Dashboard
- Map Visualizer
- Risk Dashboard
- Recommendation Panel

**Responsibilities:**

- Display interactive maps
- Visualize risk data
- Show recommendations
- Handle user interactions

## Data Flow

1. **Data Ingestion**
   - External APIs → Data Integrator → Blob Storage

2. **Data Processing**
   - Blob Storage → Data Processor → SQL Database

3. **ML Inference**
   - SQL Database → ML Models → Risk Scores

4. **API Layer**
   - Risk Scores → API Endpoints → Cache

5. **Presentation**
   - API → Dashboard → User

## Security Architecture

### Authentication & Authorization

- Azure AD for user authentication
- JWT tokens for API access
- Role-based access control (RBAC)
- Three roles: Public, Facility Manager, Government

### Data Security

- TLS 1.2+ for all communications
- Encrypted data at rest
- Encrypted data in transit
- Azure Key Vault for secrets

### Network Security

- Virtual Network integration
- Private endpoints for services
- Network Security Groups (NSG)
- DDoS protection

## Scalability

### Horizontal Scaling

- App Service auto-scaling
- Multiple instances based on load
- Load balancer distribution

### Vertical Scaling

- Upgrade App Service plan
- Increase database tier
- Larger Redis cache

### Caching Strategy

- Redis for frequently accessed data
- Cache warming on startup
- Cache invalidation on updates
- TTL-based expiration

## High Availability

### Redundancy

- Multi-instance deployment
- Database geo-replication
- Blob Storage redundancy (LRS/GRS)

### Disaster Recovery

- Automated database backups
- Point-in-time restore
- Blue-green deployment
- Automatic failover

### Monitoring

- Application Insights
- Azure Monitor
- Custom alerts
- Health check endpoints

## Performance Optimization

### API Performance

- Response caching
- Database query optimization
- Connection pooling
- Async processing

### Database Performance

- Indexed queries
- Query optimization
- Read replicas
- Partitioning

### Frontend Performance

- Lazy loading
- Data pagination
- Optimized rendering
- CDN for static assets

## Deployment Architecture

### Blue-Green Deployment

1. Deploy to green slot
2. Run smoke tests
3. Swap slots
4. Monitor production
5. Rollback if needed

### CI/CD Pipeline

1. Build & Test
2. Security Scan
3. Deploy to Staging
4. E2E Tests
5. Deploy to Production

## Technology Stack

- **Backend**: Python 3.11+, FastAPI
- **Frontend**: Streamlit
- **Database**: Azure SQL Database
- **Storage**: Azure Blob Storage
- **Cache**: Azure Redis Cache
- **ML**: Azure ML, scikit-learn
- **Testing**: pytest, Hypothesis
- **IaC**: Terraform
- **CI/CD**: GitHub Actions

## Design Principles

1. **Modularidad**: Independent components
2. **Scalability**: Handle increasing load
3. **Resilience**: Graceful degradation
4. **Real-time**: Minimal latency
5. **User-Centric**: Easy to use interface

## Future Enhancements

- Kubernetes deployment
- Multi-region deployment
- Advanced ML models
- Real-time streaming data
- Mobile application
