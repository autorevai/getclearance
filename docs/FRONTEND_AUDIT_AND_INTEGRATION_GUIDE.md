# Frontend Audit & Integration Guide

## Executive Summary

**Current State: Frontend is 100% integration-ready. Sprints 1-9 Complete.**

The frontend has Auth0 authentication, a complete API service layer, applicants module with real data, document upload, screening module, cases & AI, all polish features (toast notifications, WebSocket real-time updates, permission-based UI, loading states, 404 page), dashboard with real stats, and all placeholder pages with global search.

**All frontend integration sprints are complete.** Remaining work is feature implementation (Sprints 10-17 in `15_FEATURE_COMPLETION_SPRINTS.md`).

### Quick Assessment

| Area | Backend | Frontend | Gap |
|------|---------|----------|-----|
| Applicant Management | Full CRUD API with filtering, search, review | ✅ Real API | **Done** |
| Authentication | Auth0 JWT + RBAC + RLS | ✅ Auth0 SDK | **Done** |
| Document Upload | R2 presigned URLs, OCR processing | ✅ Full UI + API | **Done** |
| AML Screening | OpenSanctions integration, hit resolution | ✅ Real API | **Done** |
| Case Management | Full CRUD with notes, resolution workflow | ✅ Real API | **Done** |
| AI Features | Risk summaries, document analysis, assistant | ✅ Real API | **Done** |
| Real-time Updates | WebSocket ready (ARQ workers) | ✅ useRealtimeUpdates | **Done** |
| Permission UI | RBAC in token | ✅ usePermissions | **Done** |
| Dashboard Stats | API ready | ✅ Real API | **Done (Sprint 8)** |
| Global Search | API ready | ✅ SearchModal (Cmd+K) | **Done (Sprint 9)** |
| Navigation Badges | API ready | ✅ Real counts | **Done (Sprint 9)** |
| Placeholder Pages | N/A | ✅ 8 Coming Soon pages | **Done (Sprint 9)** |

---

## What Exists Today

### Frontend Structure (`frontend/src/`)

```
frontend/src/
├── App.jsx                    # Main app with routing/navigation
├── index.js                   # Entry point with providers
├── auth/                      # ✅ Sprint 1 - Auth0 integration
│   ├── AuthProvider.jsx       # Auth0 provider wrapper
│   ├── ProtectedRoute.jsx     # Route guard component
│   └── useAuth.js             # Auth hook with getToken()
├── services/                  # ✅ Sprint 2+8 - API service layer
│   ├── api.js                 # Base API client with auth headers
│   ├── applicants.js          # Applicant CRUD, review, timeline
│   ├── documents.js           # Upload URLs, confirm, analyze
│   ├── screening.js           # Check, hits, resolve, lists, stats
│   ├── cases.js               # CRUD, notes, resolution
│   ├── ai.js                  # Risk summary, assistant
│   └── dashboard.js           # ✅ Sprint 8 - Dashboard stats, activity
├── hooks/                     # ✅ Sprint 2+7+8+9 - React Query hooks
│   ├── useApplicants.js       # Applicant queries & mutations
│   ├── useDocuments.js        # Document queries & mutations
│   ├── useScreening.js        # Screening queries & mutations
│   ├── useCases.js            # Case queries & mutations
│   ├── useAI.js               # AI queries & mutations
│   ├── useDashboard.js        # ✅ Sprint 8 - Dashboard stats hooks
│   ├── useRealtimeUpdates.js  # ✅ Sprint 7 - WebSocket real-time
│   ├── usePermissions.js      # ✅ Sprint 7 - Permission-based UI
│   ├── useToast.js            # ✅ Sprint 7 - Toast convenience hook
│   ├── useGlobalSearch.js     # ✅ Sprint 9 - Search across applicants/cases
│   └── useNavigationCounts.js # ✅ Sprint 9 - Dynamic nav badge counts
├── contexts/                  # ✅ Sprint 3 - App contexts
│   └── ToastContext.jsx       # Toast notification context
├── components/
│   ├── AppShell.jsx           # ✅ Sprint 9 - Main layout + search modal + dynamic badges
│   ├── Dashboard.jsx          # ✅ Sprint 8+9 - Real API + filter dropdowns + clickable items
│   ├── ApplicantsList.jsx     # ✅ Sprint 3+9 - Real API + AI Batch Review + More Actions
│   ├── ApplicantDetail.jsx    # ✅ Sprint 3 - Real API + Documents tab
│   ├── CreateApplicantModal.jsx # ✅ Sprint 3 - Create form
│   ├── DocumentUpload.jsx     # ✅ Sprint 4 - Drag & drop, multi-file, magic bytes
│   ├── DocumentList.jsx       # ✅ Sprint 4 - Document grid with status
│   ├── DocumentPreview.jsx    # ✅ Sprint 4 - Modal with tabs, zoom, checks
│   ├── ScreeningChecks.jsx    # ✅ Sprint 5 - AML screening (real API)
│   ├── CaseManagement.jsx     # ✅ Sprint 6 - Case management (real API)
│   ├── ApplicantAssistant.jsx # ✅ Sprint 6+9 - AI chat + language selector + attach
│   ├── SearchModal.jsx        # ✅ Sprint 9 - Global search (Cmd+K)
│   ├── ErrorBoundary.jsx      # ✅ Sprint 2 - Error boundary
│   ├── shared/                # Reusable components
│   │   ├── Toast.jsx          # Toast notification component
│   │   ├── ConfirmDialog.jsx  # Confirmation modal
│   │   ├── LoadingSpinner.jsx # ✅ Sprint 7 - Multiple sizes, variants
│   │   ├── LoadingSkeleton.jsx # Skeleton loading states
│   │   ├── ErrorState.jsx     # Error display component
│   │   └── NotFound.jsx       # ✅ Sprint 7 - 404 page with suggestions
│   └── pages/                 # ✅ Sprint 9 - Placeholder pages
│       ├── ComingSoon.jsx     # Reusable placeholder template
│       ├── CompaniesPage.jsx  # KYB placeholder
│       ├── IntegrationsPage.jsx # API keys placeholder
│       ├── DeviceIntelligencePage.jsx # Device intel placeholder
│       ├── ReusableKYCPage.jsx # Portable KYC placeholder
│       ├── AnalyticsPage.jsx  # Reports placeholder
│       ├── SettingsPage.jsx   # Settings placeholder
│       ├── BillingPage.jsx    # Billing placeholder
│       └── AuditLogPage.jsx   # Audit log placeholder
```

### Backend API Endpoints (All Ready to Use)

```
/api/v1/
├── /applicants
│   ├── GET    /                    # List with filters, pagination, search
│   ├── POST   /                    # Create applicant
│   ├── GET    /{id}                # Get full details
│   ├── PATCH  /{id}                # Update applicant
│   ├── POST   /{id}/review         # Approve/reject
│   ├── POST   /{id}/steps/{step}/complete
│   ├── GET    /{id}/evidence       # Download evidence PDF
│   ├── GET    /{id}/evidence/preview
│   └── GET    /{id}/timeline       # Event timeline
│
├── /dashboard                       # ✅ NEW (Sprint 0)
│   ├── GET    /stats               # KPI statistics (today's applicants, approved, rejected, pending)
│   ├── GET    /screening-summary   # Screening hit counts by type
│   └── GET    /activity            # Recent activity feed
│
├── /documents
│   ├── POST   /upload-url          # Get presigned upload URL
│   ├── POST   /{id}/confirm        # Confirm upload complete
│   ├── POST   /upload              # Direct upload (< 10MB)
│   ├── GET    /{id}                # Get document metadata
│   ├── GET    /{id}/download       # Get presigned download URL
│   ├── DELETE /{id}                # Delete document
│   └── POST   /{id}/analyze        # Run AI analysis
│
├── /screening
│   ├── POST   /check               # Run screening check
│   ├── GET    /checks              # List checks
│   ├── GET    /checks/{id}         # Get check details with hits
│   ├── PATCH  /hits/{id}           # Resolve hit
│   ├── GET    /hits/{id}/suggestion # AI suggestion for hit
│   └── GET    /lists               # ✅ NEW - Connected list sources (OFAC, EU, UN, UK, OpenSanctions)
│
├── /cases
│   ├── GET    /                    # List cases with filters
│   ├── POST   /                    # Create case
│   ├── GET    /{id}                # Get case with notes
│   ├── PATCH  /{id}                # Update case
│   ├── POST   /{id}/resolve        # Resolve case
│   └── POST   /{id}/notes          # Add note
│
└── /ai
    ├── GET    /applicants/{id}/risk-summary    # AI risk analysis
    ├── POST   /applicants/{id}/risk-summary    # Regenerate summary
    ├── POST   /assistant                       # Applicant-facing assistant
    └── POST   /batch-analyze                   # Batch risk analysis
```

---

## Critical Gaps to Close

### 1. Authentication (MUST DO FIRST)

**Current State:** No authentication. Anyone can access anything.

**Backend Ready:**
- Auth0 JWT token validation
- RBAC with permissions (`read:applicants`, `write:applicants`, `review:applicants`, etc.)
- Row-Level Security (RLS) filtering by tenant

**Frontend Needs:**

```jsx
// Install Auth0 React SDK
// npm install @auth0/auth0-react

// src/auth/AuthProvider.jsx
import { Auth0Provider } from '@auth0/auth0-react';

export function AuthProvider({ children }) {
  return (
    <Auth0Provider
      domain={process.env.REACT_APP_AUTH0_DOMAIN}
      clientId={process.env.REACT_APP_AUTH0_CLIENT_ID}
      authorizationParams={{
        redirect_uri: window.location.origin,
        audience: process.env.REACT_APP_AUTH0_AUDIENCE,
      }}
    >
      {children}
    </Auth0Provider>
  );
}

// src/auth/useApi.js - API client with auth
import { useAuth0 } from '@auth0/auth0-react';

export function useApi() {
  const { getAccessTokenSilently, isAuthenticated } = useAuth0();

  const apiCall = async (endpoint, options = {}) => {
    const token = await getAccessTokenSilently();
    const response = await fetch(`${API_BASE_URL}${endpoint}`, {
      ...options,
      headers: {
        ...options.headers,
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json',
      },
    });

    if (!response.ok) {
      throw new Error(`API error: ${response.status}`);
    }

    return response.json();
  };

  return { apiCall, isAuthenticated };
}
```

**Environment Variables Needed:**
```env
REACT_APP_AUTH0_DOMAIN=your-tenant.auth0.com
REACT_APP_AUTH0_CLIENT_ID=your-client-id
REACT_APP_AUTH0_AUDIENCE=https://api.getclearance.dev
REACT_APP_API_BASE_URL=https://api.getclearance.dev/api/v1
```

---

### 2. API Service Layer

**Current State:** No API calls. All data is hardcoded.

**Create: `src/services/api.js`**

```javascript
// Base API configuration
const API_BASE = process.env.REACT_APP_API_BASE_URL || 'http://localhost:8000/api/v1';

class ApiService {
  constructor(getToken) {
    this.getToken = getToken;
  }

  async request(endpoint, options = {}) {
    const token = await this.getToken();
    const response = await fetch(`${API_BASE}${endpoint}`, {
      ...options,
      headers: {
        ...options.headers,
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json',
      },
    });

    if (!response.ok) {
      const error = await response.json().catch(() => ({}));
      throw new Error(error.detail || `HTTP ${response.status}`);
    }

    return response.json();
  }

  // Applicants
  async listApplicants(params = {}) {
    const query = new URLSearchParams(params).toString();
    return this.request(`/applicants?${query}`);
  }

  async getApplicant(id) {
    return this.request(`/applicants/${id}`);
  }

  async createApplicant(data) {
    return this.request('/applicants', {
      method: 'POST',
      body: JSON.stringify(data),
    });
  }

  async updateApplicant(id, data) {
    return this.request(`/applicants/${id}`, {
      method: 'PATCH',
      body: JSON.stringify(data),
    });
  }

  async reviewApplicant(id, decision, notes, riskOverride) {
    return this.request(`/applicants/${id}/review`, {
      method: 'POST',
      body: JSON.stringify({
        decision,
        notes,
        risk_score_override: riskOverride,
      }),
    });
  }

  async getApplicantTimeline(id) {
    return this.request(`/applicants/${id}/timeline`);
  }

  async downloadEvidence(id) {
    const token = await this.getToken();
    const response = await fetch(`${API_BASE}/applicants/${id}/evidence`, {
      headers: { 'Authorization': `Bearer ${token}` },
    });
    return response.blob();
  }

  // Documents
  async getUploadUrl(applicantId, documentType, fileName, contentType) {
    const formData = new FormData();
    formData.append('applicant_id', applicantId);
    formData.append('document_type', documentType);
    formData.append('file_name', fileName);
    formData.append('content_type', contentType);

    const token = await this.getToken();
    const response = await fetch(`${API_BASE}/documents/upload-url`, {
      method: 'POST',
      headers: { 'Authorization': `Bearer ${token}` },
      body: formData,
    });
    return response.json();
  }

  async confirmUpload(documentId, fileSize) {
    return this.request(`/documents/${documentId}/confirm`, {
      method: 'POST',
      body: JSON.stringify({ file_size: fileSize }),
    });
  }

  async analyzeDocument(documentId) {
    return this.request(`/documents/${documentId}/analyze`, {
      method: 'POST',
    });
  }

  // Screening
  async runScreening(data) {
    return this.request('/screening/check', {
      method: 'POST',
      body: JSON.stringify(data),
    });
  }

  async listScreeningChecks(params = {}) {
    const query = new URLSearchParams(params).toString();
    return this.request(`/screening/checks?${query}`);
  }

  async resolveHit(hitId, resolution, notes) {
    return this.request(`/screening/hits/${hitId}`, {
      method: 'PATCH',
      body: JSON.stringify({ resolution, notes }),
    });
  }

  async getHitSuggestion(hitId) {
    return this.request(`/screening/hits/${hitId}/suggestion`);
  }

  // Cases
  async listCases(params = {}) {
    const query = new URLSearchParams(params).toString();
    return this.request(`/cases?${query}`);
  }

  async createCase(data) {
    return this.request('/cases', {
      method: 'POST',
      body: JSON.stringify(data),
    });
  }

  async resolveCase(caseId, resolution, notes) {
    return this.request(`/cases/${caseId}/resolve`, {
      method: 'POST',
      body: JSON.stringify({ resolution, notes }),
    });
  }

  async addCaseNote(caseId, content) {
    return this.request(`/cases/${caseId}/notes`, {
      method: 'POST',
      body: JSON.stringify({ content }),
    });
  }

  // AI
  async getRiskSummary(applicantId) {
    return this.request(`/ai/applicants/${applicantId}/risk-summary`);
  }

  async askAssistant(query, applicantId = null) {
    return this.request('/ai/assistant', {
      method: 'POST',
      body: JSON.stringify({ query, applicant_id: applicantId }),
    });
  }
}

export default ApiService;
```

---

### 3. State Management

**Current State:** No global state. Each component has its own local state with mock data.

**Recommended: React Query for server state**

```bash
npm install @tanstack/react-query
```

```jsx
// src/hooks/useApplicants.js
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { useApi } from '../services/api';

export function useApplicants(params = {}) {
  const api = useApi();

  return useQuery({
    queryKey: ['applicants', params],
    queryFn: () => api.listApplicants(params),
    staleTime: 30000, // 30 seconds
  });
}

export function useApplicant(id) {
  const api = useApi();

  return useQuery({
    queryKey: ['applicant', id],
    queryFn: () => api.getApplicant(id),
    enabled: !!id,
  });
}

export function useReviewApplicant() {
  const api = useApi();
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ id, decision, notes, riskOverride }) =>
      api.reviewApplicant(id, decision, notes, riskOverride),
    onSuccess: (data, { id }) => {
      queryClient.invalidateQueries(['applicant', id]);
      queryClient.invalidateQueries(['applicants']);
    },
  });
}

// Similar hooks for documents, screening, cases, etc.
```

---

### 4. Component Refactoring Required

Each component needs to be converted from mock data to real API calls.

#### ApplicantsList.jsx - Changes Needed

```jsx
// BEFORE (current - mock data)
const mockApplicants = [
  { id: '1', name: 'Sofia Reyes', ... },
  ...
];

// AFTER (production)
import { useApplicants } from '../hooks/useApplicants';

export default function ApplicantsList() {
  const [filters, setFilters] = useState({
    status: null,
    risk_level: null,
    search: '',
  });

  const { data, isLoading, error } = useApplicants(filters);

  if (isLoading) return <LoadingSpinner />;
  if (error) return <ErrorMessage error={error} />;

  return (
    <div>
      {/* Existing UI, but using data.items instead of mockApplicants */}
      {data.items.map(applicant => (
        <ApplicantRow key={applicant.id} applicant={applicant} />
      ))}
      <Pagination total={data.total} limit={data.limit} offset={data.offset} />
    </div>
  );
}
```

#### ScreeningChecks.jsx - Changes Needed

```jsx
// Connect "Run New Check" button to actual API
const { mutate: runCheck, isLoading } = useMutation({
  mutationFn: (data) => api.runScreening(data),
  onSuccess: (result) => {
    // Refresh the list
    queryClient.invalidateQueries(['screeningChecks']);
    setShowNewCheck(false);
  },
});

// "Mark as Clear" and "Confirm Match" buttons need to call resolveHit
const handleResolveHit = async (hitId, resolution) => {
  await api.resolveHit(hitId, resolution, null);
  // Refresh data
};
```

#### CaseManagement.jsx - Changes Needed

```jsx
// List cases from API
const { data: cases } = useCases({ status: activeFilter });

// Create case button
const { mutate: createCase } = useCreateCase();

// Add note to case
const { mutate: addNote } = useMutation({
  mutationFn: ({ caseId, content }) => api.addCaseNote(caseId, content),
});

// Resolve case
const { mutate: resolveCase } = useMutation({
  mutationFn: ({ caseId, resolution, notes }) =>
    api.resolveCase(caseId, resolution, notes),
});
```

#### ApplicantAssistant.jsx - Changes Needed

```jsx
// BEFORE: Fake response generation
const generateResponse = (question) => {
  // Returns hardcoded strings
};

// AFTER: Real AI API call
const handleSend = async () => {
  if (!inputValue.trim()) return;

  setMessages(prev => [...prev, { role: 'user', content: inputValue }]);
  setIsTyping(true);

  try {
    const response = await api.askAssistant(inputValue, applicantId);
    setMessages(prev => [...prev, {
      role: 'assistant',
      content: response.response,
      timestamp: new Date(response.generated_at),
    }]);
  } catch (error) {
    setMessages(prev => [...prev, {
      role: 'assistant',
      content: 'Sorry, I encountered an error. Please try again.',
    }]);
  } finally {
    setIsTyping(false);
  }
};
```

---

### 5. Document Upload Flow

**Current State:** File input UI exists but does nothing.

**Implementation Needed:**

```jsx
// src/components/DocumentUpload.jsx
import { useState } from 'react';
import { useApi } from '../services/api';

export function DocumentUpload({ applicantId, onComplete }) {
  const api = useApi();
  const [uploading, setUploading] = useState(false);
  const [progress, setProgress] = useState(0);

  const handleFileSelect = async (event) => {
    const file = event.target.files[0];
    if (!file) return;

    setUploading(true);
    setProgress(0);

    try {
      // 1. Get presigned upload URL
      const { upload_url, document_id, key } = await api.getUploadUrl(
        applicantId,
        'passport', // or 'driver_license', 'utility_bill', etc.
        file.name,
        file.type
      );

      // 2. Upload directly to R2
      const xhr = new XMLHttpRequest();
      xhr.upload.onprogress = (e) => {
        if (e.lengthComputable) {
          setProgress(Math.round((e.loaded / e.total) * 100));
        }
      };

      await new Promise((resolve, reject) => {
        xhr.onload = () => xhr.status === 200 ? resolve() : reject();
        xhr.onerror = reject;
        xhr.open('PUT', upload_url);
        xhr.setRequestHeader('Content-Type', file.type);
        xhr.send(file);
      });

      // 3. Confirm upload
      await api.confirmUpload(document_id, file.size);

      // 4. Optionally trigger AI analysis
      await api.analyzeDocument(document_id);

      onComplete?.(document_id);
    } catch (error) {
      console.error('Upload failed:', error);
      // Show error to user
    } finally {
      setUploading(false);
    }
  };

  return (
    <div className="document-upload">
      <input
        type="file"
        accept="image/*,.pdf"
        onChange={handleFileSelect}
        disabled={uploading}
      />
      {uploading && (
        <div className="progress-bar">
          <div className="progress" style={{ width: `${progress}%` }} />
        </div>
      )}
    </div>
  );
}
```

---

### 6. Real-time Updates (WebSocket)

**Backend Ready:** ARQ workers can publish events to Redis pub/sub.

**Frontend Implementation:**

```jsx
// src/hooks/useRealtimeUpdates.js
import { useEffect } from 'react';
import { useQueryClient } from '@tanstack/react-query';

export function useRealtimeUpdates() {
  const queryClient = useQueryClient();

  useEffect(() => {
    const ws = new WebSocket(process.env.REACT_APP_WS_URL);

    ws.onmessage = (event) => {
      const data = JSON.parse(event.data);

      switch (data.type) {
        case 'applicant.updated':
          queryClient.invalidateQueries(['applicant', data.applicant_id]);
          queryClient.invalidateQueries(['applicants']);
          break;
        case 'screening.completed':
          queryClient.invalidateQueries(['screeningChecks']);
          queryClient.invalidateQueries(['applicant', data.applicant_id]);
          break;
        case 'document.processed':
          queryClient.invalidateQueries(['applicant', data.applicant_id]);
          break;
        // Add more event types
      }
    };

    return () => ws.close();
  }, [queryClient]);
}
```

---

## Frontend Build Checklist

### Phase 1: Foundation ✅ COMPLETE (Sprints 1-4)

- [x] **Authentication** (Sprint 1)
  - [x] Install and configure Auth0 React SDK
  - [x] Create login/logout flows
  - [x] Protect routes requiring authentication
  - [x] Pass JWT tokens to all API calls

- [x] **API Service Layer** (Sprint 2)
  - [x] Create centralized API client
  - [x] Add error handling and retry logic
  - [x] Handle 401/403 responses (redirect to login)

- [x] **Applicants Module** (Sprint 3)
  - [x] Replace mock data with API calls in ApplicantsList
  - [x] Implement real filtering and search
  - [x] Connect ApplicantDetail to real data
  - [x] Wire up Approve/Reject buttons to review API
  - [x] Implement evidence pack download

- [x] **Document Upload** (Sprint 4)
  - [x] Implement presigned URL upload flow
  - [x] Show upload progress with stages
  - [x] Display document status (pending, processing, verified, failed)
  - [x] Show extracted OCR data and AI analysis
  - [x] Multi-file upload for front/back (driver's license, ID card)
  - [x] Image thumbnail preview before upload
  - [x] File magic byte validation for security
  - [x] Drag & drop with visual feedback
  - [x] Document preview modal with zoom/rotation

### Phase 2: Core Features ✅ COMPLETE (Sprints 5-6)

- [x] **Screening Module** (Sprint 5) ✅ COMPLETE
  - [x] Connect ScreeningChecks to API
  - [x] Implement "Run New Check" flow
  - [x] Wire up hit resolution buttons
  - [x] Show AI suggestions for hits
  - [x] Add useScreeningLists hook for list sources
  - [x] Loading skeletons and error states

- [x] **Case Management** (Sprint 6) ✅ COMPLETE
  - [x] Connect CaseManagement to API
  - [x] Implement case creation
  - [x] Wire up note adding
  - [x] Implement case resolution flow
  - [x] Toast notifications for all mutations

- [x] **AI Features** (Sprint 6) ✅ COMPLETE
  - [x] Connect ApplicantAssistant to real AI API
  - [x] Show real risk summaries in applicant detail
  - [x] Implement document analysis display

### Phase 3: Polish ✅ COMPLETE (Sprint 7)

- [x] **Error Handling**
  - [x] Add error boundaries
  - [x] Show user-friendly error messages
  - [x] Implement retry mechanisms

- [x] **Loading States**
  - [x] Show loading spinners during API calls (LoadingSpinner component)
  - [x] Add skeleton loaders
  - [x] Optimistic updates for better UX

- [x] **Real-time Updates** ✅ COMPLETE
  - [x] Implement WebSocket connection (useRealtimeUpdates)
  - [x] Auto-reconnect with exponential backoff
  - [x] Auto-refresh queries on events (applicants, screening, cases, documents)
  - [x] Show notifications for important events

- [x] **Permissions** ✅ COMPLETE
  - [x] usePermissions hook with can(), canAny(), canAll()
  - [x] PermissionGate component for conditional rendering
  - [x] useDisabledForPermission for button states
  - [x] Convenience flags (canReviewApplicants, canResolveCases, etc.)

- [x] **404 Page**
  - [x] NotFoundPage component with suggestions
  - [x] ResourceNotFound for inline use

---

## Environment Configuration

### Development (.env.development)

```env
REACT_APP_API_BASE_URL=http://localhost:8000/api/v1
REACT_APP_WS_URL=ws://localhost:8000/ws
REACT_APP_AUTH0_DOMAIN=dev-getclearance.auth0.com
REACT_APP_AUTH0_CLIENT_ID=your-dev-client-id
REACT_APP_AUTH0_AUDIENCE=https://api.getclearance.dev
```

### Production (.env.production)

```env
REACT_APP_API_BASE_URL=https://api.getclearance.com/api/v1
REACT_APP_WS_URL=wss://api.getclearance.com/ws
REACT_APP_AUTH0_DOMAIN=getclearance.auth0.com
REACT_APP_AUTH0_CLIENT_ID=your-prod-client-id
REACT_APP_AUTH0_AUDIENCE=https://api.getclearance.com
```

---

## Recommended Package Additions

```bash
# Authentication
npm install @auth0/auth0-react

# Server State Management
npm install @tanstack/react-query

# Routing (if not already installed)
npm install react-router-dom

# Form Handling
npm install react-hook-form zod @hookform/resolvers

# Date Handling
npm install date-fns

# HTTP Client (optional, for advanced features)
npm install axios

# Toast Notifications
npm install react-hot-toast
```

---

## Estimated Effort

| Phase | Tasks | Effort |
|-------|-------|--------|
| Phase 1 (Foundation) | Auth + API + Applicants + Documents | 2-3 sprints |
| Phase 2 (Core) | Screening + Cases + AI | 2 sprints |
| Phase 3 (Polish) | Error handling + Loading + Real-time | 1-2 sprints |

**Total: ~5-7 sprints (10-14 weeks with 2-week sprints)**

This estimate assumes a single frontend developer working full-time. The UI is already built - the work is connecting it to the backend.

---

## Testing the Integration

### Local Development Setup

1. Start the backend:
```bash
cd backend
docker-compose up -d  # Postgres, Redis
python -m uvicorn app.main:app --reload
```

2. Start the frontend:
```bash
cd frontend
npm install
npm start
```

3. The backend has development mode that returns mock auth tokens when Auth0 isn't configured, allowing you to test API integration before setting up Auth0.

### API Testing

Use the auto-generated OpenAPI docs at `http://localhost:8000/docs` to:
- Explore all available endpoints
- Test API calls directly
- See request/response schemas

---

## Conclusion

The backend is production-ready and comprehensive. The frontend is now ~98% complete with Sprints 1-7 done.

**What's Complete:**
1. ✅ Authentication (Auth0 login/logout, protected routes)
2. ✅ API service layer (all endpoints connected)
3. ✅ Applicants module (real API, CRUD, review, batch actions)
4. ✅ Document upload (presigned URLs, multi-file, magic bytes)
5. ✅ Screening module (run checks, resolve hits, AI suggestions)
6. ✅ Cases & AI (real API, toast notifications)
7. ✅ Polish (WebSocket real-time, permissions, loading states, 404)

**What Remains:**
- ⏳ Sprint 8: Dashboard with real stats from API

The frontend is fully functional and production-ready for core KYC workflows.
