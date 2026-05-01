"""Pytest configuration and fixtures."""

from datetime import datetime
from typing import Generator

import pytest
from sqlalchemy import create_engine
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, sessionmaker

from uris_ai.models.database import Base
from uris_ai.models.db_utils import init_database, drop_all_tables


@pytest.fixture(scope="function")
def db_engine() -> Generator[Engine, None, None]:
    """Create an in-memory SQLite database engine for testing."""
    engine = create_engine("sqlite:///:memory:", echo=False)
    init_database(engine)
    yield engine
    drop_all_tables(engine)
    engine.dispose()


@pytest.fixture(scope="function")
def db_session(db_engine: Engine) -> Generator[Session, None, None]:
    """Create a database session for testing."""
    SessionFactory = sessionmaker(bind=db_engine)
    session = SessionFactory()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


@pytest.fixture
def sample_region_id() -> int:
    """Sample region ID for testing."""
    return 1


@pytest.fixture
def sample_weather_data() -> dict:
    """Sample weather data for testing."""
    return {
        "region_id": 1,
        "rainfall": 50.0,
        "humidity": 80.0,
        "temperature": 28.0,
        "wind_speed": 15.0,
    }


@pytest.fixture
def sample_datetime() -> datetime:
    """Sample datetime for testing."""
    return datetime(2024, 1, 15, 10, 30, 0)


# Mock settings for data ingestion tests
from unittest.mock import Mock, patch


@pytest.fixture(scope="session", autouse=True)
def mock_settings():
    """Mock settings to avoid requiring environment variables during tests."""
    with patch("src.uris_ai.config.Settings") as mock_settings_class:
        mock_instance = Mock()
        
        # Set default values for all required settings
        mock_instance.azure_subscription_id = "test-subscription"
        mock_instance.azure_tenant_id = "test-tenant"
        mock_instance.azure_storage_connection_string = "DefaultEndpointsProtocol=https;AccountName=test;AccountKey=test;EndpointSuffix=core.windows.net"
        mock_instance.azure_storage_container_raw_data = "raw-data"
        mock_instance.weather_api_url = "https://api.test.com/weather"
        mock_instance.weather_api_key = "test-key"
        mock_instance.osm_api_url = "https://overpass-api.de/api/interpreter"
        
        mock_settings_class.return_value = mock_instance
        
        # Also patch the settings instance
        with patch("src.uris_ai.config.settings", mock_instance):
            yield mock_instance


@pytest.fixture
def mock_blob_storage():
    """Mock Azure Blob Storage client."""
    mock_client = Mock()
    mock_blob_client = Mock()
    mock_blob_client.url = "https://test.blob.core.windows.net/container/blob.json"
    mock_blob_client.get_blob_properties.return_value = Mock(size=1024)
    mock_client.get_blob_client.return_value = mock_blob_client
    return mock_client
