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
  useExportApplicants,
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

// Dashboard hooks
export {
  dashboardKeys,
  useDashboardStats,
  useScreeningSummary,
  useRecentActivity,
  useRefreshDashboard,
  useDashboardData,
} from './useDashboard';

// Real-time updates hook
export {
  useRealtimeUpdates,
  useGlobalRealtimeUpdates,
} from './useRealtimeUpdates';

// Toast hook
export { useToast } from './useToast';

// Permission hooks
export {
  usePermissions,
  useDisabledForPermission,
  PermissionGate,
  PERMISSIONS,
} from './usePermissions';

// Global search hook
export {
  globalSearchKeys,
  useGlobalSearch,
} from './useGlobalSearch';

// Navigation counts hook
export {
  navigationCountsKeys,
  useNavigationCounts,
  formatBadgeCount,
} from './useNavigationCounts';

// Settings hooks
export {
  settingsKeys,
  useSettings,
  useUpdateGeneralSettings,
  useNotificationPreferences,
  useUpdateNotificationPreferences,
  useSecuritySettings,
  useUpdateSecuritySettings,
  useBrandingSettings,
  useUpdateBrandingSettings,
  useTeamMembers,
  useUpdateTeamMemberRole,
  useRemoveTeamMember,
  useInvitations,
  useInviteTeamMember,
  useCancelInvitation,
  useResendInvitation,
} from './useSettings';

// Audit log hooks
export {
  auditLogKeys,
  useAuditLogs,
  useAuditLogEntry,
  useAuditStats,
  useChainVerification,
  useAuditFilterOptions,
  useExportAuditLogs,
  useVerifyChain,
} from './useAuditLog';

// Analytics hooks
export {
  analyticsKeys,
  useOverview,
  useFunnel,
  useTrends,
  useGeography,
  useRiskDistribution,
  useSlaPerformance,
  useExportAnalytics,
  useAllAnalytics,
} from './useAnalytics';

// Integrations hooks
export {
  integrationsKeys,
  useApiKeys,
  useAvailablePermissions,
  useCreateApiKey,
  useRevokeApiKey,
  useRotateApiKey,
  useWebhooks,
  useAvailableEvents,
  useWebhookLogs,
  useCreateWebhook,
  useUpdateWebhook,
  useDeleteWebhook,
  useTestWebhook,
} from './useIntegrations';

// Companies (KYB) hooks
export {
  companyKeys,
  useCompanies,
  useCompany,
  usePrefetchCompany,
  useCreateCompany,
  useUpdateCompany,
  useDeleteCompany,
  useReviewCompany,
  useScreenCompany,
  useCompanyUBOs,
  useAddUBO,
  useUpdateUBO,
  useDeleteUBO,
  useLinkUBOToApplicant,
  useCompanyDocuments,
  useRequestDocumentUpload,
  useVerifyCompanyDocument,
  useDownloadCompanyDocument,
  useCompanyCounts,
  useSearchCompanies,
} from './useCompanies';

// Device Intelligence hooks
export {
  deviceIntelKeys,
  useDevices,
  useAnalyzeDevice,
  useIPCheck,
  useCheckIP,
  useApplicantDevices,
  useSessionDevice,
  useDeviceStats,
  useDeviceRiskSummary,
  useInvalidateDeviceIntel,
  useHighRiskDeviceCount,
} from './useDeviceIntel';

// Billing hooks
export {
  billingKeys,
  useUsage,
  useUsageHistory,
  useSubscription,
  useUpdateSubscription,
  useCancelSubscription,
  useInvoices,
  useDownloadInvoice,
  usePaymentMethods,
  useCreateSetupIntent,
  useDeletePaymentMethod,
  usePlans,
  useOpenPortal,
  useInvalidateBilling,
} from './useBilling';

// KYC Share hooks
export {
  kycShareKeys,
  useShareTokens,
  useGenerateShareToken,
  useRevokeShareToken,
  useVerifyShareToken,
  useVerifyShareTokenMutation,
  useAccessHistory,
  useAvailablePermissions as useKYCSharePermissions,
} from './useKYCShare';

// Questionnaires hooks
export {
  questionnaireKeys,
  useQuestionnaires,
  useQuestionnaire,
  useQuestionnaireTemplates,
  useCreateQuestionnaire,
  useUpdateQuestionnaire,
  useDeleteQuestionnaire,
  useInitializeDefaults,
  useApplicantResponses,
  useSubmitApplicantResponse,
  useCompanyResponses,
  useSubmitCompanyResponse,
  useUpdateResponse,
  useReviewResponse,
} from './useQuestionnaires';

// Biometrics hooks
export {
  biometricsKeys,
  useBiometricsStatus,
  useCompareFaces,
  useDetectLiveness,
  useDetectFaces,
  useVerifyApplicant,
  useVerifyApplicantWithFile,
} from './useBiometrics';

// Utility hooks
export { useDebounce } from './useDebounce';
export { useClickOutside } from './useClickOutside';
export { useKeyboardShortcut } from './useKeyboardShortcut';
export { useFocusTrap } from './useFocusTrap';
