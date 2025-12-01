# SignalWeave Technical Implementation Guide

**Purpose:** Practical, copy-paste ready patterns and configurations for implementing SignalWeave features. This complements ENGINEERING_CONTEXT.md with concrete implementation details.

---

## Table of Contents

1. [Infrastructure & Deployment (Railway)](#infrastructure--deployment-railway)
2. [Database Setup & Patterns](#database-setup--patterns)
3. [Backend Implementation Patterns](#backend-implementation-patterns)
4. [Frontend Implementation Patterns](#frontend-implementation-patterns)
5. [Third-Party Integrations](#third-party-integrations)
6. [Development Environment Setup](#development-environment-setup)
7. [Pre-Researched Documentation Links](#pre-researched-documentation-links)

---

## Infrastructure & Deployment (Railway)

### Railway Overview

**Railway Docs:** https://docs.railway.app/

We use Railway for:
- PostgreSQL database hosting
- Redis hosting
- FastAPI backend deployment
- Environment variable management
- Automatic deployments from GitHub

### Railway Project Structure

```
SignalWeave (Project)
├─ postgres (Service)
├─ redis (Service)
├─ backend-api (Service - FastAPI)
└─ worker (Service - ARQ background workers)
```

### Railway Environment Variables

**Required Environment Variables:**

```bash
# Database (Railway auto-injects these)
DATABASE_URL=postgresql://user:pass@host:port/dbname
DATABASE_PRIVATE_URL=postgresql://user:pass@internal-host:port/dbname

# Redis (Railway auto-injects these)
REDIS_URL=redis://user:pass@host:port
REDIS_PRIVATE_URL=redis://user:pass@internal-host:port

# Application Settings
APP_ENV=production|staging|development
SECRET_KEY=your-secret-key-here
ALLOWED_ORIGINS=https://app.signalweave.com,https://staging.signalweave.com

# Claude API
ANTHROPIC_API_KEY=sk-ant-...

# Storage (Cloudflare R2)
R2_ACCOUNT_ID=your-account-id
R2_ACCESS_KEY_ID=your-access-key
R2_SECRET_ACCESS_KEY=your-secret-key
R2_BUCKET_NAME=signalweave-documents
R2_PUBLIC_URL=https://documents.signalweave.com

# OCR Services
AWS_ACCESS_KEY_ID=your-aws-key
AWS_SECRET_ACCESS_KEY=your-aws-secret
AWS_REGION=us-east-1
GOOGLE_CLOUD_PROJECT_ID=your-gcp-project
GOOGLE_APPLICATION_CREDENTIALS=/app/gcp-credentials.json

# Screening Services
OPENSANCTIONS_API_KEY=your-opensanctions-key

# Webhooks
WEBHOOK_SECRET=your-webhook-signing-secret

# Monitoring
SENTRY_DSN=https://...@sentry.io/...
```

### Railway Deployment Configuration

**railway.json:**
```json
{
  "$schema": "https://railway.app/railway.schema.json",
  "build": {
    "builder": "NIXPACKS",
    "buildCommand": "pip install -r requirements.txt"
  },
  "deploy": {
    "startCommand": "uvicorn app.main:app --host 0.0.0.0 --port $PORT",
    "healthcheckPath": "/health",
    "healthcheckTimeout": 100,
    "restartPolicyType": "ON_FAILURE",
    "restartPolicyMaxRetries": 10
  }
}
```

**For Worker Service:**
```json
{
  "deploy": {
    "startCommand": "arq app.worker.WorkerSettings",
    "restartPolicyType": "ALWAYS"
  }
}
```

### Railway Database Connection Pattern

**DO NOT use DATABASE_URL directly** - Railway's DATABASE_URL uses query params that break with SQLAlchemy 2.0+

**Use this pattern:**

```python
# app/core/database.py
import os
from urllib.parse import urlparse, parse_qs

def get_database_url() -> str:
    """
    Railway's DATABASE_URL includes query params that break SQLAlchemy 2.0+
    We need to use DATABASE_PRIVATE_URL for internal connections
    and strip/rebuild the connection string properly.
    """
    railway_url = os.getenv("DATABASE_PRIVATE_URL") or os.getenv("DATABASE_URL")
    
    if not railway_url:
        raise ValueError("No database URL configured")
    
    # Parse the URL
    parsed = urlparse(railway_url)
    
    # Rebuild without query params (Railway adds ?sslmode=require)
    # SQLAlchemy 2.0+ wants this as a connection arg instead
    clean_url = f"postgresql+asyncpg://{parsed.username}:{parsed.password}@{parsed.hostname}:{parsed.port}{parsed.path}"
    
    return clean_url

# Connection pool configuration
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

engine = create_async_engine(
    get_database_url(),
    echo=False,
    pool_size=10,
    max_overflow=20,
    pool_pre_ping=True,  # Verify connections before using
    pool_recycle=3600,   # Recycle connections after 1 hour
    connect_args={
        "ssl": "require",
        "server_settings": {
            "application_name": "signalweave-api"
        }
    }
)

async_session_maker = sessionmaker(
    engine, 
    class_=AsyncSession, 
    expire_on_commit=False
)

async def get_db() -> AsyncSession:
    """FastAPI dependency for database sessions."""
    async with async_session_maker() as session:
        yield session
```

### Railway Redis Connection Pattern

```python
# app/core/redis.py
import os
from redis.asyncio import Redis, ConnectionPool

def get_redis_url() -> str:
    """Use REDIS_PRIVATE_URL for internal connections."""
    return os.getenv("REDIS_PRIVATE_URL") or os.getenv("REDIS_URL")

# Create connection pool
redis_pool = ConnectionPool.from_url(
    get_redis_url(),
    max_connections=50,
    decode_responses=True,
    socket_connect_timeout=5,
    socket_keepalive=True
)

async def get_redis() -> Redis:
    """FastAPI dependency for Redis connections."""
    return Redis(connection_pool=redis_pool)
```

---

## Database Setup & Patterns

### Database Migration Tool: Alembic

**Alembic Docs:** https://alembic.sqlalchemy.org/

**Installation:**
```bash
pip install alembic asyncpg
```

**Initialize Alembic:**
```bash
alembic init alembic
```

**alembic.ini configuration:**
```ini
[alembic]
script_location = alembic
sqlalchemy.url = # Leave empty - we'll set this in env.py

[loggers]
keys = root,sqlalchemy,alembic

[handlers]
keys = console

[formatters]
keys = generic

[logger_root]
level = WARN
handlers = console
qualname =

[logger_sqlalchemy]
level = WARN
handlers =
qualname = sqlalchemy.engine

[logger_alembic]
level = INFO
handlers =
qualname = alembic

[handler_console]
class = StreamHandler
args = (sys.stderr,)
level = NOTSET
formatter = generic

[formatter_generic]
format = %(levelname)-5.5s [%(name)s] %(message)s
datefmt = %H:%M:%S
```

**alembic/env.py (for Railway):**
```python
from logging.config import fileConfig
from sqlalchemy import engine_from_config
from sqlalchemy import pool
from alembic import context
import os
import sys
from pathlib import Path

# Add project root to path
sys.path.append(str(Path(__file__).parent.parent))

# Import your models
from app.models import Base

# this is the Alembic Config object
config = context.config

# Interpret the config file for Python logging.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata

def get_url():
    """Get database URL from environment (Railway-compatible)."""
    from app.core.database import get_database_url
    # Use sync driver for migrations
    return get_database_url().replace("+asyncpg", "")

def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode."""
    url = get_url()
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()

def run_migrations_online() -> None:
    """Run migrations in 'online' mode."""
    configuration = config.get_section(config.config_ini_section)
    configuration["sqlalchemy.url"] = get_url()
    
    connectable = engine_from_config(
        configuration,
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection, 
            target_metadata=target_metadata
        )

        with context.begin_transaction():
            context.run_migrations()

if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
```

**Create initial migration:**
```bash
# Generate migration from models
alembic revision --autogenerate -m "Initial schema"

# Review the generated migration in alembic/versions/

# Apply migration
alembic upgrade head
```

**Run migrations on Railway:**
Add to your build command in railway.json:
```json
{
  "build": {
    "buildCommand": "pip install -r requirements.txt && alembic upgrade head"
  }
}
```

### Row Level Security (RLS) Implementation

**Critical:** Every tenant table MUST have RLS enabled.

**Migration template for RLS tables:**

```python
# alembic/versions/xxx_add_applicants_table.py

def upgrade() -> None:
    # Create table
    op.create_table(
        'applicants',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('tenant_id', sa.String(36), nullable=False),
        sa.Column('full_name', sa.String(255), nullable=False),
        sa.Column('email', sa.String(255)),
        sa.Column('date_of_birth', sa.Date()),
        sa.Column('status', sa.String(50), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()')),
        # ... other columns
    )
    
    # Create indexes
    op.create_index('idx_applicants_tenant_id', 'applicants', ['tenant_id'])
    op.create_index('idx_applicants_status', 'applicants', ['status'])
    op.create_index('idx_applicants_created_at', 'applicants', ['created_at'])
    
    # Enable RLS
    op.execute("ALTER TABLE applicants ENABLE ROW LEVEL SECURITY")
    
    # Create RLS policy
    op.execute("""
        CREATE POLICY tenant_isolation_policy ON applicants
        USING (tenant_id = current_setting('app.current_tenant_id')::text)
        WITH CHECK (tenant_id = current_setting('app.current_tenant_id')::text)
    """)
    
    # Create trigger for updated_at
    op.execute("""
        CREATE TRIGGER update_applicants_updated_at
        BEFORE UPDATE ON applicants
        FOR EACH ROW
        EXECUTE FUNCTION update_updated_at_column()
    """)

def downgrade() -> None:
    op.drop_table('applicants')
```

**updated_at trigger function (create once in initial migration):**

```python
def upgrade() -> None:
    # Create updated_at trigger function
    op.execute("""
        CREATE OR REPLACE FUNCTION update_updated_at_column()
        RETURNS TRIGGER AS $$
        BEGIN
            NEW.updated_at = now();
            RETURN NEW;
        END;
        $$ language 'plpgsql';
    """)
```

### Setting Tenant Context in FastAPI

**app/core/dependencies.py:**

```python
from fastapi import Depends, HTTPException, Header
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.models.tenant import Tenant
import jwt
import os

async def get_current_tenant(
    authorization: str = Header(...),
    db: AsyncSession = Depends(get_db)
) -> Tenant:
    """
    Extract tenant from JWT token and set PostgreSQL session variable.
    All subsequent queries in this request will be scoped to this tenant.
    """
    try:
        # Extract token
        scheme, token = authorization.split()
        if scheme.lower() != 'bearer':
            raise HTTPException(status_code=401, detail="Invalid authentication scheme")
        
        # Decode JWT
        payload = jwt.decode(token, os.getenv("SECRET_KEY"), algorithms=["HS256"])
        tenant_id = payload.get("tenant_id")
        
        if not tenant_id:
            raise HTTPException(status_code=401, detail="Invalid token: missing tenant_id")
        
        # Set PostgreSQL session variable for RLS
        await db.execute(
            "SET LOCAL app.current_tenant_id = :tenant_id",
            {"tenant_id": tenant_id}
        )
        
        # Fetch tenant object (this query is NOT scoped by RLS since tenants table has no RLS)
        result = await db.execute(
            "SELECT * FROM tenants WHERE id = :tenant_id",
            {"tenant_id": tenant_id}
        )
        tenant = result.fetchone()
        
        if not tenant:
            raise HTTPException(status_code=404, detail="Tenant not found")
        
        return Tenant(**dict(tenant))
        
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")
    except ValueError:
        raise HTTPException(status_code=401, detail="Invalid authorization header")
```

**Usage in routes:**

```python
from fastapi import APIRouter, Depends
from app.core.dependencies import get_current_tenant, get_db

router = APIRouter()

@router.get("/applicants")
async def list_applicants(
    tenant: Tenant = Depends(get_current_tenant),  # Sets RLS context
    db: AsyncSession = Depends(get_db)
):
    # This query is automatically scoped to tenant via RLS
    result = await db.execute("SELECT * FROM applicants")
    applicants = result.fetchall()
    return {"applicants": [dict(a) for a in applicants]}
```

### Full-Text Search Pattern

**Create GIN index for full-text search:**

```python
# Migration
def upgrade() -> None:
    # Add tsvector column
    op.add_column(
        'applicants',
        sa.Column('search_vector', sa.dialects.postgresql.TSVECTOR)
    )
    
    # Create GIN index
    op.create_index(
        'idx_applicants_search',
        'applicants',
        ['search_vector'],
        postgresql_using='gin'
    )
    
    # Create trigger to update search_vector
    op.execute("""
        CREATE TRIGGER applicants_search_vector_update
        BEFORE INSERT OR UPDATE ON applicants
        FOR EACH ROW EXECUTE FUNCTION
        tsvector_update_trigger(
            search_vector, 'pg_catalog.english',
            full_name, email, phone
        );
    """)
    
    # Populate existing rows
    op.execute("""
        UPDATE applicants
        SET search_vector = to_tsvector('english', 
            coalesce(full_name, '') || ' ' ||
            coalesce(email, '') || ' ' ||
            coalesce(phone, '')
        );
    """)
```

**Query pattern:**

```python
async def search_applicants(
    query: str,
    db: AsyncSession = Depends(get_db),
    tenant: Tenant = Depends(get_current_tenant)
):
    """Search applicants with full-text search."""
    result = await db.execute(
        """
        SELECT *, ts_rank(search_vector, plainto_tsquery('english', :query)) as rank
        FROM applicants
        WHERE search_vector @@ plainto_tsquery('english', :query)
        ORDER BY rank DESC
        LIMIT 50
        """,
        {"query": query}
    )
    return result.fetchall()
```

### Trigram Matching for Fuzzy Name Search (Screening)

**Enable pg_trgm extension (run once):**

```python
# Migration
def upgrade() -> None:
    op.execute("CREATE EXTENSION IF NOT EXISTS pg_trgm")
```

**Create trigram index:**

```python
def upgrade() -> None:
    op.create_index(
        'idx_screening_entities_name_trgm',
        'screening_entities',
        ['name'],
        postgresql_using='gin',
        postgresql_ops={'name': 'gin_trgm_ops'}
    )
```

**Fuzzy matching query:**

```python
async def fuzzy_match_entity(
    name: str,
    threshold: float = 0.3,
    db: AsyncSession = Depends(get_db)
):
    """
    Find entities with similar names using trigram similarity.
    threshold: 0.0 (no match) to 1.0 (exact match)
    """
    result = await db.execute(
        """
        SELECT *, similarity(name, :name) as sim
        FROM screening_entities
        WHERE similarity(name, :name) > :threshold
        ORDER BY sim DESC
        LIMIT 20
        """,
        {"name": name, "threshold": threshold}
    )
    return result.fetchall()
```

---

## Backend Implementation Patterns

### Project Structure

```
backend/
├── app/
│   ├── __init__.py
│   ├── main.py                 # FastAPI app initialization
│   ├── core/
│   │   ├── __init__.py
│   │   ├── config.py           # Settings/env vars
│   │   ├── database.py         # DB connection
│   │   ├── redis.py            # Redis connection
│   │   ├── dependencies.py     # Shared dependencies
│   │   └── security.py         # JWT, hashing
│   ├── models/
│   │   ├── __init__.py
│   │   ├── base.py             # SQLAlchemy Base
│   │   ├── tenant.py
│   │   ├── applicant.py
│   │   ├── document.py
│   │   ├── screening.py
│   │   └── ...
│   ├── schemas/
│   │   ├── __init__.py
│   │   ├── applicant.py        # Pydantic models
│   │   ├── document.py
│   │   └── ...
│   ├── routers/
│   │   ├── __init__.py
│   │   ├── applicants.py
│   │   ├── documents.py
│   │   ├── screening.py
│   │   ├── cases.py
│   │   └── ...
│   ├── services/
│   │   ├── __init__.py
│   │   ├── ocr_service.py
│   │   ├── screening_service.py
│   │   ├── ai_service.py       # Claude API calls
│   │   └── ...
│   ├── worker/
│   │   ├── __init__.py
│   │   ├── settings.py         # ARQ worker config
│   │   ├── tasks.py            # Background tasks
│   │   └── ...
│   └── utils/
│       ├── __init__.py
│       ├── audit_log.py
│       ├── evidence_export.py
│       └── ...
├── alembic/
│   └── versions/
├── tests/
├── requirements.txt
├── railway.json
└── .env.example
```

### FastAPI App Initialization (app/main.py)

```python
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.routers import applicants, documents, screening, cases
import sentry_sdk

# Initialize Sentry for error tracking
if settings.SENTRY_DSN:
    sentry_sdk.init(
        dsn=settings.SENTRY_DSN,
        environment=settings.APP_ENV,
        traces_sample_rate=0.1,
    )

app = FastAPI(
    title="SignalWeave API",
    description="AI-native KYC/AML compliance platform",
    version="1.0.0",
    docs_url="/docs" if settings.APP_ENV != "production" else None,
    redoc_url="/redoc" if settings.APP_ENV != "production" else None,
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS.split(","),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(applicants.router, prefix="/v1/applicants", tags=["Applicants"])
app.include_router(documents.router, prefix="/v1/documents", tags=["Documents"])
app.include_router(screening.router, prefix="/v1/screening", tags=["Screening"])
app.include_router(cases.router, prefix="/v1/cases", tags=["Cases"])

@app.get("/health")
async def health_check():
    """Railway health check endpoint."""
    return {"status": "healthy"}

@app.on_event("startup")
async def startup_event():
    """Initialize connections on startup."""
    # Could initialize connection pools here if needed
    pass

@app.on_event("shutdown")
async def shutdown_event():
    """Clean up connections on shutdown."""
    # Close database connection pools, etc.
    pass
```

### Configuration Management (app/core/config.py)

```python
from pydantic_settings import BaseSettings
from functools import lru_cache

class Settings(BaseSettings):
    # App
    APP_ENV: str = "development"
    SECRET_KEY: str
    ALLOWED_ORIGINS: str = "http://localhost:3000"
    
    # Database (Railway injects these)
    DATABASE_URL: str
    DATABASE_PRIVATE_URL: str | None = None
    
    # Redis
    REDIS_URL: str
    REDIS_PRIVATE_URL: str | None = None
    
    # Claude API
    ANTHROPIC_API_KEY: str
    
    # Storage (R2)
    R2_ACCOUNT_ID: str
    R2_ACCESS_KEY_ID: str
    R2_SECRET_ACCESS_KEY: str
    R2_BUCKET_NAME: str
    R2_PUBLIC_URL: str
    
    # OCR
    AWS_ACCESS_KEY_ID: str
    AWS_SECRET_ACCESS_KEY: str
    AWS_REGION: str = "us-east-1"
    
    # Screening
    OPENSANCTIONS_API_KEY: str
    
    # Monitoring
    SENTRY_DSN: str | None = None
    
    class Config:
        env_file = ".env"
        case_sensitive = True

@lru_cache()
def get_settings() -> Settings:
    """Cached settings instance."""
    return Settings()

settings = get_settings()
```

### SQLAlchemy Models Pattern

**app/models/base.py:**

```python
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, DateTime, func

Base = declarative_base()

class TimestampMixin:
    """Mixin for created_at and updated_at columns."""
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
```

**app/models/applicant.py:**

```python
from sqlalchemy import Column, String, Date, JSON, Index
from sqlalchemy.dialects.postgresql import TSVECTOR
from app.models.base import Base, TimestampMixin
import uuid

class Applicant(Base, TimestampMixin):
    __tablename__ = 'applicants'
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    tenant_id = Column(String(36), nullable=False, index=True)
    
    # Personal information
    full_name = Column(String(255), nullable=False)
    email = Column(String(255))
    phone = Column(String(50))
    date_of_birth = Column(Date())
    
    # Status
    status = Column(String(50), nullable=False, default='pending', index=True)
    
    # JSONB fields
    verification_checks = Column(JSON, default=dict)
    risk_factors = Column(JSON, default=list)
    
    # Full-text search
    search_vector = Column(TSVECTOR)
    
    # Indexes
    __table_args__ = (
        Index('idx_applicants_search', 'search_vector', postgresql_using='gin'),
        Index('idx_applicants_tenant_status', 'tenant_id', 'status'),
    )
```

### Pydantic Schemas Pattern

**app/schemas/applicant.py:**

```python
from pydantic import BaseModel, EmailStr, Field
from datetime import date, datetime
from typing import Optional

class ApplicantBase(BaseModel):
    full_name: str = Field(..., min_length=1, max_length=255)
    email: Optional[EmailStr] = None
    phone: Optional[str] = Field(None, max_length=50)
    date_of_birth: Optional[date] = None

class ApplicantCreate(ApplicantBase):
    """Request schema for creating an applicant."""
    pass

class ApplicantUpdate(BaseModel):
    """Request schema for updating an applicant."""
    full_name: Optional[str] = Field(None, min_length=1, max_length=255)
    email: Optional[EmailStr] = None
    phone: Optional[str] = Field(None, max_length=50)
    date_of_birth: Optional[date] = None

class ApplicantResponse(ApplicantBase):
    """Response schema for applicant data."""
    id: str
    tenant_id: str
    status: str
    verification_checks: dict
    risk_factors: list
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True  # For SQLAlchemy models
```

### Router Pattern with Dependency Injection

**app/routers/applicants.py:**

```python
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.core.dependencies import get_current_tenant, get_db
from app.models.tenant import Tenant
from app.models.applicant import Applicant
from app.schemas.applicant import ApplicantCreate, ApplicantResponse, ApplicantUpdate
from app.utils.audit_log import create_audit_log
import uuid

router = APIRouter()

@router.post("", response_model=ApplicantResponse, status_code=status.HTTP_201_CREATED)
async def create_applicant(
    applicant_data: ApplicantCreate,
    tenant: Tenant = Depends(get_current_tenant),  # Sets RLS context
    db: AsyncSession = Depends(get_db)
):
    """Create a new applicant."""
    
    # Create applicant
    applicant = Applicant(
        id=str(uuid.uuid4()),
        tenant_id=tenant.id,
        **applicant_data.model_dump()
    )
    
    db.add(applicant)
    await db.commit()
    await db.refresh(applicant)
    
    # Create audit log
    await create_audit_log(
        db=db,
        tenant_id=tenant.id,
        entity_type="applicant",
        entity_id=applicant.id,
        action="created",
        actor_id=tenant.id,  # Or get from JWT
        new_value=applicant_data.model_dump()
    )
    
    return applicant

@router.get("/{applicant_id}", response_model=ApplicantResponse)
async def get_applicant(
    applicant_id: str,
    tenant: Tenant = Depends(get_current_tenant),
    db: AsyncSession = Depends(get_db)
):
    """Get applicant by ID. RLS ensures tenant isolation."""
    
    result = await db.execute(
        select(Applicant).where(Applicant.id == applicant_id)
    )
    applicant = result.scalar_one_or_none()
    
    if not applicant:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Applicant not found"
        )
    
    return applicant

@router.get("", response_model=list[ApplicantResponse])
async def list_applicants(
    status_filter: Optional[str] = None,
    limit: int = 50,
    offset: int = 0,
    tenant: Tenant = Depends(get_current_tenant),
    db: AsyncSession = Depends(get_db)
):
    """List applicants with optional filtering."""
    
    query = select(Applicant)
    
    if status_filter:
        query = query.where(Applicant.status == status_filter)
    
    query = query.limit(limit).offset(offset).order_by(Applicant.created_at.desc())
    
    result = await db.execute(query)
    applicants = result.scalars().all()
    
    return applicants

@router.patch("/{applicant_id}", response_model=ApplicantResponse)
async def update_applicant(
    applicant_id: str,
    update_data: ApplicantUpdate,
    tenant: Tenant = Depends(get_current_tenant),
    db: AsyncSession = Depends(get_db)
):
    """Update applicant. RLS ensures tenant isolation."""
    
    # Fetch existing
    result = await db.execute(
        select(Applicant).where(Applicant.id == applicant_id)
    )
    applicant = result.scalar_one_or_none()
    
    if not applicant:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Applicant not found"
        )
    
    # Store old values for audit
    old_values = {
        "full_name": applicant.full_name,
        "email": applicant.email,
        "phone": applicant.phone,
        "date_of_birth": applicant.date_of_birth
    }
    
    # Update fields
    update_dict = update_data.model_dump(exclude_unset=True)
    for field, value in update_dict.items():
        setattr(applicant, field, value)
    
    await db.commit()
    await db.refresh(applicant)
    
    # Audit log
    await create_audit_log(
        db=db,
        tenant_id=tenant.id,
        entity_type="applicant",
        entity_id=applicant.id,
        action="updated",
        actor_id=tenant.id,
        old_value=old_values,
        new_value=update_dict
    )
    
    return applicant
```

---

## Frontend Implementation Patterns

### Environment Variables (.env.local)

```bash
# API
NEXT_PUBLIC_API_URL=http://localhost:8000
NEXT_PUBLIC_WS_URL=ws://localhost:8000

# Auth
NEXT_PUBLIC_AUTH_DOMAIN=signalweave.auth0.com
NEXT_PUBLIC_AUTH_CLIENT_ID=your-client-id

# Feature Flags
NEXT_PUBLIC_ENABLE_AI_FEATURES=true
```

### API Client Setup (lib/api.ts)

```typescript
import axios from 'axios';

const api = axios.create({
  baseURL: process.env.NEXT_PUBLIC_API_URL,
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request interceptor to add auth token
api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('auth_token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => Promise.reject(error)
);

// Response interceptor for error handling
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      // Redirect to login
      window.location.href = '/login';
    }
    return Promise.reject(error);
  }
);

export default api;
```

### React Query Setup (lib/query-client.ts)

```typescript
import { QueryClient } from '@tanstack/react-query';

export const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 60 * 1000, // 1 minute
      retry: 1,
      refetchOnWindowFocus: false,
    },
  },
});
```

### Custom Hook Pattern (hooks/useApplicant.ts)

```typescript
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import api from '@/lib/api';

interface Applicant {
  id: string;
  tenant_id: string;
  full_name: string;
  email: string;
  status: string;
  created_at: string;
  // ... other fields
}

export function useApplicant(applicantId: string) {
  return useQuery({
    queryKey: ['applicant', applicantId],
    queryFn: async () => {
      const { data } = await api.get<Applicant>(`/v1/applicants/${applicantId}`);
      return data;
    },
    enabled: !!applicantId,
  });
}

export function useApplicants(filters?: { status?: string }) {
  return useQuery({
    queryKey: ['applicants', filters],
    queryFn: async () => {
      const { data } = await api.get<Applicant[]>('/v1/applicants', {
        params: filters,
      });
      return data;
    },
  });
}

export function useCreateApplicant() {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: async (applicantData: Partial<Applicant>) => {
      const { data } = await api.post<Applicant>('/v1/applicants', applicantData);
      return data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['applicants'] });
    },
  });
}
```

---

## Third-Party Integrations

### Claude API Integration (app/services/ai_service.py)

```python
import anthropic
from app.core.config import settings
import hashlib
import json

client = anthropic.Anthropic(api_key=settings.ANTHROPIC_API_KEY)

async def analyze_document_fraud(
    document_id: str,
    ocr_text: str,
    extracted_data: dict,
    document_type: str
) -> dict:
    """
    Use Claude to detect potential document fraud.
    Returns risk assessment with specific citations.
    """
    
    prompt = f"""Analyze this {document_type} for potential fraud indicators.

OCR Text:
{ocr_text}

Extracted Data:
{json.dumps(extracted_data, indent=2)}

Provide a JSON response with:
{{
  "risk_level": "low|medium|high",
  "fraud_signals": [
    {{
      "type": "font_inconsistency|altered_text|fake_template|other",
      "description": "Specific description",
      "location": "Where in document",
      "confidence": 0.0-1.0
    }}
  ],
  "overall_confidence": 0.0-1.0,
  "recommended_action": "approve|request_resubmission|manual_review"
}}

Only output valid JSON, no other text."""
    
    # Calculate hashes for audit trail
    prompt_hash = hashlib.sha256(prompt.encode()).hexdigest()
    input_hash = hashlib.sha256(
        json.dumps({"ocr": ocr_text, "data": extracted_data}).encode()
    ).hexdigest()
    
    try:
        message = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=2000,
            messages=[{"role": "user", "content": prompt}]
        )
        
        response_text = message.content[0].text
        
        # Parse JSON response
        result = json.loads(response_text)
        
        # Add metadata
        result["metadata"] = {
            "model": "claude-sonnet-4-20250514",
            "prompt_hash": prompt_hash,
            "input_hash": input_hash,
            "document_id": document_id,
            "usage": {
                "input_tokens": message.usage.input_tokens,
                "output_tokens": message.usage.output_tokens
            }
        }
        
        return result
        
    except json.JSONDecodeError:
        # Fallback if Claude doesn't return valid JSON
        return {
            "risk_level": "unknown",
            "fraud_signals": [],
            "overall_confidence": 0.0,
            "recommended_action": "manual_review",
            "error": "Failed to parse AI response"
        }
```

### OpenSanctions API Integration (app/services/screening_service.py)

**OpenSanctions API Docs:** https://www.opensanctions.org/docs/api/

```python
import httpx
from app.core.config import settings
from typing import List, Dict

async def search_sanctions(
    name: str,
    countries: List[str] = None,
    birth_date: str = None,
    threshold: float = 0.7
) -> List[Dict]:
    """
    Search OpenSanctions API for potential matches.
    
    Docs: https://www.opensanctions.org/docs/api/
    """
    
    url = "https://api.opensanctions.org/search/default"
    
    params = {
        "q": name,
        "threshold": threshold,
        "limit": 50
    }
    
    if countries:
        params["countries"] = ",".join(countries)
    
    if birth_date:
        params["birth_date"] = birth_date
    
    headers = {
        "Authorization": f"Bearer {settings.OPENSANCTIONS_API_KEY}"
    }
    
    async with httpx.AsyncClient() as client:
        response = await client.get(url, params=params, headers=headers)
        response.raise_for_status()
        data = response.json()
        
        return data.get("results", [])

async def get_entity_details(entity_id: str) -> Dict:
    """Get full details for a specific entity."""
    
    url = f"https://api.opensanctions.org/entities/{entity_id}"
    
    headers = {
        "Authorization": f"Bearer {settings.OPENSANCTIONS_API_KEY}"
    }
    
    async with httpx.AsyncClient() as client:
        response = await client.get(url, headers=headers)
        response.raise_for_status()
        return response.json()
```

### AWS Textract Integration (app/services/ocr_service.py)

**AWS Textract Docs:** https://docs.aws.amazon.com/textract/

```python
import boto3
from app.core.config import settings
from typing import Dict

# Initialize Textract client
textract = boto3.client(
    'textract',
    aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
    aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
    region_name=settings.AWS_REGION
)

async def extract_id_document(
    document_bytes: bytes,
    document_type: str = "IDENTITY_DOCUMENT"
) -> Dict:
    """
    Extract structured data from ID document using AWS Textract.
    
    Docs: https://docs.aws.amazon.com/textract/latest/dg/API_AnalyzeID.html
    """
    
    try:
        response = textract.analyze_id(
            DocumentPages=[
                {
                    'Bytes': document_bytes
                }
            ]
        )
        
        # Parse response
        extracted_data = {}
        confidence_scores = {}
        
        for id_document in response.get('IdentityDocuments', []):
            for field in id_document.get('IdentityDocumentFields', []):
                field_type = field.get('Type', {}).get('Text', '')
                field_value = field.get('ValueDetection', {}).get('Text', '')
                confidence = field.get('ValueDetection', {}).get('Confidence', 0)
                
                # Map field types to our schema
                field_mapping = {
                    'FIRST_NAME': 'first_name',
                    'LAST_NAME': 'last_name',
                    'DATE_OF_BIRTH': 'date_of_birth',
                    'DOCUMENT_NUMBER': 'document_number',
                    'EXPIRATION_DATE': 'expiry_date',
                    'ADDRESS': 'address',
                }
                
                mapped_field = field_mapping.get(field_type, field_type.lower())
                extracted_data[mapped_field] = field_value
                confidence_scores[mapped_field] = confidence
        
        # Get raw text
        raw_text = ""
        for block in response.get('Blocks', []):
            if block.get('BlockType') == 'LINE':
                raw_text += block.get('Text', '') + "\n"
        
        return {
            "extracted_data": extracted_data,
            "confidence_scores": confidence_scores,
            "ocr_text": raw_text.strip(),
            "raw_response": response
        }
        
    except Exception as e:
        raise Exception(f"Textract extraction failed: {str(e)}")
```

### Cloudflare R2 Storage (app/services/storage_service.py)

**R2 Docs:** https://developers.cloudflare.com/r2/

```python
import boto3
from app.core.config import settings
from typing import BinaryIO
import uuid

# R2 uses S3-compatible API
s3_client = boto3.client(
    's3',
    endpoint_url=f'https://{settings.R2_ACCOUNT_ID}.r2.cloudflarestorage.com',
    aws_access_key_id=settings.R2_ACCESS_KEY_ID,
    aws_secret_access_key=settings.R2_SECRET_ACCESS_KEY,
    region_name='auto'
)

async def upload_document(
    file: BinaryIO,
    tenant_id: str,
    applicant_id: str,
    document_type: str,
    content_type: str
) -> str:
    """Upload document to R2 and return object key."""
    
    # Generate unique key with tenant isolation
    file_id = str(uuid.uuid4())
    extension = content_type.split('/')[-1]
    object_key = f"{tenant_id}/applicants/{applicant_id}/documents/{file_id}.{extension}"
    
    # Upload to R2
    s3_client.upload_fileobj(
        file,
        settings.R2_BUCKET_NAME,
        object_key,
        ExtraArgs={
            'ContentType': content_type,
            'Metadata': {
                'tenant-id': tenant_id,
                'applicant-id': applicant_id,
                'document-type': document_type
            }
        }
    )
    
    return object_key

def generate_presigned_url(object_key: str, expires_in: int = 3600) -> str:
    """Generate presigned URL for temporary document access."""
    
    url = s3_client.generate_presigned_url(
        'get_object',
        Params={
            'Bucket': settings.R2_BUCKET_NAME,
            'Key': object_key
        },
        ExpiresIn=expires_in
    )
    
    return url

async def delete_document(object_key: str):
    """Delete document from R2."""
    
    s3_client.delete_object(
        Bucket=settings.R2_BUCKET_NAME,
        Key=object_key
    )
```

---

## Development Environment Setup

### Local Development with Docker Compose

**docker-compose.yml:**

```yaml
version: '3.8'

services:
  postgres:
    image: postgres:15-alpine
    environment:
      POSTGRES_DB: signalweave
      POSTGRES_USER: postgres
      POSTGRES_PASSWORD: postgres
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data
    command: 
      - "postgres"
      - "-c"
      - "shared_preload_libraries=pg_trgm"

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data

  mailhog:
    image: mailhog/mailhog
    ports:
      - "1025:1025"  # SMTP
      - "8025:8025"  # Web UI

volumes:
  postgres_data:
  redis_data:
```

**Start services:**
```bash
docker-compose up -d

# Check logs
docker-compose logs -f postgres
```

### Requirements.txt

```txt
# FastAPI
fastapi==0.109.0
uvicorn[standard]==0.27.0
pydantic==2.5.3
pydantic-settings==2.1.0

# Database
sqlalchemy==2.0.25
asyncpg==0.29.0
alembic==1.13.1
psycopg2-binary==2.9.9

# Redis & Task Queue
redis==5.0.1
arq==0.25.0

# Auth & Security
python-jose[cryptography]==3.3.0
passlib[bcrypt]==1.7.4
python-multipart==0.0.6

# HTTP Clients
httpx==0.26.0
boto3==1.34.27

# AI & ML
anthropic==0.8.1

# Monitoring
sentry-sdk==1.40.0

# Testing
pytest==7.4.4
pytest-asyncio==0.23.3
httpx==0.26.0

# Code Quality
ruff==0.1.14
black==23.12.1
mypy==1.8.0
```

### Running Locally

```bash
# Install dependencies
pip install -r requirements.txt

# Set up database
createdb signalweave
alembic upgrade head

# Enable PostgreSQL extensions
psql signalweave -c "CREATE EXTENSION IF NOT EXISTS pg_trgm;"

# Run API server
uvicorn app.main:app --reload --port 8000

# Run worker (separate terminal)
arq app.worker.WorkerSettings
```

---

## Pre-Researched Documentation Links

### Infrastructure & Deployment
- **Railway Platform:** https://docs.railway.app/
- **Railway Databases:** https://docs.railway.app/databases/postgresql
- **Railway Environment Variables:** https://docs.railway.app/deploy/variables
- **Railway Networking:** https://docs.railway.app/deploy/exposing-your-app

### Backend Core
- **FastAPI Full Tutorial:** https://fastapi.tiangolo.com/tutorial/
- **FastAPI Dependencies:** https://fastapi.tiangolo.com/tutorial/dependencies/
- **FastAPI Background Tasks:** https://fastapi.tiangolo.com/tutorial/background-tasks/
- **FastAPI Security:** https://fastapi.tiangolo.com/tutorial/security/
- **Pydantic V2 Docs:** https://docs.pydantic.dev/latest/
- **SQLAlchemy 2.0 Tutorial:** https://docs.sqlalchemy.org/en/20/tutorial/
- **SQLAlchemy Async:** https://docs.sqlalchemy.org/en/20/orm/extensions/asyncio.html
- **Alembic Tutorial:** https://alembic.sqlalchemy.org/en/latest/tutorial.html

### PostgreSQL
- **PostgreSQL Row Security:** https://www.postgresql.org/docs/current/ddl-rowsecurity.html
- **PostgreSQL Full-Text Search:** https://www.postgresql.org/docs/current/textsearch.html
- **PostgreSQL Trigram (pg_trgm):** https://www.postgresql.org/docs/current/pgtrgm.html
- **PostgreSQL JSONB:** https://www.postgresql.org/docs/current/datatype-json.html
- **Neon RLS Guide:** https://neon.tech/docs/guides/row-level-security
- **Supabase RLS Examples:** https://supabase.com/docs/guides/database/postgres/row-level-security

### Task Queues & Background Processing
- **ARQ Documentation:** https://arq-docs.helpmanual.io/
- **Redis Python Client:** https://redis-py.readthedocs.io/en/stable/
- **Celery (alternative):** https://docs.celeryq.dev/en/stable/

### Third-Party APIs
- **Claude API Docs:** https://docs.anthropic.com/claude/reference/
- **OpenSanctions API:** https://www.opensanctions.org/docs/api/
- **AWS Textract:** https://docs.aws.amazon.com/textract/
- **Textract AnalyzeID:** https://docs.aws.amazon.com/textract/latest/dg/API_AnalyzeID.html
- **Cloudflare R2 Docs:** https://developers.cloudflare.com/r2/
- **R2 S3 Compatibility:** https://developers.cloudflare.com/r2/api/s3/api/

### KYC/AML Reference Platforms
- **Sumsub API Reference:** https://docs.sumsub.com/reference/
- **Sumsub Get Started:** https://docs.sumsub.com/reference/get-started-with-api
- **Persona API Docs:** https://docs.withpersona.com/
- **Persona Inquiries:** https://docs.withpersona.com/reference/inquiries

### Frontend (React/Next.js)
- **Next.js Docs:** https://nextjs.org/docs
- **React Query (TanStack):** https://tanstack.com/query/latest
- **Axios Documentation:** https://axios-http.com/docs/intro
- **shadcn/ui Components:** https://ui.shadcn.com/

### Monitoring & Observability
- **Sentry FastAPI Integration:** https://docs.sentry.io/platforms/python/integrations/fastapi/
- **Sentry Error Tracking:** https://docs.sentry.io/product/issues/

### Security & Compliance
- **OWASP API Security:** https://owasp.org/API-Security/
- **JWT Best Practices:** https://tools.ietf.org/html/rfc8725
- **GDPR Compliance:** https://gdpr.eu/
- **KYC Regulations (FinCEN):** https://www.fincen.gov/resources/statutes-and-regulations

---

## Common Patterns Quick Reference

### Making a Database Query with RLS
```python
# Always use dependency injection
@router.get("/applicants")
async def list_applicants(
    tenant: Tenant = Depends(get_current_tenant),  # This sets RLS
    db: AsyncSession = Depends(get_db)
):
    # Query is automatically scoped to tenant
    result = await db.execute(select(Applicant))
    return result.scalars().all()
```

### Queueing a Background Task
```python
from app.worker.tasks import run_screening
from arq import ArqRedis
from app.core.redis import get_redis

async def trigger_screening(applicant_id: str):
    redis = await get_redis()
    arq = ArqRedis(redis)
    
    job = await arq.enqueue_job(
        'run_screening',
        applicant_id=applicant_id
    )
    
    return job.job_id
```

### Creating an Audit Log Entry
```python
from app.utils.audit_log import create_audit_log

await create_audit_log(
    db=db,
    tenant_id=tenant.id,
    entity_type="applicant",
    entity_id=applicant.id,
    action="status_changed",
    actor_id=user_id,
    old_value={"status": "pending"},
    new_value={"status": "approved"}
)
```

### Calling Claude API
```python
from app.services.ai_service import analyze_document_fraud

result = await analyze_document_fraud(
    document_id=doc.id,
    ocr_text=doc.ocr_text,
    extracted_data=doc.extracted_data,
    document_type="passport"
)

# Store in ai_assessments table
assessment = AIAssessment(
    document_id=doc.id,
    assessment_type="fraud_detection",
    risk_level=result["risk_level"],
    risk_factors=result["fraud_signals"],
    **result["metadata"]
)
db.add(assessment)
await db.commit()
```

---

**Last Updated:** 2024-01-XX  
**Maintainer:** Engineering Lead  
**Questions?** Post in #engineering Slack channel
