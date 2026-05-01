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
