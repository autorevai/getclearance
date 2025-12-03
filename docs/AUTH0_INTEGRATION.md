# Auth0 Integration Guide - GetClearance

This document covers Auth0 configuration, JWT token structure, common issues, and troubleshooting for the GetClearance platform.

---

## Architecture Overview

```
┌─────────────────┐         ┌─────────────────┐         ┌─────────────────┐
│    Frontend     │────────▶│     Auth0       │────────▶│    Backend      │
│    (Vercel)     │         │  (Universal     │         │   (Railway)     │
│                 │◀────────│    Login)       │         │                 │
│ @auth0/react    │  Token  │                 │         │  jose/python    │
└─────────────────┘         └─────────────────┘         └─────────────────┘
                                    │
                                    ▼
                            ┌─────────────────┐
                            │  Auth0 Action   │
                            │ (Add Claims)    │
                            │                 │
                            │ - tenant_id     │
                            │ - role          │
                            │ - permissions   │
                            └─────────────────┘
```

---

## Auth0 Tenant Configuration

### Tenant Details

| Setting | Value |
|---------|-------|
| **Domain** | `dev-8z4blmy3c8wvkp4k.us.auth0.com` |
| **Region** | US |
| **Environment** | Development |

### Applications

#### 1. Frontend SPA (Single Page Application)

| Setting | Value |
|---------|-------|
| **Name** | GetClearance Frontend |
| **Client ID** | `W5uDmvvRYDmw9Sm4avfEzoOxo26XF8rR` |
| **Application Type** | Single Page Application |
| **Allowed Callback URLs** | `http://localhost:9000, https://getclearance.vercel.app` |
| **Allowed Logout URLs** | `http://localhost:9000, https://getclearance.vercel.app` |
| **Allowed Web Origins** | `http://localhost:9000, https://getclearance.vercel.app` |

#### 2. Backend API (Machine-to-Machine) - Optional

| Setting | Value |
|---------|-------|
| **Name** | GetClearance API |
| **Client ID** | `Wjsqr9S2HMfG4JHqKE1gpLKFCCPOINcR` |
| **Application Type** | Machine to Machine |

### API Configuration

| Setting | Value |
|---------|-------|
| **API Identifier (Audience)** | `https://api.getclearance.vercel.app` |
| **Token Expiration** | 86400 seconds (24 hours) |
| **Allow Skipping User Consent** | Enabled |
| **Signing Algorithm** | RS256 |

---

## JWT Token Structure

### Token Claims (After Auth0 Action)

```json
{
  "iss": "https://dev-8z4blmy3c8wvkp4k.us.auth0.com/",
  "sub": "auth0|abc123",
  "aud": "https://api.getclearance.vercel.app",
  "iat": 1733123456,
  "exp": 1733209856,
  "azp": "W5uDmvvRYDmw9Sm4avfEzoOxo26XF8rR",
  "scope": "openid profile email offline_access",

  "https://getclearance.dev/tenant_id": "9dcded57-c483-401d-b2b7-47bb7e13e503",
  "https://getclearance.dev/role": "admin",
  "https://getclearance.dev/email": "chris.diyanni@gmail.com",
  "https://getclearance.dev/permissions": ["read:applicants", "write:applicants", "admin:*"]
}
```

### Why Namespaced Claims?

Auth0 requires custom claims to use a namespace (URL format) to avoid collisions with standard OIDC claims. We use `https://getclearance.dev/` as our namespace.

**Standard claims** (no namespace needed):
- `sub` - User ID
- `email` - User email (if requested in scope)
- `name` - User name

**Custom claims** (require namespace):
- `tenant_id` - Must be `https://getclearance.dev/tenant_id`
- `role` - Must be `https://getclearance.dev/role`
- `permissions` - Must be `https://getclearance.dev/permissions`

---

## Auth0 Action: Add Custom Claims

### Purpose
Adds tenant_id, role, and permissions from user's `app_metadata` to the access token.

### Action Code

**Name:** `Add Tenant Claims to Token`
**Trigger:** `Login / Post Login`

```javascript
exports.onExecutePostLogin = async (event, api) => {
  const namespace = 'https://getclearance.dev/';

  // Get claims from user's app_metadata (set during provisioning)
  const tenant_id = event.user.app_metadata?.tenant_id;
  const role = event.user.app_metadata?.role || 'viewer';
  const permissions = event.user.app_metadata?.permissions || [];
  const email = event.user.email;

  // Add to access token (used for API calls)
  if (tenant_id) {
    api.accessToken.setCustomClaim(`${namespace}tenant_id`, tenant_id);
  }
  api.accessToken.setCustomClaim(`${namespace}role`, role);
  api.accessToken.setCustomClaim(`${namespace}permissions`, permissions);
  api.accessToken.setCustomClaim(`${namespace}email`, email);

  // Also add to ID token (used for frontend display)
  if (tenant_id) {
    api.idToken.setCustomClaim(`${namespace}tenant_id`, tenant_id);
  }
  api.idToken.setCustomClaim(`${namespace}role`, role);
  api.idToken.setCustomClaim(`${namespace}email`, email);
};
```

### Setting User app_metadata

Users need `app_metadata` set with their tenant information. This can be done:

#### Option 1: Auth0 Dashboard (Manual)

1. Go to Auth0 Dashboard → User Management → Users
2. Find the user
3. Scroll to `app_metadata` section
4. Add JSON:
```json
{
  "tenant_id": "9dcded57-c483-401d-b2b7-47bb7e13e503",
  "role": "admin",
  "permissions": ["read:applicants", "write:applicants", "admin:*"]
}
```

#### Option 2: Auth0 Management API (Programmatic)

```bash
curl -X PATCH "https://dev-8z4blmy3c8wvkp4k.us.auth0.com/api/v2/users/auth0|USER_ID" \
  -H "Authorization: Bearer $MGMT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "app_metadata": {
      "tenant_id": "9dcded57-c483-401d-b2b7-47bb7e13e503",
      "role": "admin",
      "permissions": ["read:applicants", "write:applicants", "admin:*"]
    }
  }'
```

#### Option 3: Auto-Provisioning via Backend (Recommended)

The backend has a `/api/v1/auth/provision` endpoint that:
1. Receives the first login callback
2. Creates a tenant if needed
3. Creates a user record
4. Sets the user's `app_metadata` in Auth0

---

## Backend Token Validation

### Configuration

**File:** `backend/app/config.py`

```python
# Auth0 Settings
auth0_domain: str = "dev-8z4blmy3c8wvkp4k.us.auth0.com"
auth0_audience: str = "https://api.getclearance.vercel.app"
auth0_algorithms: list = ["RS256"]

@property
def auth0_issuer(self) -> str:
    return f"https://{self.auth0_domain}/"

@property
def auth0_jwks_url(self) -> str:
    return f"https://{self.auth0_domain}/.well-known/jwks.json"
```

### Token Verification Flow

**File:** `backend/app/dependencies.py`

1. Extract token from `Authorization: Bearer <token>` header
2. Fetch JWKS from Auth0 (cached)
3. Get `kid` from token header, find matching key in JWKS
4. Verify signature, expiration, audience, issuer
5. Extract claims (handling namespaced format)
6. Return `TokenPayload` with tenant_id, role, permissions

### Handling Namespaced Claims

```python
@classmethod
def from_jwt_payload(cls, payload: dict) -> "TokenPayload":
    namespace = "https://getclearance.dev/"

    # Extract namespaced claims and map to flat names
    tenant_id = payload.get(f"{namespace}tenant_id") or payload.get("tenant_id")
    email = payload.get(f"{namespace}email") or payload.get("email")
    role = payload.get(f"{namespace}role") or payload.get("role")
    permissions = payload.get(f"{namespace}permissions") or payload.get("permissions", [])

    return cls(
        sub=payload["sub"],
        tenant_id=tenant_id,
        email=email,
        role=role,
        permissions=permissions,
        # ... other fields
    )
```

---

## Frontend Configuration

### Environment Variables

**File:** `frontend/.env`

```bash
REACT_APP_AUTH0_DOMAIN=dev-8z4blmy3c8wvkp4k.us.auth0.com
REACT_APP_AUTH0_CLIENT_ID=W5uDmvvRYDmw9Sm4avfEzoOxo26XF8rR
REACT_APP_AUTH0_AUDIENCE=https://api.getclearance.vercel.app
REACT_APP_API_BASE_URL=https://getclearance-production.up.railway.app/api/v1
```

### Auth0Provider Configuration

```jsx
// frontend/src/auth/AuthProvider.jsx
import { Auth0Provider } from '@auth0/auth0-react';

const auth0Config = {
  domain: process.env.REACT_APP_AUTH0_DOMAIN,
  clientId: process.env.REACT_APP_AUTH0_CLIENT_ID,
  authorizationParams: {
    redirect_uri: window.location.origin,
    audience: process.env.REACT_APP_AUTH0_AUDIENCE,
    scope: 'openid profile email offline_access',
  },
  cacheLocation: 'localstorage',
};
```

### Getting Access Token for API Calls

```javascript
import { useAuth0 } from '@auth0/auth0-react';

function MyComponent() {
  const { getAccessTokenSilently } = useAuth0();

  const callApi = async () => {
    const token = await getAccessTokenSilently();

    const response = await fetch('/api/v1/applicants', {
      headers: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json',
      },
    });

    return response.json();
  };
}
```

---

## Common Issues & Solutions

### Issue 1: 403 Forbidden - "User not associated with a tenant"

**Cause:** JWT token doesn't contain `tenant_id` claim.

**Solutions:**
1. Ensure Auth0 Action is deployed and active
2. Verify user has `app_metadata.tenant_id` set
3. User may need to log out and log back in (to get new token with claims)

**Debug Steps:**
```bash
# Decode token to check claims
echo $TOKEN | cut -d'.' -f2 | base64 -d 2>/dev/null | jq .

# Look for: https://getclearance.dev/tenant_id
```

---

### Issue 2: 401 Unauthorized - "Invalid token"

**Causes:**
- Token expired
- Wrong audience
- Token signed for different API

**Solutions:**
1. Check `exp` claim in token (Unix timestamp)
2. Verify `aud` matches `AUTH0_AUDIENCE` in backend config
3. Ensure frontend requests token with correct audience

**Debug:**
```bash
# Check token audience
echo $TOKEN | cut -d'.' -f2 | base64 -d 2>/dev/null | jq '.aud'

# Should output: "https://api.getclearance.vercel.app"
```

---

### Issue 3: Token Missing Custom Claims

**Cause:** Auth0 Action not running or app_metadata not set.

**Debug Steps:**
1. Check Auth0 Dashboard → Actions → Flows → Login
2. Verify action is added to flow
3. Check user's `app_metadata` has required fields
4. Check Action logs for errors

**Test Action:**
1. Log in as user
2. Decode resulting token
3. Verify custom claims present

---

### Issue 4: CORS Errors

**Cause:** Frontend origin not in allowed list.

**Solutions:**
1. Add origin to Auth0 Application settings:
   - Allowed Callback URLs
   - Allowed Logout URLs
   - Allowed Web Origins
2. Add origin to backend CORS_ORIGINS env var

---

### Issue 5: "Unable to find signing key"

**Cause:** JWKS key rotation or caching issue.

**Solutions:**
1. Clear JWKS cache in backend (restart service)
2. Verify Auth0 is reachable from Railway
3. Check `kid` in token header matches a key in JWKS

**Debug:**
```bash
# Fetch JWKS
curl https://dev-8z4blmy3c8wvkp4k.us.auth0.com/.well-known/jwks.json | jq '.keys[].kid'

# Get kid from token
echo $TOKEN | cut -d'.' -f1 | base64 -d 2>/dev/null | jq '.kid'

# These should match
```

---

### Issue 6: SET LOCAL SQL Syntax Error (asyncpg)

**Error:**
```
asyncpg.exceptions.PostgresSyntaxError: syntax error at or near "$1"
[SQL: SET LOCAL app.current_tenant_id = $1]
```

**Cause:** PostgreSQL `SET` commands don't support parameterized queries with asyncpg.

**Solution:** Use string interpolation with UUID validation:

```python
# backend/app/database.py
async def set_tenant_context(session: AsyncSession, tenant_id: str) -> None:
    from uuid import UUID as PyUUID
    try:
        validated_uuid = str(PyUUID(tenant_id))  # Validate UUID format
    except (ValueError, TypeError):
        raise ValueError(f"Invalid tenant_id format: {tenant_id}")

    # Use string interpolation (safe because UUID is validated)
    await session.execute(
        text(f"SET LOCAL app.current_tenant_id = '{validated_uuid}'")
    )
```

---

## User Provisioning Flow

### First-Time Login (Auto-Provisioning)

```
User clicks Login
        │
        ▼
Auth0 Universal Login
        │
        ▼
User authenticates
        │
        ▼
Auth0 Action runs
        │
        ├── Has app_metadata.tenant_id? ────────▶ Add claims to token
        │                                                │
        ▼                                                ▼
No tenant_id                                      Return token
        │
        ▼
Frontend receives token
        │
        ▼
Frontend calls /api/v1/auth/provision
        │
        ▼
Backend checks database for user
        │
        ├── User exists? ────────▶ Return user info
        │
        ▼
Create tenant (if needed)
        │
        ▼
Create user record
        │
        ▼
Update Auth0 app_metadata via Management API
        │
        ▼
Return user info
        │
        ▼
User logs out and back in (gets new token with claims)
```

### Existing User Login

```
User clicks Login
        │
        ▼
Auth0 Universal Login
        │
        ▼
Auth0 Action reads app_metadata
        │
        ▼
Adds tenant_id, role, permissions to token
        │
        ▼
Frontend receives token
        │
        ▼
Frontend makes API calls with token
        │
        ▼
Backend validates token, extracts tenant_id
        │
        ▼
Queries filtered by tenant_id (multi-tenancy)
```

---

## Environment Variables Reference

### Backend (Railway)

| Variable | Required | Example |
|----------|----------|---------|
| `AUTH0_DOMAIN` | Yes | `dev-8z4blmy3c8wvkp4k.us.auth0.com` |
| `AUTH0_AUDIENCE` | Yes | `https://api.getclearance.vercel.app` |
| `AUTH0_CLIENT_ID` | Yes | `W5uDmvvRYDmw9Sm4avfEzoOxo26XF8rR` |
| `AUTH0_CLIENT_SECRET` | Yes | `<secret>` |
| `AUTH0_MGMT_CLIENT_ID` | Optional | For Management API calls |
| `AUTH0_MGMT_CLIENT_SECRET` | Optional | For Management API calls |

### Frontend (Vercel)

| Variable | Required | Example |
|----------|----------|---------|
| `REACT_APP_AUTH0_DOMAIN` | Yes | `dev-8z4blmy3c8wvkp4k.us.auth0.com` |
| `REACT_APP_AUTH0_CLIENT_ID` | Yes | `W5uDmvvRYDmw9Sm4avfEzoOxo26XF8rR` |
| `REACT_APP_AUTH0_AUDIENCE` | Yes | `https://api.getclearance.vercel.app` |

---

## Testing Auth Flow

### 1. Get Token via Browser

1. Open https://getclearance.vercel.app
2. Login with test account
3. Open DevTools → Network
4. Look for API call, copy Authorization header

### 2. Decode Token

```bash
# Paste token and decode
TOKEN="eyJhbGciOiJS..."
echo $TOKEN | cut -d'.' -f2 | base64 -d 2>/dev/null | jq .
```

### 3. Test API with Token

```bash
curl -H "Authorization: Bearer $TOKEN" \
  https://getclearance-production.up.railway.app/api/v1/applicants
```

### 4. Automated Test (Playwright)

```python
from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page()

    captured_token = None
    def capture_token(request):
        global captured_token
        auth = request.headers.get('authorization', '')
        if auth.startswith('Bearer ') and 'api' in request.url:
            captured_token = auth.replace('Bearer ', '')

    page.on('request', capture_token)
    page.goto('https://getclearance.vercel.app')

    # Login flow...
    page.fill('input[name="username"]', 'user@example.com')
    page.fill('input[name="password"]', 'password')
    page.click('button[type="submit"]')

    # Wait for API calls
    time.sleep(5)

    print(f"Token: {captured_token[:50]}...")
    browser.close()
```

---

## Useful Links

- **Auth0 Dashboard:** https://manage.auth0.com/dashboard
- **JWKS Endpoint:** https://dev-8z4blmy3c8wvkp4k.us.auth0.com/.well-known/jwks.json
- **OpenID Config:** https://dev-8z4blmy3c8wvkp4k.us.auth0.com/.well-known/openid-configuration
- **Auth0 React SDK Docs:** https://auth0.com/docs/libraries/auth0-react
- **Auth0 Actions Docs:** https://auth0.com/docs/customize/actions

---

## Quick Troubleshooting Checklist

- [ ] Auth0 Action deployed and in Login flow?
- [ ] User has `app_metadata` with `tenant_id`?
- [ ] Token contains `https://getclearance.dev/tenant_id` claim?
- [ ] Backend `AUTH0_AUDIENCE` matches frontend config?
- [ ] CORS origins configured in Auth0 Application?
- [ ] User in database `users` table with correct `tenant_id`?
- [ ] Token not expired? (check `exp` claim)
