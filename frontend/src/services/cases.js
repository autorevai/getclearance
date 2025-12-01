/**
 * Cases Service
 *
 * API methods for case management: CRUD, notes, resolution.
 */

import { ApiClient, buildQueryString } from './api';

/**
 * @typedef {Object} CaseFilters
 * @property {string} [status] - Filter by status (open, in_progress, resolved, escalated)
 * @property {string} [priority] - Filter by priority (low, medium, high, critical)
 * @property {string} [assigned_to] - Filter by assignee
 * @property {string} [applicant_id] - Filter by applicant
 * @property {string} [search] - Search in case title/description
 * @property {number} [limit] - Results per page
 * @property {number} [offset] - Pagination offset
 */

/**
 * @typedef {Object} CaseCreate
 * @property {string} title - Case title
 * @property {string} [description] - Case description
 * @property {string} applicant_id - Related applicant
 * @property {'low'|'medium'|'high'|'critical'} [priority] - Priority level
 * @property {string} [case_type] - Type of case
 */

/**
 * @typedef {Object} CaseResolution
 * @property {'approved'|'rejected'|'escalated'|'closed'} resolution
 * @property {string} [notes] - Resolution notes
 */

export class CasesService {
  /**
   * @param {Function} getToken - Async function that returns the auth token
   */
  constructor(getToken) {
    this.client = new ApiClient(getToken);
  }

  /**
   * List cases with optional filters
   * @param {CaseFilters} params
   * @returns {Promise<{items: Array, total: number}>}
   */
  list(params = {}) {
    const query = buildQueryString(params);
    return this.client.get(`/cases${query}`);
  }

  /**
   * Get a single case with all notes
   * @param {string} id - Case ID
   * @returns {Promise<Object>}
   */
  get(id) {
    return this.client.get(`/cases/${id}`);
  }

  /**
   * Create a new case
   * @param {CaseCreate} data
   * @returns {Promise<Object>}
   */
  create(data) {
    return this.client.post('/cases', data);
  }

  /**
   * Update a case
   * @param {string} id - Case ID
   * @param {Object} data - Fields to update
   * @returns {Promise<Object>}
   */
  update(id, data) {
    return this.client.patch(`/cases/${id}`, data);
  }

  /**
   * Resolve a case
   * @param {string} id - Case ID
   * @param {'approved'|'rejected'|'escalated'|'closed'} resolution
   * @param {string} [notes] - Resolution notes
   * @returns {Promise<Object>}
   */
  resolve(id, resolution, notes = null) {
    const body = { resolution };
    if (notes) body.notes = notes;
    return this.client.post(`/cases/${id}/resolve`, body);
  }

  /**
   * Add a note to a case
   * @param {string} id - Case ID
   * @param {string} content - Note content
   * @returns {Promise<Object>}
   */
  addNote(id, content) {
    return this.client.post(`/cases/${id}/notes`, { content });
  }

  /**
   * Assign a case to a user
   * @param {string} id - Case ID
   * @param {string} userId - User ID to assign to
   * @returns {Promise<Object>}
   */
  assign(id, userId) {
    return this.client.patch(`/cases/${id}`, { assigned_to: userId });
  }

  /**
   * Get cases assigned to the current user
   * @param {Object} params - Optional filters
   * @returns {Promise<{items: Array, total: number}>}
   */
  getMyCases(params = {}) {
    const query = buildQueryString({ ...params, assigned_to: 'me' });
    return this.client.get(`/cases${query}`);
  }
}

export default CasesService;
