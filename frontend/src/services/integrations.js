/**
 * Integrations Service
 *
 * API client for API keys and webhooks management.
 */

import { ApiClient, buildQueryString } from './api';

export class IntegrationsService {
  constructor(getToken) {
    this.client = new ApiClient(getToken);
  }

  // API Keys
  // ========

  /**
   * List all API keys
   * @param {Object} options - Request options
   */
  async listApiKeys(options = {}) {
    return this.client.get('/integrations/api-keys', options);
  }

  /**
   * Create a new API key
   * @param {Object} data - Key data (name, permissions, expires_at)
   * @param {Object} options - Request options
   */
  async createApiKey(data, options = {}) {
    return this.client.post('/integrations/api-keys', data, options);
  }

  /**
   * Revoke an API key
   * @param {string} keyId - Key ID
   * @param {Object} options - Request options
   */
  async revokeApiKey(keyId, options = {}) {
    return this.client.delete(`/integrations/api-keys/${keyId}`, options);
  }

  /**
   * Rotate an API key
   * @param {string} keyId - Key ID
   * @param {Object} options - Request options
   */
  async rotateApiKey(keyId, options = {}) {
    return this.client.post(`/integrations/api-keys/${keyId}/rotate`, {}, options);
  }

  /**
   * Get available permissions
   * @param {Object} options - Request options
   */
  async getAvailablePermissions(options = {}) {
    return this.client.get('/integrations/api-keys/permissions', options);
  }

  // Webhooks
  // ========

  /**
   * List all webhooks
   * @param {Object} options - Request options
   */
  async listWebhooks(options = {}) {
    return this.client.get('/integrations/webhooks', options);
  }

  /**
   * Create a new webhook
   * @param {Object} data - Webhook data (name, url, events, active)
   * @param {Object} options - Request options
   */
  async createWebhook(data, options = {}) {
    return this.client.post('/integrations/webhooks', data, options);
  }

  /**
   * Get a single webhook
   * @param {string} webhookId - Webhook ID
   * @param {Object} options - Request options
   */
  async getWebhook(webhookId, options = {}) {
    return this.client.get(`/integrations/webhooks/${webhookId}`, options);
  }

  /**
   * Update a webhook
   * @param {string} webhookId - Webhook ID
   * @param {Object} data - Update data
   * @param {Object} options - Request options
   */
  async updateWebhook(webhookId, data, options = {}) {
    return this.client.put(`/integrations/webhooks/${webhookId}`, data, options);
  }

  /**
   * Delete a webhook
   * @param {string} webhookId - Webhook ID
   * @param {Object} options - Request options
   */
  async deleteWebhook(webhookId, options = {}) {
    return this.client.delete(`/integrations/webhooks/${webhookId}`, options);
  }

  /**
   * Test a webhook
   * @param {string} webhookId - Webhook ID
   * @param {Object} options - Request options
   */
  async testWebhook(webhookId, options = {}) {
    return this.client.post(`/integrations/webhooks/${webhookId}/test`, {}, options);
  }

  /**
   * Get webhook delivery logs
   * @param {string} webhookId - Webhook ID
   * @param {Object} params - Query params (limit, offset)
   * @param {Object} options - Request options
   */
  async getWebhookLogs(webhookId, params = {}, options = {}) {
    const qs = buildQueryString(params);
    return this.client.get(`/integrations/webhooks/${webhookId}/logs${qs}`, options);
  }

  /**
   * Get available webhook events
   * @param {Object} options - Request options
   */
  async getAvailableEvents(options = {}) {
    return this.client.get('/integrations/webhooks/events', options);
  }
}
