/**
 * React Query hooks for AI Features
 *
 * Provides data fetching, caching, and mutation hooks for AI-powered features.
 */

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { useAuth } from '../auth';
import { AIService } from '../services';
import { applicantKeys } from './useApplicants';

// Query key factory
export const aiKeys = {
  all: ['ai'],
  riskSummaries: () => [...aiKeys.all, 'risk-summary'],
  riskSummary: (applicantId) => [...aiKeys.riskSummaries(), applicantId],
  assistant: () => [...aiKeys.all, 'assistant'],
  batchJobs: () => [...aiKeys.all, 'batch'],
  batchJob: (jobId) => [...aiKeys.batchJobs(), jobId],
  documentSuggestions: (documentId) => [...aiKeys.all, 'document-suggestions', documentId],
};

/**
 * Hook to fetch AI risk summary for an applicant
 * @param {string} applicantId - Applicant ID
 * @param {Object} options - Additional React Query options
 */
export function useRiskSummary(applicantId, options = {}) {
  const { getToken } = useAuth();

  return useQuery({
    queryKey: aiKeys.riskSummary(applicantId),
    queryFn: async () => {
      const service = new AIService(getToken);
      return service.getRiskSummary(applicantId);
    },
    enabled: !!applicantId,
    staleTime: 60000, // Risk summaries are stable for 1 minute
    ...options,
  });
}

/**
 * Hook to regenerate risk summary for an applicant
 * @returns Mutation object with mutate/mutateAsync functions
 */
export function useRegenerateRiskSummary() {
  const { getToken } = useAuth();
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (applicantId) => {
      const service = new AIService(getToken);
      return service.regenerateRiskSummary(applicantId);
    },
    onSuccess: (data, applicantId) => {
      queryClient.setQueryData(aiKeys.riskSummary(applicantId), data);
      queryClient.invalidateQueries({
        queryKey: applicantKeys.detail(applicantId),
      });
    },
  });
}

/**
 * Hook to ask the AI assistant a question
 * @returns Mutation object with mutate/mutateAsync functions
 */
export function useAskAssistant() {
  const { getToken } = useAuth();

  return useMutation({
    mutationFn: async ({ query, applicantId, context }) => {
      const service = new AIService(getToken);
      return service.askAssistant(query, applicantId, context);
    },
  });
}

/**
 * Hook for batch risk analysis
 * @returns Mutation object with mutate/mutateAsync functions
 */
export function useBatchAnalyze() {
  const { getToken } = useAuth();
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (applicantIds) => {
      const service = new AIService(getToken);
      return service.batchAnalyze(applicantIds);
    },
    onSuccess: () => {
      // Will need to poll for job completion
    },
  });
}

/**
 * Hook to get batch analysis job status
 * @param {string} jobId - Job ID
 * @param {Object} options - Additional React Query options
 */
export function useBatchJobStatus(jobId, options = {}) {
  const { getToken } = useAuth();

  return useQuery({
    queryKey: aiKeys.batchJob(jobId),
    queryFn: async () => {
      const service = new AIService(getToken);
      return service.getBatchStatus(jobId);
    },
    enabled: !!jobId,
    refetchInterval: (query) => {
      // Poll every 2 seconds while job is running
      const data = query.state.data;
      if (data && (data.status === 'completed' || data.status === 'failed')) {
        return false;
      }
      return 2000;
    },
    ...options,
  });
}

/**
 * Hook to get AI suggestions for document verification
 * @param {string} documentId - Document ID
 * @param {Object} options - Additional React Query options
 */
export function useDocumentSuggestions(documentId, options = {}) {
  const { getToken } = useAuth();

  return useQuery({
    queryKey: aiKeys.documentSuggestions(documentId),
    queryFn: async () => {
      const service = new AIService(getToken);
      return service.getDocumentSuggestions(documentId);
    },
    enabled: !!documentId,
    staleTime: 60000,
    ...options,
  });
}

/**
 * Custom hook for managing an AI assistant conversation
 * Tracks messages and handles sending/receiving
 *
 * @param {string} [applicantId] - Optional applicant context
 * @returns {Object} Conversation state and methods
 */
export function useAssistantConversation(applicantId = null) {
  const askAssistant = useAskAssistant();

  return {
    isLoading: askAssistant.isPending,
    error: askAssistant.error,

    /**
     * Send a message to the assistant
     * @param {string} query - User's question
     * @param {string} [context] - Additional context
     * @returns {Promise<Object>} Assistant response
     */
    sendMessage: async (query, context = null) => {
      return askAssistant.mutateAsync({ query, applicantId, context });
    },

    /**
     * Reset the conversation (client-side only - server is stateless)
     */
    reset: () => {
      askAssistant.reset();
    },
  };
}
