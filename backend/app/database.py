"""
Get Clearance - Database Configuration
=======================================
Async PostgreSQL connection pool and session management using SQLAlchemy 2.0.

Multi-tenancy is enforced via:
1. All queries filtered by tenant_id
2. PostgreSQL Row Level Security (RLS) as defense in depth

Usage in routes:
    from app.database import get_db
    
    @router.get("/items")
    async def list_items(db: AsyncSession = Depends(get_db)):
        result = await db.execute(select(Item))
        return result.scalars().all()
"""

from typing import AsyncGenerator
from contextlib import asynccontextmanager

from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
    AsyncEngine,
)
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy import text

from app.config import settings


# ===========================================
# BASE MODEL
# ===========================================
class Base(DeclarativeBase):
    """
    Base class for all SQLAlchemy models.
    
    All models should inherit from this class.
    """
    pass


# ===========================================
# ENGINE & SESSION FACTORY
# ===========================================

# Global engine reference (initialized in lifespan)
_engine: AsyncEngine | None = None
_session_factory: async_sessionmaker[AsyncSession] | None = None


async def create_db_pool() -> None:
    """
    Initialize the database connection pool.
    
    Called during application startup.
    """
    global _engine, _session_factory
    
    _engine = create_async_engine(
        settings.database_url_async,
        echo=settings.debug,  # Log SQL in debug mode
        pool_size=settings.db_pool_size,
        max_overflow=settings.db_max_overflow,
        pool_timeout=settings.db_pool_timeout,
        pool_recycle=settings.db_pool_recycle,
        pool_pre_ping=True,  # Verify connections before use
    )
    
    _session_factory = async_sessionmaker(
        bind=_engine,
        class_=AsyncSession,
        expire_on_commit=False,
        autocommit=False,
        autoflush=False,
    )


async def close_db_pool() -> None:
    """
    Close the database connection pool.
    
    Called during application shutdown.
    """
    global _engine, _session_factory
    
    if _engine is not None:
        await _engine.dispose()
        _engine = None
        _session_factory = None


def get_engine() -> AsyncEngine:
    """Get the database engine (must be initialized first)."""
    if _engine is None:
        raise RuntimeError("Database pool not initialized. Call create_db_pool() first.")
    return _engine


def get_session_factory() -> async_sessionmaker[AsyncSession]:
    """Get the session factory (must be initialized first)."""
    if _session_factory is None:
        raise RuntimeError("Database pool not initialized. Call create_db_pool() first.")
    return _session_factory


# ===========================================
# DEPENDENCY INJECTION
# ===========================================
async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    FastAPI dependency that provides a database session.
    
    Usage:
        @router.get("/items")
        async def list_items(db: AsyncSession = Depends(get_db)):
            ...
    
    The session is automatically committed on success or rolled back on exception.
    """
    factory = get_session_factory()
    async with factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


@asynccontextmanager
async def get_db_context() -> AsyncGenerator[AsyncSession, None]:
    """
    Context manager for database sessions outside of request context.
    
    Usage in background jobs:
        async with get_db_context() as db:
            result = await db.execute(select(Item))
    """
    factory = get_session_factory()
    async with factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


# ===========================================
# MULTI-TENANT CONTEXT
# ===========================================
async def set_tenant_context(session: AsyncSession, tenant_id: str) -> None:
    """
    Set the current tenant for Row Level Security.
    
    This sets a PostgreSQL session variable that RLS policies use
    to filter queries to the current tenant's data only.
    
    Args:
        session: The database session
        tenant_id: UUID of the current tenant
    
    Example:
        async def get_db_with_tenant(
            db: AsyncSession = Depends(get_db),
            tenant: Tenant = Depends(get_current_tenant),
        ) -> AsyncGenerator[AsyncSession, None]:
            await set_tenant_context(db, str(tenant.id))
            yield db
    """
    await session.execute(
        text("SET LOCAL app.current_tenant_id = :tenant_id"),
        {"tenant_id": tenant_id},
    )


# ===========================================
# UTILITY FUNCTIONS
# ===========================================
async def check_db_connection() -> bool:
    """
    Check if database is reachable.
    
    Returns:
        bool: True if connection successful, False otherwise
    """
    try:
        engine = get_engine()
        async with engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
        return True
    except Exception:
        return False
