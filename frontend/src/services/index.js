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
