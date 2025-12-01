# Master Chat Prompts - Copy & Paste Ready
**Purpose:** Ready-to-use prompts for each implementation chat  
**How to Use:** Copy the entire prompt for the chat you're starting

---

## 📦 Files to Upload to EVERY Chat

Before starting ANY chat, upload these 4 files:

1. ✅ `01_CURRENT_STATE_AUDIT.md`
2. ✅ `02_FOLDER_STRUCTURE_COMPLETE.md`
3. ✅ `05_SUMSUB_CONTEXT.md`
4. ✅ `README.md` (from your getclearance repo, NOT from this package)

**Optional but helpful:**
5. `03_CONTEXT_BUNDLE_TEMPLATE.md`

---

## Chat 1: Schema Migration (1 Day)

### Files to Upload:
1. `01_CURRENT_STATE_AUDIT.md`
2. `02_FOLDER_STRUCTURE_COMPLETE.md`
3. `05_SUMSUB_CONTEXT.md`
4. `README.md` (from repo)

### Prompt (Copy This):

```
# CHAT TITLE: Apply Schema Migration for Sumsub Features

## Context
I'm building GetClearance, an AI-native KYC/AML platform (Sumsub clone). I'm at 74% complete. The core services layer is complete, but the database schema needs minor enhancements to support Sumsub-style features like fuzzy matching confidence scores and fraud detection.

**Current Repo:** https://github.com/autorevai/getclearance

## What Exists (Read These First)
I've uploaded 4 context files - please read them first:

1. **01_CURRENT_STATE_AUDIT.md** - Shows current project status (74% complete)
2. **02_FOLDER_STRUCTURE_COMPLETE.md** - Complete directory tree
3. **05_SUMSUB_CONTEXT.md** - We're building a Sumsub competitor
4. **README.md** - Project README from my repo

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
   - Add `security_features_detected` JSONB DEFAULT '[]' - Array of detected features
   - Add `fraud_analysis` JSONB DEFAULT '{}' - Fraud detection results

3. **Create `webhook_deliveries` table:**
   - id (UUID), tenant_id (UUID FK), webhook_url (VARCHAR 500)
   - event_type (VARCHAR 100), event_id (UUID), payload (JSONB)
   - attempt_count (INTEGER DEFAULT 0), last_attempt_at (TIMESTAMPTZ)
   - next_retry_at (TIMESTAMPTZ), status (VARCHAR 50 DEFAULT 'pending')
   - http_status (INTEGER), response_body (TEXT), created_at (TIMESTAMPTZ)
   - Indexes: (tenant_id), (status, next_retry_at) WHERE status='pending', (event_type, event_id)

4. **Create `applicant_events` table:**
   - id (UUID), tenant_id (UUID FK), applicant_id (UUID FK)
   - event_type (VARCHAR 100), event_data (JSONB)
   - actor_type (VARCHAR 50), actor_id (UUID), timestamp (TIMESTAMPTZ)
   - Indexes: (applicant_id, timestamp DESC), (tenant_id), (event_type)

5. **Create `kyc_share_tokens` table (future feature):**
   - id (UUID), tenant_id (UUID FK), applicant_id (UUID FK)
   - token (VARCHAR 64 UNIQUE), scope (JSONB), user_consent (JSONB)
   - created_at (TIMESTAMPTZ), expires_at (TIMESTAMPTZ), revoked_at (TIMESTAMPTZ)
   - access_count (INTEGER DEFAULT 0), last_accessed_at (TIMESTAMPTZ), last_accessed_by (VARCHAR 255)
   - Indexes: (token UNIQUE), (applicant_id), (token, expires_at) WHERE revoked_at IS NULL

## Integration Requirements

**Must:**
- Use PostgreSQL-specific types (JSONB, UUID, TIMESTAMPTZ)
- Include both upgrade() and downgrade() functions
- Use proper SQLAlchemy syntax for Alembic
- Add server defaults where appropriate (DEFAULT '[]', DEFAULT 'pending', etc.)
- Include comments explaining each change

**Follow existing patterns:**
- Look at `migrations/versions/20251130_001_initial_schema.py` for style
- Use `op.create_table()`, `op.add_column()`, `op.alter_column()`
- Use `sa.Column()` for column definitions
- Use `postgresql.UUID(as_uuid=True)` for UUID columns
- Use `postgresql.JSONB` for JSON columns

## Architecture Constraints

**Alembic Format:**
- Revision ID: '20251130_002'
- Down revision: '20251130_001'
- Include docstring explaining changes
- upgrade() function applies changes
- downgrade() function reverts changes

**PostgreSQL Specifics:**
- Use server_default for JSONB: `server_default='[]'` or `server_default='{}'`
- Use server_default for timestamps: `server_default=sa.text('now()')`
- Use gen_random_uuid() for UUID defaults: `server_default=sa.text('gen_random_uuid()')`

## Success Criteria

- [ ] Migration file created in `backend/migrations/versions/20251130_002_add_sumsub_features.py`
- [ ] All 5 table changes included
- [ ] All indexes added for performance
- [ ] Downgrade function reverses all changes completely
- [ ] Can run `alembic upgrade head` successfully
- [ ] Can run `alembic downgrade -1` successfully
- [ ] No syntax errors
- [ ] Follows existing migration file patterns

## Reference
See `05_SUMSUB_CONTEXT.md` for why these changes support Sumsub-style features.

## Questions?
If anything is unclear about the existing schema or Alembic patterns, ask before implementing.
```

---

## Chat 2: Background Workers (5-7 Days)

### Files to Upload:
1. `01_CURRENT_STATE_AUDIT.md`
2. `02_FOLDER_STRUCTURE_COMPLETE.md`
3. `05_SUMSUB_CONTEXT.md`
4. `README.md` (from repo)
5. `03_CONTEXT_BUNDLE_TEMPLATE.md` (optional)

### Prompt (Copy This):

```
# CHAT TITLE: Create Background Workers (ARQ Setup)

## Context
I'm building GetClearance, an AI-native KYC/AML platform (Sumsub competitor). I'm at 74% complete and need to add background job processing using ARQ (Redis-based async task queue).

**Current Repo:** https://github.com/autorevai/getclearance

## What Exists (Read These First)
I've uploaded 4 context files - please read them first:

1. **01_CURRENT_STATE_AUDIT.md** - Current state audit (74% complete)
2. **02_FOLDER_STRUCTURE_COMPLETE.md** - Complete folder structure
3. **05_SUMSUB_CONTEXT.md** - Sumsub competitor context
4. **README.md** - Project README

**Key existing components:**
- ✅ Services layer exists: `app/services/screening.py`, `storage.py`, `ai.py`
- ✅ Models exist: `app/models/applicant.py`, `screening.py`, `document.py`
- ✅ API endpoints exist and are functional
- ✅ Redis configured in docker-compose.yml
- ❌ Workers directory does NOT exist yet

## What I Need You To Create

Create the background workers system for async processing:

**Files to create:**
1. `backend/app/workers/__init__.py` - Module exports
2. `backend/app/workers/config.py` - ARQ configuration
3. `backend/app/workers/screening_worker.py` - Run screening in background
4. `backend/app/workers/document_worker.py` - Process documents (OCR placeholder)
5. `backend/app/workers/ai_worker.py` - Generate risk summaries in background

## Integration Requirements

**Must call existing services:**
- `screening_worker.py` → calls `from app.services import screening_service`
  - Call `screening_service.check_individual(name, dob, country)`
  - Store results in `screening_hits` table
  
- `document_worker.py` → calls `from app.services import storage_service`
  - Download document from R2
  - Placeholder for OCR (will add in Phase 3)
  - Update `documents.status`
  
- `ai_worker.py` → calls `from app.services import ai_service`
  - Call `ai_service.generate_risk_summary(db, applicant_id)`
  - Store result in `ai_assessments` table (if exists) or applicant record

**Must update database:**
- Update `applicants.status` when jobs complete
- Update `screening_checks.status` when screening completes
- Update `documents.status` when processing completes
- Create entries in `applicant_events` for timeline

**Must use existing patterns:**
- Import DB from `app.database` (`from app.database import get_db`)
- Use async with for sessions
- Handle errors gracefully (try/except, don't crash worker)
- Log progress for monitoring

## Architecture Constraints

**ARQ Configuration (`config.py`):**
```python
from arq.connections import RedisSettings
from app.config import settings

class WorkerSettings:
    redis_settings = RedisSettings(
        host=settings.redis_host,
        port=settings.redis_port,
    )
    
    functions = [
        'app.workers.screening_worker.run_screening',
        'app.workers.document_worker.process_document',
        'app.workers.ai_worker.generate_risk_assessment',
    ]
    
    job_timeout = 300  # 5 minutes
    max_tries = 3
    retry_jobs = True
```

**Worker Function Pattern:**
```python
async def worker_function(ctx, param1: str, param2: str):
    """Docstring explaining what this does."""
    logger = ctx.get('logger')
    
    try:
        logger.info(f"Job started: {param1}")
        
        # Get DB session
        from app.database import get_db
        async with get_db() as db:
            # Do work here
            pass
        
        logger.info("Job completed")
        return {"status": "success"}
        
    except Exception as e:
        logger.error(f"Job failed: {e}")
        raise  # ARQ will retry
```

**Database Pattern:**
```python
from sqlalchemy import select
from app.models import Applicant

async with get_db() as db:
    result = await db.execute(
        select(Applicant).where(Applicant.id == applicant_id)
    )
    applicant = result.scalar_one_or_none()
    
    if applicant:
        applicant.status = 'approved'
        await db.commit()
```

## Success Criteria

- [ ] `backend/app/workers/` directory created
- [ ] All 5 files created with proper structure
- [ ] Workers can be started: `arq app.workers.config.WorkerSettings`
- [ ] Jobs can be enqueued from API (example in screening.py endpoint)
- [ ] Errors are logged, worker doesn't crash
- [ ] Database updates happen in transactions
- [ ] Each worker has docstrings and type hints
- [ ] Follows async/await patterns

## Additional Context

**How to enqueue jobs from API:**
```python
from arq import create_pool
from app.workers.config import WorkerSettings

# In API endpoint:
async def trigger_screening(applicant_id: UUID):
    redis = await create_pool(WorkerSettings.redis_settings)
    job = await redis.enqueue_job(
        'run_screening',
        applicant_id,
        check_type='full'
    )
    return {"job_id": str(job.job_id)}
```

**Example worker flow:**
1. User creates applicant via API
2. API immediately returns applicant (status='pending')
3. API enqueues screening_worker job
4. Worker runs screening in background
5. Worker updates applicant status to 'review' or 'approved'
6. Frontend polls for status updates (or webhook notifies)

## Sumsub Reference
See `05_SUMSUB_CONTEXT.md` for Sumsub's async processing patterns.

## Questions?
If anything is unclear about existing services, models, or database patterns, ask before implementing.
```

---

## Chat 3: OCR Service (5-7 Days)

### Files to Upload:
1. `01_CURRENT_STATE_AUDIT.md`
2. `02_FOLDER_STRUCTURE_COMPLETE.md`
3. `05_SUMSUB_CONTEXT.md`
4. `README.md` (from repo)

### Prompt (Copy This):

```
# CHAT TITLE: Create OCR Service (AWS Textract Integration)

## Context
I'm building GetClearance, an AI-native KYC/AML platform (Sumsub clone). I'm at ~80% complete and need to add OCR for document text extraction using AWS Textract.

**Current Repo:** https://github.com/autorevai/getclearance

## What Exists (Read These First)
I've uploaded 4 context files:

1. **01_CURRENT_STATE_AUDIT.md** - Current state
2. **02_FOLDER_STRUCTURE_COMPLETE.md** - Directory tree
3. **05_SUMSUB_CONTEXT.md** - Sumsub competitor context (see MRZ validation section)
4. **README.md** - Project README

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
2. `backend/app/services/mrz_parser.py` - Passport MRZ validation with checksum

**Update:**
3. `backend/app/workers/document_worker.py` - Call OCR service

## Integration Requirements

**OCR Service (`ocr.py`) must:**
- Download document from R2 using existing `storage_service.create_presigned_download()`
- Call AWS Textract `detect_document_text` API
- Extract plain text → return for storage in `document.ocr_text`
- Parse structured fields → return for storage in `document.extracted_data`
- Detect quality issues → return for storage in `document.fraud_analysis`
- Return confidence score (0-100)

**MRZ Parser (`mrz_parser.py`) must:**
- Parse passport MRZ (2 lines, 44 characters each)
- Validate check digits using algorithm (see Sumsub docs)
- Extract: document_number, nationality, DOB, expiry, sex, given_names, surname
- Return dict with parsed fields + validation status
- Raise MRZValidationError if checksum fails

**Document Worker integration:**
- Call `ocr_service.extract_text(document_id)` 
- If document type is 'passport': call `mrz_parser.parse_mrz(mrz_lines)`
- Update `document.status` to 'verified' or 'failed'
- Update `document.ocr_confidence` (0-100)
- Store fraud signals if quality issues detected

## Architecture Constraints

**AWS Textract (`ocr.py`):**
- Use aioboto3 for async: `import aioboto3`
- Credentials from `app.config.settings.aws_access_key_id`
- Region from `app.config.settings.aws_region`
- Timeout: 30 seconds per document
- Handle PDF and image formats (JPEG, PNG)

**Error Handling:**
```python
class OCRServiceError(Exception):
    """Raised when OCR API fails"""
    pass

class OCRConfigError(Exception):
    """Raised when AWS not configured"""
    pass

class MRZValidationError(Exception):
    """Raised when MRZ checksum fails"""
    pass
```

**Quality Checks (in `ocr.py`):**
- Detect blur using Laplacian variance (OpenCV: `cv2.Laplacian().var() < 100`)
- Detect low resolution (check image dimensions / DPI)
- Detect glare using histogram (bright spots > threshold)
- Store in `fraud_analysis` JSONB: `[{"issue": "blur", "severity": "high", "confidence": 85}]`

**MRZ Checksum Algorithm:**
```python
# Weights: 731731731... repeating
# For each character: convert to number (0-9 stay same, A-Z = 10-35)
# Multiply by weight, sum, mod 10
# Compare to check digit
```

## Success Criteria

- [ ] OCR service extracts text from images/PDFs
- [ ] MRZ parser validates passport check digits correctly
- [ ] Structured data stored in `extracted_data` JSONB
- [ ] Quality issues detected (blur, resolution, glare)
- [ ] Document worker calls OCR service
- [ ] Errors handled gracefully (OCRServiceError, OCRConfigError)
- [ ] Service has docstrings and type hints
- [ ] Can process passport, ID card, driver's license

## Expected Output Format

**`ocr.py` extract_text() should return:**
```python
{
    "ocr_text": "full extracted text...",
    "extracted_data": {
        "document_number": "ABC123456",
        "full_name": "JOHN MICHAEL DOE",
        "date_of_birth": "1990-01-15",
        "expiry_date": "2030-01-15",
        "nationality": "USA",
        "sex": "M"
    },
    "quality_issues": [
        {"issue": "slight_blur", "severity": "low", "confidence": 65}
    ],
    "ocr_confidence": 95
}
```

**`mrz_parser.py` parse_mrz() should return:**
```python
{
    "document_number": "ABC123456",
    "nationality": "USA",
    "date_of_birth": "1990-01-15",
    "sex": "M",
    "expiry_date": "2030-01-15",
    "given_names": "JOHN MICHAEL",
    "surname": "DOE",
    "checksum_valid": True,
    "mrz_line_1": "P<USADOE<<JOHN<MICHAEL<<<<<<<<<<<<<<<<<<<<<",
    "mrz_line_2": "ABC1234569USA9001155M3001155<<<<<<<<<<<<<<04"
}
```

## Sumsub Reference
See `05_SUMSUB_CONTEXT.md` Section 6 (Document Verification) for:
- MRZ checksum validation
- Security feature detection
- Quality checks

## Questions?
If unclear about document model, storage service, or MRZ algorithm, ask first.
```

---

## Chat 4: Webhook Service (3-4 Days)

### Files to Upload:
1. `01_CURRENT_STATE_AUDIT.md`
2. `02_FOLDER_STRUCTURE_COMPLETE.md`
3. `05_SUMSUB_CONTEXT.md`
4. `README.md` (from repo)

### Prompt (Copy This):

```
# CHAT TITLE: Create Webhook Service (Delivery with Retry)

## Context
I'm building GetClearance, an AI-native KYC/AML platform (Sumsub clone). I'm at ~85% complete and need to add webhook notifications for customer integrations.

**Current Repo:** https://github.com/autorevai/getclearance

## What Exists (Read These First)
I've uploaded 4 context files:

1. **01_CURRENT_STATE_AUDIT.md** - Current state
2. **02_FOLDER_STRUCTURE_COMPLETE.md** - Directory tree  
3. **05_SUMSUB_CONTEXT.md** - Sumsub webhook patterns
4. **README.md** - Project README

**Key existing components:**
- ✅ `webhook_deliveries` table exists (from schema migration)
- ✅ Workers infrastructure exists (ARQ)
- ✅ Applicants, screening, documents all trigger events
- ❌ Webhook service does NOT exist

**Reference Sumsub webhook docs:**
- https://docs.sumsub.com/docs/aml-screening-events
- Retry pattern: 3 attempts (0s, 30s, 5 minutes)
- HMAC signature verification

## What I Need You To Create

Create webhook delivery system:

**Files to create:**
1. `backend/app/services/webhook.py` - Webhook delivery service
2. `backend/app/workers/webhook_worker.py` - Background webhook delivery
3. `backend/app/schemas/webhook.py` - Webhook payload schemas

## Integration Requirements

**Webhook Service (`webhook.py`) must:**
- Send HTTP POST to customer webhook URLs
- Generate HMAC-SHA256 signature for payload verification
- Store delivery attempts in `webhook_deliveries` table
- Handle success (200-299), retryable errors (500+), permanent failures (400-499)
- Enqueue retry jobs for failed deliveries

**Webhook Worker (`webhook_worker.py`) must:**
- Process webhook delivery jobs from queue
- Implement retry logic: 3 attempts with delays (0s, 30s, 5min)
- Update `webhook_deliveries.status` and `webhook_deliveries.attempt_count`
- Stop retrying after 3 attempts or permanent failure
- Log all delivery attempts

**Webhook Schemas (`webhook.py` in schemas) must:**
- Define event payload structures for:
  - `applicant.reviewed` - When applicant approved/rejected
  - `screening.completed` - When AML screening finishes
  - `document.verified` - When document verification completes
  - `case.created` - When manual review case created

## Architecture Constraints

**Webhook Delivery Pattern:**
```python
# In webhook.py service
async def send_webhook(
    tenant_id: UUID,
    event_type: str,
    event_id: UUID,
    payload: dict,
) -> UUID:
    """Send webhook and return webhook_delivery_id"""
    
    # Get tenant's webhook URL from database
    # Create webhook_deliveries record
    # Enqueue webhook_worker job
    # Return delivery_id for tracking
```

**HMAC Signature:**
```python
import hmac
import hashlib

def generate_signature(payload: str, secret: str) -> str:
    """Generate HMAC-SHA256 signature"""
    return hmac.new(
        secret.encode(),
        payload.encode(),
        hashlib.sha256
    ).hexdigest()

# Include in headers:
# X-Webhook-Signature: {signature}
# X-Webhook-Timestamp: {unix_timestamp}
```

**Retry Logic (in worker):**
```python
RETRY_DELAYS = [0, 30, 300]  # 0s, 30s, 5min

async def deliver_webhook(ctx, delivery_id: UUID):
    # Get webhook_delivery record
    # Make HTTP request
    # If success: update status='delivered'
    # If retryable error: schedule retry if attempts < 3
    # If permanent error: update status='failed'
```

**Event Payload Example:**
```python
# applicant.reviewed event
{
    "event_type": "applicant.reviewed",
    "event_id": "uuid",
    "timestamp": "2025-11-30T12:00:00Z",
    "tenant_id": "uuid",
    "data": {
        "applicant_id": "uuid",
        "external_id": "customer-ref-123",
        "status": "approved",
        "risk_score": 15,
        "review_decision": "auto_approved"
    }
}
```

## Success Criteria

- [ ] Webhook service can send POST requests
- [ ] HMAC signatures generated correctly
- [ ] Retry logic follows Sumsub pattern (3 attempts: 0s, 30s, 5min)
- [ ] Webhook deliveries stored in database
- [ ] Worker processes jobs asynchronously
- [ ] Handles success/failure/retry cases
- [ ] Has proper error handling (timeouts, connection errors)
- [ ] Can configure webhook URL per tenant

## Sumsub Reference
See `05_SUMSUB_CONTEXT.md` Section 10.1 for:
- Webhook retry pattern
- HMAC signature verification
- Idempotency with correlationId

## Questions?
If unclear about worker patterns or webhook_deliveries schema, ask first.
```

---

## Chat 5: Evidence Export (3-4 Days)

### Files to Upload:
1. `01_CURRENT_STATE_AUDIT.md`
2. `02_FOLDER_STRUCTURE_COMPLETE.md`
3. `05_SUMSUB_CONTEXT.md`
4. `README.md` (from repo)

### Prompt (Copy This):

```
# CHAT TITLE: Create Evidence Export Service (PDF Generation)

## Context
I'm building GetClearance, an AI-native KYC/AML platform (Sumsub clone). I'm at ~90% complete and need to add evidence pack export for compliance audits.

**Current Repo:** https://github.com/autorevai/getclearance

## What Exists (Read These First)
I've uploaded 4 context files:

1. **01_CURRENT_STATE_AUDIT.md** - Current state
2. **02_FOLDER_STRUCTURE_COMPLETE.md** - Directory tree
3. **05_SUMSUB_CONTEXT.md** - Compliance requirements
4. **README.md** - Project README

**Key existing components:**
- ✅ `applicant_events` table exists (from schema migration)
- ✅ `audit_log` table exists with chain hashing
- ✅ All verification data in database
- ❌ Evidence export service does NOT exist

## What I Need You To Create

Create evidence export system:

**Files to create:**
1. `backend/app/services/evidence.py` - PDF generation service
2. `backend/app/services/timeline.py` - Event aggregation service

**Update:**
3. Add API endpoint in `backend/app/api/v1/applicants.py`:
   - `GET /applicants/{id}/evidence` - Download evidence PDF

## Integration Requirements

**Evidence Service (`evidence.py`) must:**
- Generate PDF with all verification evidence
- Include: applicant data, documents, screening results, AI assessments, timeline
- Include source citations for all data points
- Add chain-of-custody information from audit_log
- Watermark with "Official Evidence Pack" + timestamp
- Return PDF as bytes for download

**Timeline Service (`timeline.py`) must:**
- Aggregate events from `applicant_events` table
- Group by date
- Include: actor info, event type, changes made
- Return chronologically ordered events

**API Endpoint must:**
- Verify user has permission to export
- Call evidence service to generate PDF
- Return PDF with proper headers (Content-Disposition: attachment)
- Log export in audit_log

## Architecture Constraints

**PDF Generation (use ReportLab):**
```python
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table
from reportlab.lib.styles import getSampleStyleSheet

async def generate_evidence_pdf(applicant_id: UUID) -> bytes:
    """Generate evidence pack PDF"""
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter)
    
    story = []
    styles = getSampleStyleSheet()
    
    # Add title, applicant data, documents, screening, timeline
    # ...
    
    doc.build(story)
    return buffer.getvalue()
```

**Evidence Pack Structure:**
```
1. Cover Page
   - Title: "Evidence Pack - [Applicant Name]"
   - Generated: [Timestamp]
   - Applicant ID: [UUID]
   - External Reference: [External ID]

2. Applicant Information
   - Personal details
   - Risk score and status
   - Verification level

3. Documents
   - For each document:
     - Document type and number
     - OCR text and extracted data
     - Fraud analysis results
     - Verification status

4. Screening Results
   - For each screening check:
     - Check type and date
     - Hits found (with confidence scores)
     - Match classifications
     - List versions used

5. AI Assessments
   - Risk summary with citations
   - Key concerns flagged
   - Recommendation

6. Timeline
   - Chronological event log
   - Who did what when

7. Chain of Custody
   - Audit log hashes
   - Verification that data hasn't been tampered with
```

**Timeline Aggregation:**
```python
async def get_applicant_timeline(
    db: AsyncSession,
    applicant_id: UUID
) -> list[dict]:
    """Get chronological event timeline"""
    
    events = await db.execute(
        select(ApplicantEvent)
        .where(ApplicantEvent.applicant_id == applicant_id)
        .order_by(ApplicantEvent.timestamp.desc())
    )
    
    return [
        {
            "timestamp": event.timestamp,
            "event_type": event.event_type,
            "actor": event.actor_type,
            "details": event.event_data
        }
        for event in events.scalars()
    ]
```

## Success Criteria

- [ ] Evidence service generates PDF successfully
- [ ] PDF includes all required sections
- [ ] Timeline shows events chronologically
- [ ] Chain-of-custody information included
- [ ] API endpoint returns downloadable PDF
- [ ] PDF has proper formatting (readable, professional)
- [ ] Export logged in audit_log
- [ ] Works for applicants with/without screening hits

## Additional Context

**Use Cases:**
1. Regulator requests evidence of verification
2. Customer needs proof of compliance
3. Internal audit trail
4. Legal dispute resolution

**SOC 2 Requirements:**
- Must include data provenance (where each field came from)
- Must include timestamps for all actions
- Must prove data integrity (audit log hashes)
- Must be tamper-evident

## Sumsub Reference
See `05_SUMSUB_CONTEXT.md` Section 10.1 for evidence requirements.

## Questions?
If unclear about audit_log schema or chain hashing, ask first.
```

---

## Chat 6: Testing (7-10 Days)

### Files to Upload:
1. `01_CURRENT_STATE_AUDIT.md`
2. `02_FOLDER_STRUCTURE_COMPLETE.md`
3. `05_SUMSUB_CONTEXT.md`
4. `README.md` (from repo)

### Prompt (Copy This):

```
# CHAT TITLE: Create Comprehensive Test Suite

## Context
I'm building GetClearance, an AI-native KYC/AML platform (Sumsub clone). Implementation is ~95% complete. Now I need comprehensive testing before production deployment.

**Current Repo:** https://github.com/autorevai/getclearance

## What Exists (Read These First)
I've uploaded 4 context files:

1. **01_CURRENT_STATE_AUDIT.md** - What's been built
2. **02_FOLDER_STRUCTURE_COMPLETE.md** - Directory tree
3. **05_SUMSUB_CONTEXT.md** - Feature requirements
4. **README.md** - Project README

**Key existing components:**
- ✅ All services implemented (screening, storage, AI, OCR, webhooks, evidence)
- ✅ All workers implemented
- ✅ All API endpoints functional
- ⏳ Minimal test coverage (~10%)

## What I Need You To Create

Create comprehensive test suite:

**Unit Tests (create these files):**
1. `backend/tests/test_screening.py` - Screening service tests
2. `backend/tests/test_storage.py` - Storage service tests
3. `backend/tests/test_ai.py` - AI service tests
4. `backend/tests/test_workers.py` - Worker tests

**Integration Tests (create directory + files):**
5. `backend/tests/integration/__init__.py`
6. `backend/tests/integration/test_full_applicant_flow.py` - E2E applicant flow
7. `backend/tests/integration/test_screening_flow.py` - E2E screening flow

**Update:**
8. `backend/tests/conftest.py` - Add fixtures for all services

## Integration Requirements

**Test Infrastructure:**
- Use pytest + pytest-asyncio
- Use pytest fixtures for DB, Redis, services
- Mock external APIs (OpenSanctions, AWS Textract, Claude)
- Use in-memory databases for tests (SQLite async)

**Coverage Requirements:**
- Unit tests: >80% coverage for services
- Integration tests: Cover critical user flows
- Edge cases: Error handling, retries, timeouts
- Data validation: Invalid inputs, boundary cases

## Architecture Constraints

**Test Fixtures (`conftest.py`):**
```python
import pytest
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from httpx import AsyncClient

@pytest.fixture
async def db():
    """Test database session"""
    engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:"
    )
    # Create tables, yield session, cleanup

@pytest.fixture
async def client():
    """Test API client"""
    async with AsyncClient(app=app, base_url="http://test") as ac:
        yield ac

@pytest.fixture
def mock_opensanctions():
    """Mock OpenSanctions API"""
    # Return mock screening results
```

**Unit Test Example:**
```python
# test_screening.py
import pytest
from unittest.mock import AsyncMock
from app.services.screening import ScreeningService

@pytest.mark.asyncio
async def test_fuzzy_matching():
    """Test confidence scoring algorithm"""
    service = ScreeningService()
    
    # Test exact match (should be 90-100)
    score = service._calculate_confidence(
        query_name="John Doe",
        query_dob="1990-01-15",
        match_names=["John Doe"],
        match_dobs=["1990-01-15"]
    )
    assert score >= 90
    
    # Test partial match (should be 60-89)
    score = service._calculate_confidence(
        query_name="John Doe",
        query_dob="1990-01-15",
        match_names=["John Smith"],
        match_dobs=["1990-01-15"]
    )
    assert 60 <= score < 90
```

**Integration Test Example:**
```python
# test_full_applicant_flow.py
@pytest.mark.asyncio
async def test_complete_kyc_flow(client, db):
    """Test end-to-end KYC verification"""
    
    # 1. Create applicant
    response = await client.post("/api/v1/applicants", json={
        "email": "test@example.com",
        "first_name": "John",
        "last_name": "Doe"
    })
    assert response.status_code == 201
    applicant_id = response.json()["id"]
    
    # 2. Upload document
    # 3. Trigger screening
    # 4. Wait for workers to process
    # 5. Check final status
    
    # Final assertion
    response = await client.get(f"/api/v1/applicants/{applicant_id}")
    assert response.json()["status"] in ["approved", "review"]
```

## Success Criteria

- [ ] All 7 test files created
- [ ] Unit tests cover >80% of service code
- [ ] Integration tests cover happy path + error cases
- [ ] All tests pass: `pytest tests/`
- [ ] Can run with coverage: `pytest --cov=app tests/`
- [ ] Tests run in < 60 seconds
- [ ] No flaky tests (run 10 times, all pass)
- [ ] Mock all external APIs (no real API calls in tests)

## Test Coverage Requirements

**Must test:**
- Fuzzy matching algorithm (various name/DOB combinations)
- MRZ checksum validation (valid + invalid)
- Webhook retry logic (success, retryable error, permanent failure)
- Worker job processing (success, failure, retry)
- Document quality checks (blur, resolution, glare)
- PDF generation (complete evidence pack)
- API error handling (400, 404, 500 responses)

## Sumsub Reference
See `05_SUMSUB_CONTEXT.md` for feature requirements to test against.

## Questions?
If unclear about existing services or test patterns, ask first.
```

---

## Chat 7: Deployment (3-5 Days)

### Files to Upload:
1. `01_CURRENT_STATE_AUDIT.md`
2. `02_FOLDER_STRUCTURE_COMPLETE.md`
3. `05_SUMSUB_CONTEXT.md`
4. `13_DEPLOYMENT_CHECKLIST.md`
5. `README.md` (from repo)

### Prompt (Copy This):

```
# CHAT TITLE: Deploy to Production (Railway)

## Context
I'm building GetClearance, an AI-native KYC/AML platform (Sumsub clone). Development is 100% complete and tested. Ready for production deployment on Railway.

**Current Repo:** https://github.com/autorevai/getclearance

## What Exists (Read These First)
I've uploaded 5 context files:

1. **01_CURRENT_STATE_AUDIT.md** - Final state (100% complete)
2. **02_FOLDER_STRUCTURE_COMPLETE.md** - Directory tree
3. **05_SUMSUB_CONTEXT.md** - Product requirements
4. **13_DEPLOYMENT_CHECKLIST.md** - Detailed deployment guide
5. **README.md** - Project README

**Current deployment state:**
- ✅ All code complete and tested
- ✅ Dockerfile exists
- ⏳ Railway configuration needed
- ⏳ Production environment setup needed

## What I Need You To Create

Create deployment configuration:

**Files to create:**
1. `railway.json` - Railway.app deployment config (optional but helpful)
2. `docs/DEPLOYMENT_GUIDE.md` - Step-by-step deployment instructions
3. `.env.production.example` - Template for production environment variables

**Update:**
4. `.env.example` - Add all new environment variables documented

## Integration Requirements

**Railway Configuration:**
- Configure build command
- Configure start command (with migrations)
- Configure health check endpoint
- Set restart policy

**Environment Variables Needed:**
```bash
# Core
ENVIRONMENT=production
SECRET_KEY=<generated>
DEBUG=false

# Database (Railway provides)
DATABASE_URL=<railway-postgres-url>

# Redis (Railway provides)
REDIS_URL=<railway-redis-url>

# Auth0
AUTH0_DOMAIN=getclearance.auth0.com
AUTH0_CLIENT_ID=<from-auth0>
AUTH0_CLIENT_SECRET=<from-auth0>
AUTH0_AUDIENCE=https://api.getclearance.com

# Cloudflare R2
R2_ENDPOINT=<r2-endpoint>
R2_ACCESS_KEY_ID=<r2-key>
R2_SECRET_ACCESS_KEY=<r2-secret>
R2_BUCKET=getclearance-prod-docs

# APIs
ANTHROPIC_API_KEY=sk-ant-<key>
OPENSANCTIONS_API_KEY=<key>
AWS_ACCESS_KEY_ID=<key>
AWS_SECRET_ACCESS_KEY=<secret>
AWS_REGION=us-east-1

# Monitoring
SENTRY_DSN=<sentry-dsn>

# CORS
CORS_ORIGINS=https://app.getclearance.com
```

**Deployment Steps Guide Should Include:**
1. Create Railway project
2. Connect GitHub repo
3. Provision PostgreSQL database
4. Provision Redis instance
5. Set environment variables
6. Deploy backend
7. Run database migrations
8. Configure custom domain
9. Enable SSL
10. Test production endpoints
11. Set up monitoring
12. Configure alerts

## Architecture Constraints

**Start Command:**
```bash
# Should run migrations then start server
alembic upgrade head && uvicorn app.main:app --host 0.0.0.0 --port $PORT
```

**Health Check Endpoint:**
```python
@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "version": "1.0.0",
        "environment": settings.environment
    }
```

**Railway.json Example:**
```json
{
  "$schema": "https://railway.app/railway.schema.json",
  "build": {
    "builder": "NIXPACKS",
    "buildCommand": "pip install -r requirements.txt"
  },
  "deploy": {
    "startCommand": "alembic upgrade head && uvicorn app.main:app --host 0.0.0.0 --port $PORT",
    "restartPolicyType": "ON_FAILURE",
    "restartPolicyMaxRetries": 10
  }
}
```

## Success Criteria

- [ ] Railway project created and configured
- [ ] PostgreSQL and Redis provisioned
- [ ] All environment variables set
- [ ] Database migrations run successfully
- [ ] API is live and accessible
- [ ] Custom domain configured with SSL
- [ ] Health check endpoint returns 200
- [ ] Can create first test applicant
- [ ] Monitoring/alerts configured
- [ ] Deployment guide is clear and complete

## Production Readiness Checklist

**Before deploying:**
- [ ] All tests passing (>80% coverage)
- [ ] Security scan completed (no critical issues)
- [ ] Environment variables documented
- [ ] Database backup strategy defined
- [ ] Error monitoring configured (Sentry)
- [ ] Rate limiting enabled
- [ ] CORS properly configured
- [ ] API keys secured (not in code)

**After deploying:**
- [ ] Smoke tests pass (create applicant, upload doc, run screening)
- [ ] Performance acceptable (P99 latency <500ms)
- [ ] Error rate <1%
- [ ] Workers processing jobs
- [ ] Webhooks delivering
- [ ] Can export evidence PDFs

## Reference
Follow `13_DEPLOYMENT_CHECKLIST.md` for detailed Railway setup steps.

## Questions?
If unclear about Railway configuration or environment setup, ask first.
```

---

## 📊 Chat Summary

| Chat | Duration | Files Created | Priority |
|------|----------|---------------|----------|
| Chat 1: Schema Migration | 1 day | 1 migration file | 🔴 Critical |
| Chat 2: Background Workers | 5-7 days | 5 worker files | 🔴 Critical |
| Chat 3: OCR Service | 5-7 days | 2 services + 1 update | 🟡 Important |
| Chat 4: Webhook Service | 3-4 days | 3 files | 🟢 Nice-to-have |
| Chat 5: Evidence Export | 3-4 days | 2 services + 1 update | 🟢 Nice-to-have |
| Chat 6: Testing | 7-10 days | 7 test files | 🔴 Critical |
| Chat 7: Deployment | 3-5 days | 3 config files | 🔴 Critical |

**Total:** 27-38 days (4-5 weeks)

---

## ✅ Pre-Chat Checklist

Before starting EACH chat:

- [ ] Downloaded latest package
- [ ] Read relevant context files
- [ ] Uploaded 4 required context files to chat
- [ ] Copied complete prompt (not partial)
- [ ] Understand what you're asking for
- [ ] Ready to review output carefully

**Time investment:** 10 minutes prep per chat  
**Time saved:** 2-3 hours debugging per chat

---

**Copy the prompts exactly as shown - they're battle-tested and complete!** 🚀
