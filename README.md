# GetClearance

AI-native KYC/AML compliance platform - a Sumsub alternative.

**Status: Backend 100% Complete | Frontend 100% Complete (All Sprints 1-8 Done) | LIVE 🚀**

## Live Deployment

| Component | URL | Status |
|-----------|-----|--------|
| Frontend | https://getclearance.vercel.app | ✅ Live |
| Backend API | https://getclearance-production.up.railway.app | ✅ Live |
| API Docs | https://getclearance-production.up.railway.app/docs | ✅ Live |

## Current Reality

| Component | Status | Details |
|-----------|--------|---------|
| Backend API | 100% Complete | All endpoints working, deployed to Railway |
| Frontend UI | ✅ Complete | Beautiful Sumsub-style components |
| Frontend Auth | ✅ Sprint 1 Complete | Auth0 login/logout, protected routes |
| Frontend API Layer | ✅ Sprint 2 Complete | Services + React Query hooks ready |
| Applicants Module | ✅ Sprint 3 Complete | Real API integration, no mock data |
| Document Upload | ✅ Sprint 4 Complete | Multi-file upload, preview, magic byte validation |
| Screening Module | ✅ Sprint 5 Complete | Run checks, resolve hits, AI suggestions |
| Cases & AI Module | ✅ Sprint 6 Complete | Real API, toast notifications |
| Polish & Real-time | ✅ Sprint 7 Complete | WebSocket, permissions, loading states, 404 |
| Dashboard Integration | ✅ Sprint 8 Complete | Real KPIs, screening summary, activity feed |

**The app is fully functional.** Login, view applicants, upload documents, run AML screening, approve/reject, search/filter - all working with real data.

## Quick Start

### Frontend Only (UI Preview - Mock Data)

```bash
cd frontend
npm install
npm start
```

Open http://localhost:9000 - You'll see the UI with fake data.

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
├── frontend/                    # React application (100% complete, all API integration done)
│   ├── src/
│   │   ├── components/
│   │   │   ├── AppShell.jsx           # Main layout, navigation
│   │   │   ├── Dashboard.jsx          # KPI cards (real API)
│   │   │   ├── ApplicantsList.jsx     # Applicants table (real API)
│   │   │   ├── ApplicantDetail.jsx    # Individual applicant (real API)
│   │   │   ├── CreateApplicantModal.jsx # Create new applicant
│   │   │   ├── DocumentUpload.jsx     # Drag & drop upload with progress
│   │   │   ├── DocumentList.jsx       # Document grid with status
│   │   │   ├── DocumentPreview.jsx    # Preview modal with zoom/tabs
│   │   │   ├── ScreeningChecks.jsx    # AML screening
│   │   │   ├── CaseManagement.jsx     # Case queue (real API)
│   │   │   ├── ApplicantAssistant.jsx # AI chat (real API)
│   │   │   ├── ErrorBoundary.jsx      # Error handling
│   │   │   └── shared/                # Toast, ConfirmDialog, LoadingSpinner, NotFound
│   │   ├── App.jsx
│   │   └── index.js
│   └── package.json
│
├── backend/                     # FastAPI application (100% complete)
│   ├── app/
│   │   ├── main.py              # App entry point
│   │   ├── config.py            # Settings from environment
│   │   ├── database.py          # Async SQLAlchemy setup
│   │   ├── dependencies.py      # Auth, tenant context
│   │   ├── api/v1/              # API endpoints
│   │   │   ├── applicants.py    # KYC applicant CRUD
│   │   │   ├── dashboard.py     # Dashboard KPIs & activity (NEW)
│   │   │   ├── documents.py     # Document upload/download (R2)
│   │   │   ├── screening.py     # AML screening (OpenSanctions) + list sources
│   │   │   ├── cases.py         # Investigation cases
│   │   │   └── ai.py            # AI risk summaries (Claude)
│   │   ├── models/              # SQLAlchemy models
│   │   ├── schemas/             # Pydantic schemas
│   │   ├── services/            # External integrations
│   │   │   ├── screening.py     # OpenSanctions + fuzzy matching
│   │   │   ├── storage.py       # Cloudflare R2
│   │   │   ├── ai.py            # Claude AI
│   │   │   ├── ocr.py           # AWS Textract OCR
│   │   │   ├── mrz_parser.py    # Passport MRZ validation
│   │   │   ├── webhook.py       # Webhook delivery with retry
│   │   │   ├── evidence.py      # PDF evidence pack generation
│   │   │   └── timeline.py      # Event aggregation
│   │   └── workers/             # Background job processing (ARQ)
│   ├── tests/                   # Test suite
│   ├── scripts/                 # Utility scripts
│   ├── migrations/              # Alembic migrations
│   ├── Dockerfile
│   └── requirements.txt
│
├── docs/
│   ├── FRONTEND_AUDIT_AND_INTEGRATION_GUIDE.md  # Frontend gap analysis
│   ├── DEPLOYMENT_GUIDE.md      # Railway deployment
│   ├── ARCHITECTURE.md          # System design
│   └── implementation-guide/
│       ├── 08_MASTER_CHAT_PROMPTS.md     # Backend build prompts
│       └── 09_FRONTEND_SPRINT_PROMPTS.md # Frontend integration prompts
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

### Backend (Complete)
- FastAPI (async Python)
- PostgreSQL 15+ with SQLAlchemy 2.0
- Redis (caching, job queue via ARQ)
- Cloudflare R2 (document storage)
- Auth0 (authentication)

### AI & Integrations (Complete)
- Claude API (risk assessment, document analysis)
- OpenSanctions (AML/sanctions/PEP screening)
- AWS Textract (OCR document processing)

## Features

### Backend (100% Complete)
- [x] FastAPI with async SQLAlchemy
- [x] PostgreSQL with multi-tenant support (RLS)
- [x] Auth0 JWT authentication with RBAC
- [x] Applicants CRUD API with review workflow
- [x] Documents API with R2 presigned URLs
- [x] Screening API with OpenSanctions integration
- [x] Cases API for investigations
- [x] AI endpoints for risk summaries
- [x] Background workers (ARQ)
- [x] OCR with MRZ passport validation
- [x] Webhook delivery with retry logic
- [x] Evidence pack PDF export
- [x] Comprehensive test suite
- [x] Deployed to Railway

### Frontend (100% Complete - All Sprints Done)
- [x] Dashboard with KPI cards
- [x] Applicants list with filtering (real API)
- [x] Applicant detail with tabs (real API)
- [x] Create applicant modal
- [x] AML Screening interface (real API)
- [x] Case management queue (real API)
- [x] AI assistant chat (real API)
- [x] Dark/light theme
- [x] **Authentication (Auth0 login/logout)**
- [x] **API service layer (all endpoints)**
- [x] **React Query hooks with optimistic updates**
- [x] **Toast notifications**
- [x] **Confirmation dialogs**
- [x] **Keyboard shortcuts (Cmd+K, A/R for approve/reject)**
- [x] **Batch approve/reject**
- [x] **URL state sync (shareable filter URLs)**
- [x] **Error boundaries**
- [x] **Document Upload UI (Sprint 4)**
  - [x] Drag & drop with visual feedback
  - [x] Multi-file upload for front/back (driver's license, ID card)
  - [x] Image thumbnail preview before upload
  - [x] File magic byte validation for security
  - [x] Upload progress with stages (requesting, uploading, confirming, analyzing)
  - [x] Document list with status badges and OCR confidence
  - [x] Preview modal with zoom, rotation, tabs (Preview, Extracted Data, AI Analysis)
  - [x] Verification checks display (MRZ, OCR quality, fraud detection)
- [x] **Screening Module UI (Sprint 5)**
  - [x] Real API integration (no mock data)
  - [x] Run new screening checks with form
  - [x] Filter tabs connected to API (all, hits, pending)
  - [x] Hit resolution with AI suggestions
  - [x] Loading skeletons and error states
  - [x] Connected list sources from API
- [x] **Cases & AI (Sprint 6)**
  - [x] Case management with real API
  - [x] AI assistant with real Claude API
  - [x] Toast notifications for all mutations
- [x] **Polish & Real-time (Sprint 7)**
  - [x] WebSocket real-time updates (auto-reconnect, query invalidation)
  - [x] Permission-based UI controls (usePermissions hook, PermissionGate)
  - [x] Loading spinners (multiple sizes and variants)
  - [x] 404 Not Found page with suggestions
  - [x] Consistent toast.success/error/warning patterns
- [x] **Dashboard Integration (Sprint 8)**
  - [x] Real KPI stats from API (today's applicants, approved, rejected, pending)
  - [x] Real screening summary from API (sanctions, PEP, adverse media counts)
  - [x] Real activity feed from API with relative timestamps
  - [x] Loading skeletons for all dashboard widgets
  - [x] Error states with retry buttons
  - [x] Auto-refresh every 60 seconds
  - [x] Manual refresh button

## Frontend Sprints - All Complete

| Sprint | Focus | Status |
|--------|-------|--------|
| 0 | Backend Dashboard/Screening Endpoints | ✅ Complete |
| 1 | Authentication (Auth0) | ✅ Complete |
| 2 | API Service Layer | ✅ Complete |
| 3 | Applicants Module | ✅ Complete |
| 3+ | Polish & UX | ✅ Complete |
| 4 | Document Upload | ✅ Complete |
| 5 | Screening Module | ✅ Complete |
| 6 | Cases & AI | ✅ Complete |
| 7 | Polish & Real-time | ✅ Complete |
| 8 | Dashboard Integration | ✅ Complete |

**All frontend sprints complete! No remaining frontend work.**

## API Endpoints (All Working)

### Dashboard (NEW - Sprint 0)
- `GET /api/v1/dashboard/stats` - KPI statistics (today's applicants, approved, rejected, pending)
- `GET /api/v1/dashboard/screening-summary` - Screening hit counts by type
- `GET /api/v1/dashboard/activity` - Recent activity feed

### Applicants
- `GET /api/v1/applicants` - List applicants
- `GET /api/v1/applicants/{id}` - Get applicant detail
- `POST /api/v1/applicants` - Create applicant
- `PATCH /api/v1/applicants/{id}` - Update applicant
- `POST /api/v1/applicants/{id}/review` - Approve/reject
- `GET /api/v1/applicants/{id}/evidence` - Download evidence PDF

### Documents
- `POST /api/v1/documents/upload-url` - Get presigned upload URL
- `POST /api/v1/documents/{id}/confirm` - Confirm upload
- `GET /api/v1/documents/{id}/download` - Get download URL
- `POST /api/v1/documents/{id}/analyze` - AI document analysis

### Screening
- `POST /api/v1/screening/check` - Run AML screening
- `GET /api/v1/screening/checks` - List checks
- `PATCH /api/v1/screening/hits/{id}` - Resolve hit
- `GET /api/v1/screening/hits/{id}/suggestion` - AI resolution suggestion
- `GET /api/v1/screening/lists` - Connected list sources (OFAC, EU, UN, UK, OpenSanctions)

### Cases
- `GET /api/v1/cases` - List cases
- `POST /api/v1/cases` - Create case
- `POST /api/v1/cases/{id}/resolve` - Resolve case
- `POST /api/v1/cases/{id}/notes` - Add note

### AI
- `GET /api/v1/ai/applicants/{id}/risk-summary` - Generate risk summary
- `POST /api/v1/ai/assistant` - Applicant-facing assistant
- `POST /api/v1/ai/batch-analyze` - Batch risk analysis

### Health
- `GET /health` - Basic health check
- `GET /health/ready` - Readiness check (DB + Redis)

## Environment Variables

See `.env.example` for development or `.env.production.example` for production.

Key variables:

```bash
# Core
ENVIRONMENT=development
SECRET_KEY=<generate-with-openssl-rand-hex-32>

# Database
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/getclearance

# Redis
REDIS_URL=redis://localhost:6379

# Auth0
AUTH0_DOMAIN=your-tenant.auth0.com
AUTH0_CLIENT_ID=...
AUTH0_CLIENT_SECRET=...
AUTH0_AUDIENCE=https://api.getclearance.com

# Cloudflare R2 (Storage)
R2_ENDPOINT=https://...
R2_ACCESS_KEY_ID=...
R2_SECRET_ACCESS_KEY=...
R2_BUCKET=getclearance-docs

# Claude AI
ANTHROPIC_API_KEY=sk-ant-...

# OpenSanctions (Screening)
OPENSANCTIONS_API_KEY=...

# AWS (OCR)
AWS_ACCESS_KEY_ID=...
AWS_SECRET_ACCESS_KEY=...
AWS_REGION=us-east-1
```

## Development

### Prerequisites
- Node.js 18+
- Python 3.11+
- Docker & Docker Compose

### Running Tests

```bash
# Backend tests
cd backend
pytest

# With coverage
pytest --cov=app tests/
```

### Running Workers

```bash
cd backend
arq app.workers.config.WorkerSettings
```

### Utility Scripts

```bash
cd backend

# Create a new tenant
python -m scripts.create_tenant --name "Acme Corp" --admin-email "admin@acme.com"

# Seed test data
python -m scripts.seed_data --create-tenant

# Check system health
python -m scripts.check_health
```

## Deployment

### Railway (Backend - Already Deployed)

The backend is deployed on Railway. To redeploy:

1. Push to GitHub
2. Railway auto-deploys from main branch
3. Migrations run automatically via `railway.json`

See [docs/DEPLOYMENT_GUIDE.md](./docs/DEPLOYMENT_GUIDE.md) for detailed instructions.

### Frontend (Vercel - Already Deployed)

The frontend is deployed on Vercel at https://getclearance.vercel.app

Environment variables in Vercel:
```
REACT_APP_API_BASE_URL=https://getclearance-production.up.railway.app/api/v1
REACT_APP_AUTH0_DOMAIN=dev-8z4blmy3c8wvkp4k.us.auth0.com
REACT_APP_AUTH0_CLIENT_ID=W5uDmvvRYDmw9Sm4avfEzoOxo26XF8rR
REACT_APP_AUTH0_AUDIENCE=https://api.getclearance.vercel.app
```

## Documentation

- [Frontend Audit & Integration Guide](./docs/FRONTEND_AUDIT_AND_INTEGRATION_GUIDE.md) - Gap analysis
- [Frontend Sprint Prompts](./docs/implementation-guide/09_FRONTEND_SPRINT_PROMPTS.md) - Build prompts
- [Deployment Guide](./docs/DEPLOYMENT_GUIDE.md) - Railway deployment
- [Architecture](./docs/ARCHITECTURE.md) - System design
- [Engineering Context](./docs/ENGINEERING_CONTEXT.md) - Technical details

## Project Status Summary

```
Backend:  ████████████████████ 100%  - Production ready, deployed to Railway
Frontend: ████████████████████ 100%  - All sprints complete (1-8)
Overall:  ████████████████████ 100%  - Full platform complete and deployed
```

**All development complete!** The platform is fully functional with real data integration across all components.

---

Built by Chris | [GetClearance](https://getclearance.ai)
