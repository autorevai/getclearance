# MASTER Sumsub Reverse Engineering Guide
**Project:** GetClearance / SignalWeave
**Created:** December 2, 2025
**Purpose:** Complete feature parity with Sumsub + AI differentiation
**Status:** Living document - update as sprints complete

---

## Table of Contents

1. [Executive Summary](#executive-summary)
2. [Realistic Feature Parity Assessment](#realistic-feature-parity-assessment)
3. [Sumsub Feature Matrix](#sumsub-feature-matrix)
4. [Current Implementation Status](#current-implementation-status)
5. [Gap Analysis](#gap-analysis)
6. [Parallel Workstreams](#parallel-workstreams)
7. [Sprint Definitions](#sprint-definitions)
8. [Sprint Execution Template](#sprint-execution-template)
9. [Technical Specifications](#technical-specifications)
10. [Third-Party Services Required](#third-party-services-required)
11. [Success Metrics](#success-metrics)

---

## Executive Summary

### Mission
Build an AI-native KYC/AML platform that:
- **Matches** Sumsub's core verification features
- **Exceeds** Sumsub with deep Claude AI integration
- **Simplifies** developer experience with cleaner APIs
- **Accelerates** processing (<30 seconds vs Sumsub's "minutes")

### What Sumsub Does (Our Competition)

Based on comprehensive documentation analysis:

| Category | Sumsub Features |
|----------|-----------------|
| **ID Verification** | 220+ countries, 40+ languages, 40+ security features, MRZ validation |
| **AML Screening** | Sanctions, PEP, Adverse Media, Fuzzy matching, Ongoing monitoring |
| **Liveness** | Neural network-based, 3D face mapping, Anti-spoofing, 1-second detection |
| **Address Verification** | Document-based PoA, Geolocation, Non-doc database validation |
| **Database Validation** | Government cross-checks in 50+ countries |
| **Risk Assessment** | 8 risk categories, Automated workflows, Manual review queues |
| **KYB** | Company verification, UBO identification, Corporate structure |
| **Reusable KYC** | Portable identity, Token-based sharing, Partner networks |
| **Video Identification** | Live operator calls, Real-time verification |
| **Questionnaires** | Custom forms, Risk scoring, Workflow integration |

### Our Differentiation

| Capability | Sumsub | GetClearance |
|------------|--------|--------------|
| AI Integration | Basic ML models | Claude AI native (vision, NLP, reasoning) |
| Processing Speed | "Minutes" | <30 seconds target |
| False Positive Rate | 10-15% | <5% target (AI-powered) |
| Developer Experience | Complex multipart APIs | Clean REST + presigned URLs |
| Pricing | Enterprise sales only | Transparent, pay-as-you-go |
| Risk Summaries | Template-based | AI-generated with citations |
| Fraud Detection | Rule-based | AI vision analysis |

---

## Realistic Feature Parity Assessment

### After Completing ALL Sprints (Terminals 1-5)

```
Feature Parity Summary:
┌────────────────────────────────────────────────────────────────────┐
│                                                                    │
│  Core KYC/AML ████████████████████████████████████████░░  95%     │
│  - ID Verification, OCR, MRZ, Screening, Cases                    │
│                                                                    │
│  Security/Compliance █████████████████████████████████░░░  90%    │
│  - Audit logs, encryption, GDPR, rate limiting                    │
│                                                                    │
│  Business Features ████████████████████████████░░░░░░░░░  75%     │
│  - KYB, Questionnaires, Analytics, Settings                       │
│                                                                    │
│  Advanced Biometrics █████████████████░░░░░░░░░░░░░░░░░░  50%     │
│  - Liveness, Face matching (needs 3rd party)                      │
│                                                                    │
│  Enterprise Features ████████░░░░░░░░░░░░░░░░░░░░░░░░░░░  25%     │
│  - Video ID, Reusable KYC, 220+ countries                         │
│                                                                    │
│  AI Differentiation ████████████████████████████████████████ 100%+│
│  - EXCEEDS Sumsub (Claude integration)                            │
│                                                                    │
└────────────────────────────────────────────────────────────────────┘

Overall vs Sumsub: ~70-75% Feature Parity + AI Superiority
```

### What WILL Work (Terminals 1-4)

| Feature | After Sprints | Notes |
|---------|---------------|-------|
| Document upload & storage | **WORKING** | R2 presigned URLs |
| OCR text extraction | **WORKING** | AWS Textract |
| MRZ validation | **WORKING** | Check digit verification |
| AML screening (sanctions/PEP) | **WORKING** | OpenSanctions |
| Fuzzy matching | **WORKING** | Levenshtein + phonetic |
| Case management | **WORKING** | Full workflow |
| AI risk summaries | **WORKING** | Claude integration |
| Audit logging | **WORKING** | After Sprint B1 |
| PII encryption | **WORKING** | After Sprint B3 |
| Webhooks | **WORKING** | With retry logic |
| Evidence export | **WORKING** | PDF generation |
| KYB/Companies | **WORKING** | After Sprint F2 |
| Settings UI | **WORKING** | After Sprint U1 |
| Analytics | **WORKING** | After Sprint U3 |

### What NEEDS Additional Work (Terminal 5 - Advanced)

| Feature | Gap | Solution | Cost/Effort |
|---------|-----|----------|-------------|
| **Liveness Detection** | No neural network | AWS Rekognition or similar | $0.001/image + integration |
| **Face Matching (1:1)** | Not implemented | AWS Rekognition CompareFaces | $0.001/comparison |
| **Database Validation** | No govt APIs | Country-specific integrations | $$$$ per country |
| **220+ Country Templates** | Have ~20 | Document template library | Months of work |
| **Video Identification** | Not implemented | WebRTC + operator system | Major feature |
| **Reusable KYC** | Not implemented | Token infrastructure | Medium effort |
| **Device Fingerprinting** | Basic only | FingerprintJS or similar | $99-999/mo |
| **Deepfake Detection** | Not implemented | Specialized AI service | $$$ |

### Honest Timeline

| Milestone | Timeline | Feature Parity |
|-----------|----------|----------------|
| **MVP (Terminals 1-4)** | 6-8 weeks | ~70% core features |
| **+ Liveness/Face Match** | +2 weeks | ~80% |
| **+ More Countries** | +4 weeks | ~85% |
| **+ Video ID** | +6 weeks | ~90% |
| **Full Parity** | +6 months | ~95% |

### What We Beat Sumsub On (Even at 70%)

1. **AI Risk Analysis** - Claude-powered summaries with reasoning
2. **Processing Speed** - Target <30s vs "minutes"
3. **False Positive Rate** - AI reduces manual review
4. **Developer Experience** - Clean REST API
5. **Pricing Transparency** - No enterprise sales required
6. **Customization** - Open architecture

---

## Sumsub Feature Matrix

### 1. Identity Verification (ID-V)

#### 1.1 Document Verification
| Feature | Sumsub Implementation | Our Status | Priority |
|---------|----------------------|------------|----------|
| Document upload (image/PDF) | WebSDK, MobileSDK, API | **DONE** | - |
| Document type detection | Auto-detect from 220+ countries | PARTIAL | P1 |
| OCR extraction | Proprietary + Textract | **DONE** | - |
| MRZ validation | Check digit verification | **DONE** | - |
| Template matching | 40+ security features | TODO | P2 |
| Hologram detection | Image analysis | TODO | P3 |
| Microprinting detection | Image analysis | TODO | P3 |
| Watermark detection | Image analysis | TODO | P3 |
| Document expiry check | Date comparison | **DONE** | - |
| Photo quality validation | 300 DPI minimum, color | PARTIAL | P1 |

#### 1.2 Liveness Detection
| Feature | Sumsub Implementation | Our Status | Priority |
|---------|----------------------|------------|----------|
| Passive liveness | Neural network 3D mapping | TODO | P2 |
| Active liveness | Head movements/gestures | TODO | P3 |
| Face matching (1:1) | Selfie vs ID photo | TODO | P2 |
| Anti-spoofing | Detect photos, videos, masks | TODO | P2 |
| Deepfake detection | AI model | TODO | P3 |

#### 1.3 Database Validation
| Feature | Sumsub Implementation | Our Status | Priority |
|---------|----------------------|------------|----------|
| Government database check | 50+ countries | TODO | P2 |
| Credit bureau validation | US, Brazil, Mexico | TODO | P3 |
| SSN/TIN validation | US, India | TODO | P2 |
| Deceased status check | Where available | TODO | P3 |

### 2. AML Screening

#### 2.1 Core Screening
| Feature | Sumsub Implementation | Our Status | Priority |
|---------|----------------------|------------|----------|
| Sanctions screening | OFAC, UN, EU, UK, etc. | **DONE** | - |
| PEP screening | Global PEP databases | **DONE** | - |
| Adverse media | News/media monitoring | **DONE** | - |
| Fuzzy matching | Levenshtein + phonetic | **DONE** | - |
| Confidence scoring | 0-100 scale | **DONE** | - |
| Match classification | True/False positive | **DONE** | - |

#### 2.2 Screening Presets (ComplyAdvantage Mesh)
| Preset | Purpose | Our Status | Priority |
|--------|---------|------------|----------|
| Best Approval Rate | Minimize false positives | **DONE** | - |
| Default | Balanced | **DONE** | - |
| Expanded | More thorough | TODO | P2 |
| Extensive | Maximum coverage | TODO | P2 |
| Counterparty Sanctions | B2B screening | TODO | P2 |

#### 2.3 Ongoing Monitoring
| Feature | Sumsub Implementation | Our Status | Priority |
|---------|----------------------|------------|----------|
| Continuous AML monitoring | Daily re-screening | TODO | P1 |
| Alert generation | On list changes | TODO | P1 |
| Alert management | Dashboard + API | TODO | P1 |
| Monitoring enable/disable | Per applicant | TODO | P1 |

### 3. Address Verification

| Feature | Sumsub Implementation | Our Status | Priority |
|---------|----------------------|------------|----------|
| Document-based PoA | Utility bills, bank statements | TODO | P2 |
| Geolocation verification | IP/GPS-based | TODO | P3 |
| Non-doc verification | Database validation | TODO | P3 |
| Address extraction | OCR from documents | PARTIAL | P2 |

### 4. Risk Assessment

#### 4.1 Risk Labels (8 Categories)
| Category | Signals | Our Status | Priority |
|----------|---------|------------|----------|
| Email/Phone Risk | Disposable, virtual numbers | TODO | P2 |
| Device Risk | VPN, TOR, emulator, jailbreak | TODO | P2 |
| Cross-Check Risk | Country mismatch, duplicates | PARTIAL | P1 |
| Selfie Risk | Age mismatch, third-party | TODO | P2 |
| AML Risk | Sanctions, PEP, adverse media | **DONE** | - |
| Person Risk | Famous persons, name mismatch | TODO | P2 |
| Company Risk | Missing data, inconsistencies | TODO | P2 |

#### 4.2 Risk Scoring
| Feature | Sumsub Implementation | Our Status | Priority |
|---------|----------------------|------------|----------|
| Automated risk calculation | Multi-factor scoring | PARTIAL | P1 |
| Risk-based workflows | Conditional routing | TODO | P1 |
| Manual risk adjustment | Admin override | **DONE** | - |

### 5. Applicant Management

#### 5.1 Applicant Statuses (7 States)
| Status | API Value | Our Status | Priority |
|--------|-----------|------------|----------|
| Documents requested | `init` | **DONE** | - |
| Pending | `pending` | **DONE** | - |
| Awaiting service | `awaitingService` | TODO | P1 |
| Requires action | `onHold` | **DONE** | - |
| Awaiting user | `awaitingUser` | TODO | P2 |
| Approved | `completed` + GREEN | **DONE** | - |
| Rejected | `completed` + RED + FINAL | **DONE** | - |
| Resubmission requested | `completed` + RED + RETRY | TODO | P1 |

#### 5.2 Profile Management
| Feature | Sumsub Implementation | Our Status | Priority |
|---------|----------------------|------------|----------|
| Profile creation | API + SDK | **DONE** | - |
| Profile reset | Clear and restart | TODO | P1 |
| Force approve | Admin override | TODO | P1 |
| Document deactivation | Mark as inactive | TODO | P2 |
| Blocklist management | Flag for rejection | TODO | P1 |
| Tags | Custom labels | TODO | P2 |

### 6. Business Verification (KYB)

| Feature | Sumsub Implementation | Our Status | Priority |
|---------|----------------------|------------|----------|
| Company creation | API + SDK | TODO | P1 |
| Company screening | Business sanctions | TODO | P1 |
| UBO identification | Beneficial owners | TODO | P1 |
| Corporate structure | Ownership tree | TODO | P2 |
| Company documents | Registration certificates | TODO | P1 |
| Director verification | Link to KYC | TODO | P1 |

### 7. Webhooks & Notifications

| Feature | Sumsub Implementation | Our Status | Priority |
|---------|----------------------|------------|----------|
| Webhook delivery | HTTP POST | **DONE** | - |
| HMAC signature | SHA256 | **DONE** | - |
| Retry logic | 3 attempts, exponential | **DONE** | - |
| Event types | applicantReviewed, etc. | PARTIAL | P1 |
| Delivery logs | Dashboard | TODO | P1 |

### 8. Compliance Features

| Feature | Sumsub Implementation | Our Status | Priority |
|---------|----------------------|------------|----------|
| Evidence export | PDF reports | **DONE** | - |
| Audit trail | Chain-hashed logs | PARTIAL | P0 |
| SAR export | GDPR Article 15 | TODO | P1 |
| Data deletion | GDPR Article 17 | TODO | P1 |
| Retention policies | Configurable | TODO | P1 |
| Consent tracking | Opt-in/out | TODO | P2 |

### 9. Questionnaires

| Feature | Sumsub Implementation | Our Status | Priority |
|---------|----------------------|------------|----------|
| Custom forms | No-code builder | TODO | P2 |
| Question types | Text, select, date, file | TODO | P2 |
| Risk scoring | Answer-based scoring | TODO | P2 |
| Workflow integration | Conditional steps | TODO | P2 |

### 10. Reusable KYC

| Feature | Sumsub Implementation | Our Status | Priority |
|---------|----------------------|------------|----------|
| Token generation | Share tokens | TODO | P3 |
| Data sharing | Between partners | TODO | P3 |
| Consent flow | User approval | TODO | P3 |
| Partner networks | Cross-org sharing | TODO | P3 |

### 11. Video Identification

| Feature | Sumsub Implementation | Our Status | Priority |
|---------|----------------------|------------|----------|
| Live video calls | WebRTC | TODO | P3 |
| Operator verification | Trained staff | TODO | P3 |
| Document capture | In-call photos | TODO | P3 |
| Recording | Audit evidence | TODO | P3 |

---

## Current Implementation Status

### Backend Services (Existing)

```
backend/app/services/
├── screening.py       COMPLETE - OpenSanctions + fuzzy matching
├── storage.py         COMPLETE - R2/S3 presigned URLs
├── ai.py              COMPLETE - Claude risk summaries
├── ocr.py             COMPLETE - AWS Textract integration
├── mrz_parser.py      COMPLETE - Passport MRZ validation
├── webhook.py         COMPLETE - Delivery with retry
├── evidence.py        COMPLETE - PDF generation
└── timeline.py        COMPLETE - Event aggregation
```

### Backend Workers (Existing)

```
backend/app/workers/
├── config.py              COMPLETE - ARQ configuration
├── screening_worker.py    COMPLETE - Background screening
├── document_worker.py     COMPLETE - OCR processing
├── ai_worker.py           COMPLETE - Risk summaries
└── webhook_worker.py      COMPLETE - Webhook delivery
```

### API Endpoints (Existing)

```
backend/app/api/v1/
├── applicants.py      COMPLETE - CRUD + review
├── documents.py       COMPLETE - Upload/download
├── screening.py       COMPLETE - Check + resolve
├── cases.py           COMPLETE - Case management
├── ai.py              COMPLETE - Risk summaries
├── auth.py            PARTIAL - Needs security hardening
└── dashboard.py       COMPLETE - Stats endpoints
```

### Frontend Pages (Existing)

```
frontend/src/components/
├── Dashboard.jsx              COMPLETE
├── ApplicantsList.jsx         COMPLETE
├── ApplicantDetail.jsx        COMPLETE
├── ScreeningChecks.jsx        COMPLETE
├── CaseManagement.jsx         COMPLETE
├── ApplicantAssistant.jsx     COMPLETE
├── DocumentUpload.jsx         COMPLETE
├── DocumentPreview.jsx        COMPLETE
└── pages/
    ├── CompaniesPage.jsx      PLACEHOLDER
    ├── IntegrationsPage.jsx   PLACEHOLDER
    ├── DeviceIntelligencePage.jsx   PLACEHOLDER
    ├── ReusableKYCPage.jsx    PLACEHOLDER
    ├── AnalyticsPage.jsx      PLACEHOLDER
    ├── SettingsPage.jsx       PLACEHOLDER
    ├── BillingPage.jsx        PLACEHOLDER
    └── AuditLogPage.jsx       PLACEHOLDER
```

---

## Gap Analysis

### Critical Gaps (P0 - Must Fix Before Production) ✅ ALL FIXED

1. ~~**Audit Logging Not Called**~~ - ✅ Sprint B1 COMPLETE
2. ~~**PII Not Encrypted**~~ - ✅ Sprint B3 COMPLETE
3. ~~**No Rate Limiting**~~ - ✅ Sprint B2 COMPLETE
4. ~~**Debug Endpoints Exposed**~~ - ✅ Sprint B2 COMPLETE
5. ~~**Dev Mode Auth Bypass**~~ - ✅ Sprint B2 COMPLETE

### High Priority Gaps (P1 - Week 1-2)

1. **Ongoing AML Monitoring** - Daily re-screening (Sprint F1 - Terminal 2)
2. **Resubmission Workflow** - RETRY status handling
3. **Blocklist Management** - Flag for auto-rejection
4. **Profile Reset** - Clear and restart verification
5. **Risk-Based Workflows** - Conditional routing (Sprint F3 - Terminal 2)
6. ~~**Missing API Endpoints**~~ - ✅ Sprint B4 COMPLETE
7. ~~**GDPR Features**~~ - ✅ Sprint B5 COMPLETE

### Medium Priority Gaps (P2 - Week 3-5)

1. **Companies/KYB Module** - Business verification
2. **Address Verification** - PoA documents
3. **Liveness Detection** - Face matching
4. **Database Validation** - Government cross-checks
5. **Device Intelligence** - Risk signals
6. **Questionnaires** - Custom forms
7. **Analytics Dashboard** - Reporting

### Lower Priority Gaps (P3 - Week 6+)

1. **Video Identification** - Live operator calls
2. **Reusable KYC** - Portable identity
3. **Advanced Fraud Detection** - Holograms, microprinting
4. **Deepfake Detection** - AI anti-spoofing

---

## Parallel Workstreams

### Workstream Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                    PARALLEL TERMINAL WORKSTREAMS                     │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  Terminal 1: Backend Security      Terminal 2: Backend Features      │
│  ┌──────────────────────────┐      ┌──────────────────────────┐     │
│  │ Sprint B1: Audit Logging │      │ Sprint F1: Ongoing AML   │     │
│  │ Sprint B2: Rate Limiting │      │ Sprint F2: KYB Module    │     │
│  │ Sprint B3: PII Encryption│      │ Sprint F3: Risk Workflows│     │
│  │ Sprint B4: Missing APIs  │      │ Sprint F4: Questionnaires│     │
│  │ Sprint B5: GDPR Features │      │ Sprint F5: Address Verif │     │
│  │ Sprint B6: Monitoring    │      │ Sprint F6: Liveness      │     │
│  └──────────────────────────┘      └──────────────────────────┘     │
│                                                                      │
│  Terminal 3: Frontend              Terminal 4: Testing/Deploy        │
│  ┌──────────────────────────┐      ┌──────────────────────────┐     │
│  │ Sprint U1: Settings      │      │ Sprint T1: Unit Tests    │     │
│  │ Sprint U2: Audit Log     │      │ Sprint T2: Integration   │     │
│  │ Sprint U3: Analytics     │      │ Sprint T3: E2E Tests     │     │
│  │ Sprint U4: Integrations  │      │ Sprint T4: Load Tests    │     │
│  │ Sprint U5: Companies     │      │ Sprint T5: Security Scan │     │
│  │ Sprint U6: Billing       │      │ Sprint T6: Deployment    │     │
│  └──────────────────────────┘      └──────────────────────────┘     │
│                                                                      │
└─────────────────────────────────────────────────────────────────────┘
```

### Dependency Map

```
                        START
                          │
          ┌───────────────┼───────────────┐
          ▼               ▼               ▼
    ┌──────────┐    ┌──────────┐    ┌──────────┐
    │ Backend  │    │ Backend  │    │ Frontend │
    │ Security │    │ Features │    │   UI     │
    │(Terminal1)│    │(Terminal2)│    │(Terminal3)│
    └────┬─────┘    └────┬─────┘    └────┬─────┘
         │               │               │
         │               │               │
         ▼               ▼               ▼
    ┌─────────────────────────────────────────┐
    │            Testing & Deploy              │
    │              (Terminal 4)                │
    └─────────────────────────────────────────┘
                          │
                          ▼
                     PRODUCTION
```

---

## Sprint Definitions

### Terminal 1: Backend Security ✅ ALL COMPLETE (December 2, 2025)

#### Sprint B1: Audit Logging ✅ COMPLETE
**Files Created:** `services/audit.py`, `tests/test_audit.py`
**Files Updated:** `api/v1/applicants.py`, `api/v1/cases.py`, `api/v1/screening.py`, `dependencies.py`
**Result:** 12 audit tests passing, tamper-evident chain hashing implemented

#### Sprint B2: Rate Limiting ✅ COMPLETE
**Files Created:** `scripts/generate_dev_token.py`
**Files Updated:** `main.py` (slowapi, security headers, request ID middleware), `auth.py` (dev-only router)
**Result:** 200 req/min default, security headers on all responses, debug endpoints protected

#### Sprint B3: PII Encryption ✅ COMPLETE
**Files Created:** `services/encryption.py`, `models/types.py`, `scripts/migrate_encrypt_pii.py`, `tests/test_encryption.py`
**Files Updated:** `models/applicant.py`, `config.py`
**Result:** 22 encryption tests, Fernet AES-128-CBC with PBKDF2, transparent encrypt/decrypt

#### Sprint B4: Missing Endpoints ✅ COMPLETE
**Files Created:** `models/batch_job.py`
**Files Updated:** `api/v1/screening.py`, `api/v1/ai.py`, `api/v1/cases.py`
**Result:** GET /hits, batch job status, document suggestions, field name aliases

#### Sprint B5: GDPR Features ✅ COMPLETE
**Files Created:** `services/retention.py`, `tests/test_gdpr.py`
**Files Updated:** `models/applicant.py` (GDPR fields), `api/v1/applicants.py` (GDPR endpoints), `services/audit.py`
**Result:** 12 GDPR tests, SAR export, GDPR delete with AML safeguards, legal hold, consent tracking

#### Sprint B6: Monitoring ✅ COMPLETE
**Files Created:** `logging_config.py`, `tests/test_monitoring.py`
**Files Updated:** `main.py` (Sentry, health checks), `config.py`, `requirements.txt`
**Result:** 24 monitoring tests, structured JSON logging, PII scrubbing, Sentry integration

**Total: 250 tests passing across all security sprints**

---

### Terminal 2: Backend Features (15-20 days)

#### Sprint F1: Ongoing AML Monitoring (3-4 days) - HIGH
**Files:** `services/monitoring.py`, `workers/monitoring_worker.py`
**Goal:** Continuous screening

```
Tasks:
- Monitoring enable/disable per applicant
- Daily re-screening worker
- Alert generation on list changes
- Alert management API
- Monitoring status dashboard data
```

#### Sprint F2: KYB Module (5-7 days) - HIGH
**Files:** `models/company.py`, `api/v1/companies.py`, `services/kyb_screening.py`
**Goal:** Business verification

```
Tasks:
- Company model with all fields
- Beneficial owner model
- Company CRUD endpoints
- Company screening endpoint
- UBO management endpoints
- Corporate structure endpoint
```

#### Sprint F3: Risk Workflows (2-3 days) - HIGH
**Files:** `services/risk_engine.py`, `models/workflow.py`
**Goal:** Conditional processing

```
Tasks:
- Risk calculation engine
- Risk label assignment
- Workflow condition evaluation
- Automatic routing based on risk
- Risk threshold configuration
```

#### Sprint F4: Questionnaires (3-4 days) - MEDIUM
**Files:** `models/questionnaire.py`, `api/v1/questionnaires.py`
**Goal:** Custom data collection

```
Tasks:
- Questionnaire model with questions
- Question types (text, select, date, file)
- Questionnaire CRUD endpoints
- Answer submission endpoint
- Risk scoring from answers
```

#### Sprint F5: Address Verification (2-3 days) - MEDIUM
**Files:** `services/address.py`, `api/v1/addresses.py`
**Goal:** PoA verification

```
Tasks:
- PoA document types configuration
- Address extraction from documents
- Address validation logic
- Geolocation verification (optional)
```

#### Sprint F6: Liveness Detection (3-4 days) - MEDIUM
**Files:** `services/liveness.py`, `api/v1/liveness.py`
**Goal:** Face matching

```
Tasks:
- Face detection API integration
- Selfie vs ID photo matching
- Liveness score calculation
- Anti-spoofing checks
```

---

### Terminal 3: Frontend UI (12-18 days)

#### Sprint U1: Settings Page (3-4 days) - P0
**Files:** `components/settings/*`
**Goal:** User configuration

```
Tasks:
- SettingsPage.jsx with tabs
- GeneralSettings.jsx
- TeamSettings.jsx with invites
- WorkflowSettings.jsx
- NotificationSettings.jsx
- SecuritySettings.jsx
- BrandingSettings.jsx
- useSettings.js hook
- settings.js API service
```

#### Sprint U2: Audit Log Page (2-3 days) - P0
**Files:** `components/audit/*`
**Goal:** Compliance visibility

```
Tasks:
- AuditLogPage.jsx
- AuditLogTable.jsx with filtering
- AuditLogFilters.jsx
- AuditLogDetail.jsx modal
- useAuditLog.js hook
- audit.js API service
- CSV export
```

#### Sprint U3: Analytics Page (4-5 days) - P1
**Files:** `components/analytics/*`
**Goal:** Reporting dashboard

```
Tasks:
- AnalyticsPage.jsx
- OverviewCards.jsx KPIs
- FunnelChart.jsx
- TrendsChart.jsx
- GeoMap.jsx (optional)
- RiskDistribution.jsx
- SLAPerformance.jsx
- Install recharts
```

#### Sprint U4: Integrations Page (3-4 days) - P1
**Files:** `components/integrations/*`
**Goal:** API key management

```
Tasks:
- IntegrationsPage.jsx
- ApiKeysTab.jsx
- WebhooksTab.jsx
- CreateApiKeyModal.jsx
- CreateWebhookModal.jsx
- WebhookLogs.jsx
```

#### Sprint U5: Companies Page (5-7 days) - P1
**Files:** `components/companies/*`
**Goal:** KYB UI

```
Tasks:
- CompaniesPage.jsx list
- CompanyDetail.jsx
- CompanyForm.jsx
- UBOList.jsx
- CorporateStructure.jsx tree
- Link to individual KYC
```

#### Sprint U6: Billing Page (3-4 days) - P2
**Files:** `components/billing/*`
**Goal:** Usage tracking

```
Tasks:
- BillingPage.jsx
- UsageDashboard.jsx
- SubscriptionCard.jsx
- InvoiceList.jsx
- Stripe integration
```

---

### Terminal 4: Testing & Deployment (10-14 days)

#### Sprint T1: Unit Tests (2-3 days)
**Files:** `tests/test_*.py`
**Goal:** Service coverage

```
Tasks:
- test_screening.py
- test_storage.py
- test_ai.py
- test_audit.py
- test_encryption.py
- Minimum 80% coverage
```

#### Sprint T2: Integration Tests (2-3 days)
**Files:** `tests/integration/*`
**Goal:** API testing

```
Tasks:
- test_applicant_flow.py
- test_screening_flow.py
- test_document_flow.py
- test_case_flow.py
- Database fixtures
```

#### Sprint T3: E2E Tests (3-4 days)
**Files:** `frontend/e2e/*`
**Goal:** Full flow testing

```
Tasks:
- Playwright setup
- Applicant creation flow
- Document upload flow
- Screening review flow
- Case resolution flow
```

#### Sprint T4: Load Tests (1-2 days)
**Files:** `tests/load/*`
**Goal:** Performance validation

```
Tasks:
- k6 or locust setup
- 100+ req/min target
- API latency <500ms
- Identify bottlenecks
```

#### Sprint T5: Security Scan (1-2 days)
**Files:** Configuration
**Goal:** Vulnerability check

```
Tasks:
- OWASP ZAP scan
- Dependency audit
- Secrets scan
- Fix critical issues
```

#### Sprint T6: Production Deploy (2-3 days)
**Files:** Railway config, docs
**Goal:** Live deployment

```
Tasks:
- Railway project setup
- PostgreSQL + Redis provisioning
- Environment variables
- SSL/TLS configuration
- Health monitoring
- First customer onboarding
```

---

### Terminal 5: Advanced Features via API Integrations (10-15 days)

> **UPDATED: Use APIs instead of building from scratch!**
> See `docs/implementation-guide/16_API_INTEGRATIONS_VS_BUILD.md` for full research.
>
> **Key insight:** Building biometrics, fraud detection, etc. from scratch is high-risk
> and takes months. APIs cost ~$50-100/month and work immediately.

#### Sprint A1: Face Matching + Liveness (1-2 days) - USE AWS REKOGNITION
**Files:** `services/biometrics.py`, `api/v1/biometrics.py`
**Goal:** Compare selfie to ID photo + basic liveness
**API:** AWS Rekognition (~$0.001/image) - **Same credentials as Textract!**

```
Tasks:
- Create biometrics.py service (see 16_API_INTEGRATIONS_VS_BUILD.md for code)
- AWS Rekognition CompareFaces API for face matching
- AWS Rekognition DetectFaces API for basic liveness/quality
- API endpoint: POST /api/v1/biometrics/compare
- API endpoint: POST /api/v1/biometrics/liveness
- Store results in documents table (face_match_score, liveness_score)
- Frontend selfie capture component
```

**Cost:** ~$20/month for 10K verifications

#### Sprint A2: Fraud Detection Suite (1 day) - USE IPQUALITYSCORE
**Files:** `services/fraud_detection.py`, `api/v1/fraud.py`
**Goal:** Device fingerprinting, VPN detection, email/phone validation
**API:** IPQualityScore (~$0.0003/query) - **One API covers 4 features!**

```
Tasks:
- Create fraud_detection.py service (see 16_API_INTEGRATIONS_VS_BUILD.md for code)
- IP check: VPN, proxy, TOR, fraud score
- Email check: Disposable, deliverability, fraud score
- Phone check: VOIP, carrier, line type, fraud score
- Device fingerprint storage
- API endpoint: POST /api/v1/fraud/check-ip
- API endpoint: POST /api/v1/fraud/check-email
- API endpoint: POST /api/v1/fraud/check-phone
- Integrate into applicant creation flow
- Add risk labels based on fraud signals
```

**Cost:** ~$30/month for 100K queries (covers ALL fraud signals)

#### Sprint A3: Address Verification (1 day) - USE SMARTY
**Files:** `services/address_verification.py`, `api/v1/addresses.py`
**Goal:** Standardize and verify addresses
**API:** Smarty (Free tier - 50K/month)

```
Tasks:
- Create address_verification.py service
- US address verification and standardization
- Geocoding (lat/long)
- API endpoint: POST /api/v1/addresses/verify
- Store standardized address in applicants table
- Frontend address autocomplete (optional)
```

**Cost:** Free for MVP, ~$100/month at scale

#### Sprint A4: Reusable KYC Tokens (4-5 days) - BUILD THIS
**Files:** `models/kyc_token.py`, `api/v1/kyc_share.py`, `services/kyc_share.py`
**Goal:** Portable identity sharing
**Third-Party:** None (internal feature)

```
Tasks:
- KYC share token model
- Token generation with scope
- Consent flow and storage
- Token verification endpoint
- Token revocation
- Partner integration endpoints
- Expiry and access tracking
```

#### Sprint A5: Document Type Detection (2 days) - USE CLAUDE VISION
**Files:** Update `services/ocr.py`, add `services/document_classifier.py`
**Goal:** Detect document type before OCR
**API:** Claude Vision (already have!) - Use existing Anthropic key

```
Tasks:
- Create document_classifier.py using Claude Vision
- Prompt: "What type of ID document is this? (passport/drivers_license/id_card/other)"
- Extract country of origin
- Route to appropriate OCR templates
- Store document_type in documents table
```

**Cost:** ~$0.01 per classification (already paying for Claude)

#### Sprint A6: Video Identification (3-4 days) - USE TWILIO VIDEO
**Files:** `services/video_id.py`, `api/v1/video.py`, frontend components
**Goal:** Live operator verification calls
**API:** Twilio Video (~$0.004/min)

```
Tasks:
- Twilio Video SDK integration
- Create/join room endpoints
- Operator dashboard page
- In-call document capture
- Call recording to R2
- Integration with applicant workflow
```

**Cost:** ~$12/month for 3000 minutes

---

### API Integration Summary (Terminal 5)

| Original Plan | API Solution | Time Saved | Monthly Cost |
|---------------|--------------|------------|--------------|
| Face Matching (3-4 days) | AWS Rekognition | **2-3 days** | ~$10 |
| Liveness (3-4 days) | AWS Rekognition | **Same sprint** | Included |
| Device Intel (2-3 days) | IPQualityScore | **1-2 days** | ~$30 |
| Email/Phone (not planned) | IPQualityScore | **Free** | Included |
| Address Verif (2-3 days) | Smarty | **1-2 days** | Free |
| Doc Templates (5-7 days) | Claude Vision | **3-5 days** | ~$10 |
| Video ID (7-10 days) | Twilio Video | **3-6 days** | ~$12 |
| **TOTAL** | | **~15 days saved** | **~$62/month** |

**Original Terminal 5:** 20-30 days of high-risk development
**With APIs:** 10-15 days of integration work + battle-tested services

---

## Sprint Execution Template

### Standard Sprint Workflow

Every sprint follows this exact pattern. Copy and use for each sprint.

```
┌─────────────────────────────────────────────────────────────────────┐
│                    SPRINT EXECUTION WORKFLOW                         │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  1. PRE-SPRINT SETUP (5 min)                                        │
│     └── Pull latest code, create branch                             │
│                                                                      │
│  2. IMPLEMENTATION (varies)                                          │
│     └── Follow sprint tasks, reference Sumsub docs                  │
│                                                                      │
│  3. LOCAL TESTING (15-30 min)                                       │
│     └── Run tests, manual verification                              │
│                                                                      │
│  4. COMMIT & PUSH (5 min)                                           │
│     └── Descriptive commit message                                  │
│                                                                      │
│  5. POST-SPRINT VERIFICATION (10 min)                               │
│     └── Update tracking, verify in staging                          │
│                                                                      │
└─────────────────────────────────────────────────────────────────────┘
```

### 1. Pre-Sprint Setup

```bash
# Always start fresh
cd ~/getclearance
git checkout main
git pull origin main

# Create sprint branch
git checkout -b sprint/{terminal}-{sprint-id}
# Example: git checkout -b sprint/B1-audit-logging

# Verify environment
cd backend && source venv/bin/activate  # or your venv path
pip install -r requirements.txt
```

### 2. Implementation

Follow the sprint tasks in order. Reference files:
- **Terminal 1:** `docs/implementation-guide/14_BACKEND_SECURITY_SPRINT_PROMPTS.md`
- **Terminal 2:** `docs/implementation-guide/18_TERMINAL2_BACKEND_FEATURES_PROMPTS.md`
- **Terminal 3:** `docs/implementation-guide/19_TERMINAL3_PLACEHOLDER_PAGES_PROMPTS.md`
- **Terminal 4:** Sprint definitions in this document
- **Terminal 5:** `docs/implementation-guide/16_API_INTEGRATIONS_VS_BUILD.md`

### 3. Local Testing

#### Backend Testing Commands

```bash
# From backend/ directory

# Run all tests
pytest tests/ -v

# Run specific test file
pytest tests/test_{feature}.py -v

# Run with coverage
pytest tests/ --cov=app --cov-report=html

# Run only fast tests (skip slow integration)
pytest tests/ -v -m "not slow"

# Check for type errors
mypy app/

# Check for linting issues
ruff check app/
```

#### Frontend Testing Commands

```bash
# From frontend/ directory

# Run all tests
npm test

# Run with coverage
npm test -- --coverage

# Run specific test
npm test -- --testPathPattern="{ComponentName}"

# Lint check
npm run lint
```

#### Manual Verification Checklist

```
□ API endpoint returns expected response
□ Database records created/updated correctly
□ No console errors in browser
□ No errors in backend logs
□ Feature works end-to-end
□ Edge cases handled (empty data, errors)
```

### 4. Commit & Push

#### Commit Message Format

```bash
# Format: type(scope): description
#
# Types: feat, fix, refactor, test, docs, chore
# Scope: sprint ID or feature area

# Examples:
git commit -m "feat(B1): implement audit logging service with chain hashing"
git commit -m "feat(B1): add audit calls to applicants.py endpoints"
git commit -m "test(B1): add unit tests for audit service"
git commit -m "fix(B1): correct chain hash calculation for first entry"
```

#### Standard Commit Workflow

```bash
# Stage changes
git add -A

# Review what you're committing
git status
git diff --staged

# Commit with descriptive message
git commit -m "feat(SPRINT-ID): description of changes

- Detail 1
- Detail 2
- Detail 3"

# Push to remote
git push origin sprint/{terminal}-{sprint-id}

# Create PR (optional, or merge directly for solo dev)
gh pr create --title "Sprint {ID}: {Description}" --body "## Changes
- Change 1
- Change 2

## Testing
- [ ] Unit tests pass
- [ ] Manual testing complete
- [ ] No regressions"
```

### 5. Post-Sprint Verification

```bash
# Merge to main (after PR approval or directly)
git checkout main
git pull origin main
git merge sprint/{terminal}-{sprint-id}
git push origin main

# Tag the sprint completion
git tag -a "sprint-{ID}-complete" -m "Sprint {ID} completed"
git push origin --tags

# Update tracking in this document
# Change sprint status from TODO to DONE
# Add completion date
```

#### Verification Checklist

```
□ All tests passing on main branch
□ No merge conflicts
□ Sprint tracking table updated
□ Any new environment variables documented
□ README updated if needed
□ Team notified (if applicable)
```

---

### Sprint-Specific Testing Requirements

#### Terminal 1: Backend Security

| Sprint | Test Command | Manual Verification |
|--------|--------------|---------------------|
| B1: Audit | `pytest tests/test_audit.py -v` | Check audit_logs table after CRUD operations |
| B2: Rate Limit | `for i in {1..10}; do curl -X POST .../auth/token; done` | Should get 429 after limit |
| B3: Encryption | `pytest tests/test_encryption.py -v` | Query DB, confirm encrypted values |
| B4: Missing APIs | `curl` each new endpoint | Verify 200 responses |
| B5: GDPR | `pytest tests/test_gdpr.py -v` | Test export/delete endpoints |
| B6: Monitoring | Check Sentry dashboard | Verify errors captured |

#### Terminal 2: Backend Features

| Sprint | Test Command | Manual Verification |
|--------|--------------|---------------------|
| F1: Ongoing AML | `pytest tests/test_monitoring.py -v` | Trigger re-screening, check alerts |
| F2: KYB | `pytest tests/test_companies.py -v` | Create company, add UBOs |
| F3: Risk Workflows | `pytest tests/test_risk.py -v` | Verify routing based on risk |
| F4: Questionnaires | `pytest tests/test_questionnaires.py -v` | Submit answers, check scoring |
| F5: Address | `pytest tests/test_address.py -v` | Upload PoA, verify extraction |
| F6: Liveness | `pytest tests/test_liveness.py -v` | Mock face detection response |

#### Terminal 3: Frontend

| Sprint | Test Command | Manual Verification |
|--------|--------------|---------------------|
| U1: Settings | `npm test -- Settings` | Navigate all tabs, save settings |
| U2: Audit Log | `npm test -- AuditLog` | Filter, paginate, export CSV |
| U3: Analytics | `npm test -- Analytics` | Charts render, date filters work |
| U4: Integrations | `npm test -- Integrations` | Create/revoke API key |
| U5: Companies | `npm test -- Companies` | Full KYB workflow |
| U6: Billing | `npm test -- Billing` | Usage displays correctly |

#### Terminal 4: Testing & Deploy

| Sprint | Test Command | Manual Verification |
|--------|--------------|---------------------|
| T1: Unit | `pytest --cov=app --cov-fail-under=80` | 80%+ coverage |
| T2: Integration | `pytest tests/integration/ -v` | All flows pass |
| T3: E2E | `npx playwright test` | All scenarios pass |
| T4: Load | `k6 run tests/load/script.js` | <500ms p95 latency |
| T5: Security | Run OWASP ZAP | No critical findings |
| T6: Deploy | Health check endpoints | 200 OK on production |

---

## Technical Specifications

### Sumsub API Patterns to Match

#### Authentication
```
Header: X-App-Token: <token>
Header: X-App-Access-Ts: <timestamp>
Header: X-App-Access-Sig: <signature>
```

#### Applicant Statuses
```python
APPLICANT_STATUSES = {
    "init": "Documents requested",
    "pending": "Pending verification",
    "awaitingService": "Awaiting external service",
    "onHold": "Requires manual action",
    "awaitingUser": "Awaiting user action",
    "completed": "Final decision made",
}

REVIEW_ANSWERS = {
    "GREEN": "approved",
    "RED": "rejected",
}

REJECT_TYPES = {
    "FINAL": "Permanent rejection",
    "RETRY": "Resubmission allowed",
}
```

#### Webhook Payload Structure
```json
{
  "applicantId": "uuid",
  "inspectionId": "uuid",
  "correlationId": "uuid",
  "levelName": "basic-kyc",
  "externalUserId": "external-id",
  "type": "applicantReviewed",
  "reviewResult": {
    "reviewAnswer": "GREEN",
    "moderationComment": "string",
    "clientComment": "string",
    "rejectLabels": ["label"],
    "reviewRejectType": "FINAL|RETRY",
    "buttonIds": ["buttonId"]
  },
  "reviewStatus": "completed",
  "createdAt": "2025-12-02T00:00:00.000Z"
}
```

#### Fuzzy Matching Algorithm
```python
def calculate_match_score(
    query_name: str,
    hit_name: str,
    query_dob: date | None,
    hit_dob: date | None,
    query_country: str | None,
    hit_country: str | None,
) -> float:
    """
    Calculate 0-100 confidence score.

    Weights:
    - Name match: 60%
    - DOB match: 30%
    - Country match: 10%

    Name matching uses:
    - Levenshtein distance (fuzzy)
    - Soundex (phonetic)
    - Metaphone (phonetic)
    """
    score = 0.0

    # Name matching (60%)
    name_score = max(
        levenshtein_similarity(query_name, hit_name),
        soundex_match(query_name, hit_name),
        metaphone_match(query_name, hit_name),
    )
    score += name_score * 0.6

    # DOB matching (30%)
    if query_dob and hit_dob:
        if query_dob == hit_dob:
            score += 30
        elif query_dob.year == hit_dob.year:
            score += 15
    elif not query_dob and not hit_dob:
        score += 15  # No DOB to compare

    # Country matching (10%)
    if query_country and hit_country:
        if query_country == hit_country:
            score += 10
        elif are_related_countries(query_country, hit_country):
            score += 5

    return min(100, max(0, score))

# Match classification
def classify_match(score: float) -> str:
    if score >= 90:
        return "true_positive"
    elif score >= 60:
        return "potential_match"
    elif score >= 40:
        return "false_positive"
    else:
        return "unknown"
```

#### Risk Label Categories
```python
RISK_CATEGORIES = {
    "email_phone": [
        "disposable_email",
        "high_risk_email",
        "virtual_number",
        "non_deliverable",
    ],
    "device": [
        "vpn_detected",
        "tor_detected",
        "jailbroken",
        "emulator",
        "location_spoofing",
    ],
    "cross_check": [
        "country_mismatch",
        "ip_country_mismatch",
        "duplicate_account",
    ],
    "selfie": [
        "age_mismatch",
        "third_party_involvement",
        "virtual_camera",
    ],
    "aml": [
        "sanctions_hit",
        "pep_hit",
        "adverse_media",
        "criminal_activity",
    ],
    "person": [
        "famous_person",
        "name_mismatch",
        "suspicious_name",
    ],
    "company": [
        "missing_required_fields",
        "data_inconsistency",
        "unavailable_ubo_info",
    ],
}
```

---

## Success Metrics

### Feature Parity Targets

| Metric | Sumsub | GetClearance Target | Current |
|--------|--------|---------------------|---------|
| Document types | 220+ countries | 50+ countries MVP | PARTIAL |
| Languages | 40+ | 10+ MVP | PARTIAL |
| Security features | 40+ | MRZ + basic | DONE |
| Screening lists | 100+ | OpenSanctions | DONE |
| Applicant statuses | 7 | 7 | 5/7 |
| API endpoints | 100+ | 50+ MVP | ~30 |

### Performance Targets

| Metric | Sumsub | GetClearance Target | Current |
|--------|--------|---------------------|---------|
| Verification time | "Minutes" | <30 seconds | ~45s |
| API latency (p95) | ~1-2s | <500ms | ~800ms |
| Auto-approval rate | 50-60% | >70% | N/A |
| False positive rate | 10-15% | <5% | ~8% |

### Compliance Targets

| Requirement | Status | Target |
|-------------|--------|--------|
| Audit logging | ✅ DONE | 100% coverage |
| PII encryption | ✅ DONE | All PII fields |
| Rate limiting | ✅ DONE | All endpoints |
| GDPR SAR | ✅ DONE | Implemented |
| GDPR deletion | ✅ DONE | Implemented |
| Monitoring | ✅ DONE | Sentry + structured logging |
| SOC 2 readiness | READY | Type 1 ready |

---

## Execution Instructions

### How to Use This Document

1. **Pick a terminal/workstream** based on available developers
2. **Start sprints in order** within each terminal
3. **Use sprint prompts** from companion documents
4. **Update status** in this document as sprints complete
5. **Cross-reference** Sumsub docs when implementing features

### Quick Start for Each Terminal

**Terminal 1 (Backend Security):**
```bash
cd getclearance
# Open: docs/implementation-guide/14_BACKEND_SECURITY_SPRINT_PROMPTS.md
# Copy-paste: Sprint B1 prompt (Audit Logging)
```

**Terminal 2 (Backend Features):**
```bash
cd getclearance
# Open: docs/implementation-guide/18_TERMINAL2_BACKEND_FEATURES_PROMPTS.md
# Copy-paste: Sprint F1 prompt (Ongoing AML)
```

**Terminal 3 (Placeholder Pages):**
```bash
cd getclearance
# Open: docs/implementation-guide/19_TERMINAL3_PLACEHOLDER_PAGES_PROMPTS.md
# Copy-paste: Sprint S10 prompt (Settings Page)
```

**Terminal 4 (Testing):**
```bash
cd getclearance
# Wait for Terminals 1-3 to complete critical sprints
# Start: Sprint T1 (Unit Tests)
```

> **Note:** `09_FRONTEND_SPRINT_PROMPTS.md` contains Sprints 1-9 which are ALREADY COMPLETE.
> Terminal 3 now uses `19_TERMINAL3_PLACEHOLDER_PAGES_PROMPTS.md` for Sprints 10-17.

### Sprint Tracking

| Sprint | Terminal | Status | Started | Completed |
|--------|----------|--------|---------|-----------|
| B1: Audit | 1 | TODO | - | - |
| B2: Rate Limit | 1 | TODO | - | - |
| B3: Encryption | 1 | TODO | - | - |
| B4: Missing APIs | 1 | TODO | - | - |
| B5: GDPR | 1 | TODO | - | - |
| B6: Monitoring | 1 | TODO | - | - |
| F1: Ongoing AML | 2 | TODO | - | - |
| F2: KYB | 2 | TODO | - | - |
| F3: Risk Workflows | 2 | TODO | - | - |
| F4: Questionnaires | 2 | TODO | - | - |
| F5: Address | 2 | TODO | - | - |
| F6: Liveness | 2 | TODO | - | - |
| U1: Settings | 3 | TODO | - | - |
| U2: Audit Log | 3 | TODO | - | - |
| U3: Analytics | 3 | TODO | - | - |
| U4: Integrations | 3 | TODO | - | - |
| U5: Companies | 3 | TODO | - | - |
| U6: Billing | 3 | TODO | - | - |
| T1: Unit Tests | 4 | TODO | - | - |
| T2: Integration | 4 | TODO | - | - |
| T3: E2E | 4 | TODO | - | - |
| T4: Load | 4 | TODO | - | - |
| T5: Security | 4 | TODO | - | - |
| T6: Deploy | 4 | TODO | - | - |

---

## References

### Sumsub Documentation Links

**Core Verification:**
- [How ID Verification Works](https://docs.sumsub.com/docs/how-id-verification-works)
- [Applicant Statuses](https://docs.sumsub.com/docs/applicant-statuses)
- [Risk Labels](https://docs.sumsub.com/docs/applicant-risk-labels)
- [Database Validation](https://docs.sumsub.com/docs/database-validation)

**AML Screening:**
- [AML Screening](https://docs.sumsub.com/docs/aml-screening)
- [Fuzzy Matching](https://docs.sumsub.com/docs/fuzzy-matching)
- [Ongoing Monitoring](https://docs.sumsub.com/docs/ongoing-aml-monitoring)
- [Process Results](https://docs.sumsub.com/docs/process-aml-screening-results)

**Additional Features:**
- [Liveness](https://docs.sumsub.com/docs/liveness)
- [Address Verification](https://docs.sumsub.com/docs/address-verification)
- [Questionnaires](https://docs.sumsub.com/docs/questionnaire)
- [Reusable KYC](https://docs.sumsub.com/docs/reusable-kyc)

**API Reference:**
- [API Overview](https://docs.sumsub.com/reference/about-sumsub-api)
- [Results via API](https://docs.sumsub.com/docs/receive-and-interpret-results-via-api)

---

## Third-Party Services Required

### Currently Integrated

| Service | Purpose | Cost | Status |
|---------|---------|------|--------|
| **OpenSanctions** | AML screening data | Free (open source) | **INTEGRATED** |
| **AWS Textract** | OCR text extraction | ~$1.50/1000 pages | **CODE READY** (needs AWS creds) |
| **Claude AI** | Risk summaries, analysis | ~$0.01-0.03/request | **INTEGRATED** |
| **Cloudflare R2** | Document storage | $0.015/GB/mo | **INTEGRATED** |
| **Auth0** | Authentication | Free tier available | **INTEGRATED** |
| **PostgreSQL** | Database | Railway included | **INTEGRATED** |
| **Redis** | Job queue, caching | Railway included | **INTEGRATED** |

### Recommended API Stack (Terminal 5)

> **See `16_API_INTEGRATIONS_VS_BUILD.md` for full research and code examples**

| Service | Purpose | Cost | Sprint | Priority |
|---------|---------|------|--------|----------|
| **AWS Rekognition** | Face matching + liveness | ~$0.001/image | A1 | **HIGH** |
| **IPQualityScore** | Device, email, phone, VPN fraud detection | ~$0.0003/query | A2 | **HIGH** |
| **Smarty** | Address verification | Free-$100/mo | A3 | MEDIUM |
| **Twilio Video** | Video identification | ~$0.004/min | A6 | LOW |

### Total API Cost Estimate

| Volume | AWS Rekognition | IPQS | Smarty | Twilio | **Total** |
|--------|-----------------|------|--------|--------|-----------|
| 1K verif/mo | ~$2 | ~$1 | Free | - | **~$3/mo** |
| 10K verif/mo | ~$20 | ~$10 | Free | - | **~$30/mo** |
| 100K verif/mo | ~$100 | ~$30 | ~$100 | - | **~$230/mo** |

### Optional Enhancements

| Service | Purpose | Cost | When to Add |
|---------|---------|------|-------------|
| **Sentry** | Error monitoring | Free tier | Sprint B6 |
| **Stripe** | Billing | 2.9% + $0.30/tx | Sprint U6 |
| **SendGrid** | Email notifications | Free tier | When needed |
| **Persona** | Government DB validation | $250+/mo | If customers demand it |
| **Microblink** | More document templates | Quote | If going international |

### Environment Variables Needed

```bash
# ===========================================
# CURRENTLY REQUIRED (should already have)
# ===========================================
DATABASE_URL=postgresql+asyncpg://...
REDIS_URL=redis://...
AUTH0_DOMAIN=your-domain.auth0.com
AUTH0_CLIENT_ID=...
AUTH0_CLIENT_SECRET=...
ANTHROPIC_API_KEY=sk-ant-...
R2_ENDPOINT=https://...r2.cloudflarestorage.com
R2_ACCESS_KEY_ID=...
R2_SECRET_ACCESS_KEY=...
R2_BUCKET=getclearance-documents

# ===========================================
# AWS (Textract OCR + Rekognition Biometrics)
# ===========================================
# Get from: AWS IAM Console
# IMPORTANT: Same credentials work for BOTH Textract and Rekognition!
AWS_ACCESS_KEY_ID=<your-aws-key>
AWS_SECRET_ACCESS_KEY=<your-aws-secret>
AWS_REGION=us-east-1

# ===========================================
# SPRINT B3 (PII Encryption)
# ===========================================
ENCRYPTION_KEY=<generate with: openssl rand -hex 32>
ENCRYPTION_SALT=getclearance-pii-salt-v1

# ===========================================
# SPRINT B6 (Monitoring)
# ===========================================
SENTRY_DSN=https://...@sentry.io/...

# ===========================================
# TERMINAL 5 APIs (Advanced Features)
# ===========================================

# Sprint A2 - IPQualityScore (Device, Email, Phone, VPN detection)
# Get from: https://www.ipqualityscore.com/create-account
# FREE tier available for testing!
IPQS_API_KEY=<your-ipqs-key>

# Sprint A3 - Smarty (Address Verification)
# Get from: https://www.smarty.com/products/apis
# FREE tier: 50K lookups/month
SMARTY_AUTH_ID=<your-smarty-auth-id>
SMARTY_AUTH_TOKEN=<your-smarty-auth-token>

# Sprint A6 - Twilio Video (Video Identification)
# Get from: https://console.twilio.com/
TWILIO_ACCOUNT_SID=<your-twilio-sid>
TWILIO_AUTH_TOKEN=<your-twilio-token>

# ===========================================
# OPTIONAL - Add when needed
# ===========================================

# Persona (Government DB validation) - Sprint when customers demand it
PERSONA_API_KEY=<your-persona-key>

# Stripe (Billing) - Sprint U6
STRIPE_SECRET_KEY=<your-stripe-secret>
STRIPE_PUBLISHABLE_KEY=<your-stripe-publishable>
```

### AWS Credentials Setup

Since you're using **both Textract (OCR) and Rekognition (biometrics)**, here's the IAM policy needed:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "textract:DetectDocumentText",
        "textract:AnalyzeDocument",
        "rekognition:CompareFaces",
        "rekognition:DetectFaces"
      ],
      "Resource": "*"
    }
  ]
}
```

Create an IAM user with this policy, then use the access key/secret for both services.

---

## Updated Sprint Tracking (All 5 Terminals)

### Terminal 1: Backend Security ✅ ALL COMPLETE

| Sprint | Status | Started | Completed | Notes |
|--------|--------|---------|-----------|-------|
| B1: Audit Logging | ✅ DONE | Dec 2, 2025 | Dec 2, 2025 | 12 tests, chain hashing |
| B2: Rate Limiting | ✅ DONE | Dec 2, 2025 | Dec 2, 2025 | slowapi, security headers |
| B3: PII Encryption | ✅ DONE | Dec 2, 2025 | Dec 2, 2025 | 22 tests, Fernet AES |
| B4: Missing APIs | ✅ DONE | Dec 2, 2025 | Dec 2, 2025 | GET /hits, batch status |
| B5: GDPR Features | ✅ DONE | Dec 2, 2025 | Dec 2, 2025 | 12 tests, SAR export |
| B6: Monitoring | ✅ DONE | Dec 2, 2025 | Dec 2, 2025 | 24 tests, Sentry, structured logging |

### Terminal 2: Backend Features

| Sprint | Status | Started | Completed | Notes |
|--------|--------|---------|-----------|-------|
| F1: Ongoing AML | TODO | - | - | HIGH |
| F2: KYB Module | TODO | - | - | HIGH |
| F3: Risk Workflows | TODO | - | - | HIGH |
| F4: Questionnaires | TODO | - | - | MEDIUM |
| F5: Address Verif | TODO | - | - | MEDIUM |
| F6: Liveness | TODO | - | - | MEDIUM |

### Terminal 3: Frontend UI

| Sprint | Status | Started | Completed | Notes |
|--------|--------|---------|-----------|-------|
| U1: Settings | TODO | - | - | P0 |
| U2: Audit Log | TODO | - | - | P0 |
| U3: Analytics | TODO | - | - | P1 |
| U4: Integrations | TODO | - | - | P1 |
| U5: Companies | TODO | - | - | P1 |
| U6: Billing | TODO | - | - | P2 |

### Terminal 4: Testing & Deploy

| Sprint | Status | Started | Completed | Notes |
|--------|--------|---------|-----------|-------|
| T1: Unit Tests | TODO | - | - | Requires B1-B6 |
| T2: Integration | TODO | - | - | Requires F1-F6 |
| T3: E2E Tests | TODO | - | - | Requires U1-U6 |
| T4: Load Tests | TODO | - | - | |
| T5: Security Scan | TODO | - | - | |
| T6: Deploy | TODO | - | - | Final step |

### Terminal 5: Advanced Features via APIs (10-15 days total)

| Sprint | Status | Started | Completed | API/Notes |
|--------|--------|---------|-----------|-----------|
| A1: Face Match + Liveness | TODO | - | - | **AWS Rekognition** (1-2 days) |
| A2: Fraud Detection Suite | TODO | - | - | **IPQualityScore** (1 day) - covers 4 features! |
| A3: Address Verification | TODO | - | - | **Smarty** (1 day) - Free tier |
| A4: Reusable KYC | TODO | - | - | Build (4-5 days) |
| A5: Document Classification | TODO | - | - | **Claude Vision** (2 days) - already have key |
| A6: Video ID | TODO | - | - | **Twilio Video** (3-4 days) |

**API Cost:** ~$62/month at 10K verifications (vs months of development)

---

## Quick Reference: Which Document for Which Sprint

| Terminal | Primary Document | Status |
|----------|-----------------|--------|
| **Terminal 1** | `14_BACKEND_SECURITY_SPRINT_PROMPTS.md` | READY - Has copy-paste prompts |
| **Terminal 2** | `18_TERMINAL2_BACKEND_FEATURES_PROMPTS.md` | READY - Has copy-paste prompts |
| **Terminal 3** | `19_TERMINAL3_PLACEHOLDER_PAGES_PROMPTS.md` | READY - Has copy-paste prompts |
| **Terminal 4** | Sprint definitions in this document | Wait for T1-T3 |
| **Terminal 5** | `16_API_INTEGRATIONS_VS_BUILD.md` + this document | Optional advanced |

**HISTORICAL (Already Implemented):**
- `09_FRONTEND_SPRINT_PROMPTS.md` - Sprints 1-9 COMPLETE (per README)

---

## Checklist: Ready to Start?

Before beginning any sprint work:

```
□ Read this entire MASTER document
□ Understand realistic feature parity expectations (~70-75%)
□ Have all environment variables configured
□ Backend runs locally without errors
□ Frontend runs locally without errors
□ Database migrations are up to date
□ Decided which terminal to start with
□ Have the companion sprint prompt document ready
```

**Recommended Starting Order:**
1. **Terminal 1 first** - Security is critical, blocks production
2. **Terminal 2 & 3 in parallel** - Backend features + Frontend UI
3. **Terminal 4 after 1-3** - Testing requires features to exist
4. **Terminal 5 optional** - Only if you need advanced features

---

**Last Updated:** December 2, 2025
**Status:** Terminal 1 (Backend Security) 100% COMPLETE - All 6 sprints done with 250 tests passing
**Next Review:** After Terminal 2/3/4/5 sprint completions
