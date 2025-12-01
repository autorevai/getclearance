# GetClearance

AI-native KYC/AML compliance platform - a Sumsub alternative.

**Status: Backend 100% Complete | Frontend Sprint 1-2 Complete**

## Current Reality

| Component | Status | Details |
|-----------|--------|---------|
| Backend API | 100% Complete | All endpoints working, deployed to Railway |
| Frontend UI | UI Complete | Beautiful Sumsub-style components |
| Frontend Auth | ✅ Sprint 1 Complete | Auth0 login/logout, protected routes |
| Frontend API Layer | ✅ Sprint 2 Complete | Services + React Query hooks ready |
| Component Integration | In Progress | Components need to use the API hooks |

**The foundation is complete.** Auth0 authentication and API service layer are working. Components still use mock data but the hooks are ready. See [Frontend Integration Guide](./docs/FRONTEND_AUDIT_AND_INTEGRATION_GUIDE.md) for details.

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

**Note:** The frontend has authentication working. Components still use mock data until Sprint 3+ integration.

## Project Structure

```
getclearance/
├── frontend/                    # React application (UI complete, needs API integration)
│   ├── src/
│   │   ├── components/
│   │   │   ├── AppShell.jsx           # Main layout, navigation
│   │   │   ├── Dashboard.jsx          # KPI cards (mock data)
│   │   │   ├── ApplicantsList.jsx     # Applicants table (mock data)
│   │   │   ├── ApplicantDetail.jsx    # Individual applicant (mock data)
│   │   │   ├── ScreeningChecks.jsx    # AML screening (mock data)
│   │   │   ├── CaseManagement.jsx     # Case queue (mock data)
│   │   │   ├── ApplicantAssistant.jsx # End-user chat (fake responses)
│   │   │   └── DesignSystem.jsx       # Shared components
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
│   │   │   ├── documents.py     # Document upload/download (R2)
│   │   │   ├── screening.py     # AML screening (OpenSanctions)
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

### Frontend (Sprint 1-2 Complete, Components Need Integration)
- [x] Dashboard with KPI cards
- [x] Applicants list with filtering
- [x] Applicant detail with tabs
- [x] AML Screening interface
- [x] Case management queue
- [x] AI assistant chat
- [x] Dark/light theme
- [x] **Authentication (Auth0 login/logout working)**
- [x] **API service layer (all endpoints covered)**
- [x] **React Query hooks (ready to use)**
- [ ] **Component integration (still using mock data)**
- [ ] **Real-time updates (no WebSocket yet)**

## Frontend Work Remaining

Sprints 1-2 are complete. The remaining work is connecting components to the API:

| Sprint | Focus | Status |
|--------|-------|--------|
| 1 | Authentication (Auth0) | ✅ Complete |
| 2 | API Service Layer | ✅ Complete |
| 3 | Applicants Module | 🔲 Pending |
| 4 | Document Upload | 🔲 Pending |
| 5 | Screening Module | 🔲 Pending |
| 6 | Cases & AI | 🔲 Pending |
| 7 | Polish & Real-time | 🔲 Pending |

**Remaining: ~18-25 days (Sprints 3-7)**

See [Frontend Sprint Prompts](./docs/implementation-guide/09_FRONTEND_SPRINT_PROMPTS.md) for copy-paste ready prompts for each sprint.

## API Endpoints (All Working)

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

### Frontend Deployment

Once frontend integration is complete, deploy to:
- Vercel (recommended)
- Netlify
- Cloudflare Pages

## Documentation

- [Frontend Audit & Integration Guide](./docs/FRONTEND_AUDIT_AND_INTEGRATION_GUIDE.md) - Gap analysis
- [Frontend Sprint Prompts](./docs/implementation-guide/09_FRONTEND_SPRINT_PROMPTS.md) - Build prompts
- [Deployment Guide](./docs/DEPLOYMENT_GUIDE.md) - Railway deployment
- [Architecture](./docs/ARCHITECTURE.md) - System design
- [Engineering Context](./docs/ENGINEERING_CONTEXT.md) - Technical details

## Project Status Summary

```
Backend:  ████████████████████ 100%  - Production ready, deployed
Frontend: ██████████████░░░░░░  72%  - Auth + API layer done, component integration needed
Overall:  ██████████████████░░  88%  - Sprints 3-7 remaining
```

**Next Step:** Start Frontend Sprint 3 (Applicants Module Integration)

---

Built by Chris | [GetClearance](https://getclearance.ai)
