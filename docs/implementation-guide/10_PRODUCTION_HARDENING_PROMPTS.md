# Production Hardening Sprint Prompts - Copy & Paste Ready
**Purpose:** Ready-to-use prompts to close the gaps identified in the Implementation Audit
**How to Use:** Copy the entire prompt for the sprint you're starting

---

## Current Reality

Based on the Implementation Audit (`docs/IMPLEMENTATION_AUDIT.md`), we have:
- **Overall Grade: B+** - Strong foundation with gaps in production hardening
- **Backend:** Functional but missing critical security features
- **Missing:** Liveness detection, face matching, rate limiting, observability

---

## Files to Upload to EVERY Sprint Chat

Before starting ANY sprint, upload these files:

1. `docs/IMPLEMENTATION_AUDIT.md` - Gap analysis with specific issues
2. `docs/implementation-guide/02_FOLDER_STRUCTURE_COMPLETE.md` - Directory tree
3. `docs/implementation-guide/05_SUMSUB_CONTEXT.md` - Sumsub features we're replicating
4. `README.md` (from your getclearance repo)

---

## Sprint 1: Rate Limiting & API Security (Critical - 2-3 Days)

### Files to Upload:
1. `docs/IMPLEMENTATION_AUDIT.md`
2. `docs/implementation-guide/02_FOLDER_STRUCTURE_COMPLETE.md`
3. `docs/implementation-guide/05_SUMSUB_CONTEXT.md`
4. `README.md`
5. `backend/app/main.py`
6. `backend/app/config.py`

### Prompt (Copy This):

```
# CHAT TITLE: Production Hardening Sprint 1 - Rate Limiting & API Security

## Context
I'm building GetClearance, an AI-native KYC/AML platform (Sumsub clone). The backend is ~95% complete but is missing critical API security features before production deployment. The Implementation Audit identified these as critical gaps.

**Current Repo:** https://github.com/autorevai/getclearance

## What Exists (Read These First)
I've uploaded context files:

1. **IMPLEMENTATION_AUDIT.md** - Honest assessment identifying these gaps
2. **02_FOLDER_STRUCTURE_COMPLETE.md** - Directory tree
3. **05_SUMSUB_CONTEXT.md** - Sumsub patterns
4. **README.md** - Project README
5. **main.py** - FastAPI entry point
6. **config.py** - Settings configuration

**Current state:**
- ✅ All API endpoints working
- ✅ Auth0 JWT authentication
- ❌ No rate limiting (anyone can spam endpoints)
- ❌ No request ID tracing
- ❌ No API key management for tenants
- ❌ No request/response logging

## What I Need You To Create

### Part 1: Rate Limiting

**Files to create:**
1. `backend/app/middleware/rate_limit.py` - Rate limiting middleware

**Files to update:**
2. `backend/app/main.py` - Add rate limiting middleware
3. `backend/app/config.py` - Add rate limit configuration

**Rate Limit Requirements:**
- Per-tenant rate limits (based on tenant_id from JWT)
- Default: 100 requests/minute for authenticated users
- 10 requests/minute for unauthenticated endpoints (health, etc.)
- Configurable via tenant settings (premium tenants get higher limits)
- Return 429 Too Many Requests with retry-after header
- Use Redis for distributed rate limiting (already have Redis)

### Part 2: Request ID Tracing

**Files to create:**
3. `backend/app/middleware/request_id.py` - Request ID middleware

**Requirements:**
- Generate UUID for each request (or use X-Request-ID header if provided)
- Add to all log messages
- Return in X-Request-ID response header
- Pass to background workers for end-to-end tracing

### Part 3: Request/Response Logging

**Files to create:**
4. `backend/app/middleware/logging.py` - Structured logging middleware

**Requirements:**
- Log all requests with: method, path, status_code, duration_ms, tenant_id, request_id
- Use structured JSON format for log aggregation
- Don't log request/response bodies (PII concerns)
- Log errors with stack traces

### Part 4: API Key Management

**Files to create:**
5. `backend/app/services/api_keys.py` - API key service
6. `backend/app/api/v1/api_keys.py` - API key management endpoints

**Requirements:**
- Tenants can create/revoke API keys
- API keys stored hashed in database (like passwords)
- Keys have optional expiration
- Keys can be scoped (read-only, full access)
- Support both JWT and API key authentication

## Integration Requirements

### Rate Limiting Pattern:
```python
# middleware/rate_limit.py
from slowapi import Limiter
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from app.config import settings

def get_tenant_id(request):
    """Extract tenant_id from JWT for rate limiting."""
    # Get from auth context
    return request.state.tenant_id or get_remote_address(request)

limiter = Limiter(
    key_func=get_tenant_id,
    default_limits=[f"{settings.rate_limit_requests}/minute"],
    storage_uri=settings.redis_url_str,
)

# In main.py
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
```

### Request ID Pattern:
```python
# middleware/request_id.py
import uuid
from starlette.middleware.base import BaseHTTPMiddleware

class RequestIDMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        request_id = request.headers.get("X-Request-ID", str(uuid.uuid4()))
        request.state.request_id = request_id

        response = await call_next(request)
        response.headers["X-Request-ID"] = request_id
        return response
```

### Structured Logging Pattern:
```python
# middleware/logging.py
import time
import logging
import json

logger = logging.getLogger("api")

class LoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        start = time.time()
        response = await call_next(request)
        duration = (time.time() - start) * 1000

        logger.info(json.dumps({
            "request_id": getattr(request.state, "request_id", None),
            "method": request.method,
            "path": request.url.path,
            "status_code": response.status_code,
            "duration_ms": round(duration, 2),
            "tenant_id": getattr(request.state, "tenant_id", None),
        }))

        return response
```

### API Key Schema (add to database):
```sql
CREATE TABLE api_keys (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID REFERENCES tenants(id) ON DELETE CASCADE,
    name VARCHAR(255) NOT NULL,
    key_hash VARCHAR(255) NOT NULL,  -- bcrypt hash
    key_prefix VARCHAR(10) NOT NULL, -- First 10 chars for identification
    scopes JSONB DEFAULT '["read", "write"]',
    expires_at TIMESTAMPTZ,
    last_used_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    revoked_at TIMESTAMPTZ
);

CREATE INDEX idx_api_keys_prefix ON api_keys(key_prefix) WHERE revoked_at IS NULL;
```

## Architecture Constraints

**Middleware Order in main.py:**
```python
# Order matters! Add in this sequence:
app.add_middleware(LoggingMiddleware)
app.add_middleware(RequestIDMiddleware)
app.add_middleware(RateLimitMiddleware)
app.add_middleware(CORSMiddleware, ...)
```

**Config Updates:**
```python
# config.py additions
rate_limit_requests: int = Field(default=100)
rate_limit_window: int = Field(default=60)  # seconds
rate_limit_premium_requests: int = Field(default=1000)
```

## Success Criteria

- [ ] Rate limiting returns 429 after exceeding limit
- [ ] Rate limits are per-tenant (not per-IP)
- [ ] X-Request-ID header in all responses
- [ ] Request ID in all log messages
- [ ] Structured JSON logging enabled
- [ ] API keys can be created via API
- [ ] API key authentication works alongside JWT
- [ ] API keys can be revoked
- [ ] Tests pass with rate limiting enabled

## Testing Checklist

1. **Rate Limiting:**
   - Make 101 requests in 1 minute → 429 on 101st
   - Check Retry-After header is present
   - Different tenants have separate limits

2. **Request ID:**
   - Check response has X-Request-ID
   - Provide X-Request-ID → same ID returned
   - Check logs contain request_id

3. **API Keys:**
   - Create API key → returns key (only once)
   - Use API key in header → authenticated
   - Revoke key → 401 on next request
   - Expired key → 401

## Questions?
If unclear about Redis setup or authentication patterns, ask first.
```

---

## Sprint 2: Test Coverage (Critical - 3-5 Days)

### Files to Upload:
1. `docs/IMPLEMENTATION_AUDIT.md`
2. `docs/implementation-guide/02_FOLDER_STRUCTURE_COMPLETE.md`
3. `docs/implementation-guide/05_SUMSUB_CONTEXT.md`
4. `README.md`
5. `backend/tests/conftest.py`
6. `backend/pytest.ini`

### Prompt (Copy This):

```
# CHAT TITLE: Production Hardening Sprint 2 - Test Coverage to 80%+

## Context
I'm building GetClearance, an AI-native KYC/AML platform (Sumsub clone). The Implementation Audit revealed test coverage is ~40% - we need 80%+ before production. This is a critical gap.

**Current Repo:** https://github.com/autorevai/getclearance

## What Exists (Read These First)
I've uploaded context files:

1. **IMPLEMENTATION_AUDIT.md** - Identifies test coverage as critical gap
2. **02_FOLDER_STRUCTURE_COMPLETE.md** - Shows existing test structure
3. **05_SUMSUB_CONTEXT.md** - Sumsub features to test against
4. **README.md** - Project README
5. **conftest.py** - Existing test fixtures
6. **pytest.ini** - Pytest configuration

**Current test state:**
- ✅ 174 test functions across 6 files
- ✅ Worker tests exist
- ✅ Service tests exist (partial)
- ❌ No API endpoint tests (huge gap)
- ❌ No database integration tests
- ❌ No end-to-end flow tests
- ❌ ~40% coverage estimated

## What I Need You To Create

### Part 1: API Endpoint Tests

**Files to create:**
1. `backend/tests/api/__init__.py`
2. `backend/tests/api/test_applicants.py` - Applicant endpoints
3. `backend/tests/api/test_documents.py` - Document endpoints
4. `backend/tests/api/test_screening.py` - Screening endpoints
5. `backend/tests/api/test_cases.py` - Case endpoints
6. `backend/tests/api/test_ai.py` - AI endpoints

### Part 2: Database Integration Tests

**Files to create:**
7. `backend/tests/integration/__init__.py` (if not exists)
8. `backend/tests/integration/test_database.py` - DB operations
9. `backend/tests/integration/test_multi_tenant.py` - Tenant isolation

### Part 3: End-to-End Flow Tests

**Files to create:**
10. `backend/tests/e2e/__init__.py`
11. `backend/tests/e2e/test_kyc_flow.py` - Full KYC verification flow
12. `backend/tests/e2e/test_screening_flow.py` - Full screening flow

### Part 4: Enhanced Fixtures

**Files to update:**
13. `backend/tests/conftest.py` - Add more fixtures

## Integration Requirements

### Test Fixtures Needed:
```python
# conftest.py additions
import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from app.main import app
from app.database import Base

@pytest.fixture
async def db_session():
    """Create test database session."""
    engine = create_async_engine(
        "postgresql+asyncpg://postgres:postgres@localhost:5432/getclearance_test",
        echo=False,
    )
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with AsyncSession(engine) as session:
        yield session
        await session.rollback()

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

@pytest.fixture
async def client(db_session):
    """Create test API client."""
    async with AsyncClient(app=app, base_url="http://test") as ac:
        yield ac

@pytest.fixture
async def auth_headers(test_tenant):
    """Create auth headers with valid JWT."""
    # Mock JWT token for testing
    token = create_test_token(tenant_id=test_tenant.id)
    return {"Authorization": f"Bearer {token}"}

@pytest.fixture
async def test_tenant(db_session):
    """Create test tenant."""
    tenant = Tenant(name="Test Corp", slug="test-corp")
    db_session.add(tenant)
    await db_session.commit()
    return tenant

@pytest.fixture
async def test_applicant(db_session, test_tenant):
    """Create test applicant."""
    applicant = Applicant(
        tenant_id=test_tenant.id,
        email="test@example.com",
        first_name="John",
        last_name="Doe",
        status="pending",
    )
    db_session.add(applicant)
    await db_session.commit()
    return applicant
```

### API Test Pattern:
```python
# tests/api/test_applicants.py
import pytest
from httpx import AsyncClient

@pytest.mark.asyncio
async def test_list_applicants(client: AsyncClient, auth_headers, test_applicant):
    """Test listing applicants returns correct data."""
    response = await client.get("/api/v1/applicants", headers=auth_headers)

    assert response.status_code == 200
    data = response.json()
    assert "items" in data
    assert len(data["items"]) >= 1
    assert data["items"][0]["email"] == "test@example.com"

@pytest.mark.asyncio
async def test_list_applicants_unauthenticated(client: AsyncClient):
    """Test listing applicants without auth returns 401."""
    response = await client.get("/api/v1/applicants")
    assert response.status_code == 401

@pytest.mark.asyncio
async def test_create_applicant(client: AsyncClient, auth_headers):
    """Test creating applicant."""
    payload = {
        "email": "new@example.com",
        "first_name": "Jane",
        "last_name": "Smith",
    }
    response = await client.post(
        "/api/v1/applicants",
        json=payload,
        headers=auth_headers,
    )

    assert response.status_code == 201
    data = response.json()
    assert data["email"] == "new@example.com"
    assert data["status"] == "pending"
    assert "id" in data

@pytest.mark.asyncio
async def test_create_applicant_invalid_email(client: AsyncClient, auth_headers):
    """Test creating applicant with invalid email returns 422."""
    payload = {"email": "not-an-email", "first_name": "Test"}
    response = await client.post(
        "/api/v1/applicants",
        json=payload,
        headers=auth_headers,
    )
    assert response.status_code == 422

@pytest.mark.asyncio
async def test_get_applicant(client: AsyncClient, auth_headers, test_applicant):
    """Test getting single applicant."""
    response = await client.get(
        f"/api/v1/applicants/{test_applicant.id}",
        headers=auth_headers,
    )

    assert response.status_code == 200
    assert response.json()["id"] == str(test_applicant.id)

@pytest.mark.asyncio
async def test_get_applicant_not_found(client: AsyncClient, auth_headers):
    """Test getting non-existent applicant returns 404."""
    fake_id = "00000000-0000-0000-0000-000000000000"
    response = await client.get(
        f"/api/v1/applicants/{fake_id}",
        headers=auth_headers,
    )
    assert response.status_code == 404

@pytest.mark.asyncio
async def test_review_applicant_approve(client: AsyncClient, auth_headers, test_applicant):
    """Test approving applicant."""
    response = await client.post(
        f"/api/v1/applicants/{test_applicant.id}/review",
        json={"decision": "approved"},
        headers=auth_headers,
    )

    assert response.status_code == 200
    assert response.json()["status"] == "approved"

@pytest.mark.asyncio
async def test_review_applicant_reject(client: AsyncClient, auth_headers, test_applicant):
    """Test rejecting applicant."""
    response = await client.post(
        f"/api/v1/applicants/{test_applicant.id}/review",
        json={"decision": "rejected", "notes": "Failed verification"},
        headers=auth_headers,
    )

    assert response.status_code == 200
    assert response.json()["status"] == "rejected"
```

### E2E Test Pattern:
```python
# tests/e2e/test_kyc_flow.py
import pytest

@pytest.mark.asyncio
async def test_complete_kyc_verification(client, auth_headers, mock_opensanctions):
    """Test complete KYC verification flow."""
    # 1. Create applicant
    applicant_response = await client.post(
        "/api/v1/applicants",
        json={
            "email": "kyc-test@example.com",
            "first_name": "John",
            "last_name": "Smith",
            "date_of_birth": "1990-01-15",
            "nationality": "USA",
        },
        headers=auth_headers,
    )
    assert applicant_response.status_code == 201
    applicant = applicant_response.json()
    applicant_id = applicant["id"]

    # 2. Get upload URL for document
    upload_response = await client.post(
        "/api/v1/documents/upload-url",
        json={
            "applicant_id": applicant_id,
            "document_type": "passport",
            "file_name": "passport.jpg",
            "content_type": "image/jpeg",
        },
        headers=auth_headers,
    )
    assert upload_response.status_code == 200
    document_id = upload_response.json()["document_id"]

    # 3. Confirm document upload (simulate upload)
    confirm_response = await client.post(
        f"/api/v1/documents/{document_id}/confirm",
        json={"file_size": 1024000},
        headers=auth_headers,
    )
    assert confirm_response.status_code == 200

    # 4. Run screening
    screening_response = await client.post(
        "/api/v1/screening/check",
        json={
            "applicant_id": applicant_id,
            "check_types": ["sanctions", "pep"],
        },
        headers=auth_headers,
    )
    assert screening_response.status_code == 200

    # 5. Approve applicant
    review_response = await client.post(
        f"/api/v1/applicants/{applicant_id}/review",
        json={"decision": "approved"},
        headers=auth_headers,
    )
    assert review_response.status_code == 200
    assert review_response.json()["status"] == "approved"

    # 6. Download evidence pack
    evidence_response = await client.get(
        f"/api/v1/applicants/{applicant_id}/evidence",
        headers=auth_headers,
    )
    assert evidence_response.status_code == 200
    assert evidence_response.headers["content-type"] == "application/pdf"
```

## Coverage Requirements

**Target by module:**
- `app/api/` - 90% coverage
- `app/services/` - 80% coverage
- `app/workers/` - 70% coverage (harder to test)
- `app/models/` - 60% coverage (mostly declarations)

**Must test:**
- All API endpoints (happy path + error cases)
- Authentication (valid/invalid/expired tokens)
- Authorization (tenant isolation)
- Validation errors (422 responses)
- Not found errors (404 responses)
- Service error handling

## Success Criteria

- [ ] `pytest --cov=app` shows >80% coverage
- [ ] All API endpoints have tests
- [ ] E2E tests cover main flows
- [ ] Tests run in <60 seconds
- [ ] No flaky tests (run 10 times, all pass)
- [ ] All external APIs mocked

## Running Tests

```bash
cd backend

# Run all tests with coverage
pytest --cov=app --cov-report=html

# Run specific test file
pytest tests/api/test_applicants.py -v

# Run E2E tests only
pytest tests/e2e/ -v

# Run with parallel execution
pytest -n auto --cov=app
```

## Questions?
If unclear about mocking patterns or test database setup, ask first.
```

---

## Sprint 3: Liveness & Face Matching (Critical - 5-7 Days)

### Files to Upload:
1. `docs/IMPLEMENTATION_AUDIT.md`
2. `docs/implementation-guide/02_FOLDER_STRUCTURE_COMPLETE.md`
3. `docs/implementation-guide/05_SUMSUB_CONTEXT.md`
4. `README.md`
5. `backend/app/services/ocr.py`
6. `backend/app/config.py`

### Prompt (Copy This):

```
# CHAT TITLE: Production Hardening Sprint 3 - Liveness Detection & Face Matching

## Context
I'm building GetClearance, an AI-native KYC/AML platform (Sumsub clone). The Implementation Audit identified **liveness detection** as the most critical missing feature. Without it, someone can just hold up a photo of an ID - this is table stakes for any KYC provider.

**Current Repo:** https://github.com/autorevai/getclearance

## What Exists (Read These First)
I've uploaded context files:

1. **IMPLEMENTATION_AUDIT.md** - Identifies liveness as critical gap
2. **02_FOLDER_STRUCTURE_COMPLETE.md** - Directory tree
3. **05_SUMSUB_CONTEXT.md** - See liveness section
4. **README.md** - Project README
5. **ocr.py** - Existing document OCR service
6. **config.py** - Settings configuration

**Current state:**
- ✅ Document upload and OCR working
- ✅ MRZ parsing with checksum validation
- ❌ No selfie capture/upload
- ❌ No liveness detection
- ❌ No face matching (selfie vs ID photo)

**Sumsub Liveness Reference:**
- https://docs.sumsub.com/docs/liveness
- https://docs.sumsub.com/docs/live-capture
- Passive liveness (single photo analysis)
- Active liveness (head turn, blink detection)

## What I Need You To Create

### Part 1: Liveness Detection Service

**Files to create:**
1. `backend/app/services/liveness.py` - Liveness detection service

**Provider Options (choose ONE):**
- **AWS Rekognition** - Already have AWS credentials, easiest integration
- **Azure Face API** - Good accuracy, reasonable pricing
- **iProov/FaceTec** - Enterprise-grade, more complex

**Recommendation: Use AWS Rekognition** (we already have AWS for Textract)

### Part 2: Face Matching Service

**Files to create:**
2. `backend/app/services/face_matching.py` - Face comparison service

**Requirements:**
- Compare selfie to photo extracted from ID document
- Return similarity score (0-100)
- Threshold: 80% for match, 60-80% for review

### Part 3: Selfie Workflow Step

**Files to create:**
3. `backend/app/schemas/liveness.py` - Liveness schemas

**Files to update:**
4. `backend/app/api/v1/documents.py` - Add selfie upload endpoint
5. `backend/app/workers/document_worker.py` - Process selfie with liveness check
6. `backend/app/config.py` - Add liveness configuration

### Part 4: Database Schema

**Migration to create:**
7. `backend/migrations/versions/20251201_003_add_liveness.py`

**New columns:**
```sql
-- Add to applicants table
ALTER TABLE applicants ADD COLUMN selfie_document_id UUID REFERENCES documents(id);
ALTER TABLE applicants ADD COLUMN liveness_verified BOOLEAN DEFAULT FALSE;
ALTER TABLE applicants ADD COLUMN face_match_score DECIMAL(5,2);
ALTER TABLE applicants ADD COLUMN face_match_status VARCHAR(20);  -- 'match', 'no_match', 'review'

-- Add to documents table (for selfie metadata)
ALTER TABLE documents ADD COLUMN is_selfie BOOLEAN DEFAULT FALSE;
ALTER TABLE documents ADD COLUMN liveness_result JSONB;
ALTER TABLE documents ADD COLUMN face_detected BOOLEAN;
```

## Integration Requirements

### Liveness Service (AWS Rekognition):
```python
# services/liveness.py
import aioboto3
from app.config import settings

class LivenessService:
    """Liveness detection using AWS Rekognition."""

    def __init__(self):
        self.session = aioboto3.Session(
            aws_access_key_id=settings.aws_access_key_id,
            aws_secret_access_key=settings.aws_secret_access_key,
            region_name=settings.aws_region,
        )

    async def detect_liveness(self, image_bytes: bytes) -> LivenessResult:
        """
        Detect if image is a live person (not a photo of a photo).

        Uses AWS Rekognition DetectFaces with quality metrics.
        A "live" face has:
        - High sharpness (not blurry)
        - Proper lighting (not too dark/bright)
        - Correct pose (facing camera)
        - No occlusion (sunglasses, mask)
        """
        async with self.session.client('rekognition') as client:
            response = await client.detect_faces(
                Image={'Bytes': image_bytes},
                Attributes=['ALL']
            )

            if not response['FaceDetails']:
                return LivenessResult(
                    is_live=False,
                    confidence=0,
                    reason="No face detected",
                )

            face = response['FaceDetails'][0]

            # Check quality metrics
            quality = face['Quality']
            sharpness = quality['Sharpness']
            brightness = quality['Brightness']

            # Check pose
            pose = face['Pose']
            yaw = abs(pose['Yaw'])
            pitch = abs(pose['Pitch'])

            # Check for occlusions
            sunglasses = face.get('Sunglasses', {}).get('Value', False)
            eyeglasses = face.get('Eyeglasses', {}).get('Value', False)

            # Liveness score calculation
            is_live = (
                sharpness > 50 and
                30 < brightness < 80 and
                yaw < 30 and
                pitch < 30 and
                not sunglasses
            )

            confidence = min(100, (
                sharpness * 0.3 +
                (100 - abs(brightness - 55)) * 0.2 +
                (100 - yaw * 2) * 0.25 +
                (100 - pitch * 2) * 0.25
            ))

            return LivenessResult(
                is_live=is_live,
                confidence=round(confidence, 2),
                face_detected=True,
                quality_metrics={
                    "sharpness": sharpness,
                    "brightness": brightness,
                    "yaw": yaw,
                    "pitch": pitch,
                },
                issues=self._identify_issues(face),
            )

    def _identify_issues(self, face: dict) -> list[str]:
        """Identify why liveness might fail."""
        issues = []
        quality = face['Quality']
        pose = face['Pose']

        if quality['Sharpness'] < 50:
            issues.append("Image is blurry")
        if quality['Brightness'] < 30:
            issues.append("Image is too dark")
        if quality['Brightness'] > 80:
            issues.append("Image is overexposed")
        if abs(pose['Yaw']) > 30:
            issues.append("Face not facing camera")
        if face.get('Sunglasses', {}).get('Value'):
            issues.append("Sunglasses detected")
        if not face.get('EyesOpen', {}).get('Value', True):
            issues.append("Eyes appear closed")

        return issues

liveness_service = LivenessService()
```

### Face Matching Service:
```python
# services/face_matching.py
import aioboto3
from app.config import settings

class FaceMatchingService:
    """Face comparison using AWS Rekognition."""

    async def compare_faces(
        self,
        selfie_bytes: bytes,
        id_photo_bytes: bytes,
        similarity_threshold: float = 80.0,
    ) -> FaceMatchResult:
        """
        Compare selfie to ID document photo.

        Returns similarity score and match status.
        """
        async with self.session.client('rekognition') as client:
            try:
                response = await client.compare_faces(
                    SourceImage={'Bytes': selfie_bytes},
                    TargetImage={'Bytes': id_photo_bytes},
                    SimilarityThreshold=similarity_threshold,
                )

                if not response['FaceMatches']:
                    # No match above threshold
                    return FaceMatchResult(
                        match=False,
                        similarity=response.get('UnmatchedFaces', [{}])[0].get('Similarity', 0),
                        status='no_match',
                        reason="Faces do not match",
                    )

                best_match = response['FaceMatches'][0]
                similarity = best_match['Similarity']

                # Determine status
                if similarity >= 90:
                    status = 'match'
                elif similarity >= 80:
                    status = 'match'  # Above threshold
                elif similarity >= 60:
                    status = 'review'  # Needs human review
                else:
                    status = 'no_match'

                return FaceMatchResult(
                    match=similarity >= similarity_threshold,
                    similarity=round(similarity, 2),
                    status=status,
                    bounding_box=best_match['Face']['BoundingBox'],
                )

            except client.exceptions.InvalidParameterException as e:
                if "no faces" in str(e).lower():
                    return FaceMatchResult(
                        match=False,
                        similarity=0,
                        status='error',
                        reason="No face detected in one or both images",
                    )
                raise

face_matching_service = FaceMatchingService()
```

### API Endpoint:
```python
# In documents.py - add selfie endpoint
@router.post("/selfie")
async def upload_selfie(
    applicant_id: UUID,
    file: UploadFile,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Upload selfie for liveness check and face matching.

    1. Uploads selfie to storage
    2. Runs liveness detection
    3. Compares to ID document photo
    4. Updates applicant verification status
    """
    # Validate file type
    if file.content_type not in ['image/jpeg', 'image/png']:
        raise HTTPException(400, "Selfie must be JPEG or PNG")

    # Get applicant's ID document for face matching
    applicant = await get_applicant(db, applicant_id)
    id_document = await get_id_document(db, applicant_id)

    if not id_document:
        raise HTTPException(400, "Upload ID document before selfie")

    # Read file
    selfie_bytes = await file.read()

    # Run liveness check
    liveness_result = await liveness_service.detect_liveness(selfie_bytes)

    if not liveness_result.is_live:
        raise HTTPException(400, f"Liveness check failed: {liveness_result.reason}")

    # Get ID photo and run face matching
    id_photo_bytes = await storage_service.download(id_document.storage_key)
    match_result = await face_matching_service.compare_faces(
        selfie_bytes=selfie_bytes,
        id_photo_bytes=id_photo_bytes,
    )

    # Store selfie
    document = await create_document(
        db,
        applicant_id=applicant_id,
        document_type='selfie',
        is_selfie=True,
        liveness_result=liveness_result.model_dump(),
    )

    # Update applicant
    applicant.liveness_verified = liveness_result.is_live
    applicant.face_match_score = match_result.similarity
    applicant.face_match_status = match_result.status
    applicant.selfie_document_id = document.id

    await db.commit()

    return {
        "document_id": document.id,
        "liveness": liveness_result.model_dump(),
        "face_match": match_result.model_dump(),
    }
```

## Success Criteria

- [ ] Liveness service detects live vs photo-of-photo
- [ ] Face matching compares selfie to ID photo
- [ ] Similarity score returned (0-100)
- [ ] Match status: match, no_match, review
- [ ] API endpoint for selfie upload
- [ ] Applicant record updated with liveness status
- [ ] Quality issues identified (blur, lighting, pose)
- [ ] Tests with mock images

## Testing

```python
# Test with known images
@pytest.mark.asyncio
async def test_liveness_detects_live_face():
    """Test liveness detection with real selfie."""
    with open("tests/fixtures/live_selfie.jpg", "rb") as f:
        result = await liveness_service.detect_liveness(f.read())

    assert result.is_live is True
    assert result.confidence > 70

@pytest.mark.asyncio
async def test_liveness_rejects_photo_of_photo():
    """Test liveness detection rejects printed photo."""
    with open("tests/fixtures/photo_of_photo.jpg", "rb") as f:
        result = await liveness_service.detect_liveness(f.read())

    assert result.is_live is False
    assert "blurry" in result.issues or "Image" in str(result.reason)

@pytest.mark.asyncio
async def test_face_matching():
    """Test face matching with same person."""
    with open("tests/fixtures/selfie.jpg", "rb") as selfie:
        with open("tests/fixtures/id_photo.jpg", "rb") as id_photo:
            result = await face_matching_service.compare_faces(
                selfie.read(), id_photo.read()
            )

    assert result.match is True
    assert result.similarity > 80
```

## Questions?
If unclear about AWS Rekognition setup or image processing, ask first.
```

---

## Sprint 4: Observability Stack (Medium - 3-5 Days)

### Files to Upload:
1. `docs/IMPLEMENTATION_AUDIT.md`
2. `docs/implementation-guide/02_FOLDER_STRUCTURE_COMPLETE.md`
3. `README.md`
4. `backend/app/main.py`
5. `backend/app/config.py`

### Prompt (Copy This):

```
# CHAT TITLE: Production Hardening Sprint 4 - Observability Stack

## Context
I'm building GetClearance, an AI-native KYC/AML platform. The Implementation Audit identified observability as a medium-priority gap. Before scaling, we need proper monitoring, metrics, and tracing.

**Current Repo:** https://github.com/autorevai/getclearance

## What Exists (Read These First)
I've uploaded context files:

1. **IMPLEMENTATION_AUDIT.md** - Identifies observability gaps
2. **02_FOLDER_STRUCTURE_COMPLETE.md** - Directory tree
3. **README.md** - Project README
4. **main.py** - FastAPI entry point
5. **config.py** - Settings configuration

**Current state:**
- ⚠️ Sentry mentioned but not integrated
- ❌ No structured logging
- ❌ No metrics collection
- ❌ No distributed tracing
- ❌ No alerting

## What I Need You To Create

### Part 1: Structured Logging

**Files to create:**
1. `backend/app/logging_config.py` - Logging configuration
2. `backend/app/middleware/logging.py` - Request logging middleware

**Requirements:**
- JSON structured logs for log aggregation
- Request ID in all logs
- Tenant ID in all logs
- Log levels: DEBUG, INFO, WARNING, ERROR
- Don't log PII (mask sensitive fields)

### Part 2: Error Tracking (Sentry)

**Files to update:**
3. `backend/app/main.py` - Add Sentry integration
4. `backend/app/config.py` - Add Sentry DSN

**Requirements:**
- Capture all unhandled exceptions
- Attach user context (tenant_id, user_id)
- Attach request context (request_id, path)
- Performance monitoring (transaction tracing)

### Part 3: Metrics (Prometheus)

**Files to create:**
5. `backend/app/metrics.py` - Prometheus metrics
6. `backend/app/middleware/metrics.py` - Metrics middleware

**Metrics to track:**
- `http_requests_total` - Counter by method, path, status
- `http_request_duration_seconds` - Histogram
- `applicants_created_total` - Counter
- `screening_checks_total` - Counter by result (hit/clear)
- `documents_processed_total` - Counter by status
- `worker_jobs_total` - Counter by job type, status

### Part 4: Health Checks

**Files to create:**
7. `backend/app/api/health.py` - Enhanced health endpoints

**Endpoints:**
- `GET /health` - Simple liveness check
- `GET /health/ready` - Readiness check (DB, Redis)
- `GET /health/detailed` - Full status with metrics

## Integration Requirements

### Structured Logging:
```python
# logging_config.py
import logging
import json
import sys
from datetime import datetime

class JSONFormatter(logging.Formatter):
    def format(self, record):
        log_data = {
            "timestamp": datetime.utcnow().isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }

        # Add extra fields (request_id, tenant_id, etc.)
        if hasattr(record, 'request_id'):
            log_data['request_id'] = record.request_id
        if hasattr(record, 'tenant_id'):
            log_data['tenant_id'] = record.tenant_id

        # Add exception info
        if record.exc_info:
            log_data['exception'] = self.formatException(record.exc_info)

        return json.dumps(log_data)

def setup_logging(level: str = "INFO"):
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(JSONFormatter())

    logging.root.handlers = [handler]
    logging.root.setLevel(getattr(logging, level))

    # Silence noisy loggers
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("httpx").setLevel(logging.WARNING)
```

### Sentry Integration:
```python
# In main.py
import sentry_sdk
from sentry_sdk.integrations.fastapi import FastApiIntegration
from sentry_sdk.integrations.sqlalchemy import SqlalchemyIntegration
from sentry_sdk.integrations.redis import RedisIntegration

if settings.sentry_dsn:
    sentry_sdk.init(
        dsn=settings.sentry_dsn,
        integrations=[
            FastApiIntegration(transaction_style="endpoint"),
            SqlalchemyIntegration(),
            RedisIntegration(),
        ],
        traces_sample_rate=0.1,  # 10% of transactions
        profiles_sample_rate=0.1,
        environment=settings.environment,
        release=settings.app_version,
    )

# Add user context in middleware
@app.middleware("http")
async def sentry_context_middleware(request, call_next):
    with sentry_sdk.configure_scope() as scope:
        if hasattr(request.state, 'tenant_id'):
            scope.set_user({"id": str(request.state.tenant_id)})
        if hasattr(request.state, 'request_id'):
            scope.set_tag("request_id", request.state.request_id)

    return await call_next(request)
```

### Prometheus Metrics:
```python
# metrics.py
from prometheus_client import Counter, Histogram, Gauge, generate_latest

# HTTP metrics
http_requests_total = Counter(
    'http_requests_total',
    'Total HTTP requests',
    ['method', 'path', 'status']
)

http_request_duration = Histogram(
    'http_request_duration_seconds',
    'HTTP request duration',
    ['method', 'path'],
    buckets=[0.01, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0]
)

# Business metrics
applicants_total = Counter(
    'applicants_created_total',
    'Total applicants created',
    ['tenant_id']
)

screening_checks_total = Counter(
    'screening_checks_total',
    'Total screening checks',
    ['result']  # hit, clear, error
)

documents_processed_total = Counter(
    'documents_processed_total',
    'Total documents processed',
    ['document_type', 'status']
)

# Worker metrics
worker_jobs_total = Counter(
    'worker_jobs_total',
    'Total worker jobs',
    ['job_type', 'status']  # success, failure, retry
)

worker_jobs_in_progress = Gauge(
    'worker_jobs_in_progress',
    'Jobs currently being processed',
    ['job_type']
)
```

### Metrics Middleware:
```python
# middleware/metrics.py
import time
from starlette.middleware.base import BaseHTTPMiddleware
from app.metrics import http_requests_total, http_request_duration

class MetricsMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        start = time.time()
        response = await call_next(request)
        duration = time.time() - start

        # Record metrics
        path = request.url.path
        # Normalize path (replace IDs with placeholder)
        normalized_path = self._normalize_path(path)

        http_requests_total.labels(
            method=request.method,
            path=normalized_path,
            status=response.status_code
        ).inc()

        http_request_duration.labels(
            method=request.method,
            path=normalized_path
        ).observe(duration)

        return response

    def _normalize_path(self, path: str) -> str:
        """Replace UUIDs with placeholder for consistent metrics."""
        import re
        uuid_pattern = r'[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}'
        return re.sub(uuid_pattern, '{id}', path)
```

### Health Endpoints:
```python
# api/health.py
from fastapi import APIRouter, Depends
from sqlalchemy import text
from redis import Redis

router = APIRouter(tags=["health"])

@router.get("/health")
async def health():
    """Simple liveness check."""
    return {"status": "healthy"}

@router.get("/health/ready")
async def readiness(
    db: AsyncSession = Depends(get_db),
):
    """Readiness check - verify dependencies."""
    checks = {}

    # Check database
    try:
        await db.execute(text("SELECT 1"))
        checks["database"] = {"status": "ok"}
    except Exception as e:
        checks["database"] = {"status": "error", "error": str(e)}

    # Check Redis
    try:
        redis = Redis.from_url(settings.redis_url_str)
        redis.ping()
        checks["redis"] = {"status": "ok"}
    except Exception as e:
        checks["redis"] = {"status": "error", "error": str(e)}

    all_ok = all(c["status"] == "ok" for c in checks.values())

    return {
        "status": "ready" if all_ok else "not_ready",
        "checks": checks,
    }

@router.get("/health/detailed")
async def detailed_health():
    """Detailed health with metrics."""
    from prometheus_client import generate_latest

    return {
        "status": "healthy",
        "version": settings.app_version,
        "environment": settings.environment,
        "metrics_endpoint": "/metrics",
    }

@router.get("/metrics")
async def metrics():
    """Prometheus metrics endpoint."""
    from prometheus_client import generate_latest, CONTENT_TYPE_LATEST
    from starlette.responses import Response

    return Response(
        content=generate_latest(),
        media_type=CONTENT_TYPE_LATEST,
    )
```

## Config Updates:
```python
# config.py additions
sentry_dsn: str = Field(default="")
log_level: str = Field(default="INFO")
log_format: str = Field(default="json")  # json or text
metrics_enabled: bool = Field(default=True)
```

## Success Criteria

- [ ] Structured JSON logging enabled
- [ ] Request ID in all log messages
- [ ] Sentry captures errors with context
- [ ] Prometheus metrics exposed at /metrics
- [ ] Health endpoints return correct status
- [ ] Business metrics tracked (applicants, screening, etc.)
- [ ] No PII in logs

## Testing

```bash
# Check health endpoint
curl http://localhost:8000/health

# Check readiness
curl http://localhost:8000/health/ready

# Check metrics
curl http://localhost:8000/metrics

# Verify logs are JSON
docker logs backend 2>&1 | head -5 | jq .
```

## Questions?
If unclear about Prometheus setup or Sentry configuration, ask first.
```

---

## Sprint 5: Ongoing Monitoring (Medium - 3-4 Days)

### Files to Upload:
1. `docs/IMPLEMENTATION_AUDIT.md`
2. `docs/implementation-guide/02_FOLDER_STRUCTURE_COMPLETE.md`
3. `docs/implementation-guide/05_SUMSUB_CONTEXT.md`
4. `README.md`
5. `backend/app/workers/screening_worker.py`
6. `backend/app/services/screening.py`

### Prompt (Copy This):

```
# CHAT TITLE: Production Hardening Sprint 5 - Ongoing Monitoring

## Context
I'm building GetClearance, an AI-native KYC/AML platform (Sumsub clone). The Implementation Audit identified ongoing monitoring as a gap. Currently, we only screen applicants once - but sanctions lists update daily. We need continuous re-screening.

**Current Repo:** https://github.com/autorevai/getclearance

## What Exists (Read These First)
I've uploaded context files:

1. **IMPLEMENTATION_AUDIT.md** - Identifies ongoing monitoring as gap
2. **02_FOLDER_STRUCTURE_COMPLETE.md** - Directory tree
3. **05_SUMSUB_CONTEXT.md** - See ongoing monitoring section
4. **README.md** - Project README
5. **screening_worker.py** - Current screening worker
6. **screening.py** - Screening service

**Current state:**
- ✅ One-time screening on applicant creation
- ❌ No re-screening when lists update
- ❌ No scheduled monitoring
- ❌ No alerts when new hits found

**Sumsub Pattern (from docs):**
- Daily re-screening of approved applicants
- Alert when new sanctions/PEP match found
- Configurable monitoring frequency

## What I Need You To Create

### Part 1: Monitoring Service

**Files to create:**
1. `backend/app/services/monitoring.py` - Ongoing monitoring service

### Part 2: Monitoring Worker

**Files to create:**
2. `backend/app/workers/monitoring_worker.py` - Scheduled monitoring worker

### Part 3: Database Schema

**Migration to create:**
3. `backend/migrations/versions/20251201_004_add_monitoring.py`

**New table:**
```sql
CREATE TABLE monitoring_schedules (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID REFERENCES tenants(id) ON DELETE CASCADE,
    applicant_id UUID REFERENCES applicants(id) ON DELETE CASCADE,
    frequency VARCHAR(20) DEFAULT 'daily',  -- daily, weekly, monthly
    last_checked_at TIMESTAMPTZ,
    next_check_at TIMESTAMPTZ,
    enabled BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_monitoring_next_check
ON monitoring_schedules(next_check_at)
WHERE enabled = TRUE;
```

### Part 4: Webhook Events

**Files to update:**
4. `backend/app/services/webhook.py` - Add monitoring events

**New event types:**
- `monitoring.new_hit` - New screening hit found
- `monitoring.cleared` - Previously flagged applicant now clear
- `monitoring.check_completed` - Re-screening completed

## Integration Requirements

### Monitoring Service:
```python
# services/monitoring.py
from datetime import datetime, timedelta
from uuid import UUID

class MonitoringService:
    """Ongoing applicant monitoring service."""

    async def enable_monitoring(
        self,
        db: AsyncSession,
        applicant_id: UUID,
        frequency: str = "daily",
    ) -> MonitoringSchedule:
        """Enable ongoing monitoring for an applicant."""
        schedule = MonitoringSchedule(
            applicant_id=applicant_id,
            tenant_id=applicant.tenant_id,
            frequency=frequency,
            next_check_at=self._calculate_next_check(frequency),
            enabled=True,
        )
        db.add(schedule)
        await db.commit()
        return schedule

    async def get_due_checks(
        self,
        db: AsyncSession,
        limit: int = 100,
    ) -> list[MonitoringSchedule]:
        """Get applicants due for re-screening."""
        now = datetime.utcnow()
        result = await db.execute(
            select(MonitoringSchedule)
            .where(MonitoringSchedule.enabled == True)
            .where(MonitoringSchedule.next_check_at <= now)
            .order_by(MonitoringSchedule.next_check_at)
            .limit(limit)
        )
        return result.scalars().all()

    async def run_check(
        self,
        db: AsyncSession,
        schedule: MonitoringSchedule,
    ) -> MonitoringResult:
        """Run a monitoring check for one applicant."""
        applicant = await get_applicant(db, schedule.applicant_id)

        # Run screening
        result = await screening_service.check_individual(
            name=applicant.full_name,
            birth_date=applicant.date_of_birth,
            countries=[applicant.nationality],
        )

        # Check for new hits
        new_hits = self._find_new_hits(
            current_hits=result.hits,
            previous_hits=applicant.screening_hits,
        )

        # Update schedule
        schedule.last_checked_at = datetime.utcnow()
        schedule.next_check_at = self._calculate_next_check(schedule.frequency)

        await db.commit()

        # Send webhook if new hits
        if new_hits:
            await webhook_service.send_webhook(
                tenant_id=applicant.tenant_id,
                event_type="monitoring.new_hit",
                data={
                    "applicant_id": str(applicant.id),
                    "new_hits_count": len(new_hits),
                    "hits": [h.model_dump() for h in new_hits],
                },
            )

        return MonitoringResult(
            applicant_id=applicant.id,
            new_hits=new_hits,
            total_hits=len(result.hits),
        )

    def _calculate_next_check(self, frequency: str) -> datetime:
        """Calculate next check time based on frequency."""
        now = datetime.utcnow()
        if frequency == "daily":
            return now + timedelta(days=1)
        elif frequency == "weekly":
            return now + timedelta(weeks=1)
        elif frequency == "monthly":
            return now + timedelta(days=30)
        else:
            return now + timedelta(days=1)

    def _find_new_hits(
        self,
        current_hits: list,
        previous_hits: list,
    ) -> list:
        """Identify hits that weren't in previous check."""
        previous_ids = {h.matched_entity_id for h in previous_hits}
        return [h for h in current_hits if h.matched_entity_id not in previous_ids]

monitoring_service = MonitoringService()
```

### Monitoring Worker:
```python
# workers/monitoring_worker.py
from datetime import datetime
from app.services.monitoring import monitoring_service
from app.database import get_db_context

async def run_monitoring_batch(ctx: dict, batch_size: int = 100):
    """
    Process batch of applicants due for re-screening.

    Runs every hour via cron job.
    """
    logger = ctx.get("logger")
    logger.info("Starting monitoring batch")

    async with get_db_context() as db:
        # Get applicants due for check
        schedules = await monitoring_service.get_due_checks(db, limit=batch_size)

        if not schedules:
            logger.info("No applicants due for monitoring")
            return {"processed": 0}

        results = {
            "processed": 0,
            "new_hits": 0,
            "errors": 0,
        }

        for schedule in schedules:
            try:
                result = await monitoring_service.run_check(db, schedule)
                results["processed"] += 1
                results["new_hits"] += len(result.new_hits)

                if result.new_hits:
                    logger.warning(
                        f"New hits found for applicant {schedule.applicant_id}: "
                        f"{len(result.new_hits)} hits"
                    )
            except Exception as e:
                logger.error(f"Monitoring check failed: {e}")
                results["errors"] += 1

        logger.info(f"Monitoring batch complete: {results}")
        return results
```

### Worker Configuration:
```python
# In workers/config.py - add cron job
cron_jobs = [
    # Existing webhook cron...

    # Monitoring - run every hour
    cron(
        "app.workers.monitoring_worker.run_monitoring_batch",
        hour={0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12,
              13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23},
        minute=30,  # Run at :30 past each hour
    ),
]
```

### API Endpoints:
```python
# In api/v1/applicants.py - add monitoring endpoints

@router.post("/{applicant_id}/monitoring")
async def enable_monitoring(
    applicant_id: UUID,
    frequency: str = "daily",
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Enable ongoing monitoring for an applicant."""
    schedule = await monitoring_service.enable_monitoring(
        db, applicant_id, frequency
    )
    return {"schedule_id": schedule.id, "next_check_at": schedule.next_check_at}

@router.delete("/{applicant_id}/monitoring")
async def disable_monitoring(
    applicant_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Disable ongoing monitoring for an applicant."""
    await monitoring_service.disable_monitoring(db, applicant_id)
    return {"status": "disabled"}

@router.get("/{applicant_id}/monitoring/history")
async def get_monitoring_history(
    applicant_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get monitoring check history for an applicant."""
    history = await monitoring_service.get_history(db, applicant_id)
    return {"items": history}
```

## Success Criteria

- [ ] Monitoring can be enabled per applicant
- [ ] Cron job runs hourly for due checks
- [ ] New hits trigger webhook notifications
- [ ] Monitoring history tracked
- [ ] API endpoints work
- [ ] Configurable frequency (daily/weekly/monthly)
- [ ] Tests for monitoring logic

## Testing

```python
@pytest.mark.asyncio
async def test_enable_monitoring(client, auth_headers, test_applicant):
    """Test enabling monitoring."""
    response = await client.post(
        f"/api/v1/applicants/{test_applicant.id}/monitoring",
        json={"frequency": "daily"},
        headers=auth_headers,
    )
    assert response.status_code == 200
    assert "next_check_at" in response.json()

@pytest.mark.asyncio
async def test_monitoring_detects_new_hit(db, test_applicant, mock_screening):
    """Test monitoring detects new screening hits."""
    # First check - no hits
    mock_screening.return_value = ScreeningResult(hits=[])
    await monitoring_service.run_check(db, schedule)

    # Second check - new hit
    mock_screening.return_value = ScreeningResult(hits=[MockHit()])
    result = await monitoring_service.run_check(db, schedule)

    assert len(result.new_hits) == 1
```

## Questions?
If unclear about cron job setup or webhook patterns, ask first.
```

---

## Sprint Summary

| Sprint | Focus | Duration | Priority | Depends On |
|--------|-------|----------|----------|------------|
| Sprint 1 | Rate Limiting & API Security | 2-3 days | Critical | - |
| Sprint 2 | Test Coverage 80%+ | 3-5 days | Critical | Sprint 1 |
| Sprint 3 | Liveness & Face Matching | 5-7 days | Critical | Sprint 2 |
| Sprint 4 | Observability Stack | 3-5 days | Medium | Sprint 1 |
| Sprint 5 | Ongoing Monitoring | 3-4 days | Medium | Sprint 2 |

**Total Estimated Time: 16-24 days (~3-4 two-week sprints)**

**Parallel Work Possible:**
- Sprint 4 can run in parallel with Sprint 3
- Sprint 5 can run in parallel with Sprint 4

---

## Files Created/Updated by Sprint

### Sprint 1: Rate Limiting & API Security
**Create:**
- `backend/app/middleware/rate_limit.py`
- `backend/app/middleware/request_id.py`
- `backend/app/middleware/logging.py`
- `backend/app/services/api_keys.py`
- `backend/app/api/v1/api_keys.py`
- `backend/migrations/versions/20251201_002_add_api_keys.py`

**Update:**
- `backend/app/main.py`
- `backend/app/config.py`

### Sprint 2: Test Coverage
**Create:**
- `backend/tests/api/__init__.py`
- `backend/tests/api/test_applicants.py`
- `backend/tests/api/test_documents.py`
- `backend/tests/api/test_screening.py`
- `backend/tests/api/test_cases.py`
- `backend/tests/api/test_ai.py`
- `backend/tests/integration/test_database.py`
- `backend/tests/integration/test_multi_tenant.py`
- `backend/tests/e2e/__init__.py`
- `backend/tests/e2e/test_kyc_flow.py`
- `backend/tests/e2e/test_screening_flow.py`

**Update:**
- `backend/tests/conftest.py`

### Sprint 3: Liveness & Face Matching
**Create:**
- `backend/app/services/liveness.py`
- `backend/app/services/face_matching.py`
- `backend/app/schemas/liveness.py`
- `backend/migrations/versions/20251201_003_add_liveness.py`

**Update:**
- `backend/app/api/v1/documents.py`
- `backend/app/workers/document_worker.py`
- `backend/app/config.py`

### Sprint 4: Observability Stack
**Create:**
- `backend/app/logging_config.py`
- `backend/app/metrics.py`
- `backend/app/middleware/metrics.py`
- `backend/app/api/health.py`

**Update:**
- `backend/app/main.py`
- `backend/app/config.py`
- `backend/app/middleware/logging.py`

### Sprint 5: Ongoing Monitoring
**Create:**
- `backend/app/services/monitoring.py`
- `backend/app/workers/monitoring_worker.py`
- `backend/migrations/versions/20251201_004_add_monitoring.py`

**Update:**
- `backend/app/services/webhook.py`
- `backend/app/workers/config.py`
- `backend/app/api/v1/applicants.py`

---

## Pre-Sprint Checklist

Before starting EACH sprint:

- [ ] Completed previous sprint(s)
- [ ] Downloaded latest code from repo
- [ ] Read IMPLEMENTATION_AUDIT.md for context
- [ ] Uploaded required files to chat
- [ ] Copied complete prompt (not partial)
- [ ] Understand what you're asking for
- [ ] Ready to review and test output

**Time investment:** 15 minutes prep per sprint
**Time saved:** 4-6 hours debugging per sprint

---

**Copy the prompts exactly as shown - they're structured for success!**
