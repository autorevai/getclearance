/**
 * Settings Service
 *
 * API methods for tenant settings, team management, and invitations.
 * All methods support abort signals for request cancellation.
 */

import { ApiClient } from './api';

export class SettingsService {
  /**
   * @param {Function} getToken - Async function that returns the auth token
   */
  constructor(getToken) {
    this.client = new ApiClient(getToken);
  }

  // ===========================================
  // SETTINGS
  // ===========================================

  /**
   * Get all settings for the tenant
   * @param {Object} [options] - Request options
   * @returns {Promise<{general: Object, notifications: Object, branding: Object, security: Object}>}
   */
  getSettings(options = {}) {
    return this.client.get('/settings', options);
  }

  /**
   * Update general settings
   * @param {Object} data - Settings to update (company_name, timezone, date_format, language)
   * @param {Object} [options] - Request options
   * @returns {Promise<Object>}
   */
  updateGeneralSettings(data, options = {}) {
    return this.client.put('/settings/general', data, options);
  }

  // ===========================================
  // NOTIFICATION SETTINGS
  // ===========================================

  /**
   * Get notification preferences
   * @param {Object} [options] - Request options
   * @returns {Promise<Object>}
   */
  getNotificationPreferences(options = {}) {
    return this.client.get('/settings/notifications', options);
  }

  /**
   * Update notification preferences
   * @param {Object} preferences - Notification preferences
   * @param {Object} [options] - Request options
   * @returns {Promise<Object>}
   */
  updateNotificationPreferences(preferences, options = {}) {
    return this.client.put('/settings/notifications', { preferences }, options);
  }

  // ===========================================
  // SECURITY SETTINGS
  // ===========================================

  /**
   * Get security settings
   * @param {Object} [options] - Request options
   * @returns {Promise<Object>}
   */
  getSecuritySettings(options = {}) {
    return this.client.get('/settings/security', options);
  }

  /**
   * Update security settings
   * @param {Object} data - Security settings to update
   * @param {Object} [options] - Request options
   * @returns {Promise<Object>}
   */
  updateSecuritySettings(data, options = {}) {
    return this.client.put('/settings/security', data, options);
  }

  // ===========================================
  // BRANDING SETTINGS
  // ===========================================

  /**
   * Get branding settings
   * @param {Object} [options] - Request options
   * @returns {Promise<Object>}
   */
  getBrandingSettings(options = {}) {
    return this.client.get('/settings/branding', options);
  }

  /**
   * Update branding settings
   * @param {Object} data - Branding settings to update (logo_url, primary_color, accent_color)
   * @param {Object} [options] - Request options
   * @returns {Promise<Object>}
   */
  updateBrandingSettings(data, options = {}) {
    return this.client.put('/settings/branding', data, options);
  }

  // ===========================================
  // TEAM MEMBERS
  // ===========================================

  /**
   * Get list of team members
   * @param {Object} [options] - Request options
   * @returns {Promise<{items: Array, total: number}>}
   */
  getTeamMembers(options = {}) {
    return this.client.get('/settings/team', options);
  }

  /**
   * Update a team member's role
   * @param {string} memberId - User ID
   * @param {string} role - New role (admin, reviewer, analyst, viewer)
   * @param {Object} [options] - Request options
   * @returns {Promise<Object>}
   */
  updateTeamMemberRole(memberId, role, options = {}) {
    return this.client.put(`/settings/team/${memberId}/role`, { role }, options);
  }

  /**
   * Remove a team member
   * @param {string} memberId - User ID
   * @param {Object} [options] - Request options
   * @returns {Promise<Object>}
   */
  removeTeamMember(memberId, options = {}) {
    return this.client.delete(`/settings/team/${memberId}`, options);
  }

  // ===========================================
  // TEAM INVITATIONS
  // ===========================================

  /**
   * Get pending invitations
   * @param {Object} [options] - Request options
   * @returns {Promise<{items: Array, total: number}>}
   */
  getInvitations(options = {}) {
    return this.client.get('/settings/team/invitations', options);
  }

  /**
   * Send a team invitation
   * @param {string} email - Email address to invite
   * @param {string} role - Role to assign (admin, reviewer, analyst, viewer)
   * @param {string} [message] - Optional custom message
   * @param {Object} [options] - Request options
   * @returns {Promise<Object>}
   */
  inviteTeamMember(email, role, message = null, options = {}) {
    const body = { email, role };
    if (message) body.message = message;
    return this.client.post('/settings/team/invite', body, options);
  }

  /**
   * Cancel an invitation
   * @param {string} invitationId - Invitation ID
   * @param {Object} [options] - Request options
   * @returns {Promise<Object>}
   */
  cancelInvitation(invitationId, options = {}) {
    return this.client.delete(`/settings/team/invitations/${invitationId}`, options);
  }

  /**
   * Resend an invitation
   * @param {string} invitationId - Invitation ID
   * @param {Object} [options] - Request options
   * @returns {Promise<Object>}
   */
  resendInvitation(invitationId, options = {}) {
    return this.client.post(`/settings/team/invitations/${invitationId}/resend`, {}, options);
  }
}

export default SettingsService;
