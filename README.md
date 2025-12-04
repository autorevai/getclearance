# GetClearance

AI-native KYC/AML compliance platform - a Sumsub alternative.

**Status: Backend 100% Complete | Frontend 100% Complete | Terminal 5 Advanced Features DONE | LIVE**

## Live Deployment

| Component | URL | Status |
|-----------|-----|--------|
| Frontend | https://getclearance.vercel.app | Live |
| Backend API | https://getclearance-production.up.railway.app | Live |
| API Docs | https://getclearance-production.up.railway.app/docs | Live |

## Current Reality

| Component | Status | Details |
|-----------|--------|---------|
| Backend API | 100% Complete | All endpoints working, deployed to Railway |
| Frontend UI | 100% Complete | All 17 sprints done, beautiful Sumsub-style UI |
| Security | 100% Complete | All 6 security sprints (audit, encryption, GDPR) |
| Terminal 2 Features | 100% Complete | F1-F6 (Monitoring, KYB, Risk, Questionnaires, Address, Biometrics) |
| Terminal 5 Advanced | 100% Complete | A1-A5 (Face Match, Fraud Detection, Address, KYC Share, Doc Classification) |

**The app is fully functional.** Login, view applicants, upload documents, run AML screening, face matching, liveness detection, fraud detection - all working with real data.

## Key Features

### Identity Verification
- Document OCR with AWS Textract + MRZ passport parsing
- Face matching (ID photo vs selfie) via AWS Rekognition
- Liveness detection via quality analysis
- Document type auto-classification via Claude Vision

### AML/Sanctions Screening
- OpenSanctions integration (OFAC, EU, UN, UK lists)
- Fuzzy name matching with confidence scores
- Ongoing monitoring with daily re-screening
- PEP tier detection (Tier 1-3)

### Fraud Detection (IPQualityScore)
- VPN/Proxy/TOR detection
- Disposable email detection
- VOIP phone detection
- Device fingerprinting

### Compliance
- Tamper-evident audit logging (chain-hashed)
- GDPR compliance (SAR export, right to erasure, consent tracking)
- PII encryption at rest (Fernet AES)
- 5-7 year AML retention policies

## Quick Start

### Frontend Only (UI Preview)

```bash
cd frontend
npm install
npm start
```

Open http://localhost:9000

### Full Stack (Backend with Real Data)

```bash
# 1. Copy environment variables
cp .env.example .env.local
# Edit .env.local with your API keys

# 2. Start infrastructure
docker-compose up -d db redis

# 3. Backend setup
cd backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# 4. Run migrations
alembic upgrade head

# 5. Start API
uvicorn app.main:app --reload --port 8000

# 6. Start background workers (new terminal)
arq app.workers.config.WorkerSettings

# API: http://localhost:8000
# API Docs: http://localhost:8000/docs
```

**Note:** The app auto-provisions users on first login. No manual setup required.

## Project Structure

```
getclearance/
├── frontend/                    # React application (100% complete)
│   ├── src/
│   │   ├── components/
│   │   │   ├── AppShell.jsx           # Main layout, navigation
│   │   │   ├── Dashboard.jsx          # KPI cards (real API)
│   │   │   ├── ApplicantsList.jsx     # Applicants table (real API)
│   │   │   ├── ApplicantDetail.jsx    # Individual applicant (real API)
│   │   │   ├── DocumentUpload.jsx     # Drag & drop with magic byte validation
│   │   │   ├── ScreeningChecks.jsx    # AML screening with hit resolution
│   │   │   ├── CaseManagement.jsx     # Case queue (real API)
│   │   │   ├── ApplicantAssistant.jsx # AI chat (real Claude API)
│   │   │   ├── SearchModal.jsx        # Global search (Cmd+K)
│   │   │   ├── pages/                 # All feature pages (Settings, Analytics, etc.)
│   │   │   ├── settings/              # Settings components
│   │   │   ├── analytics/             # Analytics charts
│   │   │   ├── companies/             # KYB components
│   │   │   ├── billing/               # Stripe billing
│   │   │   └── kyc-share/             # Reusable KYC
│   │   ├── services/                  # API service layer
│   │   ├── hooks/                     # React Query hooks
│   │   └── auth/                      # Auth0 integration
│   └── package.json
│
├── backend/                     # FastAPI application (100% complete)
│   ├── app/
│   │   ├── main.py              # App entry point with rate limiting
│   │   ├── config.py            # Settings from environment
│   │   ├── database.py          # Async SQLAlchemy setup
│   │   ├── dependencies.py      # Auth, tenant context, audit
│   │   ├── logging_config.py    # Structured JSON logging with PII scrubbing
│   │   ├── api/v1/              # API endpoints
│   │   │   ├── applicants.py    # KYC applicant CRUD + GDPR endpoints
│   │   │   ├── documents.py     # Document upload/download + classification
│   │   │   ├── screening.py     # AML screening + hit resolution
│   │   │   ├── biometrics.py    # Face match + liveness (AWS Rekognition)
│   │   │   ├── device_intel.py  # Fraud detection (IPQualityScore)
│   │   │   ├── addresses.py     # Address verification (Smarty)
│   │   │   ├── companies.py     # KYB + UBO management
│   │   │   ├── monitoring.py    # Ongoing AML monitoring
│   │   │   ├── workflows.py     # Risk workflow rules
│   │   │   ├── questionnaires.py # Dynamic questionnaires
│   │   │   ├── kyc_share.py     # Reusable KYC tokens
│   │   │   ├── audit.py         # Audit log API
│   │   │   ├── analytics.py     # Analytics API
│   │   │   └── billing.py       # Stripe billing
│   │   ├── models/              # SQLAlchemy models
│   │   ├── schemas/             # Pydantic schemas
│   │   ├── services/            # External integrations
│   │   │   ├── screening.py     # OpenSanctions + fuzzy matching
│   │   │   ├── biometrics.py    # AWS Rekognition face match + liveness
│   │   │   ├── device_intel.py  # IPQualityScore fraud detection
│   │   │   ├── document_classifier.py # Claude Vision document type
│   │   │   ├── address_verification.py # Smarty + FATF countries
│   │   │   ├── risk_engine.py   # Weighted risk calculation
│   │   │   ├── monitoring.py    # Ongoing AML monitoring
│   │   │   ├── kyb_screening.py # Company + UBO screening
│   │   │   ├── audit.py         # Chain-hashed audit logging
│   │   │   ├── encryption.py    # PII encryption (Fernet AES)
│   │   │   ├── retention.py     # GDPR data retention
│   │   │   ├── storage.py       # Cloudflare R2
│   │   │   ├── ai.py            # Claude AI
│   │   │   └── ocr.py           # AWS Textract OCR
│   │   └── workers/             # Background job processing (ARQ)
│   ├── tests/                   # Test suite (244+ tests)
│   ├── migrations/              # Alembic migrations
│   └── requirements.txt
│
├── docs/
│   ├── DEPLOYMENT_GUIDE.md
│   ├── ARCHITECTURE.md
│   └── implementation-guide/
│       ├── MASTER_SUMSUB_REVERSE_ENGINEERING.md  # Complete sprint tracking
│       ├── 02_FOLDER_STRUCTURE_COMPLETE.md       # Current file structure
│       ├── 14_BACKEND_SECURITY_SPRINT_PROMPTS.md # Security sprints
│       ├── 18_TERMINAL2_BACKEND_FEATURES_PROMPTS.md # Backend features
│       └── 20_TERMINAL5_ADVANCED_FEATURES_PROMPTS.md # Advanced integrations
│
└── README.md
```

## Tech Stack

### Frontend
- React 18
- Auth0 React SDK (authentication)
- React Query / TanStack Query (server state)
- Lucide React (icons)
- Inline CSS (no external dependencies)

### Backend
- FastAPI (async Python)
- PostgreSQL 15+ with SQLAlchemy 2.0
- Redis (caching, job queue via ARQ)
- Cloudflare R2 (document storage)
- Auth0 (authentication)

### AI & Integrations
- Claude API (risk assessment, document analysis, document classification)
- OpenSanctions (AML/sanctions/PEP screening)
- AWS Textract (OCR document processing)
- AWS Rekognition (face matching, liveness detection)
- IPQualityScore (VPN, email, phone, device fraud detection)
- Smarty (US address verification)
- Stripe (billing)

## API Endpoints

### Biometrics (Terminal 5 - A1)
- `POST /api/v1/biometrics/compare` - Compare two faces
- `POST /api/v1/biometrics/liveness` - Check liveness
- `POST /api/v1/biometrics/detect` - Detect faces
- `POST /api/v1/biometrics/verify/{id}` - Full applicant verification
- `GET /api/v1/biometrics/status` - Service status

### Fraud Detection (Terminal 5 - A2)
- `POST /api/v1/device-intel/ip` - Check IP (VPN, proxy, TOR)
- `POST /api/v1/device-intel/email` - Validate email
- `POST /api/v1/device-intel/phone` - Validate phone
- `POST /api/v1/device-intel/check-all` - Combined check
- `GET /api/v1/device-intel/status` - Service status

### Address Verification (Terminal 5 - A3)
- `POST /api/v1/addresses/verify` - Verify address
- `POST /api/v1/addresses/applicants/{id}/verify` - Verify applicant address
- `GET /api/v1/addresses/countries` - Get country risk levels

### Document Classification (Terminal 5 - A5)
- `POST /api/v1/documents/{id}/classify` - Classify existing document
- `POST /api/v1/documents/classify` - Classify uploaded image

### Screening
- `POST /api/v1/screening/check` - Run AML screening
- `GET /api/v1/screening/checks` - List checks
- `PATCH /api/v1/screening/hits/{id}` - Resolve hit
- `GET /api/v1/screening/hits/{id}/suggestion` - AI resolution suggestion
- `GET /api/v1/screening/lists` - Connected list sources

### Monitoring
- `POST /api/v1/monitoring/applicants/{id}/enable` - Enable monitoring
- `GET /api/v1/monitoring/alerts` - List alerts
- `POST /api/v1/monitoring/alerts/{id}/resolve` - Resolve alert
- `GET /api/v1/monitoring/stats` - Monitoring dashboard stats

### Applicants
- `GET /api/v1/applicants` - List applicants
- `GET /api/v1/applicants/{id}` - Get applicant detail
- `POST /api/v1/applicants` - Create applicant
- `POST /api/v1/applicants/{id}/review` - Approve/reject
- `GET /api/v1/applicants/{id}/export` - GDPR SAR export
- `DELETE /api/v1/applicants/{id}/gdpr-delete` - Right to erasure

### Companies (KYB)
- `POST /api/v1/companies` - Create company
- `GET /api/v1/companies` - List companies
- `POST /api/v1/companies/{id}/beneficial-owners` - Add UBO
- `POST /api/v1/companies/{id}/screen` - Screen company + UBOs

## Sprint Tracking

### Backend Security Sprints (ALL COMPLETE)
| Sprint | Focus | Status |
|--------|-------|--------|
| B1 | Audit Logging (chain-hashed) | Complete |
| B2 | Rate Limiting & Security Headers | Complete |
| B3 | PII Encryption (Fernet AES) | Complete |
| B4 | Missing Endpoints Fixed | Complete |
| B5 | GDPR Compliance | Complete |
| B6 | Monitoring & Alerting (Sentry) | Complete |

### Terminal 2: Backend Features (ALL COMPLETE)
| Sprint | Feature | Status |
|--------|---------|--------|
| F1 | Ongoing AML Monitoring | Complete |
| F2 | KYB/Companies Module | Complete |
| F3 | Risk Workflows | Complete |
| F4 | Questionnaires | Complete |
| F5 | Address Verification | Complete |
| F6 | Liveness Detection | Complete |

### Terminal 5: Advanced Features (A1-A5 COMPLETE)
| Sprint | Feature | API | Status |
|--------|---------|-----|--------|
| A1 | Face Match + Liveness | AWS Rekognition | Complete |
| A2 | Fraud Detection | IPQualityScore | Complete |
| A3 | Address Verification | Smarty | Complete |
| A4 | Reusable KYC Tokens | Internal | Complete |
| A5 | Document Classification | Claude Vision | Complete |
| A6 | Video Identification | Twilio Video | TODO (optional) |

### Frontend Sprints (ALL 17 COMPLETE)
| Sprint | Focus | Status |
|--------|-------|--------|
| 1-9 | Core UI + API Integration | Complete |
| 10 | Settings Page | Complete |
| 11 | Audit Log | Complete |
| 12 | Analytics | Complete |
| 13 | Integrations | Complete |
| 14 | Companies/KYB | Complete |
| 15 | Device Intelligence | Complete |
| 16 | Billing & Usage | Complete |
| 17 | Reusable KYC | Complete |

## Environment Variables

See `.env.example` for all variables. Key ones:

```bash
# Core
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/getclearance
REDIS_URL=redis://localhost:6379

# Auth0
AUTH0_DOMAIN=your-tenant.auth0.com
AUTH0_CLIENT_ID=...
AUTH0_AUDIENCE=https://api.getclearance.com

# Security
ENCRYPTION_KEY=<generate-with-openssl-rand-hex-32>

# AI & Screening
ANTHROPIC_API_KEY=sk-ant-...
OPENSANCTIONS_API_KEY=...

# AWS (OCR + Rekognition)
AWS_ACCESS_KEY_ID=...
AWS_SECRET_ACCESS_KEY=...
AWS_REGION=us-east-1

# IPQualityScore (Fraud Detection)
IPQS_API_KEY=...

# Smarty (Address Verification)
SMARTY_AUTH_ID=...
SMARTY_AUTH_TOKEN=...

# Storage
R2_ENDPOINT=https://...
R2_ACCESS_KEY_ID=...
R2_SECRET_ACCESS_KEY=...
R2_BUCKET=getclearance-docs
```

## API Cost Estimates

| Service | Cost | Monthly @ 10K verifications |
|---------|------|------------------------------|
| AWS Rekognition | $0.001/image | ~$20 |
| IPQualityScore | $0.0003/query | ~$10 |
| Claude AI | $0.01/request | ~$100 |
| Smarty | Free-$0.01/lookup | ~$0-100 |
| OpenSanctions | Free (open source) | $0 |
| **Total** | | **~$150-250/month** |

## Running Tests

```bash
cd backend
pytest

# With coverage
pytest --cov=app tests/
```

## Deployment

### Backend (Railway)
Already deployed. Push to main branch triggers auto-deploy.

### Frontend (Vercel)
Already deployed at https://getclearance.vercel.app

## Documentation

- [Deployment Guide](./docs/DEPLOYMENT_GUIDE.md)
- [Architecture](./docs/ARCHITECTURE.md)
- [Master Sprint Tracking](./docs/implementation-guide/MASTER_SUMSUB_REVERSE_ENGINEERING.md)
- [Terminal 5 Advanced Features](./docs/implementation-guide/20_TERMINAL5_ADVANCED_FEATURES_PROMPTS.md)

## Project Status

```
Backend Core:         100% Complete
Frontend UI:          100% Complete (17 sprints)
Security:             100% Complete (6 sprints)
Terminal 2 Features:  100% Complete (F1-F6)
Terminal 5 Advanced:  100% Complete (A1-A5)
```

**Platform is production-ready for crypto exchange KYC onboarding.**

---

Built by Chris | [GetClearance](https://getclearance.ai)
