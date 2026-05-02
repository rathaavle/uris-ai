"""
FastAPI main application for URIS-AI.

Wires together all routers, middleware, and error handlers.

Requirements: 6.1, 6.4, 8.1, 8.2, 8.4, 10.1, 10.2
"""

import logging
from typing import Any

from fastapi import FastAPI, HTTPException, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from uris_ai.api.middleware import RateLimitMiddleware, RequestLoggingMiddleware
from uris_ai.api.routers import auth, recommendations, risk, users
from uris_ai.config import settings
from uris_ai.utils.logging_config import setup_logging
from uris_ai.utils.monitoring import app_insights, setup_application_insights_logging

# Setup logging first
setup_logging()
setup_application_insights_logging()

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Application factory
# ---------------------------------------------------------------------------


def create_app() -> FastAPI:
    """
    Create and configure the FastAPI application.

    Returns:
        Configured FastAPI instance
    """
    application = FastAPI(
        title=settings.app_name,
        version=settings.app_version,
        description=(
            "Urban Risk Intelligence System for Flood-Aware Mobility "
            "and Public Service Optimization"
        ),
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_url="/openapi.json",
    )

    # ------------------------------------------------------------------
    # Middleware (order matters — outermost is applied last)
    # ------------------------------------------------------------------

    # CORS — must be added before rate limiting so preflight requests pass
    application.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # Restrict to known origins in production
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Request logging
    application.add_middleware(RequestLoggingMiddleware)

    # Rate limiting (only when enabled in config)
    if settings.enable_rate_limiting:
        application.add_middleware(
            RateLimitMiddleware,
            rate_limit_per_minute=settings.rate_limit_per_minute,
            rate_limit_per_hour=settings.rate_limit_per_hour,
        )

    # ------------------------------------------------------------------
    # Exception handlers
    # ------------------------------------------------------------------

    @application.exception_handler(RequestValidationError)
    async def validation_exception_handler(
        request: Request, exc: RequestValidationError
    ) -> JSONResponse:
        """Return a structured 422 response for request validation errors."""
        logger.warning(f"Validation error on {request.url.path}: {exc.errors()}")
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content={
                "detail": "Data permintaan tidak valid",
                "errors": exc.errors(),
            },
        )

    @application.exception_handler(HTTPException)
    async def http_exception_handler(
        request: Request, exc: HTTPException
    ) -> JSONResponse:
        """Return a consistent JSON body for all HTTP exceptions."""
        return JSONResponse(
            status_code=exc.status_code,
            content={"detail": exc.detail},
            headers=getattr(exc, "headers", None),
        )

    @application.exception_handler(Exception)
    async def generic_exception_handler(
        request: Request, exc: Exception
    ) -> JSONResponse:
        """Catch-all handler that prevents stack traces leaking to clients."""
        logger.error(
            f"Unhandled exception on {request.method} {request.url.path}: {exc}",
            exc_info=True,
        )
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"detail": "Terjadi kesalahan internal pada server"},
        )

    # ------------------------------------------------------------------
    # Routers
    # ------------------------------------------------------------------

    application.include_router(auth.router)
    application.include_router(users.router)
    application.include_router(risk.router)
    application.include_router(recommendations.router)

    # ------------------------------------------------------------------
    # Root and health endpoints
    # ------------------------------------------------------------------

    @application.get("/", tags=["System"], summary="Root endpoint")
    async def root() -> dict[str, Any]:
        """Return basic application information."""
        return {
            "name": settings.app_name,
            "version": settings.app_version,
            "status": "running",
        }

    @application.get("/health", tags=["System"], summary="Health check")
    async def health() -> dict[str, Any]:
        """
        Basic health check — always returns 200 if the app is running.
        
        Requirements: 8.4, 9.4
        """
        return {
            "status": "healthy",
            "version": settings.app_version,
            "timestamp": __import__("datetime").datetime.now(
                __import__("datetime").timezone.utc
            ).isoformat(),
        }

    @application.get("/health/ready", tags=["System"], summary="Readiness check")
    async def readiness() -> dict[str, Any]:
        """
        Readiness check — verifies connectivity to dependent services.
        
        Checks:
        - Database connectivity
        - Redis cache availability
        - External API accessibility (optional)

        Requirements: 8.4, 9.4
        """
        checks: dict[str, str] = {}
        all_critical_ok = True

        # Database check (critical)
        try:
            from uris_ai.api.dependencies import get_engine
            engine = get_engine()
            with engine.connect() as conn:
                conn.execute(__import__("sqlalchemy").text("SELECT 1"))
            checks["database"] = "ok"
            logger.debug("Database readiness check: OK")
        except Exception as exc:
            logger.error(f"Database readiness check failed: {exc}", exc_info=True)
            checks["database"] = "error"
            all_critical_ok = False
            app_insights.track_error()

        # Redis check (non-critical, can operate without cache)
        try:
            from uris_ai.services.cache_service import CacheService
            cache = CacheService()
            if cache.is_available:
                checks["cache"] = "ok"
                logger.debug("Cache readiness check: OK")
            else:
                checks["cache"] = "unavailable"
                logger.warning("Cache is not available")
        except Exception as exc:
            logger.warning(f"Cache readiness check failed: {exc}")
            checks["cache"] = "error"

        # Application Insights check (non-critical)
        checks["monitoring"] = "ok" if app_insights.enabled else "disabled"

        status_value = "ready" if all_critical_ok else "not_ready"
        
        # Track readiness status
        app_insights.track_event(
            "health_check_ready",
            properties={
                "status": status_value,
                "database": checks["database"],
                "cache": checks["cache"],
            },
        )

        return {
            "status": status_value,
            "checks": checks,
            "timestamp": __import__("datetime").datetime.now(
                __import__("datetime").timezone.utc
            ).isoformat(),
        }

    @application.get("/health/live", tags=["System"], summary="Liveness check")
    async def liveness() -> dict[str, Any]:
        """
        Liveness check — confirms the process is alive and can handle requests.
        
        This endpoint should always return 200 if the application process is running.
        Kubernetes/Azure uses this to determine if the pod/instance should be restarted.
        
        Requirements: 8.4, 9.4
        """
        return {
            "status": "alive",
            "timestamp": __import__("datetime").datetime.now(
                __import__("datetime").timezone.utc
            ).isoformat(),
        }

    return application


# ---------------------------------------------------------------------------
# Application instance
# ---------------------------------------------------------------------------

app = create_app()


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "uris_ai.api.main:app",
        host=settings.api_host,
        port=settings.api_port,
        reload=settings.api_reload,
        workers=settings.api_workers if not settings.api_reload else 1,
    )
