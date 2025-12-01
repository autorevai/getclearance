# Context Bundle Template for Multi-Chat Implementation
**Purpose:** Ensure each chat has the necessary context to create consistent, integrated code

---

## 🎯 Why This Template Exists

When breaking implementation across multiple Claude chats, each chat needs:
1. **Project Context** - Understanding of the overall system
2. **Current State** - What exists now
3. **Task Specifics** - Exactly what to create
4. **Integration Points** - How it fits with existing code
5. **Architecture Constraints** - Decisions already made

Without this context, chats might create conflicting code or miss important integration points.

---

## 📦 What to Upload to EVERY Chat

### Required Files (Upload These to Each Chat)

1. **`01_CURRENT_STATE_AUDIT.md`** - What exists vs what needs to be created
2. **`02_FOLDER_STRUCTURE_COMPLETE.md`** - Complete directory tree
3. **`README.md` (from repo)** - Current project status
4. **`05_SUMSUB_CONTEXT.md`** - Reverse engineering context & Sumsub links ⭐ NEW
5. **Chat-specific implementation file** - The specific code to create

### Optional but Recommended

6. **`docs/ARCHITECTURE.md`** - System design decisions
7. **`docs/CTO_HANDOFF.md`** - Project background
8. **Sumsub Analysis Transcript** - Full reverse engineering analysis (if needed)

---

## 📝 Prompt Template for Each Chat

Use this template structure for every implementation chat:

```
# CHAT TITLE: [Specific Task Name]

## Context
I'm building GetClearance, an AI-native KYC/AML platform (Sumsub clone). I'm at [X]% complete and implementing in phases to ensure quality.

**Current Repo:** https://github.com/autorevai/getclearance

## What Exists (Read These First)
I've uploaded 3 context files - please read them to understand the current state:

1. **01_CURRENT_STATE_AUDIT.md** - Shows what's already done vs what needs to be created
2. **02_FOLDER_STRUCTURE_COMPLETE.md** - Complete directory tree with status
3. **README.md** - Current project README

## What I Need You To Create
[Be very specific about files to create]

**Files to create:**
- `backend/app/[path]/[file1].py` - [Purpose]
- `backend/app/[path]/[file2].py` - [Purpose]

## Integration Requirements
[How these files integrate with existing code]

**Must integrate with:**
- Existing service in `app/services/screening.py`
- Existing models in `app/models/`
- Existing API in `app/api/v1/`

## Architecture Constraints
[Important decisions already made]

**Follow these patterns:**
- Use async/await for all DB operations
- Use FastAPI dependency injection
- Follow existing error handling patterns
- Multi-tenant by default (filter by tenant_id)

## Success Criteria
[How to know you're done]

- [ ] Files created in correct locations
- [ ] Code follows existing patterns
- [ ] Integrates with existing services
- [ ] Includes basic error handling
- [ ] Has docstrings

## Questions?
If anything is unclear about the existing code or architecture, ask before implementing.
```

---

## 🔧 Chat-Specific Examples

### Example 1: Chat 2 (Background Workers)

```
# CHAT TITLE: Create Background Workers (ARQ Setup)

## Context
I'm building GetClearance, an AI-native KYC/AML platform. I'm at 74% complete and need to add background job processing using ARQ (Redis-based async task queue).

**Current Repo:** https://github.com/autorevai/getclearance

## What Exists (Read These First)
I've uploaded 3 context files:
1. **01_CURRENT_STATE_AUDIT.md** - Current state audit
2. **02_FOLDER_STRUCTURE_COMPLETE.md** - Complete folder structure
3. **README.md** - Project README

Key existing components:
- ✅ Services layer exists: `screening.py`, `storage.py`, `ai.py`
- ✅ Models exist: `applicant.py`, `screening.py`, `document.py`
- ✅ API endpoints exist: All functional
- ❌ Workers directory does NOT exist

## What I Need You To Create

Create the background workers system for async processing:

**Files to create:**
1. `backend/app/workers/__init__.py` - Module exports
2. `backend/app/workers/config.py` - ARQ configuration
3. `backend/app/workers/screening_worker.py` - Run screening in background
4. `backend/app/workers/document_worker.py` - OCR + fraud detection in background
5. `backend/app/workers/ai_worker.py` - Generate risk summaries in background

## Integration Requirements

**Must integrate with existing services:**
- Call `app.services.screening.check_individual()` from screening_worker
- Call `app.services.storage.create_presigned_download()` from document_worker
- Call `app.services.ai.generate_risk_summary()` from ai_worker

**Must update database:**
- Update `applicants.status` when jobs complete
- Update `screening_checks.status` when screening completes
- Update `documents.status` when OCR completes

**Must use existing patterns:**
- Import database session from `app.database`
- Use `app.dependencies.get_db()` for DB access
- Follow existing error handling with try/except

## Architecture Constraints

**ARQ Configuration:**
- Use Redis from `app.config.settings.redis_url`
- Job timeout: 300 seconds (5 minutes)
- Max retries: 3
- Retry delay: exponential backoff

**Worker Functions:**
- Must be async def
- Must accept `ctx` parameter from ARQ
- Must handle errors gracefully (don't crash worker)
- Must log progress for monitoring

**Database Transactions:**
- Always use async with for sessions
- Always commit or rollback explicitly
- Handle connection errors

## Success Criteria

- [ ] `workers/` directory created in correct location
- [ ] All 5 files created
- [ ] Workers can be started with `arq app.workers.config.WorkerSettings`
- [ ] Jobs can be enqueued from API endpoints
- [ ] Errors are logged, not crashing the worker
- [ ] Database updates happen in transactions

## Additional Context

**ARQ Job Example (follow this pattern):**
```python
async def screening_worker(ctx, applicant_id: str, check_type: str):
    """Run screening check in background."""
    logger = ctx['logger']
    redis = ctx['redis']
    
    try:
        logger.info(f"Starting screening for applicant {applicant_id}")
        
        # Your implementation here
        
        logger.info(f"Screening complete for {applicant_id}")
        return {"status": "success"}
    except Exception as e:
        logger.error(f"Screening failed: {e}")
        raise  # ARQ will retry
```

## Questions?
If anything is unclear about existing services or database models, ask before implementing.
```

---

### Example 2: Chat 3 (OCR Service)

```
# CHAT TITLE: Create OCR Service (AWS Textract Integration)

## Context
I'm building GetClearance, an AI-native KYC/AML platform. I'm at 74% complete and need to add OCR for document text extraction using AWS Textract.

**Current Repo:** https://github.com/autorevai/getclearance

## What Exists (Read These First)
I've uploaded 3 context files:
1. **01_CURRENT_STATE_AUDIT.md** - Current state audit
2. **02_FOLDER_STRUCTURE_COMPLETE.md** - Complete folder structure
3. **README.md** - Project README

Key existing components:
- ✅ Storage service exists for downloading from R2
- ✅ Document model has `ocr_text` and `extracted_data` fields
- ✅ Document worker will call this OCR service
- ❌ OCR service does NOT exist yet

## What I Need You To Create

Create OCR service for document text extraction:

**Files to create:**
1. `backend/app/services/ocr.py` - AWS Textract integration
2. `backend/app/services/mrz_parser.py` - Passport MRZ validation

**Update:**
3. `backend/app/workers/document_worker.py` - Integrate OCR service

## Integration Requirements

**OCR Service must:**
- Download document from R2 using `storage_service.create_presigned_download()`
- Call AWS Textract API
- Extract text and store in `document.ocr_text`
- Parse structured fields into `document.extracted_data` (JSON)
- Detect document quality issues (blur, low resolution)

**MRZ Parser must:**
- Parse passport MRZ lines
- Validate check digits
- Extract: document_number, nationality, date_of_birth, expiry_date, sex
- Return structured dict

**Document Worker integration:**
- Call `ocr_service.extract_text(document_id)` 
- Call `mrz_parser.parse_mrz(mrz_line_1, mrz_line_2)` if passport
- Update document status to 'verified' or 'failed'
- Create fraud signals if quality issues detected

## Architecture Constraints

**AWS Textract:**
- Use boto3 async client (aioboto3)
- Credentials from `app.config.settings.aws_access_key_id`
- Region from `app.config.settings.aws_region`
- Timeout: 30 seconds per document

**Error Handling:**
- Raise `OCRServiceError` for API failures
- Raise `OCRConfigError` if AWS not configured
- Graceful degradation: return empty result if Textract unavailable
- Log all errors for debugging

**Quality Checks:**
- Detect blur (Laplacian variance < 100)
- Detect low resolution (< 300 DPI)
- Detect glare (bright spots in histogram)
- Store quality issues in `document.fraud_analysis`

## Success Criteria

- [ ] OCR service extracts text from images/PDFs
- [ ] MRZ parser validates passport check digits
- [ ] Document worker calls OCR service
- [ ] Quality issues are detected
- [ ] Structured data stored in `extracted_data`
- [ ] Errors handled gracefully

## Additional Context

**Expected Output Format:**
```python
# ocr.py extract_text() should return:
{
    "ocr_text": "full extracted text...",
    "extracted_data": {
        "document_number": "ABC123456",
        "full_name": "JOHN MICHAEL DOE",
        "date_of_birth": "1990-01-15",
        "expiry_date": "2030-01-15",
        "nationality": "USA"
    },
    "quality_issues": [
        {"issue": "slight_blur", "severity": "low", "confidence": 65}
    ]
}
```

## Questions?
If anything is unclear about document model or storage service, ask before implementing.
```

---

## 🔑 Key Principles

### 1. Always Provide Full Context
Each chat should know:
- What already exists
- What it's creating
- How it fits together

### 2. Be Explicit About Integration Points
Don't assume the chat knows how to integrate. Tell it:
- Which existing functions to call
- Which database fields to update
- Which patterns to follow

### 3. Define Success Criteria
Make it clear when the task is complete:
- [ ] Specific files created
- [ ] Specific functionality working
- [ ] Specific patterns followed

### 4. Provide Code Examples
Show the chat what "good" looks like:
- Copy existing patterns from the repo
- Show expected input/output formats
- Demonstrate error handling

---

## ✅ Checklist Before Starting Each Chat

Before you start a new implementation chat, ensure you:

1. [ ] Uploaded `01_CURRENT_STATE_AUDIT.md`
2. [ ] Uploaded `02_FOLDER_STRUCTURE_COMPLETE.md`
3. [ ] Uploaded `README.md` from repo
4. [ ] Read the current state audit yourself
5. [ ] Know exactly which files to create
6. [ ] Understand how they integrate
7. [ ] Have a clear success criteria
8. [ ] Written a detailed prompt using the template above

---

## 🚫 Common Mistakes to Avoid

### ❌ Don't Do This:
```
"Create background workers for me"
```
Too vague - chat doesn't know:
- What workers to create
- What they should do
- How they integrate
- What already exists

### ✅ Do This Instead:
```
I need to create ARQ background workers for async processing.

[Upload context files]

Please read the context files first to understand what exists.

Create these specific files:
1. workers/config.py - ARQ setup
2. workers/screening_worker.py - Call existing screening service
3. workers/document_worker.py - Call OCR service when ready

Integration: Workers must use existing services in app/services/
Pattern: Follow async def format, use ctx parameter, handle errors

Success: Workers can be started and jobs enqueued from API
```

---

## 📊 Estimated Time Savings

**Without Context Bundle:**
- Chat creates wrong patterns: 2-3 hours debugging
- Chat doesn't integrate properly: 1-2 hours fixing
- Chat misses requirements: 1-2 hours rework
- **Total wasted:** 4-7 hours per chat

**With Context Bundle:**
- Chat creates correct code first time
- Proper integration from start
- Follows existing patterns
- **Time saved:** 4-7 hours per chat × 7 chats = 28-49 hours saved

---

## 🎓 Example Success Story

**Bad approach:**
> "Chat 1: Create workers"  
> → Creates workers that don't match existing service signatures  
> → Need to refactor services  
> → 5 hours debugging

**Good approach:**
> "Chat 1: Create workers that call these specific existing services: [details]"  
> → Creates workers that integrate perfectly  
> → Works first try  
> → 1 hour implementation

**Difference:** 4 hours saved with proper context!

---

## 💡 Pro Tips

1. **Always start chat with context files** - Make reading them the first instruction
2. **Be specific about file paths** - "Create in `backend/app/workers/config.py`", not "Create worker config"
3. **Reference existing code** - "Follow the pattern in `app/services/screening.py`"
4. **Show expected output** - Include example JSON responses
5. **Ask for confirmation** - "Did you understand the integration requirements?"

---

## 🎯 Final Checklist

Before starting ANY implementation chat:

- [ ] I've read the current state audit
- [ ] I know exactly which files to create
- [ ] I understand how they integrate with existing code
- [ ] I have the context files ready to upload
- [ ] I've written a detailed prompt following the template
- [ ] I have clear success criteria
- [ ] I'm ready to review the output carefully

**Now you're ready to create consistent, high-quality code across multiple chats!** 🚀
