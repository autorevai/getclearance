"""
Get Clearance - Test Fixtures
==============================
Comprehensive pytest fixtures for unit and integration testing.

Provides:
- In-memory SQLite async database
- Mocked external services (OpenSanctions, R2, Claude)
- Test data factories
- FastAPI TestClient
"""

import asyncio
import json
import os
from datetime import date, datetime
from typing import Any, AsyncGenerator, Generator
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import UUID, uuid4

import pytest
import pytest_asyncio
from httpx import AsyncClient, Response
from sqlalchemy import event
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.pool import StaticPool

# Set test environment before importing app modules
# Use a valid PostgreSQL URL format for pydantic validation (we won't actually connect to it)
os.environ["DATABASE_URL"] = "postgresql+asyncpg://test:test@localhost:5432/test"
os.environ["REDIS_URL"] = "redis://localhost:6379/1"
os.environ["ENVIRONMENT"] = "development"


# ===========================================
# ASYNC EVENT LOOP FIXTURE
# ===========================================

@pytest.fixture(scope="session")
def event_loop() -> Generator[asyncio.AbstractEventLoop, None, None]:
    """Create event loop for async tests."""
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


# ===========================================
# DATABASE FIXTURES
# ===========================================

@pytest_asyncio.fixture(scope="function")
async def test_engine() -> AsyncGenerator[AsyncEngine, None]:
    """
    Create in-memory SQLite engine for testing.

    Uses SQLite instead of PostgreSQL for:
    - No external dependencies
    - Fast test execution
    - Isolated test runs
    """
    engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        echo=False,
        poolclass=StaticPool,
        connect_args={"check_same_thread": False},
    )

    # Import all models to ensure they're registered
    from app.database import Base
    from app.models import (
        Applicant, ApplicantStep, AuditLog, Case, CaseNote, CaseAttachment,
        Document, ScreeningCheck, ScreeningHit, ScreeningList, Tenant, User
    )

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    yield engine

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

    await engine.dispose()


@pytest_asyncio.fixture(scope="function")
async def db(test_engine: AsyncEngine) -> AsyncGenerator[AsyncSession, None]:
    """
    Create database session for testing.

    Each test gets a fresh session with rollback on completion.
    """
    session_factory = async_sessionmaker(
        bind=test_engine,
        class_=AsyncSession,
        expire_on_commit=False,
        autocommit=False,
        autoflush=False,
    )

    async with session_factory() as session:
        yield session
        await session.rollback()


@pytest_asyncio.fixture(scope="function")
async def db_with_data(db: AsyncSession) -> AsyncGenerator[AsyncSession, None]:
    """
    Database session with seed data for integration tests.
    """
    from app.models import Tenant, User, Applicant

    # Create tenant
    tenant = Tenant(
        id=uuid4(),
        name="Test Company",
        slug="test-company",
        settings={
            "webhook": {
                "enabled": True,
                "url": "https://example.com/webhook",
                "secret": "test-webhook-secret-key-123",
                "events": ["applicant.reviewed", "screening.completed"]
            }
        }
    )
    db.add(tenant)

    # Create user
    user = User(
        id=uuid4(),
        tenant_id=tenant.id,
        email="admin@test.com",
        auth0_id="auth0|test123",
        role="admin",
    )
    db.add(user)

    # Create test applicant
    applicant = Applicant(
        id=uuid4(),
        tenant_id=tenant.id,
        external_id="EXT-001",
        email="john.doe@example.com",
        first_name="John",
        last_name="Doe",
        date_of_birth=date(1990, 1, 15),
        nationality="USA",
        country_of_residence="USA",
        status="pending",
        risk_score=25,
        flags=[],
    )
    db.add(applicant)

    await db.commit()

    yield db


# ===========================================
# TEST DATA FIXTURES
# ===========================================

@pytest.fixture
def tenant_id() -> UUID:
    """Consistent tenant ID for tests."""
    return UUID("12345678-1234-5678-1234-567812345678")


@pytest.fixture
def applicant_id() -> UUID:
    """Consistent applicant ID for tests."""
    return UUID("87654321-4321-8765-4321-876543218765")


@pytest.fixture
def sample_applicant_data() -> dict[str, Any]:
    """Sample applicant data for tests."""
    return {
        "email": "test@example.com",
        "first_name": "John",
        "last_name": "Doe",
        "date_of_birth": "1990-01-15",
        "nationality": "USA",
        "country_of_residence": "USA",
    }


@pytest.fixture
def sample_mrz_lines() -> list[str]:
    """Valid MRZ lines for passport testing."""
    # TD3 format: 2 lines x 44 characters
    # P<USADOE<<JOHN<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<
    # ABC1234560USA9001151M3001011<<<<<<<<<<<<<<04
    return [
        "P<USADOE<<JOHN<<<<<<<<<<<<<<<<<<<<<<<<<<<",
        "ABC1234560USA9001151M3001011<<<<<<<<<<<<<<04"
    ]


@pytest.fixture
def invalid_mrz_lines() -> list[str]:
    """Invalid MRZ lines with checksum errors."""
    # Same as above but with incorrect check digit
    return [
        "P<USADOE<<JOHN<<<<<<<<<<<<<<<<<<<<<<<<<<<",
        "ABC1234569USA9001151M3001011<<<<<<<<<<<<<<04"  # Changed 0 to 9 in check digit
    ]


# ===========================================
# MOCK OPENSANCTIONS FIXTURE
# ===========================================

@pytest.fixture
def mock_opensanctions_response() -> dict[str, Any]:
    """Mock response from OpenSanctions API."""
    return {
        "responses": {
            "q1": {
                "query": {"schema": "Person", "properties": {"name": ["John Doe"]}},
                "results": [
                    {
                        "id": "nk-abc123",
                        "caption": "John Doe",
                        "schema": "Person",
                        "score": 0.95,
                        "datasets": ["us_ofac_sdn"],
                        "properties": {
                            "name": ["John Doe", "Johnny Doe"],
                            "birthDate": ["1990-01-15"],
                            "nationality": ["us"],
                            "topics": ["sanction"],
                        },
                    }
                ],
            }
        }
    }


@pytest.fixture
def mock_opensanctions_clear() -> dict[str, Any]:
    """Mock response with no hits."""
    return {
        "responses": {
            "q1": {
                "query": {"schema": "Person", "properties": {"name": ["Jane Smith"]}},
                "results": [],
            }
        }
    }


@pytest.fixture
def mock_opensanctions_pep() -> dict[str, Any]:
    """Mock response with PEP hit."""
    return {
        "responses": {
            "q1": {
                "query": {"schema": "Person", "properties": {"name": ["Political Person"]}},
                "results": [
                    {
                        "id": "nk-pep123",
                        "caption": "Political Person",
                        "schema": "Person",
                        "score": 0.87,
                        "datasets": ["everypolitician"],
                        "properties": {
                            "name": ["Political Person"],
                            "birthDate": ["1965-05-20"],
                            "position": ["Minister of Finance"],
                            "topics": ["role.pep.national"],
                        },
                    }
                ],
            }
        }
    }


@pytest.fixture
def mock_opensanctions(
    mock_opensanctions_response: dict[str, Any]
) -> Generator[AsyncMock, None, None]:
    """
    Mock OpenSanctions API client.

    Patches httpx.AsyncClient to return mock responses.
    """
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = mock_opensanctions_response
    mock_response.headers = {"X-OpenSanctions-Version": "2024-01-01"}

    with patch("httpx.AsyncClient") as mock_client:
        instance = AsyncMock()
        instance.post = AsyncMock(return_value=mock_response)
        instance.get = AsyncMock(return_value=mock_response)
        instance.is_closed = False
        instance.aclose = AsyncMock()
        mock_client.return_value.__aenter__ = AsyncMock(return_value=instance)
        mock_client.return_value.__aexit__ = AsyncMock(return_value=None)
        yield mock_client


# ===========================================
# MOCK STORAGE (R2) FIXTURE
# ===========================================

@pytest.fixture
def mock_storage() -> Generator[MagicMock, None, None]:
    """
    Mock Cloudflare R2/S3 storage.

    Returns mock presigned URLs and handles upload/download operations.
    """
    with patch("aioboto3.Session") as mock_session:
        mock_client = AsyncMock()

        # Mock presigned POST
        mock_client.generate_presigned_post = AsyncMock(return_value={
            "url": "https://test-bucket.r2.cloudflarestorage.com",
            "fields": {
                "key": "test-key",
                "policy": "test-policy",
                "x-amz-signature": "test-signature",
            },
        })

        # Mock presigned GET
        mock_client.generate_presigned_url = AsyncMock(
            return_value="https://test-bucket.r2.cloudflarestorage.com/test-key?signature=abc"
        )

        # Mock head_object (for checking existence)
        mock_client.head_object = AsyncMock(return_value={
            "ContentLength": 1024,
            "ContentType": "image/jpeg",
            "LastModified": datetime.utcnow(),
            "ETag": '"abc123"',
            "Metadata": {},
        })

        # Mock delete_object
        mock_client.delete_object = AsyncMock(return_value={})

        # Mock list/delete for prefix
        mock_client.get_paginator = MagicMock()

        # Set up session to return mock client
        mock_session_instance = MagicMock()
        mock_session_instance.client = MagicMock(return_value=AsyncMock(
            __aenter__=AsyncMock(return_value=mock_client),
            __aexit__=AsyncMock(return_value=None),
        ))
        mock_session.return_value = mock_session_instance

        yield mock_session


# ===========================================
# MOCK AI (CLAUDE) FIXTURE
# ===========================================

@pytest.fixture
def mock_claude_risk_response() -> str:
    """Mock Claude API response for risk assessment."""
    return json.dumps({
        "overall_risk": "low",
        "risk_score": 25,
        "summary": "Low-risk applicant with clean screening results and verified documents.",
        "risk_factors": [
            {
                "category": "identity",
                "severity": "low",
                "description": "All identity documents verified successfully",
                "source_type": "document",
                "source_id": "doc-123",
                "source_name": "Passport verification",
            }
        ],
        "recommendations": [
            "Proceed with standard approval process",
            "No additional verification required"
        ],
    })


@pytest.fixture
def mock_claude_high_risk_response() -> str:
    """Mock Claude API response for high-risk assessment."""
    return json.dumps({
        "overall_risk": "high",
        "risk_score": 75,
        "summary": "High-risk applicant with sanctions hit requiring review.",
        "risk_factors": [
            {
                "category": "regulatory",
                "severity": "high",
                "description": "Potential match to OFAC sanctions list",
                "source_type": "screening",
                "source_id": "hit-456",
                "source_name": "OFAC SDN screening",
            }
        ],
        "recommendations": [
            "Escalate to compliance officer",
            "Request additional documentation",
            "Verify identity through secondary means"
        ],
    })


@pytest.fixture
def mock_claude(mock_claude_risk_response: str) -> Generator[MagicMock, None, None]:
    """
    Mock Claude/Anthropic API client.
    """
    with patch("anthropic.AsyncAnthropic") as mock_anthropic:
        mock_client = AsyncMock()

        # Mock message response
        mock_message = MagicMock()
        mock_content = MagicMock()
        mock_content.text = mock_claude_risk_response
        mock_message.content = [mock_content]

        mock_client.messages = AsyncMock()
        mock_client.messages.create = AsyncMock(return_value=mock_message)

        mock_anthropic.return_value = mock_client

        yield mock_anthropic


# ===========================================
# MOCK REDIS/ARQ FIXTURE
# ===========================================

@pytest.fixture
def mock_redis() -> Generator[MagicMock, None, None]:
    """Mock Redis for ARQ job queue."""
    with patch("arq.create_pool") as mock_pool:
        mock_redis_instance = AsyncMock()
        mock_redis_instance.enqueue_job = AsyncMock(return_value=MagicMock(job_id="test-job-123"))
        mock_pool.return_value = mock_redis_instance
        yield mock_pool


# ===========================================
# HTTPX/HTTP CLIENT FIXTURES
# ===========================================

@pytest.fixture
def mock_httpx_success() -> Generator[MagicMock, None, None]:
    """Mock httpx client for successful webhook delivery."""
    with patch("httpx.AsyncClient") as mock_client:
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.text = "OK"

        instance = AsyncMock()
        instance.post = AsyncMock(return_value=mock_response)

        mock_client.return_value.__aenter__ = AsyncMock(return_value=instance)
        mock_client.return_value.__aexit__ = AsyncMock(return_value=None)

        yield mock_client


@pytest.fixture
def mock_httpx_failure() -> Generator[MagicMock, None, None]:
    """Mock httpx client for failed webhook delivery."""
    with patch("httpx.AsyncClient") as mock_client:
        mock_response = MagicMock()
        mock_response.status_code = 500
        mock_response.text = "Internal Server Error"

        instance = AsyncMock()
        instance.post = AsyncMock(return_value=mock_response)

        mock_client.return_value.__aenter__ = AsyncMock(return_value=instance)
        mock_client.return_value.__aexit__ = AsyncMock(return_value=None)

        yield mock_client


# ===========================================
# FASTAPI TEST CLIENT
# ===========================================

@pytest_asyncio.fixture(scope="function")
async def client(db: AsyncSession) -> AsyncGenerator[AsyncClient, None]:
    """
    FastAPI test client with mocked database.

    Overrides the database dependency to use the test session.
    """
    from app.main import app
    from app.database import get_db

    async def override_get_db():
        yield db

    app.dependency_overrides[get_db] = override_get_db

    async with AsyncClient(app=app, base_url="http://test") as ac:
        yield ac

    app.dependency_overrides.clear()


# ===========================================
# SERVICE INSTANCE FIXTURES
# ===========================================

@pytest.fixture
def screening_service():
    """Get screening service instance for testing."""
    from app.services.screening import ScreeningService
    return ScreeningService(
        api_key="test-api-key",
        api_url="https://api.opensanctions.org/match/default",
    )


@pytest.fixture
def storage_service():
    """Get storage service instance for testing."""
    # Create mock storage service for testing
    from unittest.mock import MagicMock

    mock_service = MagicMock()
    mock_service.is_configured = True
    mock_service.upload_expires = 3600
    mock_service.download_expires = 3600

    return mock_service


@pytest.fixture
def ai_service():
    """Get AI service instance for testing."""
    from app.services.ai import AIService
    return AIService(
        api_key="test-api-key",
        model="claude-sonnet-4-20250514",
    )


@pytest.fixture
def mrz_parser():
    """Get MRZ parser instance for testing."""
    from app.services.mrz_parser import MRZParser
    return MRZParser()


# ===========================================
# WEBHOOK FIXTURES
# ===========================================

@pytest.fixture
def webhook_secret() -> str:
    """Webhook signing secret for tests."""
    return "test-webhook-secret-key-123456"


@pytest.fixture
def webhook_payload() -> dict[str, Any]:
    """Sample webhook payload for tests."""
    return {
        "event_type": "applicant.reviewed",
        "event_id": str(uuid4()),
        "timestamp": datetime.utcnow().isoformat(),
        "tenant_id": str(uuid4()),
        "correlation_id": "test-correlation-123",
        "data": {
            "applicant_id": str(uuid4()),
            "external_id": "EXT-001",
            "status": "approved",
            "risk_score": 25,
            "risk_level": "low",
            "reviewed_at": datetime.utcnow().isoformat(),
        },
    }


# ===========================================
# CLEANUP HELPERS
# ===========================================

@pytest.fixture(autouse=True)
def reset_service_singletons():
    """Reset service singletons between tests."""
    yield

    # Reset singleton clients after each test
    from app.services.screening import screening_service
    from app.services.storage import storage_service
    from app.services.ai import ai_service

    # Close any open clients
    if hasattr(screening_service, '_client') and screening_service._client:
        screening_service._client = None
    if hasattr(storage_service, '_session') and storage_service._session:
        storage_service._session = None
    if hasattr(ai_service, '_client') and ai_service._client:
        ai_service._client = None
