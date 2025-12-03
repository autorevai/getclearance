/**
 * React Query hooks for Device Intelligence
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
import { DeviceIntelService } from '../services/deviceIntel';

// Query key factory for consistent key management
export const deviceIntelKeys = {
  all: ['device-intel'],
  lists: () => [...deviceIntelKeys.all, 'list'],
  list: (filters) => [...deviceIntelKeys.lists(), filters],
  details: () => [...deviceIntelKeys.all, 'detail'],
  detail: (id) => [...deviceIntelKeys.details(), id],
  applicant: (applicantId) => [...deviceIntelKeys.all, 'applicant', applicantId],
  session: (sessionId) => [...deviceIntelKeys.all, 'session', sessionId],
  stats: (days) => [...deviceIntelKeys.all, 'stats', days],
  ipCheck: (ip) => [...deviceIntelKeys.all, 'ip-check', ip],
};

/**
 * Hook to get a memoized DeviceIntelService instance
 * Prevents recreating service on every render
 */
function useDeviceIntelService() {
  const { getToken } = useAuth();
  return useMemo(() => new DeviceIntelService(getToken), [getToken]);
}

// ===========================================
// LIST & FILTERS
// ===========================================

/**
 * Hook to fetch list of device fingerprints with filters
 * @param {Object} filters - Filter parameters (risk_level, ip_address, limit, offset)
 * @param {Object} options - Additional React Query options
 */
export function useDevices(filters = {}, options = {}) {
  const service = useDeviceIntelService();

  return useQuery({
    queryKey: deviceIntelKeys.list(filters),
    queryFn: ({ signal }) => service.list(filters, { signal }),
    staleTime: 30000,
    ...options,
  });
}

// ===========================================
// DEVICE ANALYSIS
// ===========================================

/**
 * Hook to submit device fingerprint for analysis
 * @returns Mutation object with mutate/mutateAsync functions
 */
export function useAnalyzeDevice() {
  const service = useDeviceIntelService();
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (data) => service.analyze(data),

    onSuccess: (result) => {
      // Add to cache immediately
      queryClient.setQueryData(deviceIntelKeys.detail(result.id), result);

      // Invalidate list to include new item
      queryClient.invalidateQueries({ queryKey: deviceIntelKeys.lists() });

      // Invalidate stats to reflect new scan
      queryClient.invalidateQueries({ queryKey: deviceIntelKeys.stats() });

      // If applicant was associated, invalidate their device history
      if (result.applicant_id) {
        queryClient.invalidateQueries({
          queryKey: deviceIntelKeys.applicant(result.applicant_id),
        });
      }
    },
  });
}

/**
 * Hook for quick IP reputation check (no storage)
 * @param {string} ipAddress - IP address to check
 * @param {Object} options - Additional React Query options
 */
export function useIPCheck(ipAddress, options = {}) {
  const service = useDeviceIntelService();

  return useQuery({
    queryKey: deviceIntelKeys.ipCheck(ipAddress),
    queryFn: ({ signal }) => service.checkIP(ipAddress, { signal }),
    enabled: !!ipAddress && ipAddress.length >= 7, // Minimum valid IP length
    staleTime: 60000, // Cache IP checks for 1 minute
    ...options,
  });
}

/**
 * Mutation hook for on-demand IP checks
 * Use this when you want to trigger the check manually
 */
export function useCheckIP() {
  const service = useDeviceIntelService();
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (ipAddress) => service.checkIP(ipAddress),

    onSuccess: (result, ipAddress) => {
      // Cache the result
      queryClient.setQueryData(deviceIntelKeys.ipCheck(ipAddress), result);
    },
  });
}

// ===========================================
// DEVICE HISTORY
// ===========================================

/**
 * Hook to fetch device history for an applicant
 * @param {string} applicantId - Applicant ID
 * @param {Object} options - Additional React Query options
 */
export function useApplicantDevices(applicantId, options = {}) {
  const service = useDeviceIntelService();

  return useQuery({
    queryKey: deviceIntelKeys.applicant(applicantId),
    queryFn: ({ signal }) => service.getApplicantDevices(applicantId, { signal }),
    enabled: !!applicantId,
    staleTime: 30000,
    ...options,
  });
}

/**
 * Hook to fetch device for a specific session
 * @param {string} sessionId - Session ID
 * @param {Object} options - Additional React Query options
 */
export function useSessionDevice(sessionId, options = {}) {
  const service = useDeviceIntelService();

  return useQuery({
    queryKey: deviceIntelKeys.session(sessionId),
    queryFn: ({ signal }) => service.getSessionDevice(sessionId, { signal }),
    enabled: !!sessionId,
    staleTime: 30000,
    ...options,
  });
}

// ===========================================
// STATISTICS
// ===========================================

/**
 * Hook to fetch fraud detection statistics
 * @param {number} days - Number of days for stats period (default 30)
 * @param {Object} options - Additional React Query options
 */
export function useDeviceStats(days = 30, options = {}) {
  const service = useDeviceIntelService();

  return useQuery({
    queryKey: deviceIntelKeys.stats(days),
    queryFn: ({ signal }) => service.getStats(days, { signal }),
    staleTime: 60000, // Stats can be cached longer
    ...options,
  });
}

// ===========================================
// UTILITY HOOKS
// ===========================================

/**
 * Hook to get risk summary counts for dashboard
 */
export function useDeviceRiskSummary() {
  const service = useDeviceIntelService();

  return useQuery({
    queryKey: [...deviceIntelKeys.all, 'risk-summary'],
    queryFn: async ({ signal }) => {
      const [high, medium, low] = await Promise.all([
        service.list({ risk_level: 'high', limit: 0 }, { signal }),
        service.list({ risk_level: 'medium', limit: 0 }, { signal }),
        service.list({ risk_level: 'low', limit: 0 }, { signal }),
      ]);

      return {
        high: high.total,
        medium: medium.total,
        low: low.total,
        total: high.total + medium.total + low.total,
      };
    },
    staleTime: 60000,
  });
}

/**
 * Hook to invalidate all device intel cache
 * Useful when you know data has changed externally
 */
export function useInvalidateDeviceIntel() {
  const queryClient = useQueryClient();

  return () => {
    queryClient.invalidateQueries({ queryKey: deviceIntelKeys.all });
  };
}

/**
 * Hook to get high-risk device count (for badges/alerts)
 */
export function useHighRiskDeviceCount() {
  const service = useDeviceIntelService();

  return useQuery({
    queryKey: [...deviceIntelKeys.all, 'high-risk-count'],
    queryFn: async ({ signal }) => {
      const result = await service.list({ risk_level: 'high', limit: 0 }, { signal });
      return result.total;
    },
    staleTime: 30000,
  });
}
