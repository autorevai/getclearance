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
# Start all services
docker-compose up -d

# Frontend: http://localhost:9000
# API: http://localhost:8000
# API Docs: http://localhost:8000/docs
```

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

Create `.env` in root:

```env
# Database
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/getclearance

# Redis
REDIS_URL=redis://localhost:6379

# Claude API
ANTHROPIC_API_KEY=your-key-here

# Document Storage (Cloudflare R2)
R2_ACCESS_KEY_ID=your-key
R2_SECRET_ACCESS_KEY=your-secret
R2_BUCKET=getclearance-docs
R2_ENDPOINT=https://your-account.r2.cloudflarestorage.com
```

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
