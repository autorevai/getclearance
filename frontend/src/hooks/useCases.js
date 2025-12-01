/**
 * React Query hooks for Cases
 *
 * Provides data fetching, caching, and mutation hooks for case management.
 */

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { useAuth } from '../auth';
import { CasesService } from '../services';
import { applicantKeys } from './useApplicants';

// Query key factory
export const caseKeys = {
  all: ['cases'],
  lists: () => [...caseKeys.all, 'list'],
  list: (filters) => [...caseKeys.lists(), filters],
  details: () => [...caseKeys.all, 'detail'],
  detail: (id) => [...caseKeys.details(), id],
  myCases: (filters) => [...caseKeys.all, 'my-cases', filters],
};

/**
 * Hook to fetch list of cases with filters
 * @param {Object} filters - Filter parameters (status, priority, assigned_to, applicant_id, search)
 * @param {Object} options - Additional React Query options
 */
export function useCases(filters = {}, options = {}) {
  const { getToken } = useAuth();

  return useQuery({
    queryKey: caseKeys.list(filters),
    queryFn: async () => {
      const service = new CasesService(getToken);
      return service.list(filters);
    },
    ...options,
  });
}

/**
 * Hook to fetch a single case by ID
 * @param {string} id - Case ID
 * @param {Object} options - Additional React Query options
 */
export function useCase(id, options = {}) {
  const { getToken } = useAuth();

  return useQuery({
    queryKey: caseKeys.detail(id),
    queryFn: async () => {
      const service = new CasesService(getToken);
      return service.get(id);
    },
    enabled: !!id,
    ...options,
  });
}

/**
 * Hook to fetch cases assigned to current user
 * @param {Object} filters - Additional filters
 * @param {Object} options - Additional React Query options
 */
export function useMyCases(filters = {}, options = {}) {
  const { getToken } = useAuth();

  return useQuery({
    queryKey: caseKeys.myCases(filters),
    queryFn: async () => {
      const service = new CasesService(getToken);
      return service.getMyCases(filters);
    },
    ...options,
  });
}

/**
 * Hook to create a new case
 * @returns Mutation object with mutate/mutateAsync functions
 */
export function useCreateCase() {
  const { getToken } = useAuth();
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (data) => {
      const service = new CasesService(getToken);
      return service.create(data);
    },
    onSuccess: (_, { applicant_id }) => {
      queryClient.invalidateQueries({ queryKey: caseKeys.lists() });
      if (applicant_id) {
        queryClient.invalidateQueries({
          queryKey: applicantKeys.detail(applicant_id),
        });
      }
    },
  });
}

/**
 * Hook to update a case
 * @returns Mutation object with mutate/mutateAsync functions
 */
export function useUpdateCase() {
  const { getToken } = useAuth();
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async ({ id, data }) => {
      const service = new CasesService(getToken);
      return service.update(id, data);
    },
    onSuccess: (_, { id }) => {
      queryClient.invalidateQueries({ queryKey: caseKeys.detail(id) });
      queryClient.invalidateQueries({ queryKey: caseKeys.lists() });
    },
  });
}

/**
 * Hook to resolve a case
 * @returns Mutation object with mutate/mutateAsync functions
 */
export function useResolveCase() {
  const { getToken } = useAuth();
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async ({ id, resolution, notes }) => {
      const service = new CasesService(getToken);
      return service.resolve(id, resolution, notes);
    },
    onSuccess: (_, { id, applicantId }) => {
      queryClient.invalidateQueries({ queryKey: caseKeys.detail(id) });
      queryClient.invalidateQueries({ queryKey: caseKeys.lists() });
      if (applicantId) {
        queryClient.invalidateQueries({
          queryKey: applicantKeys.detail(applicantId),
        });
      }
    },
  });
}

/**
 * Hook to add a note to a case
 * @returns Mutation object with mutate/mutateAsync functions
 */
export function useAddCaseNote() {
  const { getToken } = useAuth();
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async ({ id, content }) => {
      const service = new CasesService(getToken);
      return service.addNote(id, content);
    },
    onSuccess: (_, { id }) => {
      queryClient.invalidateQueries({ queryKey: caseKeys.detail(id) });
    },
  });
}

/**
 * Hook to assign a case to a user
 * @returns Mutation object with mutate/mutateAsync functions
 */
export function useAssignCase() {
  const { getToken } = useAuth();
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async ({ id, userId }) => {
      const service = new CasesService(getToken);
      return service.assign(id, userId);
    },
    onSuccess: (_, { id }) => {
      queryClient.invalidateQueries({ queryKey: caseKeys.detail(id) });
      queryClient.invalidateQueries({ queryKey: caseKeys.lists() });
      queryClient.invalidateQueries({ queryKey: caseKeys.myCases({}) });
    },
  });
}

/**
 * Hook to fetch cases for a specific applicant
 * @param {string} applicantId - Applicant ID
 * @param {Object} options - Additional React Query options
 */
export function useApplicantCases(applicantId, options = {}) {
  return useCases({ applicant_id: applicantId }, options);
}
