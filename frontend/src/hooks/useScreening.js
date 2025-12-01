/**
 * React Query hooks for Screening
 *
 * Provides data fetching, caching, and mutation hooks for AML screening operations.
 */

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { useAuth } from '../auth';
import { ScreeningService } from '../services';
import { applicantKeys } from './useApplicants';

// Query key factory
export const screeningKeys = {
  all: ['screening'],
  checks: () => [...screeningKeys.all, 'checks'],
  checkList: (filters) => [...screeningKeys.checks(), filters],
  checkDetail: (id) => [...screeningKeys.checks(), 'detail', id],
  hits: () => [...screeningKeys.all, 'hits'],
  hitSuggestion: (hitId) => [...screeningKeys.hits(), hitId, 'suggestion'],
};

/**
 * Hook to fetch list of screening checks
 * @param {Object} filters - Filter parameters (applicant_id, status, limit, offset)
 * @param {Object} options - Additional React Query options
 */
export function useScreeningChecks(filters = {}, options = {}) {
  const { getToken } = useAuth();

  return useQuery({
    queryKey: screeningKeys.checkList(filters),
    queryFn: async () => {
      const service = new ScreeningService(getToken);
      return service.listChecks(filters);
    },
    ...options,
  });
}

/**
 * Hook to fetch a single screening check with all hits
 * @param {string} id - Check ID
 * @param {Object} options - Additional React Query options
 */
export function useScreeningCheck(id, options = {}) {
  const { getToken } = useAuth();

  return useQuery({
    queryKey: screeningKeys.checkDetail(id),
    queryFn: async () => {
      const service = new ScreeningService(getToken);
      return service.getCheck(id);
    },
    enabled: !!id,
    ...options,
  });
}

/**
 * Hook to get AI suggestion for a screening hit
 * @param {string} hitId - Hit ID
 * @param {Object} options - Additional React Query options
 */
export function useHitSuggestion(hitId, options = {}) {
  const { getToken } = useAuth();

  return useQuery({
    queryKey: screeningKeys.hitSuggestion(hitId),
    queryFn: async () => {
      const service = new ScreeningService(getToken);
      return service.getHitSuggestion(hitId);
    },
    enabled: !!hitId,
    staleTime: 60000, // Suggestions are stable for 1 minute
    ...options,
  });
}

/**
 * Hook to run a new screening check
 * @returns Mutation object with mutate/mutateAsync functions
 */
export function useRunScreening() {
  const { getToken } = useAuth();
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (data) => {
      const service = new ScreeningService(getToken);
      return service.runCheck(data);
    },
    onSuccess: (result, { applicant_id }) => {
      queryClient.invalidateQueries({ queryKey: screeningKeys.checks() });
      if (applicant_id) {
        queryClient.invalidateQueries({
          queryKey: applicantKeys.detail(applicant_id),
        });
      }
    },
  });
}

/**
 * Hook to resolve a screening hit
 * @returns Mutation object with mutate/mutateAsync functions
 */
export function useResolveHit() {
  const { getToken } = useAuth();
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async ({ hitId, resolution, notes }) => {
      const service = new ScreeningService(getToken);
      return service.resolveHit(hitId, resolution, notes);
    },
    onSuccess: (_, { checkId, applicantId }) => {
      queryClient.invalidateQueries({ queryKey: screeningKeys.checks() });
      if (checkId) {
        queryClient.invalidateQueries({
          queryKey: screeningKeys.checkDetail(checkId),
        });
      }
      if (applicantId) {
        queryClient.invalidateQueries({
          queryKey: applicantKeys.detail(applicantId),
        });
      }
    },
  });
}

/**
 * Hook to batch resolve multiple hits
 * @returns Mutation object
 */
export function useBatchResolveHits() {
  const { getToken } = useAuth();
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (resolutions) => {
      const service = new ScreeningService(getToken);
      return service.batchResolve(resolutions);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: screeningKeys.all });
    },
  });
}

/**
 * Hook to fetch screening checks for a specific applicant
 * @param {string} applicantId - Applicant ID
 * @param {Object} options - Additional React Query options
 */
export function useApplicantScreening(applicantId, options = {}) {
  return useScreeningChecks({ applicant_id: applicantId }, options);
}
