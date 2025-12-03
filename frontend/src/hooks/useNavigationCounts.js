/**
 * Navigation Counts Hook
 *
 * Fetches real-time badge counts for navigation items.
 * Auto-refreshes every 60 seconds.
 */

import { useMemo } from 'react';
import { useQuery } from '@tanstack/react-query';
import { useAuth } from '../auth';
import { ApiClient } from '../services/api';

// Query key factory
export const navigationCountsKeys = {
  all: ['navigationCounts'],
  counts: () => [...navigationCountsKeys.all, 'counts'],
};

// Auto-refresh interval (60 seconds)
const REFETCH_INTERVAL = 60000;
const STALE_TIME = 60000;

/**
 * Service class for fetching navigation badge counts
 */
class NavigationCountsService {
  constructor(getToken) {
    this.client = new ApiClient(getToken);
  }

  /**
   * Fetch counts from various endpoints
   * @param {Object} options - Request options
   * @returns {Promise<{pending_applicants: number, unresolved_hits: number, open_cases: number}>}
   */
  async getCounts(options = {}) {
    // Fetch counts from multiple endpoints in parallel
    // Use limit=0 to just get the total without data, or use count endpoints if available
    const [applicantsResult, screeningResult, casesResult] = await Promise.allSettled([
      this.client.get('/applicants?status=pending&limit=1', options),
      this.client.get('/screening/hits?status=pending&limit=1', options),
      this.client.get('/cases?status=open&limit=1', options),
    ]);

    return {
      pending_applicants: applicantsResult.status === 'fulfilled'
        ? (applicantsResult.value.total || 0)
        : 0,
      unresolved_hits: screeningResult.status === 'fulfilled'
        ? (screeningResult.value.total || 0)
        : 0,
      open_cases: casesResult.status === 'fulfilled'
        ? (casesResult.value.total || 0)
        : 0,
    };
  }
}

/**
 * Hook to fetch navigation badge counts
 * Auto-refreshes every 60 seconds
 * @param {Object} options - Additional React Query options
 * @returns {Object} Query result with counts
 */
export function useNavigationCounts(options = {}) {
  const { getToken } = useAuth();
  const service = useMemo(() => new NavigationCountsService(getToken), [getToken]);

  return useQuery({
    queryKey: navigationCountsKeys.counts(),
    queryFn: ({ signal }) => service.getCounts({ signal }),
    staleTime: STALE_TIME,
    refetchInterval: REFETCH_INTERVAL,
    retry: 2,
    // Don't throw errors for failed badge counts - just show 0
    throwOnError: false,
    ...options,
  });
}

/**
 * Helper to format badge count for display
 * Shows 99+ for counts over 99
 * @param {number} count - The count to format
 * @returns {string|number} Formatted count
 */
export function formatBadgeCount(count) {
  if (count === null || count === undefined) return null;
  if (count > 99) return '99+';
  return count;
}

export default useNavigationCounts;
