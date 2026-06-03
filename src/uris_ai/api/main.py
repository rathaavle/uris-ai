"""
FastAPI main application for URIS-AI.

Wires together all routers, middleware, error handlers, and static files.

Requirements: 6.1, 6.4, 8.1, 8.2, 8.4, 10.1, 10.2
"""

import logging
from pathlib import Path
from typing import Any

from fastapi import FastAPI, HTTPException, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

from uris_ai.api.middleware import (
    RateLimitMiddleware,
    RequestLoggingMiddleware,
    HTTPSRedirectMiddleware,
)
from uris_ai.api.routers import auth, recommendations, risk, users
from uris_ai.config import settings, load_secrets_from_key_vault
from uris_ai.utils.logging_config import setup_logging
from uris_ai.utils.monitoring import app_insights, setup_application_insights_logging

# Setup logging first
setup_logging()
setup_application_insights_logging()

# Path ke static files
STATIC_DIR = Path(__file__).parent.parent / "static"

# Load secrets from Key Vault if enabled
load_secrets_from_key_vault(settings)

logger = logging.getLogger(__name__)

# Flag to track if startup tasks have been completed
_startup_completed = False

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
        swagger_ui_parameters={"persistAuthorization": True},
    )

    # ------------------------------------------------------------------
    # Middleware (order matters — outermost is applied last)
    # ------------------------------------------------------------------

    # HTTPS redirect (applied first to redirect before other processing)
    if settings.enforce_https:
        application.add_middleware(
            HTTPSRedirectMiddleware,
            enforce_https=True,
        )

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
        # Sanitize errors — pastikan semua nilai bisa di-serialize ke JSON
        errors = []
        for err in exc.errors():
            sanitized = {k: str(v) if isinstance(v, bytes) else v for k, v in err.items()}
            errors.append(sanitized)
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content={
                "detail": "Data permintaan tidak valid",
                "errors": errors,
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
    # Dashboard endpoint — serve HTML/CSS/JS frontend
    # ------------------------------------------------------------------

    @application.get("/dashboard", tags=["System"], include_in_schema=False)
    async def dashboard() -> FileResponse:
        """Serve the React dashboard (production build)."""
        static_index = STATIC_DIR / "index.html"
        if static_index.exists():
            return FileResponse(static_index)
        # Fallback jika belum di-build
        return JSONResponse(
            {"message": "Dashboard belum di-build. Jalankan: cd frontend && npm run build"},
            status_code=404,
        )

    @application.get("/api/dashboard", tags=["System"], summary="Dashboard data agregat")
    async def dashboard_data(db=None) -> dict[str, Any]:
        """
        Data agregat untuk dashboard JS.
        Mengembalikan KPI summary + semua wilayah dengan koordinat + Azure Maps key.
        """
        from uris_ai.api.dependencies import get_db
        from uris_ai.models.database import Region, RiskScore
        from sqlalchemy import func

        db_session = next(get_db())
        try:
            regions = db_session.query(Region).all()
            region_map = {r.region_id: r for r in regions}

            subq = (
                db_session.query(
                    RiskScore.region_id,
                    func.max(RiskScore.date).label("max_date"),
                )
                .group_by(RiskScore.region_id)
                .subquery()
            )
            latest_scores = (
                db_session.query(RiskScore)
                .join(
                    subq,
                    (RiskScore.region_id == subq.c.region_id)
                    & (RiskScore.date == subq.c.max_date),
                )
                .all()
            )

            from uris_ai.ml.flood_risk_engine import FloodRiskEngine
            engine = FloodRiskEngine()

            regions_out = []
            kritis = 0
            urs_total = 0.0

            for score in latest_scores:
                region = region_map.get(score.region_id)
                if not region:
                    continue
                cat = engine.get_risk_category(score.urban_risk_score).value
                if cat == "KRITIS":
                    kritis += 1
                urs_total += score.urban_risk_score
                regions_out.append({
                    "region_id": score.region_id,
                    "region_name": region.name,
                    "kota": region.name.split(",")[-1].strip() if "," in region.name else "",
                    "latitude": region.latitude,
                    "longitude": region.longitude,
                    "flood_risk": score.flood_risk,
                    "traffic_impact": score.traffic_impact,
                    "service_access": score.service_access,
                    "urban_risk_score": score.urban_risk_score,
                    "risk_category": cat,
                    "calculated_at": score.date.isoformat(),
                })

            n = len(regions_out)
            return {
                "summary": {
                    "total_regions": n,
                    "kritis_count": kritis,
                    "avg_urs": round(urs_total / n, 1) if n else 0.0,
                },
                "regions": regions_out,
                "maps_key": settings.azure_maps_key or "",
                "updated_at": __import__("datetime").datetime.now(
                    __import__("datetime").timezone.utc
                ).isoformat(),
            }
        finally:
            db_session.close()

    # Mount static files (assets/) — setelah semua route didefinisikan
    if STATIC_DIR.exists():
        application.mount(
            "/assets",
            StaticFiles(directory=str(STATIC_DIR / "assets")),
            name="static",
        )

    # ------------------------------------------------------------------
    # Startup and shutdown events
    # ------------------------------------------------------------------

    @application.on_event("startup")
    async def startup_event() -> None:
        """
        Execute startup tasks when the application starts.
        
        Initializes performance optimizations including:
        - Creating database indexes
        - Warming cache with frequently accessed data
        
        Requirements: 8.1
        """
        global _startup_completed
        
        if _startup_completed:
            logger.info("Startup tasks already completed, skipping")
            return
        
        logger.info("Executing application startup tasks...")
        
        try:
            from uris_ai.api.dependencies import get_db
            from uris_ai.startup import startup_event_handler
            
            # Get database session
            db = next(get_db())
            
            # Run startup tasks
            startup_event_handler(db)
            
            _startup_completed = True
            logger.info("Application startup tasks completed successfully")
            
            # Track startup event
            app_insights.track_event(
                "application_startup",
                properties={
                    "status": "success",
                    "version": settings.app_version
                }
            )
            
        except Exception as e:
            logger.error(f"Startup tasks failed: {e}", exc_info=True)
            app_insights.track_error()
            # Don't raise - allow application to start even if optimization fails

    @application.on_event("shutdown")
    async def shutdown_event() -> None:
        """
        Execute cleanup tasks when the application shuts down.
        """
        logger.info("Application shutdown initiated")
        
        # Track shutdown event
        app_insights.track_event(
            "application_shutdown",
            properties={"version": settings.app_version}
        )
        
        # Flush Application Insights telemetry
        if app_insights.enabled:
            app_insights.flush()

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

    @application.get("/health/performance", tags=["System"], summary="Performance optimization status")
    async def performance_status() -> dict[str, Any]:
        """
        Check the status of performance optimizations.
        
        Returns information about:
        - Database indexes
        - Cache availability and statistics
        - Startup completion status
        
        Requirements: 8.1
        """
        try:
            from uris_ai.api.dependencies import get_db
            from uris_ai.startup import get_startup_status
            
            db = next(get_db())
            status = get_startup_status(db)
            status["startup_completed"] = _startup_completed
            
            return {
                "status": "ok",
                "optimizations": status,
                "timestamp": __import__("datetime").datetime.now(
                    __import__("datetime").timezone.utc
                ).isoformat(),
            }
        except Exception as e:
            logger.error(f"Failed to get performance status: {e}", exc_info=True)
            return {
                "status": "error",
                "error": str(e),
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
