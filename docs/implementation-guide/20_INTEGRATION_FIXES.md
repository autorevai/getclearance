# Integration Fixes - Disconnected Items

**Purpose:** Fix wiring issues discovered during integration audit
**Created:** December 2, 2025
**Estimated Time:** 30-60 minutes total
**Can Run In:** Any terminal

---

## Summary

After auditing Terminals 1-3 completion, these disconnected items were found:

| Category | Count | Severity |
|----------|-------|----------|
| Missing model exports | 5 models | Medium - affects autogenerate migrations |
| Missing service export | 1 | Low - works but inconsistent |
| Placeholder pages | 2 | Medium - user-facing |
| Missing frontend for backend | 3 features | Medium - backend ready, no UI |

---

## Quick Fixes (Do These First)

### Fix 1: Add Missing Model Exports ✅
**File:** `backend/app/models/__init__.py`
**Time:** 2 minutes
**Status:** [x] COMPLETE ✅

Add these imports after the existing imports:

```python
# API Keys & Webhooks (Integrations)
from app.models.api_key import ApiKey
from app.models.webhook import WebhookConfig, WebhookDelivery

# Settings & Team
from app.models.settings import TenantSettings, TeamInvitation, SettingsCategory, TeamInvitationStatus
```

And add to `__all__`:

```python
    # API Keys & Webhooks
    "ApiKey",
    "WebhookConfig",
    "WebhookDelivery",
    # Settings
    "TenantSettings",
    "TeamInvitation",
    "SettingsCategory",
    "TeamInvitationStatus",
```

**Why:** Alembic's `--autogenerate` won't detect these models without the import.

---

### Fix 2: Add DeviceIntelService Export ✅
**File:** `frontend/src/services/index.js`
**Time:** 1 minute
**Status:** [x] COMPLETE ✅

Add this line:

```javascript
export { DeviceIntelService } from './deviceIntel';
```

**Why:** Consistent barrel exports for all services.

---

## Medium Fixes (Placeholder Pages)

### Fix 3: Implement BillingPage
**Backend:** READY at `/api/v1/billing/*`
**Frontend Missing:**
- `frontend/src/services/billing.js`
- `frontend/src/hooks/useBilling.js`
- `frontend/src/components/billing/` (full implementation)

**Current State:** Shows "Coming Soon" placeholder

**Time:** 2-3 hours

**Status:** [ ] Not Started

#### 3a. Create billing service
**File:** `frontend/src/services/billing.js`

```javascript
/**
 * Billing Service
 *
 * Handles subscription, usage, and invoice operations.
 */

import { getSharedClient } from './api';

const client = getSharedClient();

export const BillingService = {
  // Usage
  async getCurrentUsage() {
    return client.get('/billing/usage');
  },

  async getUsageHistory(months = 6) {
    return client.get('/billing/usage/history', { params: { months } });
  },

  // Subscription
  async getSubscription() {
    return client.get('/billing/subscription');
  },

  async updateSubscription(planId) {
    return client.post('/billing/subscription', { plan_id: planId });
  },

  async cancelSubscription() {
    return client.delete('/billing/subscription');
  },

  // Invoices
  async getInvoices(limit = 12) {
    return client.get('/billing/invoices', { params: { limit } });
  },

  async getInvoicePdf(invoiceId) {
    return client.get(`/billing/invoices/${invoiceId}/pdf`, {
      responseType: 'blob',
    });
  },

  // Payment Methods
  async getPaymentMethods() {
    return client.get('/billing/payment-methods');
  },

  async createSetupIntent() {
    return client.post('/billing/payment-method');
  },

  async removePaymentMethod(paymentMethodId) {
    return client.delete(`/billing/payment-methods/${paymentMethodId}`);
  },

  // Plans
  async getPlans() {
    return client.get('/billing/plans');
  },

  // Customer Portal
  async createPortalSession() {
    return client.post('/billing/portal');
  },
};

export default BillingService;
```

#### 3b. Create billing hooks
**File:** `frontend/src/hooks/useBilling.js`

```javascript
/**
 * Billing Hooks
 *
 * React Query hooks for billing operations.
 */

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { BillingService } from '../services/billing';

export const billingKeys = {
  all: ['billing'],
  usage: () => [...billingKeys.all, 'usage'],
  usageHistory: (months) => [...billingKeys.all, 'usage-history', months],
  subscription: () => [...billingKeys.all, 'subscription'],
  invoices: () => [...billingKeys.all, 'invoices'],
  paymentMethods: () => [...billingKeys.all, 'payment-methods'],
  plans: () => [...billingKeys.all, 'plans'],
};

// Usage
export function useCurrentUsage() {
  return useQuery({
    queryKey: billingKeys.usage(),
    queryFn: () => BillingService.getCurrentUsage(),
  });
}

export function useUsageHistory(months = 6) {
  return useQuery({
    queryKey: billingKeys.usageHistory(months),
    queryFn: () => BillingService.getUsageHistory(months),
  });
}

// Subscription
export function useSubscription() {
  return useQuery({
    queryKey: billingKeys.subscription(),
    queryFn: () => BillingService.getSubscription(),
  });
}

export function useUpdateSubscription() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (planId) => BillingService.updateSubscription(planId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: billingKeys.subscription() });
      queryClient.invalidateQueries({ queryKey: billingKeys.usage() });
    },
  });
}

export function useCancelSubscription() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: () => BillingService.cancelSubscription(),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: billingKeys.subscription() });
    },
  });
}

// Invoices
export function useInvoices(limit = 12) {
  return useQuery({
    queryKey: billingKeys.invoices(),
    queryFn: () => BillingService.getInvoices(limit),
  });
}

export function useDownloadInvoice() {
  return useMutation({
    mutationFn: async (invoiceId) => {
      const blob = await BillingService.getInvoicePdf(invoiceId);
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `invoice-${invoiceId}.pdf`;
      a.click();
      window.URL.revokeObjectURL(url);
    },
  });
}

// Payment Methods
export function usePaymentMethods() {
  return useQuery({
    queryKey: billingKeys.paymentMethods(),
    queryFn: () => BillingService.getPaymentMethods(),
  });
}

export function useCreateSetupIntent() {
  return useMutation({
    mutationFn: () => BillingService.createSetupIntent(),
  });
}

export function useRemovePaymentMethod() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (paymentMethodId) => BillingService.removePaymentMethod(paymentMethodId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: billingKeys.paymentMethods() });
    },
  });
}

// Plans
export function usePlans() {
  return useQuery({
    queryKey: billingKeys.plans(),
    queryFn: () => BillingService.getPlans(),
    staleTime: 1000 * 60 * 60, // Plans don't change often
  });
}

// Customer Portal
export function useCreatePortalSession() {
  return useMutation({
    mutationFn: async () => {
      const { url } = await BillingService.createPortalSession();
      window.location.href = url;
    },
  });
}
```

#### 3c. Create billing components

Create folder `frontend/src/components/billing/` with:
- `BillingPage.jsx` - Main page with tabs
- `UsageTab.jsx` - Usage meters and chart
- `SubscriptionTab.jsx` - Current plan, upgrade options
- `InvoicesTab.jsx` - Invoice list with download
- `PaymentMethodsTab.jsx` - Card management
- `index.js` - Barrel exports

#### 3d. Update pages/BillingPage.jsx

```javascript
import { BillingPage as BillingPageComponent } from '../billing';

export default function BillingPage() {
  return <BillingPageComponent />;
}
```

#### 3e. Add exports

**In `frontend/src/services/index.js`:**
```javascript
export { BillingService } from './billing';
```

**In `frontend/src/hooks/index.js`:**
```javascript
// Billing hooks
export {
  billingKeys,
  useCurrentUsage,
  useUsageHistory,
  useSubscription,
  useUpdateSubscription,
  useCancelSubscription,
  useInvoices,
  useDownloadInvoice,
  usePaymentMethods,
  useCreateSetupIntent,
  useRemovePaymentMethod,
  usePlans,
  useCreatePortalSession,
} from './useBilling';
```

---

### Fix 4: ReusableKYCPage (Lower Priority)
**Backend:** NOT READY - needs implementation
**Frontend:** Placeholder

**Time:** 4-6 hours (backend + frontend)

**Status:** [ ] Not Started

This is a P3 feature per the MASTER doc. Skip for now unless specifically requested.

---

## Optional Fixes (Backend Ready, No UI)

### Fix 5: Questionnaires UI
**Backend:** READY at `/api/v1/questionnaires/*`
**Frontend Missing:** Everything

**Time:** 3-4 hours

**Status:** [ ] Not Started

Components needed:
- `frontend/src/services/questionnaires.js`
- `frontend/src/hooks/useQuestionnaires.js`
- `frontend/src/components/questionnaires/`
  - `QuestionnairesPage.jsx`
  - `QuestionnaireBuilder.jsx`
  - `QuestionnairePreview.jsx`
  - `QuestionnaireResponses.jsx`

**Note:** Questionnaires are typically admin-only for building forms. The responses are collected during applicant onboarding flow, which may already be handled.

---

### Fix 6: Biometrics UI
**Backend:** READY at `/api/v1/biometrics/*`
**Frontend Missing:** Dedicated page

**Time:** 2-3 hours

**Status:** [ ] Not Started

The biometrics endpoints (face compare, liveness) are typically called during the applicant verification flow, not from a dedicated page. However, you might want:
- A biometrics results viewer in ApplicantDetail
- A selfie capture component
- Face match result display

**Note:** May already be partially integrated into ApplicantDetail. Check before building.

---

## Tracking Checklist

### Quick Fixes (15 min total)
- [x] Fix 1: Model exports added to `__init__.py` ✅ DONE
- [x] Fix 2: DeviceIntelService export added ✅ DONE

### Medium Fixes (2-3 hours)
- [x] Fix 3a: billing.js service created ✅ (Terminal 3)
- [x] Fix 3b: useBilling.js hooks created ✅ (Terminal 3)
- [x] Fix 3c: billing/ components created ✅ (Terminal 3)
- [x] Fix 3d: BillingPage.jsx updated ✅ (Terminal 3)
- [x] Fix 3e: Exports added to index files ✅ (Terminal 3)

### Additional Fixes (Completed December 2, 2025)
- [x] Fix 4: ReusableKYCPage ✅ (Terminal 3 - full implementation with KYC share)
- [x] Fix 5: Questionnaires UI ✅ DONE
  - Created: `services/questionnaires.js`
  - Created: `hooks/useQuestionnaires.js`
  - Created: `components/questionnaires/QuestionnairesPage.jsx`
  - Created: `components/questionnaires/QuestionnaireBuilder.jsx`
  - Created: `components/questionnaires/QuestionnairePreview.jsx`
  - Added routes to App.jsx
- [x] Fix 6: Biometrics UI ✅ DONE
  - Created: `services/biometrics.js`
  - Created: `hooks/useBiometrics.js`
  - Created: `components/biometrics/BiometricsPage.jsx`
  - Created: `components/biometrics/BiometricsDemo.jsx`
  - Added routes to App.jsx

---

## Testing After Fixes

### Quick Fixes Verification
```bash
# Backend - verify models load
cd backend
python -c "from app.models import ApiKey, WebhookConfig, TenantSettings; print('Models OK')"

# Frontend - verify build
cd frontend
npm run build
```

### BillingPage Verification
1. Navigate to /billing
2. Verify usage meters display
3. Verify subscription info loads
4. Verify invoice list loads
5. Test plan change flow (if Stripe configured)

---

## Notes

1. **Billing requires Stripe** - The billing backend uses Stripe. Need `STRIPE_SECRET_KEY` in env for it to work. Without it, endpoints will return errors.

2. **ReusableKYC is P3** - Don't prioritize this unless specifically requested. It's a future feature.

3. **Questionnaires may be admin-only** - The questionnaire builder is for compliance teams to create forms. The applicant-facing part may be embedded in the onboarding flow.

4. **Biometrics may already be integrated** - Check ApplicantDetail before building a separate page. Face match results may already display there.
