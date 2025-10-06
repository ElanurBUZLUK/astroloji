"""FastAPI application entry-point."""
from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from loguru import logger

from backend.app.api import admin, alerts, auth, charts, horoscope, interpretations
from backend.app.api.v1 import api_router as api_v1_router
from backend.app.config import settings
from backend.app.evaluation.observability import observability
from backend.app.logging_setup import setup_logging
from backend.app.middleware.observability import ObservabilityMiddleware, PerformanceMiddleware
from backend.app.middleware.privacy import PIIMaskingMiddleware


setup_logging(settings)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifecycle hooks for application start and shutdown."""

    logger.info("Starting service startup")
    observability.update_system_health()

    yield

    logger.info("Service shutdown complete")


def create_app() -> FastAPI:
    """Instantiate the FastAPI application and register middleware/routers."""

    app = FastAPI(
        title=settings.app_name,
        version="0.1.0",
        docs_url="/docs" if settings.debug else None,
        redoc_url="/redoc" if settings.debug else None,
        lifespan=lifespan,
    )

    # Middleware
    app.add_middleware(PIIMaskingMiddleware)
    app.add_middleware(ObservabilityMiddleware)
    app.add_middleware(PerformanceMiddleware, slow_request_threshold=2.0)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Routers
    app.include_router(api_v1_router)
    app.include_router(auth.router, prefix="/auth", tags=["auth"])
    app.include_router(charts.router, prefix="/charts", tags=["charts"])
    app.include_router(horoscope.router)
    app.include_router(interpretations.router, prefix="/interpretations", tags=["interpretations"])
    app.include_router(alerts.router, prefix="/alerts", tags=["alerts"])
    app.include_router(admin.router, prefix="/admin", tags=["admin"])

    @app.get("/")
    async def root() -> dict[str, str | list[str]]:
        return {
            "message": settings.app_name,
            "version": "0.1.0",
            "status": "operational",
            "features": [
                "Natal chart computations",
                "RAG-augmented interpretations",
                "Observability hooks",
            ],
        }

    @app.get("/health")
    async def health_check() -> dict[str, str | float | None]:
        health_data = observability.update_system_health()
        return {
            "status": "healthy",
            "health_score": health_data.get("health_score"),
            "active_alerts": health_data.get("active_alerts"),
            "timestamp": health_data.get("timestamp"),
        }

    logger.info("Application initialised", settings=settings.describe())

    return app


app = create_app()


__all__ = ["app", "create_app"]
