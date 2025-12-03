/**
 * Questionnaires Hooks
 *
 * React Query hooks for questionnaire operations.
 */

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { QuestionnairesService } from '../services/questionnaires';

export const questionnaireKeys = {
  all: ['questionnaires'],
  lists: () => [...questionnaireKeys.all, 'list'],
  list: (filters) => [...questionnaireKeys.lists(), filters],
  details: () => [...questionnaireKeys.all, 'detail'],
  detail: (id) => [...questionnaireKeys.details(), id],
  templates: () => [...questionnaireKeys.all, 'templates'],
  responses: () => [...questionnaireKeys.all, 'responses'],
  applicantResponses: (applicantId) => [...questionnaireKeys.responses(), 'applicant', applicantId],
  companyResponses: (companyId) => [...questionnaireKeys.responses(), 'company', companyId],
};

// List questionnaires
export function useQuestionnaires(params = {}) {
  return useQuery({
    queryKey: questionnaireKeys.list(params),
    queryFn: () => QuestionnairesService.list(params),
  });
}

// Get single questionnaire
export function useQuestionnaire(id, options = {}) {
  return useQuery({
    queryKey: questionnaireKeys.detail(id),
    queryFn: () => QuestionnairesService.get(id),
    enabled: !!id,
    ...options,
  });
}

// Get templates
export function useQuestionnaireTemplates() {
  return useQuery({
    queryKey: questionnaireKeys.templates(),
    queryFn: () => QuestionnairesService.getTemplates(),
    staleTime: 1000 * 60 * 60, // Templates don't change often
  });
}

// Create questionnaire
export function useCreateQuestionnaire() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (data) => QuestionnairesService.create(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: questionnaireKeys.lists() });
    },
  });
}

// Update questionnaire
export function useUpdateQuestionnaire() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ id, data }) => QuestionnairesService.update(id, data),
    onSuccess: (_, { id }) => {
      queryClient.invalidateQueries({ queryKey: questionnaireKeys.detail(id) });
      queryClient.invalidateQueries({ queryKey: questionnaireKeys.lists() });
    },
  });
}

// Delete questionnaire
export function useDeleteQuestionnaire() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (id) => QuestionnairesService.delete(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: questionnaireKeys.lists() });
    },
  });
}

// Initialize default questionnaires
export function useInitializeDefaults() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: () => QuestionnairesService.initializeDefaults(),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: questionnaireKeys.lists() });
    },
  });
}

// Get applicant responses
export function useApplicantResponses(applicantId) {
  return useQuery({
    queryKey: questionnaireKeys.applicantResponses(applicantId),
    queryFn: () => QuestionnairesService.getApplicantResponses(applicantId),
    enabled: !!applicantId,
  });
}

// Submit applicant response
export function useSubmitApplicantResponse() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ applicantId, data }) =>
      QuestionnairesService.submitApplicantResponse(applicantId, data),
    onSuccess: (_, { applicantId }) => {
      queryClient.invalidateQueries({
        queryKey: questionnaireKeys.applicantResponses(applicantId)
      });
    },
  });
}

// Get company responses
export function useCompanyResponses(companyId) {
  return useQuery({
    queryKey: questionnaireKeys.companyResponses(companyId),
    queryFn: () => QuestionnairesService.getCompanyResponses(companyId),
    enabled: !!companyId,
  });
}

// Submit company response
export function useSubmitCompanyResponse() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ companyId, data }) =>
      QuestionnairesService.submitCompanyResponse(companyId, data),
    onSuccess: (_, { companyId }) => {
      queryClient.invalidateQueries({
        queryKey: questionnaireKeys.companyResponses(companyId)
      });
    },
  });
}

// Update response
export function useUpdateResponse() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ responseId, data }) =>
      QuestionnairesService.updateResponse(responseId, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: questionnaireKeys.responses() });
    },
  });
}

// Review response
export function useReviewResponse() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ responseId, status, reviewNotes }) =>
      QuestionnairesService.reviewResponse(responseId, status, reviewNotes),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: questionnaireKeys.responses() });
    },
  });
}
