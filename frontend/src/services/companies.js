/**
 * Companies Service (KYB)
 *
 * API methods for company KYB management: CRUD, beneficial owners, documents, screening.
 * All methods support abort signals for request cancellation.
 */

import { ApiClient, buildQueryString } from './api';

/**
 * @typedef {Object} CompanyFilters
 * @property {string} [status] - Filter by status (pending, in_review, approved, rejected)
 * @property {string} [risk_level] - Filter by risk level (low, medium, high)
 * @property {string} [search] - Search by name or registration number
 * @property {string} [incorporation_country] - Filter by country (ISO 3166-1 alpha-2)
 * @property {boolean} [has_flags] - Filter by companies with screening flags
 * @property {number} [limit] - Number of results per page
 * @property {number} [offset] - Pagination offset
 * @property {string} [sort_by] - Sort field
 * @property {string} [sort_order] - Sort order (asc/desc)
 */

/**
 * @typedef {Object} CompanyCreate
 * @property {string} legal_name - Legal company name
 * @property {string} [trading_name] - Trading/DBA name
 * @property {string} [registration_number] - Company registration number
 * @property {string} [tax_id] - Tax identification number
 * @property {string} [incorporation_date] - Date of incorporation
 * @property {string} [incorporation_country] - Country code (ISO 3166-1 alpha-2)
 * @property {string} [legal_form] - Legal form (LLC, Corp, etc.)
 * @property {Object} [registered_address] - Registered address
 * @property {Object} [business_address] - Business address
 * @property {string} [website] - Company website
 * @property {string} [email] - Contact email
 * @property {string} [phone] - Contact phone
 * @property {string} [industry] - Industry classification
 * @property {string} [external_id] - External reference ID
 */

/**
 * @typedef {Object} BeneficialOwnerCreate
 * @property {string} full_name - Full name of UBO
 * @property {string} [date_of_birth] - Date of birth
 * @property {string} [nationality] - Nationality (ISO 3166-1 alpha-2)
 * @property {number} [ownership_percentage] - Ownership percentage
 * @property {string} [ownership_type] - direct/indirect/control
 * @property {boolean} [is_director] - Is company director
 * @property {boolean} [is_shareholder] - Is shareholder
 * @property {string} [role_title] - Role/title in company
 */

export class CompaniesService {
  /**
   * @param {Function} getToken - Async function that returns the auth token
   */
  constructor(getToken) {
    this.client = new ApiClient(getToken);
  }

  // ===========================================
  // COMPANY CRUD
  // ===========================================

  /**
   * List companies with optional filters and pagination
   * @param {CompanyFilters} params
   * @param {Object} [options] - Request options (signal, timeout)
   * @returns {Promise<{items: Array, total: number, limit: number, offset: number}>}
   */
  list(params = {}, options = {}) {
    const query = buildQueryString(params);
    return this.client.get(`/companies${query}`, options);
  }

  /**
   * Get a single company by ID with UBOs and documents
   * @param {string} id - Company ID
   * @param {Object} [options] - Request options
   * @returns {Promise<Object>}
   */
  get(id, options = {}) {
    return this.client.get(`/companies/${id}`, options);
  }

  /**
   * Create a new company
   * @param {CompanyCreate} data
   * @param {Object} [options] - Request options
   * @returns {Promise<Object>}
   */
  create(data, options = {}) {
    return this.client.post('/companies', data, options);
  }

  /**
   * Update a company
   * @param {string} id - Company ID
   * @param {Object} data - Fields to update
   * @param {Object} [options] - Request options
   * @returns {Promise<Object>}
   */
  update(id, data, options = {}) {
    return this.client.patch(`/companies/${id}`, data, options);
  }

  /**
   * Delete a company
   * @param {string} id - Company ID
   * @param {Object} [options] - Request options
   * @returns {Promise<void>}
   */
  delete(id, options = {}) {
    return this.client.delete(`/companies/${id}`, options);
  }

  /**
   * Review a company (approve/reject)
   * @param {string} id - Company ID
   * @param {'approved'|'rejected'} decision
   * @param {string} [notes] - Review notes
   * @param {number} [riskOverride] - Override risk score
   * @param {Object} [options] - Request options
   * @returns {Promise<Object>}
   */
  review(id, decision, notes = null, riskOverride = null, options = {}) {
    const body = { decision };
    if (notes) body.notes = notes;
    if (riskOverride !== null) body.risk_score_override = riskOverride;
    return this.client.post(`/companies/${id}/review`, body, options);
  }

  /**
   * Run screening on company and all UBOs
   * @param {string} id - Company ID
   * @param {Object} [options] - Request options
   * @returns {Promise<Object>} Screening result
   */
  screen(id, options = {}) {
    return this.client.post(`/companies/${id}/screen`, {}, options);
  }

  // ===========================================
  // BENEFICIAL OWNERS
  // ===========================================

  /**
   * List beneficial owners for a company
   * @param {string} companyId - Company ID
   * @param {Object} [options] - Request options
   * @returns {Promise<Array>}
   */
  listUBOs(companyId, options = {}) {
    return this.client.get(`/companies/${companyId}/beneficial-owners`, options);
  }

  /**
   * Add a beneficial owner to a company
   * @param {string} companyId - Company ID
   * @param {BeneficialOwnerCreate} data - UBO data
   * @param {Object} [options] - Request options
   * @returns {Promise<Object>}
   */
  addUBO(companyId, data, options = {}) {
    return this.client.post(`/companies/${companyId}/beneficial-owners`, data, options);
  }

  /**
   * Update a beneficial owner
   * @param {string} companyId - Company ID
   * @param {string} uboId - UBO ID
   * @param {Object} data - Fields to update
   * @param {Object} [options] - Request options
   * @returns {Promise<Object>}
   */
  updateUBO(companyId, uboId, data, options = {}) {
    return this.client.patch(`/companies/${companyId}/beneficial-owners/${uboId}`, data, options);
  }

  /**
   * Remove a beneficial owner
   * @param {string} companyId - Company ID
   * @param {string} uboId - UBO ID
   * @param {Object} [options] - Request options
   * @returns {Promise<void>}
   */
  deleteUBO(companyId, uboId, options = {}) {
    return this.client.delete(`/companies/${companyId}/beneficial-owners/${uboId}`, options);
  }

  /**
   * Link a UBO to an existing applicant (for KYC verification)
   * @param {string} companyId - Company ID
   * @param {string} uboId - UBO ID
   * @param {string} applicantId - Applicant ID to link
   * @param {Object} [options] - Request options
   * @returns {Promise<Object>}
   */
  linkUBOToApplicant(companyId, uboId, applicantId, options = {}) {
    return this.client.post(
      `/companies/${companyId}/beneficial-owners/${uboId}/link`,
      { applicant_id: applicantId },
      options
    );
  }

  // ===========================================
  // COMPANY DOCUMENTS
  // ===========================================

  /**
   * List documents for a company
   * @param {string} companyId - Company ID
   * @param {Object} [options] - Request options
   * @returns {Promise<Array>}
   */
  listDocuments(companyId, options = {}) {
    return this.client.get(`/companies/${companyId}/documents`, options);
  }

  /**
   * Request presigned URL for document upload
   * @param {string} companyId - Company ID
   * @param {Object} data - Document metadata
   * @param {Object} [options] - Request options
   * @returns {Promise<{document_id: string, upload_url: string, storage_key: string}>}
   */
  requestDocumentUpload(companyId, data, options = {}) {
    return this.client.post(`/companies/${companyId}/documents/upload`, data, options);
  }

  /**
   * Verify or reject a document
   * @param {string} companyId - Company ID
   * @param {string} documentId - Document ID
   * @param {'verified'|'rejected'} decision
   * @param {string} [notes] - Verification notes
   * @param {Object} [options] - Request options
   * @returns {Promise<Object>}
   */
  verifyDocument(companyId, documentId, decision, notes = null, options = {}) {
    const body = { decision };
    if (notes) body.notes = notes;
    return this.client.post(
      `/companies/${companyId}/documents/${documentId}/verify`,
      body,
      options
    );
  }

  /**
   * Get download URL for a document
   * @param {string} companyId - Company ID
   * @param {string} documentId - Document ID
   * @param {Object} [options] - Request options
   * @returns {Promise<{download_url: string, file_name: string, file_type: string}>}
   */
  getDocumentDownloadUrl(companyId, documentId, options = {}) {
    return this.client.get(
      `/companies/${companyId}/documents/${documentId}/download`,
      options
    );
  }
}

export default CompaniesService;
