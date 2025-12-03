/**
 * React Query hooks for Audit Log
 *
 * Production-grade hooks for viewing and verifying audit logs.
 */

import { useMemo } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { useAuth } from '../auth';
import { AuditService } from '../services';

// Query key factory for consistent key management
export const auditLogKeys = {
  all: ['audit-log'],
  lists: () => [...auditLogKeys.all, 'list'],
  list: (filters) => [...auditLogKeys.lists(), filters],
  details: () => [...auditLogKeys.all, 'detail'],
  detail: (id) => [...auditLogKeys.details(), id],
  stats: () => [...auditLogKeys.all, 'stats'],
  verification: () => [...auditLogKeys.all, 'verification'],
  filterOptions: () => [...auditLogKeys.all, 'filter-options'],
};

/**
 * Hook to get a memoized AuditService instance
 */
function useAuditService() {
  const { getToken } = useAuth();
  return useMemo(() => new AuditService(getToken), [getToken]);
}

/**
 * Hook to fetch list of audit log entries with filters
 * @param {Object} filters - Filter parameters
 * @param {Object} options - Additional React Query options
 */
export function useAuditLogs(filters = {}, options = {}) {
  const service = useAuditService();

  return useQuery({
    queryKey: auditLogKeys.list(filters),
    queryFn: ({ signal }) => service.list(filters, { signal }),
    staleTime: 30000,
    ...options,
  });
}

/**
 * Hook to fetch a single audit log entry by ID
 * @param {number} id - Entry ID
 * @param {Object} options - Additional React Query options
 */
export function useAuditLogEntry(id, options = {}) {
  const service = useAuditService();

  return useQuery({
    queryKey: auditLogKeys.detail(id),
    queryFn: ({ signal }) => service.get(id, { signal }),
    enabled: !!id,
    staleTime: 60000,
    ...options,
  });
}

/**
 * Hook to fetch audit log statistics
 * @param {Object} options - Additional React Query options
 */
export function useAuditStats(options = {}) {
  const service = useAuditService();

  return useQuery({
    queryKey: auditLogKeys.stats(),
    queryFn: ({ signal }) => service.getStats({ signal }),
    staleTime: 60000,
    ...options,
  });
}

/**
 * Hook to verify chain integrity
 * @param {Object} options - Additional React Query options
 */
export function useChainVerification(options = {}) {
  const service = useAuditService();

  return useQuery({
    queryKey: auditLogKeys.verification(),
    queryFn: ({ signal }) => service.verifyChain(1000, { signal }),
    staleTime: 300000, // 5 minutes - verification is expensive
    refetchOnWindowFocus: false,
    ...options,
  });
}

/**
 * Hook to fetch filter options (distinct values for dropdowns)
 * @param {Object} options - Additional React Query options
 */
export function useAuditFilterOptions(options = {}) {
  const service = useAuditService();

  return useQuery({
    queryKey: auditLogKeys.filterOptions(),
    queryFn: ({ signal }) => service.getFilterOptions({ signal }),
    staleTime: 120000,
    ...options,
  });
}

/**
 * Hook to export audit logs to CSV
 * @returns Mutation object with mutate/mutateAsync functions
 */
export function useExportAuditLogs() {
  const service = useAuditService();

  return useMutation({
    mutationFn: async (filters = {}) => {
      const csv = await service.exportCSV(filters);

      // Create and trigger download
      const blob = new Blob([csv], { type: 'text/csv;charset=utf-8;' });
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `audit_log_export_${new Date().toISOString().split('T')[0]}.csv`;
      a.style.display = 'none';
      document.body.appendChild(a);
      a.click();

      // Cleanup
      setTimeout(() => {
        window.URL.revokeObjectURL(url);
        document.body.removeChild(a);
      }, 100);

      return csv;
    },
  });
}

/**
 * Hook to manually trigger chain verification
 * @returns Mutation object with mutate/mutateAsync functions
 */
export function useVerifyChain() {
  const service = useAuditService();
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (limit = 1000) => service.verifyChain(limit),
    onSuccess: (data) => {
      queryClient.setQueryData(auditLogKeys.verification(), data);
    },
  });
}
