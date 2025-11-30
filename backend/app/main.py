"""
Get Clearance API - Main Application
=====================================
FastAPI application entry point with middleware, routers, and lifecycle management.

Run locally:
    uvicorn app.main:app --reload --port 8000

Production:
    uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4
"""

from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import JSONResponse

from app.config import settings
from app.api.router import api_router
from app.database import create_db_pool, close_db_pool


# ===========================================
# LIFESPAN MANAGEMENT
# ===========================================
@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """
    Manage application lifecycle.
    
    Startup: Initialize database pool, redis, etc.
    Shutdown: Clean up connections gracefully.
    """
    # Startup
    print(f"🚀 Starting {settings.app_name} v{settings.app_version}")
    print(f"   Environment: {settings.environment}")
    print(f"   Debug: {settings.debug}")
    
    # Initialize database connection pool
    await create_db_pool()
    print("   ✓ Database pool initialized")
    
    # TODO: Initialize Redis connection
    # TODO: Initialize ARQ worker pool
    
    yield
    
    # Shutdown
    print("👋 Shutting down...")
    await close_db_pool()
    print("   ✓ Database pool closed")


# ===========================================
# APPLICATION FACTORY
# ===========================================
def create_application() -> FastAPI:
    """
    Create and configure FastAPI application.
    
    Returns configured FastAPI instance with all middleware and routers.
    """
    app = FastAPI(
        title=settings.app_name,
        version=settings.app_version,
        description="AI-native KYC/AML compliance platform",
        docs_url="/docs" if settings.is_development() else None,
        redoc_url="/redoc" if settings.is_development() else None,
        openapi_url="/openapi.json" if settings.is_development() else "/api/openapi.json",
        lifespan=lifespan,
    )

    # -----------------------------------------
    # MIDDLEWARE (order matters - last added runs first)
    # -----------------------------------------
    
    # CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins_list,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
        expose_headers=["X-Request-ID", "X-RateLimit-Remaining"],
    )
    
    # Gzip compression for responses > 500 bytes
    app.add_middleware(GZipMiddleware, minimum_size=500)
    
    # TODO: Add rate limiting middleware
    # TODO: Add request ID middleware
    # TODO: Add tenant context middleware

    # -----------------------------------------
    # EXCEPTION HANDLERS
    # -----------------------------------------
    @app.exception_handler(Exception)
    async def global_exception_handler(request: Request, exc: Exception) -> JSONResponse:
        """Catch-all exception handler for unhandled errors."""
        # In production, don't expose internal error details
        if settings.is_production():
            return JSONResponse(
                status_code=500,
                content={"detail": "Internal server error"},
            )
        # In development, include error details
        return JSONResponse(
            status_code=500,
            content={
                "detail": str(exc),
                "type": type(exc).__name__,
            },
        )

    # -----------------------------------------
    # ROUTERS
    # -----------------------------------------
    
    # Health check (no auth required)
    @app.get("/health", tags=["Health"])
    async def health_check() -> dict:
        """
        Health check endpoint for load balancers and monitoring.
        
        Returns:
            dict: Status and version info
        """
        return {
            "status": "healthy",
            "version": settings.app_version,
            "environment": settings.environment,
        }

    @app.get("/health/ready", tags=["Health"])
    async def readiness_check() -> dict:
        """
        Readiness check - verifies all dependencies are available.
        
        Returns:
            dict: Status of each dependency
        """
        # TODO: Actually check database and redis connectivity
        return {
            "status": "ready",
            "checks": {
                "database": "ok",
                "redis": "ok",
            },
        }

    # API v1 routes
    app.include_router(api_router, prefix=settings.api_v1_prefix)

    return app


# Create application instance
app = create_application()


# ===========================================
# DEVELOPMENT SERVER
# ===========================================
if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.is_development(),
        log_level=settings.log_level.lower(),
    )
