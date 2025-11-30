"""
Get Clearance - Configuration
=============================
All settings loaded from environment variables with sensible defaults.
Uses pydantic-settings for validation and type coercion.

Environment variables can be set in:
- .env file (local development)
- Railway/Render dashboard (production)
- docker-compose.yml (containerized development)
"""

from functools import lru_cache
from typing import Literal

from pydantic import Field, PostgresDsn, RedisDsn, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings with environment variable binding."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # ===========================================
    # APPLICATION
    # ===========================================
    app_name: str = "Get Clearance API"
    app_version: str = "0.1.0"
    environment: Literal["development", "staging", "production"] = "development"
    debug: bool = Field(default=False)
    log_level: str = Field(default="INFO")

    # API versioning
    api_v1_prefix: str = "/api/v1"

    # CORS - comma-separated origins
    cors_origins: str = Field(
        default="http://localhost:3000,http://localhost:9000,https://getclearance.vercel.app"
    )

    @property
    def cors_origins_list(self) -> list[str]:
        """Parse CORS origins string into list."""
        return [origin.strip() for origin in self.cors_origins.split(",")]

    # ===========================================
    # DATABASE (PostgreSQL)
    # ===========================================
    database_url: PostgresDsn = Field(
        default="postgresql+asyncpg://postgres:postgres@localhost:5432/getclearance"
    )

    # Connection pool settings
    db_pool_size: int = Field(default=10, ge=1, le=100)
    db_max_overflow: int = Field(default=20, ge=0, le=100)
    db_pool_timeout: int = Field(default=30, ge=1)
    db_pool_recycle: int = Field(default=1800, ge=60)  # 30 minutes

    @property
    def database_url_async(self) -> str:
        """Get async database URL with asyncpg driver."""
        url = str(self.database_url)
        # Ensure asyncpg driver is used
        if "+asyncpg" not in url:
            url = url.replace("postgresql://", "postgresql+asyncpg://")
        return url

    @property
    def database_url_sync(self) -> str:
        """Get sync database URL for Alembic migrations."""
        url = str(self.database_url)
        # Remove async driver for sync operations
        return url.replace("+asyncpg", "")

    # ===========================================
    # REDIS (Cache + Queue)
    # ===========================================
    redis_url: RedisDsn = Field(default="redis://localhost:6379/0")

    @property
    def redis_url_str(self) -> str:
        """Get Redis URL as string for libraries that need it."""
        return str(self.redis_url)

    # ===========================================
    # AUTH0
    # ===========================================
    auth0_domain: str = Field(default="")
    auth0_client_id: str = Field(default="")
    auth0_client_secret: str = Field(default="", repr=False)
    auth0_audience: str = Field(default="https://api.getclearance.com")
    auth0_algorithms: list[str] = Field(default=["RS256"])

    @property
    def auth0_issuer(self) -> str:
        """Get Auth0 issuer URL."""
        return f"https://{self.auth0_domain}/"

    @property
    def auth0_jwks_url(self) -> str:
        """Get Auth0 JWKS URL for token verification."""
        return f"https://{self.auth0_domain}/.well-known/jwks.json"

    # ===========================================
    # CLOUDFLARE R2 (Document Storage)
    # ===========================================
    r2_access_key_id: str = Field(default="", repr=False)
    r2_secret_access_key: str = Field(default="", repr=False)
    r2_bucket: str = Field(default="getclearance-docs")
    r2_endpoint: str = Field(default="")
    r2_public_url: str = Field(default="")  # Optional CDN URL

    # Presigned URL expiration (seconds)
    r2_upload_url_expires: int = Field(default=3600)  # 1 hour
    r2_download_url_expires: int = Field(default=3600)  # 1 hour

    # ===========================================
    # CLAUDE AI (Anthropic)
    # ===========================================
    anthropic_api_key: str = Field(default="", repr=False)
    anthropic_model: str = Field(default="claude-sonnet-4-20250514")
    anthropic_max_tokens: int = Field(default=4096)

    # ===========================================
    # OPENSANCTIONS
    # ===========================================
    opensanctions_api_key: str = Field(default="", repr=False)
    opensanctions_api_url: str = Field(
        default="https://api.opensanctions.org/match/default"
    )

    # ===========================================
    # SECURITY
    # ===========================================
    # Secret key for signing (generate with: openssl rand -hex 32)
    secret_key: str = Field(default="CHANGE-ME-IN-PRODUCTION", repr=False)

    # Rate limiting
    rate_limit_requests: int = Field(default=100)
    rate_limit_window: int = Field(default=60)  # seconds

    # ===========================================
    # FEATURE FLAGS
    # ===========================================
    feature_ai_summaries: bool = Field(default=True)
    feature_ongoing_monitoring: bool = Field(default=False)
    feature_batch_review: bool = Field(default=True)

    # ===========================================
    # VALIDATION
    # ===========================================
    @field_validator("environment")
    @classmethod
    def validate_environment(cls, v: str) -> str:
        """Ensure valid environment."""
        valid = {"development", "staging", "production"}
        if v not in valid:
            raise ValueError(f"environment must be one of {valid}")
        return v

    def is_production(self) -> bool:
        """Check if running in production."""
        return self.environment == "production"

    def is_development(self) -> bool:
        """Check if running in development."""
        return self.environment == "development"


@lru_cache
def get_settings() -> Settings:
    """
    Get cached settings instance.
    
    Uses lru_cache to ensure settings are only loaded once.
    Call get_settings.cache_clear() if you need to reload.
    """
    return Settings()


# Convenience export
settings = get_settings()
