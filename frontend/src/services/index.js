/**
 * Services module exports
 *
 * Production-grade API services with:
 * - Automatic retry with exponential backoff
 * - Request timeout and abort handling
 * - Request deduplication for GET requests
 * - Offline detection
 * - Request/response interceptors
 * - Comprehensive error handling
 */

export {
  ApiClient,
  ApiError,
  buildQueryString,
  isOnline,
  getSharedClient,
  resetSharedClient,
} from './api';

export { ApplicantsService } from './applicants';
export { DocumentsService, uploadToPresignedUrl, uploadDocumentFlow } from './documents';
export { ScreeningService } from './screening';
export { CasesService } from './cases';
export { AIService } from './ai';
export { DashboardService } from './dashboard';
export { SettingsService } from './settings';
export { AuditService } from './audit';
export { AnalyticsService } from './analytics';
export { IntegrationsService } from './integrations';
export { CompaniesService } from './companies';
export { DeviceIntelService } from './deviceIntel';
export { QuestionnairesService } from './questionnaires';
export { BiometricsService } from './biometrics';
