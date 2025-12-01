# GetClearance

AI-native KYC/AML compliance platform - a Sumsub alternative.

**Status: 95% Complete - Ready for Production Deployment**

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

# Frontend: http://localhost:9000
# API: http://localhost:8000
# API Docs: http://localhost:8000/docs
```

**Security Note**: See [Docker Security Documentation](./docs/DOCKER_SECURITY.md) for best practices.

## Project Structure

```
getclearance/
├── frontend/                    # React application (100% complete)
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
│   │       ├── config.py        # ARQ worker configuration
│   │       ├── screening_worker.py
│   │       ├── document_worker.py
│   │       ├── ai_worker.py
│   │       └── webhook_worker.py
│   ├── tests/                   # Test suite
│   │   ├── test_screening.py
│   │   ├── test_storage.py
│   │   ├── test_ai.py
│   │   ├── test_workers.py
│   │   └── integration/
│   ├── migrations/              # Alembic migrations
│   ├── Dockerfile
│   ├── railway.json             # Railway deployment config
│   └── requirements.txt
│
├── docs/
│   ├── DEPLOYMENT_GUIDE.md      # Railway deployment instructions
│   ├── ARCHITECTURE.md          # System design
│   ├── ENGINEERING_CONTEXT.md   # Technical implementation details
│   └── implementation-guide/    # Detailed implementation docs
│
├── .env.example                 # Development environment template
├── .env.production.example      # Production environment template
├── docker-compose.yml           # PostgreSQL, Redis
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
- Redis (caching, job queue via ARQ)
- Cloudflare R2 (document storage)
- Auth0 (authentication)

### AI & Integrations
- Claude API (risk assessment, document analysis)
- OpenSanctions (AML/sanctions/PEP screening)
- AWS Textract (OCR document processing)

## Features

### Frontend
- [x] Dashboard with KPI cards and AI insights
- [x] Applicants list with filtering, batch actions
- [x] Applicant detail with AI Snapshot tab
- [x] AML Screening checks with list version tracking
- [x] Case management queue
- [x] Applicant-facing chat assistant
- [x] Dark/light theme
- [x] Responsive design

### Backend
- [x] FastAPI scaffold with async SQLAlchemy
- [x] PostgreSQL models with multi-tenant support
- [x] Auth0 JWT authentication
- [x] Applicants CRUD API
- [x] Documents API with R2 presigned URLs
- [x] Screening API with OpenSanctions integration
- [x] Cases API for investigations
- [x] AI endpoints for risk summaries
- [x] Background workers (ARQ) for async processing
- [x] OCR with MRZ passport validation
- [x] Webhook delivery with retry logic
- [x] Evidence pack PDF export
- [x] Comprehensive test suite

### Optional Enhancements (TODO)
- [ ] Utility scripts (create_tenant, seed_data, check_health)
- [ ] Additional Sumsub-specific schema features

## API Endpoints

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

# AWS (OCR - optional)
AWS_ACCESS_KEY_ID=...
AWS_SECRET_ACCESS_KEY=...
AWS_REGION=us-east-1

# Monitoring (optional)
SENTRY_DSN=...
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

# Frontend tests
cd frontend
npm test
```

### Running Workers

```bash
cd backend
arq app.workers.config.WorkerSettings
```

## Deployment

### Railway (Recommended)

1. Push to GitHub
2. Connect Railway to your repo (set root directory to `backend`)
3. Add PostgreSQL and Redis services
4. Set environment variables (see `.env.production.example`)
5. Deploy - Railway auto-runs migrations via `railway.json`

See [docs/DEPLOYMENT_GUIDE.md](./docs/DEPLOYMENT_GUIDE.md) for detailed instructions.

### Health Check

```bash
curl https://your-app.railway.app/health
# {"status": "healthy", "version": "1.0.0", "environment": "production"}
```

## Project Status

| Component | Status |
|-----------|--------|
| Frontend | 100% Complete |
| Backend API | 100% Complete |
| Services (screening, storage, AI, OCR, webhooks) | 100% Complete |
| Background Workers | 100% Complete |
| Test Suite | 100% Complete |
| Deployment Config | 100% Complete |
| **Overall** | **95% Complete** |

## Documentation

- [Deployment Guide](./docs/DEPLOYMENT_GUIDE.md) - Railway deployment
- [Architecture](./docs/ARCHITECTURE.md) - System design
- [Engineering Context](./docs/ENGINEERING_CONTEXT.md) - Technical details
- [Docker Security](./docs/DOCKER_SECURITY.md) - Security best practices
- [Implementation Guide](./docs/implementation-guide/) - Detailed docs

## License

Proprietary - All rights reserved.

---

Built by Chris | [GetClearance](https://getclearance.ai)
