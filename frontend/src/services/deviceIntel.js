/**
 * Device Intelligence Service
 *
 * API methods for device fingerprinting and fraud detection via IPQualityScore.
 * Provides IP reputation, email validation, phone validation, and combined risk scoring.
 */

import { ApiClient, buildQueryString } from './api';

/**
 * @typedef {Object} DeviceSubmission
 * @property {string} session_id - Unique session identifier
 * @property {string} ip_address - IP address to check
 * @property {string} [fingerprint_hash] - Device fingerprint hash
 * @property {string} [user_agent] - Browser user agent
 * @property {string} [browser] - Browser name
 * @property {string} [browser_version] - Browser version
 * @property {string} [operating_system] - OS name
 * @property {string} [os_version] - OS version
 * @property {string} [device_type] - desktop/mobile/tablet
 * @property {string} [device_brand] - Device brand
 * @property {string} [device_model] - Device model
 * @property {string} [screen_resolution] - Screen resolution
 * @property {string} [timezone] - Timezone
 * @property {string} [language] - Browser language
 * @property {string} [applicant_id] - Associated applicant
 * @property {string} [email] - Email for validation
 * @property {string} [phone] - Phone for validation
 * @property {string} [phone_country] - Phone country code (e.g., 'US')
 */

/**
 * @typedef {Object} DeviceFilters
 * @property {string} [risk_level] - low/medium/high
 * @property {string} [ip_address] - Filter by IP
 * @property {number} [limit] - Results per page
 * @property {number} [offset] - Pagination offset
 */

/**
 * @typedef {Object} IPCheckResult
 * @property {string} ip_address
 * @property {number} fraud_score
 * @property {boolean} is_proxy
 * @property {boolean} is_vpn
 * @property {boolean} is_tor
 * @property {boolean} is_bot
 * @property {boolean} is_datacenter
 * @property {boolean} is_mobile
 * @property {boolean} active_vpn
 * @property {boolean} active_tor
 * @property {boolean} recent_abuse
 * @property {string} [connection_type]
 * @property {string} [country_code]
 * @property {string} [city]
 * @property {string} [region]
 * @property {string} [isp]
 * @property {number} [asn]
 */

/**
 * @typedef {Object} DeviceAnalysisResult
 * @property {string} id
 * @property {string} session_id
 * @property {number} risk_score
 * @property {string} risk_level - low/medium/high
 * @property {number} fraud_score
 * @property {Object} risk_signals
 * @property {string[]} flags
 * @property {string} ip_address
 * @property {string} [country_code]
 * @property {string} [city]
 * @property {string} [isp]
 * @property {boolean} is_vpn
 * @property {boolean} is_proxy
 * @property {boolean} is_tor
 * @property {boolean} is_bot
 * @property {boolean} is_datacenter
 * @property {boolean} is_mobile
 * @property {string} [device_type]
 * @property {string} [browser]
 * @property {string} [operating_system]
 * @property {Object} [ip_check]
 * @property {Object} [email_check]
 * @property {Object} [phone_check]
 * @property {string} created_at
 */

export class DeviceIntelService {
  /**
   * @param {Function} getToken - Async function that returns the auth token
   */
  constructor(getToken) {
    this.client = new ApiClient(getToken);
  }

  // ===========================================
  // DEVICE ANALYSIS
  // ===========================================

  /**
   * Submit device fingerprint for analysis
   * @param {DeviceSubmission} data - Device data to analyze
   * @param {Object} [options] - Request options (signal, timeout)
   * @returns {Promise<DeviceAnalysisResult>}
   */
  analyze(data, options = {}) {
    return this.client.post('/device-intel/analyze', data, options);
  }

  /**
   * Quick IP check without storing results
   * @param {string} ipAddress - IP address to check
   * @param {Object} [options] - Request options
   * @returns {Promise<IPCheckResult>}
   */
  checkIP(ipAddress, options = {}) {
    return this.client.get(`/device-intel/check-ip/${encodeURIComponent(ipAddress)}`, options);
  }

  // ===========================================
  // DEVICE HISTORY
  // ===========================================

  /**
   * Get device history for an applicant
   * @param {string} applicantId - Applicant ID
   * @param {Object} [options] - Request options
   * @returns {Promise<{applicant_id: string, devices: Array, total: number, has_high_risk: boolean, has_vpn: boolean, has_tor: boolean}>}
   */
  getApplicantDevices(applicantId, options = {}) {
    return this.client.get(`/device-intel/applicant/${applicantId}`, options);
  }

  /**
   * Get device for a specific session
   * @param {string} sessionId - Session ID
   * @param {Object} [options] - Request options
   * @returns {Promise<Object>}
   */
  getSessionDevice(sessionId, options = {}) {
    return this.client.get(`/device-intel/session/${encodeURIComponent(sessionId)}`, options);
  }

  // ===========================================
  // LIST & FILTERS
  // ===========================================

  /**
   * List device fingerprints with optional filters
   * @param {DeviceFilters} params - Filter parameters
   * @param {Object} [options] - Request options
   * @returns {Promise<{items: Array, total: number, limit: number, offset: number}>}
   */
  list(params = {}, options = {}) {
    const query = buildQueryString(params);
    return this.client.get(`/device-intel${query}`, options);
  }

  // ===========================================
  // STATISTICS
  // ===========================================

  /**
   * Get fraud detection statistics
   * @param {number} [days=30] - Number of days for stats period
   * @param {Object} [options] - Request options
   * @returns {Promise<{total_scans: number, high_risk_count: number, high_risk_pct: number, vpn_detected: number, vpn_pct: number, bot_detected: number, bot_pct: number, tor_detected: number, tor_pct: number, avg_fraud_score: number, period_days: number}>}
   */
  getStats(days = 30, options = {}) {
    return this.client.get(`/device-intel/stats?days=${days}`, options);
  }
}

export default DeviceIntelService;
