/**
 * Documents Service
 *
 * API methods for document management: upload URLs, confirmation, analysis.
 * Includes robust upload handling with progress tracking and retry logic.
 */

import { ApiClient, buildQueryString, ApiError, isOnline } from './api';

/**
 * @typedef {Object} UploadUrlRequest
 * @property {string} applicant_id - Applicant ID
 * @property {string} document_type - Type of document (passport, driver_license, utility_bill, etc.)
 * @property {string} file_name - Original file name
 * @property {string} content_type - MIME type (image/jpeg, application/pdf, etc.)
 */

/**
 * @typedef {Object} UploadUrlResponse
 * @property {string} upload_url - Presigned URL for direct upload to R2
 * @property {string} document_id - Document ID to use for confirmation
 * @property {string} key - Storage key
 */

// Upload retry configuration
const UPLOAD_MAX_RETRIES = 3;
const UPLOAD_RETRY_DELAY = 1000;

export class DocumentsService {
  /**
   * @param {Function} getToken - Async function that returns the auth token
   */
  constructor(getToken) {
    this.client = new ApiClient(getToken);
  }

  /**
   * Get a presigned URL for uploading a document
   * @param {string} applicantId - Applicant ID
   * @param {string} documentType - Document type
   * @param {string} fileName - Original file name
   * @param {string} contentType - MIME type
   * @param {Object} [options] - Request options
   * @returns {Promise<UploadUrlResponse>}
   */
  getUploadUrl(applicantId, documentType, fileName, contentType, options = {}) {
    const formData = new FormData();
    formData.append('applicant_id', applicantId);
    formData.append('document_type', documentType);
    formData.append('file_name', fileName);
    formData.append('content_type', contentType);

    return this.client.postForm('/documents/upload-url', formData, options);
  }

  /**
   * Confirm that a document has been uploaded
   * @param {string} documentId - Document ID from getUploadUrl
   * @param {number} fileSize - Size of uploaded file in bytes
   * @param {Object} [options] - Request options
   * @returns {Promise<Object>}
   */
  confirmUpload(documentId, fileSize, options = {}) {
    return this.client.post(`/documents/${documentId}/confirm`, {
      file_size: fileSize,
    }, options);
  }

  /**
   * Direct upload for small files (< 10MB)
   * @param {File} file - File to upload
   * @param {string} applicantId - Applicant ID
   * @param {string} documentType - Document type
   * @param {Object} [options] - Request options
   * @returns {Promise<Object>}
   */
  directUpload(file, applicantId, documentType, options = {}) {
    const formData = new FormData();
    formData.append('file', file);
    formData.append('applicant_id', applicantId);
    formData.append('document_type', documentType);

    return this.client.postForm('/documents/upload', formData, options);
  }

  /**
   * Get document metadata
   * @param {string} id - Document ID
   * @param {Object} [options] - Request options
   * @returns {Promise<Object>}
   */
  get(id, options = {}) {
    return this.client.get(`/documents/${id}`, options);
  }

  /**
   * Get a presigned download URL for a document
   * @param {string} id - Document ID
   * @param {Object} [options] - Request options
   * @returns {Promise<{download_url: string}>}
   */
  getDownloadUrl(id, options = {}) {
    return this.client.get(`/documents/${id}/download`, options);
  }

  /**
   * Delete a document
   * @param {string} id - Document ID
   * @param {Object} [options] - Request options
   * @returns {Promise<void>}
   */
  delete(id, options = {}) {
    return this.client.delete(`/documents/${id}`, options);
  }

  /**
   * Trigger AI analysis on a document
   * @param {string} id - Document ID
   * @param {Object} [options] - Request options
   * @returns {Promise<Object>}
   */
  analyze(id, options = {}) {
    return this.client.post(`/documents/${id}/analyze`, {}, options);
  }

  /**
   * List documents for an applicant
   * @param {string} applicantId - Applicant ID
   * @param {Object} params - Optional filters
   * @param {Object} [options] - Request options
   * @returns {Promise<Array>}
   */
  listByApplicant(applicantId, params = {}, options = {}) {
    const query = buildQueryString({ ...params, applicant_id: applicantId });
    return this.client.get(`/documents${query}`, options);
  }
}

/**
 * Upload a file to R2 using a presigned URL
 * Features:
 * - Progress tracking
 * - Automatic retry on failure
 * - Abort support
 * - Offline detection
 *
 * @param {string} uploadUrl - Presigned upload URL
 * @param {File} file - File to upload
 * @param {Object} options - Upload options
 * @param {Function} [options.onProgress] - Progress callback (0-100)
 * @param {AbortSignal} [options.signal] - AbortController signal
 * @param {number} [options.maxRetries] - Max retry attempts
 * @returns {Promise<void>}
 */
export async function uploadToPresignedUrl(uploadUrl, file, options = {}) {
  const {
    onProgress = null,
    signal = null,
    maxRetries = UPLOAD_MAX_RETRIES,
  } = options;

  if (!isOnline()) {
    throw new ApiError('No internet connection', 0);
  }

  let lastError = null;

  for (let attempt = 1; attempt <= maxRetries; attempt++) {
    try {
      await new Promise((resolve, reject) => {
        const xhr = new XMLHttpRequest();

        // Handle abort signal
        if (signal) {
          if (signal.aborted) {
            reject(new ApiError('Upload cancelled', 0));
            return;
          }
          signal.addEventListener('abort', () => {
            xhr.abort();
            reject(new ApiError('Upload cancelled', 0));
          });
        }

        // Progress tracking
        if (onProgress) {
          xhr.upload.onprogress = (e) => {
            if (e.lengthComputable) {
              const percent = Math.round((e.loaded / e.total) * 100);
              onProgress(percent);
            }
          };
        }

        xhr.onload = () => {
          if (xhr.status >= 200 && xhr.status < 300) {
            resolve();
          } else {
            reject(new ApiError(`Upload failed: ${xhr.status}`, xhr.status));
          }
        };

        xhr.onerror = () => {
          reject(new ApiError('Network error during upload', 0));
        };

        xhr.ontimeout = () => {
          reject(new ApiError('Upload timed out', 0));
        };

        xhr.onabort = () => {
          reject(new ApiError('Upload cancelled', 0));
        };

        xhr.open('PUT', uploadUrl);
        xhr.setRequestHeader('Content-Type', file.type);
        xhr.timeout = 300000; // 5 minute timeout for large files
        xhr.send(file);
      });

      // Success - exit retry loop
      return;

    } catch (error) {
      lastError = error;

      // Don't retry on abort or client errors
      if (error.message === 'Upload cancelled' || (error.status >= 400 && error.status < 500)) {
        throw error;
      }

      // Retry on network/server errors
      if (attempt < maxRetries) {
        // Reset progress for retry
        if (onProgress) onProgress(0);

        // Exponential backoff
        await new Promise(r => setTimeout(r, UPLOAD_RETRY_DELAY * Math.pow(2, attempt - 1)));
      }
    }
  }

  throw lastError || new ApiError('Upload failed after retries', 0);
}

/**
 * Complete document upload flow with progress tracking
 * Handles: get URL -> upload to R2 -> confirm -> optional analysis
 *
 * @param {DocumentsService} service - Documents service instance
 * @param {Object} params - Upload parameters
 * @param {File} params.file - File to upload
 * @param {string} params.applicantId - Applicant ID
 * @param {string} params.documentType - Document type
 * @param {Object} [options] - Upload options
 * @param {Function} [options.onProgress] - Progress callback (0-100)
 * @param {Function} [options.onStage] - Stage callback ('preparing' | 'uploading' | 'confirming' | 'analyzing')
 * @param {AbortSignal} [options.signal] - AbortController signal
 * @param {boolean} [options.analyze] - Run AI analysis after upload
 * @returns {Promise<Object>} - Confirmed document
 */
export async function uploadDocumentFlow(service, params, options = {}) {
  const { file, applicantId, documentType } = params;
  const { onProgress, onStage, signal, analyze = false } = options;

  // Stage 1: Get presigned URL
  if (onStage) onStage('preparing');
  const { upload_url, document_id } = await service.getUploadUrl(
    applicantId,
    documentType,
    file.name,
    file.type,
    { signal }
  );

  // Stage 2: Upload to R2
  if (onStage) onStage('uploading');
  await uploadToPresignedUrl(upload_url, file, { onProgress, signal });

  // Stage 3: Confirm upload
  if (onStage) onStage('confirming');
  const document = await service.confirmUpload(document_id, file.size, { signal });

  // Stage 4: Optional analysis
  if (analyze) {
    if (onStage) onStage('analyzing');
    await service.analyze(document_id, { signal });
  }

  return document;
}

export default DocumentsService;
