# SignalWeave Production Deployment Checklist

**Target:** Railway.app  
**Timeline:** Week 7-8 (December 2025)  
**Launch Date:** January 2026

---

## Pre-Deployment Tasks

### Code Readiness

- [ ] All Phase 1-6 services implemented and tested
- [ ] Unit tests passing (>80% coverage)
- [ ] Integration tests passing
- [ ] E2E tests passing for critical flows
- [ ] Security audit completed (no critical issues)
- [ ] Load testing completed (100+ req/min sustained)
- [ ] Memory leak testing (24hr stability test)

### Database

- [ ] All migrations created and tested
- [ ] Indexes optimized for production queries
- [ ] RLS (Row-Level Security) policies tested
- [ ] Backup strategy defined
- [ ] Data retention policies documented
- [ ] PII encryption enabled

### Environment Variables

Create `.env.production` with:

```bash
# App Config
ENVIRONMENT=production
APP_NAME=SignalWeave
APP_VERSION=1.0.0
DEBUG=false
LOG_LEVEL=INFO

# Database
DATABASE_URL=postgresql+asyncpg://user:pass@host:5432/signalweave
DATABASE_POOL_SIZE=20
DATABASE_MAX_OVERFLOW=10

# Redis
REDIS_URL=redis://user:pass@host:6379/0
REDIS_MAX_CONNECTIONS=50

# Storage (Cloudflare R2)
R2_ENDPOINT=https://your-account-id.r2.cloudflarestorage.com
R2_ACCESS_KEY_ID=your-access-key
R2_SECRET_ACCESS_KEY=your-secret-key
R2_BUCKET=signalweave-documents-prod

# Auth0
AUTH0_DOMAIN=signalweave.auth0.com
AUTH0_CLIENT_ID=your-client-id
AUTH0_CLIENT_SECRET=your-client-secret
AUTH0_AUDIENCE=https://api.signalweave.com

# AI (Claude)
ANTHROPIC_API_KEY=sk-ant-api03-your-key

# Screening (OpenSanctions)
OPENSANCTIONS_API_KEY=your-opensanctions-key

# OCR (AWS Textract)
AWS_ACCESS_KEY_ID=your-aws-key
AWS_SECRET_ACCESS_KEY=your-aws-secret
AWS_REGION=us-east-1

# Monitoring
SENTRY_DSN=https://your-sentry-dsn@sentry.io/project-id

# Security
SECRET_KEY=generate-with-openssl-rand-hex-32
CORS_ORIGINS=https://app.signalweave.com,https://signalweave.com

# Rate Limiting
RATE_LIMIT_PER_MINUTE=100
RATE_LIMIT_BURST=20

# Webhooks
WEBHOOK_MAX_RETRIES=3
WEBHOOK_RETRY_DELAY_SECONDS=30,300,3600  # 30s, 5min, 1hr
```

### Security Checklist

- [ ] All secrets stored in environment variables (not code)
- [ ] HTTPS/TLS enabled (Railway provides this)
- [ ] CORS configured correctly
- [ ] Rate limiting enabled
- [ ] SQL injection tests passed
- [ ] XSS protection verified
- [ ] CSRF protection enabled
- [ ] JWT signature verification working
- [ ] Input validation on all endpoints
- [ ] Error messages don't leak sensitive info

---

## Railway Deployment Steps

### 1. Create Railway Project

```bash
# Install Railway CLI
npm i -g @railway/cli

# Login
railway login

# Create new project
railway init
# Select: "Create new project"
# Name: signalweave-api

# Link to GitHub repo
railway link
```

### 2. Provision Database

In Railway dashboard:
1. Click "New" → "Database" → "Add PostgreSQL"
2. Note the connection string
3. Set `DATABASE_URL` in environment variables

```bash
railway variables set DATABASE_URL="postgresql://..."
```

### 3. Provision Redis

In Railway dashboard:
1. Click "New" → "Database" → "Add Redis"
2. Note the connection string
3. Set `REDIS_URL` in environment variables

```bash
railway variables set REDIS_URL="redis://..."
```

### 4. Configure Environment Variables

Set all required environment variables:

```bash
# Core
railway variables set ENVIRONMENT=production
railway variables set SECRET_KEY=$(openssl rand -hex 32)

# Auth0
railway variables set AUTH0_DOMAIN=signalweave.auth0.com
railway variables set AUTH0_CLIENT_ID=your-client-id
railway variables set AUTH0_CLIENT_SECRET=your-client-secret
railway variables set AUTH0_AUDIENCE=https://api.signalweave.com

# Cloudflare R2
railway variables set R2_ENDPOINT=https://...
railway variables set R2_ACCESS_KEY_ID=...
railway variables set R2_SECRET_ACCESS_KEY=...
railway variables set R2_BUCKET=signalweave-documents-prod

# APIs
railway variables set ANTHROPIC_API_KEY=sk-ant-...
railway variables set OPENSANCTIONS_API_KEY=...

# AWS (for Textract)
railway variables set AWS_ACCESS_KEY_ID=...
railway variables set AWS_SECRET_ACCESS_KEY=...
railway variables set AWS_REGION=us-east-1

# Monitoring
railway variables set SENTRY_DSN=https://...

# CORS
railway variables set CORS_ORIGINS=https://app.signalweave.com
```

### 5. Create Railway.toml

Create `railway.toml` in project root:

```toml
[build]
builder = "nixpacks"
buildCommand = "pip install -r requirements.txt"

[deploy]
startCommand = "alembic upgrade head && uvicorn app.main:app --host 0.0.0.0 --port $PORT"
restartPolicyType = "on_failure"
restartPolicyMaxRetries = 10

[healthcheck]
path = "/health"
timeout = 100
interval = 60
```

### 6. Deploy

```bash
# Deploy from local
railway up

# Or deploy from GitHub (recommended)
# In Railway dashboard:
# 1. Connect GitHub repo
# 2. Select branch: main
# 3. Click "Deploy"
```

### 7. Run Database Migrations

```bash
# Railway will run migrations automatically via startCommand
# Or manually:
railway run alembic upgrade head
```

### 8. Configure Custom Domain

In Railway dashboard:
1. Go to "Settings" → "Domains"
2. Add custom domain: `api.signalweave.com`
3. Update DNS records as instructed
4. Wait for SSL certificate provisioning (~5 minutes)

### 9. Verify Deployment

```bash
# Check health
curl https://api.signalweave.com/health

# Expected response:
# {
#   "status": "healthy",
#   "version": "1.0.0",
#   "environment": "production"
# }

# Check API docs (if enabled for production)
curl https://api.signalweave.com/docs
```

---

## Post-Deployment Verification

### Smoke Tests

Run these critical path tests:

```bash
# 1. Create applicant
curl -X POST https://api.signalweave.com/api/v1/applicants \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "first_name": "Test",
    "last_name": "User"
  }'

# 2. Upload document (get presigned URL)
curl -X POST https://api.signalweave.com/api/v1/documents/upload-url \
  -H "Authorization: Bearer $TOKEN" \
  -d "applicant_id=..." \
  -d "document_type=passport" \
  -d "file_name=passport.jpg"

# 3. Run screening
curl -X POST https://api.signalweave.com/api/v1/screening/check \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Test User",
    "date_of_birth": "1990-01-15",
    "country": "USA"
  }'

# 4. List applicants
curl https://api.signalweave.com/api/v1/applicants \
  -H "Authorization: Bearer $TOKEN"
```

### Performance Tests

- [ ] API latency P99 < 500ms
- [ ] Database query time P99 < 100ms
- [ ] Screening check completes < 5 seconds
- [ ] Document upload (10MB) < 30 seconds
- [ ] 100 concurrent requests handled without errors

### Monitoring Setup

In Railway dashboard:
1. Enable "Metrics" tab
2. Monitor:
   - CPU usage (<70% average)
   - Memory usage (<80% average)
   - Request rate
   - Error rate (<1%)
   - Database connections

### Sentry Configuration

```python
# Already in app/main.py, verify it's working:
import sentry_sdk
from sentry_sdk.integrations.fastapi import FastApiIntegration

sentry_sdk.init(
    dsn=settings.sentry_dsn,
    environment=settings.environment,
    traces_sample_rate=0.1,  # 10% of transactions
    integrations=[FastApiIntegration()],
)
```

Test error reporting:
```bash
# Trigger a test error
curl https://api.signalweave.com/api/v1/test-error

# Check Sentry dashboard for the error
```

---

## Database Backup Strategy

### Automated Backups (Railway)

Railway provides automatic daily backups. Verify:
1. Go to Database → "Backups" tab
2. Ensure backups are enabled
3. Test restore procedure (in staging first!)

### Manual Backup

```bash
# Download latest backup
railway db dump --output backup.sql

# Restore from backup
railway db restore backup.sql
```

### Backup Retention

- **Daily:** Keep 30 days
- **Weekly:** Keep 12 weeks
- **Monthly:** Keep 12 months

---

## Rollback Plan

If deployment fails:

### Rollback Steps

```bash
# 1. Revert to previous deployment
railway rollback

# 2. If database migration failed, rollback migration
railway run alembic downgrade -1

# 3. Verify health
curl https://api.signalweave.com/health

# 4. Check error logs
railway logs
```

---

## First Customer Onboarding

### Create First Tenant

```bash
railway run python scripts/create_tenant.py \
  --name "Acme Corp" \
  --email "admin@acme.com"

# Note the tenant_id and API key
```

### Configure Auth0

1. Create Auth0 application for tenant
2. Configure callback URLs
3. Enable custom claims for `tenant_id` and `role`
4. Test login flow

### Test Full Flow

1. User signs up via frontend
2. Creates applicant
3. Uploads ID document
4. Document processed (OCR + fraud check)
5. Screening runs
6. AI generates risk summary
7. Compliance officer reviews
8. Applicant approved
9. Evidence pack exported

---

## Monitoring & Alerts

### Set Up Alerts

In Sentry or Railway:
- [ ] Error rate > 5% for 5 minutes
- [ ] API latency P99 > 1 second
- [ ] Database connections > 80% of pool
- [ ] Memory usage > 90%
- [ ] Disk usage > 85%

### Health Check Endpoints

Monitor these endpoints:
- `GET /health` - Basic health
- `GET /health/ready` - Readiness (DB + Redis connected)

### Log Monitoring

```bash
# Stream logs
railway logs --follow

# Filter for errors
railway logs | grep ERROR

# Filter for specific service
railway logs --service api
```

---

## Success Criteria

Deployment is successful when:

- [ ] All smoke tests pass
- [ ] Error rate <1%
- [ ] API latency P99 <500ms
- [ ] Uptime monitoring shows 99.9%
- [ ] First customer completes full KYC flow
- [ ] All alerts configured and tested
- [ ] Team has access to logs and metrics
- [ ] Rollback procedure tested

---

## Post-Launch Checklist (Week 1)

- [ ] Monitor error rates daily
- [ ] Review slow query logs
- [ ] Check database performance
- [ ] Verify backup success
- [ ] Customer feedback collection
- [ ] Performance optimization (if needed)
- [ ] Security scan (external audit)
- [ ] Documentation updates

---

**Deployment Owner:** [Your Name]  
**Deployment Date:** [Target Date]  
**Status:** [ ] Not Started [ ] In Progress [ ] Complete

---

## Emergency Contacts

- **DevOps:** [Contact]
- **Database Admin:** [Contact]
- **Security Lead:** [Contact]
- **Railway Support:** support@railway.app
