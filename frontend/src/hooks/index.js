/**
 * Hooks module exports
 *
 * Provides React Query hooks for all API operations.
 *
 * Usage:
 *   import { useApplicants, useReviewApplicant } from '../hooks';
 *
 *   function ApplicantsList() {
 *     const { data, isLoading, error } = useApplicants({ status: 'pending' });
 *     const reviewMutation = useReviewApplicant();
 *     ...
 *   }
 */

// Applicant hooks
export {
  applicantKeys,
  useApplicants,
  useApplicant,
  useApplicantTimeline,
  useCreateApplicant,
  useUpdateApplicant,
  useReviewApplicant,
  useCompleteStep,
  useDownloadEvidence,
} from './useApplicants';

// Document hooks
export {
  documentKeys,
  useDocument,
  useApplicantDocuments,
  useUploadDocument,
  useDirectUpload,
  useDeleteDocument,
  useAnalyzeDocument,
  useDocumentDownloadUrl,
  useDownloadDocument,
} from './useDocuments';

// Screening hooks
export {
  screeningKeys,
  useScreeningChecks,
  useScreeningCheck,
  useHitSuggestion,
  useRunScreening,
  useResolveHit,
  useBatchResolveHits,
  useApplicantScreening,
} from './useScreening';

// Case hooks
export {
  caseKeys,
  useCases,
  useCase,
  useMyCases,
  useCreateCase,
  useUpdateCase,
  useResolveCase,
  useAddCaseNote,
  useAssignCase,
  useApplicantCases,
} from './useCases';

// AI hooks
export {
  aiKeys,
  useRiskSummary,
  useRegenerateRiskSummary,
  useAskAssistant,
  useBatchAnalyze,
  useBatchJobStatus,
  useDocumentSuggestions,
  useAssistantConversation,
} from './useAI';
