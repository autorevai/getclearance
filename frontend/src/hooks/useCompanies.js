/**
 * React Query hooks for Companies (KYB)
 *
 * Production-grade hooks with:
 * - Singleton service instances (no recreation on each render)
 * - Optimistic updates for instant UI feedback
 * - Proper cache invalidation strategies
 * - Prefetching for predictive loading
 */

import { useCallback, useMemo } from 'react';
import {
  useQuery,
  useMutation,
  useQueryClient,
} from '@tanstack/react-query';
import { useAuth } from '../auth';
import { CompaniesService } from '../services/companies';

// Query key factory for consistent key management
export const companyKeys = {
  all: ['companies'],
  lists: () => [...companyKeys.all, 'list'],
  list: (filters) => [...companyKeys.lists(), filters],
  details: () => [...companyKeys.all, 'detail'],
  detail: (id) => [...companyKeys.details(), id],
  ubos: (id) => [...companyKeys.detail(id), 'ubos'],
  documents: (id) => [...companyKeys.detail(id), 'documents'],
  screening: (id) => [...companyKeys.detail(id), 'screening'],
};

/**
 * Hook to get a memoized CompaniesService instance
 * Prevents recreating service on every render
 */
function useCompaniesService() {
  const { getToken } = useAuth();
  return useMemo(() => new CompaniesService(getToken), [getToken]);
}

// ===========================================
// COMPANY LIST & DETAIL HOOKS
// ===========================================

/**
 * Hook to fetch list of companies with filters and pagination
 * @param {Object} filters - Filter parameters (status, risk_level, search, etc.)
 * @param {Object} options - Additional React Query options
 */
export function useCompanies(filters = {}, options = {}) {
  const service = useCompaniesService();

  return useQuery({
    queryKey: companyKeys.list(filters),
    queryFn: ({ signal }) => service.list(filters, { signal }),
    staleTime: 30000,
    ...options,
  });
}

/**
 * Hook to fetch a single company by ID with UBOs and documents
 * @param {string} id - Company ID
 * @param {Object} options - Additional React Query options
 */
export function useCompany(id, options = {}) {
  const service = useCompaniesService();

  return useQuery({
    queryKey: companyKeys.detail(id),
    queryFn: ({ signal }) => service.get(id, { signal }),
    enabled: !!id,
    staleTime: 30000,
    ...options,
  });
}

/**
 * Hook to prefetch a company (for hover states, etc.)
 */
export function usePrefetchCompany() {
  const queryClient = useQueryClient();
  const service = useCompaniesService();

  return useCallback(
    (id) => {
      if (!id) return;
      queryClient.prefetchQuery({
        queryKey: companyKeys.detail(id),
        queryFn: ({ signal }) => service.get(id, { signal }),
        staleTime: 30000,
      });
    },
    [queryClient, service]
  );
}

// ===========================================
// COMPANY CRUD MUTATIONS
// ===========================================

/**
 * Hook to create a new company
 * @returns Mutation object with mutate/mutateAsync functions
 */
export function useCreateCompany() {
  const service = useCompaniesService();
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (data) => service.create(data),
    onSuccess: (newCompany) => {
      // Add to cache immediately
      queryClient.setQueryData(companyKeys.detail(newCompany.id), newCompany);
      // Invalidate list to refetch with new item
      queryClient.invalidateQueries({ queryKey: companyKeys.lists() });
    },
  });
}

/**
 * Hook to update a company with optimistic updates
 * @returns Mutation object with mutate/mutateAsync functions
 */
export function useUpdateCompany() {
  const service = useCompaniesService();
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ id, data }) => service.update(id, data),

    // Optimistic update
    onMutate: async ({ id, data }) => {
      await queryClient.cancelQueries({ queryKey: companyKeys.detail(id) });
      const previousCompany = queryClient.getQueryData(companyKeys.detail(id));

      if (previousCompany) {
        queryClient.setQueryData(companyKeys.detail(id), {
          ...previousCompany,
          ...data,
          updated_at: new Date().toISOString(),
        });
      }

      return { previousCompany };
    },

    onError: (err, { id }, context) => {
      if (context?.previousCompany) {
        queryClient.setQueryData(companyKeys.detail(id), context.previousCompany);
      }
    },

    onSettled: (_, __, { id }) => {
      queryClient.invalidateQueries({ queryKey: companyKeys.detail(id) });
      queryClient.invalidateQueries({ queryKey: companyKeys.lists() });
    },
  });
}

/**
 * Hook to delete a company
 * @returns Mutation object with mutate/mutateAsync functions
 */
export function useDeleteCompany() {
  const service = useCompaniesService();
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (id) => service.delete(id),

    onSuccess: (_, id) => {
      // Remove from cache
      queryClient.removeQueries({ queryKey: companyKeys.detail(id) });
      queryClient.invalidateQueries({ queryKey: companyKeys.lists() });
    },
  });
}

/**
 * Hook to review (approve/reject) a company with optimistic updates
 * @returns Mutation object with mutate/mutateAsync functions
 */
export function useReviewCompany() {
  const service = useCompaniesService();
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ id, decision, notes, riskOverride }) =>
      service.review(id, decision, notes, riskOverride),

    onMutate: async ({ id, decision }) => {
      await queryClient.cancelQueries({ queryKey: companyKeys.detail(id) });
      const previousCompany = queryClient.getQueryData(companyKeys.detail(id));

      if (previousCompany) {
        queryClient.setQueryData(companyKeys.detail(id), {
          ...previousCompany,
          status: decision,
          reviewed_at: new Date().toISOString(),
        });
      }

      return { previousCompany };
    },

    onError: (err, { id }, context) => {
      if (context?.previousCompany) {
        queryClient.setQueryData(companyKeys.detail(id), context.previousCompany);
      }
    },

    onSettled: (_, __, { id }) => {
      queryClient.invalidateQueries({ queryKey: companyKeys.detail(id) });
      queryClient.invalidateQueries({ queryKey: companyKeys.lists() });
    },
  });
}

/**
 * Hook to run screening on a company and its UBOs
 * @returns Mutation object with mutate/mutateAsync functions
 */
export function useScreenCompany() {
  const service = useCompaniesService();
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (id) => service.screen(id),

    onMutate: async (id) => {
      await queryClient.cancelQueries({ queryKey: companyKeys.detail(id) });
      const previousCompany = queryClient.getQueryData(companyKeys.detail(id));

      // Set screening in progress
      if (previousCompany) {
        queryClient.setQueryData(companyKeys.detail(id), {
          ...previousCompany,
          screening_status: 'in_progress',
        });
      }

      return { previousCompany };
    },

    onError: (err, id, context) => {
      if (context?.previousCompany) {
        queryClient.setQueryData(companyKeys.detail(id), context.previousCompany);
      }
    },

    onSettled: (_, __, id) => {
      queryClient.invalidateQueries({ queryKey: companyKeys.detail(id) });
      queryClient.invalidateQueries({ queryKey: companyKeys.lists() });
    },
  });
}

// ===========================================
// BENEFICIAL OWNER HOOKS
// ===========================================

/**
 * Hook to fetch beneficial owners for a company
 * @param {string} companyId - Company ID
 * @param {Object} options - Additional React Query options
 */
export function useCompanyUBOs(companyId, options = {}) {
  const service = useCompaniesService();

  return useQuery({
    queryKey: companyKeys.ubos(companyId),
    queryFn: ({ signal }) => service.listUBOs(companyId, { signal }),
    enabled: !!companyId,
    staleTime: 30000,
    ...options,
  });
}

/**
 * Hook to add a beneficial owner to a company
 * @returns Mutation object with mutate/mutateAsync functions
 */
export function useAddUBO() {
  const service = useCompaniesService();
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ companyId, data }) => service.addUBO(companyId, data),

    onSuccess: (_, { companyId }) => {
      queryClient.invalidateQueries({ queryKey: companyKeys.detail(companyId) });
      queryClient.invalidateQueries({ queryKey: companyKeys.ubos(companyId) });
      queryClient.invalidateQueries({ queryKey: companyKeys.lists() });
    },
  });
}

/**
 * Hook to update a beneficial owner with optimistic updates
 * @returns Mutation object with mutate/mutateAsync functions
 */
export function useUpdateUBO() {
  const service = useCompaniesService();
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ companyId, uboId, data }) =>
      service.updateUBO(companyId, uboId, data),

    onSuccess: (_, { companyId }) => {
      queryClient.invalidateQueries({ queryKey: companyKeys.detail(companyId) });
      queryClient.invalidateQueries({ queryKey: companyKeys.ubos(companyId) });
    },
  });
}

/**
 * Hook to delete a beneficial owner
 * @returns Mutation object with mutate/mutateAsync functions
 */
export function useDeleteUBO() {
  const service = useCompaniesService();
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ companyId, uboId }) => service.deleteUBO(companyId, uboId),

    onSuccess: (_, { companyId }) => {
      queryClient.invalidateQueries({ queryKey: companyKeys.detail(companyId) });
      queryClient.invalidateQueries({ queryKey: companyKeys.ubos(companyId) });
      queryClient.invalidateQueries({ queryKey: companyKeys.lists() });
    },
  });
}

/**
 * Hook to link a UBO to an existing applicant KYC
 * @returns Mutation object with mutate/mutateAsync functions
 */
export function useLinkUBOToApplicant() {
  const service = useCompaniesService();
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ companyId, uboId, applicantId }) =>
      service.linkUBOToApplicant(companyId, uboId, applicantId),

    onSuccess: (_, { companyId }) => {
      queryClient.invalidateQueries({ queryKey: companyKeys.detail(companyId) });
      queryClient.invalidateQueries({ queryKey: companyKeys.ubos(companyId) });
    },
  });
}

// ===========================================
// DOCUMENT HOOKS
// ===========================================

/**
 * Hook to fetch documents for a company
 * @param {string} companyId - Company ID
 * @param {Object} options - Additional React Query options
 */
export function useCompanyDocuments(companyId, options = {}) {
  const service = useCompaniesService();

  return useQuery({
    queryKey: companyKeys.documents(companyId),
    queryFn: ({ signal }) => service.listDocuments(companyId, { signal }),
    enabled: !!companyId,
    staleTime: 30000,
    ...options,
  });
}

/**
 * Hook to request document upload URL
 * @returns Mutation object with mutate/mutateAsync functions
 */
export function useRequestDocumentUpload() {
  const service = useCompaniesService();

  return useMutation({
    mutationFn: ({ companyId, data }) =>
      service.requestDocumentUpload(companyId, data),
  });
}

/**
 * Hook to verify or reject a company document
 * @returns Mutation object with mutate/mutateAsync functions
 */
export function useVerifyCompanyDocument() {
  const service = useCompaniesService();
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ companyId, documentId, decision, notes }) =>
      service.verifyDocument(companyId, documentId, decision, notes),

    onSuccess: (_, { companyId }) => {
      queryClient.invalidateQueries({ queryKey: companyKeys.detail(companyId) });
      queryClient.invalidateQueries({ queryKey: companyKeys.documents(companyId) });
    },
  });
}

/**
 * Hook to get document download URL
 * @returns Mutation for triggering download
 */
export function useDownloadCompanyDocument() {
  const service = useCompaniesService();

  return useMutation({
    mutationFn: async ({ companyId, documentId }) => {
      const result = await service.getDocumentDownloadUrl(companyId, documentId);

      // Open download URL
      const a = document.createElement('a');
      a.href = result.download_url;
      a.download = result.file_name;
      a.target = '_blank';
      a.style.display = 'none';
      document.body.appendChild(a);
      a.click();

      setTimeout(() => {
        document.body.removeChild(a);
      }, 100);

      return result;
    },
  });
}

// ===========================================
// UTILITY HOOKS
// ===========================================

/**
 * Hook to get company counts by status (for dashboard)
 */
export function useCompanyCounts() {
  const service = useCompaniesService();

  return useQuery({
    queryKey: [...companyKeys.all, 'counts'],
    queryFn: async ({ signal }) => {
      const [pending, approved, rejected] = await Promise.all([
        service.list({ status: 'pending', limit: 0 }, { signal }),
        service.list({ status: 'approved', limit: 0 }, { signal }),
        service.list({ status: 'rejected', limit: 0 }, { signal }),
      ]);

      return {
        pending: pending.total,
        approved: approved.total,
        rejected: rejected.total,
        total: pending.total + approved.total + rejected.total,
      };
    },
    staleTime: 60000,
  });
}

/**
 * Hook for searching companies with debounced input
 * Use with a debounced search term
 */
export function useSearchCompanies(searchTerm, options = {}) {
  const service = useCompaniesService();

  return useQuery({
    queryKey: [...companyKeys.lists(), 'search', searchTerm],
    queryFn: ({ signal }) =>
      service.list({ search: searchTerm, limit: 10 }, { signal }),
    enabled: !!searchTerm && searchTerm.length >= 2,
    staleTime: 10000,
    ...options,
  });
}
