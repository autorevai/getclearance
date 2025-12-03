"""
Get Clearance API - Main Application
=====================================
FastAPI application entry point with middleware, routers, and lifecycle management.

Run locally:
    uvicorn app.main:app --reload --port 8000

Production:
    uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4

Features:
- Rate limiting (slowapi)
- Security headers
- Request ID tracing
- Structured JSON logging
- Sentry error tracking
- Health/readiness checks
"""

import uuid
import logging
from contextlib import asynccontextmanager
from typing import Any, AsyncGenerator

from fastapi import FastAPI, HTTPException, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import JSONResponse
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address
from sqlalchemy import text
from starlette.middleware.base import BaseHTTPMiddleware

from app.config import settings
from app.api.router import api_router
from app.database import create_db_pool, close_db_pool, get_db
from app.logging_config import (
    setup_logging,
    get_logger,
    set_request_context,
    clear_request_context,
    request_id_var,
)


# ===========================================
# SENTRY INTEGRATION
# ===========================================

def scrub_pii_from_event(event: dict[str, Any], hint: dict[str, Any]) -> dict[str, Any] | None:
    """
    Remove PII from Sentry events before sending.

    This is a Sentry before_send hook that sanitizes sensitive data.

    Args:
        event: Sentry event dictionary
        hint: Additional context about the event

    Returns:
        Sanitized event or None to drop the event
    """
    # Sensitive fields to redact
    sensitive_fields = {
        'email', 'phone', 'ssn', 'password', 'secret',
        'token', 'api_key', 'authorization', 'first_name',
        'last_name', 'address', 'date_of_birth', 'dob',
    }

    def redact_dict(d: dict[str, Any]) -> dict[str, Any]:
        """Recursively redact sensitive fields from a dictionary."""
        result = {}
        for key, value in d.items():
            lower_key = key.lower()
            if any(field in lower_key for field in sensitive_fields):
                result[key] = "[REDACTED]"
            elif isinstance(value, dict):
                result[key] = redact_dict(value)
            elif isinstance(value, list):
                result[key] = [
                    redact_dict(item) if isinstance(item, dict) else item
                    for item in value
                ]
            else:
                result[key] = value
        return result

    # Scrub request data
    if "request" in event:
        if "data" in event["request"]:
            event["request"]["data"] = redact_dict(event["request"]["data"])
        if "cookies" in event["request"]:
            event["request"]["cookies"] = "[REDACTED]"
        if "headers" in event["request"]:
            headers = event["request"]["headers"]
            if isinstance(headers, dict):
                for key in list(headers.keys()):
                    if "auth" in key.lower() or "cookie" in key.lower():
                        headers[key] = "[REDACTED]"

    # Scrub extra context
    if "extra" in event:
        event["extra"] = redact_dict(event["extra"])

    # Scrub contexts
    if "contexts" in event:
        event["contexts"] = redact_dict(event["contexts"])

    return event


def initialize_sentry() -> None:
    """
    Initialize Sentry error tracking if configured.

    Requires SENTRY_DSN environment variable to be set.
    """
    if not settings.sentry_dsn:
        return

    try:
        import sentry_sdk
        from sentry_sdk.integrations.fastapi import FastApiIntegration
        from sentry_sdk.integrations.sqlalchemy import SqlalchemyIntegration
        from sentry_sdk.integrations.logging import LoggingIntegration

        sentry_sdk.init(
            dsn=settings.sentry_dsn,
            environment=settings.environment,
            release=f"getclearance@{settings.app_version}",
            traces_sample_rate=settings.sentry_traces_sample_rate,
            profiles_sample_rate=settings.sentry_profiles_sample_rate,
            integrations=[
                FastApiIntegration(transaction_style="endpoint"),
                SqlalchemyIntegration(),
                LoggingIntegration(
                    level=logging.INFO,
                    event_level=logging.ERROR,
                ),
            ],
            before_send=scrub_pii_from_event,
            send_default_pii=False,  # Extra safety
        )
        print("   ✓ Sentry initialized")
    except ImportError:
        print("   ! Sentry SDK not installed, error tracking disabled")
    except Exception as e:
        print(f"   ! Failed to initialize Sentry: {e}")


# Initialize logging
setup_logging(
    is_production=settings.is_production(),
    log_level=settings.log_level,
)
logger = get_logger(__name__)


# ===========================================
# RATE LIMITING
# ===========================================

def get_rate_limit_key(request: Request) -> str:
    """
    Extract rate limit key from request.

    Uses authenticated user ID if available, otherwise falls back to IP.
    This provides per-user rate limiting for authenticated requests.
    """
    # Try to get user ID from request state (set by auth middleware)
    user_id = getattr(request.state, "user_id", None)
    if user_id:
        return f"user:{user_id}"

    # Fall back to IP address
    return get_remote_address(request)


# Initialize rate limiter
# Use Redis if available, otherwise fall back to in-memory storage
_storage_uri = "memory://"
if hasattr(settings, 'redis_url_str') and settings.redis_url_str:
    _storage_uri = settings.redis_url_str

limiter = Limiter(
    key_func=get_rate_limit_key,
    default_limits=["200/minute"],  # Default: 200 requests per minute
    storage_uri=_storage_uri,
)


# ===========================================
# SECURITY HEADERS MIDDLEWARE
# ===========================================

class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """
    Add security headers to all responses.

    Headers added:
    - X-Content-Type-Options: Prevent MIME sniffing
    - X-Frame-Options: Prevent clickjacking
    - X-XSS-Protection: Legacy XSS protection
    - Referrer-Policy: Control referrer information
    - Content-Security-Policy: Restrict resource loading (API only)
    - Strict-Transport-Security: Force HTTPS (production only)
    - Cache-Control: Prevent caching of sensitive data
    """

    async def dispatch(self, request: Request, call_next) -> Response:
        response = await call_next(request)

        # Prevent MIME type sniffing
        response.headers["X-Content-Type-Options"] = "nosniff"

        # Prevent clickjacking
        response.headers["X-Frame-Options"] = "DENY"

        # Legacy XSS protection (for older browsers)
        response.headers["X-XSS-Protection"] = "1; mode=block"

        # Control referrer information
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"

        # Content Security Policy for API (restrictive since we don't serve HTML)
        response.headers["Content-Security-Policy"] = "default-src 'none'; frame-ancestors 'none'"

        # HSTS - Force HTTPS in production
        if settings.is_production():
            response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"

        # Prevent caching of API responses with sensitive data
        if "/api/" in request.url.path:
            response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, private"
            response.headers["Pragma"] = "no-cache"

        return response


# ===========================================
# REQUEST ID MIDDLEWARE
# ===========================================

class RequestIDMiddleware(BaseHTTPMiddleware):
    """
    Add unique request ID to all requests for tracing.

    The request ID is:
    - Generated as UUID v4 if not provided
    - Accepted from X-Request-ID header if provided
    - Added to response headers as X-Request-ID
    - Available in request.state.request_id for logging
    - Propagated to logging context for correlation
    """

    async def dispatch(self, request: Request, call_next) -> Response:
        # Get request ID from header or generate new one
        request_id = request.headers.get("X-Request-ID")
        if not request_id:
            request_id = str(uuid.uuid4())

        # Store in request state for access in handlers
        request.state.request_id = request_id

        # Set logging context
        set_request_context(request_id=request_id)

        try:
            # Process request
            response = await call_next(request)

            # Add to response headers
            response.headers["X-Request-ID"] = request_id

            return response
        finally:
            # Clear logging context
            clear_request_context()


# ===========================================
# LIFESPAN MANAGEMENT
# ===========================================
@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """
    Manage application lifecycle.

    Startup: Initialize database pool, redis, Sentry, etc.
    Shutdown: Clean up connections gracefully.
    """
    # Startup
    logger.info(
        "Starting application",
        extra={
            "app_name": settings.app_name,
            "version": settings.app_version,
            "environment": settings.environment,
        },
    )
    print(f"🚀 Starting {settings.app_name} v{settings.app_version}")
    print(f"   Environment: {settings.environment}")
    print(f"   Debug: {settings.debug}")

    # Initialize Sentry error tracking
    initialize_sentry()

    # Initialize database connection pool
    await create_db_pool()
    print("   ✓ Database pool initialized")
    logger.info("Database pool initialized")

    # TODO: Initialize Redis connection
    # TODO: Initialize ARQ worker pool

    yield

    # Shutdown
    logger.info("Shutting down application")
    print("👋 Shutting down...")
    await close_db_pool()
    print("   ✓ Database pool closed")
    logger.info("Database pool closed")


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
    # RATE LIMITING
    # -----------------------------------------
    app.state.limiter = limiter
    app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

    # -----------------------------------------
    # MIDDLEWARE (order matters - last added runs first)
    # -----------------------------------------

    # Security headers (runs first - adds headers to all responses)
    app.add_middleware(SecurityHeadersMiddleware)

    # Request ID tracking (runs second - adds ID for tracing)
    app.add_middleware(RequestIDMiddleware)

    # CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins_list,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
        expose_headers=["X-Request-ID", "X-RateLimit-Remaining", "X-RateLimit-Limit", "X-RateLimit-Reset"],
    )

    # Gzip compression for responses > 500 bytes
    app.add_middleware(GZipMiddleware, minimum_size=500)

    # TODO: Add tenant context middleware

    # -----------------------------------------
    # EXCEPTION HANDLERS
    # -----------------------------------------
    def _get_cors_headers(request: Request) -> dict:
        """Get CORS headers for the request origin if allowed."""
        origin = request.headers.get("origin", "")
        if origin in settings.cors_origins_list:
            return {
                "Access-Control-Allow-Origin": origin,
                "Access-Control-Allow-Credentials": "true",
            }
        return {}

    @app.exception_handler(HTTPException)
    async def http_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:
        """Handle HTTP exceptions with CORS headers."""
        return JSONResponse(
            status_code=exc.status_code,
            content={"detail": exc.detail},
            headers=_get_cors_headers(request),
        )

    @app.exception_handler(Exception)
    async def global_exception_handler(request: Request, exc: Exception) -> JSONResponse:
        """Catch-all exception handler for unhandled errors."""
        # Log the error with structured logging
        logger.exception(
            f"Unhandled exception: {type(exc).__name__}",
            extra={
                "error_type": type(exc).__name__,
                "path": request.url.path,
                "method": request.method,
            },
        )

        headers = _get_cors_headers(request)

        # In production, don't expose internal error details
        if settings.is_production():
            return JSONResponse(
                status_code=500,
                content={"detail": "Internal server error"},
                headers=headers,
            )
        # In development, include error details
        return JSONResponse(
            status_code=500,
            content={
                "detail": str(exc),
                "type": type(exc).__name__,
            },
            headers=headers,
        )

    # -----------------------------------------
    # ROUTERS
    # -----------------------------------------

    # Health check (no auth required)
    @app.get("/health", tags=["Health"])
    async def health_check() -> dict:
        """
        Health check endpoint for load balancers and monitoring.

        This is a lightweight check that always returns immediately.
        Use /health/ready for dependency checks.

        Returns:
            dict: Status and version info
        """
        return {
            "status": "healthy",
            "version": settings.app_version,
            "environment": settings.environment,
        }

    @app.get("/health/ready", tags=["Health"])
    async def readiness_check() -> JSONResponse:
        """
        Readiness check - verifies all dependencies are available.

        Checks:
        - Database connectivity
        - Redis connectivity (if configured)

        Returns:
            JSONResponse: Status of each dependency with 200 or 503 status code
        """
        from app.database import async_session_maker

        checks: dict[str, str] = {}

        # Check database connectivity
        try:
            async with async_session_maker() as session:
                await session.execute(text("SELECT 1"))
                checks["database"] = "healthy"
        except Exception as e:
            checks["database"] = f"unhealthy: {str(e)[:100]}"
            logger.error(f"Database health check failed: {e}")

        # Check Redis connectivity (if configured)
        if settings.redis_url_str and settings.redis_url_str != "redis://localhost:6379/0":
            try:
                import redis.asyncio as aioredis
                client = aioredis.from_url(settings.redis_url_str)
                await client.ping()
                await client.close()
                checks["redis"] = "healthy"
            except ImportError:
                checks["redis"] = "not_configured"
            except Exception as e:
                checks["redis"] = f"unhealthy: {str(e)[:100]}"
                logger.error(f"Redis health check failed: {e}")
        else:
            checks["redis"] = "not_configured"

        # Determine overall status
        all_healthy = all(
            v == "healthy" or v == "not_configured"
            for v in checks.values()
        )

        status_code = 200 if all_healthy else 503
        status = "ready" if all_healthy else "not_ready"

        return JSONResponse(
            status_code=status_code,
            content={
                "status": status,
                "checks": checks,
                "version": settings.app_version,
            },
        )

    @app.get("/health/live", tags=["Health"])
    async def liveness_check() -> dict:
        """
        Liveness check - indicates if the application is running.

        This is an even simpler check than /health for Kubernetes liveness probes.
        If this fails, the container should be restarted.

        Returns:
            dict: Simple alive status
        """
        return {"status": "alive"}

    # Debug endpoint - only available in development
    if settings.is_development():
        @app.get("/debug/auth-config", tags=["Debug"])
        async def debug_auth_config() -> dict:
            """Debug endpoint to check Auth0 configuration (no secrets exposed)."""
            return {
                "auth0_domain_set": bool(settings.auth0_domain),
                "auth0_domain": settings.auth0_domain if settings.auth0_domain else "NOT SET",
                "auth0_audience": settings.auth0_audience,
                "auth0_issuer": settings.auth0_issuer,
                "cors_origins": settings.cors_origins_list,
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
