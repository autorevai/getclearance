/**
 * Hooks module exports
 *
 * Production-grade React Query hooks for all API operations.
 * Features:
 * - Optimistic updates for instant UI feedback
 * - Request deduplication and caching
 * - Automatic retry with exponential backoff
 * - Abort signal support for cleanup
 * - Infinite scroll support
 * - Prefetching for predictive loading
 */

// Applicant hooks
export {
  applicantKeys,
  useApplicants,
  useInfiniteApplicants,
  useApplicant,
  usePrefetchApplicant,
  useApplicantTimeline,
  useCreateApplicant,
  useUpdateApplicant,
  useReviewApplicant,
  useBatchReviewApplicants,
  useCompleteStep,
  useDownloadEvidence,
  useApplicantCounts,
  useSearchApplicants,
} from './useApplicants';

// Document hooks
export {
  documentKeys,
  useDocument,
  useApplicantDocuments,
  useDocumentPolling,
  useUploadDocument,
  useDirectUpload,
  useDeleteDocument,
  useAnalyzeDocument,
  useDocumentDownloadUrl,
  useDownloadDocument,
  useBatchUpload,
} from './useDocuments';

// Screening hooks
export {
  screeningKeys,
  useScreeningChecks,
  useScreeningCheck,
  useScreeningCheckPolling,
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
  useInfiniteCases,
  useCase,
  useMyCases,
  useCreateCase,
  useUpdateCase,
  useResolveCase,
  useAddCaseNote,
  useAssignCase,
  useApplicantCases,
  useCaseCounts,
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
  usePrefetchRiskSummary,
} from './useAI';
