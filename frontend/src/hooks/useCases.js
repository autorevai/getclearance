/**
 * React Query hooks for Cases
 *
 * Production-grade hooks with:
 * - Optimistic updates for status changes
 * - Real-time note additions
 * - Assignment tracking
 */

import { useMemo } from 'react';
import { useQuery, useMutation, useQueryClient, useInfiniteQuery } from '@tanstack/react-query';
import { useAuth } from '../auth';
import { CasesService } from '../services';
import { applicantKeys } from './useApplicants';

export const caseKeys = {
  all: ['cases'],
  lists: () => [...caseKeys.all, 'list'],
  list: (filters) => [...caseKeys.lists(), filters],
  details: () => [...caseKeys.all, 'detail'],
  detail: (id) => [...caseKeys.details(), id],
  myCases: (filters) => [...caseKeys.all, 'my-cases', filters],
};

function useCasesService() {
  const { getToken } = useAuth();
  return useMemo(() => new CasesService(getToken), [getToken]);
}

export function useCases(filters = {}, options = {}) {
  const service = useCasesService();

  return useQuery({
    queryKey: caseKeys.list(filters),
    queryFn: ({ signal }) => service.list(filters, { signal }),
    staleTime: 30000,
    ...options,
  });
}

export function useInfiniteCases(filters = {}, options = {}) {
  const service = useCasesService();
  const limit = filters.limit || 20;

  return useInfiniteQuery({
    queryKey: [...caseKeys.list(filters), 'infinite'],
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

export function useCase(id, options = {}) {
  const service = useCasesService();

  return useQuery({
    queryKey: caseKeys.detail(id),
    queryFn: ({ signal }) => service.get(id, { signal }),
    enabled: !!id,
    staleTime: 30000,
    ...options,
  });
}

export function useMyCases(filters = {}, options = {}) {
  const service = useCasesService();

  return useQuery({
    queryKey: caseKeys.myCases(filters),
    queryFn: ({ signal }) => service.getMyCases(filters, { signal }),
    staleTime: 30000,
    ...options,
  });
}

export function useCreateCase() {
  const service = useCasesService();
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (data) => service.create(data),
    onSuccess: (newCase, { applicant_id }) => {
      queryClient.setQueryData(caseKeys.detail(newCase.id), newCase);
      queryClient.invalidateQueries({ queryKey: caseKeys.lists() });
      if (applicant_id) {
        queryClient.invalidateQueries({ queryKey: applicantKeys.detail(applicant_id) });
      }
    },
  });
}

export function useUpdateCase() {
  const service = useCasesService();
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ id, data }) => service.update(id, data),

    onMutate: async ({ id, data }) => {
      await queryClient.cancelQueries({ queryKey: caseKeys.detail(id) });

      const previousCase = queryClient.getQueryData(caseKeys.detail(id));

      if (previousCase) {
        queryClient.setQueryData(caseKeys.detail(id), {
          ...previousCase,
          ...data,
          updated_at: new Date().toISOString(),
        });
      }

      return { previousCase };
    },

    onError: (err, { id }, context) => {
      if (context?.previousCase) {
        queryClient.setQueryData(caseKeys.detail(id), context.previousCase);
      }
    },

    onSettled: (_, __, { id }) => {
      queryClient.invalidateQueries({ queryKey: caseKeys.detail(id) });
      queryClient.invalidateQueries({ queryKey: caseKeys.lists() });
    },
  });
}

export function useResolveCase() {
  const service = useCasesService();
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ id, resolution, notes }) => service.resolve(id, resolution, notes),

    onMutate: async ({ id, resolution }) => {
      await queryClient.cancelQueries({ queryKey: caseKeys.detail(id) });

      const previousCase = queryClient.getQueryData(caseKeys.detail(id));

      if (previousCase) {
        queryClient.setQueryData(caseKeys.detail(id), {
          ...previousCase,
          status: 'resolved',
          resolution,
          resolved_at: new Date().toISOString(),
        });
      }

      return { previousCase };
    },

    onError: (err, { id }, context) => {
      if (context?.previousCase) {
        queryClient.setQueryData(caseKeys.detail(id), context.previousCase);
      }
    },

    onSettled: (_, __, { id, applicantId }) => {
      queryClient.invalidateQueries({ queryKey: caseKeys.detail(id) });
      queryClient.invalidateQueries({ queryKey: caseKeys.lists() });
      if (applicantId) {
        queryClient.invalidateQueries({ queryKey: applicantKeys.detail(applicantId) });
      }
    },
  });
}

export function useAddCaseNote() {
  const service = useCasesService();
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ id, content }) => service.addNote(id, content),

    // Optimistic update - add note immediately
    onMutate: async ({ id, content }) => {
      await queryClient.cancelQueries({ queryKey: caseKeys.detail(id) });

      const previousCase = queryClient.getQueryData(caseKeys.detail(id));

      if (previousCase) {
        const optimisticNote = {
          id: `temp-${Date.now()}`,
          content,
          created_at: new Date().toISOString(),
          created_by: 'current-user', // Will be replaced by server response
        };

        queryClient.setQueryData(caseKeys.detail(id), {
          ...previousCase,
          notes: [...(previousCase.notes || []), optimisticNote],
        });
      }

      return { previousCase };
    },

    onError: (err, { id }, context) => {
      if (context?.previousCase) {
        queryClient.setQueryData(caseKeys.detail(id), context.previousCase);
      }
    },

    onSettled: (_, __, { id }) => {
      queryClient.invalidateQueries({ queryKey: caseKeys.detail(id) });
    },
  });
}

export function useAssignCase() {
  const service = useCasesService();
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ id, userId }) => service.assign(id, userId),

    onMutate: async ({ id, userId }) => {
      await queryClient.cancelQueries({ queryKey: caseKeys.detail(id) });

      const previousCase = queryClient.getQueryData(caseKeys.detail(id));

      if (previousCase) {
        queryClient.setQueryData(caseKeys.detail(id), {
          ...previousCase,
          assigned_to: userId,
        });
      }

      return { previousCase };
    },

    onError: (err, { id }, context) => {
      if (context?.previousCase) {
        queryClient.setQueryData(caseKeys.detail(id), context.previousCase);
      }
    },

    onSettled: (_, __, { id }) => {
      queryClient.invalidateQueries({ queryKey: caseKeys.detail(id) });
      queryClient.invalidateQueries({ queryKey: caseKeys.lists() });
      queryClient.invalidateQueries({ queryKey: caseKeys.myCases({}) });
    },
  });
}

export function useApplicantCases(applicantId, options = {}) {
  return useCases({ applicant_id: applicantId }, options);
}

/**
 * Hook to get case counts by status (for dashboard)
 */
export function useCaseCounts() {
  const service = useCasesService();

  return useQuery({
    queryKey: [...caseKeys.all, 'counts'],
    queryFn: ({ signal }) => service.getCounts({ signal }),
    staleTime: 60000,
  });
}
