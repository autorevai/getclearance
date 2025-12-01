/**
 * React Query hooks for Applicants
 *
 * Provides data fetching, caching, and mutation hooks for applicant operations.
 */

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
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
 * Hook to fetch list of applicants with filters and pagination
 * @param {Object} filters - Filter parameters (status, risk_level, search, limit, offset)
 * @param {Object} options - Additional React Query options
 */
export function useApplicants(filters = {}, options = {}) {
  const { getToken } = useAuth();

  return useQuery({
    queryKey: applicantKeys.list(filters),
    queryFn: async () => {
      const service = new ApplicantsService(getToken);
      return service.list(filters);
    },
    ...options,
  });
}

/**
 * Hook to fetch a single applicant by ID
 * @param {string} id - Applicant ID
 * @param {Object} options - Additional React Query options
 */
export function useApplicant(id, options = {}) {
  const { getToken } = useAuth();

  return useQuery({
    queryKey: applicantKeys.detail(id),
    queryFn: async () => {
      const service = new ApplicantsService(getToken);
      return service.get(id);
    },
    enabled: !!id,
    ...options,
  });
}

/**
 * Hook to fetch applicant timeline/audit log
 * @param {string} id - Applicant ID
 * @param {Object} options - Additional React Query options
 */
export function useApplicantTimeline(id, options = {}) {
  const { getToken } = useAuth();

  return useQuery({
    queryKey: applicantKeys.timeline(id),
    queryFn: async () => {
      const service = new ApplicantsService(getToken);
      return service.getTimeline(id);
    },
    enabled: !!id,
    ...options,
  });
}

/**
 * Hook to create a new applicant
 * @returns Mutation object with mutate/mutateAsync functions
 */
export function useCreateApplicant() {
  const { getToken } = useAuth();
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (data) => {
      const service = new ApplicantsService(getToken);
      return service.create(data);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: applicantKeys.lists() });
    },
  });
}

/**
 * Hook to update an applicant
 * @returns Mutation object with mutate/mutateAsync functions
 */
export function useUpdateApplicant() {
  const { getToken } = useAuth();
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async ({ id, data }) => {
      const service = new ApplicantsService(getToken);
      return service.update(id, data);
    },
    onSuccess: (_, { id }) => {
      queryClient.invalidateQueries({ queryKey: applicantKeys.detail(id) });
      queryClient.invalidateQueries({ queryKey: applicantKeys.lists() });
    },
  });
}

/**
 * Hook to review (approve/reject) an applicant
 * @returns Mutation object with mutate/mutateAsync functions
 */
export function useReviewApplicant() {
  const { getToken } = useAuth();
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async ({ id, decision, notes, riskOverride }) => {
      const service = new ApplicantsService(getToken);
      return service.review(id, decision, notes, riskOverride);
    },
    onSuccess: (_, { id }) => {
      queryClient.invalidateQueries({ queryKey: applicantKeys.detail(id) });
      queryClient.invalidateQueries({ queryKey: applicantKeys.lists() });
      queryClient.invalidateQueries({ queryKey: applicantKeys.timeline(id) });
    },
  });
}

/**
 * Hook to complete a verification step
 * @returns Mutation object with mutate/mutateAsync functions
 */
export function useCompleteStep() {
  const { getToken } = useAuth();
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async ({ id, step }) => {
      const service = new ApplicantsService(getToken);
      return service.completeStep(id, step);
    },
    onSuccess: (_, { id }) => {
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
  const { getToken } = useAuth();

  return useMutation({
    mutationFn: async ({ id, filename }) => {
      const service = new ApplicantsService(getToken);
      const blob = await service.downloadEvidence(id);

      // Trigger browser download
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = filename || `evidence-${id}.pdf`;
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);
      document.body.removeChild(a);

      return blob;
    },
  });
}
