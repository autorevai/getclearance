/**
 * React Query hooks for Screening
 *
 * Production-grade hooks with:
 * - Optimistic updates for hit resolution
 * - Polling for check completion
 * - AI suggestion caching
 */

import { useMemo } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { useAuth } from '../auth';
import { ScreeningService } from '../services';
import { applicantKeys } from './useApplicants';

export const screeningKeys = {
  all: ['screening'],
  checks: () => [...screeningKeys.all, 'checks'],
  checkList: (filters) => [...screeningKeys.checks(), filters],
  checkDetail: (id) => [...screeningKeys.checks(), 'detail', id],
  hits: () => [...screeningKeys.all, 'hits'],
  hitSuggestion: (hitId) => [...screeningKeys.hits(), hitId, 'suggestion'],
};

function useScreeningService() {
  const { getToken } = useAuth();
  return useMemo(() => new ScreeningService(getToken), [getToken]);
}

export function useScreeningChecks(filters = {}, options = {}) {
  const service = useScreeningService();

  return useQuery({
    queryKey: screeningKeys.checkList(filters),
    queryFn: ({ signal }) => service.listChecks(filters, { signal }),
    staleTime: 30000,
    ...options,
  });
}

export function useScreeningCheck(id, options = {}) {
  const service = useScreeningService();

  return useQuery({
    queryKey: screeningKeys.checkDetail(id),
    queryFn: ({ signal }) => service.getCheck(id, { signal }),
    enabled: !!id,
    staleTime: 30000,
    ...options,
  });
}

/**
 * Poll a screening check until complete
 */
export function useScreeningCheckPolling(id, options = {}) {
  const service = useScreeningService();
  const { enabled = true, onComplete } = options;

  return useQuery({
    queryKey: [...screeningKeys.checkDetail(id), 'polling'],
    queryFn: ({ signal }) => service.getCheck(id, { signal }),
    enabled: !!id && enabled,
    refetchInterval: (query) => {
      const check = query.state.data;
      if (!check) return 2000;

      if (check.status === 'completed' || check.status === 'failed') {
        if (onComplete) onComplete(check);
        return false;
      }
      return 2000;
    },
    staleTime: 0,
  });
}

export function useHitSuggestion(hitId, options = {}) {
  const service = useScreeningService();

  return useQuery({
    queryKey: screeningKeys.hitSuggestion(hitId),
    queryFn: ({ signal }) => service.getHitSuggestion(hitId, { signal }),
    enabled: !!hitId,
    staleTime: 300000, // Suggestions are stable for 5 minutes
    ...options,
  });
}

export function useRunScreening() {
  const service = useScreeningService();
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (data) => service.runCheck(data),
    onSuccess: (result, { applicant_id }) => {
      queryClient.invalidateQueries({ queryKey: screeningKeys.checks() });
      if (applicant_id) {
        queryClient.invalidateQueries({ queryKey: applicantKeys.detail(applicant_id) });
      }
    },
  });
}

export function useResolveHit() {
  const service = useScreeningService();
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ hitId, resolution, notes }) =>
      service.resolveHit(hitId, resolution, notes),

    // Optimistic update
    onMutate: async ({ hitId, resolution, checkId }) => {
      if (!checkId) return {};

      await queryClient.cancelQueries({ queryKey: screeningKeys.checkDetail(checkId) });

      const previousCheck = queryClient.getQueryData(screeningKeys.checkDetail(checkId));

      if (previousCheck?.hits) {
        const updatedHits = previousCheck.hits.map((hit) =>
          hit.id === hitId
            ? { ...hit, resolution, resolved_at: new Date().toISOString() }
            : hit
        );

        queryClient.setQueryData(screeningKeys.checkDetail(checkId), {
          ...previousCheck,
          hits: updatedHits,
        });
      }

      return { previousCheck };
    },

    onError: (err, { checkId }, context) => {
      if (context?.previousCheck) {
        queryClient.setQueryData(screeningKeys.checkDetail(checkId), context.previousCheck);
      }
    },

    onSettled: (_, __, { checkId, applicantId }) => {
      queryClient.invalidateQueries({ queryKey: screeningKeys.checks() });
      if (checkId) {
        queryClient.invalidateQueries({ queryKey: screeningKeys.checkDetail(checkId) });
      }
      if (applicantId) {
        queryClient.invalidateQueries({ queryKey: applicantKeys.detail(applicantId) });
      }
    },
  });
}

export function useBatchResolveHits() {
  const service = useScreeningService();
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (resolutions) => {
      const results = await Promise.allSettled(
        resolutions.map(({ hitId, resolution, notes }) =>
          service.resolveHit(hitId, resolution, notes)
        )
      );

      const succeeded = results.filter((r) => r.status === 'fulfilled').length;
      const failed = results.filter((r) => r.status === 'rejected').length;

      return { succeeded, failed, total: resolutions.length };
    },
    onSettled: () => {
      queryClient.invalidateQueries({ queryKey: screeningKeys.all });
    },
  });
}

export function useApplicantScreening(applicantId, options = {}) {
  return useScreeningChecks({ applicant_id: applicantId }, options);
}
