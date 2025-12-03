# Frontend Sprint Prompts - Copy & Paste Ready
**Purpose:** Ready-to-use prompts for each frontend integration sprint
**How to Use:** Copy the entire prompt for the sprint you're starting

---

## Current Reality

The frontend has beautiful Sumsub-style UI components but is **100% mock data** with **zero backend integration**. The backend is production-ready with full APIs. These sprints connect the two.

**Backend Status:** Production-ready, deployed, most APIs working
**Frontend Status:** UI prototype only - needs API integration

---

## ✅ Backend Dashboard & Screening APIs (Sprint 0 Complete)

**Sprint 0 has been completed.** The following backend endpoints are now available:

| Endpoint | Status | Purpose |
|----------|--------|---------|
| `GET /api/v1/dashboard/stats` | ✅ Complete | KPIs (today's applicants, approved, rejected, pending) |
| `GET /api/v1/dashboard/screening-summary` | ✅ Complete | Screening hit counts by type (sanctions, PEP, adverse media) |
| `GET /api/v1/dashboard/activity` | ✅ Complete | Recent activity feed (reviews, screening hits, documents) |
| `GET /api/v1/screening/lists` | ✅ Complete | Connected list sources (OFAC, EU, UN, UK, OpenSanctions) |

**Sprint 8 (Dashboard Integration) and Sprint 5 (Screening) can now proceed.**

---

## Files to Upload to EVERY Sprint Chat

Before starting ANY sprint, upload these files:

1. `FRONTEND_AUDIT_AND_INTEGRATION_GUIDE.md` - Gap analysis and implementation patterns
2. `02_FOLDER_STRUCTURE_COMPLETE.md` - Directory tree (updated for frontend work)
3. `05_SUMSUB_CONTEXT.md` - Sumsub features we're replicating
4. `README.md` (from your getclearance repo)

**Optional but helpful:**
5. The specific component file you're working on (e.g., `ApplicantsList.jsx`)

---

## Sprint 0: Backend Dashboard & Screening List Endpoints ✅ COMPLETE

### Status: COMPLETED (2025-12-02)

**Implemented:**
- `backend/app/api/v1/dashboard.py` - New dashboard router
- `GET /api/v1/dashboard/stats` - KPI statistics with day-over-day changes
- `GET /api/v1/dashboard/screening-summary` - Screening hit counts by type
- `GET /api/v1/dashboard/activity` - Activity feed (reviews, screening, documents)
- `GET /api/v1/screening/lists` - Connected screening list sources

### Why This Sprint Existed
The frontend Dashboard and Screening pages displayed mock data because the backend endpoints didn't exist. This sprint created them.

### Files to Upload:
1. `backend/app/api/v1/` directory structure
2. `backend/app/models/` relevant models
3. `README.md` (from repo)

### Prompt (Copy This):

```
# CHAT TITLE: Backend Sprint 0 - Dashboard & Screening List Endpoints

## Context
I'm building GetClearance, an AI-native KYC/AML platform. The frontend has mock data for Dashboard KPIs, screening summary, activity feed, and connected list sources. I need to create the backend endpoints to serve real data.

**Current Repo:** https://github.com/autorevai/getclearance

## Current State
- Backend deployed on Railway with PostgreSQL
- Frontend showing hardcoded mock data for:
  - Dashboard KPIs (47 applicants, 38 approved, etc.)
  - Screening hit summary (2 sanctions, 5 PEP, 8 adverse media)
  - Recent activity feed
  - Connected List Sources (OFAC, EU, UN, UK, OpenSanctions)

## What I Need You To Create

### Part 1: Dashboard Router
**File to create:** `backend/app/api/v1/dashboard.py`

#### Endpoint 1: GET /api/v1/dashboard/stats
Returns KPI statistics for the dashboard.

**Response Schema:**
```json
{
  "today_applicants": 47,
  "today_applicants_change": 12,
  "approved": 38,
  "approved_change": 8,
  "rejected": 4,
  "rejected_change": -2,
  "pending_review": 12,
  "pending_review_change": 0
}
```

**Implementation:**
- Count applicants created today vs yesterday
- Count by status (approved, rejected, pending)
- Calculate day-over-day changes

#### Endpoint 2: GET /api/v1/dashboard/screening-summary
Returns screening hit counts by type.

**Response Schema:**
```json
{
  "sanctions_matches": 2,
  "pep_hits": 5,
  "adverse_media": 8
}
```

**Implementation:**
- Count screening_hits by hit_type
- Filter by tenant_id

#### Endpoint 3: GET /api/v1/dashboard/activity
Returns recent activity feed (last 20 items).

**Response Schema:**
```json
{
  "items": [
    {
      "type": "approved",
      "applicant_name": "Emily Park",
      "time": "2025-12-02T10:30:00Z",
      "reviewer": "You",
      "detail": null
    },
    {
      "type": "screening_hit",
      "applicant_name": "Marcus Webb",
      "time": "2025-12-02T10:15:00Z",
      "reviewer": null,
      "detail": "PEP match detected"
    }
  ]
}
```

**Implementation:**
- Query recent applicant status changes
- Query recent screening hits
- Query recent document uploads
- Merge and sort by timestamp
- Limit to 20 items

### Part 2: Screening Lists Endpoint
**File to modify:** `backend/app/api/v1/screening.py`

#### Endpoint: GET /api/v1/screening/lists
Returns connected screening list sources.

**Response Schema:**
```json
{
  "items": [
    {
      "id": "ofac",
      "name": "OFAC SDN",
      "version": "OFAC-2025-11-27",
      "last_updated": "2025-11-27T00:00:00Z",
      "entity_count": 12847
    },
    {
      "id": "opensanctions",
      "name": "OpenSanctions",
      "version": "OS-2025-12-02",
      "last_updated": "2025-12-02T06:00:00Z",
      "entity_count": 89234
    }
  ]
}
```

**Implementation:**
- Query screening_lists table
- Return all active list sources with versions and counts
- If no real lists exist, return configured defaults

### Part 3: Register Routes
**File to modify:** `backend/app/api/v1/__init__.py`

Add the dashboard router to the API.

## Architecture Constraints

**All endpoints must:**
- Use `TenantDB` dependency for multi-tenant filtering
- Use `AuthenticatedUser` dependency for auth
- Return proper Pydantic response models
- Handle empty data gracefully (return zeros, not errors)

**Dashboard stats query example:**
```python
from datetime import datetime, timedelta
from sqlalchemy import func, and_

today = datetime.utcnow().date()
yesterday = today - timedelta(days=1)

# Count today's applicants
today_count = await db.scalar(
    select(func.count(Applicant.id))
    .where(and_(
        Applicant.tenant_id == user.tenant_id,
        func.date(Applicant.created_at) == today
    ))
)

# Count yesterday's for comparison
yesterday_count = await db.scalar(
    select(func.count(Applicant.id))
    .where(and_(
        Applicant.tenant_id == user.tenant_id,
        func.date(Applicant.created_at) == yesterday
    ))
)

change = today_count - yesterday_count
```

## Success Criteria

- [ ] `GET /api/v1/dashboard/stats` returns real KPIs from database
- [ ] `GET /api/v1/dashboard/screening-summary` returns real hit counts
- [ ] `GET /api/v1/dashboard/activity` returns recent activity feed
- [ ] `GET /api/v1/screening/lists` returns list sources
- [ ] All endpoints require authentication
- [ ] All endpoints filter by tenant_id
- [ ] Empty tenant returns zeros (not errors)

## Testing

After implementation, test with curl:
```bash
# Get auth token first, then:
curl -H "Authorization: Bearer $TOKEN" \
  https://getclearance-production.up.railway.app/api/v1/dashboard/stats

curl -H "Authorization: Bearer $TOKEN" \
  https://getclearance-production.up.railway.app/api/v1/dashboard/screening-summary

curl -H "Authorization: Bearer $TOKEN" \
  https://getclearance-production.up.railway.app/api/v1/dashboard/activity

curl -H "Authorization: Bearer $TOKEN" \
  https://getclearance-production.up.railway.app/api/v1/screening/lists
```

## Questions?
If unclear about database schema or existing patterns, ask first.
```

---

## Sprint 1: Authentication Foundation (Critical - 3-5 Days)

### Files to Upload:
1. `FRONTEND_AUDIT_AND_INTEGRATION_GUIDE.md`
2. `02_FOLDER_STRUCTURE_COMPLETE.md`
3. `05_SUMSUB_CONTEXT.md`
4. `README.md` (from repo)
5. `frontend/src/App.jsx`
6. `frontend/src/index.js`

### Prompt (Copy This):

```
# CHAT TITLE: Frontend Sprint 1 - Authentication Foundation

## Context
I'm building GetClearance, an AI-native KYC/AML platform (Sumsub clone). The backend is 100% complete and deployed with Auth0 JWT authentication. The frontend is a beautiful UI prototype but has ZERO authentication - anyone can access everything.

**Current Repo:** https://github.com/autorevai/getclearance

## What Exists (Read These First)
I've uploaded context files - please read them first:

1. **FRONTEND_AUDIT_AND_INTEGRATION_GUIDE.md** - Complete gap analysis between frontend/backend
2. **02_FOLDER_STRUCTURE_COMPLETE.md** - Directory tree
3. **05_SUMSUB_CONTEXT.md** - Sumsub features we're replicating
4. **README.md** - Project README
5. **App.jsx** - Current frontend entry point (NO auth)
6. **index.js** - React entry point

**Current state:**
- Backend: Full Auth0 JWT validation + RBAC + Row-Level Security
- Frontend: No authentication whatsoever
- Risk: Anyone can see mock data (real data would be exposed)

## What I Need You To Create

### Part 1: Auth0 React Integration

**Files to create:**
1. `frontend/src/auth/AuthProvider.jsx` - Auth0 context provider
2. `frontend/src/auth/ProtectedRoute.jsx` - Route guard component
3. `frontend/src/auth/useAuth.js` - Custom hook for auth state
4. `frontend/src/auth/index.js` - Module exports

**Files to update:**
5. `frontend/src/index.js` - Wrap app with AuthProvider
6. `frontend/src/App.jsx` - Add protected routes and login flow
7. `frontend/package.json` - Add @auth0/auth0-react dependency

### Part 2: Login/Logout UI

**Files to create:**
8. `frontend/src/components/LoginPage.jsx` - Login screen with Auth0 redirect
9. `frontend/src/components/LoadingScreen.jsx` - Loading state during auth check

### Part 3: Environment Configuration

**Files to create/update:**
10. `frontend/.env` - Auth0 config for frontend (Create React App requires REACT_APP_ prefix)

**IMPORTANT:** Create React App requires the `REACT_APP_` prefix for env vars to be accessible in browser code. Create `frontend/.env` with:

```bash
# frontend/.env
# These map to your existing Auth0 config in root .env.local
REACT_APP_AUTH0_DOMAIN=dev-8z4blmy3c8wvkp4k.us.auth0.com
REACT_APP_AUTH0_CLIENT_ID=W5uDmvvRYDmw9Sm4avfEzoOxo26XF8rR
REACT_APP_AUTH0_AUDIENCE=https://api.getclearance.vercel.app
REACT_APP_API_BASE_URL=http://localhost:8000/api/v1
```

Note: The CLIENT_SECRET stays in the backend only (never expose secrets to frontend).

## Integration Requirements

### AuthProvider.jsx must:
- Wrap entire app with Auth0Provider from @auth0/auth0-react
- Configure with environment variables (domain, clientId, audience)
- Set redirect_uri to window.location.origin
- Request offline_access for refresh tokens

### ProtectedRoute.jsx must:
- Check if user is authenticated
- Redirect to login if not authenticated
- Show loading screen while checking auth state
- Pass user context to child components

### useAuth.js hook must provide:
- isAuthenticated - boolean
- isLoading - boolean
- user - user profile object
- login() - trigger Auth0 login
- logout() - trigger Auth0 logout
- getToken() - get access token for API calls

### App.jsx updates must:
- Wrap routes with AuthProvider
- Use ProtectedRoute for dashboard, applicants, screening, cases
- Allow unauthenticated access to login page only
- Show user info in AppShell header
- Add logout button to sidebar/header

## Architecture Constraints

**Auth0 Configuration (using your existing credentials):**
```javascript
// AuthProvider.jsx - uses your existing Auth0 setup
const auth0Config = {
  domain: process.env.REACT_APP_AUTH0_DOMAIN,  // dev-8z4blmy3c8wvkp4k.us.auth0.com
  clientId: process.env.REACT_APP_AUTH0_CLIENT_ID,  // W5uDmvvRYDmw9Sm4avfEzoOxo26XF8rR
  authorizationParams: {
    redirect_uri: window.location.origin,
    audience: process.env.REACT_APP_AUTH0_AUDIENCE,  // https://api.getclearance.vercel.app
    scope: 'openid profile email offline_access',
  },
  cacheLocation: 'localstorage', // Persist across page refreshes
};
```

**Token Storage:**
- Use Auth0's built-in token management (localstorage)
- Tokens will be used for all API calls in future sprints
- Access token contains tenant_id claim from backend

**Environment Variables (create frontend/.env):**
```bash
# frontend/.env
# Create React App requires REACT_APP_ prefix for browser-accessible vars
REACT_APP_AUTH0_DOMAIN=dev-8z4blmy3c8wvkp4k.us.auth0.com
REACT_APP_AUTH0_CLIENT_ID=W5uDmvvRYDmw9Sm4avfEzoOxo26XF8rR
REACT_APP_AUTH0_AUDIENCE=https://api.getclearance.vercel.app
REACT_APP_API_BASE_URL=http://localhost:8000/api/v1
```

**Why REACT_APP_ prefix?**
Create React App (which your frontend uses) only exposes env vars starting with `REACT_APP_` to the browser. This is a security feature - it prevents accidentally leaking backend secrets. Your backend `.env.local` uses `AUTH0_DOMAIN` etc., but the frontend needs its own copy with the prefix.

## Success Criteria

- [ ] Auth0 React SDK installed and configured
- [ ] Unauthenticated users redirected to login page
- [ ] Login page shows Auth0 Universal Login
- [ ] After login, user redirected to dashboard
- [ ] User info displayed in header/sidebar
- [ ] Logout button works (clears session, redirects to login)
- [ ] Protected routes block unauthenticated access
- [ ] Loading screen shows during auth check
- [ ] Environment variables documented
- [ ] No TypeScript errors (if using TS) or console errors

## Testing the Integration

After implementation:
1. Clear browser storage
2. Navigate to http://localhost:9000
3. Should redirect to login page
4. Click login -> Auth0 Universal Login appears
5. Login with test credentials
6. Redirected to dashboard with user info visible
7. Refresh page -> still logged in (token persisted)
8. Click logout -> redirected to login, session cleared
9. Try accessing /dashboard directly -> redirected to login

## Reference
See `FRONTEND_AUDIT_AND_INTEGRATION_GUIDE.md` Section 1 for code examples.

## Questions?
If unclear about Auth0 configuration or existing frontend structure, ask first.
```

---

## Sprint 2: API Service Layer (Critical - 3-4 Days)

### Files to Upload:
1. `FRONTEND_AUDIT_AND_INTEGRATION_GUIDE.md`
2. `02_FOLDER_STRUCTURE_COMPLETE.md`
3. `05_SUMSUB_CONTEXT.md`
4. `README.md` (from repo)
5. `frontend/src/auth/useAuth.js` (created in Sprint 1)

### Prompt (Copy This):

```
# CHAT TITLE: Frontend Sprint 2 - API Service Layer

## Context
I'm building GetClearance, an AI-native KYC/AML platform (Sumsub clone). Sprint 1 added Auth0 authentication. Now I need to create the API service layer that all components will use to communicate with the backend.

**Current Repo:** https://github.com/autorevai/getclearance

## What Exists (Read These First)
I've uploaded context files:

1. **FRONTEND_AUDIT_AND_INTEGRATION_GUIDE.md** - Complete API endpoint list and patterns
2. **02_FOLDER_STRUCTURE_COMPLETE.md** - Directory tree
3. **05_SUMSUB_CONTEXT.md** - Sumsub features
4. **README.md** - Project README
5. **useAuth.js** - Auth hook from Sprint 1 (has getToken())

**Current state:**
- Authentication: Working (Sprint 1)
- API calls: None - all components use mock data
- Backend APIs: All working and documented

**Backend API Structure (from README):**
```
/api/v1/applicants - Applicant CRUD
/api/v1/documents - Document upload/download
/api/v1/screening - AML screening
/api/v1/cases - Case management
/api/v1/ai - AI features
```

## What I Need You To Create

### Part 1: Core API Client

**Files to create:**
1. `frontend/src/services/api.js` - Base API client with auth headers
2. `frontend/src/services/applicants.js` - Applicant-specific API methods
3. `frontend/src/services/documents.js` - Document API methods
4. `frontend/src/services/screening.js` - Screening API methods
5. `frontend/src/services/cases.js` - Cases API methods
6. `frontend/src/services/ai.js` - AI API methods
7. `frontend/src/services/index.js` - Module exports

### Part 2: React Query Setup

**Files to create:**
8. `frontend/src/hooks/useApplicants.js` - React Query hooks for applicants
9. `frontend/src/hooks/useDocuments.js` - React Query hooks for documents
10. `frontend/src/hooks/useScreening.js` - React Query hooks for screening
11. `frontend/src/hooks/useCases.js` - React Query hooks for cases
12. `frontend/src/hooks/useAI.js` - React Query hooks for AI
13. `frontend/src/hooks/index.js` - Module exports

**Files to update:**
14. `frontend/src/index.js` - Add QueryClientProvider
15. `frontend/package.json` - Add @tanstack/react-query

### Part 3: Error Handling

**Files to create:**
16. `frontend/src/utils/errors.js` - Error handling utilities
17. `frontend/src/components/ErrorBoundary.jsx` - React error boundary

## Integration Requirements

### api.js must:
- Use environment variable for API base URL
- Get access token from Auth0 for every request
- Add Authorization: Bearer {token} header
- Add Content-Type: application/json header
- Handle 401 errors (redirect to login)
- Handle 403 errors (show permission denied)
- Handle 500 errors (show generic error)
- Support all HTTP methods (GET, POST, PATCH, DELETE)
- Parse JSON responses automatically

### Service files must:
- Import and use base API client
- Implement all endpoints from backend API
- Use proper TypeScript/JSDoc types
- Handle pagination parameters (limit, offset)
- Handle filter parameters (status, search, etc.)

### React Query hooks must:
- Use service methods for data fetching
- Configure staleTime (30 seconds default)
- Configure retry logic (3 retries with backoff)
- Return { data, isLoading, error, refetch }
- Support mutations with optimistic updates
- Invalidate queries after mutations

## Architecture Constraints

**Base API Client Pattern:**
```javascript
// services/api.js
class ApiClient {
  constructor(getToken) {
    this.baseUrl = process.env.REACT_APP_API_BASE_URL;
    this.getToken = getToken;
  }

  async request(endpoint, options = {}) {
    const token = await this.getToken();

    const response = await fetch(`${this.baseUrl}${endpoint}`, {
      ...options,
      headers: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json',
        ...options.headers,
      },
    });

    if (response.status === 401) {
      // Token expired - redirect to login
      window.location.href = '/login';
      throw new Error('Unauthorized');
    }

    if (response.status === 403) {
      throw new Error('Permission denied');
    }

    if (!response.ok) {
      const error = await response.json().catch(() => ({}));
      throw new Error(error.detail || `HTTP ${response.status}`);
    }

    return response.json();
  }

  get(endpoint) { return this.request(endpoint); }

  post(endpoint, data) {
    return this.request(endpoint, {
      method: 'POST',
      body: JSON.stringify(data),
    });
  }

  patch(endpoint, data) {
    return this.request(endpoint, {
      method: 'PATCH',
      body: JSON.stringify(data),
    });
  }

  delete(endpoint) {
    return this.request(endpoint, { method: 'DELETE' });
  }
}
```

**React Query Hook Pattern:**
```javascript
// hooks/useApplicants.js
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { useAuth } from '../auth';
import { ApplicantsService } from '../services';

export function useApplicants(filters = {}) {
  const { getToken } = useAuth();
  const service = new ApplicantsService(getToken);

  return useQuery({
    queryKey: ['applicants', filters],
    queryFn: () => service.list(filters),
    staleTime: 30000,
  });
}

export function useApplicant(id) {
  const { getToken } = useAuth();
  const service = new ApplicantsService(getToken);

  return useQuery({
    queryKey: ['applicant', id],
    queryFn: () => service.get(id),
    enabled: !!id,
  });
}

export function useReviewApplicant() {
  const { getToken } = useAuth();
  const service = new ApplicantsService(getToken);
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ id, decision, notes }) =>
      service.review(id, decision, notes),
    onSuccess: (_, { id }) => {
      queryClient.invalidateQueries(['applicant', id]);
      queryClient.invalidateQueries(['applicants']);
    },
  });
}
```

**API Methods Required:**

```javascript
// Applicants Service
list(params) // GET /applicants?status=&search=&limit=&offset=
get(id) // GET /applicants/{id}
create(data) // POST /applicants
update(id, data) // PATCH /applicants/{id}
review(id, decision, notes) // POST /applicants/{id}/review
getTimeline(id) // GET /applicants/{id}/timeline
downloadEvidence(id) // GET /applicants/{id}/evidence (returns blob)

// Documents Service
getUploadUrl(applicantId, type, fileName, contentType) // POST /documents/upload-url
confirmUpload(documentId, fileSize) // POST /documents/{id}/confirm
get(id) // GET /documents/{id}
getDownloadUrl(id) // GET /documents/{id}/download
delete(id) // DELETE /documents/{id}
analyze(id) // POST /documents/{id}/analyze

// Screening Service
runCheck(data) // POST /screening/check
listChecks(params) // GET /screening/checks
getCheck(id) // GET /screening/checks/{id}
resolveHit(hitId, resolution, notes) // PATCH /screening/hits/{id}
getHitSuggestion(hitId) // GET /screening/hits/{id}/suggestion

// Cases Service
list(params) // GET /cases
get(id) // GET /cases/{id}
create(data) // POST /cases
update(id, data) // PATCH /cases/{id}
resolve(id, resolution, notes) // POST /cases/{id}/resolve
addNote(id, content) // POST /cases/{id}/notes

// AI Service
getRiskSummary(applicantId) // GET /ai/applicants/{id}/risk-summary
regenerateRiskSummary(applicantId) // POST /ai/applicants/{id}/risk-summary
askAssistant(query, applicantId) // POST /ai/assistant
batchAnalyze(applicantIds) // POST /ai/batch-analyze
```

## Success Criteria

- [ ] Base API client created with auth headers
- [ ] All 5 service files created with all methods
- [ ] React Query installed and configured
- [ ] All React Query hooks created
- [ ] Error handling works (401 redirects, errors displayed)
- [ ] Can make authenticated API calls from console
- [ ] No TypeScript/JSDoc errors
- [ ] Services are testable (dependency injection for getToken)

## Testing the Integration

After implementation:
```javascript
// In browser console (logged in):
const { getToken } = window.__AUTH__;  // Expose for testing
const api = new ApiClient(getToken);

// Test API call
const applicants = await api.get('/applicants');
console.log(applicants);  // Should show real data from backend
```

## Reference
See `FRONTEND_AUDIT_AND_INTEGRATION_GUIDE.md` Section 2-3 for full patterns.

## Questions?
If unclear about backend API structure or authentication, ask first.
```

---

## Sprint 3: Applicants Module Integration (Critical - 5-7 Days)

### Files to Upload:
1. `FRONTEND_AUDIT_AND_INTEGRATION_GUIDE.md`
2. `02_FOLDER_STRUCTURE_COMPLETE.md`
3. `05_SUMSUB_CONTEXT.md`
4. `README.md` (from repo)
5. `frontend/src/components/ApplicantsList.jsx`
6. `frontend/src/components/ApplicantDetail.jsx`
7. `frontend/src/hooks/useApplicants.js` (created in Sprint 2)

### Prompt (Copy This):

```
# CHAT TITLE: Frontend Sprint 3 - Applicants Module Integration

## Context
I'm building GetClearance, an AI-native KYC/AML platform (Sumsub clone). Sprints 1-2 added authentication and API services. Now I need to connect the Applicants UI to the real backend API.

**Current Repo:** https://github.com/autorevai/getclearance

## What Exists (Read These First)
I've uploaded context files:

1. **FRONTEND_AUDIT_AND_INTEGRATION_GUIDE.md** - Implementation patterns
2. **02_FOLDER_STRUCTURE_COMPLETE.md** - Directory tree
3. **05_SUMSUB_CONTEXT.md** - Sumsub features
4. **README.md** - Project README
5. **ApplicantsList.jsx** - Current UI (uses mockApplicants)
6. **ApplicantDetail.jsx** - Current UI (uses mockApplicant)
7. **useApplicants.js** - React Query hooks from Sprint 2

**Current state:**
- Authentication: Working (Sprint 1)
- API Layer: Working (Sprint 2)
- ApplicantsList.jsx: Shows mock data (hardcoded array)
- ApplicantDetail.jsx: Shows mock data (hardcoded object)

## What I Need You To Do

### Part 1: Update ApplicantsList.jsx

**Changes needed:**
1. Remove mockApplicants array
2. Import and use useApplicants() hook
3. Show loading skeleton while fetching
4. Show error state if API fails
5. Connect filters (status, risk_level, search) to API params
6. Connect pagination to API params (limit, offset)
7. Make table rows clickable to navigate to detail
8. Connect "New Applicant" button to create flow

### Part 2: Update ApplicantDetail.jsx

**Changes needed:**
1. Remove mockApplicant object
2. Import and use useApplicant(id) hook
3. Get applicant ID from URL params (react-router)
4. Show loading skeleton while fetching
5. Show 404 error if applicant not found
6. Connect Approve/Reject buttons to useReviewApplicant()
7. Connect "Download Evidence" button to API
8. Show real AI risk summary using useAI hook
9. Show real timeline using getTimeline()

### Part 3: Create New Applicant Flow

**Files to create:**
1. `frontend/src/components/CreateApplicantModal.jsx` - Modal form to create applicant

**Changes needed:**
2. Add modal trigger to ApplicantsList
3. Form submits to API, then refreshes list

### Part 4: Routing Setup

**Files to update:**
4. `frontend/src/App.jsx` - Add react-router routes for applicant detail

**Changes needed:**
- /applicants -> ApplicantsList
- /applicants/:id -> ApplicantDetail

## Integration Requirements

### ApplicantsList must:
- Use useApplicants() hook for data
- Pass filter state to hook: { status, risk_level, search, limit, offset }
- Show skeleton rows during loading
- Show error message with retry button on failure
- Update URL params when filters change (for shareable links)
- Show total count and pagination
- Navigate to /applicants/:id on row click

### ApplicantDetail must:
- Get ID from useParams() hook
- Use useApplicant(id) hook for data
- Use useAI().getRiskSummary(id) for AI insights
- Show loading skeleton while fetching
- Show 404 page if applicant not found (API returns 404)
- Approve button calls: reviewMutation.mutate({ id, decision: 'approved' })
- Reject button calls: reviewMutation.mutate({ id, decision: 'rejected' })
- Download evidence button calls API and triggers download

### CreateApplicantModal must:
- Form fields: email, first_name, last_name, date_of_birth, nationality
- Submit button calls useCreateApplicant() mutation
- On success: close modal, refetch applicants list
- On error: show error message in modal
- Loading state on submit button

## Architecture Constraints

**Component Pattern:**
```jsx
// ApplicantsList.jsx
import { useApplicants } from '../hooks/useApplicants';
import { LoadingSkeleton, ErrorState } from './shared';

export default function ApplicantsList() {
  const [filters, setFilters] = useState({
    status: null,
    risk_level: null,
    search: '',
    limit: 50,
    offset: 0,
  });

  const { data, isLoading, error, refetch } = useApplicants(filters);

  if (isLoading) return <LoadingSkeleton rows={10} />;
  if (error) return <ErrorState message={error.message} onRetry={refetch} />;

  return (
    <div>
      {/* Filters connected to setFilters */}
      {/* Table using data.items */}
      {/* Pagination using data.total, data.limit, data.offset */}
    </div>
  );
}
```

**Detail Page Pattern:**
```jsx
// ApplicantDetail.jsx
import { useParams, useNavigate } from 'react-router-dom';
import { useApplicant, useReviewApplicant } from '../hooks/useApplicants';
import { useRiskSummary } from '../hooks/useAI';

export default function ApplicantDetail() {
  const { id } = useParams();
  const navigate = useNavigate();

  const { data: applicant, isLoading, error } = useApplicant(id);
  const { data: riskSummary } = useRiskSummary(id);
  const reviewMutation = useReviewApplicant();

  if (isLoading) return <DetailSkeleton />;
  if (error?.message?.includes('404')) return <NotFound />;
  if (error) return <ErrorState message={error.message} />;

  const handleApprove = () => {
    reviewMutation.mutate(
      { id, decision: 'approved' },
      { onSuccess: () => navigate('/applicants') }
    );
  };

  return (
    <div>
      {/* Applicant info using `applicant` */}
      {/* AI summary using `riskSummary` */}
      {/* Action buttons with handlers */}
    </div>
  );
}
```

**Evidence Download Pattern:**
```javascript
const handleDownloadEvidence = async () => {
  setDownloading(true);
  try {
    const blob = await applicantsService.downloadEvidence(id);
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `evidence_${applicant.first_name}_${applicant.last_name}.pdf`;
    a.click();
    window.URL.revokeObjectURL(url);
  } finally {
    setDownloading(false);
  }
};
```

## Success Criteria

- [ ] ApplicantsList shows real data from API
- [ ] Filters work (status, risk, search)
- [ ] Pagination works (can navigate pages)
- [ ] Loading skeleton shows during fetch
- [ ] Error state shows with retry button
- [ ] Clicking row navigates to detail page
- [ ] ApplicantDetail shows real applicant data
- [ ] AI risk summary shows real data
- [ ] Approve/Reject buttons work (status changes)
- [ ] Evidence download works (PDF downloads)
- [ ] Create applicant modal works
- [ ] URL reflects current applicant (/applicants/:id)

## Testing Checklist

After implementation:
1. Login and navigate to /applicants
2. Verify real data loads (not mock data)
3. Try each filter - verify list updates
4. Search for an applicant name - verify results
5. Click pagination - verify page changes
6. Click applicant row - verify detail page loads
7. On detail page, verify AI summary loads
8. Click Approve - verify status changes to "approved"
9. Click Download Evidence - verify PDF downloads
10. Click "New Applicant" - fill form - verify created in list

## Reference
See `FRONTEND_AUDIT_AND_INTEGRATION_GUIDE.md` Section 4 for component patterns.

## Questions?
If unclear about routing setup or existing component structure, ask first.
```

---

## Sprint 4: Document Upload Integration (High - 4-5 Days)

### Files to Upload:
1. `FRONTEND_AUDIT_AND_INTEGRATION_GUIDE.md`
2. `02_FOLDER_STRUCTURE_COMPLETE.md`
3. `05_SUMSUB_CONTEXT.md`
4. `README.md` (from repo)
5. `frontend/src/components/ApplicantDetail.jsx` (updated in Sprint 3)
6. `frontend/src/services/documents.js` (created in Sprint 2)

### Prompt (Copy This):

```
# CHAT TITLE: Frontend Sprint 4 - Document Upload Integration

## Context
I'm building GetClearance, an AI-native KYC/AML platform (Sumsub clone). Sprints 1-3 added auth, API layer, and applicants integration. Now I need document upload functionality for KYC verification.

**Current Repo:** https://github.com/autorevai/getclearance

## What Exists (Read These First)
I've uploaded context files:

1. **FRONTEND_AUDIT_AND_INTEGRATION_GUIDE.md** - Document upload patterns
2. **02_FOLDER_STRUCTURE_COMPLETE.md** - Directory tree
3. **05_SUMSUB_CONTEXT.md** - Document verification requirements
4. **README.md** - Project README
5. **ApplicantDetail.jsx** - Applicant detail (needs document section)
6. **documents.js** - Document service (has upload methods)

**Current state:**
- Applicant detail page working with real data
- Document upload UI exists but doesn't work
- Backend has presigned URL upload flow ready

**Backend Document Flow:**
1. Frontend requests presigned upload URL
2. Backend returns URL + document_id
3. Frontend uploads directly to R2 (Cloudflare storage)
4. Frontend confirms upload with backend
5. Backend triggers OCR/processing

## What I Need You To Create

### Part 1: Document Upload Component

**Files to create:**
1. `frontend/src/components/DocumentUpload.jsx` - Drag & drop upload component
2. `frontend/src/components/DocumentList.jsx` - Display uploaded documents
3. `frontend/src/components/DocumentPreview.jsx` - View/download document

### Part 2: Document Hooks

**Files to create:**
4. `frontend/src/hooks/useDocuments.js` - React Query hooks (if not in Sprint 2)

### Part 3: Integration with Applicant Detail

**Files to update:**
5. `frontend/src/components/ApplicantDetail.jsx` - Add Documents tab with upload

## Integration Requirements

### DocumentUpload.jsx must:
- Accept drag & drop files
- Accept click to select files
- Show file type validation (images, PDFs only)
- Show file size validation (max 50MB)
- Display upload progress (0-100%)
- Support multiple document types (passport, id_card, driver_license, utility_bill)
- Call presigned URL flow on upload
- Show success/error states
- Call analyze endpoint after successful upload

### DocumentList.jsx must:
- Display all documents for an applicant
- Show document type, status, upload date
- Show OCR confidence score
- Show extracted data (name, DOB, document number)
- Show fraud signals if any
- Allow download via presigned URL
- Allow delete (with confirmation)

### DocumentPreview.jsx must:
- Open in modal/slide-over
- Show document image/PDF
- Show extracted OCR text
- Show AI analysis results
- Show verification checks (pass/fail)

### Upload Flow Implementation:
```javascript
async function uploadDocument(file, applicantId, documentType) {
  // 1. Get presigned upload URL from backend
  const { upload_url, document_id, key } = await documentsService.getUploadUrl(
    applicantId,
    documentType,
    file.name,
    file.type
  );

  // 2. Upload directly to R2
  await uploadToR2(upload_url, file, (progress) => {
    setUploadProgress(progress);
  });

  // 3. Confirm upload with backend
  await documentsService.confirmUpload(document_id, file.size);

  // 4. Trigger AI analysis
  await documentsService.analyze(document_id);

  return document_id;
}

async function uploadToR2(url, file, onProgress) {
  return new Promise((resolve, reject) => {
    const xhr = new XMLHttpRequest();

    xhr.upload.onprogress = (e) => {
      if (e.lengthComputable) {
        onProgress(Math.round((e.loaded / e.total) * 100));
      }
    };

    xhr.onload = () => {
      if (xhr.status >= 200 && xhr.status < 300) {
        resolve();
      } else {
        reject(new Error(`Upload failed: ${xhr.status}`));
      }
    };

    xhr.onerror = () => reject(new Error('Upload failed'));

    xhr.open('PUT', url);
    xhr.setRequestHeader('Content-Type', file.type);
    xhr.send(file);
  });
}
```

## Architecture Constraints

**DocumentUpload Component Pattern:**
```jsx
export default function DocumentUpload({ applicantId, onUploadComplete }) {
  const [uploading, setUploading] = useState(false);
  const [progress, setProgress] = useState(0);
  const [error, setError] = useState(null);
  const [documentType, setDocumentType] = useState('passport');

  const handleFileSelect = async (files) => {
    const file = files[0];

    // Validate
    if (file.size > 50 * 1024 * 1024) {
      setError('File too large (max 50MB)');
      return;
    }

    if (!['image/jpeg', 'image/png', 'application/pdf'].includes(file.type)) {
      setError('Invalid file type (JPEG, PNG, PDF only)');
      return;
    }

    setUploading(true);
    setError(null);

    try {
      const documentId = await uploadDocument(file, applicantId, documentType);
      onUploadComplete?.(documentId);
    } catch (err) {
      setError(err.message);
    } finally {
      setUploading(false);
      setProgress(0);
    }
  };

  return (
    <div className="document-upload">
      <select value={documentType} onChange={(e) => setDocumentType(e.target.value)}>
        <option value="passport">Passport</option>
        <option value="driver_license">Driver's License</option>
        <option value="id_card">ID Card</option>
        <option value="utility_bill">Utility Bill</option>
      </select>

      <div
        className="drop-zone"
        onDrop={handleDrop}
        onDragOver={handleDragOver}
      >
        {uploading ? (
          <ProgressBar progress={progress} />
        ) : (
          <p>Drag & drop or click to upload</p>
        )}
      </div>

      {error && <ErrorMessage message={error} />}
    </div>
  );
}
```

**Document Status Display:**
```jsx
const statusConfig = {
  pending: { label: 'Pending', color: 'gray' },
  processing: { label: 'Processing', color: 'blue' },
  verified: { label: 'Verified', color: 'green' },
  failed: { label: 'Failed', color: 'red' },
  pending_review: { label: 'Pending Review', color: 'yellow' },
};
```

## Success Criteria

- [ ] DocumentUpload component accepts drag & drop
- [ ] DocumentUpload validates file type and size
- [ ] Upload progress bar works (0-100%)
- [ ] Presigned URL flow works (upload directly to R2)
- [ ] Upload confirmation sent to backend
- [ ] AI analysis triggered after upload
- [ ] DocumentList shows all applicant documents
- [ ] Documents show status (processing, verified, failed)
- [ ] Documents show extracted OCR data
- [ ] Documents show fraud signals
- [ ] Document download works (via presigned URL)
- [ ] Document delete works (with confirmation)
- [ ] Preview modal shows document image/PDF
- [ ] Preview shows AI analysis results

## Testing Checklist

After implementation:
1. Navigate to applicant detail page
2. Click Documents tab
3. Select document type (passport)
4. Drag & drop a passport image
5. Verify progress bar shows upload progress
6. Verify document appears in list with "processing" status
7. Wait for processing to complete
8. Verify status changes to "verified" or "pending_review"
9. Verify OCR extracted data shows (name, DOB, etc.)
10. Click document to preview
11. Verify image and analysis results show
12. Click download - verify file downloads
13. Test with invalid file (too large, wrong type) - verify error shows

## Reference
See `FRONTEND_AUDIT_AND_INTEGRATION_GUIDE.md` Section 5 for upload patterns.

## Questions?
If unclear about presigned URL flow or document types, ask first.
```

---

## Sprint 5: Screening Module Integration (High - 4-5 Days)

### Files to Upload:
1. `FRONTEND_AUDIT_AND_INTEGRATION_GUIDE.md`
2. `02_FOLDER_STRUCTURE_COMPLETE.md`
3. `05_SUMSUB_CONTEXT.md`
4. `README.md` (from repo)
5. `frontend/src/components/ScreeningChecks.jsx`
6. `frontend/src/services/screening.js` (created in Sprint 2)

### Prompt (Copy This):

```
# CHAT TITLE: Frontend Sprint 5 - Screening Module Integration

## Context
I'm building GetClearance, an AI-native KYC/AML platform (Sumsub clone). Sprints 1-4 added auth, API layer, applicants, and document upload. Now I need to connect the AML screening UI to the backend.

**Current Repo:** https://github.com/autorevai/getclearance

## What Exists (Read These First)
I've uploaded context files:

1. **FRONTEND_AUDIT_AND_INTEGRATION_GUIDE.md** - Screening patterns
2. **02_FOLDER_STRUCTURE_COMPLETE.md** - Directory tree
3. **05_SUMSUB_CONTEXT.md** - AML screening requirements (CRITICAL)
4. **README.md** - Project README
5. **ScreeningChecks.jsx** - Current UI (uses mockChecks)
6. **screening.js** - Screening service

**Current state:**
- ScreeningChecks.jsx shows beautiful UI with mock data
- mockChecks array has hardcoded screening results
- "Run New Check" button does nothing
- "Mark as Clear" / "Confirm Match" buttons do nothing

**Backend Screening API:**
- POST /screening/check - Run new screening
- GET /screening/checks - List all checks
- GET /screening/checks/{id} - Get check with hits
- PATCH /screening/hits/{id} - Resolve hit
- GET /screening/hits/{id}/suggestion - AI suggestion

## What I Need You To Do

### Part 1: Update ScreeningChecks.jsx

**Changes needed:**
1. Remove mockChecks array
2. Remove mockListSources array
3. Import and use useScreeningChecks() hook
4. Connect filters (all, hits, pending) to API
5. Show loading skeleton while fetching
6. Show error state if API fails

### Part 2: Connect "Run New Check" Modal

**Changes needed:**
1. Modal form submits to runScreening() API
2. Show loading state during check
3. On success, refresh checks list and show result
4. On error, show error message

### Part 3: Connect Hit Resolution

**Changes needed:**
1. "Mark as Clear" button calls resolveHit(id, 'confirmed_false')
2. "Confirm Match" button calls resolveHit(id, 'confirmed_true')
3. Show loading state during resolution
4. On success, update hit status in UI
5. Show AI suggestion before resolution (via getHitSuggestion)

### Part 4: Create Screening Hooks

**Files to create/update:**
1. `frontend/src/hooks/useScreening.js` - Add all screening hooks

## Integration Requirements

### ScreeningChecks must:
- Use useScreeningChecks() for main list
- Filter by status (all, hit, pending_review)
- Show real hit count and confidence scores
- Show real list sources and versions
- Click check to open detail panel
- Detail panel shows real hits from API

### "Run New Check" must:
- Form fields: entity_type (individual/company), name, country, date_of_birth
- Submit calls screening.runCheck({ name, country, date_of_birth, check_types: ['sanctions', 'pep'] })
- Show loading spinner during check (can take 5-10 seconds)
- On completion, show result (clear or hit count)
- Close modal and refresh list

### Hit Resolution must:
- Before user decides, fetch AI suggestion: getHitSuggestion(hitId)
- Display AI recommendation with confidence
- "Mark as Clear" resolves as false positive
- "Confirm Match" resolves as true positive
- Resolution updates applicant flags if true positive
- Show confirmation toast on success

### AI Suggestion Display:
```jsx
// In the hit detail panel
const { data: suggestion, isLoading } = useHitSuggestion(hitId);

{suggestion && (
  <div className="ai-review-section">
    <div className="ai-review-header">
      <Sparkles /> AI Recommendation
    </div>
    <div className="ai-review-text">
      {suggestion.reasoning}
    </div>
    <div>
      Suggested: <strong>{suggestion.suggested_resolution}</strong>
      ({Math.round(suggestion.confidence * 100)}% confidence)
    </div>
  </div>
)}
```

## Architecture Constraints

**Component Updates:**
```jsx
// ScreeningChecks.jsx
import { useScreeningChecks, useRunScreening, useResolveHit } from '../hooks/useScreening';

export default function ScreeningChecks() {
  const [activeFilter, setActiveFilter] = useState('all');
  const [selectedCheck, setSelectedCheck] = useState(null);

  // Map UI filter to API filter
  const apiFilter = activeFilter === 'all' ? {}
    : activeFilter === 'hits' ? { status: 'hit' }
    : { status: 'pending_review' };

  const { data, isLoading, error } = useScreeningChecks(apiFilter);
  const runScreeningMutation = useRunScreening();
  const resolveHitMutation = useResolveHit();

  if (isLoading) return <ScreeningSkeleton />;
  if (error) return <ErrorState message={error.message} />;

  const handleRunCheck = async (formData) => {
    try {
      const result = await runScreeningMutation.mutateAsync(formData);
      setShowNewCheck(false);
      if (result.hit_count > 0) {
        toast.warning(`${result.hit_count} potential matches found`);
      } else {
        toast.success('Screening clear - no matches found');
      }
    } catch (err) {
      toast.error(`Screening failed: ${err.message}`);
    }
  };

  const handleResolveHit = async (hitId, resolution) => {
    try {
      await resolveHitMutation.mutateAsync({ hitId, resolution });
      toast.success(`Hit marked as ${resolution}`);
    } catch (err) {
      toast.error(`Resolution failed: ${err.message}`);
    }
  };

  return (
    // Existing UI, but using data.items instead of mockChecks
  );
}
```

**Stats Row (real data):**
```jsx
// Calculate stats from real data
const stats = useMemo(() => ({
  pendingReview: data?.items.filter(c => c.match_status === 'pending_review').length || 0,
  totalHits: data?.items.filter(c => c.status === 'hit').length || 0,
  truePositives: data?.items.filter(c => c.match_status === 'confirmed_true').length || 0,
  checksToday: data?.items.filter(c => isToday(c.created_at)).length || 0,
}), [data]);
```

## Success Criteria

- [ ] ScreeningChecks shows real data from API
- [ ] Filter tabs work (all, hits, pending review)
- [ ] Stats row shows real counts
- [ ] Loading skeleton shows during fetch
- [ ] Error state shows with retry button
- [ ] "Run New Check" modal submits to API
- [ ] Check runs and shows result (hit count or clear)
- [ ] List refreshes after running check
- [ ] Click check opens detail panel with real hits
- [ ] Detail panel shows AI suggestion
- [ ] "Mark as Clear" resolves hit as false positive
- [ ] "Confirm Match" resolves hit as true positive
- [ ] Resolution updates hit status in UI
- [ ] List sources show real data (version, entity count)

## Testing Checklist

After implementation:
1. Navigate to /screening
2. Verify real data loads (not mock data)
3. Click filter tabs - verify list updates
4. Verify stats show correct counts
5. Click "Run New Check"
6. Enter name: "Vladimir Putin" (known sanctions hit)
7. Submit and wait for result
8. Verify hit is found and displayed
9. Click the new check in list
10. Verify detail panel shows hit with AI suggestion
11. Click "Mark as Clear" - verify status updates
12. Run another check with a common name - verify clear result
13. Check list sources section shows real data

## Reference
See `FRONTEND_AUDIT_AND_INTEGRATION_GUIDE.md` for screening patterns.
See `05_SUMSUB_CONTEXT.md` Section 7 for AML screening requirements.

## Questions?
If unclear about hit resolution flow or screening API, ask first.
```

---

## Sprint 6: Case Management & AI Integration (Medium - 4-5 Days)

### Files to Upload:
1. `FRONTEND_AUDIT_AND_INTEGRATION_GUIDE.md`
2. `02_FOLDER_STRUCTURE_COMPLETE.md`
3. `05_SUMSUB_CONTEXT.md`
4. `README.md` (from repo)
5. `frontend/src/components/CaseManagement.jsx`
6. `frontend/src/components/ApplicantAssistant.jsx`

### Prompt (Copy This):

```
# CHAT TITLE: Frontend Sprint 6 - Case Management & AI Integration

## Context
I'm building GetClearance, an AI-native KYC/AML platform (Sumsub clone). Sprints 1-5 added auth, API layer, applicants, documents, and screening. Now I need to connect Case Management and the AI Assistant to the backend.

**Current Repo:** https://github.com/autorevai/getclearance

## What Exists (Read These First)
I've uploaded context files:

1. **FRONTEND_AUDIT_AND_INTEGRATION_GUIDE.md** - Case and AI patterns
2. **02_FOLDER_STRUCTURE_COMPLETE.md** - Directory tree
3. **05_SUMSUB_CONTEXT.md** - Case management requirements
4. **README.md** - Project README
5. **CaseManagement.jsx** - Current UI (uses mockCases)
6. **ApplicantAssistant.jsx** - Current UI (uses fake generateResponse)

**Current state:**
- CaseManagement.jsx shows mock cases
- Create Case button does nothing
- Add Note button does nothing
- Resolve buttons do nothing
- ApplicantAssistant.jsx has hardcoded responses
- AI doesn't call real Claude API

## What I Need You To Do

### Part 1: Update CaseManagement.jsx

**Changes needed:**
1. Remove mockCases array
2. Import and use useCases() hook
3. Connect filters (open, in_progress, resolved, escalated) to API
4. Connect "Create Case" button to API
5. Connect "Add Note" to addNote() API
6. Connect "Clear" / "Escalate" buttons to resolveCase() API
7. Show real AI summary in detail panel
8. Show loading and error states

### Part 2: Update ApplicantAssistant.jsx

**Changes needed:**
1. Remove generateResponse() function (hardcoded)
2. Import and use useAssistant() hook
3. Connect send button to askAssistant() API
4. Show real AI responses from Claude
5. Handle loading state (typing indicator)
6. Handle errors gracefully

### Part 3: Create Hooks

**Files to create/update:**
1. `frontend/src/hooks/useCases.js` - Case management hooks
2. `frontend/src/hooks/useAI.js` - Add askAssistant hook

## Integration Requirements

### CaseManagement must:
- Use useCases() for main list
- Filter by status (open, in_progress, resolved, escalated, all)
- Sort by priority and due date
- Click case to select and show detail panel
- Detail panel shows:
  - Subject (linked applicant)
  - AI Summary (from backend AI analysis)
  - Notes (real notes from API)
  - Action buttons

### Case Actions must:
- "Create Case" opens modal, submits to POST /cases
- "Add Note" calls POST /cases/{id}/notes
- "Clear" calls POST /cases/{id}/resolve with resolution: 'cleared'
- "Escalate" calls POST /cases/{id}/resolve with resolution: 'escalated'

### ApplicantAssistant must:
- Send messages to POST /ai/assistant
- Include applicant_id if viewing applicant detail
- Display real Claude responses
- Show typing indicator during API call
- Handle errors (show friendly message)
- Multi-language support (pass language preference)

### AI Response Format:
```javascript
// API request
const response = await aiService.askAssistant({
  query: "What documents do I need?",
  applicant_id: applicantId, // optional - for context
});

// API response
{
  response: "For verification, you'll need...",
  generated_at: "2025-12-01T12:00:00Z"
}
```

## Architecture Constraints

**CaseManagement Updates:**
```jsx
import { useCases, useCreateCase, useResolveCase, useAddNote } from '../hooks/useCases';

export default function CaseManagement() {
  const [activeFilter, setActiveFilter] = useState('open');
  const [selectedCase, setSelectedCase] = useState(null);
  const [noteText, setNoteText] = useState('');

  const statusFilter = activeFilter === 'all' ? {} : { status: activeFilter };
  const { data, isLoading, error } = useCases(statusFilter);

  const createCaseMutation = useCreateCase();
  const resolveCaseMutation = useResolveCase();
  const addNoteMutation = useAddNote();

  const handleCreateCase = async (formData) => {
    await createCaseMutation.mutateAsync(formData);
    setShowCreateModal(false);
  };

  const handleResolve = async (resolution) => {
    await resolveCaseMutation.mutateAsync({
      caseId: selectedCase.id,
      resolution,
      notes: null,
    });
    setSelectedCase(null);
  };

  const handleAddNote = async () => {
    if (!noteText.trim()) return;
    await addNoteMutation.mutateAsync({
      caseId: selectedCase.id,
      content: noteText,
    });
    setNoteText('');
    // Refetch case to show new note
  };

  // ... rest of component
}
```

**ApplicantAssistant Updates:**
```jsx
import { useAskAssistant } from '../hooks/useAI';

export default function ApplicantAssistant({ applicantId }) {
  const [messages, setMessages] = useState([
    { role: 'assistant', content: "Hi! How can I help you today?" }
  ]);
  const [inputValue, setInputValue] = useState('');

  const askAssistantMutation = useAskAssistant();

  const handleSend = async () => {
    if (!inputValue.trim()) return;

    // Add user message
    setMessages(prev => [...prev, { role: 'user', content: inputValue }]);
    const query = inputValue;
    setInputValue('');

    try {
      const response = await askAssistantMutation.mutateAsync({
        query,
        applicant_id: applicantId,
      });

      setMessages(prev => [...prev, {
        role: 'assistant',
        content: response.response,
        timestamp: new Date(response.generated_at),
      }]);
    } catch (error) {
      setMessages(prev => [...prev, {
        role: 'assistant',
        content: "I'm sorry, I encountered an error. Please try again.",
      }]);
    }
  };

  return (
    <div className="applicant-assistant">
      {/* Messages display */}
      {messages.map((msg, i) => (
        <MessageBubble key={i} message={msg} />
      ))}

      {/* Typing indicator */}
      {askAssistantMutation.isLoading && <TypingIndicator />}

      {/* Input */}
      <input
        value={inputValue}
        onChange={(e) => setInputValue(e.target.value)}
        onKeyDown={(e) => e.key === 'Enter' && handleSend()}
        disabled={askAssistantMutation.isLoading}
      />
    </div>
  );
}
```

## Success Criteria

### Case Management:
- [ ] Shows real cases from API
- [ ] Filter tabs work
- [ ] Stats show real counts
- [ ] Create Case modal works
- [ ] Add Note works (note appears in list)
- [ ] Clear/Escalate buttons work
- [ ] Detail panel shows real data
- [ ] AI summary shows real analysis

### AI Assistant:
- [ ] Sends messages to real AI API
- [ ] Shows Claude responses (not hardcoded)
- [ ] Typing indicator shows during API call
- [ ] Handles errors gracefully
- [ ] Suggested questions work
- [ ] Context-aware (knows applicant status if provided)

## Testing Checklist

### Case Management:
1. Navigate to /cases
2. Verify real cases load (or empty state if none)
3. Click "Create Case" and fill form
4. Submit - verify case appears in list
5. Click case to select
6. Type note and click send - verify note appears
7. Click "Clear" - verify case status changes
8. Click "Escalate" on another case - verify status changes

### AI Assistant:
1. Navigate to AI assistant (or applicant detail with assistant)
2. Type "What documents do I need?"
3. Verify typing indicator shows
4. Verify response from Claude (not hardcoded)
5. Ask "Why was my document rejected?"
6. Verify context-aware response
7. Test error handling (disconnect network, verify graceful error)

## Reference
See `FRONTEND_AUDIT_AND_INTEGRATION_GUIDE.md` for patterns.

## Questions?
If unclear about case workflow or AI integration, ask first.
```

---

## Sprint 7: Polish, Error Handling & Real-time Updates (Medium - 3-4 Days)

### Files to Upload:
1. `FRONTEND_AUDIT_AND_INTEGRATION_GUIDE.md`
2. `02_FOLDER_STRUCTURE_COMPLETE.md`
3. `README.md` (from repo)
4. Any components that need polish

### Prompt (Copy This):

```
# CHAT TITLE: Frontend Sprint 7 - Polish & Real-time Updates

## Context
I'm building GetClearance, an AI-native KYC/AML platform (Sumsub clone). Sprints 1-6 connected all UI components to the backend. Now I need to add polish: error boundaries, loading states, toast notifications, and real-time updates.

**Current Repo:** https://github.com/autorevai/getclearance

## What Exists (Read These First)
I've uploaded context files:

1. **FRONTEND_AUDIT_AND_INTEGRATION_GUIDE.md** - Polish requirements
2. **02_FOLDER_STRUCTURE_COMPLETE.md** - Directory tree
3. **README.md** - Project README

**Current state:**
- All components connected to backend APIs
- Basic loading/error states exist
- No toast notifications
- No WebSocket real-time updates
- Error handling is inconsistent

## What I Need You To Create

### Part 1: Toast Notifications

**Files to create:**
1. `frontend/src/components/ToastProvider.jsx` - Toast context and provider
2. `frontend/src/hooks/useToast.js` - Hook to trigger toasts

**Changes needed:**
3. Add toast calls after all mutations (create, update, delete, resolve)
4. Add error toasts for API failures

### Part 2: Consistent Loading States

**Files to create:**
5. `frontend/src/components/shared/LoadingSkeleton.jsx` - Skeleton components
6. `frontend/src/components/shared/LoadingSpinner.jsx` - Spinner component

**Changes needed:**
7. Add skeletons to all list views
8. Add spinners to all buttons during mutations

### Part 3: Error Boundaries

**Files to create:**
9. `frontend/src/components/ErrorBoundary.jsx` - React error boundary
10. `frontend/src/components/shared/ErrorState.jsx` - Error display component
11. `frontend/src/components/shared/NotFound.jsx` - 404 page

**Changes needed:**
12. Wrap main app sections with ErrorBoundary
13. Add consistent error states to all data-fetching components

### Part 4: WebSocket Real-time Updates (Optional)

**Files to create:**
14. `frontend/src/hooks/useRealtimeUpdates.js` - WebSocket hook

**Changes needed:**
15. Invalidate queries when events received
16. Show notification when applicant status changes

### Part 5: Permission-based UI

**Changes needed:**
17. Hide/disable buttons user doesn't have permission for
18. Show appropriate message for denied actions

## Integration Requirements

### Toast Notifications:
- Success: Green, auto-dismiss after 3 seconds
- Error: Red, dismiss on click or after 5 seconds
- Warning: Yellow, for potential issues
- Info: Blue, for neutral notifications

### Loading Skeletons:
- Match the shape of actual content
- Subtle pulse animation
- Replace actual content during loading

### Error States:
- Friendly error message
- Retry button that refetches data
- Link to support for persistent errors

### WebSocket Events (from backend):
```javascript
// Event types to listen for:
'applicant.created'
'applicant.updated'
'applicant.reviewed'
'screening.completed'
'document.processed'
'case.created'
'case.resolved'
```

### Permission Checks:
```javascript
// User permissions from Auth0 token
const permissions = [
  'read:applicants',
  'write:applicants',
  'review:applicants',
  'read:screening',
  'review:screening',
  'read:cases',
  'write:cases',
  'review:cases',
];

// Use in components
const { user } = useAuth();
const canReview = user.permissions.includes('review:applicants');

{canReview && <ApproveButton />}
```

## Architecture Constraints

**Toast Provider Pattern:**
```jsx
// ToastProvider.jsx
import { createContext, useContext, useState } from 'react';

const ToastContext = createContext();

export function ToastProvider({ children }) {
  const [toasts, setToasts] = useState([]);

  const addToast = (message, type = 'info') => {
    const id = Date.now();
    setToasts(prev => [...prev, { id, message, type }]);
    setTimeout(() => removeToast(id), type === 'error' ? 5000 : 3000);
  };

  const removeToast = (id) => {
    setToasts(prev => prev.filter(t => t.id !== id));
  };

  return (
    <ToastContext.Provider value={{ addToast }}>
      {children}
      <ToastContainer toasts={toasts} onRemove={removeToast} />
    </ToastContext.Provider>
  );
}

export const useToast = () => useContext(ToastContext);
```

**Usage in mutations:**
```jsx
const reviewMutation = useReviewApplicant();
const { addToast } = useToast();

const handleApprove = async () => {
  try {
    await reviewMutation.mutateAsync({ id, decision: 'approved' });
    addToast('Applicant approved successfully', 'success');
    navigate('/applicants');
  } catch (error) {
    addToast(`Failed to approve: ${error.message}`, 'error');
  }
};
```

**WebSocket Hook:**
```jsx
// useRealtimeUpdates.js
import { useEffect } from 'react';
import { useQueryClient } from '@tanstack/react-query';
import { useAuth } from '../auth';

export function useRealtimeUpdates() {
  const queryClient = useQueryClient();
  const { getToken } = useAuth();

  useEffect(() => {
    const connectWebSocket = async () => {
      const token = await getToken();
      const ws = new WebSocket(
        `${process.env.REACT_APP_WS_URL}?token=${token}`
      );

      ws.onmessage = (event) => {
        const data = JSON.parse(event.data);

        switch (data.type) {
          case 'applicant.updated':
          case 'applicant.reviewed':
            queryClient.invalidateQueries(['applicant', data.applicant_id]);
            queryClient.invalidateQueries(['applicants']);
            break;
          case 'screening.completed':
            queryClient.invalidateQueries(['screeningChecks']);
            break;
          case 'document.processed':
            queryClient.invalidateQueries(['applicant', data.applicant_id]);
            break;
          case 'case.created':
          case 'case.resolved':
            queryClient.invalidateQueries(['cases']);
            break;
        }
      };

      return () => ws.close();
    };

    connectWebSocket();
  }, [queryClient, getToken]);
}
```

## Success Criteria

### Toast Notifications:
- [ ] Success toasts show after create/update/delete
- [ ] Error toasts show after API failures
- [ ] Toasts auto-dismiss appropriately
- [ ] Toasts can be manually dismissed

### Loading States:
- [ ] All list views show skeletons during load
- [ ] All buttons show spinners during mutations
- [ ] No UI flashing between states

### Error Handling:
- [ ] Error boundaries catch component errors
- [ ] Error states show with retry buttons
- [ ] 404 pages show for missing resources
- [ ] Network errors show helpful messages

### Real-time Updates (if implemented):
- [ ] WebSocket connects on login
- [ ] Lists refresh when events received
- [ ] Notifications show for important events

### Permissions:
- [ ] Buttons hidden for unauthorized users
- [ ] Actions blocked with permission message

## Testing Checklist

1. **Toast Notifications:**
   - Create applicant -> success toast
   - Approve applicant -> success toast
   - Disconnect network, try action -> error toast

2. **Loading States:**
   - Navigate to /applicants -> skeleton shows
   - Click approve -> button shows spinner

3. **Error Handling:**
   - Navigate to /applicants/invalid-uuid -> 404 page
   - Disconnect network -> error state with retry
   - Cause JS error -> error boundary catches it

4. **Permissions (if user has limited role):**
   - Viewer role -> approve button hidden
   - Try to access admin feature -> access denied message

## Reference
See `FRONTEND_AUDIT_AND_INTEGRATION_GUIDE.md` Section 6 for patterns.

## Questions?
If unclear about WebSocket setup or permission structure, ask first.
```

---

## Sprint 8: Dashboard Integration (High - 2-3 Days)

### Prerequisites
- **Sprint 0 must be completed first** (backend dashboard endpoints)
- Sprint 2 (API Service Layer)

### Files to Upload:
1. `FRONTEND_AUDIT_AND_INTEGRATION_GUIDE.md`
2. `02_FOLDER_STRUCTURE_COMPLETE.md`
3. `README.md` (from repo)
4. `frontend/src/components/Dashboard.jsx`

### Prompt (Copy This):

```
# CHAT TITLE: Frontend Sprint 8 - Dashboard Integration

## Context
I'm building GetClearance, an AI-native KYC/AML platform (Sumsub clone). Sprint 0 created the backend dashboard endpoints. Now I need to connect the Dashboard UI to real data.

**Current Repo:** https://github.com/autorevai/getclearance

## What Exists (Read These First)
I've uploaded context files:

1. **FRONTEND_AUDIT_AND_INTEGRATION_GUIDE.md** - Implementation patterns
2. **02_FOLDER_STRUCTURE_COMPLETE.md** - Directory tree
3. **README.md** - Project README
4. **Dashboard.jsx** - Current UI (uses mock data)

**Current state:**
- Dashboard.jsx has hardcoded mock data:
  - mockKPIs (47 applicants, 38 approved, etc.)
  - mockScreeningHits (2 sanctions, 5 PEP, 8 adverse)
  - mockRecentActivity (Emily Park, Marcus Webb, etc.)
  - mockAIInsights
- Backend endpoints exist (Sprint 0):
  - GET /api/v1/dashboard/stats
  - GET /api/v1/dashboard/screening-summary
  - GET /api/v1/dashboard/activity

## What I Need You To Do

### Part 1: Create Dashboard Hooks

**Files to create:**
1. `frontend/src/hooks/useDashboard.js` - React Query hooks for dashboard data

**Hooks needed:**
```javascript
export function useDashboardStats() {
  // Fetches GET /api/v1/dashboard/stats
}

export function useScreeningSummary() {
  // Fetches GET /api/v1/dashboard/screening-summary
}

export function useRecentActivity() {
  // Fetches GET /api/v1/dashboard/activity
}
```

### Part 2: Update Dashboard.jsx

**Changes needed:**
1. Remove mockKPIs array
2. Remove mockScreeningHits array
3. Remove mockRecentActivity array
4. Import and use useDashboardStats() hook
5. Import and use useScreeningSummary() hook
6. Import and use useRecentActivity() hook
7. Show loading skeletons while fetching
8. Show error states if API fails
9. Add refresh button to manually refetch data

### Part 3: Add Dashboard Service

**Files to create:**
2. `frontend/src/services/dashboard.js` - Dashboard API methods

```javascript
export class DashboardService {
  constructor(getToken) {
    this.api = new ApiClient(getToken);
  }

  async getStats() {
    return this.api.get('/dashboard/stats');
  }

  async getScreeningSummary() {
    return this.api.get('/dashboard/screening-summary');
  }

  async getActivity() {
    return this.api.get('/dashboard/activity');
  }
}
```

## Integration Requirements

### Dashboard must:
- Use useDashboardStats() for KPI cards
- Use useScreeningSummary() for screening hits widget
- Use useRecentActivity() for activity feed
- Show skeleton loading states
- Auto-refresh data every 60 seconds (staleTime)
- Show "Last updated" timestamp

### KPI Cards mapping:
```jsx
// Map API response to card display
const { data: stats } = useDashboardStats();

const kpiCards = [
  {
    label: "Today's Applicants",
    value: stats?.today_applicants || 0,
    change: stats?.today_applicants_change || 0,
    trend: stats?.today_applicants_change >= 0 ? 'up' : 'down'
  },
  {
    label: 'Approved',
    value: stats?.approved || 0,
    change: stats?.approved_change || 0,
    trend: stats?.approved_change >= 0 ? 'up' : 'down'
  },
  // ... etc
];
```

### Screening Hits mapping:
```jsx
const { data: screening } = useScreeningSummary();

const screeningHits = [
  { severity: 'high', count: screening?.sanctions_matches || 0, label: 'Sanctions Matches' },
  { severity: 'medium', count: screening?.pep_hits || 0, label: 'PEP Hits' },
  { severity: 'low', count: screening?.adverse_media || 0, label: 'Adverse Media' },
];
```

### Activity Feed mapping:
```jsx
const { data: activity } = useRecentActivity();

// activity.items already in correct format from API
{activity?.items?.map((item, index) => (
  <ActivityItem key={index} {...item} />
))}
```

## Architecture Constraints

**Component Pattern:**
```jsx
// Dashboard.jsx
import { useDashboardStats, useScreeningSummary, useRecentActivity } from '../hooks/useDashboard';

export default function Dashboard() {
  const { data: stats, isLoading: statsLoading, error: statsError } = useDashboardStats();
  const { data: screening, isLoading: screeningLoading } = useScreeningSummary();
  const { data: activity, isLoading: activityLoading } = useRecentActivity();

  return (
    <div className="dashboard">
      {/* KPI Section */}
      <section className="kpi-grid">
        {statsLoading ? (
          <KPISkeleton count={4} />
        ) : statsError ? (
          <ErrorState message="Failed to load stats" />
        ) : (
          kpiCards.map(card => <KPICard key={card.label} {...card} />)
        )}
      </section>

      {/* Screening Hits */}
      <section className="screening-summary">
        {screeningLoading ? (
          <ScreeningSkeleton />
        ) : (
          <ScreeningHitsWidget hits={screeningHits} />
        )}
      </section>

      {/* Activity Feed */}
      <section className="activity-feed">
        {activityLoading ? (
          <ActivitySkeleton count={5} />
        ) : (
          <ActivityFeed items={activity?.items || []} />
        )}
      </section>

      {/* AI Insights - keep as is for now (separate AI integration) */}
    </div>
  );
}
```

**React Query Configuration:**
```javascript
// useDashboard.js
export function useDashboardStats() {
  const { getToken } = useAuth();
  const service = new DashboardService(getToken);

  return useQuery({
    queryKey: ['dashboard', 'stats'],
    queryFn: () => service.getStats(),
    staleTime: 60000, // Refresh every minute
    refetchInterval: 60000, // Auto-refresh
  });
}
```

## Success Criteria

- [ ] Dashboard shows real KPIs from API
- [ ] KPI change indicators show real day-over-day changes
- [ ] Screening hits widget shows real counts
- [ ] Activity feed shows real recent activity
- [ ] Loading skeletons show during fetch
- [ ] Error states show with retry button
- [ ] Data auto-refreshes every 60 seconds
- [ ] No mock data remains in Dashboard.jsx (except AI Insights)

## Testing Checklist

After implementation:
1. Login and navigate to /dashboard
2. Verify KPIs show real numbers (may be zeros if no data)
3. Verify screening hits show real counts
4. Verify activity feed shows real events
5. Wait 60 seconds - verify data refreshes
6. Disconnect network - verify error state shows
7. Reconnect - verify retry button works

## Reference
See `FRONTEND_AUDIT_AND_INTEGRATION_GUIDE.md` for patterns.

## Questions?
If unclear about API response format or existing Dashboard structure, ask first.
```

---

## Sprint 9: Remaining Gaps & Placeholder Pages (Medium - 3-5 Days) ✅ COMPLETE

### Status: COMPLETED (2025-12-02)

**Implemented:**
- `frontend/src/components/SearchModal.jsx` - Global search modal (Cmd+K)
- `frontend/src/components/pages/ComingSoon.jsx` - Reusable placeholder template
- `frontend/src/components/pages/*.jsx` - 8 placeholder pages (Companies, Integrations, DeviceIntel, ReusableKYC, Analytics, Settings, Billing, AuditLog)
- `frontend/src/hooks/useGlobalSearch.js` - Search across applicants/cases
- `frontend/src/hooks/useNavigationCounts.js` - Dynamic nav badge counts
- Updated `AppShell.jsx` - Search modal integration, dynamic badges, Cmd+K shortcut
- Updated `Dashboard.jsx` - Filter dropdowns, AI insight actions, activity click handlers
- Updated `ApplicantsList.jsx` - AI Batch Review button, More Actions dropdown per row
- Updated `ApplicantAssistant.jsx` - Language selector (9 languages), attach document button
- Updated `App.jsx` - Routes for all placeholder pages

**Features Completed:**
- ✅ Global search modal opens with Cmd+K / Ctrl+K
- ✅ Search across applicants and cases with debounced queries
- ✅ Navigation badge counts fetched from real API (auto-refresh 60s)
- ✅ 8 Coming Soon placeholder pages with planned features list
- ✅ Dashboard filter buttons functional (Today/Week/Month/Quarter)
- ✅ AI insight action buttons navigate to correct pages
- ✅ Activity feed items clickable (navigate to applicant/case)
- ✅ More Actions dropdown per applicant row (View, Export, Screen, Create Case, Reject)
- ✅ Language selector in AI Assistant (EN, ES, FR, DE, PT, ZH, JA, KO, AR)
- ✅ Attach document button in AI Assistant (file picker)

---

### Why This Sprint?
After completing Sprints 1-8, there are remaining gaps:
1. **8 placeholder pages** that show "Coming Soon"
2. **Dashboard mock data** (AI insights, SLA performance)
3. **Non-functional UI buttons** (export, AI batch review, attach, global search)
4. **Hard-coded badge counts** in navigation

### Files to Upload:
1. `FRONTEND_AUDIT_AND_INTEGRATION_GUIDE.md`
2. `02_FOLDER_STRUCTURE_COMPLETE.md`
3. `README.md` (from repo)
4. `frontend/src/components/AppShell.jsx`
5. `frontend/src/components/Dashboard.jsx`
6. `frontend/src/components/ApplicantsList.jsx`
7. `frontend/src/components/ApplicantAssistant.jsx`

### Prompt (Copy This):

```
# CHAT TITLE: Frontend Sprint 9 - Remaining Gaps & Placeholder Pages

## Context
I'm building GetClearance, an AI-native KYC/AML platform (Sumsub clone). Sprints 1-8 completed the core functionality. Now I need to address remaining gaps: placeholder pages, mock data, and non-functional buttons.

**Current Repo:** https://github.com/autorevai/getclearance

## What Exists (Read These First)
I've uploaded context files:

1. **FRONTEND_AUDIT_AND_INTEGRATION_GUIDE.md** - Implementation patterns
2. **02_FOLDER_STRUCTURE_COMPLETE.md** - Directory tree
3. **README.md** - Project README
4. **AppShell.jsx** - Navigation with placeholder items
5. **Dashboard.jsx** - Has mock AI insights and SLA
6. **ApplicantsList.jsx** - Has non-functional AI Batch Review button
7. **ApplicantAssistant.jsx** - Has non-functional attach and language buttons

## Current Gaps

### Gap 1: Placeholder Pages (8 pages show "Coming Soon")
These navigation items exist but lead nowhere:
- Companies/KYB
- Integrations
- Device Intelligence (BETA)
- Reusable KYC (BETA)
- Analytics
- Settings
- Billing & Usage
- Audit Log

### Gap 2: Dashboard Mock Data
- `mockAIInsights` array is hardcoded
- AI insight action buttons don't work
- SLA Performance ring shows hardcoded 94%

### Gap 3: Non-functional UI Buttons
- **AppShell**: Global search bar (renders but no action)
- **AppShell**: Notifications bell (shows badge but no dropdown)
- **AppShell**: Hard-coded badge counts (12, 3, 5) in navItems
- **Dashboard**: "Today" and "All Products" filter buttons
- **Dashboard**: Activity item click (no navigation)
- **ApplicantsList**: "AI Batch Review" button
- **ApplicantsList**: "More actions" [...] dropdown per row
- **CaseManagement**: "Export" button in case detail
- **ApplicantAssistant**: Language selector dropdown
- **ApplicantAssistant**: Attach document button

## What I Need You To Do

### Part 1: Create Placeholder Page Components

**File to create:** `frontend/src/components/pages/ComingSoon.jsx`

A reusable "Coming Soon" page component:
```jsx
export default function ComingSoon({
  title,
  description,
  icon: Icon,
  expectedDate,
  features = []
}) {
  return (
    <div className="coming-soon-page">
      <div className="coming-soon-content">
        {Icon && <Icon size={64} className="coming-soon-icon" />}
        <h1>{title}</h1>
        <p className="coming-soon-description">{description}</p>

        {features.length > 0 && (
          <div className="planned-features">
            <h3>Planned Features:</h3>
            <ul>
              {features.map((feature, i) => (
                <li key={i}>{feature}</li>
              ))}
            </ul>
          </div>
        )}

        {expectedDate && (
          <p className="expected-date">Expected: {expectedDate}</p>
        )}

        <button onClick={() => window.history.back()}>
          ← Go Back
        </button>
      </div>
    </div>
  );
}
```

### Part 2: Create Specific Placeholder Pages

**Files to create:**

1. `frontend/src/components/pages/CompaniesPage.jsx`
```jsx
import ComingSoon from './ComingSoon';
import { Building2 } from 'lucide-react';

export default function CompaniesPage() {
  return (
    <ComingSoon
      title="Companies / KYB"
      description="Know Your Business verification for corporate entities"
      icon={Building2}
      expectedDate="Q1 2025"
      features={[
        "Corporate entity verification",
        "UBO (Ultimate Beneficial Owner) identification",
        "Business document verification",
        "Corporate structure mapping",
        "Risk assessment for businesses"
      ]}
    />
  );
}
```

2. `frontend/src/components/pages/IntegrationsPage.jsx` - API keys, webhooks management
3. `frontend/src/components/pages/DeviceIntelligencePage.jsx` - Device fingerprinting (BETA)
4. `frontend/src/components/pages/ReusableKYCPage.jsx` - Portable identity (BETA)
5. `frontend/src/components/pages/AnalyticsPage.jsx` - Reports and dashboards
6. `frontend/src/components/pages/SettingsPage.jsx` - Account settings, team management
7. `frontend/src/components/pages/BillingPage.jsx` - Usage, invoices, plans
8. `frontend/src/components/pages/AuditLogPage.jsx` - Compliance audit trail

### Part 3: Add Routes for Placeholder Pages

**Update App.jsx:**
```jsx
import CompaniesPage from './components/pages/CompaniesPage';
import IntegrationsPage from './components/pages/IntegrationsPage';
import DeviceIntelligencePage from './components/pages/DeviceIntelligencePage';
import ReusableKYCPage from './components/pages/ReusableKYCPage';
import AnalyticsPage from './components/pages/AnalyticsPage';
import SettingsPage from './components/pages/SettingsPage';
import BillingPage from './components/pages/BillingPage';
import AuditLogPage from './components/pages/AuditLogPage';

// Add routes
<Route path="/companies" element={<CompaniesPage />} />
<Route path="/integrations" element={<IntegrationsPage />} />
<Route path="/device-intel" element={<DeviceIntelligencePage />} />
<Route path="/reusable-kyc" element={<ReusableKYCPage />} />
<Route path="/analytics" element={<AnalyticsPage />} />
<Route path="/settings" element={<SettingsPage />} />
<Route path="/billing" element={<BillingPage />} />
<Route path="/audit-log" element={<AuditLogPage />} />
```

### Part 4: Connect Dashboard AI Insights to Real API

**Changes to Dashboard.jsx:**

1. Remove `mockAIInsights` array
2. Create new hook `useAIInsights()` that calls `/ai/dashboard-insights`
3. If backend endpoint doesn't exist, show a placeholder state:
```jsx
const AIInsightsSection = () => {
  const { data: insights, isLoading, error } = useAIInsights();

  if (isLoading) return <InsightsSkeleton />;
  if (error || !insights) {
    return (
      <div className="ai-insights-placeholder">
        <Sparkles size={24} />
        <p>AI Insights will appear here once enough data is collected.</p>
        <small>Insights are generated based on applicant patterns and screening results.</small>
      </div>
    );
  }

  return insights.map(insight => <InsightCard key={insight.id} {...insight} />);
};
```

4. Connect SLA Performance to real data:
```jsx
// Add to useDashboardStats or create usePerformanceMetrics
const { data: performance } = usePerformanceMetrics();
const slaOnTime = performance?.sla_percentage ?? null;

// In render:
{slaOnTime !== null ? (
  <SLAGauge value={slaOnTime} />
) : (
  <SLAPlaceholder message="SLA tracking requires processing history" />
)}
```

5. Make AI insight action buttons work:
```jsx
const handleInsightAction = (insight) => {
  switch (insight.action) {
    case 'View Analytics':
      navigate('/analytics');
      break;
    case 'Review Applicants':
      navigate('/applicants?risk_level=high');
      break;
    case 'Run Re-screen':
      navigate('/screening?needs_rescreen=true');
      break;
  }
};
```

### Part 5: Implement Global Search

**Update AppShell.jsx:**

1. Create search modal/dropdown:
```jsx
const [searchOpen, setSearchOpen] = useState(false);
const [searchQuery, setSearchQuery] = useState('');
const [searchResults, setSearchResults] = useState(null);

// Add keyboard shortcut
useEffect(() => {
  const handleKeyDown = (e) => {
    if ((e.metaKey || e.ctrlKey) && e.key === 'k') {
      e.preventDefault();
      setSearchOpen(true);
    }
    if (e.key === 'Escape') {
      setSearchOpen(false);
    }
  };
  window.addEventListener('keydown', handleKeyDown);
  return () => window.removeEventListener('keydown', handleKeyDown);
}, []);
```

2. Create `useGlobalSearch` hook:
```jsx
// hooks/useGlobalSearch.js
export function useGlobalSearch(query) {
  const { getToken } = useAuth();

  return useQuery({
    queryKey: ['globalSearch', query],
    queryFn: async () => {
      if (!query || query.length < 2) return null;
      const api = new ApiClient(getToken);
      // Search across multiple endpoints
      const [applicants, cases] = await Promise.all([
        api.get(`/applicants?search=${query}&limit=5`),
        api.get(`/cases?search=${query}&limit=5`),
      ]);
      return {
        applicants: applicants.items || [],
        cases: cases.items || [],
      };
    },
    enabled: query?.length >= 2,
    staleTime: 30000,
  });
}
```

3. Create SearchModal component:
```jsx
// components/SearchModal.jsx
export default function SearchModal({ isOpen, onClose }) {
  const [query, setQuery] = useState('');
  const { data: results, isLoading } = useGlobalSearch(query);
  const navigate = useNavigate();

  const handleSelect = (type, id) => {
    navigate(type === 'applicant' ? `/applicants/${id}` : `/cases/${id}`);
    onClose();
  };

  return (
    <Dialog open={isOpen} onClose={onClose}>
      <div className="search-modal">
        <input
          autoFocus
          placeholder="Search applicants, cases..."
          value={query}
          onChange={(e) => setQuery(e.target.value)}
        />

        {isLoading && <LoadingSpinner />}

        {results && (
          <div className="search-results">
            {results.applicants.length > 0 && (
              <div className="result-section">
                <h4>Applicants</h4>
                {results.applicants.map(a => (
                  <div key={a.id} onClick={() => handleSelect('applicant', a.id)}>
                    {a.full_name} • {a.email}
                  </div>
                ))}
              </div>
            )}
            {results.cases.length > 0 && (
              <div className="result-section">
                <h4>Cases</h4>
                {results.cases.map(c => (
                  <div key={c.id} onClick={() => handleSelect('case', c.id)}>
                    {c.title} • {c.status}
                  </div>
                ))}
              </div>
            )}
          </div>
        )}
      </div>
    </Dialog>
  );
}
```

### Part 6: Connect Navigation Badge Counts

**Update AppShell.jsx:**

Replace hard-coded badge counts with real data:
```jsx
// Create hook to get counts
const { data: counts } = useNavigationCounts();

const navItems = [
  { id: 'applicants', label: 'Applicants', icon: Users, badge: counts?.pending_applicants },
  { id: 'screening', label: 'Screening', icon: Shield, badge: counts?.unresolved_hits },
  { id: 'cases', label: 'Cases', icon: FolderKanban, badge: counts?.open_cases },
  // ... other items
];
```

Create the hook:
```jsx
// hooks/useNavigationCounts.js
export function useNavigationCounts() {
  const { getToken } = useAuth();

  return useQuery({
    queryKey: ['navigationCounts'],
    queryFn: async () => {
      const api = new ApiClient(getToken);
      const [applicants, screening, cases] = await Promise.all([
        api.get('/applicants?status=pending_review&limit=0'),
        api.get('/screening/hits?status=pending&limit=0'),
        api.get('/cases?status=open&limit=0'),
      ]);
      return {
        pending_applicants: applicants.total || 0,
        unresolved_hits: screening.total || 0,
        open_cases: cases.total || 0,
      };
    },
    staleTime: 60000, // Refresh every minute
    refetchInterval: 60000,
  });
}
```

### Part 7: Fix Minor Non-functional Buttons

**ApplicantsList.jsx - AI Batch Review:**
```jsx
const handleAIBatchReview = async () => {
  if (selectedIds.length === 0) {
    toast.error('Select applicants first');
    return;
  }

  // Option A: Navigate to batch review page
  navigate(`/applicants/batch-review?ids=${selectedIds.join(',')}`);

  // Option B: Show modal with AI recommendations (if backend supports)
  // setShowBatchReviewModal(true);
};
```

**ApplicantsList.jsx - More Actions dropdown:**
```jsx
const MoreActionsDropdown = ({ applicant }) => {
  const [open, setOpen] = useState(false);

  return (
    <div className="dropdown">
      <button onClick={() => setOpen(!open)}>...</button>
      {open && (
        <div className="dropdown-menu">
          <button onClick={() => navigate(`/applicants/${applicant.id}`)}>
            View Details
          </button>
          <button onClick={() => handleExportApplicant(applicant.id)}>
            Export PDF
          </button>
          <button onClick={() => handleRunScreening(applicant.id)}>
            Run Screening
          </button>
          <button onClick={() => handleCreateCase(applicant.id)}>
            Create Case
          </button>
        </div>
      )}
    </div>
  );
};
```

**CaseManagement.jsx - Export button:**
```jsx
const handleExportCase = async () => {
  if (!selectedCase) return;

  try {
    const blob = await casesService.exportCase(selectedCase.id);
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `case-${selectedCase.id}.pdf`;
    a.click();
    URL.revokeObjectURL(url);
    toast.success('Case exported');
  } catch (error) {
    toast.error('Failed to export case');
  }
};
```

**ApplicantAssistant.jsx - Language selector:**
```jsx
const [language, setLanguage] = useState('en');
const [showLanguageMenu, setShowLanguageMenu] = useState(false);

const languages = [
  { code: 'en', label: 'English', flag: '🇺🇸' },
  { code: 'es', label: 'Español', flag: '🇪🇸' },
  { code: 'fr', label: 'Français', flag: '🇫🇷' },
  { code: 'de', label: 'Deutsch', flag: '🇩🇪' },
  { code: 'pt', label: 'Português', flag: '🇧🇷' },
  { code: 'zh', label: '中文', flag: '🇨🇳' },
  { code: 'ja', label: '日本語', flag: '🇯🇵' },
  { code: 'ko', label: '한국어', flag: '🇰🇷' },
  { code: 'ar', label: 'العربية', flag: '🇸🇦' },
];

// Pass language to API
const handleSend = async () => {
  await askAssistantMutation.mutateAsync({
    query: inputValue,
    applicant_id: applicantId,
    language: language, // Include language preference
  });
};
```

**ApplicantAssistant.jsx - Attach button:**
```jsx
const fileInputRef = useRef(null);

const handleAttachClick = () => {
  fileInputRef.current?.click();
};

const handleFileSelect = async (e) => {
  const file = e.target.files?.[0];
  if (!file) return;

  // Add file message to chat
  setMessages(prev => [...prev, {
    role: 'user',
    content: `[Attached: ${file.name}]`,
    file: file,
  }]);

  // Send with file context
  await askAssistantMutation.mutateAsync({
    query: `Please review this document: ${file.name}`,
    applicant_id: applicantId,
    // Note: Actual file upload would need backend support
  });
};

// In render:
<input
  type="file"
  ref={fileInputRef}
  onChange={handleFileSelect}
  accept="image/*,.pdf"
  style={{ display: 'none' }}
/>
<button onClick={handleAttachClick}>
  <Paperclip size={20} />
</button>
```

**Dashboard.jsx - Filter buttons:**
```jsx
const [dateFilter, setDateFilter] = useState('today');
const [productFilter, setProductFilter] = useState('all');

// Pass filters to hooks
const { data: stats } = useDashboardStats({
  date_filter: dateFilter,
  product_filter: productFilter
});

// In render:
<button
  className={dateFilter === 'today' ? 'active' : ''}
  onClick={() => setDateFilter('today')}
>
  Today
</button>
<button
  className={dateFilter === 'week' ? 'active' : ''}
  onClick={() => setDateFilter('week')}
>
  This Week
</button>
```

**Dashboard.jsx - Activity item click:**
```jsx
const handleActivityClick = (item) => {
  switch (item.type) {
    case 'applicant_reviewed':
    case 'applicant_created':
      navigate(`/applicants/${item.applicant_id}`);
      break;
    case 'screening_hit':
      navigate(`/screening?hit_id=${item.hit_id}`);
      break;
    case 'case_created':
    case 'case_resolved':
      navigate(`/cases/${item.case_id}`);
      break;
    case 'document_uploaded':
      navigate(`/applicants/${item.applicant_id}?tab=documents`);
      break;
  }
};
```

## Architecture Constraints

**Placeholder pages should:**
- Use consistent styling with rest of app
- Show planned features to set expectations
- Have a back button
- Include expected timeline if known

**Global search should:**
- Open with Cmd+K / Ctrl+K
- Close on Escape
- Debounce API calls (300ms)
- Show results grouped by type
- Navigate on selection

**Badge counts should:**
- Refresh every 60 seconds
- Show 0 if none (don't hide badge)
- Max display of 99+ for large numbers

## Success Criteria

### Placeholder Pages:
- [ ] All 8 placeholder pages created with routes
- [ ] Each shows relevant features and timeline
- [ ] Back button works
- [ ] Consistent styling

### Dashboard:
- [ ] AI Insights section shows placeholder if no API
- [ ] AI Insight action buttons navigate correctly
- [ ] SLA Performance connected or shows placeholder
- [ ] Filter buttons (Today/Week) work
- [ ] Activity items are clickable

### Global Search:
- [ ] Cmd+K opens search modal
- [ ] Search queries applicants and cases
- [ ] Results are clickable and navigate
- [ ] Escape closes modal

### Navigation:
- [ ] Badge counts come from real API
- [ ] Counts refresh every minute

### Minor Buttons:
- [ ] AI Batch Review does something (navigate or modal)
- [ ] More actions dropdown works per row
- [ ] Case Export button downloads PDF
- [ ] Language selector changes language
- [ ] Attach button opens file picker

## Testing Checklist

1. **Placeholder Pages:**
   - Click each nav item -> appropriate Coming Soon page
   - Back button returns to previous page

2. **Global Search:**
   - Press Cmd+K -> search modal opens
   - Type "john" -> shows matching applicants
   - Click result -> navigates to detail
   - Press Escape -> modal closes

3. **Navigation Badges:**
   - Create pending applicant -> badge increments
   - Resolve applicant -> badge decrements

4. **Dashboard:**
   - Click "This Week" filter -> data changes
   - Click activity item -> navigates correctly
   - AI insights show placeholder or real data

5. **Minor Buttons:**
   - Select applicants, click AI Batch Review -> action happens
   - Click [...] on row -> dropdown appears
   - Click Export on case -> PDF downloads

## Files to Create Summary

```
frontend/src/components/pages/
├── ComingSoon.jsx           (reusable template)
├── CompaniesPage.jsx        (KYB)
├── IntegrationsPage.jsx     (API keys, webhooks)
├── DeviceIntelligencePage.jsx (BETA)
├── ReusableKYCPage.jsx      (BETA)
├── AnalyticsPage.jsx
├── SettingsPage.jsx
├── BillingPage.jsx
└── AuditLogPage.jsx

frontend/src/components/
└── SearchModal.jsx          (global search)

frontend/src/hooks/
├── useGlobalSearch.js
└── useNavigationCounts.js
```

## Reference
See `FRONTEND_AUDIT_AND_INTEGRATION_GUIDE.md` for patterns.

## Questions?
If unclear about which features should be placeholder vs functional, ask first.
```

---

## Sprint Summary

| Sprint | Focus | Duration | Priority | Status |
|--------|-------|----------|----------|--------|
| **Sprint 0** | **Backend Dashboard/Screening Endpoints** | **1-2 days** | **Critical** | ✅ **COMPLETE** |
| Sprint 1 | Authentication | 3-5 days | Critical | ✅ Complete |
| Sprint 2 | API Service Layer | 3-4 days | Critical | ✅ Complete |
| Sprint 3 | Applicants Module | 5-7 days | Critical | ✅ Complete |
| Sprint 4 | Document Upload | 4-5 days | High | ✅ Complete |
| Sprint 5 | Screening Module | 4-5 days | High | ✅ Complete |
| Sprint 6 | Cases & AI | 4-5 days | Medium | ✅ Complete |
| Sprint 7 | Polish & Real-time | 3-4 days | Medium | ✅ Complete |
| Sprint 8 | Dashboard Integration | 2-3 days | High | ✅ Complete |
| **Sprint 9** | **Remaining Gaps & Placeholder Pages** | **3-5 days** | **Medium** | ✅ **COMPLETE** |

**ALL FRONTEND INTEGRATION SPRINTS COMPLETE (0-9)!** See `15_FEATURE_COMPLETION_SPRINTS.md` for Sprint 10-17 (placeholder → production).

### Sprint Dependencies Diagram
```
Sprint 0 (Backend Endpoints) ✅ COMPLETE
    ├── Sprint 5 (Screening) - /screening/lists ✅ Available
    └── Sprint 8 (Dashboard) - /dashboard/* endpoints ✅ Available

Sprint 1 (Auth) ✅ → Sprint 2 (API Layer) ✅ → Sprint 3 (Applicants) ✅ → Sprint 4 (Documents) ✅
                                           ↘ Sprint 5 (Screening) ✅
                                           ↘ Sprint 6 (Cases & AI) ✅
                                                                   ↘ Sprint 7 (Polish) ✅
                                           ↘ Sprint 8 (Dashboard) ✅
                                                                   ↘ Sprint 9 (Placeholders) ✅ COMPLETE
```

**All Sprints Complete!** Frontend integration work is done. Future sprints (10-17) will implement placeholder features.

---

## Pre-Sprint Checklist

Before starting EACH sprint:

- [ ] Completed previous sprint(s)
- [ ] Downloaded latest code from repo
- [ ] Read relevant context files
- [ ] Uploaded required files to chat
- [ ] Copied complete prompt (not partial)
- [ ] Understand what you're asking for
- [ ] Ready to review and test output

**Time investment:** 15 minutes prep per sprint
**Time saved:** 4-6 hours debugging per sprint

---

**Copy the prompts exactly as shown - they're structured for success!**
