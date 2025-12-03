/**
 * Billing Service
 *
 * API methods for subscription management, usage tracking, and invoices.
 * Integrates with Stripe for payment processing.
 */

import { ApiClient } from './api';

/**
 * @typedef {Object} UsageMetric
 * @property {string} name - Metric display name
 * @property {number} count - Current count
 * @property {number|null} limit - Plan limit (null = unlimited)
 * @property {string} unit - Unit type
 * @property {number|null} percentage_used - Percentage of limit used
 */

/**
 * @typedef {Object} UsageResponse
 * @property {string} tenant_id
 * @property {string} period_start
 * @property {string} period_end
 * @property {Object.<string, UsageMetric>} metrics
 */

/**
 * @typedef {Object} Subscription
 * @property {string} id - Stripe subscription ID
 * @property {string} status - active, past_due, canceled, etc.
 * @property {string} plan_id - Plan identifier
 * @property {string} plan_name - Plan display name
 * @property {string} current_period_start
 * @property {string} current_period_end
 * @property {boolean} cancel_at_period_end
 * @property {string|null} canceled_at
 * @property {number} amount - Amount in cents
 * @property {string} amount_formatted
 * @property {string} interval - month or year
 * @property {Object|null} payment_method
 */

/**
 * @typedef {Object} Invoice
 * @property {string} id
 * @property {string} number
 * @property {string} status
 * @property {number} amount_due
 * @property {string} amount_due_formatted
 * @property {number} amount_paid
 * @property {string} currency
 * @property {string} created
 * @property {string|null} due_date
 * @property {string|null} paid_at
 * @property {string|null} pdf_url
 * @property {string|null} hosted_invoice_url
 */

/**
 * @typedef {Object} Plan
 * @property {string} id
 * @property {string} name
 * @property {number} amount
 * @property {string} amount_formatted
 * @property {string} interval
 * @property {string[]} features
 */

export class BillingService {
  /**
   * @param {Function} getToken - Async function that returns the auth token
   */
  constructor(getToken) {
    this.client = new ApiClient(getToken);
  }

  // ===========================================
  // USAGE
  // ===========================================

  /**
   * Get current period usage
   * @param {Object} [options] - Request options
   * @returns {Promise<UsageResponse>}
   */
  getUsage(options = {}) {
    return this.client.get('/billing/usage', options);
  }

  /**
   * Get historical usage
   * @param {number} [months=6] - Number of months
   * @param {Object} [options] - Request options
   * @returns {Promise<{history: Array}>}
   */
  getUsageHistory(months = 6, options = {}) {
    return this.client.get(`/billing/usage/history?months=${months}`, options);
  }

  // ===========================================
  // SUBSCRIPTION
  // ===========================================

  /**
   * Get current subscription
   * @param {Object} [options] - Request options
   * @returns {Promise<Subscription|null>}
   */
  getSubscription(options = {}) {
    return this.client.get('/billing/subscription', options);
  }

  /**
   * Create or update subscription
   * @param {Object} data - Subscription data
   * @param {string} data.plan_id - Plan ID (starter, professional, enterprise)
   * @param {string} [data.payment_method_id] - Stripe payment method ID
   * @param {Object} [options] - Request options
   * @returns {Promise<Subscription>}
   */
  createOrUpdateSubscription(data, options = {}) {
    return this.client.post('/billing/subscription', data, options);
  }

  /**
   * Cancel subscription
   * @param {boolean} [immediately=false] - Cancel immediately vs at period end
   * @param {Object} [options] - Request options
   * @returns {Promise<Subscription>}
   */
  cancelSubscription(immediately = false, options = {}) {
    return this.client.delete(`/billing/subscription?immediately=${immediately}`, options);
  }

  // ===========================================
  // INVOICES
  // ===========================================

  /**
   * List invoices
   * @param {number} [limit=10] - Maximum invoices to return
   * @param {Object} [options] - Request options
   * @returns {Promise<Invoice[]>}
   */
  getInvoices(limit = 10, options = {}) {
    return this.client.get(`/billing/invoices?limit=${limit}`, options);
  }

  /**
   * Get invoice PDF URL
   * @param {string} invoiceId - Invoice ID
   * @param {Object} [options] - Request options
   * @returns {Promise<{pdf_url: string}>}
   */
  getInvoicePdf(invoiceId, options = {}) {
    return this.client.get(`/billing/invoices/${invoiceId}/pdf`, options);
  }

  /**
   * Download invoice PDF
   * @param {string} invoiceId - Invoice ID
   * @returns {Promise<void>}
   */
  async downloadInvoice(invoiceId) {
    const result = await this.getInvoicePdf(invoiceId);
    if (result.pdf_url) {
      window.open(result.pdf_url, '_blank');
    }
  }

  // ===========================================
  // PAYMENT METHODS
  // ===========================================

  /**
   * Create setup intent for adding payment method
   * @param {Object} [options] - Request options
   * @returns {Promise<{id: string, client_secret: string}>}
   */
  createSetupIntent(options = {}) {
    return this.client.post('/billing/payment-method', {}, options);
  }

  /**
   * List payment methods
   * @param {Object} [options] - Request options
   * @returns {Promise<Array>}
   */
  getPaymentMethods(options = {}) {
    return this.client.get('/billing/payment-methods', options);
  }

  /**
   * Delete a payment method
   * @param {string} paymentMethodId - Payment method ID
   * @param {Object} [options] - Request options
   * @returns {Promise<void>}
   */
  deletePaymentMethod(paymentMethodId, options = {}) {
    return this.client.delete(`/billing/payment-methods/${paymentMethodId}`, options);
  }

  // ===========================================
  // PLANS & PORTAL
  // ===========================================

  /**
   * Get available subscription plans
   * @param {Object} [options] - Request options
   * @returns {Promise<Plan[]>}
   */
  getPlans(options = {}) {
    return this.client.get('/billing/plans', options);
  }

  /**
   * Create customer portal session
   * @param {string} returnUrl - URL to return to after portal
   * @param {Object} [options] - Request options
   * @returns {Promise<{url: string}>}
   */
  createPortalSession(returnUrl, options = {}) {
    return this.client.post('/billing/portal', { return_url: returnUrl }, options);
  }

  /**
   * Open Stripe customer portal
   * @param {string} returnUrl - URL to return to after portal
   * @returns {Promise<void>}
   */
  async openPortal(returnUrl) {
    const result = await this.createPortalSession(returnUrl);
    if (result.url) {
      window.location.href = result.url;
    }
  }
}

export default BillingService;
