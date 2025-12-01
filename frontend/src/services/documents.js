/**
 * Documents Service
 *
 * API methods for document management: upload URLs, confirmation, analysis.
 */

import { ApiClient, buildQueryString } from './api';

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
   * @returns {Promise<UploadUrlResponse>}
   */
  getUploadUrl(applicantId, documentType, fileName, contentType) {
    const formData = new FormData();
    formData.append('applicant_id', applicantId);
    formData.append('document_type', documentType);
    formData.append('file_name', fileName);
    formData.append('content_type', contentType);

    return this.client.postForm('/documents/upload-url', formData);
  }

  /**
   * Confirm that a document has been uploaded
   * @param {string} documentId - Document ID from getUploadUrl
   * @param {number} fileSize - Size of uploaded file in bytes
   * @returns {Promise<Object>}
   */
  confirmUpload(documentId, fileSize) {
    return this.client.post(`/documents/${documentId}/confirm`, {
      file_size: fileSize,
    });
  }

  /**
   * Direct upload for small files (< 10MB)
   * @param {File} file - File to upload
   * @param {string} applicantId - Applicant ID
   * @param {string} documentType - Document type
   * @returns {Promise<Object>}
   */
  directUpload(file, applicantId, documentType) {
    const formData = new FormData();
    formData.append('file', file);
    formData.append('applicant_id', applicantId);
    formData.append('document_type', documentType);

    return this.client.postForm('/documents/upload', formData);
  }

  /**
   * Get document metadata
   * @param {string} id - Document ID
   * @returns {Promise<Object>}
   */
  get(id) {
    return this.client.get(`/documents/${id}`);
  }

  /**
   * Get a presigned download URL for a document
   * @param {string} id - Document ID
   * @returns {Promise<{download_url: string}>}
   */
  getDownloadUrl(id) {
    return this.client.get(`/documents/${id}/download`);
  }

  /**
   * Delete a document
   * @param {string} id - Document ID
   * @returns {Promise<void>}
   */
  delete(id) {
    return this.client.delete(`/documents/${id}`);
  }

  /**
   * Trigger AI analysis on a document
   * @param {string} id - Document ID
   * @returns {Promise<Object>}
   */
  analyze(id) {
    return this.client.post(`/documents/${id}/analyze`, {});
  }

  /**
   * List documents for an applicant
   * @param {string} applicantId - Applicant ID
   * @param {Object} params - Optional filters
   * @returns {Promise<Array>}
   */
  listByApplicant(applicantId, params = {}) {
    const query = buildQueryString({ ...params, applicant_id: applicantId });
    return this.client.get(`/documents${query}`);
  }
}

/**
 * Upload a file to R2 using a presigned URL
 * Shows progress via callback
 *
 * @param {string} uploadUrl - Presigned upload URL
 * @param {File} file - File to upload
 * @param {Function} [onProgress] - Progress callback (0-100)
 * @returns {Promise<void>}
 */
export async function uploadToPresignedUrl(uploadUrl, file, onProgress = null) {
  return new Promise((resolve, reject) => {
    const xhr = new XMLHttpRequest();

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
        reject(new Error(`Upload failed: ${xhr.status}`));
      }
    };

    xhr.onerror = () => reject(new Error('Upload failed'));
    xhr.onabort = () => reject(new Error('Upload aborted'));

    xhr.open('PUT', uploadUrl);
    xhr.setRequestHeader('Content-Type', file.type);
    xhr.send(file);
  });
}

export default DocumentsService;
