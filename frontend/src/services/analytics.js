/**
 * Analytics Service
 *
 * API client for analytics endpoints.
 */

import { ApiClient, buildQueryString } from './api';

export class AnalyticsService {
  constructor(getToken) {
    this.client = new ApiClient('/api/v1/analytics', getToken);
  }

  /**
   * Get all analytics data in a single request (faster page load)
   * @param {Date} startDate - Start date
   * @param {Date} endDate - End date
   * @param {string} granularity - 'day', 'week', or 'month'
   * @param {Object} options - Request options
   */
  async getAll(startDate, endDate, granularity = 'day', options = {}) {
    const params = { granularity };
    if (startDate) params.start_date = formatDate(startDate);
    if (endDate) params.end_date = formatDate(endDate);
    const qs = buildQueryString(params);
    return this.client.get(`/all${qs}`, options);
  }

  /**
   * Get overview KPI metrics
   * @param {Date} startDate - Start date
   * @param {Date} endDate - End date
   * @param {Object} options - Request options
   */
  async getOverview(startDate, endDate, options = {}) {
    const params = {};
    if (startDate) params.start_date = formatDate(startDate);
    if (endDate) params.end_date = formatDate(endDate);
    const qs = buildQueryString(params);
    return this.client.get(`/overview${qs}`, options);
  }

  /**
   * Get verification funnel data
   * @param {Date} startDate - Start date
   * @param {Date} endDate - End date
   * @param {Object} options - Request options
   */
  async getFunnel(startDate, endDate, options = {}) {
    const params = {};
    if (startDate) params.start_date = formatDate(startDate);
    if (endDate) params.end_date = formatDate(endDate);
    const qs = buildQueryString(params);
    return this.client.get(`/funnel${qs}`, options);
  }

  /**
   * Get time series trend data
   * @param {Date} startDate - Start date
   * @param {Date} endDate - End date
   * @param {string} granularity - 'day', 'week', or 'month'
   * @param {Object} options - Request options
   */
  async getTrends(startDate, endDate, granularity = 'day', options = {}) {
    const params = { granularity };
    if (startDate) params.start_date = formatDate(startDate);
    if (endDate) params.end_date = formatDate(endDate);
    const qs = buildQueryString(params);
    return this.client.get(`/trends${qs}`, options);
  }

  /**
   * Get geographic distribution
   * @param {Date} startDate - Start date
   * @param {Date} endDate - End date
   * @param {Object} options - Request options
   */
  async getGeography(startDate, endDate, options = {}) {
    const params = {};
    if (startDate) params.start_date = formatDate(startDate);
    if (endDate) params.end_date = formatDate(endDate);
    const qs = buildQueryString(params);
    return this.client.get(`/geography${qs}`, options);
  }

  /**
   * Get risk score distribution
   * @param {Date} startDate - Start date
   * @param {Date} endDate - End date
   * @param {Object} options - Request options
   */
  async getRiskDistribution(startDate, endDate, options = {}) {
    const params = {};
    if (startDate) params.start_date = formatDate(startDate);
    if (endDate) params.end_date = formatDate(endDate);
    const qs = buildQueryString(params);
    return this.client.get(`/risk${qs}`, options);
  }

  /**
   * Get SLA performance metrics
   * @param {Date} startDate - Start date
   * @param {Date} endDate - End date
   * @param {Object} options - Request options
   */
  async getSlaPerformance(startDate, endDate, options = {}) {
    const params = {};
    if (startDate) params.start_date = formatDate(startDate);
    if (endDate) params.end_date = formatDate(endDate);
    const qs = buildQueryString(params);
    return this.client.get(`/sla${qs}`, options);
  }

  /**
   * Export analytics report
   * @param {Date} startDate - Start date
   * @param {Date} endDate - End date
   * @param {string} format - 'csv' or 'json'
   * @param {Object} options - Request options
   */
  async exportReport(startDate, endDate, format = 'csv', options = {}) {
    const params = { format };
    if (startDate) params.start_date = formatDate(startDate);
    if (endDate) params.end_date = formatDate(endDate);
    const qs = buildQueryString(params);

    if (format === 'csv') {
      // For CSV, return raw text
      const response = await this.client.get(`/export${qs}`, {
        ...options,
        rawResponse: true,
      });
      return response;
    }

    return this.client.get(`/export${qs}`, options);
  }
}

/**
 * Format date for API
 * @param {Date} date
 * @returns {string} YYYY-MM-DD format
 */
function formatDate(date) {
  if (!date) return null;
  if (typeof date === 'string') return date;
  return date.toISOString().split('T')[0];
}
