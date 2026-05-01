"""
FastAPI main application for URIS-AI.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from uris_ai.config import settings

# Create FastAPI app
app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="Urban Risk Intelligence System for Flood-Aware Mobility and Public Service Optimization",
    docs_url="/docs",
    redoc_url="/redoc",
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
async def root() -> dict:
    """Root endpoint."""
    return {
        "name": settings.app_name,
        "version": settings.app_version,
        "status": "running",
    }


@app.get("/health")
async def health() -> dict:
    """Health check endpoint."""
    return {
        "status": "healthy",
        "version": settings.app_version,
    }


@app.get("/health/ready")
async def readiness() -> dict:
    """Readiness check endpoint."""
    # TODO: Check database connection, external services, etc.
    return {
        "status": "ready",
        "checks": {
            "database": "ok",
            "cache": "ok",
            "storage": "ok",
        },
    }


@app.get("/health/live")
async def liveness() -> dict:
    """Liveness check endpoint."""
    return {
        "status": "alive",
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "uris_ai.api.main:app",
        host=settings.api_host,
        port=settings.api_port,
        reload=settings.api_reload,
    )
