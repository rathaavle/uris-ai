-- URIS-AI Database Schema
-- Urban Risk Intelligence System for Flood-Aware Mobility and Public Service Optimization
-- Requirements: 7.1

-- ============================================================================
-- Table: regions
-- Description: Stores administrative region information
-- ============================================================================
CREATE TABLE regions (
    region_id INT PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    latitude FLOAT NOT NULL,
    longitude FLOAT NOT NULL,
    elevation FLOAT,
    drainage_capacity FLOAT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_name (name)
);

-- ============================================================================
-- Table: weather_data
-- Description: Stores weather data per region
-- ============================================================================
CREATE TABLE weather_data (
    id INT PRIMARY KEY AUTO_INCREMENT,
    region_id INT NOT NULL,
    date DATETIME NOT NULL,
    rainfall FLOAT NOT NULL,
    humidity FLOAT NOT NULL,
    temperature FLOAT NOT NULL,
    wind_speed FLOAT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (region_id) REFERENCES regions(region_id) ON DELETE CASCADE,
    INDEX idx_region_date (region_id, date)
);

-- ============================================================================
-- Table: flood_events
-- Description: Stores historical flood event data
-- ============================================================================
CREATE TABLE flood_events (
    id INT PRIMARY KEY AUTO_INCREMENT,
    region_id INT NOT NULL,
    date DATETIME NOT NULL,
    severity INT NOT NULL CHECK (severity BETWEEN 1 AND 4),
    water_level FLOAT,
    duration_hours INT,
    affected_area_km2 FLOAT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (region_id) REFERENCES regions(region_id) ON DELETE CASCADE,
    INDEX idx_region_date (region_id, date)
);

-- ============================================================================
-- Table: roads
-- Description: Stores road network data
-- ============================================================================
CREATE TABLE roads (
    id INT PRIMARY KEY AUTO_INCREMENT,
    region_id INT NOT NULL,
    road_name VARCHAR(255),
    road_type VARCHAR(50),
    road_density FLOAT NOT NULL,
    length_km FLOAT,
    is_main_road BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (region_id) REFERENCES regions(region_id) ON DELETE CASCADE,
    INDEX idx_region (region_id)
);

-- ============================================================================
-- Table: public_facilities
-- Description: Stores public facility data
-- ============================================================================
CREATE TABLE public_facilities (
    id INT PRIMARY KEY AUTO_INCREMENT,
    region_id INT NOT NULL,
    name VARCHAR(255) NOT NULL,
    type VARCHAR(50) NOT NULL,
    latitude FLOAT NOT NULL,
    longitude FLOAT NOT NULL,
    capacity INT,
    is_operational BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (region_id) REFERENCES regions(region_id) ON DELETE CASCADE,
    INDEX idx_region_type (region_id, type)
);

-- ============================================================================
-- Table: risk_scores
-- Description: Stores calculated risk scores
-- ============================================================================
CREATE TABLE risk_scores (
    id INT PRIMARY KEY AUTO_INCREMENT,
    region_id INT NOT NULL,
    date DATETIME NOT NULL,
    flood_risk FLOAT NOT NULL CHECK (flood_risk BETWEEN 0 AND 100),
    traffic_impact FLOAT NOT NULL CHECK (traffic_impact BETWEEN 0 AND 100),
    service_access FLOAT NOT NULL CHECK (service_access BETWEEN 0 AND 100),
    urban_risk_score FLOAT NOT NULL CHECK (urban_risk_score BETWEEN 0 AND 100),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (region_id) REFERENCES regions(region_id) ON DELETE CASCADE,
    INDEX idx_region_date (region_id, date),
    INDEX idx_urs (urban_risk_score)
);

-- ============================================================================
-- Table: recommendations
-- Description: Stores system-generated recommendations
-- ============================================================================
CREATE TABLE recommendations (
    id INT PRIMARY KEY AUTO_INCREMENT,
    region_id INT NOT NULL,
    recommendation_type VARCHAR(50) NOT NULL,
    description TEXT NOT NULL,
    urgency_level VARCHAR(20) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMP,
    is_active BOOLEAN DEFAULT TRUE,
    FOREIGN KEY (region_id) REFERENCES regions(region_id) ON DELETE CASCADE,
    INDEX idx_region_active (region_id, is_active),
    INDEX idx_urgency (urgency_level)
);

-- ============================================================================
-- Table: users
-- Description: Stores user information and roles
-- ============================================================================
CREATE TABLE users (
    id INT PRIMARY KEY AUTO_INCREMENT,
    username VARCHAR(100) NOT NULL UNIQUE,
    email VARCHAR(255) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    role VARCHAR(50) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_login TIMESTAMP,
    is_active BOOLEAN DEFAULT TRUE,
    INDEX idx_email (email),
    INDEX idx_role (role)
);
