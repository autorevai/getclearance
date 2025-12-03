/**
 * Audit Log Service
 *
 * API methods for viewing and verifying audit logs.
 * All methods support abort signals for request cancellation.
 */

import { ApiClient, buildQueryString } from './api';

export class AuditService {
  /**
   * @param {Function} getToken - Async function that returns the auth token
   */
  constructor(getToken) {
    this.client = new ApiClient(getToken);
  }

  /**
   * List audit log entries with filters and pagination
   * @param {Object} params - Filter parameters
   * @param {string} [params.resource_type] - Filter by resource type
   * @param {string} [params.resource_id] - Filter by resource ID
   * @param {string} [params.actor_id] - Filter by user who performed action
   * @param {string} [params.action] - Filter by action type
   * @param {string} [params.start_date] - Filter entries after this date
   * @param {string} [params.end_date] - Filter entries before this date
   * @param {string} [params.search] - Search in action or user email
   * @param {number} [params.limit] - Number of results per page
   * @param {number} [params.offset] - Pagination offset
   * @param {string} [params.sort_order] - asc or desc
   * @param {Object} [options] - Request options
   * @returns {Promise<{items: Array, total: number, limit: number, offset: number}>}
   */
  list(params = {}, options = {}) {
    const query = buildQueryString(params);
    return this.client.get(`/audit-log${query}`, options);
  }

  /**
   * Get a single audit log entry by ID
   * @param {number} id - Entry ID
   * @param {Object} [options] - Request options
   * @returns {Promise<Object>}
   */
  get(id, options = {}) {
    return this.client.get(`/audit-log/${id}`, options);
  }

  /**
   * Export audit logs to CSV
   * @param {Object} filters - Filter parameters
   * @param {Object} [options] - Request options
   * @returns {Promise<string>} CSV content
   */
  exportCSV(filters = {}, options = {}) {
    const query = buildQueryString(filters);
    return this.client.requestText(`/audit-log/export/csv${query}`, options);
  }

  /**
   * Verify audit chain integrity
   * @param {number} [limit] - Maximum entries to verify
   * @param {Object} [options] - Request options
   * @returns {Promise<Object>} Verification result
   */
  verifyChain(limit = 1000, options = {}) {
    const query = buildQueryString({ limit });
    return this.client.get(`/audit-log/verify/chain${query}`, options);
  }

  /**
   * Get audit log statistics
   * @param {Object} [options] - Request options
   * @returns {Promise<Object>}
   */
  getStats(options = {}) {
    return this.client.get('/audit-log/stats/summary', options);
  }

  /**
   * Get filter options (distinct values for dropdowns)
   * @param {Object} [options] - Request options
   * @returns {Promise<{actions: Array, resource_types: Array, users: Array}>}
   */
  getFilterOptions(options = {}) {
    return this.client.get('/audit-log/filters/options', options);
  }
}

export default AuditService;
