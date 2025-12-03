# Backend Security Sprint Prompts - Production Readiness
**Purpose:** Ready-to-use prompts for each backend security sprint to make GetClearance production-ready
**How to Use:** Copy the entire prompt for the sprint you're starting

---

## Current Reality

The backend has solid architecture (FastAPI, PostgreSQL, Auth0) but **critical security features are incomplete**:

- **Audit logging model exists but is NEVER called** (25+ TODO comments)
- **PII stored in plaintext** (comments say "encrypted" but it's not)
- **No rate limiting** (API open to abuse)
- **Debug endpoints exposed** (information disclosure)
- **Missing compliance features** (no SAR, no data deletion)

**Backend Status:** Functional but NOT production-ready
**Security Status:** Prototype-level - fails compliance audit

---

## Sprint Overview

| Sprint | Focus | Duration | Priority | Status |
|--------|-------|----------|----------|--------|
| **Sprint 1** | Audit Logging Implementation | 2-3 days | CRITICAL | ✅ **COMPLETE** |
| **Sprint 2** | Rate Limiting & Security Hardening | 1-2 days | CRITICAL | ✅ **COMPLETE** |
| **Sprint 3** | PII Encryption | 2-3 days | CRITICAL | ✅ **COMPLETE** |
| **Sprint 4** | Missing Endpoints & Field Fixes | 1-2 days | HIGH | ✅ **COMPLETE** |
| **Sprint 5** | GDPR Compliance Features | 2-3 days | HIGH | ✅ **COMPLETE** |
| **Sprint 6** | Monitoring & Alerting | 1-2 days | MEDIUM | ✅ **COMPLETE** |

**Total Estimated: ALL SPRINTS COMPLETE - Production Ready! 🎉**

---

## Files to Upload to EVERY Sprint Chat

Before starting ANY sprint, upload these files:

1. `TECHNICAL_IMPLEMENTATION_GUIDE.md` - Backend patterns
2. `02_FOLDER_STRUCTURE_COMPLETE.md` - Directory tree
3. `README.md` (from your getclearance repo)
4. The specific files mentioned in each sprint

---

## Sprint 1: Audit Logging Implementation ✅ COMPLETE

### Completion Summary
**Completed:** December 2, 2025
**Files Created:**
- `backend/app/services/audit.py` - Audit service with `record_audit_log()`, `verify_audit_chain()`, and convenience functions
- `backend/tests/test_audit.py` - 12 passing tests for audit functionality

**Files Updated:**
- `backend/app/dependencies.py` - Added `RequestContext` and `AuditContext` for IP/user-agent capture
- `backend/app/api/v1/applicants.py` - Audit logging for create, update, review, step_complete
- `backend/app/api/v1/cases.py` - Audit logging for create, resolve, add_note
- `backend/app/api/v1/screening.py` - Audit logging for resolve_hit + applicant flagging on true positive

**Test Results:** 185 tests passing (12 new audit tests)

### Original Sprint Details (For Reference)

### Files to Upload:
1. `backend/app/models/audit.py` - Existing audit model
2. `backend/app/api/v1/applicants.py` - Needs audit logging
3. `backend/app/api/v1/cases.py` - Needs audit logging
4. `backend/app/api/v1/screening.py` - Needs audit logging
5. `README.md` (from repo)

### Prompt (Copy This):

```
# CHAT TITLE: Backend Sprint 1 - Audit Logging Implementation

## Context
I'm building GetClearance, an AI-native KYC/AML platform. The backend has an audit logging model with chain-hashing for tamper evidence, but it's NEVER called in any endpoint. There are 25+ TODO comments saying "Create audit log entry" but none are implemented.

**Current Repo:** https://github.com/autorevai/getclearance

## What Exists (Read These First)
I've uploaded context files:

1. **audit.py** - Existing audit log model with chain hashing (READ THIS FIRST)
2. **applicants.py** - Applicant endpoints with TODO comments for audit
3. **cases.py** - Case endpoints with TODO comments for audit
4. **screening.py** - Screening endpoints with TODO comments for audit
5. **README.md** - Project README

**Current state:**
- AuditLog model exists in `backend/app/models/audit.py`
- Model has `previous_hash` field for chain verification
- Model has `entity_type`, `entity_id`, `action`, `actor_id`, `old_value`, `new_value`
- NO audit logs are ever created - all TODO comments

**Files with TODO audit comments:**
- `applicants.py`: Lines 221-223, 267, 325, 383 (create, update, review, delete)
- `cases.py`: Lines 249, 345, 544 (create, resolve, add note)
- `screening.py`: Lines 542-544 (resolve hit)

## What I Need You To Do

### Part 1: Create Audit Service

**File to create:** `backend/app/services/audit.py`

**Requirements:**
1. Function to create audit log entries
2. Automatically calculate chain hash from previous entry
3. Support for all entity types (applicant, case, screening_hit, document)
4. Include actor_id from JWT token
5. Store old/new values as JSONB
6. Timestamp with timezone

**Audit service pattern:**
```python
from datetime import datetime
from uuid import UUID
import hashlib
import json
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.audit import AuditLog

async def record_audit_log(
    db: AsyncSession,
    tenant_id: UUID,
    entity_type: str,  # 'applicant', 'case', 'screening_hit', 'document'
    entity_id: UUID,
    action: str,  # 'created', 'updated', 'reviewed', 'resolved', 'deleted'
    actor_id: UUID,
    old_value: dict | None = None,
    new_value: dict | None = None,
    ip_address: str | None = None,
    user_agent: str | None = None,
) -> AuditLog:
    """
    Create tamper-evident audit log entry with chain hashing.
    """
    # Get previous log entry for this tenant to calculate chain hash
    prev_log = await db.execute(
        select(AuditLog)
        .where(AuditLog.tenant_id == tenant_id)
        .order_by(AuditLog.created_at.desc())
        .limit(1)
    )
    prev_entry = prev_log.scalar_one_or_none()

    # Calculate chain hash
    previous_hash = prev_entry.current_hash if prev_entry else "GENESIS"

    # Create hash of current entry
    hash_input = json.dumps({
        "previous_hash": previous_hash,
        "entity_type": entity_type,
        "entity_id": str(entity_id),
        "action": action,
        "actor_id": str(actor_id),
        "timestamp": datetime.utcnow().isoformat(),
    }, sort_keys=True)
    current_hash = hashlib.sha256(hash_input.encode()).hexdigest()

    # Create log entry
    log_entry = AuditLog(
        tenant_id=tenant_id,
        entity_type=entity_type,
        entity_id=entity_id,
        action=action,
        actor_id=actor_id,
        old_value=old_value,
        new_value=new_value,
        previous_hash=previous_hash,
        current_hash=current_hash,
        ip_address=ip_address,
        user_agent=user_agent,
    )

    db.add(log_entry)
    await db.flush()  # Get ID without committing

    return log_entry
```

### Part 2: Update applicants.py

**Replace ALL TODO audit comments with actual calls.**

**Locations to update:**

1. **Create applicant (line ~221-223):**
```python
# REPLACE THIS:
# TODO: Initialize workflow steps based on workflow_id
# TODO: Trigger initial screening
# TODO: Create audit log entry

# WITH THIS:
from app.services.audit import record_audit_log

await record_audit_log(
    db=db,
    tenant_id=user.tenant_id,
    entity_type="applicant",
    entity_id=applicant.id,
    action="created",
    actor_id=UUID(user.id),
    new_value=data.model_dump(mode='json'),
    ip_address=request.client.host if request.client else None,
)
```

2. **Update applicant (line ~267):**
```python
await record_audit_log(
    db=db,
    tenant_id=user.tenant_id,
    entity_type="applicant",
    entity_id=applicant.id,
    action="updated",
    actor_id=UUID(user.id),
    old_value=old_values,  # Capture before update
    new_value=data.model_dump(mode='json', exclude_unset=True),
)
```

3. **Review applicant (line ~325):**
```python
await record_audit_log(
    db=db,
    tenant_id=user.tenant_id,
    entity_type="applicant",
    entity_id=applicant.id,
    action="reviewed",
    actor_id=UUID(user.id),
    old_value={"status": old_status, "risk_level": old_risk},
    new_value={"status": data.decision, "notes": data.notes},
)
```

4. **Delete applicant (line ~383):**
```python
await record_audit_log(
    db=db,
    tenant_id=user.tenant_id,
    entity_type="applicant",
    entity_id=applicant_id,
    action="deleted",
    actor_id=UUID(user.id),
    old_value=applicant_data,  # Store full record before deletion
)
```

### Part 3: Update cases.py

**Locations to update:**

1. **Create case (line ~249):**
```python
await record_audit_log(
    db=db,
    tenant_id=user.tenant_id,
    entity_type="case",
    entity_id=case.id,
    action="created",
    actor_id=UUID(user.id),
    new_value={
        "subject_type": data.subject_type,
        "subject_id": str(data.subject_id),
        "case_type": data.case_type,
        "priority": data.priority,
    },
)
```

2. **Resolve case (line ~345):**
```python
await record_audit_log(
    db=db,
    tenant_id=user.tenant_id,
    entity_type="case",
    entity_id=case.id,
    action="resolved",
    actor_id=UUID(user.id),
    old_value={"status": old_status},
    new_value={"status": "resolved", "resolution": data.resolution, "notes": data.notes},
)
```

3. **Add note (line ~544):**
```python
await record_audit_log(
    db=db,
    tenant_id=user.tenant_id,
    entity_type="case",
    entity_id=case.id,
    action="note_added",
    actor_id=UUID(user.id),
    new_value={"note_id": str(note.id), "content_preview": data.content[:100]},
)
```

### Part 4: Update screening.py

**Location to update:**

1. **Resolve hit (line ~542-544):**
```python
# REPLACE THIS:
# TODO: If confirmed_true, update applicant flags
# TODO: Create case if needed
# TODO: Create audit log entry

# WITH THIS:
await record_audit_log(
    db=db,
    tenant_id=user.tenant_id,
    entity_type="screening_hit",
    entity_id=hit.id,
    action="resolved",
    actor_id=UUID(user.id),
    old_value={"resolution_status": old_resolution},
    new_value={
        "resolution_status": data.resolution,
        "notes": data.notes,
        "is_true_positive": data.resolution == "confirmed_true",
    },
)

# Also implement the TODO for updating applicant flags:
if data.resolution == "confirmed_true":
    applicant = await db.get(Applicant, hit.applicant_id)
    if applicant:
        # Add to risk flags
        flags = applicant.flags or []
        flags.append({
            "type": hit.hit_type,
            "source": hit.list_source,
            "confirmed_at": datetime.utcnow().isoformat(),
            "hit_id": str(hit.id),
        })
        applicant.flags = flags
        applicant.risk_level = "high"

        # Audit the applicant flag update
        await record_audit_log(
            db=db,
            tenant_id=user.tenant_id,
            entity_type="applicant",
            entity_id=applicant.id,
            action="flagged",
            actor_id=UUID(user.id),
            new_value={"flag_added": hit.hit_type, "hit_id": str(hit.id)},
        )
```

### Part 5: Add Request Context Dependency

**File to update:** `backend/app/dependencies.py`

Add a dependency to capture request metadata for audit logs:

```python
from fastapi import Request

class RequestContext:
    def __init__(self, ip_address: str | None, user_agent: str | None):
        self.ip_address = ip_address
        self.user_agent = user_agent

async def get_request_context(request: Request) -> RequestContext:
    return RequestContext(
        ip_address=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent"),
    )
```

## Architecture Constraints

**All audit logs must:**
- Be created in the same transaction as the action
- Include chain hash for tamper evidence
- Store actor_id from authenticated user
- Include IP address and user agent when available
- Never be updated or deleted (append-only)

**Database considerations:**
- AuditLog table should NOT have RLS (admins need full access)
- Index on `tenant_id`, `entity_type`, `entity_id`, `created_at`
- Consider partitioning by month for large tenants

## Success Criteria

- [ ] `record_audit_log()` function created in `services/audit.py`
- [ ] All 4 applicant operations create audit logs
- [ ] All 3 case operations create audit logs
- [ ] Screening hit resolution creates audit log
- [ ] Confirmed true positive updates applicant flags
- [ ] Chain hashing works (verify with test)
- [ ] No more TODO audit comments in codebase
- [ ] IP address and user agent captured

## Testing

After implementation:
```bash
# Run tests
cd backend
pytest tests/test_audit.py -v

# Manual verification
# 1. Create an applicant via API
# 2. Query audit_logs table
# 3. Verify chain hash links to previous entry
# 4. Verify actor_id matches authenticated user
```

## Migration (if needed)

If AuditLog table needs updates:
```bash
alembic revision --autogenerate -m "Add audit log indexes"
alembic upgrade head
```

## Questions?
If unclear about existing audit model or endpoint locations, ask first.
```

---

## Sprint 2: Rate Limiting & Security Hardening ✅ COMPLETE

### Completion Summary
**Completed:** December 2, 2025
**Files Created:**
- `backend/scripts/generate_dev_token.py` - Dev token generator for local API testing

**Files Updated:**
- `backend/app/main.py` - Added rate limiting (slowapi), security headers middleware, request ID middleware
- `backend/app/api/v1/auth.py` - Debug endpoints moved to dev-only router (only included in development mode)
- `backend/app/dependencies.py` - Dev mode auth bypass now requires explicit dev token format
- `backend/requirements.txt` - Added slowapi==0.1.9

**Security Features Implemented:**
1. **Rate Limiting** - 200 req/minute default, per-user or per-IP based
2. **Security Headers Middleware** - X-Content-Type-Options, X-Frame-Options, X-XSS-Protection, Referrer-Policy, CSP, HSTS (production)
3. **Request ID Middleware** - UUID tracking via X-Request-ID header
4. **Debug Endpoints Protected** - Only available in development mode
5. **Dev Auth Bypass Fixed** - Now requires explicit `dev_` prefixed token format

**Dev Token Format:**
```
dev_{user_id}_{tenant_id}_{role}
Example: dev_testuser_00000000-0000-0000-0000-000000000001_admin
```

**Test Results:** 185 tests passing

### Original Sprint Details (For Reference)

### Why This Sprint?
The API has NO rate limiting (TODO in `main.py`) and debug endpoints are exposed that leak user/tenant information.

**Security Risk:**
- Brute force attacks on authentication
- DDoS vulnerability
- Information disclosure via `/debug/*` endpoints

### Files to Upload:
1. `backend/app/main.py` - Main app with TODO for rate limiting
2. `backend/app/api/v1/auth.py` - Debug endpoints to remove
3. `backend/app/dependencies.py` - Auth bypass in dev mode
4. `README.md` (from repo)

### Prompt (Copy This):

```
# CHAT TITLE: Backend Sprint 2 - Rate Limiting & Security Hardening

## Context
I'm building GetClearance, an AI-native KYC/AML platform. The API has no rate limiting and exposes debug endpoints that leak sensitive information.

**Current Repo:** https://github.com/autorevai/getclearance

## What Exists (Read These First)
I've uploaded context files:

1. **main.py** - FastAPI app with `# TODO: Add rate limiting middleware`
2. **auth.py** - Contains `/debug/token-claims`, `/debug/user-lookup`, `/debug/applicants-count`
3. **dependencies.py** - Returns mock admin token in dev mode if Auth0 not configured
4. **README.md** - Project README

**Current problems:**
1. Line 93 in main.py: `# TODO: Add rate limiting middleware`
2. auth.py has unprotected debug endpoints anyone can access
3. dependencies.py line 159-171 returns admin token for ANY request if in dev mode

## What I Need You To Do

### Part 1: Add Rate Limiting Middleware

**Install dependency:**
```bash
pip install slowapi
```

**Add to requirements.txt:**
```
slowapi==0.1.9
```

**Update main.py:**

```python
# Add imports
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware

# Create limiter
limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter

# Add exception handler
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# Add middleware
app.add_middleware(SlowAPIMiddleware)
```

**Apply rate limits to sensitive endpoints:**

```python
# In auth.py or create a decorator
from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)

# Login endpoint - strict limit
@router.post("/token")
@limiter.limit("5/minute")  # 5 attempts per minute
async def login(request: Request, ...):
    ...

# Screening endpoint - moderate limit (expensive operation)
@router.post("/screening/check")
@limiter.limit("30/minute")  # 30 checks per minute
async def run_screening(request: Request, ...):
    ...

# AI endpoints - moderate limit (expensive)
@router.post("/ai/assistant")
@limiter.limit("20/minute")
async def ask_assistant(request: Request, ...):
    ...

# Standard CRUD - higher limit
@router.get("/applicants")
@limiter.limit("100/minute")
async def list_applicants(request: Request, ...):
    ...
```

**Rate limit configuration by endpoint type:**
| Endpoint Type | Limit | Reason |
|---------------|-------|--------|
| Authentication | 5/min | Prevent brute force |
| Screening checks | 30/min | Expensive API calls |
| AI endpoints | 20/min | Claude API costs |
| CRUD operations | 100/min | Normal usage |
| Health checks | 1000/min | Monitoring |

### Part 2: Remove or Protect Debug Endpoints

**Option A: Remove completely (RECOMMENDED for production):**

Delete these routes from `auth.py`:
```python
# DELETE THESE:
@router.get("/debug/token-claims")
@router.get("/debug/user-lookup")
@router.get("/debug/applicants-count")
```

**Option B: Protect with admin-only access:**

```python
from app.dependencies import get_admin_user

@router.get("/debug/token-claims")
async def debug_token_claims(
    user: TokenPayload = Depends(get_admin_user),  # Admin only
):
    # Only accessible to admin users
    ...
```

**Create admin dependency:**
```python
# In dependencies.py
async def get_admin_user(
    user: TokenPayload = Depends(get_current_user),
) -> TokenPayload:
    if "admin:*" not in user.permissions:
        raise HTTPException(
            status_code=403,
            detail="Admin access required"
        )
    return user
```

### Part 3: Fix Development Mode Auth Bypass

**Current dangerous code in dependencies.py (lines 159-171):**
```python
# Skip validation in development if no Auth0 configured
if settings.is_development() and not settings.auth0_domain:
    return TokenPayload(
        sub="dev-user-123",
        ...
        role="admin",  # Always admin in dev
        permissions=["read:applicants", "write:applicants", "admin:*"],
    )
```

**Fix:**

```python
# In dependencies.py

async def get_current_user(
    authorization: str = Header(..., alias="Authorization"),
    db: AsyncSession = Depends(get_db),
) -> TokenPayload:
    """
    Validate JWT token and return user payload.
    """
    # NEVER skip auth validation - even in development
    if not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=401,
            detail="Invalid authorization header format"
        )

    token = authorization.split(" ")[1]

    try:
        # Always validate the token
        payload = await validate_jwt_token(token)
        return payload
    except JWTError as e:
        raise HTTPException(
            status_code=401,
            detail=f"Invalid token: {str(e)}"
        )

# For local development, use a proper dev token generator script instead:
# python -m scripts.generate_dev_token --email dev@test.com --role admin
```

**Create dev token generator script:**
```python
# backend/scripts/generate_dev_token.py
import jwt
import click
from datetime import datetime, timedelta
from app.config import settings

@click.command()
@click.option("--email", required=True, help="Developer email")
@click.option("--role", default="admin", help="User role")
@click.option("--tenant-id", default="00000000-0000-0000-0000-000000000001")
def generate_dev_token(email: str, role: str, tenant_id: str):
    """Generate a development JWT token."""

    payload = {
        "sub": f"dev|{email}",
        "email": email,
        "tenant_id": tenant_id,
        "role": role,
        "permissions": ["read:applicants", "write:applicants", "admin:*"],
        "iat": datetime.utcnow(),
        "exp": datetime.utcnow() + timedelta(days=30),
    }

    token = jwt.encode(payload, settings.secret_key, algorithm="HS256")

    print(f"\nDevelopment Token (valid for 30 days):\n")
    print(token)
    print(f"\nUsage:")
    print(f'curl -H "Authorization: Bearer {token}" http://localhost:8000/api/v1/applicants')

if __name__ == "__main__":
    generate_dev_token()
```

### Part 4: Add Security Headers Middleware

**Add to main.py:**

```python
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)

        # Security headers
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        response.headers["Content-Security-Policy"] = "default-src 'self'"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"

        # Remove server header
        if "server" in response.headers:
            del response.headers["server"]

        return response

# Add middleware
app.add_middleware(SecurityHeadersMiddleware)
```

### Part 5: Add Request ID Middleware

**Fix the TODO in main.py line 94-95:**

```python
import uuid
from contextvars import ContextVar

request_id_var: ContextVar[str] = ContextVar("request_id", default="")

class RequestIDMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        request_id = request.headers.get("X-Request-ID", str(uuid.uuid4()))
        request_id_var.set(request_id)

        response = await call_next(request)
        response.headers["X-Request-ID"] = request_id

        return response

# Add middleware
app.add_middleware(RequestIDMiddleware)
```

## Architecture Constraints

**Rate limiting must:**
- Use Redis backend for distributed rate limiting (production)
- Fall back to in-memory for development
- Return 429 Too Many Requests with Retry-After header
- Log rate limit violations for security monitoring

**Security headers must:**
- Be applied to ALL responses
- Include HSTS for HTTPS enforcement
- Prevent clickjacking and XSS

## Success Criteria

- [ ] Rate limiting middleware added
- [ ] Sensitive endpoints have appropriate limits
- [ ] Debug endpoints removed or protected
- [ ] Dev mode auth bypass removed
- [ ] Dev token generator script created
- [ ] Security headers middleware added
- [ ] Request ID middleware added
- [ ] No TODO comments remaining in main.py

## Testing

After implementation:
```bash
# Test rate limiting
for i in {1..10}; do
  curl -X POST http://localhost:8000/api/v1/auth/token \
    -H "Content-Type: application/json" \
    -d '{"email": "test@test.com", "password": "wrong"}'
done
# Should get 429 after 5 requests

# Test debug endpoints removed
curl http://localhost:8000/api/v1/auth/debug/token-claims
# Should get 404

# Test security headers
curl -I http://localhost:8000/health
# Should see X-Content-Type-Options, X-Frame-Options, etc.

# Test request ID
curl -I http://localhost:8000/health
# Should see X-Request-ID header
```

## Questions?
If unclear about rate limit values or middleware order, ask first.
```

---

## Sprint 3: PII Encryption ✅ COMPLETE

### Completion Summary
**Completed:** December 2, 2025
**Files Created:**
- `backend/app/services/encryption.py` - Fernet (AES-128-CBC) encryption service with PBKDF2 key derivation
- `backend/app/models/types.py` - EncryptedString and EncryptedJSON SQLAlchemy types
- `backend/migrations/versions/20251202_004_add_pii_encryption.py` - Schema migration for encrypted columns
- `backend/scripts/migrate_encrypt_pii.py` - One-time PII data migration script
- `backend/tests/test_encryption.py` - 22 tests for encryption functionality

**Files Updated:**
- `backend/app/config.py` - Added `encryption_key` and `encryption_salt` settings
- `backend/app/models/applicant.py` - PII fields now use EncryptedString type, added email_hash for lookups
- `backend/requirements.txt` - Added cryptography package

**Encrypted Fields:**
- `email` - EncryptedString(512)
- `phone` - EncryptedString(256)
- `first_name` - EncryptedString(512)
- `last_name` - EncryptedString(512)
- `email_hash` - SHA-256 hash for searchable lookups

**Security Features:**
1. Fernet encryption (AES-128-CBC with HMAC)
2. PBKDF2 key derivation with 100,000 iterations
3. Transparent encrypt/decrypt via SQLAlchemy TypeDecorator
4. Legacy plaintext detection for graceful migration
5. Key rotation support

**Test Results:** 207 tests passing (22 new encryption tests)

**Post-Deployment Steps:**
1. Set `ENCRYPTION_KEY` env var (generate with: `openssl rand -hex 32`)
2. Run schema migration: `alembic upgrade head`
3. Run PII migration: `python -m scripts.migrate_encrypt_pii`

### Original Sprint Details (For Reference)

### Why This Sprint?
The applicant model has comments saying "encrypted at rest via PostgreSQL" but NO encryption is actually implemented. PII (email, phone, SSN, names) is stored in plaintext.

**Compliance Risk:** GDPR Article 32, CCPA, and most KYC regulations require encryption of personal data.

### Files to Upload:
1. `backend/app/models/applicant.py` - PII fields (plaintext)
2. `backend/app/config.py` - Need encryption key
3. `README.md` (from repo)

### Prompt (Copy This):

```
# CHAT TITLE: Backend Sprint 3 - PII Encryption

## Context
I'm building GetClearance, an AI-native KYC/AML platform. The applicant model claims "encrypted at rest via PostgreSQL" but the fields are actually plaintext. I need to implement real encryption for PII.

**Current Repo:** https://github.com/autorevai/getclearance

## What Exists (Read These First)
I've uploaded context files:

1. **applicant.py** - Model with plaintext PII fields and misleading comments
2. **config.py** - Settings, needs encryption key
3. **README.md** - Project README

**Current misleading comments in applicant.py:**
```python
# Personal info (encrypted at rest via PostgreSQL)
email: Mapped[str | None] = mapped_column(String(255))
phone: Mapped[str | None] = mapped_column(String(50))
first_name: Mapped[str | None] = mapped_column(String(255))
last_name: Mapped[str | None] = mapped_column(String(255))
```

**Reality:** These are NOT encrypted - they're plaintext strings.

## What I Need You To Do

### Part 1: Create Encryption Service

**Install dependency:**
```bash
pip install cryptography
```

**Add to requirements.txt:**
```
cryptography==41.0.7
```

**File to create:** `backend/app/services/encryption.py`

```python
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
import base64
import os
from app.config import settings

class EncryptionService:
    """
    Application-level encryption for PII fields.
    Uses Fernet (AES-128-CBC with HMAC).
    """

    def __init__(self):
        self._fernet = self._create_fernet()

    def _create_fernet(self) -> Fernet:
        """Create Fernet instance from encryption key."""
        # Derive key from secret using PBKDF2
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=settings.encryption_salt.encode(),
            iterations=100000,
        )
        key = base64.urlsafe_b64encode(
            kdf.derive(settings.encryption_key.encode())
        )
        return Fernet(key)

    def encrypt(self, plaintext: str | None) -> str | None:
        """Encrypt a string value. Returns None if input is None."""
        if plaintext is None:
            return None
        return self._fernet.encrypt(plaintext.encode()).decode()

    def decrypt(self, ciphertext: str | None) -> str | None:
        """Decrypt a string value. Returns None if input is None."""
        if ciphertext is None:
            return None
        try:
            return self._fernet.decrypt(ciphertext.encode()).decode()
        except Exception:
            # If decryption fails, might be legacy plaintext data
            # Log warning and return as-is for migration period
            return ciphertext

# Singleton instance
encryption_service = EncryptionService()

def encrypt_pii(value: str | None) -> str | None:
    """Encrypt a PII field value."""
    return encryption_service.encrypt(value)

def decrypt_pii(value: str | None) -> str | None:
    """Decrypt a PII field value."""
    return encryption_service.decrypt(value)
```

### Part 2: Add Encryption Config

**Update config.py:**

```python
class Settings(BaseSettings):
    # ... existing fields ...

    # Encryption
    encryption_key: str = Field(
        default="CHANGE-ME-GENERATE-WITH-OPENSSL",
        description="Key for PII encryption (use: openssl rand -hex 32)"
    )
    encryption_salt: str = Field(
        default="getclearance-pii-salt-v1",
        description="Salt for key derivation"
    )
```

**Add to .env.example:**
```bash
# Encryption (REQUIRED for production)
# Generate with: openssl rand -hex 32
ENCRYPTION_KEY=your-32-byte-hex-key-here
ENCRYPTION_SALT=getclearance-pii-salt-v1
```

### Part 3: Create Encrypted String Type

**File to create:** `backend/app/models/types.py`

```python
from sqlalchemy import TypeDecorator, String
from app.services.encryption import encrypt_pii, decrypt_pii

class EncryptedString(TypeDecorator):
    """
    SQLAlchemy type that encrypts/decrypts on database read/write.
    """
    impl = String
    cache_ok = True

    def __init__(self, length: int = 1024):
        # Encrypted values are longer than plaintext
        super().__init__(length)

    def process_bind_param(self, value, dialect):
        """Encrypt before writing to database."""
        return encrypt_pii(value)

    def process_result_value(self, value, dialect):
        """Decrypt after reading from database."""
        return decrypt_pii(value)
```

### Part 4: Update Applicant Model

**Update applicant.py:**

```python
from app.models.types import EncryptedString

class Applicant(TenantModel):
    __tablename__ = "applicants"

    # ... existing fields ...

    # Personal info (ENCRYPTED at application level)
    email: Mapped[str | None] = mapped_column(EncryptedString(512))
    phone: Mapped[str | None] = mapped_column(EncryptedString(256))
    first_name: Mapped[str | None] = mapped_column(EncryptedString(512))
    last_name: Mapped[str | None] = mapped_column(EncryptedString(512))

    # Additional PII fields that need encryption
    ssn: Mapped[str | None] = mapped_column(EncryptedString(256))
    passport_number: Mapped[str | None] = mapped_column(EncryptedString(256))
    address_line_1: Mapped[str | None] = mapped_column(EncryptedString(1024))
    address_line_2: Mapped[str | None] = mapped_column(EncryptedString(1024))

    # Non-PII fields stay as regular strings
    nationality: Mapped[str | None] = mapped_column(String(100))
    status: Mapped[str] = mapped_column(String(50), default="pending")
```

### Part 5: Create Migration for Existing Data

**Create migration script:**

```python
# backend/scripts/migrate_encrypt_pii.py
"""
One-time migration to encrypt existing plaintext PII data.
Run ONCE after deploying encryption feature.
"""
import asyncio
from sqlalchemy import select, update
from app.database import async_session_maker
from app.models.applicant import Applicant
from app.services.encryption import encrypt_pii

async def migrate_pii():
    """Encrypt all existing plaintext PII."""
    async with async_session_maker() as db:
        # Fetch all applicants
        result = await db.execute(select(Applicant))
        applicants = result.scalars().all()

        migrated = 0
        for applicant in applicants:
            # Check if already encrypted (Fernet tokens start with 'gAAAAA')
            if applicant.email and not applicant.email.startswith('gAAAAA'):
                # This is plaintext, encrypt it
                applicant.email = encrypt_pii(applicant.email)
                applicant.phone = encrypt_pii(applicant.phone)
                applicant.first_name = encrypt_pii(applicant.first_name)
                applicant.last_name = encrypt_pii(applicant.last_name)
                migrated += 1

        await db.commit()
        print(f"Migrated {migrated} applicants")

if __name__ == "__main__":
    asyncio.run(migrate_pii())
```

### Part 6: Update Search to Handle Encrypted Fields

**Problem:** You can't search encrypted fields with SQL LIKE.

**Solution:** Create a searchable hash column:

```python
# In applicant.py
import hashlib

class Applicant(TenantModel):
    # ... existing fields ...

    # Searchable hash of email (for lookups)
    email_hash: Mapped[str | None] = mapped_column(String(64), index=True)

    def set_email(self, email: str | None):
        """Set email and update hash for searching."""
        self.email = email
        if email:
            self.email_hash = hashlib.sha256(email.lower().encode()).hexdigest()
        else:
            self.email_hash = None
```

**For search by name, use a separate search index table:**
```python
# Create a non-encrypted search index (contains only partial/hashed data)
class ApplicantSearchIndex(Base):
    __tablename__ = "applicant_search_index"

    applicant_id: Mapped[UUID] = mapped_column(ForeignKey("applicants.id"), primary_key=True)
    name_soundex: Mapped[str] = mapped_column(String(10))  # Phonetic matching
    name_metaphone: Mapped[str] = mapped_column(String(20))  # Better phonetic
    # DO NOT store actual names here
```

## Architecture Constraints

**Encryption must:**
- Use Fernet (AES-128-CBC with HMAC) for symmetric encryption
- Derive key using PBKDF2 with high iteration count
- Handle legacy plaintext during migration period
- NOT break existing API responses (decrypt transparently)

**Search considerations:**
- Direct SQL search on encrypted fields is impossible
- Use hash columns for exact match lookups
- Use phonetic indexes for fuzzy name search
- Consider dedicated search service for complex queries

## Success Criteria

- [ ] EncryptionService created with Fernet
- [ ] EncryptedString SQLAlchemy type created
- [ ] Applicant model updated to use EncryptedString
- [ ] Config updated with encryption key settings
- [ ] Migration script for existing data
- [ ] Email hash column for lookups
- [ ] API responses still return decrypted values
- [ ] New applicants are encrypted on create

## Testing

After implementation:
```bash
# Test encryption
python -c "
from app.services.encryption import encrypt_pii, decrypt_pii
encrypted = encrypt_pii('test@example.com')
print(f'Encrypted: {encrypted}')
print(f'Decrypted: {decrypt_pii(encrypted)}')
"

# Verify in database
psql -d getclearance -c "SELECT email FROM applicants LIMIT 1"
# Should see encrypted string like 'gAAAAABm...'

# Run migration
python -m scripts.migrate_encrypt_pii

# Test API still works
curl http://localhost:8000/api/v1/applicants/1
# Should return decrypted email in response
```

## Questions?
If unclear about encryption algorithm choice or search strategy, ask first.
```

---

## Sprint 4: Missing Endpoints & Field Fixes ✅ COMPLETE

### Completion Summary
**Completed:** December 2, 2025
**Files Created:**
- `backend/app/models/batch_job.py` - BatchJob model for tracking background processing
- `backend/migrations/versions/20251202_005_add_batch_jobs.py` - Migration for batch_jobs table

**Files Updated:**
- `backend/app/api/v1/screening.py` - Added GET /hits endpoint with filtering (resolved, applicant_id, hit_type)
- `backend/app/api/v1/ai.py` - Added GET /batch-analyze/{job_id} and GET /documents/{id}/suggestions
- `backend/app/api/v1/cases.py` - Fixed CaseUpdate to accept both `assignee_id` and `assigned_to`
- `backend/app/models/__init__.py` - Added BatchJob export

**New Endpoints:**
1. `GET /api/v1/screening/hits` - List screening hits with filtering
2. `GET /api/v1/screening/hits/{id}` - Get single hit by ID
3. `GET /api/v1/ai/batch-analyze/{job_id}` - Get batch job status
4. `GET /api/v1/ai/documents/{id}/suggestions` - Get document AI suggestions

**Fixes:**
- Case assignment now accepts both `assigned_to` and `assignee_id` field names
- Batch analyze now returns `job_id` for status tracking

**Test Results:** 207 tests passing

### Original Sprint Details (For Reference)

### Why This Sprint?
The frontend calls endpoints that don't exist or uses field names that don't match the backend.

**Broken functionality:**
- `GET /screening/hits` - Frontend calls but backend has no GET endpoint
- `GET /ai/batch-analyze/{jobId}` - No status checking endpoint
- `GET /ai/documents/{id}/suggestions` - Not implemented
- Case assignment uses `assigned_to` but backend expects `assignee_id`

### Files to Upload:
1. `backend/app/api/v1/screening.py`
2. `backend/app/api/v1/ai.py`
3. `backend/app/api/v1/cases.py`
4. `frontend/src/services/screening.js` (for reference)
5. `frontend/src/services/cases.js` (for reference)

### Prompt (Copy This):

```
# CHAT TITLE: Backend Sprint 4 - Missing Endpoints & Field Fixes

## Context
I'm building GetClearance, an AI-native KYC/AML platform. The frontend calls several endpoints that don't exist in the backend, causing 404 errors.

**Current Repo:** https://github.com/autorevai/getclearance

## What Exists (Read These First)
I've uploaded context files:

1. **screening.py** - Backend screening endpoints (missing GET /hits)
2. **ai.py** - Backend AI endpoints (missing batch status)
3. **cases.py** - Backend case endpoints (field name mismatch)
4. **screening.js** - Frontend expects these endpoints
5. **cases.js** - Frontend field names

## Missing Endpoints

### 1. GET /api/v1/screening/hits

**Frontend calls (screening.js line 38-40):**
```javascript
async getUnresolvedHits() {
  return this.api.get('/screening/hits?status=pending');
}
```

**Backend has:** Only `PATCH /screening/hits/{id}` for resolving

**Need to create:**
```python
@router.get("/hits", response_model=list[ScreeningHitResponse])
async def list_screening_hits(
    status: str | None = Query(None, description="Filter by resolution status"),
    applicant_id: UUID | None = Query(None),
    limit: int = Query(50, le=100),
    offset: int = Query(0),
    user: TokenPayload = Depends(get_current_user),
    db: TenantDB = Depends(get_tenant_db),
):
    """List screening hits with optional filtering."""
    query = select(ScreeningHit).where(ScreeningHit.tenant_id == user.tenant_id)

    if status:
        query = query.where(ScreeningHit.resolution_status == status)
    if applicant_id:
        query = query.where(ScreeningHit.applicant_id == applicant_id)

    query = query.order_by(ScreeningHit.created_at.desc())
    query = query.limit(limit).offset(offset)

    result = await db.execute(query)
    return result.scalars().all()
```

### 2. GET /api/v1/ai/batch-analyze/{job_id}

**Frontend calls (ai.js line 34-36):**
```javascript
async getBatchStatus(jobId) {
  return this.api.get(`/ai/batch-analyze/${jobId}`);
}
```

**Backend has:** Only `POST /ai/batch-analyze` (starts job, no status)

**Need to create:**
```python
@router.get("/batch-analyze/{job_id}", response_model=BatchJobStatus)
async def get_batch_job_status(
    job_id: UUID,
    user: TokenPayload = Depends(get_current_user),
    db: TenantDB = Depends(get_tenant_db),
):
    """Get status of a batch analysis job."""
    # Query from batch_jobs table or Redis
    job = await db.execute(
        select(BatchJob).where(
            BatchJob.id == job_id,
            BatchJob.tenant_id == user.tenant_id,
        )
    )
    job = job.scalar_one_or_none()

    if not job:
        raise HTTPException(404, "Batch job not found")

    return BatchJobStatus(
        job_id=job.id,
        status=job.status,  # pending, processing, completed, failed
        progress=job.progress,  # 0-100
        total_items=job.total_items,
        processed_items=job.processed_items,
        errors=job.errors,
        completed_at=job.completed_at,
    )
```

**Create BatchJob model if needed:**
```python
class BatchJob(TenantModel):
    __tablename__ = "batch_jobs"

    job_type: Mapped[str] = mapped_column(String(50))  # 'risk_analysis'
    status: Mapped[str] = mapped_column(String(20), default="pending")
    progress: Mapped[int] = mapped_column(default=0)
    total_items: Mapped[int] = mapped_column(default=0)
    processed_items: Mapped[int] = mapped_column(default=0)
    errors: Mapped[list] = mapped_column(JSON, default=list)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
```

### 3. GET /api/v1/ai/documents/{id}/suggestions

**Frontend calls (ai.js line 38-40):**
```javascript
async getDocumentSuggestions(documentId) {
  return this.api.get(`/ai/documents/${documentId}/suggestions`);
}
```

**Backend:** Not implemented at all

**Need to create:**
```python
@router.get("/documents/{document_id}/suggestions", response_model=DocumentSuggestions)
async def get_document_suggestions(
    document_id: UUID,
    user: TokenPayload = Depends(get_current_user),
    db: TenantDB = Depends(get_tenant_db),
):
    """Get AI suggestions for document issues."""
    document = await db.get(Document, document_id)

    if not document:
        raise HTTPException(404, "Document not found")

    # Get existing AI assessment if available
    assessment = await db.execute(
        select(AIAssessment).where(
            AIAssessment.document_id == document_id,
            AIAssessment.assessment_type == "document_suggestions",
        )
    )
    assessment = assessment.scalar_one_or_none()

    if assessment:
        return DocumentSuggestions(**assessment.result)

    # Generate new suggestions if none exist
    suggestions = await generate_document_suggestions(document)

    # Cache the result
    new_assessment = AIAssessment(
        document_id=document_id,
        assessment_type="document_suggestions",
        result=suggestions.model_dump(),
    )
    db.add(new_assessment)
    await db.commit()

    return suggestions
```

### 4. Fix Case Assignment Field Name

**Frontend calls (cases.js line 42-43):**
```javascript
async assign(id, userId) {
  return this.api.patch(`/cases/${id}`, { assigned_to: userId });
}
```

**Backend expects:** `assignee_id`

**Fix in cases.py:**
```python
class CaseUpdate(BaseModel):
    # Accept both field names for backwards compatibility
    assignee_id: UUID | None = Field(None, alias="assigned_to")

    class Config:
        populate_by_name = True  # Accept both assignee_id and assigned_to
```

**Or update frontend to use correct field name.**

## Response Schemas Needed

```python
# schemas/screening.py
class ScreeningHitResponse(BaseModel):
    id: UUID
    applicant_id: UUID
    check_id: UUID
    hit_type: str  # sanctions, pep, adverse_media
    matched_entity: str
    match_score: float
    list_source: str
    resolution_status: str  # pending, confirmed_true, confirmed_false
    resolved_by: UUID | None
    resolved_at: datetime | None
    created_at: datetime

# schemas/ai.py
class BatchJobStatus(BaseModel):
    job_id: UUID
    status: str  # pending, processing, completed, failed
    progress: int  # 0-100
    total_items: int
    processed_items: int
    errors: list[dict]
    completed_at: datetime | None

class DocumentSuggestions(BaseModel):
    document_id: UUID
    suggestions: list[DocumentSuggestion]
    generated_at: datetime

class DocumentSuggestion(BaseModel):
    type: str  # 'quality', 'completeness', 'verification'
    severity: str  # 'info', 'warning', 'error'
    message: str
    action: str | None  # Suggested action
```

## Success Criteria

- [ ] GET /screening/hits endpoint created
- [ ] GET /ai/batch-analyze/{job_id} endpoint created
- [ ] BatchJob model created (if needed)
- [ ] GET /ai/documents/{id}/suggestions endpoint created
- [ ] Case assignment accepts both field names
- [ ] All frontend 404 errors resolved
- [ ] Response schemas match frontend expectations

## Testing

```bash
# Test new endpoints
curl -H "Authorization: Bearer $TOKEN" \
  http://localhost:8000/api/v1/screening/hits?status=pending

curl -H "Authorization: Bearer $TOKEN" \
  http://localhost:8000/api/v1/ai/batch-analyze/some-job-id

curl -H "Authorization: Bearer $TOKEN" \
  http://localhost:8000/api/v1/ai/documents/some-doc-id/suggestions

# Test case assignment with both field names
curl -X PATCH -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"assigned_to": "user-uuid"}' \
  http://localhost:8000/api/v1/cases/case-id
```

## Questions?
If unclear about response format expectations, ask first.
```

---

## Sprint 5: GDPR Compliance Features ✅ COMPLETE

### Completion Summary
**Completed:** December 2, 2025

**Files Created:**
- `backend/app/services/retention.py` - Data retention policy service with AML-compliant retention periods
- `backend/migrations/versions/20251202_006_add_gdpr_compliance.py` - Migration for GDPR fields
- `backend/tests/test_gdpr.py` - 12 tests for retention policies

**Files Updated:**
- `backend/app/models/applicant.py` - Added GDPR fields:
  - `legal_hold`, `legal_hold_reason`, `legal_hold_set_by`, `legal_hold_set_at`
  - `consent_given`, `consent_given_at`, `consent_ip_address`, `consent_withdrawn_at`
  - `retention_expires_at`
- `backend/app/api/v1/applicants.py` - Added GDPR endpoints:
  - `GET /{id}/export` - SAR export (JSON/PDF)
  - `DELETE /{id}/gdpr-delete` - GDPR deletion with safeguards
  - `POST /{id}/consent` - Consent tracking
  - `POST /{id}/legal-hold` - Set legal hold
  - `DELETE /{id}/legal-hold` - Remove legal hold
- `backend/app/services/audit.py` - Added GDPR audit functions:
  - `audit_gdpr_data_exported`
  - `audit_gdpr_data_deleted`
  - `audit_consent_recorded`
  - `audit_legal_hold_set`
  - `audit_legal_hold_removed`
- `backend/app/schemas/applicant.py` - Added GDPR schemas

**Features Implemented:**
- Subject Access Request (SAR) export (GDPR Article 15 & 20)
- Right to Erasure with AML safeguards (GDPR Article 17)
- Legal hold to prevent deletion during investigations
- Consent tracking with IP address logging
- Retention policies based on applicant status:
  - approved/rejected: 5 years (AML requirement)
  - flagged: 7 years (extended for confirmed hits)
  - pending: 90 days
  - withdrawn: 30 days

**Test Results:** 219 tests passing (12 new GDPR tests)

### Original Sprint Details (For Reference)

### Why This Sprint?
The platform handles EU citizen data but lacks GDPR-required features:
- No Subject Access Request (SAR) export
- No data deletion capability
- No data retention policies

### Files to Upload:
1. `backend/app/api/v1/applicants.py`
2. `backend/app/models/applicant.py`
3. `README.md`

### Prompt (Copy This):

```
# CHAT TITLE: Backend Sprint 5 - GDPR Compliance Features

## Context
I'm building GetClearance, a KYC/AML platform that processes EU citizen data. GDPR requires:
- Article 15: Right of access (Subject Access Request)
- Article 17: Right to erasure (deletion)
- Article 20: Right to data portability (export)

**Current Repo:** https://github.com/autorevai/getclearance

## What I Need You To Create

### Part 1: Subject Access Request (SAR) Export

**Endpoint:** `GET /api/v1/applicants/{id}/export`

```python
@router.get("/{applicant_id}/export")
async def export_applicant_data(
    applicant_id: UUID,
    format: str = Query("json", enum=["json", "pdf"]),
    user: TokenPayload = Depends(get_current_user),
    db: TenantDB = Depends(get_tenant_db),
):
    """
    Export all data associated with an applicant (GDPR Article 15 & 20).
    Returns complete data package in requested format.
    """
    applicant = await db.get(Applicant, applicant_id)
    if not applicant:
        raise HTTPException(404, "Applicant not found")

    # Gather all related data
    export_data = {
        "personal_information": {
            "first_name": applicant.first_name,
            "last_name": applicant.last_name,
            "email": applicant.email,
            "phone": applicant.phone,
            "date_of_birth": applicant.date_of_birth.isoformat() if applicant.date_of_birth else None,
            "nationality": applicant.nationality,
            "address": applicant.address,
        },
        "verification_status": {
            "status": applicant.status,
            "risk_level": applicant.risk_level,
            "created_at": applicant.created_at.isoformat(),
            "updated_at": applicant.updated_at.isoformat(),
        },
        "documents": await get_applicant_documents(db, applicant_id),
        "screening_results": await get_applicant_screening(db, applicant_id),
        "cases": await get_applicant_cases(db, applicant_id),
        "audit_trail": await get_applicant_audit_log(db, applicant_id),
        "ai_assessments": await get_applicant_ai_assessments(db, applicant_id),
        "export_metadata": {
            "exported_at": datetime.utcnow().isoformat(),
            "exported_by": user.email,
            "format": format,
            "gdpr_articles": ["15", "20"],
        }
    }

    if format == "pdf":
        pdf = generate_sar_pdf(export_data)
        return Response(
            content=pdf,
            media_type="application/pdf",
            headers={"Content-Disposition": f"attachment; filename=sar_{applicant_id}.pdf"}
        )

    return export_data
```

### Part 2: Right to Erasure (Data Deletion)

**Endpoint:** `DELETE /api/v1/applicants/{id}/gdpr-delete`

```python
@router.delete("/{applicant_id}/gdpr-delete")
async def gdpr_delete_applicant(
    applicant_id: UUID,
    confirmation: str = Query(..., description="Must be 'CONFIRM_DELETE'"),
    reason: str = Query(..., description="Reason for deletion request"),
    user: TokenPayload = Depends(get_current_user),
    db: TenantDB = Depends(get_tenant_db),
):
    """
    Permanently delete applicant and all associated data (GDPR Article 17).
    This action is IRREVERSIBLE.
    """
    if confirmation != "CONFIRM_DELETE":
        raise HTTPException(400, "Must confirm deletion with 'CONFIRM_DELETE'")

    applicant = await db.get(Applicant, applicant_id)
    if not applicant:
        raise HTTPException(404, "Applicant not found")

    # Check for legal holds
    if applicant.legal_hold:
        raise HTTPException(
            409,
            "Cannot delete: applicant is under legal hold. Contact compliance."
        )

    # Check retention period (some records must be kept for AML compliance)
    if applicant.status in ["flagged", "rejected"] and not can_delete_for_aml(applicant):
        raise HTTPException(
            409,
            "Cannot delete: AML regulations require retention of flagged records for 5 years."
        )

    # Delete associated data
    await delete_applicant_documents(db, applicant_id)  # Also delete from R2
    await delete_applicant_screening(db, applicant_id)
    await delete_applicant_cases(db, applicant_id)
    await delete_applicant_ai_assessments(db, applicant_id)

    # Create deletion audit log BEFORE deleting applicant
    await record_audit_log(
        db=db,
        tenant_id=user.tenant_id,
        entity_type="applicant",
        entity_id=applicant_id,
        action="gdpr_deleted",
        actor_id=UUID(user.id),
        old_value={"reason": reason, "email_hash": hash_email(applicant.email)},
        new_value=None,
    )

    # Delete applicant
    await db.delete(applicant)
    await db.commit()

    return {"status": "deleted", "applicant_id": str(applicant_id)}
```

### Part 3: Data Retention Policy

**Create retention service:**

```python
# backend/app/services/retention.py

from datetime import datetime, timedelta

RETENTION_POLICIES = {
    "approved": timedelta(days=365 * 5),      # 5 years
    "rejected": timedelta(days=365 * 5),      # 5 years (AML requirement)
    "flagged": timedelta(days=365 * 7),       # 7 years
    "pending": timedelta(days=90),            # 90 days
    "withdrawn": timedelta(days=30),          # 30 days
}

async def get_expired_applicants(db: AsyncSession) -> list[Applicant]:
    """Find applicants past their retention period."""
    expired = []

    for status, retention_period in RETENTION_POLICIES.items():
        cutoff = datetime.utcnow() - retention_period
        result = await db.execute(
            select(Applicant).where(
                Applicant.status == status,
                Applicant.updated_at < cutoff,
                Applicant.legal_hold == False,
            )
        )
        expired.extend(result.scalars().all())

    return expired

# Background job to run weekly
async def retention_cleanup_job():
    """Automated cleanup of expired records."""
    async with async_session_maker() as db:
        expired = await get_expired_applicants(db)

        for applicant in expired:
            # Auto-delete or notify for review
            await notify_retention_expiry(applicant)
```

### Part 4: Legal Hold Support

**Add to applicant model:**
```python
class Applicant(TenantModel):
    # ... existing fields ...

    # GDPR & Compliance
    legal_hold: Mapped[bool] = mapped_column(default=False)
    legal_hold_reason: Mapped[str | None] = mapped_column(String(500))
    legal_hold_set_by: Mapped[UUID | None] = mapped_column(ForeignKey("users.id"))
    legal_hold_set_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    # Consent tracking
    consent_given: Mapped[bool] = mapped_column(default=False)
    consent_given_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    consent_ip_address: Mapped[str | None] = mapped_column(String(45))
```

### Part 5: Consent Tracking Endpoint

```python
@router.post("/{applicant_id}/consent")
async def record_consent(
    applicant_id: UUID,
    consent: ConsentRequest,
    request: Request,
    db: TenantDB = Depends(get_tenant_db),
):
    """Record applicant's consent for data processing."""
    applicant = await db.get(Applicant, applicant_id)
    if not applicant:
        raise HTTPException(404, "Applicant not found")

    applicant.consent_given = consent.consent
    applicant.consent_given_at = datetime.utcnow()
    applicant.consent_ip_address = request.client.host

    await db.commit()

    return {"status": "consent_recorded"}
```

## Success Criteria

- [ ] SAR export endpoint (JSON and PDF)
- [ ] GDPR delete endpoint with safeguards
- [ ] Legal hold support
- [ ] Retention policy service
- [ ] Consent tracking
- [ ] Audit logs for all GDPR operations
- [ ] AML retention rules enforced

## Testing

```bash
# Test SAR export
curl -H "Authorization: Bearer $TOKEN" \
  http://localhost:8000/api/v1/applicants/{id}/export?format=json

# Test GDPR delete
curl -X DELETE -H "Authorization: Bearer $TOKEN" \
  "http://localhost:8000/api/v1/applicants/{id}/gdpr-delete?confirmation=CONFIRM_DELETE&reason=user_request"

# Verify legal hold blocks deletion
# (should return 409)
```

## Questions?
If unclear about retention periods or AML requirements, ask first.
```

---

## Sprint 6: Monitoring & Alerting ✅ COMPLETE

### Completion Summary
**Completed:** December 2, 2025

**Files Created:**
- `backend/app/logging_config.py` - Structured JSON logging with PII scrubbing and request context
- `backend/tests/test_monitoring.py` - 24 tests for monitoring features

**Files Updated:**
- `backend/app/main.py` - Added Sentry integration, improved health checks
- `backend/app/config.py` - Added `sentry_dsn`, `sentry_traces_sample_rate` settings
- `backend/requirements.txt` - Added `sentry-sdk[fastapi]==1.38.0`

**Features Implemented:**
1. **Sentry Integration** - Error tracking with PII scrubbing before events are sent
2. **Structured Logging** - JSON formatter for production, colored output for development
3. **Request Context Propagation** - request_id, tenant_id, user_id in all log entries
4. **PII Scrubbing** - Automatic redaction of email, phone, SSN, credit card in logs
5. **Health Check Endpoints**:
   - `GET /health` - Simple liveness check
   - `GET /health/ready` - Readiness with database and Redis checks
   - `GET /health/live` - Kubernetes liveness probe

**Test Results:** 24 new monitoring tests passing

### Original Sprint Details (For Reference)

### Why This Sprint?
No monitoring or alerting is configured. When issues occur in production, there's no visibility.

### Files to Upload:
1. `backend/app/main.py`
2. `backend/requirements.txt`

### Prompt (Copy This):

```
# CHAT TITLE: Backend Sprint 6 - Monitoring & Alerting

## Context
I'm building GetClearance, a KYC/AML platform deployed on Railway. Need to add production monitoring and alerting.

**Current Repo:** https://github.com/autorevai/getclearance

## What I Need You To Do

### Part 1: Sentry Integration

**Install:**
```bash
pip install sentry-sdk[fastapi]
```

**Update main.py:**
```python
import sentry_sdk
from sentry_sdk.integrations.fastapi import FastApiIntegration
from sentry_sdk.integrations.sqlalchemy import SqlalchemyIntegration

if settings.sentry_dsn:
    sentry_sdk.init(
        dsn=settings.sentry_dsn,
        environment=settings.environment,
        traces_sample_rate=0.1,  # 10% of requests
        profiles_sample_rate=0.1,
        integrations=[
            FastApiIntegration(transaction_style="endpoint"),
            SqlalchemyIntegration(),
        ],
        # Scrub PII from error reports
        before_send=scrub_pii,
    )

def scrub_pii(event, hint):
    """Remove PII from Sentry events."""
    if "request" in event:
        if "data" in event["request"]:
            # Remove sensitive fields
            for field in ["email", "phone", "ssn", "password"]:
                if field in event["request"]["data"]:
                    event["request"]["data"][field] = "[REDACTED]"
    return event
```

### Part 2: Structured Logging

```python
# backend/app/logging_config.py
import logging
import json
from datetime import datetime
from contextvars import ContextVar

request_id_var: ContextVar[str] = ContextVar("request_id", default="")

class JSONFormatter(logging.Formatter):
    def format(self, record):
        log_record = {
            "timestamp": datetime.utcnow().isoformat(),
            "level": record.levelname,
            "message": record.getMessage(),
            "logger": record.name,
            "request_id": request_id_var.get(),
        }
        if record.exc_info:
            log_record["exception"] = self.formatException(record.exc_info)
        return json.dumps(log_record)

def setup_logging():
    handler = logging.StreamHandler()
    handler.setFormatter(JSONFormatter())

    logging.root.handlers = [handler]
    logging.root.setLevel(logging.INFO)
```

### Part 3: Health Check Endpoints

```python
@router.get("/health")
async def health():
    return {"status": "healthy"}

@router.get("/health/ready")
async def readiness(db: AsyncSession = Depends(get_db)):
    """Check all dependencies."""
    checks = {}

    # Database
    try:
        await db.execute(text("SELECT 1"))
        checks["database"] = "healthy"
    except Exception as e:
        checks["database"] = f"unhealthy: {str(e)}"

    # Redis
    try:
        redis = await get_redis()
        await redis.ping()
        checks["redis"] = "healthy"
    except Exception as e:
        checks["redis"] = f"unhealthy: {str(e)}"

    all_healthy = all(v == "healthy" for v in checks.values())

    return JSONResponse(
        status_code=200 if all_healthy else 503,
        content={"status": "ready" if all_healthy else "not_ready", "checks": checks}
    )
```

### Part 4: Metrics Endpoint (Prometheus)

```python
# Optional: Add prometheus metrics
from prometheus_client import Counter, Histogram, generate_latest

REQUEST_COUNT = Counter(
    "http_requests_total",
    "Total HTTP requests",
    ["method", "endpoint", "status"]
)

REQUEST_LATENCY = Histogram(
    "http_request_duration_seconds",
    "HTTP request latency",
    ["method", "endpoint"]
)

@app.get("/metrics")
async def metrics():
    return Response(
        content=generate_latest(),
        media_type="text/plain"
    )
```

## Success Criteria

- [ ] Sentry integration with PII scrubbing
- [ ] Structured JSON logging
- [ ] Request ID in all logs
- [ ] Health check endpoints
- [ ] Readiness check with dependency status
- [ ] Metrics endpoint (optional)

## Questions?
If unclear about Sentry DSN or log levels, ask first.
```

---

## Sprint Dependencies Diagram

```
Sprint 1 (Audit Logging) ─────────────────────────────────────┐
                                                               │
Sprint 2 (Rate Limiting) ─────────────────────────────────────┤
                                                               │
Sprint 3 (PII Encryption) ────────────────────────────────────┤──> Production Ready
                                                               │
Sprint 4 (Missing Endpoints) ─────────────────────────────────┤
                                                               │
Sprint 5 (GDPR Compliance) ───────────────────────────────────┤
                                                               │
Sprint 6 (Monitoring) ────────────────────────────────────────┘
```

**Parallel Work Possible:**
- Sprints 1, 2, 3 can run in parallel (independent)
- Sprint 4 is independent
- Sprint 5 depends on Sprint 1 (audit logging)
- Sprint 6 is independent

---

## Pre-Sprint Checklist

Before starting EACH sprint:

- [ ] Completed any dependent sprints
- [ ] Downloaded latest code from repo
- [ ] Read relevant context files
- [ ] Uploaded required files to chat
- [ ] Copied complete prompt (not partial)
- [ ] Have database access for testing
- [ ] Ready to deploy to Railway

**Time investment:** 15 minutes prep per sprint
**Time saved:** 4-6 hours debugging per sprint

---

## Post-Sprint Verification

After completing ALL sprints, verify:

```bash
# 1. Audit logs being created
psql -d getclearance -c "SELECT COUNT(*) FROM audit_logs"

# 2. Rate limiting working
for i in {1..10}; do curl -X POST http://localhost:8000/api/v1/auth/token; done

# 3. PII encrypted
psql -d getclearance -c "SELECT email FROM applicants LIMIT 1"
# Should see 'gAAAAAB...' not plaintext

# 4. Debug endpoints removed
curl http://localhost:8000/api/v1/auth/debug/token-claims
# Should get 404

# 5. Missing endpoints exist
curl http://localhost:8000/api/v1/screening/hits
# Should get 200 (not 404)

# 6. GDPR export works
curl http://localhost:8000/api/v1/applicants/{id}/export

# 7. Sentry receiving errors
# Check Sentry dashboard

# 8. Health checks work
curl http://localhost:8000/health/ready
```

---

**Copy the prompts exactly as shown - they're structured for security compliance!**
