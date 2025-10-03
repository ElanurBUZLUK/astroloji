"""
FastAPI main application factory
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from app.api import auth, charts, interpretations, alerts, admin
from app.api.v1 import api_router as api_v1_router
from app.config import settings
from app.middleware.observability import ObservabilityMiddleware, PerformanceMiddleware
from app.evaluation.observability import observability

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events"""
    # Startup
    print("🚀 Starting Astro-AA API...")
    print("📊 Observability system initialized")
    
    # Update initial system health
    observability.update_system_health()
    
    yield
    
    # Shutdown
    print("🛑 Shutting down Astro-AA API...")

def create_app() -> FastAPI:
    """Create FastAPI application with middleware and routers"""
    
    app = FastAPI(
        title="Astro-AA API",
        description="AI Astrolog - Almuten-centric astrology interpretation engine",
        version="0.1.0",
        docs_url="/docs" if settings.DEBUG else None,
        redoc_url="/redoc" if settings.DEBUG else None,
        lifespan=lifespan,
    )
    
    # Add observability middleware
    app.add_middleware(ObservabilityMiddleware)
    app.add_middleware(PerformanceMiddleware, slow_request_threshold=2.0)
    
    # CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.ALLOWED_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # Include routers
    app.include_router(api_v1_router)
    app.include_router(auth.router, prefix="/auth", tags=["auth"])
    app.include_router(charts.router, prefix="/charts", tags=["charts"])
    app.include_router(interpretations.router, prefix="/interpretations", tags=["interpretations"])
    app.include_router(alerts.router, prefix="/alerts", tags=["alerts"])
    app.include_router(admin.router, prefix="/admin", tags=["admin"])
    
    @app.get("/")
    async def root():
        return {
            "message": "Astro-AA API", 
            "version": "0.1.0",
            "status": "operational",
            "features": [
                "Almuten-centric calculations",
                "Zodiacal Releasing",
                "RAG-augmented interpretations",
                "Real-time observability"
            ]
        }
    
    @app.get("/health")
    async def health_check():
        health_data = observability.update_system_health()
        return {
            "status": "healthy",
            "health_score": health_data["health_score"],
            "active_alerts": health_data["active_alerts"],
            "timestamp": health_data.get("timestamp")
        }
    
    return app

app = create_app()
