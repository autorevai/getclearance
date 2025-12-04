/**
 * React Query hooks for Analytics
 *
 * Production-grade hooks for analytics data fetching.
 */

import { useMemo } from 'react';
import { useQuery, useMutation } from '@tanstack/react-query';
import { useAuth } from '../auth';
import { AnalyticsService } from '../services';

// Query key factory for consistent key management
export const analyticsKeys = {
  all: ['analytics'],
  combined: (startDate, endDate, granularity) => [...analyticsKeys.all, 'combined', startDate, endDate, granularity],
  overview: (startDate, endDate) => [...analyticsKeys.all, 'overview', startDate, endDate],
  funnel: (startDate, endDate) => [...analyticsKeys.all, 'funnel', startDate, endDate],
  trends: (startDate, endDate, granularity) => [...analyticsKeys.all, 'trends', startDate, endDate, granularity],
  geography: (startDate, endDate) => [...analyticsKeys.all, 'geography', startDate, endDate],
  risk: (startDate, endDate) => [...analyticsKeys.all, 'risk', startDate, endDate],
  sla: (startDate, endDate) => [...analyticsKeys.all, 'sla', startDate, endDate],
};

/**
 * Hook to get a memoized AnalyticsService instance
 */
function useAnalyticsService() {
  const { getToken } = useAuth();
  return useMemo(() => new AnalyticsService(getToken), [getToken]);
}

/**
 * Format date to string for query keys
 */
function formatDateKey(date) {
  if (!date) return null;
  if (typeof date === 'string') return date;
  return date.toISOString().split('T')[0];
}

/**
 * Hook to fetch overview metrics
 * @param {Date} startDate - Start date
 * @param {Date} endDate - End date
 * @param {Object} options - Additional React Query options
 */
export function useOverview(startDate, endDate, options = {}) {
  const service = useAnalyticsService();
  const startKey = formatDateKey(startDate);
  const endKey = formatDateKey(endDate);

  return useQuery({
    queryKey: analyticsKeys.overview(startKey, endKey),
    queryFn: ({ signal }) => service.getOverview(startDate, endDate, { signal }),
    staleTime: 60000, // 1 minute
    ...options,
  });
}

/**
 * Hook to fetch verification funnel data
 * @param {Date} startDate - Start date
 * @param {Date} endDate - End date
 * @param {Object} options - Additional React Query options
 */
export function useFunnel(startDate, endDate, options = {}) {
  const service = useAnalyticsService();
  const startKey = formatDateKey(startDate);
  const endKey = formatDateKey(endDate);

  return useQuery({
    queryKey: analyticsKeys.funnel(startKey, endKey),
    queryFn: ({ signal }) => service.getFunnel(startDate, endDate, { signal }),
    staleTime: 60000,
    ...options,
  });
}

/**
 * Hook to fetch time series trends
 * @param {Date} startDate - Start date
 * @param {Date} endDate - End date
 * @param {string} granularity - 'day', 'week', or 'month'
 * @param {Object} options - Additional React Query options
 */
export function useTrends(startDate, endDate, granularity = 'day', options = {}) {
  const service = useAnalyticsService();
  const startKey = formatDateKey(startDate);
  const endKey = formatDateKey(endDate);

  return useQuery({
    queryKey: analyticsKeys.trends(startKey, endKey, granularity),
    queryFn: ({ signal }) => service.getTrends(startDate, endDate, granularity, { signal }),
    staleTime: 60000,
    ...options,
  });
}

/**
 * Hook to fetch geographic distribution
 * @param {Date} startDate - Start date
 * @param {Date} endDate - End date
 * @param {Object} options - Additional React Query options
 */
export function useGeography(startDate, endDate, options = {}) {
  const service = useAnalyticsService();
  const startKey = formatDateKey(startDate);
  const endKey = formatDateKey(endDate);

  return useQuery({
    queryKey: analyticsKeys.geography(startKey, endKey),
    queryFn: ({ signal }) => service.getGeography(startDate, endDate, { signal }),
    staleTime: 60000,
    ...options,
  });
}

/**
 * Hook to fetch risk score distribution
 * @param {Date} startDate - Start date
 * @param {Date} endDate - End date
 * @param {Object} options - Additional React Query options
 */
export function useRiskDistribution(startDate, endDate, options = {}) {
  const service = useAnalyticsService();
  const startKey = formatDateKey(startDate);
  const endKey = formatDateKey(endDate);

  return useQuery({
    queryKey: analyticsKeys.risk(startKey, endKey),
    queryFn: ({ signal }) => service.getRiskDistribution(startDate, endDate, { signal }),
    staleTime: 60000,
    ...options,
  });
}

/**
 * Hook to fetch SLA performance metrics
 * @param {Date} startDate - Start date
 * @param {Date} endDate - End date
 * @param {Object} options - Additional React Query options
 */
export function useSlaPerformance(startDate, endDate, options = {}) {
  const service = useAnalyticsService();
  const startKey = formatDateKey(startDate);
  const endKey = formatDateKey(endDate);

  return useQuery({
    queryKey: analyticsKeys.sla(startKey, endKey),
    queryFn: ({ signal }) => service.getSlaPerformance(startDate, endDate, { signal }),
    staleTime: 60000,
    ...options,
  });
}

/**
 * Hook to export analytics report
 * @returns Mutation object with mutate/mutateAsync functions
 */
export function useExportAnalytics() {
  const service = useAnalyticsService();

  return useMutation({
    mutationFn: async ({ startDate, endDate, format = 'csv' }) => {
      const data = await service.exportReport(startDate, endDate, format);

      if (format === 'csv') {
        // Create and trigger download
        const blob = new Blob([data], { type: 'text/csv;charset=utf-8;' });
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        const startStr = formatDateKey(startDate);
        const endStr = formatDateKey(endDate);
        a.download = `analytics_${startStr}_${endStr}.csv`;
        a.style.display = 'none';
        document.body.appendChild(a);
        a.click();

        // Cleanup
        setTimeout(() => {
          window.URL.revokeObjectURL(url);
          document.body.removeChild(a);
        }, 100);
      }

      return data;
    },
  });
}

/**
 * Combined hook to fetch all analytics data in a SINGLE request (fast!)
 * @param {Date} startDate - Start date
 * @param {Date} endDate - End date
 * @param {string} granularity - Trend granularity
 */
export function useAllAnalytics(startDate, endDate, granularity = 'day') {
  const service = useAnalyticsService();
  const startKey = formatDateKey(startDate);
  const endKey = formatDateKey(endDate);

  const query = useQuery({
    queryKey: analyticsKeys.combined(startKey, endKey, granularity),
    queryFn: ({ signal }) => service.getAll(startDate, endDate, granularity, { signal }),
    staleTime: 60000, // 1 minute
  });

  return {
    overview: query.data?.overview,
    funnel: query.data?.funnel,
    trends: query.data?.trends,
    geography: query.data?.geography,
    risk: query.data?.risk,
    sla: query.data?.sla,
    isLoading: query.isLoading,
    isError: query.isError,
    error: query.error,
    refetch: query.refetch,
  };
}
