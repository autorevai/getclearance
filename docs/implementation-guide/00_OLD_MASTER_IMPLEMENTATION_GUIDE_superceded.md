# SignalWeave Implementation Master Guide
**Based on Sumsub Reverse Engineering Analysis**

**Created:** November 30, 2025  
**Target Launch:** January 2026 (8 weeks)  
**Current Status:** Backend scaffold 40% complete, Frontend 100% complete

---

## 📋 Table of Contents

1. [Current State Assessment](#current-state-assessment)
2. [Critical Architecture Changes](#critical-architecture-changes)
3. [Phase Breakdown](#phase-breakdown)
4. [Chat-by-Chat Strategy](#chat-strategy)
5. [File Organization](#file-organization)
6. [Testing Strategy](#testing-strategy)
7. [Deployment Checklist](#deployment-checklist)

---

## 🎯 Current State Assessment

### ✅ What You Have
- **Frontend:** 100% complete (React, deployed to Vercel)
- **Backend Scaffold:** FastAPI structure, models, basic endpoints
- **Database:** PostgreSQL schema defined, migrations ready
- **Infrastructure:** Docker Compose with Postgres, Redis, MinIO

### ⏳ What's Missing (Critical Path)
1. **Storage Service** - R2/S3 integration for documents
2. **Screening Service** - OpenSanctions with fuzzy matching
3. **AI Service** - Claude API for risk summaries
4. **OCR Service** - AWS Textract/Google Vision
5. **Background Workers** - ARQ jobs for async processing
6. **Webhook System** - Delivery with retry logic

---

## 🔧 Critical Architecture Changes

### Schema Additions Required

```sql
-- 1. Add fuzzy matching fields to screening_hits
ALTER TABLE screening_hits 
  ALTER COLUMN confidence TYPE DECIMAL(5,2),
  ADD COLUMN match_type VARCHAR(50),
  ADD COLUMN pep_relationship VARCHAR(50),
  ADD COLUMN sentiment VARCHAR(20),
  ADD COLUMN source_reputation VARCHAR(20);

-- 2. Add fraud detection fields to documents
ALTER TABLE documents
  ADD COLUMN security_features_detected JSONB DEFAULT '[]',
  ADD COLUMN fraud_analysis JSONB DEFAULT '{}';

-- 3. Add webhook delivery tracking (NEW TABLE)
CREATE TABLE webhook_deliveries (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID REFERENCES tenants(id),
    webhook_url VARCHAR(500) NOT NULL,
    event_type VARCHAR(100) NOT NULL,
    event_id UUID NOT NULL,
    payload JSONB NOT NULL,
    attempt_count INTEGER DEFAULT 0,
    last_attempt_at TIMESTAMPTZ,
    next_retry_at TIMESTAMPTZ,
    status VARCHAR(50) DEFAULT 'pending',
    http_status INTEGER,
    response_body TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);
CREATE INDEX idx_webhook_pending ON webhook_deliveries(status, next_retry_at)
    WHERE status = 'pending';

-- 4. Add applicant events for timeline (NEW TABLE)
CREATE TABLE applicant_events (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID REFERENCES tenants(id),
    applicant_id UUID REFERENCES applicants(id),
    event_type VARCHAR(100) NOT NULL,
    event_data JSONB,
    actor_type VARCHAR(50),
    actor_id UUID,
    timestamp TIMESTAMPTZ DEFAULT NOW()
);
CREATE INDEX idx_applicant_events_timeline ON applicant_events(applicant_id, timestamp DESC);

-- 5. Add KYC share tokens for reusable KYC (NEW TABLE - FUTURE)
CREATE TABLE kyc_share_tokens (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID REFERENCES tenants(id),
    applicant_id UUID REFERENCES applicants(id),
    token VARCHAR(64) NOT NULL UNIQUE,
    scope JSONB NOT NULL,
    user_consent JSONB NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    expires_at TIMESTAMPTZ NOT NULL,
    revoked_at TIMESTAMPTZ,
    access_count INTEGER DEFAULT 0,
    last_accessed_at TIMESTAMPTZ,
    last_accessed_by VARCHAR(255)
);
CREATE INDEX idx_kyc_tokens_active ON kyc_share_tokens(token) 
    WHERE revoked_at IS NULL AND expires_at > NOW();
```

### New Dependencies to Add

```txt
# requirements.txt additions
boto3==1.34.34              # AWS SDK (for Textract, S3)
python-Levenshtein==0.25.0  # Fuzzy string matching
anthropic==0.18.1           # Claude API client
arq==0.25.0                 # Redis-based task queue
httpx==0.26.0               # Async HTTP client
phonenumbers==8.13.27       # Phone number validation
pycountry==23.12.11         # Country code validation
```

---

## 📊 Phase Breakdown

### **PHASE 1: Core Services (Week 1)** 🔴
**Goal:** Enable document uploads and screening  
**Files to Create:** 6 files  
**Estimated Time:** 5-7 days

**Deliverables:**
1. ✅ Storage service (R2 presigned URLs)
2. ✅ Screening service (OpenSanctions + fuzzy matching)
3. ✅ AI service (Claude risk summaries)
4. ✅ Updated schema migration
5. ✅ Integration tests

**Success Criteria:**
- [ ] Documents upload to R2 successfully
- [ ] Screening returns hits with confidence scores
- [ ] AI generates risk summaries with citations
- [ ] All services have >80% test coverage

---

### **PHASE 2: Background Workers (Week 2)** 🟡
**Goal:** Async processing for screening, OCR, AI  
**Files to Create:** 5 files  
**Estimated Time:** 5-7 days

**Deliverables:**
1. ✅ ARQ worker setup
2. ✅ Screening worker
3. ✅ Document processing worker (OCR + fraud)
4. ✅ AI assessment worker
5. ✅ Worker monitoring/logging

**Success Criteria:**
- [ ] Jobs process within SLA (<30 seconds)
- [ ] Failed jobs retry with exponential backoff
- [ ] Worker health monitoring works
- [ ] Dead letter queue handles failures

---

### **PHASE 3: OCR & Fraud Detection (Week 2-3)** 🟡
**Goal:** Extract data from documents, detect fraud  
**Files to Create:** 4 files  
**Estimated Time:** 5-7 days

**Deliverables:**
1. ✅ OCR service (AWS Textract integration)
2. ✅ MRZ parser for passports
3. ✅ Fraud detection (AI vision + heuristics)
4. ✅ Document quality checks

**Success Criteria:**
- [ ] OCR accuracy >95% on clear documents
- [ ] MRZ checksum validation works
- [ ] Fraud detection catches edited images
- [ ] Quality checks reject blurry/damaged docs

---

### **PHASE 4: Webhooks & Notifications (Week 3)** 🟢
**Goal:** Reliable webhook delivery with retries  
**Files to Create:** 3 files  
**Estimated Time:** 3-4 days

**Deliverables:**
1. ✅ Webhook service with retry logic
2. ✅ HMAC signature verification
3. ✅ Webhook delivery worker

**Success Criteria:**
- [ ] Webhooks deliver with <5% failure rate
- [ ] Retries use exponential backoff (3 attempts)
- [ ] Signature verification prevents spoofing
- [ ] Delivery logs stored for audit

---

### **PHASE 5: Evidence & Compliance (Week 4)** 🟢
**Goal:** Generate audit-ready evidence packs  
**Files to Create:** 3 files  
**Estimated Time:** 3-4 days

**Deliverables:**
1. ✅ Evidence export service (PDF generation)
2. ✅ Chain-of-custody tracking
3. ✅ Applicant timeline aggregation

**Success Criteria:**
- [ ] Evidence PDFs include all source citations
- [ ] Chain-hashing prevents tampering
- [ ] Timeline shows all events chronologically
- [ ] Exports meet SOC 2 requirements

---

### **PHASE 6: Integration & Testing (Week 5-6)** 🟢
**Goal:** Connect frontend, end-to-end testing  
**Files to Create:** 10+ test files  
**Estimated Time:** 7-10 days

**Deliverables:**
1. ✅ Frontend API integration
2. ✅ E2E test suite
3. ✅ Load testing
4. ✅ Security hardening

**Success Criteria:**
- [ ] Frontend fully connected (no mocks)
- [ ] E2E tests cover happy + unhappy paths
- [ ] System handles 100 req/min
- [ ] Security scan passes (no critical issues)

---

### **PHASE 7: Deployment (Week 7-8)** 🔵
**Goal:** Production deployment on Railway  
**Files to Create:** Deployment configs  
**Estimated Time:** 5-7 days

**Deliverables:**
1. ✅ Railway configuration
2. ✅ Environment setup
3. ✅ Monitoring/alerting
4. ✅ First customer onboarding

**Success Criteria:**
- [ ] Production URL live with SSL
- [ ] Database backups automated
- [ ] Uptime monitoring configured
- [ ] First paying customer verified

---

## 🗣️ Chat-by-Chat Strategy

### Why Break Into Multiple Chats?
1. **Context Management:** Each chat focuses on one service
2. **Iteration Speed:** Faster feedback loops per component
3. **Testing Focus:** Test each piece before moving on
4. **Debugging:** Isolated issues are easier to fix

### Recommended Chat Sequence

#### **Chat 1: Database Migration + Storage Service**
**Duration:** 1-2 hours  
**Files:** 2 (migration, storage.py)

**Prompt Template:**
```
I'm implementing Phase 1 of SignalWeave (KYC platform cloning Sumsub). 

Current state: Backend scaffold exists, need to add schema changes and storage service.

Tasks:
1. Create Alembic migration for schema additions (webhook_deliveries, applicant_events, screening_hits updates)
2. Create storage.py service for Cloudflare R2 integration
3. Update documents API to use presigned URLs

Reference: /MASTER_IMPLEMENTATION_GUIDE.md Phase 1
```

#### **Chat 2: Screening Service + Fuzzy Matching**
**Duration:** 2-3 hours  
**Files:** 3 (screening.py, tests, API updates)

**Prompt Template:**
```
Phase 1, Step 2: Implementing OpenSanctions screening with Sumsub-style fuzzy matching.

Need:
1. screening.py service with Levenshtein distance matching
2. Confidence scoring algorithm (0-100)
3. Match classification (true_positive, potential_match, false_positive, unknown)
4. Update screening API to call service

Reference: Sumsub analysis section 7 (Screening Lifecycle Model)
```

#### **Chat 3: AI Service (Claude Integration)**
**Duration:** 1-2 hours  
**Files:** 2 (ai.py, tests)

**Prompt Template:**
```
Phase 1, Step 3: Claude API integration for risk summaries.

Need:
1. ai.py service with risk assessment
2. Document fraud detection using vision
3. Structured JSON output with citations
4. Store in ai_assessments table

Reference: Sumsub analysis section 10.5 (AI Integration Strategy)
```

#### **Chat 4: Background Workers Setup**
**Duration:** 2-3 hours  
**Files:** 4 (ARQ config, screening_worker, document_worker, ai_worker)

**Prompt Template:**
```
Phase 2: Setting up ARQ background workers for async processing.

Need:
1. ARQ worker configuration
2. screening_worker.py - Run screening in background
3. document_worker.py - OCR + fraud detection
4. ai_worker.py - Generate risk summaries
5. Update API endpoints to enqueue jobs

Reference: Phase 2 deliverables in MASTER_IMPLEMENTATION_GUIDE.md
```

#### **Chat 5: OCR Service**
**Duration:** 2-3 hours  
**Files:** 3 (ocr.py, mrz_parser.py, tests)

**Prompt Template:**
```
Phase 3: OCR integration with AWS Textract + MRZ parsing.

Need:
1. ocr.py service for document text extraction
2. MRZ parser with checksum validation
3. Document quality checks (blur, resolution, glare)
4. Integration with document_worker

Reference: Sumsub analysis section 6 (Document Verification)
```

#### **Chat 6: Webhook Service**
**Duration:** 1-2 hours  
**Files:** 2 (webhook.py, webhook_worker.py)

**Prompt Template:**
```
Phase 4: Webhook delivery system with retry logic.

Need:
1. webhook.py service
2. HMAC signature generation
3. Retry logic with exponential backoff (3 attempts: 0s, 30s, 5min)
4. webhook_worker.py for async delivery

Reference: Sumsub analysis section 5.3 (Webhook Payload Structure)
```

#### **Chat 7: Evidence Export**
**Duration:** 2-3 hours  
**Files:** 2 (evidence.py, timeline.py)

**Prompt Template:**
```
Phase 5: Evidence pack generation for compliance.

Need:
1. evidence.py - PDF export with citations
2. timeline.py - Aggregate applicant events
3. Chain-of-custody tracking
4. SOC 2 compliance formatting

Reference: Sumsub analysis section 10.1 (Critical Behaviors)
```

#### **Chat 8: Frontend Integration**
**Duration:** 2-3 hours  
**Files:** Frontend API service layer

**Prompt Template:**
```
Phase 6: Connect React frontend to real API (remove mocks).

Need:
1. API service layer with axios
2. Auth token injection
3. Error handling
4. Replace all mock data with real API calls

Current: Frontend uses mock data
Target: Full integration with backend
```

#### **Chat 9: Testing & Security**
**Duration:** 3-4 hours  
**Files:** Comprehensive test suite

**Prompt Template:**
```
Phase 6: Comprehensive testing and security hardening.

Need:
1. Integration tests for all services
2. E2E tests for critical flows
3. Security audit (SQL injection, XSS, CSRF)
4. Load testing (100 req/min target)

Reference: Phase 6 success criteria
```

#### **Chat 10: Deployment**
**Duration:** 2-3 hours  
**Files:** Deployment configs

**Prompt Template:**
```
Phase 7: Production deployment to Railway.

Need:
1. Railway.json configuration
2. Environment variable setup
3. Database migration strategy
4. Monitoring and alerting setup

Target: Live production URL with first customer
```

---

## 📁 File Organization

### Files Created in This Package

```
signalweave-implementation/
├── 00_MASTER_IMPLEMENTATION_GUIDE.md          # This file
├── 01_PHASE1_schema_migration.sql             # Database updates
├── 02_PHASE1_storage_service.py               # R2/S3 integration
├── 03_PHASE1_screening_service.py             # OpenSanctions + fuzzy matching
├── 04_PHASE1_ai_service.py                    # Claude API integration
├── 05_PHASE2_worker_config.py                 # ARQ setup
├── 06_PHASE2_screening_worker.py              # Background screening
├── 07_PHASE2_document_worker.py               # OCR + fraud detection
├── 08_PHASE3_ocr_service.py                   # AWS Textract integration
├── 09_PHASE3_mrz_parser.py                    # Passport MRZ validation
├── 10_PHASE4_webhook_service.py               # Webhook delivery
├── 11_PHASE5_evidence_service.py              # PDF export
├── 12_INTEGRATION_TESTS.py                    # Test suite
└── 13_DEPLOYMENT_CHECKLIST.md                 # Production readiness
```

### Where to Put These Files in Your Repo

```
getclearance/
├── backend/
│   ├── app/
│   │   ├── services/
│   │   │   ├── storage.py          ← 02_PHASE1_storage_service.py
│   │   │   ├── screening.py        ← 03_PHASE1_screening_service.py
│   │   │   ├── ai.py               ← 04_PHASE1_ai_service.py
│   │   │   ├── ocr.py              ← 08_PHASE3_ocr_service.py
│   │   │   ├── mrz_parser.py       ← 09_PHASE3_mrz_parser.py
│   │   │   ├── webhook.py          ← 10_PHASE4_webhook_service.py
│   │   │   └── evidence.py         ← 11_PHASE5_evidence_service.py
│   │   │
│   │   ├── workers/
│   │   │   ├── __init__.py
│   │   │   ├── config.py           ← 05_PHASE2_worker_config.py
│   │   │   ├── screening_worker.py ← 06_PHASE2_screening_worker.py
│   │   │   └── document_worker.py  ← 07_PHASE2_document_worker.py
│   │   │
│   ├── migrations/versions/
│   │   └── <timestamp>_add_sumsub_features.py  ← 01_PHASE1_schema_migration.sql
│   │
│   └── tests/
│       ├── integration/
│       │   └── test_services.py    ← 12_INTEGRATION_TESTS.py
```

---

## 🧪 Testing Strategy

### Unit Tests (Per Service)
- **Storage:** Upload/download presigned URLs
- **Screening:** Fuzzy matching accuracy
- **AI:** Response parsing, error handling
- **OCR:** Text extraction, MRZ validation

### Integration Tests (Cross-Service)
- **Document Flow:** Upload → OCR → Fraud Detection → Storage
- **Screening Flow:** Create check → Query API → Store hits → Create case
- **Webhook Flow:** Event → Delivery → Retry → Success

### E2E Tests (Full Applicant Journey)
1. Create applicant via API
2. Upload ID document
3. Trigger screening
4. AI generates risk summary
5. Manual review → approve/reject
6. Evidence pack export

### Performance Tests
- **Load:** 100 concurrent requests
- **Latency:** P99 < 500ms for API calls
- **Worker Throughput:** 10 jobs/second
- **Database:** Queries < 100ms

---

## 🚀 Deployment Checklist

### Pre-Deployment
- [ ] All tests passing (unit + integration + E2E)
- [ ] Security scan completed (no critical issues)
- [ ] Environment variables documented
- [ ] Database backup strategy defined
- [ ] Monitoring configured (Sentry, Datadog, etc.)

### Deployment Steps
1. [ ] Create Railway project
2. [ ] Provision PostgreSQL database
3. [ ] Provision Redis instance
4. [ ] Set environment variables
5. [ ] Run database migrations
6. [ ] Deploy backend (FastAPI)
7. [ ] Connect custom domain
8. [ ] Enable SSL certificate
9. [ ] Configure CORS for frontend
10. [ ] Test production endpoints

### Post-Deployment
- [ ] Smoke tests on production
- [ ] Create first tenant
- [ ] Onboard test customer
- [ ] Monitor error rates
- [ ] Set up alerting (>5% error rate)

---

## 📈 Success Metrics

### Technical Metrics
- **Uptime:** 99.9% (43 minutes downtime/month max)
- **API Latency:** P99 < 500ms
- **Screening Accuracy:** >95% true positives detected
- **OCR Accuracy:** >95% on clear documents
- **Webhook Delivery:** >98% success rate

### Business Metrics
- **Time to Verification:** <30 seconds (vs Sumsub's "minutes")
- **Auto-Approval Rate:** >70% for low-risk applicants
- **False Positive Rate:** <5% for screening
- **Cost per Verification:** <$0.50

---

## 🎯 Critical Path Summary

**Must-Have for MVP (Weeks 1-3):**
1. ✅ Storage service (documents upload/download)
2. ✅ Screening service (OpenSanctions integration)
3. ✅ Basic AI summaries (Claude API)
4. ✅ Background workers (async processing)
5. ✅ Webhook delivery (notify customers)

**Nice-to-Have for V1 (Weeks 4-6):**
- OCR with high accuracy
- Advanced fraud detection
- Evidence pack export
- Full E2E testing

**Future (Post-Launch):**
- Reusable KYC tokens
- Multi-language support
- Database validation (govt cross-check)
- NFC passport reading

---

## 🆘 Getting Help

### If You Get Stuck

**Chat Strategy:**
1. Copy the relevant phase section
2. Include error messages/stack traces
3. Reference specific files by number (e.g., "Issue with 03_PHASE1_screening_service.py")
4. Ask for debugging help or alternative approaches

**Example Debug Prompt:**
```
I'm implementing 03_PHASE1_screening_service.py but getting this error:

[paste error]

The fuzzy matching isn't returning expected confidence scores. 
Here's my current code:

[paste relevant code]

Can you help debug the _calculate_confidence method?
```

---

## 📚 Key References

### Sumsub Analysis Sections
- **Section 3:** Entity → Table Mapping
- **Section 4:** State Machine Diagrams
- **Section 5:** API Reconstruction
- **Section 7:** Screening Lifecycle Model
- **Section 10:** Engineering Recommendations

### Your Current Docs
- `docs/ARCHITECTURE.md` - Full database schema
- `docs/CTO_HANDOFF.md` - Current status
- `backend/README.md` - Setup instructions

---

**Next Step:** Download this guide and the accompanying code files, then start with Chat 1 (Database Migration + Storage Service).

Good luck! 🚀
