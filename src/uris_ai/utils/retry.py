"""
Shared exponential backoff retry utility.

Provides a reusable retry mechanism with configurable backoff, jitter,
and callback support for use across all URIS-AI components.

Requirements: 7.3
"""

import logging
import random
import time
from dataclasses import dataclass, field
from typing import Any, Callable, Optional, Tuple, Type

logger = logging.getLogger(__name__)


class RetryExhaustedError(Exception):
    """
    Raised when all retry attempts have been exhausted.

    Wraps the last exception that caused the final failure so callers
    can inspect the root cause.
    """

    def __init__(self, message: str, last_exception: Optional[Exception] = None) -> None:
        super().__init__(message)
        self.last_exception = last_exception


@dataclass
class RetryConfig:
    """
    Configuration for the exponential backoff retry strategy.

    Attributes:
        max_retries: Maximum number of retry attempts (not counting the initial call).
        initial_backoff_seconds: Backoff duration (in seconds) before the first retry.
        max_backoff_seconds: Upper cap on the computed backoff duration.
        backoff_multiplier: Factor by which the backoff grows on each attempt.
        jitter: When True, adds ±20 % random variation to the computed backoff.
    """

    max_retries: int = 3
    initial_backoff_seconds: float = 1.0
    max_backoff_seconds: float = 60.0
    backoff_multiplier: float = 2.0
    jitter: bool = True


def retry_with_backoff(
    func: Callable[..., Any],
    *args: Any,
    retry_config: Optional[RetryConfig] = None,
    retryable_exceptions: Optional[Tuple[Type[Exception], ...]] = None,
    on_retry: Optional[Callable[[int, Exception, float], None]] = None,
    **kwargs: Any,
) -> Any:
    """
    Call *func* with exponential backoff retries.

    The function is called up to ``retry_config.max_retries + 1`` times in
    total (one initial attempt plus up to ``max_retries`` retries).

    Backoff formula::

        backoff = min(initial * multiplier ^ attempt, max_backoff)

    When ``jitter=True`` the actual sleep time is::

        sleep = backoff * uniform(0.8, 1.2)

    Args:
        func: Callable to invoke.
        *args: Positional arguments forwarded to *func*.
        retry_config: Retry strategy configuration.  Defaults to
            ``RetryConfig()`` (3 retries, 1 s initial backoff).
        retryable_exceptions: Tuple of exception types that should trigger a
            retry.  Any other exception type is re-raised immediately.
            Defaults to ``(Exception,)`` — retry on any exception.
        on_retry: Optional callback invoked before each retry sleep with
            signature ``(attempt: int, exception: Exception, backoff: float)``.
            *attempt* is 1-based (first retry = 1).
        **kwargs: Keyword arguments forwarded to *func*.

    Returns:
        The return value of *func* on success.

    Raises:
        RetryExhaustedError: When all retries are exhausted.  The
            ``last_exception`` attribute holds the final exception.
        Exception: Any exception type not in *retryable_exceptions* is
            re-raised immediately without retrying.
    """
    config = retry_config or RetryConfig()
    retryable = retryable_exceptions or (Exception,)

    last_exception: Optional[Exception] = None

    for attempt in range(config.max_retries + 1):
        try:
            return func(*args, **kwargs)
        except retryable as exc:
            last_exception = exc

            if attempt == config.max_retries:
                # All retries exhausted — raise RetryExhaustedError
                raise RetryExhaustedError(
                    f"All {config.max_retries} retries exhausted for {getattr(func, '__name__', repr(func))}",
                    last_exception=exc,
                ) from exc

            # Compute backoff for this retry
            backoff = min(
                config.initial_backoff_seconds * (config.backoff_multiplier ** attempt),
                config.max_backoff_seconds,
            )

            if config.jitter:
                backoff = backoff * random.uniform(0.8, 1.2)

            retry_number = attempt + 1  # 1-based for human-readable logging

            logger.warning(
                "Attempt %d/%d failed for %s: %s. Retrying in %.2fs.",
                retry_number,
                config.max_retries,
                getattr(func, "__name__", repr(func)),
                exc,
                backoff,
            )

            if on_retry is not None:
                on_retry(retry_number, exc, backoff)

            time.sleep(backoff)
        except Exception:
            # Non-retryable exception — re-raise immediately
            raise
