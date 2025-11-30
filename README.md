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

# 2. Start all services
docker-compose up -d

# Frontend: http://localhost:9000
# API: http://localhost:8000
# API Docs: http://localhost:8000/docs
```

**Security Note**: This Docker setup follows security best practices. See [Docker Security Documentation](./docs/DOCKER_SECURITY.md) for details.

## Project Structure

```
getclearance/
├── frontend/                 # React application
│   ├── src/
│   │   ├── components/       # UI components
│   │   │   ├── AppShell.jsx          # Main layout, navigation
│   │   │   ├── Dashboard.jsx         # KPI cards, AI insights
│   │   │   ├── ApplicantsList.jsx    # Applicants table
│   │   │   ├── ApplicantDetail.jsx   # Individual applicant view
│   │   │   ├── ScreeningChecks.jsx   # AML screening
│   │   │   ├── CaseManagement.jsx    # Case queue
│   │   │   ├── ApplicantAssistant.jsx # End-user chat
│   │   │   └── DesignSystem.jsx      # Shared components
│   │   ├── App.jsx
│   │   └── index.js
│   └── package.json
│
├── backend/                  # FastAPI application (TODO)
│   ├── app/
│   │   ├── api/v1/          # API routes
│   │   ├── models/          # SQLAlchemy models
│   │   ├── schemas/         # Pydantic schemas
│   │   ├── services/        # Business logic
│   │   └── workers/         # Background jobs
│   ├── migrations/          # Alembic
│   └── requirements.txt
│
├── docs/
│   ├── ARCHITECTURE.md      # System design
│   └── HANDOVER.md          # Project status
│
├── docker-compose.yml
└── README.md
```

## Tech Stack

### Frontend
- React 18
- Lucide React (icons)
- Inline CSS (no external dependencies)

### Backend (V1)
- FastAPI
- PostgreSQL 15+
- Redis
- ARQ (task queue)
- Cloudflare R2 (document storage)

### AI
- Claude API (risk assessment, document analysis)

## Features

### Implemented (Frontend)
- [x] Dashboard with KPI cards and AI insights
- [x] Applicants list with filtering, batch actions
- [x] Applicant detail with AI Snapshot tab
- [x] AML Screening checks with list version tracking
- [x] Case management queue
- [x] Applicant-facing chat assistant
- [x] Dark/light theme
- [x] Responsive design

### TODO (Backend)
- [ ] FastAPI scaffold
- [ ] PostgreSQL models
- [ ] Authentication (JWT)
- [ ] Applicants CRUD API
- [ ] Companies (KYB) API
- [ ] Screening engine + OpenSanctions integration
- [ ] Evidence pack export
- [ ] Claude API integration for AI summaries

## Development

### Prerequisites
- Node.js 18+
- Docker & Docker Compose
- Python 3.11+ (for backend)

### Environment Variables

**Important**:
- Never commit `.env.local` or `.env` files to version control
- Use strong, unique passwords for production
- For Docker Compose: copy `.env.local` to `.env` or use `docker-compose --env-file .env.local up`

Key variables:
- `POSTGRES_PASSWORD` - Database password (required)
- `REDIS_PASSWORD` - Redis password (optional for dev, required for prod)
- `MINIO_ROOT_PASSWORD` - MinIO password (required)
- `ANTHROPIC_API_KEY` - Claude API key
- `R2_ACCESS_KEY_ID`, `R2_SECRET_ACCESS_KEY` - Cloudflare R2 credentials

### Running Tests

```bash
# Frontend
cd frontend && npm test

# Backend
cd backend && pytest
```

## Deployment

### Option 1: Railway (Recommended for V1)

1. Push to GitHub
2. Connect Railway to your repo
3. Add PostgreSQL and Redis services
4. Set environment variables
5. Deploy

### Option 2: Render

Similar to Railway - connect repo, add managed Postgres/Redis.

### Option 3: AWS (Production)

See `docs/ARCHITECTURE.md` for full AWS deployment guide.

## API Documentation

When backend is running: http://localhost:8000/docs

Key endpoints:
- `GET /api/v1/applicants` - List applicants
- `GET /api/v1/applicants/{id}` - Get applicant detail
- `POST /api/v1/screening/run` - Run screening check
- `GET /api/v1/cases` - List cases
- `POST /api/v1/evidence/export` - Generate evidence pack

## License

Proprietary - All rights reserved.

---

Built by Chris | [Get Clearance](https://getclearance.ai)
