# Rencana Implementasi: URIS-AI

## Overview

Dokumen ini berisi rencana implementasi lengkap untuk URIS-AI (Urban Risk Intelligence System for Flood-Aware Mobility and Public Service Optimization). Sistem ini akan dibangun menggunakan Python dengan arsitektur modular berbasis Azure cloud services.

**Teknologi Utama:**

- Backend: Python 3.11+, FastAPI
- Frontend: Streamlit
- Database: Azure SQL Database
- Storage: Azure Blob Storage
- ML: Azure Machine Learning, scikit-learn, TensorFlow
- Testing: pytest, Hypothesis (property-based testing)
- Cloud: Microsoft Azure

**Pendekatan Implementasi:**
Implementasi akan dilakukan secara incremental, dimulai dari setup infrastructure, kemudian data layer, processing layer, AI/ML layer, application layer, dan terakhir presentation layer. Setiap tahap akan divalidasi dengan testing sebelum melanjutkan ke tahap berikutnya.

---

## Tasks

- [x] 1. Setup Project dan Infrastructure Azure
  - Inisialisasi struktur project Python
  - Setup Azure resources (Resource Group, App Services, SQL Database, Blob Storage)
  - Konfigurasi environment variables dan secrets management
  - Setup CI/CD pipeline dasar
  - _Requirements: 9.1, 9.3_

- [ ] 2. Implementasi Database Schema dan Models
  - [ ] 2.1 Buat database schema untuk semua tabel
    - Implementasi tabel: regions, weather_data, flood_events, roads, public_facilities, risk_scores, recommendations, users
    - Tambahkan indexes dan foreign key constraints sesuai design
    - _Requirements: 7.1_
  - [ ] 2.2 Buat SQLAlchemy ORM models
    - Definisikan models untuk semua entities
    - Implementasi relationships antar models
    - _Requirements: 7.1_
  - [ ]\* 2.3 Buat unit tests untuk database models
    - Test CRUD operations untuk setiap model
    - Test relationships dan constraints
    - _Requirements: 7.1_

- [ ] 3. Implementasi Data Ingestion Layer
  - [ ] 3.1 Buat base DataIntegrator class dan interface
    - Implementasi abstract methods untuk data fetching
    - Setup Azure Blob Storage client
    - _Requirements: 7.1, 7.2_
  - [ ] 3.2 Implementasi Weather_API_Connector
    - Integrasi dengan BMKG API atau weather API setara
    - Implementasi retry mechanism dengan exponential backoff
    - _Requirements: 1.1, 7.2_
  - [ ] 3.3 Implementasi Historical_Flood_Loader
    - Load dan parse data historis banjir
    - Validasi dan normalisasi data
    - _Requirements: 1.2_
  - [ ] 3.4 Implementasi OSM_Data_Fetcher
    - Fetch data jalan dan fasilitas dari OpenStreetMap API
    - Parse dan transform data OSM ke format internal
    - _Requirements: 7.1_
  - [ ] 3.5 Implementasi Data_Validator dengan schema validation
    - Definisikan schemas untuk setiap data type
    - Implementasi validation logic
    - _Requirements: 7.4_
  - [ ]\* 3.6 Buat property test untuk Data_Validator
    - **Property 7: Data Validation Rejection of Invalid Data**
    - **Validates: Requirements 7.4**
  - [ ]\* 3.7 Buat integration tests untuk data ingestion
    - Test integrasi dengan external APIs (menggunakan mocks)
    - Test data persistence ke Blob Storage
    - Test error handling untuk API failures
    - _Requirements: 7.2, 7.3_

- [ ] 4. Checkpoint - Validasi Data Ingestion Layer
  - Ensure all tests pass, ask the user if questions arise.

- [ ] 5. Implementasi Data Processing Layer
  - [ ] 5.1 Buat Data_Cleaner untuk data cleaning
    - Implementasi handling missing values
    - Implementasi outlier detection dan removal
    - _Requirements: 7.1_
  - [ ] 5.2 Buat Region_Integrator untuk data integration
    - Implementasi logic untuk menggabungkan data berdasarkan region_id
    - Implementasi spatial joins untuk data geografis
    - _Requirements: 7.1_
  - [ ] 5.3 Buat Feature_Engineer untuk ML feature engineering
    - Implementasi rolling averages dan lag features
    - Implementasi feature extraction dari data temporal
    - _Requirements: 1.2_
  - [ ] 5.4 Buat Data_Transformer untuk normalisasi dan encoding
    - Implementasi normalization (min-max, z-score)
    - Implementasi categorical encoding
    - _Requirements: 1.2_
  - [ ]\* 5.5 Buat unit tests untuk data processing components
    - Test data cleaning logic
    - Test feature engineering outputs
    - _Requirements: 7.1_

- [ ] 6. Implementasi AI/ML Layer - Flood Risk Engine
  - [ ] 6.1 Buat Flood_Risk_Engine class dan interface
    - Definisikan input/output data structures
    - Setup Azure ML workspace connection
    - _Requirements: 1.1_
  - [ ] 6.2 Implementasi data preparation untuk model training
    - Load dan preprocess training data
    - Split data menjadi train/validation/test sets
    - _Requirements: 1.2, 1.5_
  - [ ] 6.3 Training model ML untuk prediksi risiko banjir
    - Implementasi model training pipeline (scikit-learn atau TensorFlow)
    - Hyperparameter tuning
    - Model evaluation dan validation
    - _Requirements: 1.5_
  - [ ] 6.4 Implementasi predict_flood_risk dan batch_predict methods
    - Implementasi inference logic
    - Implementasi batch prediction untuk efisiensi
    - _Requirements: 1.1, 1.3_
  - [ ] 6.5 Implementasi get_risk_category method
    - Konversi skor numerik ke kategori (Rendah/Sedang/Tinggi/Kritis)
    - _Requirements: 1.3_
  - [ ]\* 6.6 Buat property test untuk risk category mapping
    - **Property 1: Risk Score to Category Mapping Consistency**
    - **Validates: Requirements 1.3**
  - [ ] 6.7 Implementasi model deployment ke Azure ML Endpoint
    - Deploy model sebagai REST endpoint
    - Setup model versioning
    - _Requirements: 9.2_
  - [ ]\* 6.8 Buat integration tests untuk Flood_Risk_Engine
    - Test model inference
    - Test error handling untuk invalid inputs
    - _Requirements: 1.1, 1.4_

- [ ] 7. Checkpoint - Validasi Flood Risk Engine
  - Ensure all tests pass, ask the user if questions arise.

- [ ] 8. Implementasi AI/ML Layer - Traffic Analyzer
  - [ ] 8.1 Buat Traffic_Analyzer class dan interface
    - Definisikan input/output data structures
    - _Requirements: 2.1_
  - [ ] 8.2 Implementasi analyze_traffic_impact method
    - Implementasi logic untuk estimasi dampak banjir terhadap lalu lintas
    - Integrasi dengan data jalan dari database
    - _Requirements: 2.1, 2.3_
  - [ ] 8.3 Implementasi get_affected_roads method
    - Query roads yang terdampak berdasarkan flood risk
    - _Requirements: 2.1_
  - [ ] 8.4 Implementasi estimate_congestion_level method
    - Estimasi tingkat kemacetan per ruas jalan
    - _Requirements: 2.2_
  - [ ] 8.5 Implementasi check_region_isolation method
    - Deteksi wilayah terisolasi (semua jalan utama tidak dapat dilalui)
    - _Requirements: 2.4_
  - [ ]\* 8.6 Buat property test untuk region isolation detection
    - **Property 2: Region Isolation Detection**
    - **Validates: Requirements 2.4**
  - [ ]\* 8.7 Buat unit tests untuk Traffic_Analyzer
    - Test traffic impact calculation
    - Test congestion level estimation
    - _Requirements: 2.1, 2.3_

- [ ] 9. Implementasi AI/ML Layer - Service Accessibility Module
  - [ ] 9.1 Buat Service_Accessibility_Module class dan interface
    - Definisikan input/output data structures
    - _Requirements: 3.1_
  - [ ] 9.2 Implementasi evaluate_accessibility method
    - Evaluasi aksesibilitas fasilitas publik berdasarkan traffic impact
    - _Requirements: 3.1, 3.4_
  - [ ] 9.3 Implementasi find_alternative_facilities method
    - Implementasi spatial search untuk fasilitas alternatif dalam radius
    - Implementasi distance calculation (Haversine formula)
    - _Requirements: 3.2_
  - [ ]\* 9.4 Buat property test untuk alternative facility radius constraint
    - **Property 3: Alternative Facility Radius Constraint**
    - **Validates: Requirements 3.2**
  - [ ] 9.5 Implementasi estimate_facility_load method
    - Estimasi beban fasilitas berdasarkan pengalihan pengguna
    - _Requirements: 3.3_
  - [ ] 9.6 Implementasi get_affected_facilities method
    - Query fasilitas yang terdampak di wilayah tertentu
    - _Requirements: 3.1_
  - [ ]\* 9.7 Buat unit tests untuk Service_Accessibility_Module
    - Test accessibility evaluation
    - Test alternative facility search
    - Test facility load estimation
    - _Requirements: 3.1, 3.2, 3.3_

- [ ] 10. Implementasi AI/ML Layer - Risk Scoring Engine
  - [ ] 10.1 Buat Risk_Scoring_Engine class dan interface
    - Definisikan input/output data structures
    - _Requirements: 4.1_
  - [ ] 10.2 Implementasi calculate_urban_risk_score method
    - Implementasi weighted sum formula untuk URS
    - Implementasi configurable weights
    - _Requirements: 4.1_
  - [ ]\* 10.3 Buat property test untuk Urban Risk Score calculation
    - **Property 4: Urban Risk Score Calculation Correctness**
    - **Validates: Requirements 4.1**
  - [ ] 10.4 Implementasi batch_calculate method
    - Batch calculation untuk multiple regions
    - _Requirements: 4.2_
  - [ ] 10.5 Implementasi get_risk_trend method
    - Query historical risk scores untuk trend analysis
    - _Requirements: 4.4_
  - [ ] 10.6 Implementasi save_risk_history method
    - Persist risk scores ke database
    - _Requirements: 4.4_
  - [ ]\* 10.7 Buat unit tests untuk Risk_Scoring_Engine
    - Test URS calculation dengan berbagai input
    - Test batch calculation
    - Test risk history persistence
    - _Requirements: 4.1, 4.4_

- [ ] 11. Checkpoint - Validasi AI/ML Layer
  - Ensure all tests pass, ask the user if questions arise.

- [ ] 12. Implementasi AI/ML Layer - Recommendation Engine
  - [ ] 12.1 Buat Recommendation_Engine class dan interface
    - Definisikan input/output data structures
    - _Requirements: 5.1_
  - [ ] 12.2 Implementasi generate_recommendations method
    - Implementasi rule-based recommendation logic
    - Integrasi dengan risk scores dan accessibility reports
    - _Requirements: 5.1, 5.3_
  - [ ] 12.3 Implementasi find_safe_route method
    - Implementasi pathfinding algorithm yang menghindari high-risk regions
    - Integrasi dengan road network data
    - _Requirements: 5.2_
  - [ ]\* 12.4 Buat property test untuk safe route avoidance
    - **Property 5: Safe Route Avoidance of High-Risk Regions**
    - **Validates: Requirements 5.2**
  - [ ] 12.5 Implementasi classify_urgency method
    - Klasifikasi urgency berdasarkan time to impact
    - _Requirements: 5.4_
  - [ ]\* 12.6 Buat property test untuk urgency classification
    - **Property 6: Urgency Classification Consistency**
    - **Validates: Requirements 5.4**
  - [ ]\* 12.7 Buat unit tests untuk Recommendation_Engine
    - Test recommendation generation
    - Test safe route finding
    - Test urgency classification
    - _Requirements: 5.1, 5.2, 5.4, 5.5_

- [ ] 13. Implementasi Application Layer - FastAPI Backend
  - [ ] 13.1 Setup FastAPI application structure
    - Buat main FastAPI app dengan routers
    - Setup CORS middleware
    - Setup error handlers
    - _Requirements: 6.1, 6.4_
  - [ ] 13.2 Implementasi authentication dan authorization
    - Integrasi dengan Azure Active Directory
    - Implementasi JWT token handling
    - Implementasi role-based access control (RBAC)
    - _Requirements: 10.1, 10.2_
  - [ ] 13.3 Implementasi Risk_Service endpoints
    - GET /regions/{region_id}/risk - Get risk score untuk region
    - GET /regions/risk - Get risk scores untuk semua regions
    - GET /regions/{region_id}/risk/trend - Get risk trend
    - _Requirements: 4.2, 4.4_
  - [ ] 13.4 Implementasi Recommendation_Service endpoints
    - GET /regions/{region_id}/recommendations - Get recommendations
    - POST /routes/safe - Find safe route dari origin ke destination
    - _Requirements: 5.1, 5.2_
  - [ ] 13.5 Implementasi User_Service endpoints
    - POST /auth/login - User login
    - POST /auth/logout - User logout
    - GET /users/me - Get current user info
    - _Requirements: 10.2_
  - [ ] 13.6 Implementasi Cache_Manager dengan Redis
    - Setup Azure Cache for Redis connection
    - Implementasi caching untuk frequently accessed data
    - Implementasi cache invalidation strategy
    - _Requirements: 8.1_
  - [ ] 13.7 Implementasi rate limiting
    - Setup rate limiting middleware
    - Konfigurasi rate limits per endpoint
    - _Requirements: 8.2_
  - [ ]\* 13.8 Buat integration tests untuk API endpoints
    - Test semua endpoints dengan berbagai scenarios
    - Test authentication dan authorization
    - Test error responses
    - _Requirements: 6.1, 10.2, 10.4_

- [ ] 14. Checkpoint - Validasi Application Layer
  - Ensure all tests pass, ask the user if questions arise.

- [ ] 15. Implementasi Presentation Layer - Streamlit Dashboard
  - [ ] 15.1 Setup Streamlit application structure
    - Buat main Streamlit app
    - Setup page configuration dan layout
    - _Requirements: 6.1_
  - [ ] 15.2 Implementasi Map_Visualizer component
    - Integrasi dengan Azure Maps atau Leaflet
    - Implementasi choropleth visualization untuk URS
    - Implementasi interactive map (zoom, pan, click)
    - _Requirements: 6.2, 4.2_
  - [ ] 15.3 Implementasi Risk_Dashboard component
    - Display Urban Risk Score untuk selected region
    - Display risk category dan confidence
    - Display risk trend chart
    - _Requirements: 6.6, 4.2_
  - [ ] 15.4 Implementasi Recommendation_Panel component
    - Display recommendations dengan urgency levels
    - Display safe routes pada map
    - Display alternative facilities
    - _Requirements: 6.6, 5.1_
  - [ ] 15.5 Implementasi User_Interface untuk login dan role management
    - Login form dengan Azure AD integration
    - Role-based UI rendering
    - _Requirements: 10.1, 10.3_
  - [ ] 15.6 Implementasi responsive design untuk mobile
    - Optimize layout untuk mobile devices
    - Test pada berbagai screen sizes
    - _Requirements: 6.5_
  - [ ] 15.7 Implementasi filter dan parameter selection
    - Filter berdasarkan waktu
    - Filter berdasarkan kategori risiko
    - Region selection
    - _Requirements: 6.2_
  - [ ]\* 15.8 Buat end-to-end tests untuk dashboard
    - Test user workflows (view map, select region, view details)
    - Test UI interactions
    - _Requirements: 6.1, 6.2, 6.6_

- [ ] 16. Implementasi Scheduled Data Ingestion dengan Azure Functions
  - [ ] 16.1 Buat Azure Function untuk scheduled weather data fetching
    - Setup timer trigger (setiap 10 menit)
    - Implementasi weather data fetching dan storage
    - _Requirements: 1.1, 7.2_
  - [ ] 16.2 Buat Azure Function untuk scheduled risk calculation
    - Setup timer trigger (setiap 5 menit saat kondisi risiko aktif)
    - Trigger risk calculation pipeline
    - _Requirements: 3.4, 4.3_
  - [ ] 16.3 Implementasi error handling dan retry logic
    - Implementasi exponential backoff untuk retries
    - Logging dan alerting untuk failures
    - _Requirements: 7.3_
  - [ ]\* 16.4 Buat integration tests untuk Azure Functions
    - Test scheduled execution
    - Test error handling
    - _Requirements: 7.2, 7.3_

- [ ] 17. Implementasi Monitoring dan Logging
  - [ ] 17.1 Setup Azure Application Insights
    - Integrasi Application Insights dengan FastAPI dan Streamlit
    - Setup custom metrics dan events
    - _Requirements: 8.4_
  - [ ] 17.2 Implementasi structured logging
    - Setup logging configuration untuk semua components
    - Implementasi log levels (DEBUG, INFO, WARNING, ERROR, CRITICAL)
    - _Requirements: 7.3_
  - [ ] 17.3 Setup alerting rules
    - Configure alerts untuk critical errors
    - Configure alerts untuk performance degradation
    - Configure alerts untuk security events
    - _Requirements: 8.4_
  - [ ] 17.4 Implementasi health check endpoints
    - /health - Basic health check
    - /health/ready - Readiness check (database, external services)
    - /health/live - Liveness check
    - _Requirements: 8.4, 9.4_

- [ ] 18. Implementasi Security Features
  - [ ] 18.1 Setup Azure Key Vault untuk secrets management
    - Store database credentials, API keys, certificates
    - Integrasi Key Vault dengan aplikasi
    - _Requirements: 10.5_
  - [ ] 18.2 Implementasi TLS/HTTPS untuk semua komunikasi
    - Configure SSL certificates
    - Enforce HTTPS di semua endpoints
    - _Requirements: 10.5_
  - [ ] 18.3 Implementasi input validation dan sanitization
    - Validate semua user inputs
    - Sanitize inputs untuk prevent SQL injection dan XSS
    - _Requirements: 10.4_
  - [ ]\* 18.4 Buat security tests
    - Test authentication dan authorization
    - Test input validation
    - Test SQL injection prevention
    - Test XSS prevention
    - _Requirements: 10.2, 10.4, 10.5_

- [ ] 19. Checkpoint - Validasi Security dan Monitoring
  - Ensure all tests pass, ask the user if questions arise.

- [ ] 20. Implementasi Deployment dan CI/CD
  - [ ] 20.1 Setup Azure DevOps atau GitHub Actions pipeline
    - Configure build pipeline
    - Configure test pipeline
    - Configure deployment pipeline
    - _Requirements: 9.2_
  - [ ] 20.2 Implementasi blue-green deployment strategy
    - Setup blue dan green environments
    - Implementasi traffic switching logic
    - Implementasi automatic rollback
    - _Requirements: 9.2, 9.4_
  - [ ] 20.3 Setup infrastructure as code (Terraform atau ARM templates)
    - Define semua Azure resources sebagai code
    - Setup automated infrastructure provisioning
    - _Requirements: 9.1_
  - [ ] 20.4 Implementasi automated testing dalam CI/CD
    - Run unit tests dan property tests di CI
    - Run integration tests di CI
    - Run security scans di CI
    - _Requirements: 8.1_
  - [ ]\* 20.5 Buat deployment smoke tests
    - Test critical endpoints setelah deployment
    - Test database connectivity
    - Test external service connectivity
    - _Requirements: 9.2_

- [ ] 21. Performance Optimization dan Load Testing
  - [ ] 21.1 Implementasi database query optimization
    - Add missing indexes
    - Optimize slow queries
    - _Requirements: 8.1_
  - [ ] 21.2 Implementasi caching strategy
    - Cache frequently accessed data
    - Implement cache warming
    - _Requirements: 8.1_
  - [ ] 21.3 Setup auto-scaling untuk Azure App Services
    - Configure auto-scaling rules
    - Set scaling thresholds
    - _Requirements: 8.3_
  - [ ]\* 21.4 Buat load tests dengan Locust
    - Test dengan 500 concurrent users
    - Verify response time SLA (<5 seconds)
    - Test auto-scaling behavior
    - _Requirements: 8.1, 8.2, 8.3_

- [ ] 22. Data Migration dan Seeding
  - [ ] 22.1 Buat scripts untuk initial data seeding
    - Seed regions data (Jakarta dan Jawa Barat)
    - Seed historical flood data
    - Seed roads dan facilities data
    - _Requirements: 7.1_
  - [ ] 22.2 Buat scripts untuk data migration
    - Migration scripts untuk schema updates
    - Data transformation scripts
    - _Requirements: 7.1_
  - [ ]\* 22.3 Test data migration scripts
    - Test migration pada test database
    - Verify data integrity setelah migration
    - _Requirements: 7.1_

- [ ] 23. Documentation
  - [ ] 23.1 Buat API documentation dengan OpenAPI/Swagger
    - Document semua endpoints
    - Include request/response examples
    - _Requirements: 6.4_
  - [ ] 23.2 Buat user documentation
    - User guide untuk dashboard
    - FAQ untuk common questions
    - _Requirements: 6.3_
  - [ ] 23.3 Buat developer documentation
    - Architecture overview
    - Setup instructions
    - Deployment guide
    - _Requirements: 9.1_
  - [ ] 23.4 Buat runbook untuk operations
    - Incident response procedures
    - Monitoring dan alerting guide
    - Troubleshooting guide
    - _Requirements: 8.4_

- [ ] 24. Final Integration Testing dan User Acceptance
  - [ ]\* 24.1 Buat comprehensive integration tests
    - Test end-to-end workflows
    - Test semua user scenarios dari requirements
    - _Requirements: 1.1, 2.1, 3.1, 4.1, 5.1, 6.1_
  - [ ]\* 24.2 Buat performance tests
    - Verify semua performance requirements terpenuhi
    - Test system uptime dan availability
    - _Requirements: 8.1, 8.2, 8.4_
  - [ ] 24.3 Conduct security audit
    - Review security implementation
    - Run penetration testing (jika applicable)
    - _Requirements: 10.1, 10.2, 10.4, 10.5_

- [ ] 25. Final Checkpoint - System Ready for Production
  - Ensure all tests pass, ask the user if questions arise.

---

## Notes

- Tasks yang ditandai dengan `*` adalah optional dan dapat di-skip untuk MVP yang lebih cepat
- Setiap task mereferensikan requirements spesifik untuk traceability
- Checkpoint tasks memastikan validasi incremental
- Property tests memvalidasi universal correctness properties dari design
- Unit tests memvalidasi specific examples dan edge cases
- Integration tests memvalidasi interaksi antar komponen
- End-to-end tests memvalidasi complete user workflows

## Testing Strategy Summary

**Property-Based Tests (7 properties):**

1. Risk Score to Category Mapping Consistency (Task 6.6)
2. Region Isolation Detection (Task 8.6)
3. Alternative Facility Radius Constraint (Task 9.4)
4. Urban Risk Score Calculation Correctness (Task 10.3)
5. Safe Route Avoidance of High-Risk Regions (Task 12.4)
6. Urgency Classification Consistency (Task 12.6)
7. Data Validation Rejection of Invalid Data (Task 3.6)

**Unit Tests:**

- Database models (Task 2.3)
- Data processing components (Task 5.5)
- Flood Risk Engine (Task 6.8)
- Traffic Analyzer (Task 8.7)
- Service Accessibility Module (Task 9.7)
- Risk Scoring Engine (Task 10.7)
- Recommendation Engine (Task 12.7)

**Integration Tests:**

- Data ingestion (Task 3.7)
- API endpoints (Task 13.8)
- Azure Functions (Task 16.4)
- Security features (Task 18.4)
- Deployment (Task 20.5)
- Data migration (Task 22.3)
- End-to-end workflows (Task 24.1)

**Performance Tests:**

- Load testing (Task 21.4)
- Performance requirements validation (Task 24.2)

## Deployment Strategy

Sistem akan di-deploy menggunakan **blue-green deployment** untuk memastikan zero-downtime updates:

1. Deploy ke green environment
2. Run smoke tests
3. Switch traffic dari blue ke green
4. Monitor green environment
5. Rollback ke blue jika ada issues

## Monitoring dan Observability

Sistem akan menggunakan Azure Application Insights untuk:

- Application metrics (request rate, response time, error rate)
- Infrastructure metrics (CPU, memory, disk, network)
- Business metrics (active users, predictions generated)
- Alerting untuk critical issues

## Security

Sistem mengimplementasikan:

- Role-Based Access Control (RBAC) dengan 3 roles
- Azure Active Directory untuk authentication
- TLS 1.2+ untuk semua komunikasi
- Azure Key Vault untuk secrets management
- Input validation dan sanitization untuk prevent injection attacks
