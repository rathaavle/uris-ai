"""Pytest configuration and fixtures."""

import pytest
from typing import Generator


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
