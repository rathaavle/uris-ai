"""
Custom middleware for URIS-AI FastAPI application.

Includes:
- Rate limiting middleware (Requirements: 8.2)
- Request logging middleware
"""

import logging
import time
from collections import defaultdict
from typing import Callable, Dict, Tuple

from fastapi import Request, Response, status
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

logger = logging.getLogger(__name__)


class RateLimitMiddleware(BaseHTTPMiddleware):
    """
    Token-bucket rate limiting middleware.

    Limits requests per client IP address using a sliding window counter.
    Applies configurable per-minute and per-hour limits.

    Requirements: 8.2
    """

    # Endpoint-specific overrides: path_prefix → (per_minute, per_hour)
    ENDPOINT_LIMITS: Dict[str, Tuple[int, int]] = {
        "/auth/login": (10, 100),       # Stricter limit on login to prevent brute-force
        "/routes/safe": (30, 500),      # Route finding is compute-intensive
    }

    def __init__(
        self,
        app,
        rate_limit_per_minute: int = 60,
        rate_limit_per_hour: int = 1000,
    ):
        """
        Initialise the rate limiter.

        Args:
            app: ASGI application
            rate_limit_per_minute: Default max requests per minute per IP
            rate_limit_per_hour: Default max requests per hour per IP
        """
        super().__init__(app)
        self.default_per_minute = rate_limit_per_minute
        self.default_per_hour = rate_limit_per_hour

        # In-memory counters: {ip: [(timestamp, count), ...]}
        # In production, replace with Redis-backed counters for multi-instance support
        self._minute_counts: Dict[str, list] = defaultdict(list)
        self._hour_counts: Dict[str, list] = defaultdict(list)

    def _get_limits(self, path: str) -> Tuple[int, int]:
        """Return (per_minute, per_hour) limits for the given path."""
        for prefix, limits in self.ENDPOINT_LIMITS.items():
            if path.startswith(prefix):
                return limits
        return self.default_per_minute, self.default_per_hour

    def _count_recent(self, records: list, window_seconds: int) -> int:
        """Count requests within the sliding window."""
        now = time.time()
        cutoff = now - window_seconds
        return sum(1 for ts in records if ts > cutoff)

    def _prune(self, records: list, window_seconds: int) -> list:
        """Remove timestamps outside the window."""
        now = time.time()
        cutoff = now - window_seconds
        return [ts for ts in records if ts > cutoff]

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Apply rate limiting before forwarding the request."""
        # Skip rate limiting for health check endpoints
        if request.url.path.startswith("/health"):
            return await call_next(request)

        client_ip = request.client.host if request.client else "unknown"
        path = request.url.path
        now = time.time()

        per_minute, per_hour = self._get_limits(path)

        # Prune old entries
        self._minute_counts[client_ip] = self._prune(
            self._minute_counts[client_ip], 60
        )
        self._hour_counts[client_ip] = self._prune(
            self._hour_counts[client_ip], 3600
        )

        minute_count = len(self._minute_counts[client_ip])
        hour_count = len(self._hour_counts[client_ip])

        if minute_count >= per_minute:
            logger.warning(
                f"Rate limit exceeded (per-minute) for IP {client_ip} on {path}"
            )
            return JSONResponse(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                content={
                    "detail": "Terlalu banyak permintaan. Coba lagi dalam 1 menit.",
                    "code": "RATE_LIMIT_MINUTE",
                },
                headers={"Retry-After": "60"},
            )

        if hour_count >= per_hour:
            logger.warning(
                f"Rate limit exceeded (per-hour) for IP {client_ip} on {path}"
            )
            return JSONResponse(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                content={
                    "detail": "Terlalu banyak permintaan. Coba lagi dalam 1 jam.",
                    "code": "RATE_LIMIT_HOUR",
                },
                headers={"Retry-After": "3600"},
            )

        # Record this request
        self._minute_counts[client_ip].append(now)
        self._hour_counts[client_ip].append(now)

        response = await call_next(request)

        # Add rate limit headers to response
        response.headers["X-RateLimit-Limit-Minute"] = str(per_minute)
        response.headers["X-RateLimit-Remaining-Minute"] = str(
            max(0, per_minute - minute_count - 1)
        )
        response.headers["X-RateLimit-Limit-Hour"] = str(per_hour)
        response.headers["X-RateLimit-Remaining-Hour"] = str(
            max(0, per_hour - hour_count - 1)
        )

        return response


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """
    Middleware that logs each request with method, path, status, and duration.
    """

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        start = time.time()
        response = await call_next(request)
        duration_ms = (time.time() - start) * 1000

        logger.info(
            f"{request.method} {request.url.path} "
            f"→ {response.status_code} ({duration_ms:.1f}ms)"
        )
        return response
