/**
 * React Query hooks for Dashboard
 *
 * Production-grade hooks with:
 * - Auto-refresh every 60 seconds
 * - Singleton service instances
 * - Manual refetch support
 */

import { useMemo, useCallback } from 'react';
import { useQuery, useQueryClient } from '@tanstack/react-query';
import { useAuth } from '../auth';
import { DashboardService } from '../services/dashboard';

// Query key factory for consistent key management
export const dashboardKeys = {
  all: ['dashboard'],
  stats: () => [...dashboardKeys.all, 'stats'],
  screeningSummary: () => [...dashboardKeys.all, 'screening-summary'],
  activity: (limit) => [...dashboardKeys.all, 'activity', { limit }],
};

// Auto-refresh interval (60 seconds)
const REFETCH_INTERVAL = 60000;
const STALE_TIME = 60000;

/**
 * Hook to get a memoized DashboardService instance
 * Prevents recreating service on every render
 */
function useDashboardService() {
  const { getToken } = useAuth();
  return useMemo(() => new DashboardService(getToken), [getToken]);
}

/**
 * Hook to fetch dashboard KPI statistics
 * Auto-refreshes every 60 seconds
 * @param {Object} options - Additional React Query options
 */
export function useDashboardStats(options = {}) {
  const service = useDashboardService();

  return useQuery({
    queryKey: dashboardKeys.stats(),
    queryFn: ({ signal }) => service.getStats({ signal }),
    staleTime: STALE_TIME,
    refetchInterval: REFETCH_INTERVAL,
    ...options,
  });
}

/**
 * Hook to fetch screening hit summary
 * Auto-refreshes every 60 seconds
 * @param {Object} options - Additional React Query options
 */
export function useScreeningSummary(options = {}) {
  const service = useDashboardService();

  return useQuery({
    queryKey: dashboardKeys.screeningSummary(),
    queryFn: ({ signal }) => service.getScreeningSummary({ signal }),
    staleTime: STALE_TIME,
    refetchInterval: REFETCH_INTERVAL,
    ...options,
  });
}

/**
 * Hook to fetch recent activity feed
 * Auto-refreshes every 60 seconds
 * @param {number} limit - Number of items to fetch
 * @param {Object} options - Additional React Query options
 */
export function useRecentActivity(limit = 20, options = {}) {
  const service = useDashboardService();

  return useQuery({
    queryKey: dashboardKeys.activity(limit),
    queryFn: ({ signal }) => service.getActivity(limit, { signal }),
    staleTime: STALE_TIME,
    refetchInterval: REFETCH_INTERVAL,
    ...options,
  });
}

/**
 * Hook to manually refresh all dashboard data
 * Returns a function that invalidates all dashboard queries
 */
export function useRefreshDashboard() {
  const queryClient = useQueryClient();

  return useCallback(() => {
    queryClient.invalidateQueries({ queryKey: dashboardKeys.all });
  }, [queryClient]);
}

/**
 * Convenience hook that fetches all dashboard data at once
 * Useful for getting loading/error states in one place
 */
export function useDashboardData() {
  const stats = useDashboardStats();
  const screening = useScreeningSummary();
  const activity = useRecentActivity();
  const refresh = useRefreshDashboard();

  return {
    stats,
    screening,
    activity,
    refresh,
    isLoading: stats.isLoading || screening.isLoading || activity.isLoading,
    isError: stats.isError || screening.isError || activity.isError,
    error: stats.error || screening.error || activity.error,
  };
}
