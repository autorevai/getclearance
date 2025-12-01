# REVISED Implementation Plan - GetClearance
**Status:** 74% Complete → 100% Target  
**Timeline:** 4-5 Weeks (Revised from 8 weeks)  
**Last Updated:** November 30, 2025

---

## 🎉 Major Update: You're Way Ahead of Schedule!

Based on the current state audit, **Phase 1 is essentially done**:
- ✅ Storage service (R2) - EXISTS
- ✅ Screening service (OpenSanctions) - EXISTS  
- ✅ AI service (Claude) - EXISTS

**What's left:** Background workers, OCR, webhooks, testing, deployment

---

## 📋 Revised Phase Plan

### ~~Phase 1: Core Services~~ ✅ COMPLETE (74% done overall)
**Status:** DONE - Services already exist  
**Skip to Phase 2**

---

### Phase 2: Background Workers (Week 1) 🔴 PRIORITY
**Goal:** Enable async processing for long-running tasks  
**Duration:** 5-7 days  
**Files to Create:** 5 files

#### What to Create
1. `backend/app/workers/__init__.py`
2. `backend/app/workers/config.py` - ARQ worker configuration
3. `backend/app/workers/screening_worker.py` - Background screening
4. `backend/app/workers/document_worker.py` - Document processing
5. `backend/app/workers/ai_worker.py` - AI risk summaries

#### Success Criteria
- [ ] Workers can be started with `arq app.workers.config.WorkerSettings`
- [ ] Jobs can be enqueued from API endpoints
- [ ] Screening runs in background (doesn't block API)
- [ ] Document processing queued after upload
- [ ] AI summaries generated asynchronously

---

### Phase 3: OCR Integration (Week 2) 🟡
**Goal:** Extract text and data from documents  
**Duration:** 5-7 days  
**Files to Create:** 2 new + 1 update

#### What to Create
1. `backend/app/services/ocr.py` - AWS Textract integration
2. `backend/app/services/mrz_parser.py` - Passport MRZ validation
3. Update `backend/app/workers/document_worker.py` - Integrate OCR

#### Success Criteria
- [ ] OCR extracts text from uploaded documents
- [ ] MRZ parser validates passport check digits
- [ ] Structured data stored in `document.extracted_data`
- [ ] Quality issues detected (blur, resolution, glare)
- [ ] Fraud signals generated for suspicious documents

---

### Phase 4: Webhooks & Notifications (Week 3) 🟢
**Goal:** Notify customers of application status changes  
**Duration:** 3-4 days  
**Files to Create:** 3 files

#### What to Create
1. `backend/app/services/webhook.py` - Webhook delivery with retry
2. `backend/app/workers/webhook_worker.py` - Background delivery
3. `backend/app/schemas/webhook.py` - Webhook payload schemas

#### Success Criteria
- [ ] Webhooks deliver on applicant status change
- [ ] Retry logic works (3 attempts: 0s, 30s, 5min)
- [ ] HMAC signature generation working
- [ ] Delivery logs stored in database
- [ ] Failed webhooks create alerts

---

### Phase 5: Evidence & Compliance (Week 3-4) 🟢
**Goal:** Generate audit-ready evidence packs  
**Duration:** 3-4 days  
**Files to Create:** 2 files + API updates

#### What to Create
1. `backend/app/services/evidence.py` - PDF generation
2. `backend/app/services/timeline.py` - Event aggregation
3. Update API endpoints to expose evidence export

#### Success Criteria
- [ ] Evidence PDFs generated with citations
- [ ] Timeline aggregates all applicant events
- [ ] Chain-of-custody tracked
- [ ] Exports meet SOC 2 requirements
- [ ] Download endpoint works

---

### Phase 6: Testing (Week 4-5) 🟢
**Goal:** Comprehensive test coverage  
**Duration:** 7-10 days  
**Files to Create:** 6 files

#### What to Create
1. `backend/tests/test_screening.py` - Screening service tests
2. `backend/tests/test_storage.py` - Storage service tests
3. `backend/tests/test_ai.py` - AI service tests
4. `backend/tests/test_workers.py` - Worker tests
5. `backend/tests/integration/test_full_applicant_flow.py` - E2E test
6. `backend/tests/integration/test_screening_flow.py` - E2E screening test

#### Success Criteria
- [ ] Unit test coverage >80%
- [ ] Integration tests pass
- [ ] E2E tests cover critical flows
- [ ] Load testing validates 100+ req/min
- [ ] Security scan passes (no critical issues)

---

### Phase 7: Deployment (Week 5) 🔵
**Goal:** Production deployment on Railway  
**Duration:** 3-5 days  
**Files to Create:** 2-3 files

#### What to Create
1. `docs/DEPLOYMENT.md` - Step-by-step Railway guide
2. `railway.json` - Railway configuration (optional)
3. Update `.env.example` - Document all required env vars

#### Success Criteria
- [ ] Railway project created
- [ ] PostgreSQL & Redis provisioned
- [ ] Environment variables configured
- [ ] Migrations run successfully
- [ ] Production URL live with SSL
- [ ] Health checks passing
- [ ] First customer onboarded

---

## 🗣️ Ready-to-Use Chat Prompts

### Chat 1: Schema Migration (1 Day)

**Files to Upload:**
1. `01_CURRENT_STATE_AUDIT.md`
2. `02_FOLDER_STRUCTURE_COMPLETE.md`
3. `README.md` (from repo)

**Prompt:**
```
# CHAT TITLE: Apply Schema Migration for Sumsub Features

## Context
I'm building GetClearance, an AI-native KYC/AML platform (Sumsub clone). I'm at 74% complete. The core services layer is complete, but the database schema needs minor enhancements to support Sumsub-style features like fuzzy matching confidence scores and fraud detection.

**Current Repo:** https://github.com/autorevai/getclearance

## What Exists (Read These First)
I've uploaded 3 context files - please read them first:

1. **01_CURRENT_STATE_AUDIT.md** - Shows current project status
2. **02_FOLDER_STRUCTURE_COMPLETE.md** - Complete directory tree
3. **README.md** - Project README

**Key existing components:**
- ✅ All models exist in `backend/app/models/`
- ✅ Initial migration exists: `migrations/versions/20251130_001_initial_schema.py`
- ❌ Schema enhancements NOT applied yet

## What I Need You To Create

Create an Alembic migration that adds Sumsub-inspired schema enhancements:

**File to create:**
- `backend/migrations/versions/20251130_002_add_sumsub_features.py`

**Changes needed:**

1. **Update `screening_hits` table:**
   - Change `confidence` column from INTEGER to DECIMAL(5,2)
   - Add `match_type` VARCHAR(50) - Values: 'true_positive', 'potential_match', 'false_positive', 'unknown'
   - Add `pep_relationship` VARCHAR(50) - Values: 'direct', 'family', 'associate'
   - Add `sentiment` VARCHAR(20) - Values: 'positive', 'neutral', 'negative'
   - Add `source_reputation` VARCHAR(20) - Values: 'high', 'medium', 'low'

2. **Update `documents` table:**
   - Add `security_features_detected` JSONB - Array of detected features
   - Add `fraud_analysis` JSONB - Fraud detection results

3. **Create `webhook_deliveries` table:**
   - id, tenant_id, webhook_url, event_type, event_id, payload (JSONB)
   - attempt_count, last_attempt_at, next_retry_at, status, http_status, response_body
   - created_at
   - Indexes on (tenant_id), (status, next_retry_at), (event_type, event_id)

4. **Create `applicant_events` table:**
   - id, tenant_id, applicant_id, event_type, event_data (JSONB)
   - actor_type, actor_id, timestamp
   - Indexes on (applicant_id, timestamp), (tenant_id), (event_type)

5. **Create `kyc_share_tokens` table (future feature):**
   - id, tenant_id, applicant_id, token, scope (JSONB), user_consent (JSONB)
   - created_at, expires_at, revoked_at, access_count, last_accessed_at, last_accessed_by
   - Indexes on (token), (applicant_id), (token, expires_at) WHERE not revoked

## Integration Requirements

**Must:**
- Use PostgreSQL-specific types (JSONB, UUID)
- Include both upgrade() and downgrade() functions
- Use proper SQLAlchemy syntax for Alembic
- Add server defaults where appropriate
- Include comments explaining each change

## Success Criteria

- [ ] Migration file created in correct location
- [ ] All table changes included
- [ ] Indexes added for performance
- [ ] Downgrade function reverses all changes
- [ ] Can run `alembic upgrade head` successfully
- [ ] Can run `alembic downgrade -1` successfully

## Questions?
If anything is unclear about the existing schema, ask before implementing.
```

---

### Chat 2: Background Workers (5-7 Days)

**Files to Upload:**
1. `01_CURRENT_STATE_AUDIT.md`
2. `02_FOLDER_STRUCTURE_COMPLETE.md`
3. `README.md` (from repo)
4. `03_CONTEXT_BUNDLE_TEMPLATE.md`

**Prompt:**
```
# CHAT TITLE: Create Background Workers (ARQ Setup)

## Context
I'm building GetClearance, an AI-native KYC/AML platform. I'm at 74% complete and need to add background job processing using ARQ (Redis-based async task queue).

**Current Repo:** https://github.com/autorevai/getclearance

## What Exists (Read These First)
I've uploaded 5 context files - please read them first:

1. **01_CURRENT_STATE_AUDIT.md** - Current state audit
2. **02_FOLDER_STRUCTURE_COMPLETE.md** - Complete folder structure
3. **README.md** - Project README
4. **05_SUMSUB_CONTEXT.md** - We're building a Sumsub competitor (reverse engineering context) ⭐
5. **03_CONTEXT_BUNDLE_TEMPLATE.md** - Integration patterns

**Key existing components:**
- ✅ Services layer exists: `app/services/screening.py`, `storage.py`, `ai.py`
- ✅ Models exist: `app/models/applicant.py`, `screening.py`, `document.py`
- ✅ API endpoints exist and are functional
- ❌ Workers directory does NOT exist yet

## What I Need You To Create

Create the background workers system for async processing:

**Files to create:**
1. `backend/app/workers/__init__.py` - Module exports
2. `backend/app/workers/config.py` - ARQ configuration
3. `backend/app/workers/screening_worker.py` - Run screening in background
4. `backend/app/workers/document_worker.py` - Process documents (OCR will be added later)
5. `backend/app/workers/ai_worker.py` - Generate risk summaries in background

## Integration Requirements

**Must call existing services:**
- `screening_worker` → calls `app.services.screening.check_individual()`
- `document_worker` → calls `app.services.storage` to download files
- `ai_worker` → calls `app.services.ai.generate_risk_summary()`

**Must update database:**
- Update `applicants.status` when jobs complete
- Update `screening_checks.status` when screening completes
- Update `documents.status` when processing completes
- Create entries in `applicant_events` for timeline

**Must use existing patterns:**
- Import DB from `app.database`
- Use async with for sessions
- Handle errors gracefully
- Log progress for monitoring

## Architecture Constraints

**ARQ Configuration:**
- Redis URL from `app.config.settings.redis_url`
- Job timeout: 300 seconds
- Max retries: 3
- Retry delay: exponential backoff

**Worker Functions Pattern:**
```python
async def worker_function(ctx, param1, param2):
    """Docstring explaining what this does."""
    logger = ctx['logger']
    
    try:
        # Implementation
        logger.info("Job started")
        # ... do work ...
        logger.info("Job completed")
        return {"status": "success"}
    except Exception as e:
        logger.error(f"Job failed: {e}")
        raise  # ARQ will retry
```

## Success Criteria

- [ ] `backend/app/workers/` directory created
- [ ] All 5 files created
- [ ] Workers can be started: `arq app.workers.config.WorkerSettings`
- [ ] Jobs can be enqueued from API
- [ ] Errors logged, worker doesn't crash
- [ ] Database updates in transactions
- [ ] Can run `pytest tests/test_workers.py` (you don't need to create tests yet)

## Additional Context

**How to enqueue jobs from API:**
```python
from arq import create_pool
from app.workers.config import WorkerSettings

# In API endpoint:
redis = await create_pool(WorkerSettings.redis_settings)
job = await redis.enqueue_job('screening_worker', applicant_id, check_type)
```

**Example usage:**
1. User creates applicant via API
2. API immediately returns applicant (status='pending')
3. API enqueues screening_worker job
4. Worker runs screening in background
5. Worker updates applicant status to 'review' or 'approved'
6. Frontend polls for status updates

## Questions?
If anything is unclear about existing services or models, ask before implementing.
```

---

### Chat 3: OCR Service (5-7 Days)

**Files to Upload:**
1. `01_CURRENT_STATE_AUDIT.md`
2. `02_FOLDER_STRUCTURE_COMPLETE.md`
3. `README.md` (from repo)

**Prompt:**
```
# CHAT TITLE: Create OCR Service (AWS Textract Integration)

## Context
I'm building GetClearance, an AI-native KYC/AML platform. I'm at ~80% complete and need to add OCR for document text extraction using AWS Textract.

**Current Repo:** https://github.com/autorevai/getclearance

## What Exists (Read These First)
I've uploaded 4 context files:
1. **01_CURRENT_STATE_AUDIT.md**
2. **02_FOLDER_STRUCTURE_COMPLETE.md**
3. **README.md**
4. **05_SUMSUB_CONTEXT.md** - Sumsub reverse engineering context ⭐

**Key existing components:**
- ✅ Storage service for downloading from R2
- ✅ Document model has `ocr_text` and `extracted_data` JSONB fields
- ✅ Document worker exists (will call OCR service)
- ❌ OCR service does NOT exist

**Reference Sumsub docs for MRZ validation:**
- https://docs.sumsub.com/docs/database-validation
- MRZ checksum validation is CRITICAL - easiest fraud detection with 100% accuracy

## What I Need You To Create

Create OCR service for document text extraction:

**Files to create:**
1. `backend/app/services/ocr.py` - AWS Textract integration
2. `backend/app/services/mrz_parser.py` - Passport MRZ validation

**Update:**
3. `backend/app/workers/document_worker.py` - Call OCR service

## Integration Requirements

**OCR Service must:**
- Download document from R2 using existing `storage_service`
- Call AWS Textract `detect_document_text` API
- Extract plain text → store in `document.ocr_text`
- Parse structured fields → store in `document.extracted_data`
- Detect quality issues → store in `document.fraud_analysis`

**MRZ Parser must:**
- Parse passport MRZ (2 lines, 44 chars each)
- Validate check digits using algorithm
- Extract: document_number, nationality, DOB, expiry, sex
- Return dict with parsed fields

**Document Worker integration:**
- Call `ocr_service.extract_text(document_id)`
- If passport: call `mrz_parser.parse_mrz(mrz_lines)`
- Update `document.status` to 'verified' or 'failed'
- Update `document.ocr_confidence` (0-100)

## Architecture Constraints

**AWS Textract:**
- Use aioboto3 for async
- Credentials from `app.config.settings`
- Timeout: 30 seconds
- Handle errors gracefully

**Quality Checks:**
- Detect blur using Laplacian variance
- Detect low resolution (< 300 DPI)
- Detect glare using histogram
- Store in `fraud_analysis` JSONB

## Success Criteria

- [ ] OCR extracts text from images/PDFs
- [ ] MRZ parser validates check digits
- [ ] Structured data in `extracted_data`
- [ ] Quality issues detected
- [ ] Document worker integrated
- [ ] Errors handled gracefully

## Expected Output Format

```python
# extract_text() should return:
{
    "ocr_text": "full text...",
    "extracted_data": {
        "document_number": "ABC123456",
        "full_name": "JOHN DOE",
        "date_of_birth": "1990-01-15",
        "expiry_date": "2030-01-15",
        "nationality": "USA"
    },
    "quality_issues": [
        {"issue": "slight_blur", "severity": "low"}
    ],
    "ocr_confidence": 95
}
```

## Questions?
If unclear about document model or storage service, ask first.
```

---

## 📊 Implementation Timeline

| Phase | Duration | Status | Files |
|-------|----------|--------|-------|
| Phase 1 | ~~Week 1~~ | ✅ DONE | 0 (services exist) |
| Phase 2 | Week 1 | 🔴 TODO | 5 (workers) |
| Phase 3 | Week 2 | 🟡 TODO | 2 new, 1 update |
| Phase 4 | Week 3 | 🟢 TODO | 3 (webhooks) |
| Phase 5 | Week 3-4 | 🟢 TODO | 2 (evidence) |
| Phase 6 | Week 4-5 | 🟢 TODO | 6 (tests) |
| Phase 7 | Week 5 | 🔵 TODO | 2-3 (deployment) |

**Total:** 4-5 weeks to production

---

## ✅ Pre-Chat Checklist

Before starting each chat:

- [ ] Read current state audit
- [ ] Know which files to create
- [ ] Upload all context files
- [ ] Use prompt template
- [ ] Have clear success criteria
- [ ] Understand integration points

---

**You're 74% done - let's finish strong!** 🚀
