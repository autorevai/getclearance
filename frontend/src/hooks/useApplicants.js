/**
 * React Query hooks for Applicants
 *
 * Production-grade hooks with:
 * - Singleton service instances (no recreation on each render)
 * - Optimistic updates for instant UI feedback
 * - Proper cache invalidation strategies
 * - Infinite query support for pagination
 * - Prefetching for predictive loading
 */

import { useCallback, useMemo } from 'react';
import {
  useQuery,
  useMutation,
  useQueryClient,
  useInfiniteQuery,
} from '@tanstack/react-query';
import { useAuth } from '../auth';
import { ApplicantsService } from '../services';

// Query key factory for consistent key management
export const applicantKeys = {
  all: ['applicants'],
  lists: () => [...applicantKeys.all, 'list'],
  list: (filters) => [...applicantKeys.lists(), filters],
  details: () => [...applicantKeys.all, 'detail'],
  detail: (id) => [...applicantKeys.details(), id],
  timeline: (id) => [...applicantKeys.detail(id), 'timeline'],
  evidence: (id) => [...applicantKeys.detail(id), 'evidence'],
};

/**
 * Hook to get a memoized ApplicantsService instance
 * Prevents recreating service on every render
 */
function useApplicantsService() {
  const { getToken } = useAuth();
  return useMemo(() => new ApplicantsService(getToken), [getToken]);
}

/**
 * Hook to fetch list of applicants with filters and pagination
 * @param {Object} filters - Filter parameters (status, risk_level, search, limit, offset)
 * @param {Object} options - Additional React Query options
 */
export function useApplicants(filters = {}, options = {}) {
  const service = useApplicantsService();

  return useQuery({
    queryKey: applicantKeys.list(filters),
    queryFn: ({ signal }) => service.list(filters, { signal }),
    staleTime: 30000,
    ...options,
  });
}

/**
 * Hook for infinite scrolling applicant list
 * @param {Object} filters - Filter parameters
 * @param {Object} options - Additional React Query options
 */
export function useInfiniteApplicants(filters = {}, options = {}) {
  const service = useApplicantsService();
  const limit = filters.limit || 20;

  return useInfiniteQuery({
    queryKey: [...applicantKeys.list(filters), 'infinite'],
    queryFn: ({ pageParam = 0, signal }) =>
      service.list({ ...filters, limit, offset: pageParam }, { signal }),
    getNextPageParam: (lastPage, allPages) => {
      const totalFetched = allPages.reduce((sum, page) => sum + page.items.length, 0);
      return totalFetched < lastPage.total ? totalFetched : undefined;
    },
    staleTime: 30000,
    ...options,
  });
}

/**
 * Hook to fetch a single applicant by ID
 * @param {string} id - Applicant ID
 * @param {Object} options - Additional React Query options
 */
export function useApplicant(id, options = {}) {
  const service = useApplicantsService();

  return useQuery({
    queryKey: applicantKeys.detail(id),
    queryFn: ({ signal }) => service.get(id, { signal }),
    enabled: !!id,
    staleTime: 30000,
    ...options,
  });
}

/**
 * Hook to prefetch an applicant (for hover states, etc.)
 */
export function usePrefetchApplicant() {
  const queryClient = useQueryClient();
  const service = useApplicantsService();

  return useCallback(
    (id) => {
      if (!id) return;
      queryClient.prefetchQuery({
        queryKey: applicantKeys.detail(id),
        queryFn: ({ signal }) => service.get(id, { signal }),
        staleTime: 30000,
      });
    },
    [queryClient, service]
  );
}

/**
 * Hook to fetch applicant timeline/audit log
 * @param {string} id - Applicant ID
 * @param {Object} options - Additional React Query options
 */
export function useApplicantTimeline(id, options = {}) {
  const service = useApplicantsService();

  return useQuery({
    queryKey: applicantKeys.timeline(id),
    queryFn: ({ signal }) => service.getTimeline(id, { signal }),
    enabled: !!id,
    staleTime: 60000, // Timeline changes less frequently
    ...options,
  });
}

/**
 * Hook to create a new applicant
 * @returns Mutation object with mutate/mutateAsync functions
 */
export function useCreateApplicant() {
  const service = useApplicantsService();
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (data) => service.create(data),
    onSuccess: (newApplicant) => {
      // Add to cache immediately
      queryClient.setQueryData(
        applicantKeys.detail(newApplicant.id),
        newApplicant
      );
      // Invalidate list to refetch with new item
      queryClient.invalidateQueries({ queryKey: applicantKeys.lists() });
    },
  });
}

/**
 * Hook to update an applicant with optimistic updates
 * @returns Mutation object with mutate/mutateAsync functions
 */
export function useUpdateApplicant() {
  const service = useApplicantsService();
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ id, data }) => service.update(id, data),

    // Optimistic update
    onMutate: async ({ id, data }) => {
      // Cancel outgoing refetches
      await queryClient.cancelQueries({ queryKey: applicantKeys.detail(id) });

      // Snapshot previous value
      const previousApplicant = queryClient.getQueryData(applicantKeys.detail(id));

      // Optimistically update
      if (previousApplicant) {
        queryClient.setQueryData(applicantKeys.detail(id), {
          ...previousApplicant,
          ...data,
          updated_at: new Date().toISOString(),
        });
      }

      return { previousApplicant };
    },

    // Rollback on error
    onError: (err, { id }, context) => {
      if (context?.previousApplicant) {
        queryClient.setQueryData(applicantKeys.detail(id), context.previousApplicant);
      }
    },

    // Refetch after success or error
    onSettled: (_, __, { id }) => {
      queryClient.invalidateQueries({ queryKey: applicantKeys.detail(id) });
      queryClient.invalidateQueries({ queryKey: applicantKeys.lists() });
    },
  });
}

/**
 * Hook to review (approve/reject) an applicant with optimistic updates
 * @returns Mutation object with mutate/mutateAsync functions
 */
export function useReviewApplicant() {
  const service = useApplicantsService();
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ id, decision, notes, riskOverride }) =>
      service.review(id, decision, notes, riskOverride),

    // Optimistic update
    onMutate: async ({ id, decision }) => {
      await queryClient.cancelQueries({ queryKey: applicantKeys.detail(id) });

      const previousApplicant = queryClient.getQueryData(applicantKeys.detail(id));

      // Optimistically update status based on decision
      if (previousApplicant) {
        const newStatus =
          decision === 'approve' ? 'approved' :
          decision === 'reject' ? 'rejected' :
          'pending_info';

        queryClient.setQueryData(applicantKeys.detail(id), {
          ...previousApplicant,
          status: newStatus,
          reviewed_at: new Date().toISOString(),
        });
      }

      return { previousApplicant };
    },

    onError: (err, { id }, context) => {
      if (context?.previousApplicant) {
        queryClient.setQueryData(applicantKeys.detail(id), context.previousApplicant);
      }
    },

    onSettled: (_, __, { id }) => {
      queryClient.invalidateQueries({ queryKey: applicantKeys.detail(id) });
      queryClient.invalidateQueries({ queryKey: applicantKeys.lists() });
      queryClient.invalidateQueries({ queryKey: applicantKeys.timeline(id) });
    },
  });
}

/**
 * Hook to complete a verification step with optimistic updates
 * @returns Mutation object with mutate/mutateAsync functions
 */
export function useCompleteStep() {
  const service = useApplicantsService();
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ id, step }) => service.completeStep(id, step),

    onMutate: async ({ id, step }) => {
      await queryClient.cancelQueries({ queryKey: applicantKeys.detail(id) });

      const previousApplicant = queryClient.getQueryData(applicantKeys.detail(id));

      if (previousApplicant?.steps) {
        const updatedSteps = previousApplicant.steps.map((s) =>
          s.name === step ? { ...s, status: 'completed', completed_at: new Date().toISOString() } : s
        );

        queryClient.setQueryData(applicantKeys.detail(id), {
          ...previousApplicant,
          steps: updatedSteps,
        });
      }

      return { previousApplicant };
    },

    onError: (err, { id }, context) => {
      if (context?.previousApplicant) {
        queryClient.setQueryData(applicantKeys.detail(id), context.previousApplicant);
      }
    },

    onSettled: (_, __, { id }) => {
      queryClient.invalidateQueries({ queryKey: applicantKeys.detail(id) });
      queryClient.invalidateQueries({ queryKey: applicantKeys.timeline(id) });
    },
  });
}

/**
 * Hook to download evidence pack
 * Returns a function to trigger the download
 */
export function useDownloadEvidence() {
  const service = useApplicantsService();

  return useMutation({
    mutationFn: async ({ id, filename }) => {
      const blob = await service.downloadEvidence(id);

      // Create download link
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = filename || `evidence-${id}.pdf`;
      a.style.display = 'none';
      document.body.appendChild(a);
      a.click();

      // Cleanup
      setTimeout(() => {
        window.URL.revokeObjectURL(url);
        document.body.removeChild(a);
      }, 100);

      return blob;
    },
  });
}

/**
 * Hook to get applicant counts by status (for dashboard)
 */
export function useApplicantCounts() {
  const service = useApplicantsService();

  return useQuery({
    queryKey: [...applicantKeys.all, 'counts'],
    queryFn: async ({ signal }) => {
      // Fetch minimal data for each status
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
 * Hook for searching applicants with debounced input
 * Use with a debounced search term
 */
export function useSearchApplicants(searchTerm, options = {}) {
  const service = useApplicantsService();

  return useQuery({
    queryKey: [...applicantKeys.lists(), 'search', searchTerm],
    queryFn: ({ signal }) =>
      service.list({ search: searchTerm, limit: 10 }, { signal }),
    enabled: !!searchTerm && searchTerm.length >= 2,
    staleTime: 10000,
    ...options,
  });
}

/**
 * Hook to batch review multiple applicants
 * @returns Mutation object with mutate/mutateAsync functions
 */
export function useBatchReviewApplicants() {
  const service = useApplicantsService();
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async ({ ids, decision, notes }) => {
      // Process all reviews in parallel
      const results = await Promise.allSettled(
        ids.map((id) => service.review(id, decision, notes))
      );

      const succeeded = results.filter((r) => r.status === 'fulfilled').length;
      const failed = results.filter((r) => r.status === 'rejected').length;

      return { succeeded, failed, total: ids.length };
    },

    // Optimistic update for all selected applicants
    onMutate: async ({ ids, decision }) => {
      // Cancel all related queries
      await Promise.all(
        ids.map((id) =>
          queryClient.cancelQueries({ queryKey: applicantKeys.detail(id) })
        )
      );

      // Store previous values
      const previousApplicants = {};
      ids.forEach((id) => {
        previousApplicants[id] = queryClient.getQueryData(applicantKeys.detail(id));
      });

      // Optimistically update all
      const newStatus =
        decision === 'approve' ? 'approved' :
        decision === 'reject' ? 'rejected' :
        'pending_info';

      ids.forEach((id) => {
        const previous = previousApplicants[id];
        if (previous) {
          queryClient.setQueryData(applicantKeys.detail(id), {
            ...previous,
            status: newStatus,
            reviewed_at: new Date().toISOString(),
          });
        }
      });

      return { previousApplicants };
    },

    onError: (err, { ids }, context) => {
      // Rollback all
      if (context?.previousApplicants) {
        ids.forEach((id) => {
          if (context.previousApplicants[id]) {
            queryClient.setQueryData(applicantKeys.detail(id), context.previousApplicants[id]);
          }
        });
      }
    },

    onSettled: (_, __, { ids }) => {
      // Invalidate all affected queries
      ids.forEach((id) => {
        queryClient.invalidateQueries({ queryKey: applicantKeys.detail(id) });
        queryClient.invalidateQueries({ queryKey: applicantKeys.timeline(id) });
      });
      queryClient.invalidateQueries({ queryKey: applicantKeys.lists() });
    },
  });
}
