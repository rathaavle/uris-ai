"""
Unit tests for the retry utility module.

Tests cover:
- Successful call on first attempt
- Retry on retryable exception, success on second attempt
- All retries exhausted raises RetryExhaustedError
- Non-retryable exception is not retried
- Backoff timing (mock time.sleep, verify calls)
- Jitter adds variation to backoff
- on_retry callback is called with correct arguments
- max_backoff_seconds caps the backoff

Requirements: 7.3
"""

from unittest.mock import MagicMock, call, patch

import pytest

from uris_ai.utils.retry import RetryConfig, RetryExhaustedError, retry_with_backoff


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_flaky(fail_times: int, return_value: object = "ok"):
    """
    Return a callable that raises ValueError for the first *fail_times*
    calls and then returns *return_value*.
    """
    calls = {"count": 0}

    def flaky(*args, **kwargs):
        if calls["count"] < fail_times:
            calls["count"] += 1
            raise ValueError(f"Transient failure #{calls['count']}")
        return return_value

    flaky.__name__ = "flaky"
    return flaky


# ---------------------------------------------------------------------------
# Test: successful call on first attempt
# ---------------------------------------------------------------------------


class TestSuccessOnFirstAttempt:
    @patch("uris_ai.utils.retry.time.sleep")
    def test_returns_value_without_sleeping(self, mock_sleep):
        """A function that succeeds immediately returns its value without sleeping."""
        result = retry_with_backoff(lambda: 42, retry_config=RetryConfig(max_retries=3))

        assert result == 42
        mock_sleep.assert_not_called()

    @patch("uris_ai.utils.retry.time.sleep")
    def test_passes_args_and_kwargs(self, mock_sleep):
        """Positional and keyword arguments are forwarded to the function."""

        def add(a, b, multiplier=1):
            return (a + b) * multiplier

        result = retry_with_backoff(add, 3, 4, multiplier=2, retry_config=RetryConfig())
        assert result == 14


# ---------------------------------------------------------------------------
# Test: retry on retryable exception, success on second attempt
# ---------------------------------------------------------------------------


class TestRetryOnTransientFailure:
    @patch("uris_ai.utils.retry.time.sleep")
    def test_succeeds_on_second_attempt(self, mock_sleep):
        """Retries once after a transient failure and returns the value."""
        flaky = _make_flaky(fail_times=1, return_value="success")

        result = retry_with_backoff(
            flaky,
            retry_config=RetryConfig(max_retries=3, jitter=False),
        )

        assert result == "success"
        assert mock_sleep.call_count == 1  # slept once before the retry

    @patch("uris_ai.utils.retry.time.sleep")
    def test_succeeds_on_third_attempt(self, mock_sleep):
        """Retries twice after transient failures and returns the value."""
        flaky = _make_flaky(fail_times=2, return_value="done")

        result = retry_with_backoff(
            flaky,
            retry_config=RetryConfig(max_retries=3, jitter=False),
        )

        assert result == "done"
        assert mock_sleep.call_count == 2


# ---------------------------------------------------------------------------
# Test: all retries exhausted raises RetryExhaustedError
# ---------------------------------------------------------------------------


class TestRetryExhausted:
    @patch("uris_ai.utils.retry.time.sleep")
    def test_raises_retry_exhausted_error(self, mock_sleep):
        """Raises RetryExhaustedError when all retries are exhausted."""
        always_fails = _make_flaky(fail_times=999)

        with pytest.raises(RetryExhaustedError):
            retry_with_backoff(
                always_fails,
                retry_config=RetryConfig(max_retries=3, jitter=False),
            )

    @patch("uris_ai.utils.retry.time.sleep")
    def test_retry_exhausted_wraps_last_exception(self, mock_sleep):
        """RetryExhaustedError.last_exception holds the final exception."""
        always_fails = _make_flaky(fail_times=999)

        with pytest.raises(RetryExhaustedError) as exc_info:
            retry_with_backoff(
                always_fails,
                retry_config=RetryConfig(max_retries=2, jitter=False),
            )

        assert exc_info.value.last_exception is not None
        assert isinstance(exc_info.value.last_exception, ValueError)

    @patch("uris_ai.utils.retry.time.sleep")
    def test_sleep_called_max_retries_times(self, mock_sleep):
        """time.sleep is called exactly max_retries times before giving up."""
        always_fails = _make_flaky(fail_times=999)
        max_retries = 4

        with pytest.raises(RetryExhaustedError):
            retry_with_backoff(
                always_fails,
                retry_config=RetryConfig(max_retries=max_retries, jitter=False),
            )

        assert mock_sleep.call_count == max_retries


# ---------------------------------------------------------------------------
# Test: non-retryable exception is not retried
# ---------------------------------------------------------------------------


class TestNonRetryableException:
    @patch("uris_ai.utils.retry.time.sleep")
    def test_non_retryable_exception_propagates_immediately(self, mock_sleep):
        """An exception not in retryable_exceptions is re-raised without retrying."""

        def raises_type_error():
            raise TypeError("not retryable")

        with pytest.raises(TypeError, match="not retryable"):
            retry_with_backoff(
                raises_type_error,
                retry_config=RetryConfig(max_retries=3),
                retryable_exceptions=(ValueError,),
            )

        mock_sleep.assert_not_called()

    @patch("uris_ai.utils.retry.time.sleep")
    def test_retryable_exception_is_retried(self, mock_sleep):
        """An exception in retryable_exceptions triggers a retry."""
        flaky = _make_flaky(fail_times=1, return_value="ok")

        result = retry_with_backoff(
            flaky,
            retry_config=RetryConfig(max_retries=3, jitter=False),
            retryable_exceptions=(ValueError,),
        )

        assert result == "ok"
        assert mock_sleep.call_count == 1


# ---------------------------------------------------------------------------
# Test: backoff timing
# ---------------------------------------------------------------------------


class TestBackoffTiming:
    @patch("uris_ai.utils.retry.time.sleep")
    def test_exponential_backoff_without_jitter(self, mock_sleep):
        """
        Backoff grows exponentially: initial * multiplier^attempt.
        With jitter=False the sleep values are exact.
        """
        always_fails = _make_flaky(fail_times=999)
        config = RetryConfig(
            max_retries=3,
            initial_backoff_seconds=1.0,
            backoff_multiplier=2.0,
            max_backoff_seconds=60.0,
            jitter=False,
        )

        with pytest.raises(RetryExhaustedError):
            retry_with_backoff(always_fails, retry_config=config)

        # attempt 0 → 1.0 * 2^0 = 1.0
        # attempt 1 → 1.0 * 2^1 = 2.0
        # attempt 2 → 1.0 * 2^2 = 4.0
        expected_calls = [call(1.0), call(2.0), call(4.0)]
        assert mock_sleep.call_args_list == expected_calls

    @patch("uris_ai.utils.retry.time.sleep")
    def test_max_backoff_caps_sleep_duration(self, mock_sleep):
        """Backoff is capped at max_backoff_seconds."""
        always_fails = _make_flaky(fail_times=999)
        config = RetryConfig(
            max_retries=5,
            initial_backoff_seconds=10.0,
            backoff_multiplier=4.0,
            max_backoff_seconds=30.0,
            jitter=False,
        )

        with pytest.raises(RetryExhaustedError):
            retry_with_backoff(always_fails, retry_config=config)

        for sleep_call in mock_sleep.call_args_list:
            assert sleep_call[0][0] <= 30.0, (
                f"Sleep duration {sleep_call[0][0]} exceeds max_backoff_seconds=30.0"
            )


# ---------------------------------------------------------------------------
# Test: jitter adds variation to backoff
# ---------------------------------------------------------------------------


class TestJitter:
    @patch("uris_ai.utils.retry.time.sleep")
    def test_jitter_produces_values_within_20_percent(self, mock_sleep):
        """
        With jitter=True the actual sleep time is within ±20 % of the
        nominal backoff.
        """
        always_fails = _make_flaky(fail_times=999)
        config = RetryConfig(
            max_retries=3,
            initial_backoff_seconds=10.0,
            backoff_multiplier=1.0,  # constant backoff = 10 s
            max_backoff_seconds=60.0,
            jitter=True,
        )

        with pytest.raises(RetryExhaustedError):
            retry_with_backoff(always_fails, retry_config=config)

        for sleep_call in mock_sleep.call_args_list:
            actual = sleep_call[0][0]
            assert 8.0 <= actual <= 12.0, (
                f"Jittered sleep {actual:.3f}s is outside ±20% of 10.0s"
            )

    @patch("uris_ai.utils.retry.time.sleep")
    def test_jitter_false_produces_exact_values(self, mock_sleep):
        """With jitter=False the sleep time equals the nominal backoff exactly."""
        always_fails = _make_flaky(fail_times=999)
        config = RetryConfig(
            max_retries=2,
            initial_backoff_seconds=5.0,
            backoff_multiplier=1.0,
            max_backoff_seconds=60.0,
            jitter=False,
        )

        with pytest.raises(RetryExhaustedError):
            retry_with_backoff(always_fails, retry_config=config)

        for sleep_call in mock_sleep.call_args_list:
            assert sleep_call[0][0] == 5.0


# ---------------------------------------------------------------------------
# Test: on_retry callback
# ---------------------------------------------------------------------------


class TestOnRetryCallback:
    @patch("uris_ai.utils.retry.time.sleep")
    def test_on_retry_called_on_each_retry(self, mock_sleep):
        """on_retry is called once per retry (not on the initial attempt)."""
        always_fails = _make_flaky(fail_times=999)
        on_retry = MagicMock()

        with pytest.raises(RetryExhaustedError):
            retry_with_backoff(
                always_fails,
                retry_config=RetryConfig(max_retries=3, jitter=False),
                on_retry=on_retry,
            )

        assert on_retry.call_count == 3

    @patch("uris_ai.utils.retry.time.sleep")
    def test_on_retry_receives_correct_attempt_number(self, mock_sleep):
        """on_retry receives 1-based attempt numbers."""
        always_fails = _make_flaky(fail_times=999)
        attempt_numbers = []

        def capture_attempt(attempt, exc, backoff):
            attempt_numbers.append(attempt)

        with pytest.raises(RetryExhaustedError):
            retry_with_backoff(
                always_fails,
                retry_config=RetryConfig(max_retries=3, jitter=False),
                on_retry=capture_attempt,
            )

        assert attempt_numbers == [1, 2, 3]

    @patch("uris_ai.utils.retry.time.sleep")
    def test_on_retry_receives_exception_and_backoff(self, mock_sleep):
        """on_retry receives the exception and the computed backoff duration."""
        always_fails = _make_flaky(fail_times=999)
        callback_args = []

        def capture(attempt, exc, backoff):
            callback_args.append((attempt, exc, backoff))

        config = RetryConfig(
            max_retries=2,
            initial_backoff_seconds=2.0,
            backoff_multiplier=3.0,
            max_backoff_seconds=60.0,
            jitter=False,
        )

        with pytest.raises(RetryExhaustedError):
            retry_with_backoff(always_fails, retry_config=config, on_retry=capture)

        # attempt 0 → backoff = 2.0 * 3^0 = 2.0
        # attempt 1 → backoff = 2.0 * 3^1 = 6.0
        assert len(callback_args) == 2
        assert callback_args[0][0] == 1
        assert isinstance(callback_args[0][1], ValueError)
        assert callback_args[0][2] == pytest.approx(2.0)
        assert callback_args[1][0] == 2
        assert callback_args[1][2] == pytest.approx(6.0)

    @patch("uris_ai.utils.retry.time.sleep")
    def test_on_retry_not_called_on_success(self, mock_sleep):
        """on_retry is not called when the function succeeds on the first attempt."""
        on_retry = MagicMock()

        result = retry_with_backoff(
            lambda: "ok",
            retry_config=RetryConfig(max_retries=3),
            on_retry=on_retry,
        )

        assert result == "ok"
        on_retry.assert_not_called()
