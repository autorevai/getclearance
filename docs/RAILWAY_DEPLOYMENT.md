# Railway Deployment Guide - GetClearance

This document covers the Railway deployment setup and all issues encountered/resolved during the initial deployment.

## Deployment Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     Railway Project                          │
│                   (divine-nourishment)                       │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐       │
│  │  getclearance │  │   Postgres   │  │    Redis     │       │
│  │   (Backend)   │  │  (Database)  │  │   (Cache)    │       │
│  │              │  │              │  │              │       │
│  │ Port: 8080   │  │ Port: 5432   │  │ Port: 6379   │       │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘       │
│         │                 │                 │               │
│         └────────────────┼────────────────┘               │
│                          │                                  │
│              Internal Network (*.railway.internal)          │
│                                                              │
└─────────────────────────────────────────────────────────────┘
                           │
                           ▼
              Public URL: getclearance-production.up.railway.app
```

## Service Configuration

### getclearance (Backend API)

| Setting | Value |
|---------|-------|
| **Root Directory** | `/backend` |
| **Builder** | Dockerfile |
| **Start Command** | `bash start.sh` |
| **Port** | 8080 (Railway assigns via $PORT) |
| **Target Port** | 8080 |
| **Health Check Path** | `/health` |
| **Health Check Timeout** | 100s |

### PostgreSQL

| Setting | Value |
|---------|-------|
| **Internal Host** | `postgres.railway.internal` |
| **Port** | 5432 |
| **Database** | `railway` |

### Redis

| Setting | Value |
|---------|-------|
| **Internal Host** | `redis.railway.internal` |
| **Port** | 6379 |

---

## Environment Variables

### Required Variables for getclearance Service

```bash
# Application
SECRET_KEY=<generate-with-openssl-rand-hex-32>
ENVIRONMENT=production
DEBUG=false
LOG_LEVEL=INFO
API_PORT=8000

# Database (auto-populated if using Railway reference)
DATABASE_URL=postgresql://postgres:<password>@postgres.railway.internal:5432/railway
DATABASE_POOL_SIZE=20
DATABASE_MAX_OVERFLOW=10

# Redis (auto-populated if using Railway reference)
REDIS_URL=redis://default:<password>@redis.railway.internal:6379
REDIS_MAX_CONNECTIONS=50

# Auth0
AUTH0_DOMAIN=dev-8z4blmy3c8wvkp4k.us.auth0.com
AUTH0_CLIENT_ID=W5uDmvvRYDmw9Sm4avfEzoOxo26XF8rR
AUTH0_CLIENT_SECRET=<your-auth0-client-secret>
AUTH0_AUDIENCE=https://api.getclearance.vercel.app

# Cloudflare R2 Storage
R2_ENDPOINT=https://<account-id>.r2.cloudflarestorage.com
R2_ACCESS_KEY_ID=<your-r2-access-key>
R2_SECRET_ACCESS_KEY=<your-r2-secret-key>
R2_BUCKET=getclearance-docs

# AI & Screening
ANTHROPIC_API_KEY=<your-anthropic-api-key>
OPENSANCTIONS_API_KEY=<your-opensanctions-api-key>

# CORS
CORS_ORIGINS=https://getclearance.vercel.app,https://www.getclearance.vercel.app
FRONTEND_URL=https://getclearance.vercel.app
```

### Using Railway Variable References

Instead of hardcoding database/redis URLs, you can use Railway references:

```bash
DATABASE_URL=${{Postgres.DATABASE_URL}}
REDIS_URL=${{Redis.REDIS_URL}}
```

---

## Issues Encountered & Solutions

### Issue 1: Root Directory Not Set

**Problem:** Railway was looking at the repo root and couldn't find Python files.

**Error:**
```
Railpack could not detect language
```

**Solution:** Set Root Directory to `/backend` in Railway service settings.

**Location:** Service → Settings → Source → Root Directory → `/backend`

---

### Issue 2: Port Mismatch

**Problem:** Dockerfile hardcoded port 8000, but Railway assigns its own port via `$PORT` environment variable.

**Error:**
```
Healthcheck failed - service unavailable
```

**Solution:** Updated Dockerfile CMD to use shell form for variable expansion:

```dockerfile
# Before (broken)
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]

# After (working)
CMD uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}
```

---

### Issue 3: Target Port Mismatch

**Problem:** Railway's public networking target port was set to 8000, but Railway assigned port 8080 to the container.

**Error:**
```
{"status":"error","code":502,"message":"Application failed to respond"}
```

**Solution:** Changed target port in Networking settings from 8000 to 8080.

**Location:** Service → Settings → Networking → Target Port → `8080`

---

### Issue 4: Truncated Environment Variables

**Problem:** Railway's Raw Editor has a character limit, causing long variables to be truncated.

**Affected Variables:**
- `REDIS_URL` - truncated to `redis://...@redis.railway` (missing `.internal:6379`)
- `AUTH0_CLIENT_SECRET` - truncated
- `R2_ENDPOINT` - truncated to `...cloudflarestorag` (missing `e.com`)
- `ANTHROPIC_API_KEY` - truncated
- `CORS_ORIGINS` - truncated

**Solution:** Edit variables individually through the UI, not Raw Editor.

---

### Issue 5: Database Host Resolution Failure

**Problem:** Truncated DATABASE_URL caused host resolution to fail.

**Error:**
```
psycopg2.OperationalError: could not translate host name "post" to address
```

**Solution:** Ensure full DATABASE_URL is set:
```
postgresql://postgres:<password>@postgres.railway.internal:5432/railway
```

---

### Issue 6: Duplicate Alembic Migration

**Problem:** Two migrations tried to add the same `updated_at` column to `screening_checks`.

**Error:**
```
sqlalchemy.exc.ProgrammingError: column "updated_at" of relation "screening_checks" already exists
```

**Solution:**
1. Deleted duplicate migration file `20251201_003_add_screening_updated_at.py`
2. Created `start.sh` script to fix alembic version if stuck:

```bash
python -c "
from sqlalchemy import create_engine, text
import os

db_url = os.environ.get('DATABASE_URL', '').replace('+asyncpg', '')
engine = create_engine(db_url)
with engine.connect() as conn:
    result = conn.execute(text('SELECT version_num FROM alembic_version'))
    current = result.scalar()
    if current == '005':
        conn.execute(text('DELETE FROM alembic_version'))
        conn.execute(text(\"INSERT INTO alembic_version (version_num) VALUES ('004')\"))
        conn.commit()
"
```

---

### Issue 7: Missing numpy Dependency

**Problem:** OCR service imports numpy but it wasn't in requirements.txt.

**Error:**
```
ModuleNotFoundError: No module named 'numpy'
```

**Solution:** Added to `requirements.txt`:
```
numpy==1.26.4
pillow==10.4.0
```

---

## Files Modified for Railway Deployment

### backend/Dockerfile
- Changed CMD to shell form for `$PORT` expansion
- Removed Docker HEALTHCHECK (Railway manages its own)

### backend/railway.json
```json
{
  "$schema": "https://railway.app/railway.schema.json",
  "build": {
    "builder": "NIXPACKS",
    "buildCommand": "pip install -r requirements.txt"
  },
  "deploy": {
    "startCommand": "bash start.sh",
    "restartPolicyType": "ON_FAILURE",
    "restartPolicyMaxRetries": 10,
    "healthcheckPath": "/health",
    "healthcheckTimeout": 100
  }
}
```

### backend/start.sh
```bash
#!/bin/bash
set -e

export PORT=${PORT:-8000}

echo "🚀 Starting GetClearance Backend..."
echo "   Environment: ${ENVIRONMENT:-development}"
echo "   Port: ${PORT}"

# Fix alembic version if needed
echo "📦 Checking database migrations..."
python -c "
from sqlalchemy import create_engine, text
import os

db_url = os.environ.get('DATABASE_URL', '')
if db_url:
    db_url = db_url.replace('+asyncpg', '')
    try:
        engine = create_engine(db_url)
        with engine.connect() as conn:
            result = conn.execute(text('SELECT version_num FROM alembic_version'))
            current = result.scalar()
            print(f'   Current alembic version: {current}')
            if current == '005':
                conn.execute(text('DELETE FROM alembic_version'))
                conn.execute(text(\"INSERT INTO alembic_version (version_num) VALUES ('004')\"))
                conn.commit()
                print('   ✓ Fixed alembic version (005 -> 004)')
    except Exception as e:
        print(f'   Note: Could not check alembic version: {e}')
"

echo "📦 Running database migrations..."
alembic upgrade head
echo "   ✓ Migrations complete"

echo "🌐 Starting uvicorn server..."
exec uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}
```

### backend/requirements.txt
- Added `numpy==1.26.4`
- Added `pillow==10.4.0`

---

## Useful Railway CLI Commands

```bash
# Set token for CLI access
export RAILWAY_TOKEN=<your-project-token>

# Check project status
railway status

# View logs
railway logs --service getclearance

# List variables
railway variables --service getclearance

# Deploy manually (if not using GitHub auto-deploy)
railway up
```

---

## Vercel Frontend Configuration

For the frontend to connect to Railway backend, set these in Vercel:

| Variable | Value |
|----------|-------|
| `REACT_APP_API_BASE_URL` | `https://getclearance-production.up.railway.app/api/v1` |
| `REACT_APP_AUTH0_DOMAIN` | `dev-8z4blmy3c8wvkp4k.us.auth0.com` |
| `REACT_APP_AUTH0_CLIENT_ID` | `W5uDmvvRYDmw9Sm4avfEzoOxo26XF8rR` |
| `REACT_APP_AUTH0_AUDIENCE` | `https://api.getclearance.vercel.app` |

**Important:** `AUTH0_AUDIENCE` must match between Vercel frontend and Railway backend.

---

## Health Check Endpoints

| Endpoint | Purpose | Expected Response |
|----------|---------|-------------------|
| `GET /health` | Basic health check | `{"status":"healthy","version":"0.1.0","environment":"production"}` |
| `GET /health/ready` | Readiness check (DB + Redis) | `{"status":"ready","checks":{"database":"ok","redis":"ok"}}` |

---

## Deployment Checklist

- [ ] Root Directory set to `/backend`
- [ ] PostgreSQL service added and running
- [ ] Redis service added and running
- [ ] All environment variables set (not truncated!)
- [ ] Target port matches $PORT (usually 8080)
- [ ] Health check path set to `/health`
- [ ] GitHub repo connected for auto-deploy
- [ ] Public domain generated
- [ ] Vercel frontend updated with backend URL

---

## Monitoring

Railway provides:
- **Logs**: Real-time container logs
- **Metrics**: CPU, Memory, Network usage
- **Observability**: Request traces and errors

Access via: Railway Dashboard → Service → Logs/Metrics tabs

---

## Cost Estimate

Railway Hobby plan (~$5/month) includes:
- 512 MB RAM per service
- Shared CPU
- 1 GB disk per database
- $5 credit included

For production workloads, consider Pro plan for:
- More RAM/CPU
- Better SLAs
- Team features
