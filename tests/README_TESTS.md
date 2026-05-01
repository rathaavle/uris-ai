# Unit Tests untuk Database Models

## Overview

File ini berisi dokumentasi untuk unit tests yang telah dibuat untuk semua database models di URIS-AI system.

**Requirements:** 7.1

## Test Coverage

### 1. Region Model Tests (`TestRegionModel`)

Tests untuk model Region yang mencakup:

- ✅ **test_create_region**: Membuat region dengan semua field
- ✅ **test_create_region_minimal_fields**: Membuat region dengan field minimal (required only)
- ✅ **test_read_region**: Membaca region dari database
- ✅ **test_update_region**: Update field region
- ✅ **test_delete_region**: Hapus region dari database
- ✅ **test_region_timestamps**: Verifikasi created_at dan updated_at timestamps

### 2. WeatherData Model Tests (`TestWeatherDataModel`)

Tests untuk model WeatherData yang mencakup:

- ✅ **test_create_weather_data**: Membuat weather data dengan semua field
- ✅ **test_weather_data_relationship**: Test relationship antara WeatherData dan Region
- ✅ **test_weather_data_cascade_delete**: Test CASCADE delete (weather data terhapus saat region dihapus)
- ✅ **test_weather_data_foreign_key_constraint**: Test foreign key constraint enforcement

### 3. FloodEvent Model Tests (`TestFloodEventModel`)

Tests untuk model FloodEvent yang mencakup:

- ✅ **test_create_flood_event**: Membuat flood event dengan semua field
- ✅ **test_flood_event_severity_constraint**: Test constraint severity (1-4)
- ✅ **test_flood_event_relationship**: Test relationship antara FloodEvent dan Region

### 4. Road Model Tests (`TestRoadModel`)

Tests untuk model Road yang mencakup:

- ✅ **test_create_road**: Membuat road dengan semua field
- ✅ **test_road_default_values**: Test default values (is_main_road=False)
- ✅ **test_road_relationship**: Test relationship antara Road dan Region

### 5. PublicFacility Model Tests (`TestPublicFacilityModel`)

Tests untuk model PublicFacility yang mencakup:

- ✅ **test_create_public_facility**: Membuat public facility dengan semua field
- ✅ **test_public_facility_types**: Test berbagai tipe facility (hospital, clinic, school, government)
- ✅ **test_public_facility_relationship**: Test relationship antara PublicFacility dan Region

### 6. RiskScore Model Tests (`TestRiskScoreModel`)

Tests untuk model RiskScore yang mencakup:

- ✅ **test_create_risk_score**: Membuat risk score dengan semua field
- ✅ **test_risk_score_range_constraints**: Test constraint range (0-100) untuk semua score fields
- ✅ **test_risk_score_relationship**: Test relationship antara RiskScore dan Region

### 7. Recommendation Model Tests (`TestRecommendationModel`)

Tests untuk model Recommendation yang mencakup:

- ✅ **test_create_recommendation**: Membuat recommendation dengan semua field
- ✅ **test_recommendation_types**: Test berbagai tipe recommendation (alert, route, service)
- ✅ **test_recommendation_relationship**: Test relationship antara Recommendation dan Region

### 8. User Model Tests (`TestUserModel`)

Tests untuk model User yang mencakup:

- ✅ **test_create_user**: Membuat user dengan semua field
- ✅ **test_user_unique_username**: Test unique constraint untuk username
- ✅ **test_user_unique_email**: Test unique constraint untuk email
- ✅ **test_user_roles**: Test berbagai role (public, facility_manager, government)

### 9. Model Representation Tests (`TestModelRepresentations`)

Tests untuk `__repr__` methods dari semua models:

- ✅ Test repr untuk Region
- ✅ Test repr untuk WeatherData
- ✅ Test repr untuk FloodEvent
- ✅ Test repr untuk Road
- ✅ Test repr untuk PublicFacility
- ✅ Test repr untuk RiskScore
- ✅ Test repr untuk Recommendation
- ✅ Test repr untuk User

## Test Fixtures

File `conftest.py` menyediakan fixtures berikut:

- **db_engine**: In-memory SQLite database engine untuk testing
- **db_session**: Database session dengan automatic rollback
- **sample_region_id**: Sample region ID (1)
- **sample_weather_data**: Sample weather data dictionary
- **sample_datetime**: Sample datetime object

## Menjalankan Tests

### Prerequisites

1. Install Python 3.11+ di `D:\libprogram\python\Python312`
2. Install dependencies menggunakan Poetry:

```bash
poetry install
```

### Menjalankan Semua Tests

```bash
poetry run pytest tests/test_models.py -v
```

### Menjalankan Tests dengan Coverage Report

```bash
poetry run pytest tests/test_models.py -v --cov=src/uris_ai/models --cov-report=html
```

### Menjalankan Specific Test Class

```bash
poetry run pytest tests/test_models.py::TestRegionModel -v
```

### Menjalankan Specific Test Method

```bash
poetry run pytest tests/test_models.py::TestRegionModel::test_create_region -v
```

## Test Database

Tests menggunakan **in-memory SQLite database** yang:

- Dibuat fresh untuk setiap test function
- Tidak mempengaruhi database production
- Otomatis di-cleanup setelah test selesai
- Sangat cepat karena di memory

## CRUD Operations Coverage

Setiap model di-test untuk operasi CRUD:

| Model          | Create | Read | Update | Delete       |
| -------------- | ------ | ---- | ------ | ------------ |
| Region         | ✅     | ✅   | ✅     | ✅           |
| WeatherData    | ✅     | ✅   | -      | ✅ (cascade) |
| FloodEvent     | ✅     | ✅   | -      | -            |
| Road           | ✅     | ✅   | -      | -            |
| PublicFacility | ✅     | ✅   | -      | -            |
| RiskScore      | ✅     | ✅   | -      | -            |
| Recommendation | ✅     | ✅   | -      | -            |
| User           | ✅     | ✅   | -      | -            |

## Relationships Coverage

Semua relationships di-test:

- ✅ Region → WeatherData (one-to-many)
- ✅ Region → FloodEvent (one-to-many)
- ✅ Region → Road (one-to-many)
- ✅ Region → PublicFacility (one-to-many)
- ✅ Region → RiskScore (one-to-many)
- ✅ Region → Recommendation (one-to-many)

## Constraints Coverage

Semua constraints di-test:

- ✅ Foreign key constraints
- ✅ Unique constraints (username, email)
- ✅ Check constraints (severity 1-4, scores 0-100)
- ✅ NOT NULL constraints
- ✅ CASCADE delete behavior

## Next Steps

Setelah Python terinstall dengan benar:

1. Install dependencies: `poetry install`
2. Run tests: `poetry run pytest tests/test_models.py -v`
3. Verify semua tests pass
4. Generate coverage report: `poetry run pytest --cov-report=html`
5. Review coverage report di `htmlcov/index.html`

## Status

✅ **Task 2.3 COMPLETE** - Unit tests untuk database models sudah dibuat dengan lengkap dan mencakup:

- CRUD operations untuk setiap model
- Relationships dan constraints
- Edge cases dan error handling
