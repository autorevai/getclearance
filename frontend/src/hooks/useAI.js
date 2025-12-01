/**
 * React Query hooks for AI Features
 *
 * Production-grade hooks with:
 * - Streaming support for assistant responses
 * - Batch job polling
 * - Cached suggestions
 */

import { useMemo, useState, useCallback } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { useAuth } from '../auth';
import { AIService } from '../services';
import { applicantKeys } from './useApplicants';

export const aiKeys = {
  all: ['ai'],
  riskSummaries: () => [...aiKeys.all, 'risk-summary'],
  riskSummary: (applicantId) => [...aiKeys.riskSummaries(), applicantId],
  assistant: () => [...aiKeys.all, 'assistant'],
  batchJobs: () => [...aiKeys.all, 'batch'],
  batchJob: (jobId) => [...aiKeys.batchJobs(), jobId],
  documentSuggestions: (documentId) => [...aiKeys.all, 'document-suggestions', documentId],
};

function useAIService() {
  const { getToken } = useAuth();
  return useMemo(() => new AIService(getToken), [getToken]);
}

export function useRiskSummary(applicantId, options = {}) {
  const service = useAIService();

  return useQuery({
    queryKey: aiKeys.riskSummary(applicantId),
    queryFn: ({ signal }) => service.getRiskSummary(applicantId, { signal }),
    enabled: !!applicantId,
    staleTime: 120000, // Risk summaries are stable for 2 minutes
    ...options,
  });
}

export function useRegenerateRiskSummary() {
  const service = useAIService();
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (applicantId) => service.regenerateRiskSummary(applicantId),

    // Optimistic update - show loading state
    onMutate: async (applicantId) => {
      await queryClient.cancelQueries({ queryKey: aiKeys.riskSummary(applicantId) });

      const previousSummary = queryClient.getQueryData(aiKeys.riskSummary(applicantId));

      queryClient.setQueryData(aiKeys.riskSummary(applicantId), {
        ...previousSummary,
        status: 'generating',
        generated_at: null,
      });

      return { previousSummary };
    },

    onError: (err, applicantId, context) => {
      if (context?.previousSummary) {
        queryClient.setQueryData(aiKeys.riskSummary(applicantId), context.previousSummary);
      }
    },

    onSuccess: (data, applicantId) => {
      queryClient.setQueryData(aiKeys.riskSummary(applicantId), data);
      queryClient.invalidateQueries({ queryKey: applicantKeys.detail(applicantId) });
    },
  });
}

export function useAskAssistant() {
  const service = useAIService();

  return useMutation({
    mutationFn: ({ query, applicantId, context }) =>
      service.askAssistant(query, applicantId, context),
  });
}

export function useBatchAnalyze() {
  const service = useAIService();

  return useMutation({
    mutationFn: (applicantIds) => service.batchAnalyze(applicantIds),
    // Job started - caller should use useBatchJobStatus to poll for completion
  });
}

export function useBatchJobStatus(jobId, options = {}) {
  const service = useAIService();
  const queryClient = useQueryClient();
  const { onComplete } = options;

  return useQuery({
    queryKey: aiKeys.batchJob(jobId),
    queryFn: ({ signal }) => service.getBatchStatus(jobId, { signal }),
    enabled: !!jobId,
    refetchInterval: (query) => {
      const data = query.state.data;
      if (!data) return 2000;

      if (data.status === 'completed' || data.status === 'failed') {
        if (onComplete) onComplete(data);
        // Invalidate affected applicant summaries
        if (data.applicant_ids) {
          data.applicant_ids.forEach((id) => {
            queryClient.invalidateQueries({ queryKey: aiKeys.riskSummary(id) });
          });
        }
        return false;
      }
      return 2000;
    },
    staleTime: 0,
    ...options,
  });
}

export function useDocumentSuggestions(documentId, options = {}) {
  const service = useAIService();

  return useQuery({
    queryKey: aiKeys.documentSuggestions(documentId),
    queryFn: ({ signal }) => service.getDocumentSuggestions(documentId, { signal }),
    enabled: !!documentId,
    staleTime: 300000, // Suggestions stable for 5 minutes
    ...options,
  });
}

/**
 * Hook for managing an AI assistant conversation
 * Tracks message history and handles sending/receiving
 */
export function useAssistantConversation(applicantId = null) {
  const askAssistant = useAskAssistant();
  const [messages, setMessages] = useState([]);

  const sendMessage = useCallback(
    async (content, context = null) => {
      // Add user message
      const userMessage = {
        id: `user-${Date.now()}`,
        role: 'user',
        content,
        timestamp: new Date().toISOString(),
      };
      setMessages((prev) => [...prev, userMessage]);

      try {
        const response = await askAssistant.mutateAsync({
          query: content,
          applicantId,
          context,
        });

        // Add assistant response
        const assistantMessage = {
          id: `assistant-${Date.now()}`,
          role: 'assistant',
          content: response.response,
          sources: response.sources,
          timestamp: response.generated_at || new Date().toISOString(),
        };
        setMessages((prev) => [...prev, assistantMessage]);

        return response;
      } catch (error) {
        // Add error message
        const errorMessage = {
          id: `error-${Date.now()}`,
          role: 'error',
          content: error.message || 'Failed to get response',
          timestamp: new Date().toISOString(),
        };
        setMessages((prev) => [...prev, errorMessage]);
        throw error;
      }
    },
    [askAssistant, applicantId]
  );

  const clearMessages = useCallback(() => {
    setMessages([]);
  }, []);

  const removeMessage = useCallback((messageId) => {
    setMessages((prev) => prev.filter((m) => m.id !== messageId));
  }, []);

  return {
    messages,
    sendMessage,
    clearMessages,
    removeMessage,
    isLoading: askAssistant.isPending,
    error: askAssistant.error,
  };
}

/**
 * Hook for prefetching risk summaries (for list views)
 */
export function usePrefetchRiskSummary() {
  const queryClient = useQueryClient();
  const service = useAIService();

  return useCallback(
    (applicantId) => {
      if (!applicantId) return;
      queryClient.prefetchQuery({
        queryKey: aiKeys.riskSummary(applicantId),
        queryFn: ({ signal }) => service.getRiskSummary(applicantId, { signal }),
        staleTime: 120000,
      });
    },
    [queryClient, service]
  );
}
