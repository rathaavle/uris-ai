#!/usr/bin/env python3
"""
Data seeding script for URIS-AI system.

This script populates the database with initial data including:
- Regions in Jakarta and Jawa Barat
- Historical flood events
- Roads and facilities data

Requirements: 7.1

Usage:
    python scripts/seed_data.py [--drop-existing]

Options:
    --drop-existing    Drop existing data before seeding (WARNING: destructive)
"""

import argparse
import logging
import sys
from datetime import datetime, timedelta
from pathlib import Path
from typing import List

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from sqlalchemy.orm import Session

from uris_ai.config import settings
from uris_ai.models.database import (
    Base,
    FloodEvent,
    PublicFacility,
    Region,
    Road,
)
from uris_ai.models.db_utils import create_db_engine, create_session_factory

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


def get_jakarta_regions() -> List[dict]:
    """
    Get sample regions data for Jakarta.
    
    Returns realistic kelurahan/kecamatan data for Jakarta.
    """
    return [
        {
            "name": "Menteng, Jakarta Pusat",
            "latitude": -6.1944,
            "longitude": 106.8294,
            "elevation": 7.0,
            "drainage_capacity": 150.0,
        },
        {
            "name": "Tanah Abang, Jakarta Pusat",
            "latitude": -6.1867,
            "longitude": 106.8133,
            "elevation": 5.0,
            "drainage_capacity": 120.0,
        },
        {
            "name": "Kemayoran, Jakarta Pusat",
            "latitude": -6.1667,
            "longitude": 106.8500,
            "elevation": 8.0,
            "drainage_capacity": 180.0,
        },
        {
            "name": "Kelapa Gading, Jakarta Utara",
            "latitude": -6.1578,
            "longitude": 106.9097,
            "elevation": 3.0,
            "drainage_capacity": 100.0,
        },
        {
            "name": "Penjaringan, Jakarta Utara",
            "latitude": -6.1167,
            "longitude": 106.7833,
            "elevation": 2.0,
            "drainage_capacity": 80.0,
        },
        {
            "name": "Pademangan, Jakarta Utara",
            "latitude": -6.1333,
            "longitude": 106.8333,
            "elevation": 4.0,
            "drainage_capacity": 110.0,
        },
        {
            "name": "Kebayoran Baru, Jakarta Selatan",
            "latitude": -6.2425,
            "longitude": 106.7972,
            "elevation": 15.0,
            "drainage_capacity": 200.0,
        },
        {
            "name": "Tebet, Jakarta Selatan",
            "latitude": -6.2333,
            "longitude": 106.8500,
            "elevation": 12.0,
            "drainage_capacity": 170.0,
        },
        {
            "name": "Cilandak, Jakarta Selatan",
            "latitude": -6.2917,
            "longitude": 106.8000,
            "elevation": 50.0,
            "drainage_capacity": 250.0,
        },
        {
            "name": "Cengkareng, Jakarta Barat",
            "latitude": -6.1500,
            "longitude": 106.7333,
            "elevation": 6.0,
            "drainage_capacity": 130.0,
        },
        {
            "name": "Kebon Jeruk, Jakarta Barat",
            "latitude": -6.1833,
            "longitude": 106.7667,
            "elevation": 10.0,
            "drainage_capacity": 160.0,
        },
        {
            "name": "Grogol Petamburan, Jakarta Barat",
            "latitude": -6.1667,
            "longitude": 106.7833,
            "elevation": 8.0,
            "drainage_capacity": 140.0,
        },
        {
            "name": "Matraman, Jakarta Timur",
            "latitude": -6.2000,
            "longitude": 106.8667,
            "elevation": 9.0,
            "drainage_capacity": 145.0,
        },
        {
            "name": "Jatinegara, Jakarta Timur",
            "latitude": -6.2167,
            "longitude": 106.8667,
            "elevation": 7.0,
            "drainage_capacity": 135.0,
        },
        {
            "name": "Cakung, Jakarta Timur",
            "latitude": -6.1667,
            "longitude": 106.9333,
            "elevation": 5.0,
            "drainage_capacity": 115.0,
        },
    ]


def get_jabar_regions() -> List[dict]:
    """
    Get sample regions data for Jawa Barat.
    
    Returns realistic kelurahan/kecamatan data for Jawa Barat.
    """
    return [
        {
            "name": "Bandung Wetan, Kota Bandung",
            "latitude": -6.9175,
            "longitude": 107.6191,
            "elevation": 768.0,
            "drainage_capacity": 220.0,
        },
        {
            "name": "Cicendo, Kota Bandung",
            "latitude": -6.9147,
            "longitude": 107.5931,
            "elevation": 750.0,
            "drainage_capacity": 210.0,
        },
        {
            "name": "Coblong, Kota Bandung",
            "latitude": -6.8722,
            "longitude": 107.6069,
            "elevation": 800.0,
            "drainage_capacity": 240.0,
        },
        {
            "name": "Bogor Tengah, Kota Bogor",
            "latitude": -6.5950,
            "longitude": 106.7969,
            "elevation": 290.0,
            "drainage_capacity": 190.0,
        },
        {
            "name": "Bogor Utara, Kota Bogor",
            "latitude": -6.5700,
            "longitude": 106.8000,
            "elevation": 250.0,
            "drainage_capacity": 180.0,
        },
        {
            "name": "Tanah Sareal, Kota Bogor",
            "latitude": -6.5833,
            "longitude": 106.7833,
            "elevation": 270.0,
            "drainage_capacity": 185.0,
        },
        {
            "name": "Bekasi Timur, Kota Bekasi",
            "latitude": -6.2500,
            "longitude": 107.0167,
            "elevation": 19.0,
            "drainage_capacity": 125.0,
        },
        {
            "name": "Bekasi Barat, Kota Bekasi",
            "latitude": -6.2333,
            "longitude": 106.9833,
            "elevation": 15.0,
            "drainage_capacity": 120.0,
        },
        {
            "name": "Pondok Gede, Kota Bekasi",
            "latitude": -6.2667,
            "longitude": 106.9833,
            "elevation": 22.0,
            "drainage_capacity": 130.0,
        },
        {
            "name": "Depok, Kota Depok",
            "latitude": -6.4000,
            "longitude": 106.8186,
            "elevation": 80.0,
            "drainage_capacity": 165.0,
        },
    ]


def seed_regions(session: Session, drop_existing: bool = False) -> List[Region]:
    """
    Seed regions data for Jakarta and Jawa Barat.
    
    Args:
        session: Database session
        drop_existing: Whether to delete existing regions first
        
    Returns:
        List of created Region objects
    """
    logger.info("Seeding regions data...")
    
    if drop_existing:
        logger.warning("Dropping existing regions...")
        session.query(Region).delete()
        session.commit()
    
    # Check if regions already exist
    existing_count = session.query(Region).count()
    if existing_count > 0:
        logger.info(f"Found {existing_count} existing regions. Skipping region seeding.")
        return session.query(Region).all()
    
    # Combine Jakarta and Jawa Barat regions
    all_regions_data = get_jakarta_regions() + get_jabar_regions()
    
    regions = []
    for region_data in all_regions_data:
        region = Region(**region_data)
        session.add(region)
        regions.append(region)
    
    session.commit()
    logger.info(f"Successfully seeded {len(regions)} regions")
    
    return regions


def seed_flood_events(session: Session, regions: List[Region], drop_existing: bool = False) -> List[FloodEvent]:
    """
    Seed historical flood events data.
    
    Creates realistic flood event data for the past 2 years.
    
    Args:
        session: Database session
        regions: List of Region objects to create flood events for
        drop_existing: Whether to delete existing flood events first
        
    Returns:
        List of created FloodEvent objects
    """
    logger.info("Seeding flood events data...")
    
    if drop_existing:
        logger.warning("Dropping existing flood events...")
        session.query(FloodEvent).delete()
        session.commit()
    
    # Check if flood events already exist
    existing_count = session.query(FloodEvent).count()
    if existing_count > 0:
        logger.info(f"Found {existing_count} existing flood events. Skipping flood event seeding.")
        return session.query(FloodEvent).all()
    
    flood_events = []
    
    # Create flood events for the past 2 years
    end_date = datetime.now()
    start_date = end_date - timedelta(days=730)  # 2 years
    
    # Define flood-prone regions (lower elevation, lower drainage capacity)
    flood_prone_regions = [r for r in regions if r.elevation < 20 and r.drainage_capacity < 150]
    
    # Generate flood events during rainy season (Nov-Mar)
    current_date = start_date
    while current_date <= end_date:
        month = current_date.month
        
        # Rainy season: higher probability of floods
        if month in [11, 12, 1, 2, 3]:
            # 20% chance of flood event per day in flood-prone regions
            import random
            random.seed(int(current_date.timestamp()))
            
            for region in flood_prone_regions:
                if random.random() < 0.20:
                    # Determine severity based on region characteristics
                    if region.elevation < 5:
                        severity = random.choice([2, 3, 3, 4])  # Higher severity for low elevation
                    else:
                        severity = random.choice([1, 2, 2, 3])
                    
                    # Generate realistic flood parameters
                    water_level = None
                    duration_hours = None
                    affected_area_km2 = None
                    
                    if severity >= 2:
                        water_level = random.uniform(20, 150) if severity == 2 else random.uniform(50, 250)
                        duration_hours = random.randint(2, 12) if severity == 2 else random.randint(6, 48)
                        affected_area_km2 = random.uniform(0.5, 3.0) if severity == 2 else random.uniform(2.0, 10.0)
                    
                    flood_event = FloodEvent(
                        region_id=region.region_id,
                        date=current_date,
                        severity=severity,
                        water_level=water_level,
                        duration_hours=duration_hours,
                        affected_area_km2=affected_area_km2,
                    )
                    session.add(flood_event)
                    flood_events.append(flood_event)
        
        current_date += timedelta(days=1)
    
    session.commit()
    logger.info(f"Successfully seeded {len(flood_events)} flood events")
    
    return flood_events


def seed_roads(session: Session, regions: List[Region], drop_existing: bool = False) -> List[Road]:
    """
    Seed roads data for each region.
    
    Args:
        session: Database session
        regions: List of Region objects to create roads for
        drop_existing: Whether to delete existing roads first
        
    Returns:
        List of created Road objects
    """
    logger.info("Seeding roads data...")
    
    if drop_existing:
        logger.warning("Dropping existing roads...")
        session.query(Road).delete()
        session.commit()
    
    # Check if roads already exist
    existing_count = session.query(Road).count()
    if existing_count > 0:
        logger.info(f"Found {existing_count} existing roads. Skipping road seeding.")
        return session.query(Road).all()
    
    roads = []
    road_types = ["primary", "secondary", "tertiary", "residential"]
    
    import random
    
    for region in regions:
        # Seed for consistent data per region
        random.seed(region.region_id)
        
        # Create 3-7 roads per region
        num_roads = random.randint(3, 7)
        
        for i in range(num_roads):
            road_type = random.choice(road_types)
            is_main_road = road_type in ["primary", "secondary"]
            
            # Road density varies by type
            if road_type == "primary":
                road_density = random.uniform(0.8, 1.5)
                length_km = random.uniform(5.0, 15.0)
            elif road_type == "secondary":
                road_density = random.uniform(0.6, 1.2)
                length_km = random.uniform(3.0, 10.0)
            elif road_type == "tertiary":
                road_density = random.uniform(0.4, 0.9)
                length_km = random.uniform(2.0, 7.0)
            else:  # residential
                road_density = random.uniform(0.2, 0.6)
                length_km = random.uniform(0.5, 3.0)
            
            road_name = f"Jalan {region.name.split(',')[0]} {i+1}"
            
            road = Road(
                region_id=region.region_id,
                road_name=road_name,
                road_type=road_type,
                road_density=road_density,
                length_km=length_km,
                is_main_road=is_main_road,
            )
            session.add(road)
            roads.append(road)
    
    session.commit()
    logger.info(f"Successfully seeded {len(roads)} roads")
    
    return roads


def seed_facilities(session: Session, regions: List[Region], drop_existing: bool = False) -> List[PublicFacility]:
    """
    Seed public facilities data (hospitals, clinics, schools, government offices).
    
    Args:
        session: Database session
        regions: List of Region objects to create facilities for
        drop_existing: Whether to delete existing facilities first
        
    Returns:
        List of created PublicFacility objects
    """
    logger.info("Seeding public facilities data...")
    
    if drop_existing:
        logger.warning("Dropping existing facilities...")
        session.query(PublicFacility).delete()
        session.commit()
    
    # Check if facilities already exist
    existing_count = session.query(PublicFacility).count()
    if existing_count > 0:
        logger.info(f"Found {existing_count} existing facilities. Skipping facility seeding.")
        return session.query(PublicFacility).all()
    
    facilities = []
    facility_types = ["hospital", "clinic", "school", "government"]
    
    import random
    
    for region in regions:
        # Seed for consistent data per region
        random.seed(region.region_id + 1000)
        
        # Create 4-8 facilities per region (at least one of each type)
        for facility_type in facility_types:
            num_facilities = random.randint(1, 2)
            
            for i in range(num_facilities):
                # Generate coordinates near region center with some offset
                lat_offset = random.uniform(-0.01, 0.01)
                lon_offset = random.uniform(-0.01, 0.01)
                
                # Determine capacity based on type
                if facility_type == "hospital":
                    capacity = random.randint(100, 500)
                    name = f"RS {region.name.split(',')[0]} {i+1}"
                elif facility_type == "clinic":
                    capacity = random.randint(20, 100)
                    name = f"Puskesmas {region.name.split(',')[0]} {i+1}"
                elif facility_type == "school":
                    capacity = random.randint(200, 1000)
                    name = f"Sekolah {region.name.split(',')[0]} {i+1}"
                else:  # government
                    capacity = random.randint(50, 200)
                    name = f"Kantor Kelurahan {region.name.split(',')[0]} {i+1}"
                
                facility = PublicFacility(
                    region_id=region.region_id,
                    name=name,
                    type=facility_type,
                    latitude=region.latitude + lat_offset,
                    longitude=region.longitude + lon_offset,
                    capacity=capacity,
                    is_operational=True,
                )
                session.add(facility)
                facilities.append(facility)
    
    session.commit()
    logger.info(f"Successfully seeded {len(facilities)} public facilities")
    
    return facilities


def main():
    """Main function to run data seeding."""
    parser = argparse.ArgumentParser(description="Seed initial data for URIS-AI system")
    parser.add_argument(
        "--drop-existing",
        action="store_true",
        help="Drop existing data before seeding (WARNING: destructive)",
    )
    args = parser.parse_args()
    
    if args.drop_existing:
        logger.warning("WARNING: --drop-existing flag is set. This will delete all existing data!")
        response = input("Are you sure you want to continue? (yes/no): ")
        if response.lower() != "yes":
            logger.info("Seeding cancelled by user")
            return
    
    try:
        # Create database engine and session
        logger.info("Connecting to database...")
        engine = create_db_engine(settings.azure_mysql_connection_string)
        session_factory = create_session_factory(engine)
        
        # Create tables if they don't exist
        logger.info("Ensuring database schema exists...")
        Base.metadata.create_all(bind=engine)
        
        # Create session
        session = session_factory()
        
        try:
            # Seed data in order (respecting foreign key constraints)
            regions = seed_regions(session, drop_existing=args.drop_existing)
            seed_flood_events(session, regions, drop_existing=args.drop_existing)
            seed_roads(session, regions, drop_existing=args.drop_existing)
            seed_facilities(session, regions, drop_existing=args.drop_existing)
            
            logger.info("Data seeding completed successfully!")
            
        finally:
            session.close()
            
    except Exception as e:
        logger.error(f"Error during data seeding: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
