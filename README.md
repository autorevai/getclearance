# Get Clearance

AI-native KYC/AML compliance platform.

## Quick Start

### Frontend Only (React)

```bash
cd frontend
npm install
npm start
```

Open http://localhost:9000

### Full Stack (with Backend)

```bash
# 1. For Docker Compose, copy .env.local to .env (or use --env-file .env.local)
cp .env.local .env

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

# Frontend: http://localhost:9000
# API: http://localhost:8000
# API Docs: http://localhost:8000/docs
```

**Security Note**: This Docker setup follows security best practices. See [Docker Security Documentation](./docs/DOCKER_SECURITY.md) for details.

## Project Structure

```
getclearance/
├── frontend/                    # React application
│   ├── src/
│   │   ├── components/
│   │   │   ├── AppShell.jsx           # Main layout, navigation
│   │   │   ├── Dashboard.jsx          # KPI cards, AI insights
│   │   │   ├── ApplicantsList.jsx     # Applicants table
│   │   │   ├── ApplicantDetail.jsx    # Individual applicant view
│   │   │   ├── ScreeningChecks.jsx    # AML screening
│   │   │   ├── CaseManagement.jsx     # Case queue
│   │   │   ├── ApplicantAssistant.jsx # End-user chat
│   │   │   └── DesignSystem.jsx       # Shared components
│   │   ├── App.jsx
│   │   └── index.js
│   └── package.json
│
├── backend/                     # FastAPI application
│   ├── app/
│   │   ├── main.py              # App entry point
│   │   ├── config.py            # Settings from environment
│   │   ├── database.py          # Async SQLAlchemy setup
│   │   ├── dependencies.py      # Auth, tenant context
│   │   ├── api/
│   │   │   ├── router.py        # API router aggregator
│   │   │   └── v1/
│   │   │       ├── applicants.py    # KYC applicant CRUD
│   │   │       ├── documents.py     # Document upload/download (R2)
│   │   │       ├── screening.py     # AML screening (OpenSanctions)
│   │   │       ├── cases.py         # Investigation cases
│   │   │       └── ai.py            # AI risk summaries (Claude)
│   │   ├── models/              # SQLAlchemy models
│   │   │   ├── tenant.py        # Tenant, User
│   │   │   ├── applicant.py     # Applicant, ApplicantStep
│   │   │   ├── document.py      # Document
│   │   │   ├── screening.py     # ScreeningCheck, ScreeningHit
│   │   │   ├── case.py          # Case, CaseNote
│   │   │   └── audit.py         # AuditLog (chain-hashed)
│   │   ├── schemas/             # Pydantic schemas
│   │   │   └── applicant.py
│   │   └── services/            # External integrations
│   │       ├── screening.py     # OpenSanctions API
│   │       ├── storage.py       # Cloudflare R2
│   │       └── ai.py            # Claude AI
│   ├── migrations/              # Alembic migrations
│   │   ├── env.py
│   │   └── versions/
│   ├── Dockerfile
│   ├── requirements.txt
│   └── alembic.ini
│
├── docs/
│   ├── ARCHITECTURE.md          # System design
│   ├── CTO_HANDOFF.md           # Project status & next steps
│   ├── HANDOVER.md              # Overview
│   ├── DOCKER_SECURITY.md       # Security best practices
│   └── DOCKER_SECURITY_QUICK_REF.md
│
├── docker-compose.yml           # PostgreSQL, Redis, MinIO
└── README.md
```

## Tech Stack

### Frontend
- React 18
- Lucide React (icons)
- Inline CSS (no external dependencies)

### Backend
- FastAPI (async Python)
- PostgreSQL 15+ with SQLAlchemy 2.0
- Redis (caching, job queue)
- Cloudflare R2 (document storage)
- Auth0 (authentication)

### AI & Integrations
- Claude API (risk assessment, document analysis)
- OpenSanctions (AML/sanctions/PEP screening)

## Features

### Frontend (Complete)
- [x] Dashboard with KPI cards and AI insights
- [x] Applicants list with filtering, batch actions
- [x] Applicant detail with AI Snapshot tab
- [x] AML Screening checks with list version tracking
- [x] Case management queue
- [x] Applicant-facing chat assistant
- [x] Dark/light theme
- [x] Responsive design

### Backend (Complete)
- [x] FastAPI scaffold with async SQLAlchemy
- [x] PostgreSQL models with multi-tenant support
- [x] Auth0 JWT authentication
- [x] Applicants CRUD API
- [x] Documents API with R2 presigned URLs
- [x] Screening API with OpenSanctions integration
- [x] Cases API for investigations
- [x] AI endpoints for risk summaries

### TODO
- [ ] Background workers (ARQ jobs)
- [ ] Periodic re-screening
- [ ] Evidence pack export
- [ ] Railway deployment

## API Endpoints

### Applicants
- `GET /api/v1/applicants` - List applicants
- `GET /api/v1/applicants/{id}` - Get applicant detail
- `POST /api/v1/applicants` - Create applicant
- `PATCH /api/v1/applicants/{id}` - Update applicant
- `POST /api/v1/applicants/{id}/review` - Approve/reject

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

## Environment Variables

Key variables in `.env.local`:

```bash
# Database
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/getclearance

# Auth0
AUTH0_DOMAIN=your-tenant.auth0.com
AUTH0_CLIENT_ID=...
AUTH0_AUDIENCE=https://api.getclearance.com

# OpenSanctions (Screening)
OPENSANCTIONS_API_KEY=...

# Cloudflare R2 (Storage)
R2_ACCESS_KEY_ID=...
R2_SECRET_ACCESS_KEY=...
R2_ENDPOINT=https://...
R2_BUCKET=getclearance-docs

# Claude AI
ANTHROPIC_API_KEY=sk-ant-...
```

## Development

### Prerequisites
- Node.js 18+
- Python 3.11+
- Docker & Docker Compose

### Running Tests

```bash
# Frontend
cd frontend && npm test

# Backend
cd backend && pytest
```

## Deployment

### Railway (Recommended)

1. Push to GitHub
2. Connect Railway to your repo
3. Add PostgreSQL and Redis services
4. Set environment variables
5. Deploy

See `docs/CTO_HANDOFF.md` for detailed deployment guide.

## License

Proprietary - All rights reserved.

---

Built by Chris | [Get Clearance](https://getclearance.ai)
