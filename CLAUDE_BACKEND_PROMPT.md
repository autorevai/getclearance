# Claude Backend Development Prompt

Copy and paste this into a new Claude chat to continue building Get Clearance.

---

## Context

You are building the backend for **Get Clearance**, an AI-native KYC/AML compliance platform. The frontend (React) is complete and deployed. You need to build the FastAPI backend to connect it to real data.

**Repository:** https://github.com/autorevai/getclearance
**Target Launch:** January 2026
**Current State:** Frontend complete, backend needs to be built from scratch

---

## What's Already Done

- **Frontend (Complete):** React 18 app with all UI components
  - Dashboard, ApplicantsList, ApplicantDetail, ScreeningChecks, CaseManagement
  - Dark/light mode, collapsible sidebar, AI assistant panel
  - Running on Vercel (or localhost:9000)

- **Infrastructure Files:**
  - `docker-compose.yml` - PostgreSQL + Redis
  - `backend/init.sql` - Database schema reference
  - `docs/ARCHITECTURE.md` - Full system design with database schema
  - `docs/HANDOVER.md` - Project overview and build order
  - `.env.example` - Required environment variables

---

## Your Task: Build the Backend

Build the FastAPI backend in the `backend/` folder following this priority order:

### Week 1: Foundation

1. **FastAPI Scaffold**
   - Create `backend/app/` structure per ARCHITECTURE.md
   - Set up `main.py`, `config.py` (pydantic-settings), `dependencies.py`
   - Add health check endpoint
   - Configure CORS for frontend

2. **Database Setup**
   - SQLAlchemy 2.0 models matching the schema in ARCHITECTURE.md
   - Start with: `tenants`, `users`, `applicants`, `applicant_steps`, `documents`
   - Alembic migrations
   - Connection pooling

3. **Authentication (Auth0)**
   - Integrate Auth0 for authentication
   - Protect API routes with JWT validation
   - Extract tenant_id from token claims
   - Set up row-level security pattern
   - Configure Auth0 tenant with custom claims for tenant_id and role

### Week 2: Core APIs

4. **Applicants API** (`/api/v1/applicants`)
   - `GET /` - List with filters (status, risk, date range, search)
   - `GET /{id}` - Full detail with steps, documents, screening
   - `POST /` - Create new applicant
   - `PATCH /{id}` - Update status, add review decision
   - `POST /{id}/steps/{step_id}/complete` - Mark step complete

5. **Documents API** (`/api/v1/documents`)
   - `POST /upload` - Upload to Cloudflare R2, return presigned URL
   - `GET /{id}` - Get document metadata
   - `GET /{id}/download` - Generate presigned download URL

6. **Connect Frontend**
   - Replace mock data in React with real API calls
   - Add API service layer with axios/fetch
   - Handle auth token injection
   - Error handling and loading states

### Week 3: Screening

7. **Screening API** (`/api/v1/screening`)
   - `POST /check` - Run screening against OpenSanctions
   - `GET /checks` - List screening checks
   - `GET /checks/{id}` - Check detail with hits
   - `PATCH /hits/{id}` - Resolve hit (confirm/clear)

8. **OpenSanctions Integration**
   - API client for OpenSanctions
   - Fuzzy matching with confidence scores
   - Store list_version_id for audit trail
   - Background job for periodic re-screening

### Week 4: Polish & Deploy

9. **Cases API** (`/api/v1/cases`)
   - CRUD for investigation cases
   - Case notes and attachments
   - Assignment and escalation

10. **Deploy to Railway**
    - Dockerfile for FastAPI
    - Railway PostgreSQL + Redis
    - Environment variables
    - Connect to Vercel frontend

---

## Technical Requirements

### Database Schema
Use the full schema from `docs/ARCHITECTURE.md`. Key tables:
- `tenants`, `users` (multi-tenant foundation)
- `applicants`, `applicant_steps` (KYC workflow)
- `documents` (file metadata, R2 paths)
- `screening_checks`, `screening_hits` (AML screening)
- `cases`, `case_notes` (investigation)
- `audit_log` (immutable, chain-hashed)

### API Structure
```
backend/
├── app/
│   ├── __init__.py
│   ├── main.py              # FastAPI app entry
│   ├── config.py            # Settings from env
│   ├── dependencies.py      # DB session, auth, tenant
│   ├── api/
│   │   └── v1/
│   │       ├── applicants.py
│   │       ├── documents.py
│   │       ├── screening.py
│   │       └── cases.py
│   ├── models/              # SQLAlchemy models
│   ├── schemas/             # Pydantic schemas
│   ├── services/            # Business logic
│   └── workers/             # Background jobs (ARQ)
├── migrations/              # Alembic
├── tests/
├── Dockerfile
└── requirements.txt
```

### Environment Variables (from .env.example)
```
DATABASE_URL=postgresql://...
REDIS_URL=redis://...
ANTHROPIC_API_KEY=sk-ant-...
R2_ACCESS_KEY_ID=...
R2_SECRET_ACCESS_KEY=...
R2_BUCKET=getclearance-docs
R2_ENDPOINT=https://...
AUTH0_DOMAIN=your-tenant.auth0.com
AUTH0_CLIENT_ID=...
AUTH0_CLIENT_SECRET=...
AUTH0_AUDIENCE=https://api.getclearance.com
OPENSANCTIONS_API_KEY=...
```

### Key Patterns

1. **Multi-Tenancy**
   - Every table has `tenant_id`
   - Extract from auth token, inject into all queries
   - Use PostgreSQL RLS for defense in depth

2. **Audit Logging**
   - Log every mutation with old/new values
   - Chain-hash entries for tamper evidence
   - Never delete, only soft-delete

3. **AI Integration (Phase 2)**
   - Claude API for risk summaries
   - Store with citations and provenance
   - Background jobs for batch processing

---

## Commands to Get Started

```bash
# Clone and enter backend
cd getclearance/backend

# Create virtual environment
python -m venv venv
source venv/bin/activate

# Install dependencies (you'll create this)
pip install fastapi uvicorn sqlalchemy alembic pydantic-settings python-jose httpx

# Start infrastructure
docker-compose up -d

# Run API
uvicorn app.main:app --reload --port 8000
```

---

## First Steps

Start with this message:

> "Create the FastAPI scaffold in backend/app/ with:
> 1. main.py with health check and CORS
> 2. config.py with pydantic-settings for DATABASE_URL, REDIS_URL, etc.
> 3. Basic project structure matching ARCHITECTURE.md
> 4. requirements.txt with initial dependencies"

Then continue building each component. Reference ARCHITECTURE.md for the database schema and API structure.

---

## Design Principles

1. **AI-First** - Every API response includes AI-ready data structures
2. **Audit Everything** - Immutable log with chain hashing
3. **Citations Required** - AI never makes unsupported claims
4. **Provenance** - Always include list_version_id, timestamps, sources
5. **Multi-Tenant** - Row-level security, tenant isolation

---

*This prompt covers the full backend build. Tackle it in order, commit frequently, and reference the architecture docs.*
