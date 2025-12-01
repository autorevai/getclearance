/**
 * Screening Service
 *
 * API methods for AML/KYC screening: checks, hits, resolutions.
 */

import { ApiClient, buildQueryString } from './api';

/**
 * @typedef {Object} ScreeningCheckRequest
 * @property {string} applicant_id - Applicant ID
 * @property {string} [check_type] - Type of check (sanctions, pep, adverse_media, etc.)
 * @property {Object} [search_params] - Additional search parameters
 */

/**
 * @typedef {Object} ScreeningFilters
 * @property {string} [applicant_id] - Filter by applicant
 * @property {string} [status] - Filter by status (pending, completed, failed)
 * @property {number} [limit] - Results per page
 * @property {number} [offset] - Pagination offset
 */

/**
 * @typedef {Object} HitResolution
 * @property {'true_positive'|'false_positive'|'potential_match'} resolution
 * @property {string} [notes] - Resolution notes
 */

export class ScreeningService {
  /**
   * @param {Function} getToken - Async function that returns the auth token
   */
  constructor(getToken) {
    this.client = new ApiClient(getToken);
  }

  /**
   * Run a new screening check
   * @param {ScreeningCheckRequest} data
   * @returns {Promise<Object>}
   */
  runCheck(data) {
    return this.client.post('/screening/check', data);
  }

  /**
   * List screening checks with optional filters
   * @param {ScreeningFilters} params
   * @returns {Promise<{items: Array, total: number}>}
   */
  listChecks(params = {}) {
    const query = buildQueryString(params);
    return this.client.get(`/screening/checks${query}`);
  }

  /**
   * Get a single screening check with all hits
   * @param {string} id - Check ID
   * @returns {Promise<Object>}
   */
  getCheck(id) {
    return this.client.get(`/screening/checks/${id}`);
  }

  /**
   * Resolve a screening hit
   * @param {string} hitId - Hit ID
   * @param {'true_positive'|'false_positive'|'potential_match'} resolution
   * @param {string} [notes] - Resolution notes
   * @returns {Promise<Object>}
   */
  resolveHit(hitId, resolution, notes = null) {
    const body = { resolution };
    if (notes) body.notes = notes;
    return this.client.patch(`/screening/hits/${hitId}`, body);
  }

  /**
   * Get AI suggestion for how to resolve a hit
   * @param {string} hitId - Hit ID
   * @returns {Promise<{suggestion: string, confidence: number, reasoning: string}>}
   */
  getHitSuggestion(hitId) {
    return this.client.get(`/screening/hits/${hitId}/suggestion`);
  }

  /**
   * Get all unresolved hits
   * @param {Object} params - Optional filters
   * @returns {Promise<Array>}
   */
  getUnresolvedHits(params = {}) {
    const query = buildQueryString({ ...params, resolved: false });
    return this.client.get(`/screening/hits${query}`);
  }

  /**
   * Batch resolve multiple hits
   * @param {Array<{hitId: string, resolution: string, notes?: string}>} resolutions
   * @returns {Promise<Array>}
   */
  async batchResolve(resolutions) {
    const results = await Promise.all(
      resolutions.map(({ hitId, resolution, notes }) =>
        this.resolveHit(hitId, resolution, notes)
      )
    );
    return results;
  }
}

export default ScreeningService;
