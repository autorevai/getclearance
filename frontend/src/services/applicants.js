/**
 * Applicants Service
 *
 * API methods for applicant management: CRUD, review, timeline, evidence.
 * All methods support abort signals for request cancellation.
 */

import { ApiClient, buildQueryString } from './api';

/**
 * @typedef {Object} ApplicantFilters
 * @property {string} [status] - Filter by status (pending, approved, rejected, etc.)
 * @property {string} [risk_level] - Filter by risk level (low, medium, high)
 * @property {string} [search] - Search by name or email
 * @property {number} [limit] - Number of results per page
 * @property {number} [offset] - Pagination offset
 */

/**
 * @typedef {Object} ApplicantCreate
 * @property {string} external_id - External identifier
 * @property {string} email - Email address
 * @property {string} [first_name] - First name
 * @property {string} [last_name] - Last name
 * @property {string} [phone] - Phone number
 * @property {Object} [metadata] - Additional metadata
 */

/**
 * @typedef {Object} ReviewDecision
 * @property {'approve'|'reject'|'request_info'} decision - Review decision
 * @property {string} [notes] - Review notes
 * @property {number} [risk_score_override] - Override risk score (0-100)
 */

export class ApplicantsService {
  /**
   * @param {Function} getToken - Async function that returns the auth token
   */
  constructor(getToken) {
    this.client = new ApiClient(getToken);
  }

  /**
   * List applicants with optional filters and pagination
   * @param {ApplicantFilters} params
   * @param {Object} [options] - Request options (signal, timeout)
   * @returns {Promise<{items: Array, total: number, limit: number, offset: number}>}
   */
  list(params = {}, options = {}) {
    const query = buildQueryString(params);
    return this.client.get(`/applicants${query}`, options);
  }

  /**
   * Get a single applicant by ID
   * @param {string} id - Applicant ID
   * @param {Object} [options] - Request options
   * @returns {Promise<Object>}
   */
  get(id, options = {}) {
    return this.client.get(`/applicants/${id}`, options);
  }

  /**
   * Create a new applicant
   * @param {ApplicantCreate} data
   * @param {Object} [options] - Request options
   * @returns {Promise<Object>}
   */
  create(data, options = {}) {
    return this.client.post('/applicants', data, options);
  }

  /**
   * Update an applicant
   * @param {string} id - Applicant ID
   * @param {Object} data - Fields to update
   * @param {Object} [options] - Request options
   * @returns {Promise<Object>}
   */
  update(id, data, options = {}) {
    return this.client.patch(`/applicants/${id}`, data, options);
  }

  /**
   * Review an applicant (approve/reject)
   * @param {string} id - Applicant ID
   * @param {'approve'|'reject'|'request_info'} decision
   * @param {string} [notes] - Review notes
   * @param {number} [riskOverride] - Override risk score
   * @param {Object} [options] - Request options
   * @returns {Promise<Object>}
   */
  review(id, decision, notes = null, riskOverride = null, options = {}) {
    const body = { decision };
    if (notes) body.notes = notes;
    if (riskOverride !== null) body.risk_score_override = riskOverride;
    return this.client.post(`/applicants/${id}/review`, body, options);
  }

  /**
   * Complete a verification step
   * @param {string} id - Applicant ID
   * @param {string} step - Step name (e.g., 'identity', 'documents', 'screening')
   * @param {Object} [options] - Request options
   * @returns {Promise<Object>}
   */
  completeStep(id, step, options = {}) {
    return this.client.post(`/applicants/${id}/steps/${step}/complete`, {}, options);
  }

  /**
   * Get applicant timeline/audit log
   * @param {string} id - Applicant ID
   * @param {Object} [options] - Request options
   * @returns {Promise<Array>}
   */
  getTimeline(id, options = {}) {
    return this.client.get(`/applicants/${id}/timeline`, options);
  }

  /**
   * Download evidence pack (PDF) for an applicant
   * @param {string} id - Applicant ID
   * @param {Object} [options] - Request options
   * @returns {Promise<Blob>}
   */
  downloadEvidence(id, options = {}) {
    return this.client.requestBlob(`/applicants/${id}/evidence`, options);
  }

  /**
   * Get evidence preview (lighter version)
   * @param {string} id - Applicant ID
   * @param {Object} [options] - Request options
   * @returns {Promise<Object>}
   */
  getEvidencePreview(id, options = {}) {
    return this.client.get(`/applicants/${id}/evidence/preview`, options);
  }

  /**
   * Export applicants to CSV
   * @param {Object} filters - Filter parameters (status, risk_level, search, ids)
   * @param {Object} [options] - Request options
   * @returns {Promise<string>} CSV content
   */
  exportCSV(filters = {}, options = {}) {
    const query = buildQueryString({ ...filters, format: 'csv' });
    return this.client.requestText(`/applicants/export${query}`, options);
  }
}

export default ApplicantsService;
