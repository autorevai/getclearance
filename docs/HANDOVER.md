# Get Clearance Compliance Platform - Handover Document

## Project Overview

Building an AI-native KYC/AML compliance platform to compete with Sumsub, Flagright, and similar incumbents. The key differentiator is deep AI integration for faster approvals, intelligent document processing, and automated risk assessment.

**Target Market:** US-focused initially, then expand globally
**Target Launch:** January 2026
**Current Date:** November 30, 2025

---

## What's Done

### Frontend React Components (Complete)

All components are in `frontend/` folder:
- React 18 + Lucide React icons
- Inline CSS (no external dependencies needed)
- Dark/light theme support
- DM Sans + JetBrains Mono fonts

| Component | File | Status | Description |
|-----------|------|--------|-------------|
| AppShell | `AppShell.jsx` | ✅ Complete | Main layout with sidebar nav, top bar, search, AI assistant panel |
| Dashboard | `Dashboard.jsx` | ✅ Complete | KPI cards, AI insights feed, screening summary, SLA performance |
| ApplicantsList | `ApplicantsList.jsx` | ✅ Complete | Filterable table, batch actions, AI batch review, risk scores |
| ApplicantDetail | `ApplicantDetail.jsx` | ✅ Complete | Full profile, AI Snapshot tab, screening results, activity timeline |
| ScreeningChecks | `ScreeningChecks.jsx` | ✅ Complete | AML screening, sanctions/PEP matching, list version tracking |
| CaseManagement | `CaseManagement.jsx` | ✅ Complete | Case queue, AI summaries, notes, resolution workflow |
| ApplicantAssistant | `ApplicantAssistant.jsx` | ✅ Complete | End-user chat assistant for onboarding help |
| DesignSystem | `DesignSystem.jsx` | ✅ Complete | Reusable: Button, Badge, Card, Avatar, RiskScore, EmptyState, Spinner |
| App | `App.jsx` | ✅ Complete | Main entry point with routing |

### Infrastructure (Complete)

| Item | Status |
|------|--------|
| docker-compose.yml | ✅ Postgres + Redis + MinIO |
| ARCHITECTURE.md | ✅ Full system design with Railway deployment |
| README.md | ✅ Setup instructions |
| .gitignore | ✅ |
| Project structure | ✅ Monorepo with frontend/ and backend/ |

### Design Decisions

1. **Branding:** Get Clearance, logo "GC", indigo/violet accent (#6366f1)
2. **Theme:** Dark mode default
3. **Typography:** DM Sans for UI, JetBrains Mono for IDs/code
4. **AI Integration:** Sparkle icon throughout, dedicated AI panel, AI Snapshot tab

---

## What Needs Building (January Launch)

### Critical Path (Must Have)

| Item | Priority | Estimate | Notes |
|------|----------|----------|-------|
| Auth (Clerk or Auth0) | P0 | 2-3 days | Login, signup, protect API routes |
| FastAPI scaffold | P0 | 1 day | Main app, config, dependencies |
| Database models | P0 | 2 days | SQLAlchemy from ARCHITECTURE.md schema |
| Applicants API | P0 | 3-4 days | CRUD, connect frontend to real data |
| Document upload | P0 | 2 days | Upload to Cloudflare R2, store refs |
| Basic screening | P0 | 3-4 days | OpenSanctions API integration |
| Deploy to Railway | P0 | 1 day | Postgres + Redis + API live |

**Total: ~2-3 weeks focused work**

### After Launch (P1)

| Item | Notes |
|------|-------|
| Companies/KYB API | Business entity verification |
| Cases API | Investigation workflow |
| Evidence Pack export | PDF generation with citations |
| Claude AI integration | Risk summaries, document analysis |
| Frontend: Companies page | Mirror Applicants pattern |
| Frontend: Integrations page | Config tiles for data sources |

---

## Project Structure

```
getclearance/
├── frontend/
│   ├── src/
│   │   ├── components/      # All UI components (done)
│   │   ├── App.jsx
│   │   └── index.js
│   ├── public/
│   └── package.json
│
├── backend/
│   ├── app/                 # FastAPI (to build)
│   └── init.sql
│
├── docs/
│   ├── ARCHITECTURE.md      # Full system design
│   └── HANDOVER.md          # This file
│
├── docker-compose.yml
├── README.md
└── .gitignore
```

---

## How to Continue

### 1. Get the code running

```bash
# Frontend
cd frontend
npm install
npm start

# Infrastructure (Postgres + Redis)
docker-compose up -d
```

### 2. Start new chat for backend

In the next Claude chat within this project, say:

> "I have Get Clearance set up in GitHub. Frontend is done. Need to build the backend for January launch. Start with Clerk auth + FastAPI scaffold. ARCHITECTURE.md has the database schema."

### 3. Build order

```
Week 1: Auth + FastAPI scaffold + DB models
Week 2: Applicants API + Document upload
Week 3: Screening integration (OpenSanctions)
Week 4: Deploy to Railway + testing + first customer
```

---

## Tech Stack

| Layer | Technology |
|-------|------------|
| Frontend | React 18, Lucide icons |
| Frontend Hosting | Vercel or Netlify |
| Backend | FastAPI (Python) |
| Database | PostgreSQL 15+ |
| Cache/Queue | Redis + ARQ |
| Document Storage | Cloudflare R2 |
| Auth | Clerk or Auth0 |
| Screening Data | OpenSanctions API |
| AI | Claude API |
| Hosting | Railway |
| DNS/CDN | Cloudflare |

---

## Design Principles

1. **AI-First** - Every screen surfaces AI insights
2. **Less Clicking** - Batch actions, keyboard shortcuts
3. **Provenance Always** - Show list_version_id, timestamps, sources
4. **Clean Tables** - Visual risk bars, status badges
5. **Dark Mode Default** - Light mode as toggle
6. **Citations Required** - AI never makes unsupported claims

---

*Created: November 30, 2025*
