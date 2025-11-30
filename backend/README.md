# Get Clearance - Backend API

AI-native KYC/AML compliance platform backend built with FastAPI.

## Quick Start

```bash
# 1. Clone and enter backend
cd getclearance/backend

# 2. Create virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Set up environment
# Edit .env.local with your values

# 5. Start infrastructure
docker-compose up -d db redis

# 6. Run migrations
alembic upgrade head

# 7. Start API
uvicorn app.main:app --reload --port 8000
```

API will be available at:
- **API**: http://localhost:8000
- **Docs**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## Project Structure

```
backend/
├── app/
│   ├── __init__.py
│   ├── main.py              # FastAPI app entry point
│   ├── config.py            # Settings (pydantic-settings)
│   ├── database.py          # SQLAlchemy async setup
│   ├── dependencies.py      # Auth, tenant, permissions
│   │
│   ├── api/
│   │   ├── router.py        # API router aggregator
│   │   └── v1/
│   │       ├── applicants.py
│   │       ├── documents.py
│   │       ├── screening.py
│   │       └── cases.py
│   │
│   ├── models/              # SQLAlchemy models
│   │   ├── tenant.py        # Tenant, User
│   │   ├── applicant.py     # Applicant, ApplicantStep
│   │   ├── document.py      # Document
│   │   ├── screening.py     # ScreeningCheck, ScreeningHit
│   │   ├── case.py          # Case, CaseNote
│   │   └── audit.py         # AuditLog
│   │
│   ├── schemas/             # Pydantic schemas
│   │   └── applicant.py
│   │
│   ├── services/            # Business logic (TODO)
│   └── workers/             # Background jobs (TODO)
│
├── migrations/              # Alembic migrations
│   ├── env.py
│   └── versions/
│       └── 20251130_001_initial_schema.py
│
├── tests/                   # Pytest tests (TODO)
├── Dockerfile
├── requirements.txt
├── alembic.ini
└── .env.local
```

## API Endpoints

### Health
- `GET /health` - Health check
- `GET /health/ready` - Readiness check

### Applicants (KYC)
- `GET /api/v1/applicants` - List applicants
- `GET /api/v1/applicants/{id}` - Get applicant detail
- `POST /api/v1/applicants` - Create applicant
- `PATCH /api/v1/applicants/{id}` - Update applicant
- `POST /api/v1/applicants/{id}/review` - Review (approve/reject)
- `POST /api/v1/applicants/{id}/steps/{step_id}/complete` - Complete step

### Documents
- `POST /api/v1/documents/upload-url` - Get presigned upload URL
- `POST /api/v1/documents/{id}/confirm` - Confirm upload complete
- `POST /api/v1/documents/upload` - Direct upload (< 10MB)
- `GET /api/v1/documents/{id}` - Get document metadata
- `GET /api/v1/documents/{id}/download` - Get download URL

### Screening (AML/Sanctions/PEP)
- `POST /api/v1/screening/check` - Run screening check
- `GET /api/v1/screening/checks` - List checks
- `GET /api/v1/screening/checks/{id}` - Get check detail
- `PATCH /api/v1/screening/hits/{id}` - Resolve hit

### Cases
- `GET /api/v1/cases` - List cases
- `GET /api/v1/cases/{id}` - Get case detail
- `POST /api/v1/cases` - Create case
- `PATCH /api/v1/cases/{id}` - Update case
- `POST /api/v1/cases/{id}/resolve` - Resolve case
- `POST /api/v1/cases/{id}/notes` - Add note

## Authentication

Uses Auth0 for JWT-based authentication. Set these environment variables:

```
AUTH0_DOMAIN=your-tenant.auth0.com
AUTH0_CLIENT_ID=your-client-id
AUTH0_AUDIENCE=https://api.getclearance.com
```

In development without Auth0 configured, the API returns mock user context.

## Database Migrations

```bash
# Create new migration
alembic revision --autogenerate -m "description"

# Apply migrations
alembic upgrade head

# Rollback one step
alembic downgrade -1

# View history
alembic history
```

## Development

```bash
# Format code
black app/
ruff check app/ --fix

# Type checking
mypy app/

# Run tests
pytest tests/ -v

# Run with coverage
pytest tests/ --cov=app --cov-report=html
```

## Docker

```bash
# Build and run all services
docker-compose up -d

# View logs
docker-compose logs -f api

# Rebuild after changes
docker-compose up -d --build api

# Stop everything
docker-compose down

# Stop and remove volumes
docker-compose down -v
```

## Environment Variables

Key variables:

| Variable | Description | Default |
|----------|-------------|---------|
| `DATABASE_URL` | PostgreSQL connection string | Required |
| `REDIS_URL` | Redis connection string | Required |
| `AUTH0_DOMAIN` | Auth0 tenant domain | Required in prod |
| `ANTHROPIC_API_KEY` | Claude API key | Required for AI |
| `R2_ACCESS_KEY_ID` | Cloudflare R2 access key | Required for docs |

## Tech Stack

- **Framework**: FastAPI
- **Database**: PostgreSQL 15+ with SQLAlchemy 2.0
- **Cache/Queue**: Redis with ARQ
- **Auth**: Auth0 (JWT)
- **Storage**: Cloudflare R2 (S3-compatible)
- **AI**: Claude API (Anthropic)

## TODO

- [ ] Complete services layer (business logic)
- [ ] Background workers (ARQ jobs)
- [ ] OpenSanctions integration
- [ ] R2 storage service
- [ ] Claude AI integration
- [ ] Test suite
- [ ] Rate limiting middleware
- [ ] Request ID middleware

## License

Proprietary - All rights reserved.
