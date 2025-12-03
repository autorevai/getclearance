# Terminal Context Files Guide
**Purpose:** What exists, what to create, what to leverage for each terminal

---

## Current Codebase Summary

### Backend (~9,700+ lines of Python)

```
backend/app/
├── config.py              ✅ COMPLETE - Settings from env vars
├── database.py            ✅ COMPLETE - Async SQLAlchemy setup
├── dependencies.py        ✅ COMPLETE - FastAPI dependencies
├── main.py                ✅ COMPLETE - App entrypoint
│
├── models/                ✅ COMPLETE - All models exist
│   ├── applicant.py       (336 lines) - Full applicant model
│   ├── document.py        (218 lines) - Documents with metadata
│   ├── screening.py       (242 lines) - Screening checks/hits
│   ├── case.py            (163 lines) - Case management
│   ├── audit.py           (128 lines) - Audit log model (NOT CALLED)
│   ├── tenant.py          (105 lines) - Multi-tenancy
│   └── base.py            (68 lines) - Base model class
│
├── schemas/               ⚠️ PARTIAL - Need more schemas
│   ├── applicant.py       - Applicant DTOs
│   └── webhook.py         - Webhook payloads
│
├── api/v1/               ✅ MOSTLY COMPLETE
│   ├── applicants.py      (739 lines) - CRUD + review
│   ├── screening.py       (729 lines) - Check + resolve
│   ├── auth.py            (672 lines) - Auth0 + dev mode
│   ├── documents.py       (547 lines) - Upload/download
│   ├── cases.py           (392 lines) - Case management
│   ├── dashboard.py       (317 lines) - Stats
│   └── ai.py              (295 lines) - Risk summaries
│
├── services/             ✅ COMPLETE - Core services exist
│   ├── evidence.py        (873 lines) - PDF generation
│   ├── ai.py              (698 lines) - Claude integration
│   ├── ocr.py             (671 lines) - AWS Textract
│   ├── screening.py       (599 lines) - OpenSanctions
│   ├── webhook.py         (598 lines) - Delivery + retry
│   ├── storage.py         (561 lines) - R2/S3 presigned URLs
│   ├── timeline.py        (438 lines) - Event aggregation
│   └── mrz_parser.py      (417 lines) - Passport MRZ
│
├── workers/              ✅ COMPLETE - Background jobs
│   ├── config.py          - ARQ configuration
│   ├── screening_worker.py
│   ├── document_worker.py
│   ├── ai_worker.py
│   └── webhook_worker.py
│
└── migrations/versions/  ✅ 4 migrations exist
    ├── 20251130_001_initial_schema.py
    ├── 20251130_002_add_sumsub_features.py
    ├── 20251201_001_add_webhook_configs.py
    └── 20251201_002_add_missing_updated_at.py
```

### Frontend (~40+ components)

```
frontend/src/
├── App.jsx                ✅ Router setup
├── index.js               ✅ Entry point
│
├── auth/                  ✅ COMPLETE
│   ├── AuthProvider.jsx
│   ├── useAuth.js
│   ├── ProtectedRoute.jsx
│   └── AuthErrorBoundary.jsx
│
├── components/            ✅ MOSTLY COMPLETE
│   ├── AppShell.jsx       - Layout with sidebar
│   ├── Dashboard.jsx      - Stats cards + charts
│   ├── ApplicantsList.jsx - Table with filters
│   ├── ApplicantDetail.jsx- Full detail view
│   ├── ApplicantAssistant.jsx - AI chat
│   ├── CaseManagement.jsx - Cases list + filters
│   ├── ScreeningChecks.jsx- AML results
│   ├── DocumentUpload.jsx - Drag/drop upload
│   ├── DocumentPreview.jsx- View documents
│   ├── DocumentList.jsx   - Document table
│   ├── CreateApplicantModal.jsx
│   ├── SearchModal.jsx    - Global search
│   ├── LoginPage.jsx
│   ├── LoadingScreen.jsx
│   ├── ErrorBoundary.jsx
│   └── DesignSystem.jsx   - Component library
│
├── components/shared/     ✅ COMPLETE
│   ├── Toast.jsx
│   ├── ConfirmDialog.jsx
│   ├── LoadingSpinner.jsx
│   ├── LoadingSkeleton.jsx
│   ├── ErrorState.jsx
│   └── NotFound.jsx
│
├── components/pages/      ⚠️ PLACEHOLDERS - Need implementation
│   ├── SettingsPage.jsx   - Coming Soon placeholder
│   ├── AuditLogPage.jsx   - Coming Soon placeholder
│   ├── AnalyticsPage.jsx  - Coming Soon placeholder
│   ├── IntegrationsPage.jsx - Coming Soon placeholder
│   ├── CompaniesPage.jsx  - Coming Soon placeholder
│   ├── BillingPage.jsx    - Coming Soon placeholder
│   ├── ReusableKYCPage.jsx- Coming Soon placeholder
│   ├── DeviceIntelligencePage.jsx - Coming Soon placeholder
│   └── ComingSoon.jsx     - Placeholder component
│
├── hooks/                 ✅ COMPLETE
│   ├── useApplicants.js
│   ├── useCases.js
│   ├── useDocuments.js
│   ├── useScreening.js
│   ├── useDashboard.js
│   ├── useAI.js
│   ├── useToast.js
│   ├── useDebounce.js
│   ├── useClickOutside.js
│   ├── useKeyboardShortcut.js
│   ├── useFocusTrap.js
│   ├── useGlobalSearch.js
│   ├── useNavigationCounts.js
│   ├── usePermissions.js
│   └── useRealtimeUpdates.js
│
├── services/              ✅ COMPLETE
│   ├── api.js             - Axios instance
│   ├── applicants.js
│   ├── cases.js
│   ├── documents.js
│   ├── screening.js
│   ├── dashboard.js
│   └── ai.js
│
├── contexts/              ✅ COMPLETE
│   └── ToastContext.jsx
│
└── utils/                 ⚠️ MINIMAL
    └── errors.js
```

---

## Terminal 1: Backend Security

### What EXISTS (leverage these):

| File | Status | Notes |
|------|--------|-------|
| `models/audit.py` | ✅ Model exists | Has `AuditLog` + `compute_checksum()` |
| `config.py` | ✅ Settings exist | Has rate limit settings (not used) |
| `dependencies.py` | ✅ Exists | Add rate limit dependency here |
| `main.py` | ✅ Exists | Add middleware here |

### What to CREATE:

| Sprint | Files to Create | Leverage |
|--------|-----------------|----------|
| **B1: Audit Logging** | `services/audit.py` | Use existing `models/audit.py` |
| | Update `api/v1/applicants.py` | Add 4 audit calls |
| | Update `api/v1/cases.py` | Add 3 audit calls |
| | Update `api/v1/screening.py` | Add 1 audit call |
| **B2: Rate Limiting** | Update `main.py` | Add slowapi middleware |
| | Update `dependencies.py` | Add rate limit dependency |
| | Update `api/v1/auth.py` | Fix dev mode bypass |
| **B3: PII Encryption** | `services/encryption.py` | New file |
| | `models/types.py` | EncryptedString SQLAlchemy type |
| | Migration | Encrypt existing PII |
| **B4: Missing APIs** | Update `api/v1/screening.py` | Add GET /hits endpoint |
| | Update `api/v1/ai.py` | Add batch/suggestions endpoints |
| **B5: GDPR** | Update `api/v1/applicants.py` | Add export/delete endpoints |
| | `services/retention.py` | New retention policy service |
| **B6: Monitoring** | Update `main.py` | Add Sentry |
| | `logging_config.py` | Structured logging |

### Context Files to Read for Terminal 1:

```
# Essential (read these first)
backend/app/models/audit.py        # Audit model already exists!
backend/app/config.py              # Settings structure
backend/app/main.py                # Where to add middleware
backend/app/dependencies.py        # FastAPI dependencies

# API files to update
backend/app/api/v1/applicants.py   # Add audit calls here
backend/app/api/v1/cases.py        # Add audit calls here
backend/app/api/v1/screening.py    # Add audit calls here
backend/app/api/v1/auth.py         # Fix security issues

# Reference
docs/implementation-guide/14_BACKEND_SECURITY_SPRINT_PROMPTS.md
```

---

## Terminal 2: Backend Features

### What EXISTS (leverage these):

| File | Status | Notes |
|------|--------|-------|
| `services/screening.py` | ✅ Complete | Add ongoing monitoring to this |
| `models/applicant.py` | ✅ Complete | Has monitoring_enabled field |
| `workers/screening_worker.py` | ✅ Complete | Add monitoring worker logic |
| `api/v1/dashboard.py` | ✅ Exists | Add monitoring stats |

### What to CREATE:

| Sprint | Files to Create | Leverage |
|--------|-----------------|----------|
| **F1: Ongoing AML** | `services/monitoring.py` | Use `services/screening.py` patterns |
| | `workers/monitoring_worker.py` | Use existing worker patterns |
| | Update `api/v1/screening.py` | Add monitoring endpoints |
| **F2: KYB Module** | `models/company.py` | New model |
| | `models/beneficial_owner.py` | New model |
| | `api/v1/companies.py` | New router |
| | `services/kyb_screening.py` | Use `services/screening.py` |
| | Migration | Add company tables |
| **F3: Risk Workflows** | `services/risk_engine.py` | New service |
| | `models/workflow.py` | New model (optional) |
| | Update applicant processing | Add risk routing |
| **F4: Questionnaires** | `models/questionnaire.py` | New model |
| | `api/v1/questionnaires.py` | New router |
| **F5: Address Verif** | `services/address.py` | New service (Smarty API) |
| | Update `api/v1/documents.py` | Add PoA processing |
| **F6: Liveness** | `services/liveness.py` | New service (placeholder) |

### Context Files to Read for Terminal 2:

```
# Essential patterns to follow
backend/app/services/screening.py  # Pattern for new services
backend/app/workers/screening_worker.py  # Pattern for workers
backend/app/models/applicant.py    # Model patterns
backend/app/api/v1/applicants.py   # API patterns

# For KYB, reference applicant structure
backend/app/models/applicant.py
backend/app/api/v1/applicants.py

# Reference
docs/implementation-guide/15_FEATURE_COMPLETION_SPRINTS.md
```

---

## Terminal 3: Frontend UI

### What EXISTS (leverage these):

| File | Status | Notes |
|------|--------|-------|
| `components/pages/*.jsx` | ⚠️ Placeholders | Replace ComingSoon content |
| `components/AppShell.jsx` | ✅ Complete | Sidebar already has nav links |
| `hooks/*.js` | ✅ Complete | 15 hooks to reuse |
| `services/*.js` | ✅ Complete | API patterns established |
| `components/shared/*.jsx` | ✅ Complete | Reusable components |

### What to CREATE/UPDATE:

| Sprint | Files to Create | Leverage |
|--------|-----------------|----------|
| **U1: Settings** | Replace `pages/SettingsPage.jsx` | Use shared components |
| | `services/settings.js` | Follow `api.js` pattern |
| | `hooks/useSettings.js` | Follow hook patterns |
| **U2: Audit Log** | Replace `pages/AuditLogPage.jsx` | Use Table from ApplicantsList |
| | `services/audit.js` | Follow API pattern |
| | `hooks/useAuditLog.js` | Follow hook pattern |
| **U3: Analytics** | Replace `pages/AnalyticsPage.jsx` | Use Dashboard patterns |
| | Install recharts | For charts |
| **U4: Integrations** | Replace `pages/IntegrationsPage.jsx` | Use modal patterns |
| | `services/integrations.js` | New service |
| **U5: Companies** | Replace `pages/CompaniesPage.jsx` | Copy ApplicantsList pattern |
| | `services/companies.js` | New service |
| | `hooks/useCompanies.js` | Follow hook pattern |
| **U6: Billing** | Replace `pages/BillingPage.jsx` | New page |

### Context Files to Read for Terminal 3:

```
# Essential patterns
frontend/src/components/ApplicantsList.jsx  # Table + filters pattern
frontend/src/components/ApplicantDetail.jsx # Detail view pattern
frontend/src/components/Dashboard.jsx       # Cards + stats pattern
frontend/src/hooks/useApplicants.js         # Hook pattern
frontend/src/services/applicants.js         # Service pattern
frontend/src/services/api.js                # Base API setup

# Shared components to reuse
frontend/src/components/shared/Toast.jsx
frontend/src/components/shared/ConfirmDialog.jsx
frontend/src/components/shared/LoadingSpinner.jsx

# Pages to replace (currently placeholders)
frontend/src/components/pages/SettingsPage.jsx
frontend/src/components/pages/AuditLogPage.jsx
frontend/src/components/pages/AnalyticsPage.jsx

# Reference
docs/implementation-guide/09_FRONTEND_SPRINT_PROMPTS.md
docs/implementation-guide/15_FEATURE_COMPLETION_SPRINTS.md
```

---

## Terminal 4: Testing & Deploy

### What EXISTS:

| File | Status | Notes |
|------|--------|-------|
| `backend/tests/conftest.py` | ✅ Exists | Test fixtures |
| `backend/tests/test_*.py` | ⚠️ Partial | Some tests exist |
| `frontend/src/__tests__/*.jsx` | ⚠️ Partial | 3 document tests |
| `frontend/setupTests.js` | ✅ Exists | Jest setup |

### What to CREATE:

| Sprint | Files to Create | Leverage |
|--------|-----------------|----------|
| **T1: Unit Tests** | `tests/test_audit.py` | Use conftest fixtures |
| | `tests/test_encryption.py` | |
| | `tests/test_screening.py` | |
| **T2: Integration** | `tests/integration/*.py` | New directory |
| **T3: E2E** | `frontend/e2e/*.spec.js` | Playwright |
| | `playwright.config.js` | |
| **T4: Load** | `tests/load/script.js` | k6 or locust |
| **T5: Security** | OWASP ZAP config | External tool |
| **T6: Deploy** | Railway configs | Update existing |

### Context Files to Read for Terminal 4:

```
# Test patterns
backend/tests/conftest.py
frontend/src/__tests__/DocumentUpload.test.jsx
frontend/src/setupTests.js

# What to test
backend/app/services/*.py
backend/app/api/v1/*.py
frontend/src/components/*.jsx
```

---

## Terminal 5: Advanced APIs

### What EXISTS:

| File | Status | Notes |
|------|--------|-------|
| AWS config in `config.py` | ✅ Settings exist | Add Rekognition to same creds |
| `services/ocr.py` | ✅ AWS pattern | Copy for Rekognition |

### What to CREATE:

| Sprint | Files to Create | Leverage |
|--------|-----------------|----------|
| **A1: Face Match** | `services/biometrics.py` | Use `services/ocr.py` AWS pattern |
| | `api/v1/biometrics.py` | New router |
| **A2: Fraud Detection** | `services/fraud_detection.py` | New (IPQS API) |
| | `api/v1/fraud.py` | New router |
| **A3: Address** | `services/address_verification.py` | New (Smarty API) |
| **A4: Reusable KYC** | `models/kyc_token.py` | New model |
| | `services/kyc_share.py` | New service |
| **A5: Doc Classify** | `services/document_classifier.py` | Use `services/ai.py` pattern |
| **A6: Video ID** | `services/video_id.py` | New (Twilio API) |

---

## Quick Start Commands for Each Terminal

### Terminal 1: Backend Security
```bash
cd ~/getclearance

# Read these files first
cat backend/app/models/audit.py
cat backend/app/main.py
cat backend/app/dependencies.py

# Key prompt file
cat docs/implementation-guide/14_BACKEND_SECURITY_SPRINT_PROMPTS.md
```

### Terminal 2: Backend Features
```bash
cd ~/getclearance

# Read these patterns
cat backend/app/services/screening.py
cat backend/app/models/applicant.py
cat backend/app/api/v1/applicants.py

# Key prompt file
cat docs/implementation-guide/15_FEATURE_COMPLETION_SPRINTS.md
```

### Terminal 3: Frontend
```bash
cd ~/getclearance/frontend

# Read these patterns
cat src/components/ApplicantsList.jsx
cat src/hooks/useApplicants.js
cat src/services/applicants.js

# See what's placeholder
cat src/components/pages/SettingsPage.jsx
```

### Terminal 4: Testing
```bash
cd ~/getclearance

# See existing test setup
cat backend/tests/conftest.py
cat frontend/src/setupTests.js
ls -la backend/tests/
ls -la frontend/src/__tests__/
```

---

## Summary: What's Built vs What to Create

| Category | Exists | To Create | Effort |
|----------|--------|-----------|--------|
| **Models** | 7 models (1,260 lines) | 4 new (company, questionnaire, kyc_token, workflow) | Medium |
| **Services** | 8 services (4,855 lines) | 8 new (audit, encryption, monitoring, risk, etc.) | High |
| **API Routes** | 7 routers (3,691 lines) | 5 new (companies, questionnaires, biometrics, etc.) | Medium |
| **Workers** | 4 workers | 1 new (monitoring) | Low |
| **Frontend Pages** | 8 placeholder pages | Replace all 8 with real content | High |
| **Frontend Hooks** | 15 hooks | 4 new (settings, audit, companies, integrations) | Medium |
| **Tests** | Partial | Full coverage needed | Medium |

**Bottom line:** You have a solid foundation. ~60% of the infrastructure exists. The sprints are about:
1. **Connecting** what exists (audit model exists but isn't called)
2. **Extending** patterns (new services follow existing patterns)
3. **Replacing** placeholders (frontend pages are "Coming Soon")
