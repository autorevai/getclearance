/**
 * React Query hooks for Billing
 *
 * Production-grade hooks with:
 * - Singleton service instances (no recreation on each render)
 * - Optimistic updates for instant UI feedback
 * - Proper cache invalidation strategies
 */

import { useMemo } from 'react';
import {
  useQuery,
  useMutation,
  useQueryClient,
} from '@tanstack/react-query';
import { useAuth } from '../auth';
import { BillingService } from '../services/billing';

// Query key factory for consistent key management
export const billingKeys = {
  all: ['billing'],
  usage: () => [...billingKeys.all, 'usage'],
  usageHistory: (months) => [...billingKeys.all, 'usage-history', months],
  subscription: () => [...billingKeys.all, 'subscription'],
  invoices: (limit) => [...billingKeys.all, 'invoices', limit],
  paymentMethods: () => [...billingKeys.all, 'payment-methods'],
  plans: () => [...billingKeys.all, 'plans'],
};

/**
 * Hook to get a memoized BillingService instance
 * Prevents recreating service on every render
 */
function useBillingService() {
  const { getToken } = useAuth();
  return useMemo(() => new BillingService(getToken), [getToken]);
}

// ===========================================
// USAGE HOOKS
// ===========================================

/**
 * Hook to fetch current period usage
 * @param {Object} options - Additional React Query options
 */
export function useUsage(options = {}) {
  const service = useBillingService();

  return useQuery({
    queryKey: billingKeys.usage(),
    queryFn: ({ signal }) => service.getUsage({ signal }),
    staleTime: 60000, // Usage can be cached for 1 minute
    ...options,
  });
}

/**
 * Hook to fetch historical usage
 * @param {number} months - Number of months to fetch
 * @param {Object} options - Additional React Query options
 */
export function useUsageHistory(months = 6, options = {}) {
  const service = useBillingService();

  return useQuery({
    queryKey: billingKeys.usageHistory(months),
    queryFn: ({ signal }) => service.getUsageHistory(months, { signal }),
    staleTime: 300000, // History can be cached for 5 minutes
    ...options,
  });
}

// ===========================================
// SUBSCRIPTION HOOKS
// ===========================================

/**
 * Hook to fetch current subscription
 * @param {Object} options - Additional React Query options
 */
export function useSubscription(options = {}) {
  const service = useBillingService();

  return useQuery({
    queryKey: billingKeys.subscription(),
    queryFn: ({ signal }) => service.getSubscription({ signal }),
    staleTime: 60000,
    ...options,
  });
}

/**
 * Hook to create or update subscription
 * @returns Mutation object with mutate/mutateAsync functions
 */
export function useUpdateSubscription() {
  const service = useBillingService();
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (data) => service.createOrUpdateSubscription(data),

    onSuccess: (subscription) => {
      // Update subscription cache
      queryClient.setQueryData(billingKeys.subscription(), subscription);
      // Invalidate usage (may have new limits)
      queryClient.invalidateQueries({ queryKey: billingKeys.usage() });
    },
  });
}

/**
 * Hook to cancel subscription
 * @returns Mutation object with mutate/mutateAsync functions
 */
export function useCancelSubscription() {
  const service = useBillingService();
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (immediately = false) => service.cancelSubscription(immediately),

    onSuccess: (subscription) => {
      queryClient.setQueryData(billingKeys.subscription(), subscription);
    },
  });
}

// ===========================================
// INVOICE HOOKS
// ===========================================

/**
 * Hook to fetch invoices
 * @param {number} limit - Maximum invoices to fetch
 * @param {Object} options - Additional React Query options
 */
export function useInvoices(limit = 10, options = {}) {
  const service = useBillingService();

  return useQuery({
    queryKey: billingKeys.invoices(limit),
    queryFn: ({ signal }) => service.getInvoices(limit, { signal }),
    staleTime: 60000,
    ...options,
  });
}

/**
 * Hook to download invoice PDF
 * @returns Mutation for triggering download
 */
export function useDownloadInvoice() {
  const service = useBillingService();

  return useMutation({
    mutationFn: (invoiceId) => service.downloadInvoice(invoiceId),
  });
}

// ===========================================
// PAYMENT METHOD HOOKS
// ===========================================

/**
 * Hook to fetch payment methods
 * @param {Object} options - Additional React Query options
 */
export function usePaymentMethods(options = {}) {
  const service = useBillingService();

  return useQuery({
    queryKey: billingKeys.paymentMethods(),
    queryFn: ({ signal }) => service.getPaymentMethods({ signal }),
    staleTime: 60000,
    ...options,
  });
}

/**
 * Hook to create setup intent for adding payment method
 * @returns Mutation object with mutate/mutateAsync functions
 */
export function useCreateSetupIntent() {
  const service = useBillingService();

  return useMutation({
    mutationFn: () => service.createSetupIntent(),
  });
}

/**
 * Hook to delete a payment method
 * @returns Mutation object with mutate/mutateAsync functions
 */
export function useDeletePaymentMethod() {
  const service = useBillingService();
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (paymentMethodId) => service.deletePaymentMethod(paymentMethodId),

    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: billingKeys.paymentMethods() });
    },
  });
}

// ===========================================
// PLAN & PORTAL HOOKS
// ===========================================

/**
 * Hook to fetch available plans
 * @param {Object} options - Additional React Query options
 */
export function usePlans(options = {}) {
  const service = useBillingService();

  return useQuery({
    queryKey: billingKeys.plans(),
    queryFn: ({ signal }) => service.getPlans({ signal }),
    staleTime: 3600000, // Plans can be cached for 1 hour
    ...options,
  });
}

/**
 * Hook to open Stripe customer portal
 * @returns Mutation for opening portal
 */
export function useOpenPortal() {
  const service = useBillingService();

  return useMutation({
    mutationFn: (returnUrl) => service.openPortal(returnUrl || window.location.href),
  });
}

/**
 * Hook to invalidate all billing cache
 * Useful when you know data has changed externally
 */
export function useInvalidateBilling() {
  const queryClient = useQueryClient();

  return () => {
    queryClient.invalidateQueries({ queryKey: billingKeys.all });
  };
}
