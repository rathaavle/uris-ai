"""
Azure Function: Scheduled Weather Data Fetcher

Timer trigger that runs every 10 minutes to fetch weather data
from the external API and store it to Azure Blob Storage.

Requirements: 1.1, 7.2, 7.3
"""

import json
import logging
import os
from datetime import datetime, timezone
from typing import List

import azure.functions as func

logger = logging.getLogger(__name__)

# Default region IDs for Jakarta and West Java
# These can be overridden via the WEATHER_REGION_IDS environment variable
DEFAULT_REGION_IDS: List[int] = list(range(1, 11))  # Regions 1-10 as default


def _get_region_ids() -> List[int]:
    """
    Get the list of region IDs to fetch weather data for.

    Reads from WEATHER_REGION_IDS environment variable (comma-separated integers).
    Falls back to DEFAULT_REGION_IDS if not set or invalid.

    Returns:
        List of region IDs
    """
    region_ids_env = os.environ.get("WEATHER_REGION_IDS", "")
    if region_ids_env:
        try:
            return [int(rid.strip()) for rid in region_ids_env.split(",") if rid.strip()]
        except ValueError:
            logger.warning(
                "Invalid WEATHER_REGION_IDS value '%s', using defaults", region_ids_env
            )
    return DEFAULT_REGION_IDS


def main(mytimer: func.TimerRequest) -> None:
    """
    Azure Function entry point for scheduled weather data fetching.

    Triggered every 10 minutes via timer trigger (NCRONTAB: 0 */10 * * * *).
    Fetches weather data for all configured regions and stores to Azure Blob Storage.

    Args:
        mytimer: Azure Functions timer trigger object
    """
    utc_timestamp = datetime.now(timezone.utc).isoformat()

    if mytimer.past_due:
        logger.warning(
            "Weather fetcher timer is past due. Execution time: %s", utc_timestamp
        )

    logger.info(
        "Weather data fetcher triggered at %s",
        utc_timestamp,
        extra={
            "function_name": "weather_fetcher",
            "trigger_time": utc_timestamp,
            "past_due": mytimer.past_due,
        },
    )

    region_ids = _get_region_ids()
    logger.info(
        "Fetching weather data for %d regions: %s",
        len(region_ids),
        region_ids,
    )

    try:
        _fetch_and_store_weather(region_ids, utc_timestamp)
    except Exception as exc:
        # Catch all exceptions to prevent the function host from crashing.
        # The error is logged with full context for debugging.
        logger.error(
            "Unhandled error in weather_fetcher function: %s",
            exc,
            exc_info=True,
            extra={
                "function_name": "weather_fetcher",
                "trigger_time": utc_timestamp,
                "region_ids": region_ids,
            },
        )


def _fetch_and_store_weather(region_ids: List[int], trigger_time: str) -> None:
    """
    Fetch weather data and store it to Azure Blob Storage.

    Imports are deferred inside the function so that the Azure Functions
    host can load the module even when optional dependencies (e.g. the
    settings object that requires a .env file) are not fully configured.

    Args:
        region_ids: List of region IDs to fetch weather data for
        trigger_time: ISO-format UTC timestamp of the trigger (for logging)

    Raises:
        Exception: Re-raises any unexpected exception after logging
    """
    # Deferred import to avoid import-time side effects in the Functions host
    from uris_ai.data.weather_connector import WeatherAPIConnector
    from uris_ai.data.integrator import DataFetchError
    from uris_ai.utils import AlertLevel, AlertManager, RetryConfig, retry_with_backoff
    from uris_ai.utils.retry import RetryExhaustedError

    connector = WeatherAPIConnector()
    alert_manager = AlertManager(source="weather_fetcher")

    retry_config = RetryConfig(max_retries=3, initial_backoff_seconds=2.0)

    try:
        weather_batch = retry_with_backoff(
            connector.fetch_weather_data,
            region_ids,
            retry_config=retry_config,
            retryable_exceptions=(DataFetchError, Exception),
            on_retry=lambda attempt, exc, backoff: logger.warning(
                "Retry %d for fetch_weather_data after %.2fs: %s",
                attempt,
                backoff,
                exc,
                extra={
                    "function_name": "weather_fetcher",
                    "trigger_time": trigger_time,
                    "retry_attempt": attempt,
                },
            ),
        )
    except (RetryExhaustedError, DataFetchError, Exception) as exc:
        alert_manager.send_alert(
            level=AlertLevel.CRITICAL,
            message=f"All retries exhausted fetching weather data: {exc}",
            details={
                "function_name": "weather_fetcher",
                "trigger_time": trigger_time,
                "region_ids": region_ids,
                "error_type": type(exc).__name__,
                "error_message": str(exc),
            },
        )
        logger.error(
            "Failed to fetch weather data after retries: %s",
            exc,
            extra={
                "function_name": "weather_fetcher",
                "trigger_time": trigger_time,
                "region_ids": region_ids,
                "error_type": type(exc).__name__,
            },
        )
        return

    logger.info(
        "Successfully fetched weather data for %d regions",
        len(weather_batch.data),
        extra={
            "function_name": "weather_fetcher",
            "trigger_time": trigger_time,
            "regions_fetched": len(weather_batch.data),
            "batch_timestamp": weather_batch.timestamp.isoformat(),
        },
    )

    # Store raw data to Azure Blob Storage
    storage_result = connector.store_raw_data(
        data=weather_batch,
        data_type="weather",
        metadata={
            "trigger_time": trigger_time,
            "region_count": str(len(weather_batch.data)),
            "source": weather_batch.source,
        },
    )

    if storage_result.success:
        logger.info(
            "Weather data stored successfully: blob=%s, size=%d bytes",
            storage_result.blob_name,
            storage_result.size_bytes,
            extra={
                "function_name": "weather_fetcher",
                "trigger_time": trigger_time,
                "blob_name": storage_result.blob_name,
                "blob_url": storage_result.blob_url,
                "size_bytes": storage_result.size_bytes,
            },
        )
    else:
        logger.error(
            "Failed to store weather data to blob storage: %s",
            storage_result.error_message,
            extra={
                "function_name": "weather_fetcher",
                "trigger_time": trigger_time,
                "error_type": "StorageError",
                "error_message": storage_result.error_message,
            },
        )
