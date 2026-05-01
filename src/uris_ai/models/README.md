# URIS-AI Database Models

This directory contains the database schema and SQLAlchemy ORM models for the URIS-AI system.

## Files

- **schema.sql**: SQL schema definition for all database tables
- **database.py**: SQLAlchemy ORM models matching the schema
- **db_utils.py**: Database utility functions for connection and session management
- ****init**.py**: Module exports

## Database Schema

The URIS-AI system uses 8 main tables:

### 1. regions

Stores administrative region information (kelurahan/kecamatan).

**Key columns:**

- `region_id` (PK): Unique region identifier
- `name`: Region name
- `latitude`, `longitude`: Geographic coordinates
- `elevation`: Region elevation in meters
- `drainage_capacity`: Drainage capacity in m³/hour

### 2. weather_data

Stores time-series weather data per region.

**Key columns:**

- `region_id` (FK): Reference to regions table
- `date`: Timestamp of weather data
- `rainfall`: Rainfall in mm
- `humidity`: Humidity percentage
- `temperature`: Temperature in °C
- `wind_speed`: Wind speed in km/h

### 3. flood_events

Stores historical flood event data.

**Key columns:**

- `region_id` (FK): Reference to regions table
- `date`: Timestamp of flood event
- `severity`: Severity level (1=Low, 2=Medium, 3=High, 4=Critical)
- `water_level`: Water level in cm
- `duration_hours`: Duration in hours
- `affected_area_km2`: Affected area in km²

### 4. roads

Stores road network data.

**Key columns:**

- `region_id` (FK): Reference to regions table
- `road_name`: Name of the road
- `road_type`: Type (primary/secondary/tertiary)
- `road_density`: Road density in km/km²
- `length_km`: Road length in km
- `is_main_road`: Boolean flag for main roads

### 5. public_facilities

Stores public facility data (hospitals, clinics, schools, government offices).

**Key columns:**

- `region_id` (FK): Reference to regions table
- `name`: Facility name
- `type`: Facility type (hospital/clinic/school/government)
- `latitude`, `longitude`: Facility coordinates
- `capacity`: Facility capacity (optional)
- `is_operational`: Operational status

### 6. risk_scores

Stores calculated risk scores.

**Key columns:**

- `region_id` (FK): Reference to regions table
- `date`: Timestamp of calculation
- `flood_risk`: Flood risk score (0-100)
- `traffic_impact`: Traffic impact score (0-100)
- `service_access`: Service accessibility score (0-100)
- `urban_risk_score`: Urban Risk Score (0-100)

### 7. recommendations

Stores system-generated recommendations.

**Key columns:**

- `region_id` (FK): Reference to regions table
- `recommendation_type`: Type (route/alert/service)
- `description`: Recommendation details
- `urgency_level`: Urgency (Segera/Waspada/Siaga)
- `expires_at`: Expiration timestamp
- `is_active`: Active status

### 8. users

Stores user information and roles.

**Key columns:**

- `username`: Unique username
- `email`: Unique email address
- `password_hash`: Hashed password (bcrypt)
- `role`: User role (public/facility_manager/government)
- `is_active`: Account status

## Usage

### Creating Database Engine

```python
from uris_ai.models import create_db_engine, init_database

# Create engine
engine = create_db_engine("postgresql://user:pass@localhost/uris_ai")

# Initialize database (create all tables)
init_database(engine)
```

### Creating Sessions

```python
from uris_ai.models import create_session_factory, get_db_session

# Create session factory
session_factory = create_session_factory(engine)

# Get a session
for session in get_db_session(session_factory):
    # Use session here
    regions = session.query(Region).all()
```

### Using Models

```python
from uris_ai.models import Region, WeatherData
from datetime import datetime

# Create a new region
region = Region(
    region_id=1,
    name="Jakarta Pusat",
    latitude=-6.1751,
    longitude=106.8650,
    elevation=8.0,
    drainage_capacity=1000.0
)

# Create weather data
weather = WeatherData(
    region_id=1,
    date=datetime.utcnow(),
    rainfall=50.0,
    humidity=85.0,
    temperature=28.5,
    wind_speed=15.0
)

# Add to session and commit
session.add(region)
session.add(weather)
session.commit()
```

### Querying Data

```python
from uris_ai.models import Region, RiskScore
from sqlalchemy import desc

# Query regions with high risk
high_risk_regions = (
    session.query(Region)
    .join(RiskScore)
    .filter(RiskScore.urban_risk_score > 70)
    .order_by(desc(RiskScore.urban_risk_score))
    .all()
)

# Query weather data for a region
weather_data = (
    session.query(WeatherData)
    .filter(WeatherData.region_id == 1)
    .order_by(desc(WeatherData.date))
    .limit(10)
    .all()
)
```

## Relationships

All models have proper relationships defined:

- **Region** has one-to-many relationships with:
  - WeatherData
  - FloodEvent
  - Road
  - PublicFacility
  - RiskScore
  - Recommendation

All foreign key relationships use `CASCADE` delete to maintain referential integrity.

## Indexes

The schema includes indexes for optimal query performance:

- `regions.name`: For region name searches
- `weather_data(region_id, date)`: For time-series queries
- `flood_events(region_id, date)`: For historical flood queries
- `roads.region_id`: For road lookups by region
- `public_facilities(region_id, type)`: For facility searches
- `risk_scores(region_id, date)`: For risk score time-series
- `risk_scores.urban_risk_score`: For filtering by risk level
- `recommendations(region_id, is_active)`: For active recommendations
- `recommendations.urgency_level`: For filtering by urgency
- `users.email`: For user authentication
- `users.role`: For role-based queries

## Constraints

The schema enforces data integrity through constraints:

- **Check constraints** on risk scores (0-100 range)
- **Check constraint** on flood event severity (1-4 range)
- **Unique constraints** on user username and email
- **Foreign key constraints** with CASCADE delete

## Requirements

This implementation satisfies **Requirements 7.1** from the URIS-AI specification:

- Complete database schema for all 8 tables
- Proper indexes and foreign key constraints
- SQLAlchemy ORM models with relationships
- Type hints and documentation
