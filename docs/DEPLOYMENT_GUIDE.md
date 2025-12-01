# GetClearance Production Deployment Guide

Deploy the GetClearance API to Railway.app.

---

## Prerequisites

- [Railway CLI](https://docs.railway.app/develop/cli) installed
- GitHub repository connected
- API keys ready (Auth0, Cloudflare R2, Anthropic, OpenSanctions)

---

## Step 1: Create Railway Project

```bash
# Install Railway CLI
npm i -g @railway/cli

# Login to Railway
railway login

# Initialize new project (run from backend directory)
cd backend
railway init
# Select: "Create new project"
# Name: getclearance-api
```

---

## Step 2: Provision PostgreSQL Database

In Railway dashboard:
1. Click **"New"** → **"Database"** → **"Add PostgreSQL"**
2. Wait for provisioning (~30 seconds)
3. Railway automatically sets `DATABASE_URL` variable

Verify:
```bash
railway variables | grep DATABASE_URL
```

---

## Step 3: Provision Redis

In Railway dashboard:
1. Click **"New"** → **"Database"** → **"Add Redis"**
2. Wait for provisioning
3. Railway automatically sets `REDIS_URL` variable

Verify:
```bash
railway variables | grep REDIS_URL
```

---

## Step 4: Set Environment Variables

Set all required environment variables:

```bash
# Core Configuration
railway variables set ENVIRONMENT=production
railway variables set DEBUG=false
railway variables set LOG_LEVEL=INFO
railway variables set SECRET_KEY=$(openssl rand -hex 32)

# Auth0 Authentication
railway variables set AUTH0_DOMAIN=getclearance.auth0.com
railway variables set AUTH0_CLIENT_ID=<your-client-id>
railway variables set AUTH0_CLIENT_SECRET=<your-client-secret>
railway variables set AUTH0_AUDIENCE=https://api.getclearance.com

# Cloudflare R2 Storage
railway variables set R2_ENDPOINT=<your-r2-endpoint>
railway variables set R2_ACCESS_KEY_ID=<your-r2-key>
railway variables set R2_SECRET_ACCESS_KEY=<your-r2-secret>
railway variables set R2_BUCKET=getclearance-prod-docs

# Claude AI (Anthropic)
railway variables set ANTHROPIC_API_KEY=<your-anthropic-key>

# OpenSanctions Screening
railway variables set OPENSANCTIONS_API_KEY=<your-opensanctions-key>

# AWS (for Textract OCR - optional)
railway variables set AWS_ACCESS_KEY_ID=<your-aws-key>
railway variables set AWS_SECRET_ACCESS_KEY=<your-aws-secret>
railway variables set AWS_REGION=us-east-1

# Monitoring (optional but recommended)
railway variables set SENTRY_DSN=<your-sentry-dsn>

# CORS - Update with your frontend domain
railway variables set CORS_ORIGINS=https://app.getclearance.com
```

---

## Step 5: Connect GitHub Repository

In Railway dashboard:
1. Go to your project → **Settings** → **Source**
2. Click **"Connect GitHub"**
3. Select repository: `autorevai/getclearance`
4. Set root directory: `backend`
5. Set branch: `main`

---

## Step 6: Deploy

### Option A: Deploy from GitHub (Recommended)
Simply push to `main` branch - Railway auto-deploys.

```bash
git add .
git commit -m "Add Railway deployment config"
git push origin main
```

### Option B: Deploy from CLI
```bash
cd backend
railway up
```

---

## Step 7: Verify Deployment

### Check Deployment Status
```bash
railway status
```

### View Logs
```bash
railway logs --follow
```

### Test Health Endpoint
```bash
# Get your deployment URL from Railway dashboard
curl https://your-app.railway.app/health

# Expected response:
# {
#   "status": "healthy",
#   "version": "1.0.0",
#   "environment": "production"
# }
```

### Test Readiness
```bash
curl https://your-app.railway.app/health/ready
```

---

## Step 8: Configure Custom Domain

1. Go to Railway dashboard → **Settings** → **Domains**
2. Click **"Add Domain"**
3. Enter: `api.getclearance.com`
4. Add DNS records as instructed:
   - **Type:** CNAME
   - **Name:** api
   - **Value:** `<railway-provided-value>`
5. Wait for SSL provisioning (~5 minutes)

---

## Step 9: Run Smoke Tests

Test critical endpoints:

```bash
# Set your API URL
API_URL=https://api.getclearance.com

# Get auth token (replace with your method)
TOKEN="your-jwt-token"

# 1. Health check
curl $API_URL/health

# 2. List applicants (requires auth)
curl -H "Authorization: Bearer $TOKEN" $API_URL/api/v1/applicants

# 3. Create test applicant
curl -X POST $API_URL/api/v1/applicants \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "first_name": "Test",
    "last_name": "User"
  }'
```

---

## Post-Deployment Checklist

- [ ] Health endpoint returns 200
- [ ] Readiness endpoint returns 200
- [ ] Can authenticate with Auth0 token
- [ ] Can create applicant
- [ ] Can upload document (R2 working)
- [ ] Can run screening (OpenSanctions working)
- [ ] Can generate AI summary (Claude working)
- [ ] Custom domain working with SSL
- [ ] Monitoring/alerts configured

---

## Monitoring

### Railway Metrics
Railway dashboard provides:
- CPU usage
- Memory usage
- Request counts
- Error rates

### Sentry (Error Tracking)
If configured, Sentry provides:
- Error tracking
- Performance monitoring
- Release tracking

### Health Checks
Railway automatically monitors `/health` endpoint.

---

## Database Management

### Run Migrations Manually
```bash
railway run alembic upgrade head
```

### Check Current Migration
```bash
railway run alembic current
```

### Database Backups
Railway provides automatic daily backups. Access via:
1. Dashboard → PostgreSQL service → **Backups**

### Manual Backup
```bash
railway db dump --output backup.sql
```

---

## Rollback

### Rollback to Previous Deployment
```bash
railway rollback
```

### Rollback Database Migration
```bash
railway run alembic downgrade -1
```

---

## Troubleshooting

### Deployment Fails
```bash
# Check build logs
railway logs --build

# Common issues:
# - Missing requirements in requirements.txt
# - Python version mismatch
# - Build command errors
```

### Database Connection Issues
```bash
# Verify DATABASE_URL is set
railway variables | grep DATABASE_URL

# Test connection
railway run python -c "from app.database import engine; print('Connected!')"
```

### CORS Errors
Ensure `CORS_ORIGINS` includes your frontend domain:
```bash
railway variables set CORS_ORIGINS=https://app.getclearance.com,https://getclearance.com
```

### Health Check Failing
```bash
# Check if app is starting
railway logs | grep -i "starting\|error"

# Verify health endpoint works locally
curl localhost:8000/health
```

---

## Scaling

### Horizontal Scaling
In Railway dashboard → **Settings**:
- Enable **"Replicas"** for horizontal scaling
- Set replica count based on load

### Vertical Scaling
Adjust resources in Railway dashboard:
- Memory: Start with 512MB, scale to 2GB if needed
- CPU: Railway auto-scales

---

## Security Checklist

- [x] All secrets in environment variables (not in code)
- [x] HTTPS/SSL enabled (Railway provides)
- [x] CORS configured for production domain only
- [x] Debug mode disabled
- [x] API docs disabled in production
- [ ] Rate limiting enabled (TODO)
- [ ] WAF configured (optional, via Cloudflare)

---

## Cost Estimation

Railway pricing (as of 2024):
- **Hobby Plan:** $5/month (includes $5 credit)
- **Pro Plan:** $20/month (includes $20 credit)
- **Usage:** ~$0.000231/minute per vCPU, ~$0.000231/minute per 512MB RAM

Estimated monthly cost for GetClearance:
- API service: ~$10-30/month
- PostgreSQL: ~$5-15/month
- Redis: ~$5/month
- **Total:** ~$20-50/month

---

## Support

- **Railway Docs:** https://docs.railway.app
- **Railway Discord:** https://discord.gg/railway
- **Railway Support:** support@railway.app

---

**Last Updated:** December 2025
