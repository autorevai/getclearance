# Get Clearance - CTO/Dev Team Handoff

**Date:** November 30, 2025  
**Status:** Phase 1 Backend Complete - Ready for Team Onboarding  
**Target Launch:** January 2026

---

## Executive Summary

Get Clearance is an AI-native KYC/AML compliance platform. This document provides everything needed to onboard a development team and continue building toward the January 2026 launch.

**What's Done:**
- ✅ Complete React frontend (deployed to Vercel)
- ✅ FastAPI backend scaffold with auth, database, and core APIs
- ✅ Database schema with migrations
- ✅ Docker development environment
- ✅ Architecture documentation

**What's Next:**
- OpenSanctions integration (screening)
- Cloudflare R2 integration (document storage)
- Claude AI integration (risk summaries)
- Railway deployment

---

## Quick Start for New Developers

```bash
# Clone the repository
git clone https://github.com/autorevai/getclearance.git
cd getclearance

# Start infrastructure (Postgres, Redis, MinIO)
docker-compose up -d db redis minio

# Backend setup
cd backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
# Edit .env with your values

# Run migrations
alembic upgrade head

# Start API (port 8000)
uvicorn app.main:app --reload --port 8000

# Frontend setup (separate terminal)
cd ../frontend
npm install
npm start  # Runs on port 9000
```

**Verify Setup:**
- API Health: http://localhost:8000/health
- API Docs: http://localhost:8000/docs
- Frontend: http://localhost:9000

---

## Repository Structure

```
getclearance/
├── frontend/                 # React app (COMPLETE)
│   ├── src/
│   │   ├── components/       # All UI components
│   │   │   ├── AppShell.jsx
│   │   │   ├── Dashboard.jsx
│   │   │   ├── ApplicantsList.jsx
│   │   │   ├── ApplicantDetail.jsx
│   │   │   ├── ScreeningChecks.jsx
│   │   │   ├── CaseManagement.jsx
│   │   │   └── DesignSystem.jsx
│   │   └── App.jsx
│   └── package.json
│
├── backend/                  # FastAPI app (SCAFFOLD COMPLETE)
│   ├── app/
│   │   ├── main.py           # Entry point, CORS, health checks
│   │   ├── config.py         # Settings from environment
│   │   ├── database.py       # Async SQLAlchemy
│   │   ├── dependencies.py   # Auth, tenant context
│   │   ├── api/v1/           # API routes
│   │   │   ├── applicants.py
│   │   │   ├── documents.py
│   │   │   ├── screening.py
│   │   │   └── cases.py
│   │   ├── models/           # SQLAlchemy models
│   │   └── schemas/          # Pydantic schemas
│   ├── migrations/           # Alembic migrations
│   ├── requirements.txt
│   └── Dockerfile
│
├── docs/
│   ├── ARCHITECTURE.md       # Full system design
│   └── HANDOVER.md
│
└── docker-compose.yml
```

---

## Architecture Overview

### Tech Stack

| Layer | Technology | Status |
|-------|------------|--------|
| Frontend | React 18 + Lucide | ✅ Complete |
| Frontend Hosting | Vercel | ✅ Deployed |
| API | FastAPI | ✅ Scaffold Complete |
| Database | PostgreSQL 15 | ✅ Schema Complete |
| Cache/Queue | Redis + ARQ | ⏳ Redis ready, ARQ pending |
| Object Storage | Cloudflare R2 | ⏳ Integration pending |
| Auth | Auth0 | ✅ Code ready, config pending |
| Screening | OpenSanctions | ⏳ Integration pending |
| AI | Claude API | ⏳ Integration pending |
| Backend Hosting | Railway | ⏳ Deployment pending |

### Multi-Tenancy Model

Every table includes `tenant_id`. Row-Level Security (RLS) is ready to enable in PostgreSQL. The `dependencies.py` file handles tenant context extraction from Auth0 JWT claims.

```python
# How tenant isolation works
@router.get("/applicants")
async def list_applicants(
    db: TenantDB,      # Auto-filtered to current tenant
    user: AuthenticatedUser,  # Contains tenant_id, role, permissions
):
    # Queries automatically scoped to user's tenant
    ...
```

---

## API Endpoints

### Applicants (`/api/v1/applicants`)
| Method | Endpoint | Description | Status |
|--------|----------|-------------|--------|
| GET | `/` | List with filters | ✅ |
| GET | `/{id}` | Full detail | ✅ |
| POST | `/` | Create | ✅ |
| PATCH | `/{id}` | Update | ✅ |
| POST | `/{id}/review` | Approve/Reject | ✅ |
| POST | `/{id}/steps/{step}/complete` | Complete step | ✅ |

### Documents (`/api/v1/documents`)
| Method | Endpoint | Description | Status |
|--------|----------|-------------|--------|
| POST | `/upload-url` | Get presigned URL | ⏳ Mock |
| POST | `/{id}/confirm` | Confirm upload | ⏳ Mock |
| POST | `/upload` | Direct upload | ⏳ Mock |
| GET | `/{id}` | Get metadata | ✅ |
| GET | `/{id}/download` | Get download URL | ⏳ Mock |

### Screening (`/api/v1/screening`)
| Method | Endpoint | Description | Status |
|--------|----------|-------------|--------|
| POST | `/check` | Run check | ⏳ Mock |
| GET | `/checks` | List checks | ✅ |
| GET | `/checks/{id}` | Check detail | ✅ |
| PATCH | `/hits/{id}` | Resolve hit | ✅ |

### Cases (`/api/v1/cases`)
| Method | Endpoint | Description | Status |
|--------|----------|-------------|--------|
| GET | `/` | List with filters | ✅ |
| GET | `/{id}` | Case detail | ✅ |
| POST | `/` | Create | ✅ |
| PATCH | `/{id}` | Update | ✅ |
| POST | `/{id}/resolve` | Resolve | ✅ |
| POST | `/{id}/notes` | Add note | ✅ |

---

## Database Schema

Core tables with relationships:

```
tenants ─┬─► users
         ├─► applicants ─┬─► applicant_steps
         │               ├─► documents
         │               ├─► screening_checks ─► screening_hits
         │               └─► cases ─┬─► case_notes
         │                          └─► case_attachments
         └─► audit_log (immutable, chain-hashed)
```

Full schema in `docs/ARCHITECTURE.md`.

---

## Remaining Work (Priority Order)

### Week 1: External Integrations

**1. Auth0 Configuration** (1 day)
- Create Auth0 tenant
- Configure custom claims for `tenant_id` and `role`
- Update `.env` with credentials
- Test JWT validation

**2. Cloudflare R2 Integration** (2 days)
```python
# Create: backend/app/services/storage.py
class StorageService:
    async def create_presigned_upload(self, key: str) -> str: ...
    async def create_presigned_download(self, key: str) -> str: ...
    async def delete(self, key: str) -> None: ...
```

**3. OpenSanctions Integration** (3 days)
```python
# Create: backend/app/services/screening.py
class ScreeningService:
    async def check_individual(self, name: str, dob: date, country: str) -> list[Hit]: ...
    async def check_company(self, name: str, jurisdiction: str) -> list[Hit]: ...
```

### Week 2: AI & Background Jobs

**4. Claude AI Integration** (2 days)
```python
# Create: backend/app/services/ai.py
class AIService:
    async def generate_risk_summary(self, applicant_id: UUID) -> str: ...
    async def analyze_document(self, document_id: UUID) -> dict: ...
    async def suggest_hit_resolution(self, hit_id: UUID) -> dict: ...
```

**5. Background Workers** (2 days)
```python
# Create: backend/app/workers/screening.py
# Using ARQ for async Redis queue
async def run_screening_check(ctx, applicant_id: str): ...
async def process_document(ctx, document_id: str): ...
```

**6. Connect Frontend** (2 days)
- Add API service layer to React
- Replace mock data with real API calls
- Handle auth token injection

### Week 3: Deploy & Polish

**7. Railway Deployment** (1 day)
- Configure PostgreSQL
- Configure Redis
- Set environment variables
- Connect custom domain

**8. Testing** (2 days)
- Pytest fixtures for models
- API integration tests
- Auth flow tests

**9. First Customer Onboarding** (2 days)
- Create production tenant
- Configure workflow
- Verify end-to-end flow

---

## Environment Variables

Required for production:

```bash
# Core
DATABASE_URL=postgresql+asyncpg://...
REDIS_URL=redis://...

# Auth
AUTH0_DOMAIN=your-tenant.auth0.com
AUTH0_CLIENT_ID=...
AUTH0_AUDIENCE=https://api.getclearance.com

# Storage
R2_ACCESS_KEY_ID=...
R2_SECRET_ACCESS_KEY=...
R2_BUCKET=getclearance-docs
R2_ENDPOINT=https://...

# AI
ANTHROPIC_API_KEY=sk-ant-...

# Screening
OPENSANCTIONS_API_KEY=...
```

---

## Development Guidelines

### Code Style
- Python: Black + Ruff + MyPy
- Run before committing: `black app/ && ruff check app/ --fix`

### Git Workflow
- `main` - production
- `develop` - integration
- Feature branches: `feature/description`

### Database Migrations
```bash
# Create migration
alembic revision --autogenerate -m "Add new table"

# Apply
alembic upgrade head

# Rollback
alembic downgrade -1
```

### Testing
```bash
pytest tests/ -v
pytest tests/ --cov=app --cov-report=html
```

---

## Key Design Decisions

1. **AI-First**: Every screen surfaces AI insights. Claude integration planned for risk summaries and document analysis.

2. **Audit Everything**: Immutable audit log with chain hashing for tamper evidence.

3. **Citations Required**: AI never makes unsupported claims. All summaries include source citations.

4. **Multi-Tenant from Day 1**: Row-level security, tenant isolation built into every query.

5. **Async Everything**: FastAPI async, asyncpg, async Redis for high throughput.

---

## Contacts & Resources

- **Repository**: https://github.com/autorevai/getclearance
- **Frontend (Live)**: https://getclearance.vercel.app
- **Architecture Docs**: `docs/ARCHITECTURE.md`
- **API Docs (Local)**: http://localhost:8000/docs

---

## Estimated Timeline to Launch

| Week | Focus | Deliverable |
|------|-------|-------------|
| 1 | External Integrations | Auth0 + R2 + OpenSanctions working |
| 2 | AI & Workers | Claude summaries, background jobs |
| 3 | Connect & Deploy | Frontend connected, Railway live |
| 4 | Polish & Launch | Testing, first customer onboarded |

**Target Launch: January 2026**

---

*This handoff document created: November 30, 2025*
