/**
 * Dashboard Service
 *
 * API methods for dashboard data: stats, screening summary, activity feed.
 * All methods support abort signals for request cancellation.
 */

import { ApiClient } from './api';

/**
 * @typedef {Object} DashboardStats
 * @property {number} today_applicants - Today's applicant count
 * @property {number} today_applicants_change - Change from yesterday
 * @property {number} approved - Approved count today
 * @property {number} approved_change - Change from yesterday
 * @property {number} rejected - Rejected count today
 * @property {number} rejected_change - Change from yesterday
 * @property {number} pending_review - Pending review count
 * @property {number} pending_review_change - Change from yesterday
 */

/**
 * @typedef {Object} ScreeningSummary
 * @property {number} sanctions_matches - Sanctions match count
 * @property {number} pep_hits - PEP hit count
 * @property {number} adverse_media - Adverse media count
 */

/**
 * @typedef {Object} ActivityItem
 * @property {string} type - Activity type (approved, rejected, screening_hit, document_uploaded)
 * @property {string} applicant_name - Applicant name
 * @property {string} time - Timestamp
 * @property {string|null} reviewer - Reviewer name
 * @property {string|null} detail - Additional detail
 */

/**
 * @typedef {Object} ActivityFeed
 * @property {ActivityItem[]} items - List of activity items
 */

export class DashboardService {
  /**
   * @param {Function} getToken - Async function that returns the auth token
   */
  constructor(getToken) {
    this.client = new ApiClient(getToken);
  }

  /**
   * Get dashboard KPI statistics
   * @param {Object} [options] - Request options (signal, timeout)
   * @returns {Promise<DashboardStats>}
   */
  getStats(options = {}) {
    return this.client.get('/dashboard/stats', options);
  }

  /**
   * Get screening hit summary
   * @param {Object} [options] - Request options
   * @returns {Promise<ScreeningSummary>}
   */
  getScreeningSummary(options = {}) {
    return this.client.get('/dashboard/screening-summary', options);
  }

  /**
   * Get recent activity feed
   * @param {number} [limit=20] - Number of items to fetch
   * @param {Object} [options] - Request options
   * @returns {Promise<ActivityFeed>}
   */
  getActivity(limit = 20, options = {}) {
    const query = limit !== 20 ? `?limit=${limit}` : '';
    return this.client.get(`/dashboard/activity${query}`, options);
  }
}

export default DashboardService;
