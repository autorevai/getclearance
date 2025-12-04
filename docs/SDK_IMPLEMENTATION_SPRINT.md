# Web SDK Implementation Sprint

**Project:** GetClearance Web SDK
**Created:** December 2, 2025
**Purpose:** Enable customer websites to embed identity verification flows
**Status:** Sprint 1 Complete, Ready for Testing

---

## Executive Summary

This sprint delivered the **embeddable Web SDK** that enables your customers to integrate identity verification directly into their websites. Like Sumsub's WebSDK, this allows end-users to complete KYC verification without leaving the customer's site.

### What Was Built

| Component | Location | Status |
|-----------|----------|--------|
| **SDK Backend API** | `backend/app/api/v1/sdk.py` | COMPLETE |
| **Verification Flow Component** | `frontend/src/components/sdk/VerificationSDK.jsx` | COMPLETE |
| **SDK Verify Page** | `frontend/src/components/sdk/SDKVerifyPage.jsx` | COMPLETE |
| **Demo/Test Page** | `frontend/src/components/sdk/SDKDemoPage.jsx` | COMPLETE |
| **App Routing Update** | `frontend/src/App.jsx` | COMPLETE |
| **Router Registration** | `backend/app/api/router.py` | COMPLETE |

---

## Architecture Overview

```
Customer Website                    GetClearance Platform
┌─────────────────────┐            ┌──────────────────────┐
│                     │            │                      │
│  1. User clicks     │            │  SDK Access Token    │
│     "Verify ID"     │────────────▶  POST /sdk/access-token
│                     │            │  (API Key auth)      │
│                     │◀────────────  Returns: access_token
│                     │            │                      │
│  2. Frontend loads  │            │  SDK Endpoints       │
│     SDK with token  │────────────▶  GET /sdk/config     │
│                     │            │  POST /sdk/documents │
│     <VerificationSDK│            │  POST /sdk/steps     │
│       accessToken=  │            │  POST /sdk/submit    │
│       "sdk_xxx" />  │            │                      │
│                     │            │                      │
│  3. User completes  │            │  Webhook             │
│     verification    │◀────────────  POST /webhooks      │
│                     │            │  (status update)     │
└─────────────────────┘            └──────────────────────┘
```

---

## How It Works

### Step 1: Customer Backend Gets Access Token

```bash
curl -X POST https://api.getclearance.ai/api/v1/sdk/access-token \
  -H "Content-Type: application/json" \
  -H "X-API-Key: sk_live_xxxxx" \
  -d '{
    "external_user_id": "user_123",
    "email": "user@example.com",
    "first_name": "John",
    "last_name": "Doe"
  }'
```

Response:
```json
{
  "access_token": "sdk_abc123...",
  "applicant_id": "uuid-here",
  "expires_at": "2025-12-02T12:00:00Z",
  "sdk_url": "https://app.getclearance.ai/sdk/verify?token=sdk_abc123..."
}
```

### Step 2: Customer Frontend Embeds SDK

**Option A: Redirect to hosted page**
```javascript
window.location.href = response.sdk_url;
```

**Option B: Open in popup/iframe**
```javascript
window.open(response.sdk_url, 'verification', 'width=500,height=700');
```

**Option C: Embed React component**
```jsx
import { VerificationSDK } from '@getclearance/sdk';

<VerificationSDK
  accessToken={accessToken}
  onComplete={(result) => {
    console.log('Verification submitted!', result);
  }}
  onError={(error) => {
    console.error('Error:', error);
  }}
/>
```

### Step 3: User Completes Verification

The SDK guides users through:
1. **Consent** - Data processing agreement
2. **Document** - Upload ID (passport, driver's license, ID card)
3. **Selfie** - Take a photo for face matching
4. **Review** - Submit for verification

### Step 4: Customer Receives Webhook

```json
{
  "type": "applicant.status_changed",
  "applicant_id": "uuid-here",
  "external_user_id": "user_123",
  "status": "approved",
  "timestamp": "2025-12-02T12:00:00Z"
}
```

---

## SDK Endpoints Reference

All endpoints use SDK token authentication: `Authorization: Bearer sdk_xxx`

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/v1/sdk/access-token` | POST | Generate SDK token (requires API key) |
| `/api/v1/sdk/config` | GET | Get verification flow configuration |
| `/api/v1/sdk/documents/upload-url` | POST | Get presigned URL for document upload |
| `/api/v1/sdk/documents/confirm` | POST | Confirm document upload completed |
| `/api/v1/sdk/steps/complete` | POST | Mark a step as complete |
| `/api/v1/sdk/status` | GET | Get current verification status |
| `/api/v1/sdk/submit` | POST | Submit verification for review |

---

## Sprint Tracking

### Sprint 1: Core SDK (COMPLETE)

| Task | Status | Notes |
|------|--------|-------|
| Create SDK API endpoints | DONE | `backend/app/api/v1/sdk.py` |
| Implement SDK token system | DONE | In-memory store (use Redis in production) |
| Create VerificationSDK component | DONE | Full 4-step flow |
| Build ConsentStep component | DONE | GDPR consent UI |
| Build DocumentStep component | DONE | Multi-document with camera capture |
| Build SelfieStep component | DONE | Camera + upload with preview |
| Build ReviewStep component | DONE | Summary and submit |
| Create SDKVerifyPage (public route) | DONE | `/sdk/verify?token=xxx` |
| Create SDKDemoPage | DONE | `/sdk/demo` for testing |
| Update App.jsx routing | DONE | SDK routes outside Auth0 |
| Register SDK router | DONE | In `api/router.py` |

### Sprint 2: Production Readiness (TODO)

| Task | Status | Priority |
|------|--------|----------|
| Move SDK tokens to Redis | TODO | HIGH |
| Add webhook notifications on status change | TODO | HIGH |
| Create SDK branding/theming options | TODO | MEDIUM |
| Add liveness detection (AWS Rekognition) | TODO | MEDIUM |
| Add face matching (selfie vs ID) | TODO | MEDIUM |
| Create NPM package for React component | TODO | LOW |
| Add vanilla JS SDK (no React) | TODO | LOW |
| Create SDK analytics/logging | TODO | LOW |

### Sprint 3: Advanced Features (TODO)

| Task | Status | Priority |
|------|--------|----------|
| Multi-language support | TODO | MEDIUM |
| Custom step configuration per tenant | TODO | MEDIUM |
| Progressive disclosure for complex flows | TODO | LOW |
| Video verification step | TODO | LOW |
| Questionnaire step integration | TODO | LOW |

---

## Testing the SDK

### Method 1: Demo Page

1. Run the frontend: `cd frontend && npm start`
2. Navigate to: `http://localhost:9000/sdk/demo`
3. Enter a test API key (or use "test_demo_key" in dev mode)
4. Generate an access token
5. Click "Open SDK Here" to test the flow

### Method 2: Direct URL

After generating a token via API:
```
http://localhost:9000/sdk/verify?token=sdk_xxx
```

### Method 3: cURL Testing

```bash
# Generate token (with test key in dev mode)
curl -X POST http://localhost:8000/api/v1/sdk/access-token \
  -H "Content-Type: application/json" \
  -H "X-API-Key: test_dev_key" \
  -d '{
    "external_user_id": "test_user_1",
    "email": "test@example.com"
  }'

# Get SDK config
TOKEN="sdk_xxx"
curl http://localhost:8000/api/v1/sdk/config \
  -H "Authorization: Bearer $TOKEN"

# Get status
curl http://localhost:8000/api/v1/sdk/status \
  -H "Authorization: Bearer $TOKEN"
```

---

## Files Changed/Created

### Backend
```
backend/app/api/v1/sdk.py           # NEW - SDK API endpoints
backend/app/api/router.py           # MODIFIED - Added SDK router
```

### Frontend
```
frontend/src/components/sdk/
├── VerificationSDK.jsx             # NEW - Main SDK component
├── SDKVerifyPage.jsx               # NEW - Public verify page
└── SDKDemoPage.jsx                 # NEW - Demo/test page

frontend/src/App.jsx                # MODIFIED - Added SDK routes
```

---

## Known Issues & TODOs

### Critical for Production

1. **SDK Token Storage**: Currently using in-memory dict. Must move to Redis.
   ```python
   # sdk.py line ~100
   _sdk_tokens: dict[str, dict] = {}  # TODO: Use Redis
   ```

2. **API Key Validation**: Fallback to test keys only works in DEBUG mode.

3. **Document Processing**: After upload, need to trigger OCR/screening workers.
   ```python
   # sdk.py line ~350
   # TODO: Trigger document processing (OCR, verification)
   ```

4. **Database Migration**: Run the migration to add `custom_data` column:
   ```bash
   cd backend
   alembic upgrade head
   ```

### Nice to Have

- [ ] Customizable branding per tenant (logo, colors)
- [ ] Step skipping/reordering based on workflow
- [ ] Mobile-optimized camera experience
- [ ] QR code for mobile handoff

---

## Integration Checklist for Customers

- [ ] Get API key from Settings > Integrations
- [ ] Set up webhook endpoint to receive status updates
- [ ] Implement backend endpoint to generate SDK tokens
- [ ] Add SDK to frontend (redirect, popup, or embed)
- [ ] Test with real documents in sandbox mode
- [ ] Go live!

---

## Next Steps

1. **Test the SDK flow** at `/sdk/demo`
2. **Fix any issues** discovered during testing
3. **Move to Sprint 2** for production hardening
4. **Create customer documentation** for integration

---

**Last Updated:** December 3, 2025
**Sprint Status:** Sprint 1 COMPLETE - Ready for Testing

---

## Quick Test Commands

```bash
# Backend
cd backend
uvicorn app.main:app --reload --port 8000

# Frontend (in another terminal)
cd frontend
npm start

# Then visit:
# http://localhost:9000/sdk/demo
```
