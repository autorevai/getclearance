# Terminal 3: Placeholder Pages to Production - Copy-Paste Prompts

**Purpose:** Ready-to-use prompts for implementing placeholder pages
**Terminal:** 3 (Frontend + Backend for each feature)
**Prerequisites:** None initially, but some features need Terminal 2 APIs

---

## How to Use This Document

1. Open a NEW Claude Code terminal
2. Copy the entire prompt for the sprint you want to run
3. Paste it and let Claude execute
4. Review, test, and commit before moving to next sprint

---

## Sprint Order (Recommended)

| Sprint | Feature | Depends On | Ready to Start? |
|--------|---------|------------|-----------------|
| S10 | Settings Page | Nothing | YES |
| S11 | Audit Log Page | Audit model exists | YES |
| S12 | Analytics Page | Dashboard stats exist | YES |
| S13 | Integrations Page | Nothing | YES |
| S14 | Companies/KYB | Terminal 2 F2 (KYB Backend) | After T2-F2 |
| S15 | Device Intelligence | Terminal 2 recommends IPQualityScore | After T2 API setup |
| S16 | Billing & Usage | Stripe account | When Stripe ready |
| S17 | Reusable KYC | Most features complete | Last |

---

## Sprint 10: Settings Page (P0)

### Prompt - Copy Everything Below This Line

```
I need you to implement a full Settings page for our compliance platform. Currently there's a placeholder "Coming Soon" page.

## Context Files to Read First
- frontend/src/components/AppShell.jsx (navigation structure)
- frontend/src/App.jsx (routing)
- backend/app/models/tenant.py (tenant model)
- backend/app/api/v1/users.py (user patterns)

## What to Build

### Backend (do this first)

1. Create `backend/app/models/settings.py`:
   - TenantSettings model with: id, tenant_id, category (general/notifications/branding/security), key, value (JSONB), updated_at, updated_by
   - TeamInvitation model with: id, tenant_id, email, role, invited_by, invited_at, accepted_at, expires_at

2. Create `backend/app/schemas/settings.py`:
   - SettingsUpdate schema
   - TeamInviteRequest schema
   - Response schemas

3. Create `backend/app/api/v1/settings.py`:
   - GET /api/v1/settings - Get all tenant settings
   - PUT /api/v1/settings - Update settings
   - GET /api/v1/settings/team - List team members
   - POST /api/v1/settings/team/invite - Invite team member
   - PUT /api/v1/settings/team/{id}/role - Update member role
   - DELETE /api/v1/settings/team/{id} - Remove team member
   - GET /api/v1/settings/notifications - Get notification preferences
   - PUT /api/v1/settings/notifications - Update notification preferences

4. Create migration for settings tables

5. Register routes in `backend/app/api/v1/__init__.py`

### Frontend (after backend)

1. Create `frontend/src/services/settings.js`:
   - getSettings(), updateSettings()
   - getTeamMembers(), inviteTeamMember(), updateTeamMemberRole(), removeTeamMember()
   - getNotificationPreferences(), updateNotificationPreferences()

2. Create `frontend/src/hooks/useSettings.js`:
   - useSettings() hook with React Query

3. Create settings components in `frontend/src/components/settings/`:
   - SettingsPage.jsx - Main page with tabs
   - GeneralSettings.jsx - Company name, timezone
   - TeamSettings.jsx - Team member list, invite modal
   - NotificationSettings.jsx - Toggle switches for email notifications
   - SecuritySettings.jsx - Password requirements, session timeout
   - BrandingSettings.jsx - Logo upload, primary color

4. Update App.jsx to route /settings to SettingsPage

## UI Requirements
- Use Mantine components (Tabs, TextInput, Switch, ColorInput, FileInput)
- Tabbed interface: General | Team | Notifications | Security | Branding
- Team table with columns: Name, Email, Role, Last Active, Actions
- Invite modal with email input and role selector (Admin/Analyst/Viewer)
- Save button with loading state and success notification
- Match existing app styling

## Testing
After implementation:
1. npm run build in frontend (must pass)
2. Test each tab loads
3. Test settings save and persist
4. Test team invite flow

Please implement this now, starting with the backend.
```

---

## Sprint 11: Audit Log Page (P0)

### Prompt - Copy Everything Below This Line

```
I need you to implement a full Audit Log page for our compliance platform. The audit_logs table already exists but has no UI.

## Context Files to Read First
- backend/app/models/audit.py (existing audit model)
- backend/app/services/audit.py (existing audit service)
- frontend/src/components/ApplicantsList.jsx (table patterns)
- frontend/src/hooks/useApplicants.js (hook patterns)

## What to Build

### Backend

1. Create `backend/app/api/v1/audit.py`:
   - GET /api/v1/audit-log - List audit entries with filters:
     - entity_type (applicant, case, screening_hit, document)
     - entity_id
     - actor_id (user who performed action)
     - action (created, updated, deleted, reviewed, approved, rejected)
     - start_date, end_date
     - limit, offset (pagination)
   - GET /api/v1/audit-log/{id} - Get single audit entry details
   - GET /api/v1/audit-log/export - Export to CSV
   - GET /api/v1/audit-log/verify - Verify chain integrity using checksum

2. Create `backend/app/schemas/audit.py`:
   - AuditLogResponse schema
   - AuditLogListResponse with pagination
   - AuditLogFilters schema

3. Register routes in `backend/app/api/v1/__init__.py`

### Frontend

1. Create `frontend/src/services/audit.js`:
   - getAuditLogs(filters), getAuditLogById(id)
   - exportAuditLogs(filters, format)
   - verifyChainIntegrity()

2. Create `frontend/src/hooks/useAuditLog.js`:
   - useAuditLogs(filters)
   - useAuditLogById(id)

3. Create audit components in `frontend/src/components/audit/`:
   - AuditLogPage.jsx - Main page
   - AuditLogTable.jsx - Data table with sorting
   - AuditLogFilters.jsx - Filter controls (dropdowns, date picker)
   - AuditLogDetail.jsx - Modal showing full entry with before/after diff

4. Update App.jsx to route /audit-log to AuditLogPage

## UI Requirements
- Use Mantine Table, Select, DatePickerInput, Modal
- Filters row: Date range picker, Entity type dropdown, User dropdown, Action dropdown
- Table columns: Timestamp, User, Action, Entity Type, Entity ID, Details (truncated)
- Click row to open detail modal
- Detail modal shows: before value vs after value (JSON diff)
- Export CSV button in top right
- Chain verification indicator (green checkmark if valid)
- Infinite scroll or pagination controls

## Important
- The audit model already has `compute_checksum()` for chain verification
- Use the existing audit service patterns
- Ensure proper tenant isolation on all queries

## Testing
After implementation:
1. npm run build in frontend (must pass)
2. Test filters work
3. Test export works
4. Test detail modal shows diff

Please implement this now, starting with the backend API.
```

---

## Sprint 12: Analytics Page (P1)

### Prompt - Copy Everything Below This Line

```
I need you to implement a full Analytics page for our compliance platform. Currently there's a placeholder.

## Context Files to Read First
- backend/app/api/v1/dashboard.py (existing dashboard stats)
- frontend/src/components/Dashboard.jsx (existing dashboard patterns)
- backend/app/models/applicant.py (applicant model)
- backend/app/models/screening.py (screening model)

## What to Build

### Backend

1. Create `backend/app/services/analytics.py`:
   - get_overview_metrics(tenant_id, start_date, end_date)
   - get_verification_funnel(tenant_id, start_date, end_date)
   - get_trends(tenant_id, start_date, end_date, granularity)
   - get_geographic_distribution(tenant_id, start_date, end_date)
   - get_risk_distribution(tenant_id, start_date, end_date)
   - get_sla_performance(tenant_id, start_date, end_date)

2. Create `backend/app/api/v1/analytics.py`:
   - GET /api/v1/analytics/overview - Summary metrics
   - GET /api/v1/analytics/funnel - Verification funnel data
   - GET /api/v1/analytics/trends - Time series by day/week/month
   - GET /api/v1/analytics/geography - Distribution by country
   - GET /api/v1/analytics/risk - Risk score histogram
   - GET /api/v1/analytics/sla - SLA performance metrics
   - GET /api/v1/analytics/export - Export report (CSV or PDF)

3. Create `backend/app/schemas/analytics.py`:
   - OverviewMetrics, FunnelData, TrendPoint, etc.

4. Register routes in `backend/app/api/v1/__init__.py`

### Frontend

1. Install chart library if not present:
   - Add recharts to package.json

2. Create `frontend/src/services/analytics.js`:
   - getOverview(startDate, endDate)
   - getFunnel(startDate, endDate)
   - getTrends(startDate, endDate, granularity)
   - getGeography(startDate, endDate)
   - getRiskDistribution(startDate, endDate)
   - getSlaPerformance(startDate, endDate)
   - exportReport(startDate, endDate, format)

3. Create `frontend/src/hooks/useAnalytics.js`:
   - useOverview(), useFunnel(), useTrends(), etc.

4. Create analytics components in `frontend/src/components/analytics/`:
   - AnalyticsPage.jsx - Main page with date range selector
   - OverviewCards.jsx - KPI cards (total verifications, approval rate, avg time, avg risk)
   - FunnelChart.jsx - Verification funnel visualization
   - TrendsChart.jsx - Line chart for applications over time
   - GeoDistribution.jsx - Bar chart by country
   - RiskHistogram.jsx - Risk score distribution
   - SLAGauge.jsx - Circular gauge showing % on-time

5. Update App.jsx to route /analytics to AnalyticsPage

## UI Requirements
- Date range selector at top (preset: Last 7 days, Last 30 days, Last 90 days, Custom)
- Grid of KPI cards at top
- 2x2 grid of charts below
- Export Report button (PDF or CSV)
- Use Mantine Paper for cards, recharts for charts
- Responsive layout

## Data Calculations
- Approval Rate = approved / (approved + rejected) * 100
- Avg Processing Time = avg(approved_at - created_at) in hours
- SLA On-Time = cases resolved within 24hrs / total resolved

## Testing
After implementation:
1. npm run build in frontend (must pass)
2. Test date range changes update charts
3. Test export generates file
4. Verify calculations match expected

Please implement this now, starting with the backend service.
```

---

## Sprint 13: Integrations Page (P1)

### Prompt - Copy Everything Below This Line

```
I need you to implement a full Integrations page for API key and webhook management.

## Context Files to Read First
- backend/app/api/v1/__init__.py (route registration)
- frontend/src/components/settings/ (if exists, for patterns)
- backend/app/core/security.py (for secure key generation patterns)

## What to Build

### Backend

1. Create `backend/app/models/api_key.py`:
   - ApiKey model: id, tenant_id, name, key_hash (SHA-256), key_prefix (first 8 chars), permissions (JSONB), last_used_at, expires_at, created_at, created_by, revoked_at

2. Create `backend/app/models/webhook.py`:
   - WebhookConfig model: id, tenant_id, url, secret (for HMAC), events (JSONB array), active, failure_count, last_success_at, created_at
   - WebhookDelivery model: id, webhook_id, event_type, payload, response_code, response_body, delivered_at

3. Create migrations for both tables

4. Create `backend/app/services/integrations.py`:
   - generate_api_key() - returns full key, stores hash
   - verify_api_key(key) - verifies against hash
   - sign_webhook_payload(secret, payload) - HMAC-SHA256
   - send_webhook(webhook_id, event, payload)

5. Create `backend/app/api/v1/integrations.py`:
   - GET /api/v1/integrations/api-keys - List API keys (show prefix only)
   - POST /api/v1/integrations/api-keys - Create API key (return full key ONCE)
   - DELETE /api/v1/integrations/api-keys/{id} - Revoke key
   - POST /api/v1/integrations/api-keys/{id}/rotate - Rotate key
   - GET /api/v1/integrations/webhooks - List webhooks
   - POST /api/v1/integrations/webhooks - Create webhook
   - PUT /api/v1/integrations/webhooks/{id} - Update webhook
   - DELETE /api/v1/integrations/webhooks/{id} - Delete webhook
   - POST /api/v1/integrations/webhooks/{id}/test - Send test event
   - GET /api/v1/integrations/webhooks/{id}/logs - Get delivery logs

6. Create `backend/app/schemas/integrations.py`:
   - ApiKeyCreate, ApiKeyResponse, ApiKeyCreatedResponse (includes full key)
   - WebhookCreate, WebhookUpdate, WebhookResponse
   - WebhookDeliveryResponse

7. Register routes in `backend/app/api/v1/__init__.py`

### Frontend

1. Create `frontend/src/services/integrations.js`:
   - API key CRUD functions
   - Webhook CRUD functions
   - testWebhook(id), getWebhookLogs(id)

2. Create `frontend/src/hooks/useIntegrations.js`:
   - useApiKeys(), useWebhooks(), useWebhookLogs(id)

3. Create integration components in `frontend/src/components/integrations/`:
   - IntegrationsPage.jsx - Main page with tabs
   - ApiKeysTab.jsx - API key list and management
   - CreateApiKeyModal.jsx - Create key with name and permissions
   - KeyCreatedModal.jsx - Shows full key ONCE with copy button
   - WebhooksTab.jsx - Webhook list and management
   - CreateWebhookModal.jsx - URL, events checkboxes
   - WebhookLogsModal.jsx - Delivery log table

4. Update App.jsx to route /integrations to IntegrationsPage

## UI Requirements
- Tabs: API Keys | Webhooks
- API Keys table: Name, Key Prefix (sk_live_xxxx...), Created, Last Used, Actions
- Create key modal: Name input, Permission checkboxes (read:applicants, write:applicants, etc.)
- Key created modal: Show full key with copy button, warning "This will only be shown once"
- Webhooks table: URL, Events, Status (Active/Paused), Last Delivery, Actions
- Create webhook: URL input, Event checkboxes, Active toggle
- Test button with success/failure feedback
- Logs modal: Table with timestamp, status code, response time

## Security
- NEVER store full API keys, only hashes
- Generate keys with secrets.token_urlsafe(32)
- HMAC signature: X-Webhook-Signature header

## Testing
After implementation:
1. npm run build in frontend (must pass)
2. Test create API key shows key once
3. Test create webhook
4. Test webhook test delivery
5. Test revoke key

Please implement this now, starting with the backend models.
```

---

## Sprint 14: Companies/KYB Module (P1)

### Prerequisites
- Terminal 2 Sprint F2 (KYB Backend) should be complete first

### Prompt - Copy Everything Below This Line

```
I need you to implement a full Companies/KYB (Know Your Business) module.

## Context Files to Read First
- backend/app/models/applicant.py (applicant patterns)
- backend/app/api/v1/applicants.py (CRUD patterns)
- frontend/src/components/ApplicantsList.jsx (list patterns)
- frontend/src/components/ApplicantDetail.jsx (detail patterns)

## What to Build

### Backend

1. Create `backend/app/models/company.py`:
   - Company model: id, tenant_id, legal_name, trading_name, registration_number, jurisdiction, incorporation_date, company_type (corporation/llc/partnership), status (pending/in_review/verified/rejected), risk_level, address (JSONB), industry, website, phone, created_at, updated_at

2. Create `backend/app/models/beneficial_owner.py`:
   - BeneficialOwner model: id, company_id (FK), applicant_id (FK to link KYC), first_name, last_name, ownership_percentage, role, is_controlling, is_pep, verified, created_at

3. Create migrations

4. Create `backend/app/services/kyb_verification.py`:
   - verify_company(company_id) - Run company through screening
   - check_beneficial_owners(company_id) - Verify all UBOs have completed KYC
   - calculate_company_risk(company_id) - Aggregate risk score

5. Create `backend/app/api/v1/companies.py`:
   - GET /api/v1/companies - List companies with filters
   - POST /api/v1/companies - Create company
   - GET /api/v1/companies/{id} - Get company details
   - PUT /api/v1/companies/{id} - Update company
   - DELETE /api/v1/companies/{id} - Delete company
   - POST /api/v1/companies/{id}/verify - Start verification
   - GET /api/v1/companies/{id}/ubos - List beneficial owners
   - POST /api/v1/companies/{id}/ubos - Add beneficial owner
   - PUT /api/v1/companies/{id}/ubos/{ubo_id} - Update UBO
   - DELETE /api/v1/companies/{id}/ubos/{ubo_id} - Remove UBO
   - GET /api/v1/companies/{id}/documents - List company documents
   - POST /api/v1/companies/{id}/documents - Upload company document
   - GET /api/v1/companies/{id}/screening - Get screening results

6. Create `backend/app/schemas/company.py`:
   - CompanyCreate, CompanyUpdate, CompanyResponse
   - BeneficialOwnerCreate, BeneficialOwnerResponse
   - CompanyListResponse with pagination

7. Register routes

### Frontend

1. Create `frontend/src/services/companies.js`:
   - Full CRUD for companies and UBOs
   - verifyCompany(id), getCompanyScreening(id)

2. Create `frontend/src/hooks/useCompanies.js`:
   - useCompanies(filters), useCompany(id)
   - useCompanyUBOs(companyId)
   - useCompanyScreening(companyId)

3. Create company components in `frontend/src/components/companies/`:
   - CompaniesPage.jsx - List page with filters
   - CompanyDetail.jsx - Detail page with tabs
   - CompanyForm.jsx - Create/edit form
   - CompanyOverview.jsx - Overview tab
   - UBOList.jsx - Beneficial owners tab
   - AddUBOModal.jsx - Add UBO modal (can link to existing applicant)
   - CompanyDocuments.jsx - Documents tab
   - CompanyScreening.jsx - Screening results tab

4. Update App.jsx to route /companies and /companies/:id

## UI Requirements
- Companies list: Table with Name, Reg #, Jurisdiction, Status, Risk, UBO Count
- Status badges: Pending (gray), In Review (blue), Verified (green), Rejected (red)
- Detail page tabs: Overview | Beneficial Owners | Documents | Screening
- UBO list: Table with Name, Ownership %, Role, Verified status
- Add UBO: Can create new OR link to existing applicant for KYC
- Corporate structure could show ownership percentages visually

## Business Logic
- Company can't be Verified until all UBOs with >25% ownership are verified
- Risk score aggregates: company jurisdiction risk + UBO risk scores + screening hits
- UBOs should link to individual applicant KYC records

## Testing
After implementation:
1. npm run build in frontend (must pass)
2. Test create company
3. Test add UBO and link to applicant
4. Test start verification
5. Test status workflow

Please implement this now, starting with the backend models.
```

---

## Sprint 15: Device Intelligence (P2)

### Prerequisites
- Consider using IPQualityScore API (see `16_API_INTEGRATIONS_VS_BUILD.md`)

### Prompt - Copy Everything Below This Line

```
I need you to implement Device Intelligence using IPQualityScore API for fraud detection.

## Context Files to Read First
- docs/implementation-guide/16_API_INTEGRATIONS_VS_BUILD.md (API integration guide)
- backend/app/services/screening.py (external API patterns)
- backend/app/core/config.py (config patterns)

## What to Build

### Backend

1. Add to `backend/app/core/config.py`:
   - IPQUALITYSCORE_API_KEY setting from env

2. Create `backend/app/models/device.py`:
   - DeviceFingerprint model: id, applicant_id (FK), session_id, fingerprint_hash, ip_address, user_agent, browser, os, screen_resolution, timezone, language, is_vpn, is_proxy, is_tor, is_bot, fraud_score, risk_signals (JSONB), raw_response (JSONB), created_at

3. Create migration

4. Create `backend/app/services/device_intel.py`:
   - async def check_ip(ip_address) -> dict - Call IPQualityScore IP reputation
   - async def check_email(email) -> dict - Call IPQualityScore email validation
   - async def check_phone(phone) -> dict - Call IPQualityScore phone validation
   - async def analyze_device(device_data) -> DeviceRiskResult
   - Risk scoring logic

5. Create `backend/app/api/v1/device_intel.py`:
   - POST /api/v1/device-intel/analyze - Submit device fingerprint for analysis
   - GET /api/v1/device-intel/applicant/{id} - Get device history for applicant
   - GET /api/v1/device-intel/session/{id} - Get session device info
   - GET /api/v1/device-intel/stats - Fraud statistics dashboard data

6. Create `backend/app/schemas/device.py`:
   - DeviceSubmission (what client sends)
   - DeviceAnalysisResult (response)

7. Register routes

### Frontend

1. Create `frontend/src/services/deviceIntel.js`:
   - submitDeviceFingerprint(data)
   - getApplicantDevices(applicantId)
   - getDeviceStats()

2. Create `frontend/src/hooks/useDeviceIntel.js`:
   - useDeviceSubmit()
   - useApplicantDevices(applicantId)
   - useDeviceStats()

3. Create device components in `frontend/src/components/device-intel/`:
   - DeviceIntelPage.jsx - Dashboard overview
   - DeviceRiskCard.jsx - Show risk indicators for a device
   - FraudStats.jsx - Overall fraud metrics
   - DeviceHistory.jsx - Device list for an applicant

4. Update ApplicantDetail.jsx to show device risk info

5. Update App.jsx to route /device-intelligence to DeviceIntelPage

## IPQualityScore Integration

API Endpoints to use:
- IP Reputation: GET https://ipqualityscore.com/api/json/ip/{api_key}/{ip}
- Email Validation: GET https://ipqualityscore.com/api/json/email/{api_key}/{email}
- Phone Validation: GET https://ipqualityscore.com/api/json/phone/{api_key}/{phone}

Response fields to capture:
- fraud_score (0-100)
- vpn, proxy, tor, active_vpn
- bot_status
- recent_abuse
- country_code
- ISP, ASN
- mobile (is mobile connection)

## Risk Scoring Logic
- fraud_score > 85: HIGH risk
- fraud_score > 70: MEDIUM risk
- fraud_score <= 70: LOW risk
- Additional flags: VPN/Proxy = +20, Tor = +30, Bot = +40

## UI Requirements
- Dashboard shows: Total scans, High risk %, VPN detected %, Bot detected %
- Device card shows: IP, Location, Risk score (color coded), Flags (VPN, Proxy, Tor, Bot)
- History table for applicant: Session time, IP, Risk, Flags

## Testing
After implementation:
1. npm run build in frontend (must pass)
2. Test with real IP (yours)
3. Verify risk scoring
4. Test dashboard stats

Please implement this now, starting with the backend service.
```

---

## Sprint 16: Billing & Usage (P2)

### Prerequisites
- Stripe account set up
- STRIPE_SECRET_KEY and STRIPE_WEBHOOK_SECRET in env

### Prompt - Copy Everything Below This Line

```
I need you to implement Billing & Usage tracking with Stripe integration.

## Context Files to Read First
- backend/app/core/config.py (config patterns)
- backend/app/models/tenant.py (tenant model)

## What to Build

### Backend

1. Add to `backend/app/core/config.py`:
   - STRIPE_SECRET_KEY
   - STRIPE_WEBHOOK_SECRET
   - STRIPE_PRICE_IDS (dict of plan -> price_id)

2. Create `backend/app/models/usage.py`:
   - UsageRecord model: id, tenant_id, metric_type (verification/screening/document/api_call), count, period_start, period_end, created_at
   - Subscription model: id, tenant_id, stripe_customer_id, stripe_subscription_id, plan (free/starter/pro/enterprise), status, current_period_start, current_period_end, created_at

3. Create migrations

4. Create `backend/app/services/usage.py`:
   - record_usage(tenant_id, metric_type) - Increment usage counter
   - get_current_usage(tenant_id) -> dict
   - get_usage_history(tenant_id, months) -> list

5. Create `backend/app/services/billing.py`:
   - create_customer(tenant_id, email) - Create Stripe customer
   - create_subscription(tenant_id, plan) - Create subscription
   - update_subscription(tenant_id, plan) - Change plan
   - cancel_subscription(tenant_id)
   - get_invoices(tenant_id) -> list
   - handle_webhook(payload, signature) - Process Stripe webhooks

6. Create `backend/app/api/v1/billing.py`:
   - GET /api/v1/billing/usage - Current period usage
   - GET /api/v1/billing/usage/history - Historical usage
   - GET /api/v1/billing/subscription - Current subscription
   - POST /api/v1/billing/subscription - Create/update subscription
   - DELETE /api/v1/billing/subscription - Cancel subscription
   - GET /api/v1/billing/invoices - List invoices
   - GET /api/v1/billing/invoices/{id}/pdf - Download invoice PDF
   - POST /api/v1/billing/payment-method - Update payment method (returns Stripe setup intent)
   - POST /api/v1/billing/webhook - Stripe webhook endpoint

7. Create `backend/app/schemas/billing.py`:
   - UsageResponse, UsageHistoryResponse
   - SubscriptionResponse, SubscriptionCreate
   - InvoiceResponse

8. Register routes

### Frontend

1. Install Stripe if not present:
   - Add @stripe/stripe-js and @stripe/react-stripe-js

2. Create `frontend/src/services/billing.js`:
   - getCurrentUsage(), getUsageHistory()
   - getSubscription(), updateSubscription(plan), cancelSubscription()
   - getInvoices(), getInvoicePdf(id)
   - getPaymentSetupIntent()

3. Create `frontend/src/hooks/useBilling.js`:
   - useUsage(), useUsageHistory()
   - useSubscription()
   - useInvoices()

4. Create billing components in `frontend/src/components/billing/`:
   - BillingPage.jsx - Main page with tabs
   - UsageTab.jsx - Current usage meters and history chart
   - SubscriptionTab.jsx - Current plan, upgrade options
   - InvoicesTab.jsx - Invoice list with download
   - PaymentMethodForm.jsx - Stripe Elements card form
   - PlanSelector.jsx - Plan comparison cards

5. Update App.jsx to route /billing to BillingPage

## Usage Tracking
Add usage recording to existing endpoints:
- POST /applicants -> record_usage('verification')
- POST /screening/check -> record_usage('screening')
- POST /documents -> record_usage('document')
- All API key authenticated requests -> record_usage('api_call')

## Plan Limits
- Free: 10 verifications/month
- Starter ($49/mo): 100 verifications/month
- Pro ($199/mo): 500 verifications/month
- Enterprise: Custom

## UI Requirements
- Usage meters: Visual progress bars showing used/limit
- Usage history: Line chart of usage over time
- Subscription card: Current plan, next billing date, amount
- Plan comparison: 3-4 plan cards with features list
- Invoice table: Date, Amount, Status, Download PDF button
- Payment method: Show last 4 digits, Update button with Stripe Elements

## Stripe Webhooks to Handle
- invoice.paid - Update subscription status
- invoice.payment_failed - Mark subscription past_due
- customer.subscription.updated - Sync subscription changes
- customer.subscription.deleted - Mark subscription cancelled

## Testing
After implementation:
1. npm run build in frontend (must pass)
2. Test usage is being recorded
3. Test subscription flow with Stripe test mode
4. Test webhook handling

Please implement this now, starting with the backend models and services.
```

---

## Sprint 17: Reusable KYC (P3)

### Prerequisites
- Most other features complete
- Clear business requirements for token format/expiry

### Prompt - Copy Everything Below This Line

```
I need you to implement Reusable KYC (portable identity) allowing verified users to share their KYC with other services.

## Context Files to Read First
- backend/app/models/applicant.py (applicant model)
- backend/app/services/screening.py (verification patterns)
- backend/app/core/security.py (token patterns)

## What to Build

### Backend

1. Create `backend/app/models/kyc_share.py`:
   - KYCShareToken model: id, applicant_id (FK), token_hash, token_prefix, shared_with (company name/domain), permissions (JSONB - what data is shared), expires_at, max_uses, use_count, revoked_at, created_at
   - KYCShareLog model: id, token_id, requester_ip, requester_domain, accessed_fields, accessed_at

2. Create migrations

3. Create `backend/app/services/kyc_share.py`:
   - generate_share_token(applicant_id, permissions, expires_days, max_uses) -> token
   - verify_share_token(token) -> applicant_data (filtered by permissions)
   - revoke_share_token(token_id)
   - get_share_history(applicant_id)
   - log_access(token_id, requester_info)

4. Create `backend/app/api/v1/kyc_share.py`:
   - POST /api/v1/kyc-share/token - Generate share token (applicant consent required)
   - GET /api/v1/kyc-share/verify/{token} - Verify token and get shared data (public endpoint for receiving parties)
   - POST /api/v1/kyc-share/revoke/{token_id} - Revoke share token
   - GET /api/v1/kyc-share/tokens - List active share tokens for applicant
   - GET /api/v1/kyc-share/history - Access log for applicant's shared data

5. Create `backend/app/schemas/kyc_share.py`:
   - ShareTokenCreate (permissions, expires_days, shared_with)
   - ShareTokenResponse (token shown once)
   - SharedKYCData (filtered applicant data)
   - ShareHistoryResponse

6. Register routes

### Frontend

1. Create `frontend/src/services/kycShare.js`:
   - generateShareToken(applicantId, permissions, options)
   - getShareTokens(applicantId)
   - revokeShareToken(tokenId)
   - getShareHistory(applicantId)

2. Create `frontend/src/hooks/useKYCShare.js`:
   - useShareTokens(applicantId)
   - useShareHistory(applicantId)
   - useGenerateToken()

3. Create KYC share components in `frontend/src/components/kyc-share/`:
   - ReusableKYCPage.jsx - Main page explaining the feature
   - ShareTokenList.jsx - List of active share tokens
   - GenerateTokenModal.jsx - Create new share token
   - ConsentFlow.jsx - Consent UI before generating token
   - ShareHistory.jsx - Log of who accessed shared data
   - TokenCreatedModal.jsx - Show token once with copy button

4. Add "Share KYC" action to ApplicantDetail.jsx

5. Update App.jsx to route /reusable-kyc to ReusableKYCPage

## Permission Options
User can select what to share:
- basic_info: name, date of birth
- id_verification: ID type, ID number, verification status
- address: verified address
- screening: AML screening result
- documents: access to verified documents
- full: everything

## Token Format
- Generate: secrets.token_urlsafe(32)
- Prefix for display: first 8 chars
- Store: SHA-256 hash only

## Security Requirements
- Tokens expire (default 30 days, max 90 days)
- Tokens have max use limit (default 1, max 10)
- Log every access with IP and domain
- Rate limit verify endpoint
- Require applicant consent before generating

## Consent Flow
1. User clicks "Share My KYC"
2. Select what to share (checkboxes)
3. Enter who you're sharing with (company name)
4. Set expiry and max uses
5. Review and confirm consent
6. Token generated and shown once

## UI Requirements
- Token list: Table with Shared With, Permissions, Expires, Uses, Status, Actions
- Generate modal: Multi-step wizard (Select Data -> Enter Recipient -> Set Limits -> Confirm)
- Token created: Show full token, QR code, copy button
- History: Table with Accessor, Date, Data Accessed

## Testing
After implementation:
1. npm run build in frontend (must pass)
2. Test consent flow
3. Test token generation
4. Test verify endpoint returns correct data
5. Test revoke works
6. Test expiry and max uses enforced

Please implement this now, starting with the backend models.
```

---

## Quick Reference

| Sprint | Backend First | Frontend After | Main Deliverable |
|--------|---------------|----------------|------------------|
| S10 | settings.py, model, migration | SettingsPage with tabs | Full settings management |
| S11 | audit.py endpoints | AuditLogPage with filters | Searchable audit log |
| S12 | analytics.py service + endpoints | AnalyticsPage with charts | Visual reports |
| S13 | api_key.py, webhook.py models | IntegrationsPage | API key + webhook management |
| S14 | company.py, ubo.py models | CompaniesPage + CompanyDetail | Full KYB module |
| S15 | device_intel.py with IPQualityScore | DeviceIntelPage | Fraud detection dashboard |
| S16 | usage.py, billing.py with Stripe | BillingPage | Usage tracking + billing |
| S17 | kyc_share.py | ReusableKYCPage | Portable identity sharing |

---

## After Each Sprint

1. **Test the build:**
   ```bash
   cd frontend && npm run build
   ```

2. **Test manually:**
   - Navigate to the new page
   - Test CRUD operations
   - Test edge cases

3. **Commit:**
   ```bash
   git add .
   git commit -m "Sprint X: [Feature Name] - [Brief description]"
   ```
