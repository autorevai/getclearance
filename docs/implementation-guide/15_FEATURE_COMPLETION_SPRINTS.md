# Feature Completion Sprints - Placeholder to Production
**Purpose:** Plan implementation of all placeholder features to make them fully functional
**Created:** December 2, 2025
**Status:** Planning

---

## Current State

The application has **8 placeholder pages** that show "Coming Soon":

| Feature | Current Status | Priority | Backend Required | Frontend Required |
|---------|---------------|----------|------------------|-------------------|
| Companies/KYB | Placeholder | P1 | Full implementation | Full implementation |
| Integrations | Placeholder | P1 | API key management | Settings UI |
| Device Intelligence | Placeholder (BETA) | P2 | Device fingerprinting service | Dashboard |
| Reusable KYC | Placeholder (BETA) | P3 | Token/sharing system | Share flow UI |
| Analytics | Placeholder | P1 | Report generation | Charts/dashboards |
| Settings | Placeholder | P0 | Settings storage | Full settings UI |
| Billing & Usage | Placeholder | P2 | Usage tracking/Stripe | Billing dashboard |
| Audit Log | Placeholder | P0 | Query interface | Log viewer UI |

---

## Sprint Priorities

### Priority 0 (Must Have - Week 1-2)
- **Settings Page** - Users need to configure the system
- **Audit Log Page** - Compliance requirement

### Priority 1 (Should Have - Week 3-5)
- **Companies/KYB** - Core product feature
- **Integrations** - API key management for customers
- **Analytics** - Reporting for compliance

### Priority 2 (Nice to Have - Week 6-8)
- **Device Intelligence** - Advanced fraud detection
- **Billing & Usage** - Monetization

### Priority 3 (Future - Week 9+)
- **Reusable KYC** - Portable identity feature

---

## Sprint 10: Settings Page (P0 - 3-4 Days)

### Why This Sprint?
Users need to configure workflows, team permissions, notifications, and branding. Currently no way to change any settings.

### Backend Tasks

**Files to create:**
1. `backend/app/api/v1/settings.py` - Settings CRUD endpoints
2. `backend/app/models/settings.py` - Settings model
3. `backend/app/schemas/settings.py` - Request/response schemas

**Endpoints to create:**
```
GET  /api/v1/settings                    - Get all tenant settings
PUT  /api/v1/settings                    - Update settings
GET  /api/v1/settings/team               - List team members
POST /api/v1/settings/team/invite        - Invite team member
PUT  /api/v1/settings/team/{id}/role     - Update member role
DELETE /api/v1/settings/team/{id}        - Remove team member
GET  /api/v1/settings/workflows          - List workflow templates
PUT  /api/v1/settings/workflows/{id}     - Update workflow
GET  /api/v1/settings/notifications      - Get notification preferences
PUT  /api/v1/settings/notifications      - Update notification preferences
```

**Database changes:**
```sql
CREATE TABLE tenant_settings (
  id UUID PRIMARY KEY,
  tenant_id UUID REFERENCES tenants(id),
  category VARCHAR(50),  -- 'general', 'notifications', 'branding', 'security'
  key VARCHAR(100),
  value JSONB,
  updated_at TIMESTAMP,
  updated_by UUID
);

CREATE TABLE team_invitations (
  id UUID PRIMARY KEY,
  tenant_id UUID,
  email VARCHAR(255),
  role VARCHAR(50),
  invited_by UUID,
  invited_at TIMESTAMP,
  accepted_at TIMESTAMP,
  expires_at TIMESTAMP
);
```

### Frontend Tasks

**Files to create:**
1. `frontend/src/components/settings/SettingsPage.jsx` - Main settings page
2. `frontend/src/components/settings/GeneralSettings.jsx` - General tab
3. `frontend/src/components/settings/TeamSettings.jsx` - Team management tab
4. `frontend/src/components/settings/WorkflowSettings.jsx` - Workflow config tab
5. `frontend/src/components/settings/NotificationSettings.jsx` - Notification preferences
6. `frontend/src/components/settings/SecuritySettings.jsx` - 2FA, sessions
7. `frontend/src/components/settings/BrandingSettings.jsx` - Logo, colors
8. `frontend/src/hooks/useSettings.js` - Settings hooks
9. `frontend/src/services/settings.js` - Settings API service

**UI Requirements:**
- Tabbed interface (General | Team | Workflows | Notifications | Security | Branding)
- Team member list with role badges
- Invite member modal with email input and role selector
- Toggle switches for notifications
- Color picker for branding
- Save/Cancel buttons with confirmation

### Success Criteria
- [ ] Can view current settings
- [ ] Can update company name and logo
- [ ] Can invite team members via email
- [ ] Can change team member roles
- [ ] Can remove team members
- [ ] Can enable/disable email notifications
- [ ] Can configure SLA thresholds
- [ ] Settings persist after page refresh

---

## Sprint 11: Audit Log Page (P0 - 2-3 Days)

### Why This Sprint?
Compliance auditors need to see who did what and when. The audit_logs table exists but has no UI.

### Backend Tasks

**Files to modify:**
1. `backend/app/api/v1/audit.py` - Audit log query endpoints

**Endpoints to create:**
```
GET  /api/v1/audit-log                   - List audit entries (paginated)
GET  /api/v1/audit-log/{id}              - Get single audit entry
GET  /api/v1/audit-log/export            - Export to CSV/PDF
GET  /api/v1/audit-log/verify            - Verify chain integrity
```

**Query parameters for list endpoint:**
- `entity_type` - Filter by type (applicant, case, screening_hit, document)
- `entity_id` - Filter by specific entity
- `actor_id` - Filter by user who performed action
- `action` - Filter by action type (created, updated, deleted, reviewed)
- `start_date` - Date range start
- `end_date` - Date range end
- `limit` / `offset` - Pagination

### Frontend Tasks

**Files to create:**
1. `frontend/src/components/audit/AuditLogPage.jsx` - Main audit log page
2. `frontend/src/components/audit/AuditLogTable.jsx` - Table with filtering
3. `frontend/src/components/audit/AuditLogFilters.jsx` - Filter controls
4. `frontend/src/components/audit/AuditLogDetail.jsx` - Entry detail modal
5. `frontend/src/hooks/useAuditLog.js` - Audit hooks
6. `frontend/src/services/audit.js` - Audit API service

**UI Requirements:**
- Searchable, filterable table
- Date range picker
- Entity type filter dropdown
- User filter dropdown
- Action type filter
- Export to CSV button
- Click row to see full details (old value → new value)
- Chain verification status indicator
- Infinite scroll or pagination

### Success Criteria
- [ ] Can view all audit entries
- [ ] Can filter by date range
- [ ] Can filter by entity type
- [ ] Can filter by user
- [ ] Can see before/after values
- [ ] Can export to CSV
- [ ] Can verify chain integrity

---

## Sprint 12: Analytics Page (P1 - 4-5 Days)

### Why This Sprint?
Compliance teams need reports on verification volumes, pass/fail rates, processing times, and risk distributions.

### Backend Tasks

**Files to create:**
1. `backend/app/api/v1/analytics.py` - Analytics endpoints
2. `backend/app/services/analytics.py` - Report generation logic

**Endpoints to create:**
```
GET  /api/v1/analytics/overview          - Summary metrics
GET  /api/v1/analytics/funnel            - Verification funnel
GET  /api/v1/analytics/trends            - Time series data
GET  /api/v1/analytics/geography         - Geographic distribution
GET  /api/v1/analytics/risk              - Risk score distribution
GET  /api/v1/analytics/sla               - SLA performance
GET  /api/v1/analytics/export            - Export report (PDF/CSV)
```

**Report data structure:**
```json
{
  "overview": {
    "total_verifications": 1234,
    "approval_rate": 85.5,
    "avg_processing_time_hours": 2.4,
    "risk_score_avg": 32
  },
  "funnel": {
    "started": 1500,
    "documents_submitted": 1400,
    "screening_passed": 1300,
    "approved": 1050,
    "rejected": 150
  },
  "trends": [
    { "date": "2025-12-01", "applications": 45, "approved": 38, "rejected": 4 }
  ]
}
```

### Frontend Tasks

**Files to create:**
1. `frontend/src/components/analytics/AnalyticsPage.jsx` - Main page
2. `frontend/src/components/analytics/OverviewCards.jsx` - KPI cards
3. `frontend/src/components/analytics/FunnelChart.jsx` - Verification funnel
4. `frontend/src/components/analytics/TrendsChart.jsx` - Time series
5. `frontend/src/components/analytics/GeoMap.jsx` - Geographic heat map
6. `frontend/src/components/analytics/RiskDistribution.jsx` - Risk histogram
7. `frontend/src/components/analytics/SLAPerformance.jsx` - SLA metrics
8. `frontend/src/hooks/useAnalytics.js` - Analytics hooks
9. `frontend/src/services/analytics.js` - Analytics API

**Libraries to add:**
- `recharts` or `chart.js` for charts
- `react-simple-maps` for geography (optional)

**UI Requirements:**
- Date range selector
- KPI cards at top (total, approval rate, avg time, avg risk)
- Verification funnel visualization
- Line chart for trends over time
- Bar chart for geographic distribution
- Histogram for risk score distribution
- SLA gauge showing % on-time
- Export report button (PDF)

### Success Criteria
- [ ] Can see overall KPIs
- [ ] Can view verification funnel
- [ ] Can see trends over time
- [ ] Can filter by date range
- [ ] Can export report to PDF
- [ ] Charts are interactive

---

## Sprint 13: Integrations Page (P1 - 3-4 Days)

### Why This Sprint?
Customers need to manage API keys and configure webhooks for their applications.

### Backend Tasks

**Files to create:**
1. `backend/app/api/v1/integrations.py` - API key and webhook management
2. `backend/app/models/api_key.py` - API key model
3. `backend/app/models/webhook.py` - Webhook configuration model

**Endpoints to create:**
```
# API Keys
GET    /api/v1/integrations/api-keys          - List API keys
POST   /api/v1/integrations/api-keys          - Create API key
DELETE /api/v1/integrations/api-keys/{id}     - Revoke API key
POST   /api/v1/integrations/api-keys/{id}/rotate - Rotate key

# Webhooks
GET    /api/v1/integrations/webhooks          - List webhooks
POST   /api/v1/integrations/webhooks          - Create webhook
PUT    /api/v1/integrations/webhooks/{id}     - Update webhook
DELETE /api/v1/integrations/webhooks/{id}     - Delete webhook
POST   /api/v1/integrations/webhooks/{id}/test - Send test event
GET    /api/v1/integrations/webhooks/{id}/logs - Delivery logs
```

**Database changes:**
```sql
CREATE TABLE api_keys (
  id UUID PRIMARY KEY,
  tenant_id UUID,
  name VARCHAR(100),
  key_hash VARCHAR(64),  -- SHA-256 of actual key
  key_prefix VARCHAR(8), -- First 8 chars for display
  permissions JSONB,     -- ['read:applicants', 'write:applicants']
  last_used_at TIMESTAMP,
  expires_at TIMESTAMP,
  created_at TIMESTAMP,
  created_by UUID
);

CREATE TABLE webhook_configs (
  id UUID PRIMARY KEY,
  tenant_id UUID,
  url VARCHAR(500),
  secret VARCHAR(64),   -- For HMAC signature
  events JSONB,         -- ['applicant.approved', 'applicant.rejected']
  active BOOLEAN,
  created_at TIMESTAMP
);
```

### Frontend Tasks

**Files to create:**
1. `frontend/src/components/integrations/IntegrationsPage.jsx` - Main page
2. `frontend/src/components/integrations/ApiKeysTab.jsx` - API key management
3. `frontend/src/components/integrations/WebhooksTab.jsx` - Webhook configuration
4. `frontend/src/components/integrations/CreateApiKeyModal.jsx` - Create key modal
5. `frontend/src/components/integrations/CreateWebhookModal.jsx` - Create webhook modal
6. `frontend/src/components/integrations/WebhookLogs.jsx` - Delivery log viewer
7. `frontend/src/hooks/useIntegrations.js` - Integration hooks
8. `frontend/src/services/integrations.js` - Integration API

**UI Requirements:**
- Tabs: API Keys | Webhooks | Connected Services
- API Keys: Table with name, prefix (sk_live_xxxx...), last used, actions
- Create key modal with name, permissions checkboxes
- Show full key ONCE on creation (copyable)
- Webhooks: Table with URL, events, status, last delivery
- Test webhook button
- Webhook delivery log with status, timestamp, response

### Success Criteria
- [ ] Can create/revoke API keys
- [ ] Key shown once on creation
- [ ] Can configure webhooks
- [ ] Can test webhooks
- [ ] Can view delivery logs
- [ ] HMAC signature generation works

---

## Sprint 14: Companies/KYB Module (P1 - 5-7 Days)

### Why This Sprint?
KYB (Know Your Business) is a major feature for verifying corporate entities, not just individuals.

### Backend Tasks

**Files to create:**
1. `backend/app/models/company.py` - Company entity model
2. `backend/app/models/beneficial_owner.py` - UBO model
3. `backend/app/api/v1/companies.py` - Company endpoints
4. `backend/app/services/kyb_screening.py` - Business screening

**Endpoints to create:**
```
GET    /api/v1/companies                     - List companies
POST   /api/v1/companies                     - Create company
GET    /api/v1/companies/{id}                - Get company details
PUT    /api/v1/companies/{id}                - Update company
DELETE /api/v1/companies/{id}                - Delete company
POST   /api/v1/companies/{id}/verify         - Start verification
GET    /api/v1/companies/{id}/ubos           - List beneficial owners
POST   /api/v1/companies/{id}/ubos           - Add beneficial owner
PUT    /api/v1/companies/{id}/ubos/{ubo_id}  - Update UBO
GET    /api/v1/companies/{id}/documents      - Company documents
GET    /api/v1/companies/{id}/structure      - Corporate structure tree
```

**Database schema:**
```sql
CREATE TABLE companies (
  id UUID PRIMARY KEY,
  tenant_id UUID,
  legal_name VARCHAR(500),
  trading_name VARCHAR(500),
  registration_number VARCHAR(100),
  jurisdiction VARCHAR(100),
  incorporation_date DATE,
  company_type VARCHAR(50),  -- 'corporation', 'llc', 'partnership'
  status VARCHAR(50),        -- 'pending', 'verified', 'rejected'
  risk_level VARCHAR(20),
  address JSONB,
  created_at TIMESTAMP
);

CREATE TABLE beneficial_owners (
  id UUID PRIMARY KEY,
  company_id UUID REFERENCES companies(id),
  applicant_id UUID REFERENCES applicants(id),  -- Link to KYC
  ownership_percentage DECIMAL(5,2),
  role VARCHAR(100),
  is_controlling BOOLEAN,
  verified BOOLEAN,
  created_at TIMESTAMP
);
```

### Frontend Tasks

**Files to create:**
1. `frontend/src/components/companies/CompaniesPage.jsx` - Main list
2. `frontend/src/components/companies/CompanyDetail.jsx` - Detail view
3. `frontend/src/components/companies/CompanyForm.jsx` - Create/edit
4. `frontend/src/components/companies/UBOList.jsx` - Beneficial owners
5. `frontend/src/components/companies/CorporateStructure.jsx` - Tree view
6. `frontend/src/hooks/useCompanies.js` - Company hooks
7. `frontend/src/services/companies.js` - Company API

**UI Requirements:**
- Company list with status badges
- Company detail page with tabs (Overview | Documents | UBOs | Structure)
- UBO list showing ownership % and verification status
- Corporate structure tree diagram
- Link UBOs to individual applicant KYC
- Status workflow (Pending → In Review → Verified/Rejected)

### Success Criteria
- [ ] Can create companies
- [ ] Can add beneficial owners
- [ ] Can link UBOs to individual KYC
- [ ] Can upload company documents
- [ ] Can view corporate structure
- [ ] Company screening runs

---

## Sprint 15: Device Intelligence (P2 - 4-5 Days)

### Why This Sprint?
Advanced fraud detection through device fingerprinting, IP analysis, and behavioral signals.

### Backend Tasks

**Files to create:**
1. `backend/app/services/device_intel.py` - Device fingerprinting service
2. `backend/app/models/device.py` - Device/session model
3. `backend/app/api/v1/device_intel.py` - Device intel endpoints

**Endpoints to create:**
```
POST /api/v1/device-intel/fingerprint    - Submit device fingerprint
GET  /api/v1/device-intel/device/{id}    - Get device risk info
GET  /api/v1/device-intel/applicant/{id} - Devices for applicant
GET  /api/v1/device-intel/dashboard      - Fraud metrics overview
```

**Device fingerprint data:**
```json
{
  "device_id": "hashed_fingerprint",
  "browser": "Chrome 120",
  "os": "macOS 14.1",
  "screen_resolution": "1920x1080",
  "timezone": "America/New_York",
  "language": "en-US",
  "ip_address": "1.2.3.4",
  "vpn_detected": false,
  "proxy_detected": false,
  "tor_detected": false,
  "bot_probability": 0.02,
  "risk_signals": ["new_device", "timezone_mismatch"]
}
```

### Frontend Tasks

**Files to create:**
1. `frontend/src/components/device-intel/DeviceIntelPage.jsx`
2. `frontend/src/components/device-intel/DeviceRiskCard.jsx`
3. `frontend/src/components/device-intel/FraudDashboard.jsx`
4. `frontend/src/hooks/useDeviceIntel.js`
5. `frontend/src/services/deviceIntel.js`

### Success Criteria
- [ ] Can view device fingerprints
- [ ] Can see VPN/proxy detection
- [ ] Can view fraud signals
- [ ] Dashboard shows fraud metrics

---

## Sprint 16: Billing & Usage (P2 - 4-5 Days)

### Why This Sprint?
Track usage metrics and integrate with Stripe for billing.

### Backend Tasks

**Files to create:**
1. `backend/app/services/usage.py` - Usage tracking
2. `backend/app/services/billing.py` - Stripe integration
3. `backend/app/api/v1/billing.py` - Billing endpoints

**Endpoints to create:**
```
GET  /api/v1/billing/usage              - Current period usage
GET  /api/v1/billing/usage/history      - Historical usage
GET  /api/v1/billing/subscription       - Current subscription
POST /api/v1/billing/subscription       - Update subscription
GET  /api/v1/billing/invoices           - Invoice list
GET  /api/v1/billing/invoices/{id}/pdf  - Download invoice
POST /api/v1/billing/payment-method     - Add payment method
```

### Frontend Tasks

**Files to create:**
1. `frontend/src/components/billing/BillingPage.jsx`
2. `frontend/src/components/billing/UsageDashboard.jsx`
3. `frontend/src/components/billing/SubscriptionCard.jsx`
4. `frontend/src/components/billing/InvoiceList.jsx`
5. `frontend/src/hooks/useBilling.js`
6. `frontend/src/services/billing.js`

### Success Criteria
- [ ] Can view current usage
- [ ] Can view subscription status
- [ ] Can download invoices
- [ ] Stripe integration works

---

## Sprint 17: Reusable KYC (P3 - 5-7 Days)

### Why This Sprint?
Allow verified users to share their KYC with other services (portable identity).

### Backend Tasks

**Files to create:**
1. `backend/app/models/kyc_share.py` - Share token model
2. `backend/app/api/v1/kyc_share.py` - Share endpoints
3. `backend/app/services/kyc_share.py` - Token generation/validation

**Endpoints:**
```
POST /api/v1/kyc-share/token           - Generate share token
GET  /api/v1/kyc-share/verify/{token}  - Verify share token
POST /api/v1/kyc-share/revoke/{token}  - Revoke share token
GET  /api/v1/kyc-share/history         - Share history
```

### Frontend Tasks

**Files to create:**
1. `frontend/src/components/kyc-share/ReusableKYCPage.jsx`
2. `frontend/src/components/kyc-share/ShareTokenGenerator.jsx`
3. `frontend/src/components/kyc-share/ShareHistory.jsx`
4. `frontend/src/components/kyc-share/ConsentFlow.jsx`

### Success Criteria
- [ ] Can generate share tokens
- [ ] Can verify tokens
- [ ] Can revoke tokens
- [ ] Consent flow works

---

## Timeline Summary

| Week | Sprints | Focus |
|------|---------|-------|
| 1-2 | Sprint 10, 11 | Settings + Audit Log (P0) |
| 3-5 | Sprint 12, 13, 14 | Analytics + Integrations + KYB (P1) |
| 6-8 | Sprint 15, 16 | Device Intel + Billing (P2) |
| 9+ | Sprint 17 | Reusable KYC (P3) |

**Total estimated: 8-10 weeks for full feature completion**

---

## Pre-Sprint Checklist

Before starting each sprint:
- [ ] Backend Sprint X completed (if dependent)
- [ ] Database migrations ready
- [ ] API documentation updated
- [ ] Frontend components identified
- [ ] Test cases defined

---

## Notes

1. **Sprints 10-17 depend on Backend Security Sprints 1-6** being complete first
2. **Settings (Sprint 10)** should be done before other features that need configuration
3. **Audit Log (Sprint 11)** should use the audit service from Backend Sprint 1
4. **KYB (Sprint 14)** is a major feature and may take longer than estimated
5. **Device Intelligence (Sprint 15)** may require third-party service integration
6. **Billing (Sprint 16)** requires Stripe account setup
