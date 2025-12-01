/**
 * AI Service
 *
 * API methods for AI-powered features: risk summaries, assistant, batch analysis.
 */

import { ApiClient } from './api';

/**
 * @typedef {Object} RiskSummary
 * @property {number} risk_score - Overall risk score (0-100)
 * @property {string} risk_level - Risk level (low, medium, high)
 * @property {string} summary - AI-generated summary
 * @property {Array<string>} risk_factors - List of identified risk factors
 * @property {Array<string>} recommendations - Recommended actions
 * @property {string} generated_at - Timestamp
 */

/**
 * @typedef {Object} AssistantQuery
 * @property {string} query - User's question
 * @property {string} [applicant_id] - Optional applicant context
 * @property {string} [context] - Additional context
 */

/**
 * @typedef {Object} AssistantResponse
 * @property {string} response - AI response text
 * @property {Array<Object>} [sources] - Referenced sources
 * @property {string} generated_at - Timestamp
 */

export class AIService {
  /**
   * @param {Function} getToken - Async function that returns the auth token
   */
  constructor(getToken) {
    this.client = new ApiClient(getToken);
  }

  /**
   * Get AI-generated risk summary for an applicant
   * @param {string} applicantId - Applicant ID
   * @returns {Promise<RiskSummary>}
   */
  getRiskSummary(applicantId) {
    return this.client.get(`/ai/applicants/${applicantId}/risk-summary`);
  }

  /**
   * Regenerate risk summary for an applicant
   * @param {string} applicantId - Applicant ID
   * @returns {Promise<RiskSummary>}
   */
  regenerateRiskSummary(applicantId) {
    return this.client.post(`/ai/applicants/${applicantId}/risk-summary`, {});
  }

  /**
   * Ask the AI assistant a question
   * @param {string} query - User's question
   * @param {string} [applicantId] - Optional applicant context
   * @param {string} [context] - Additional context
   * @returns {Promise<AssistantResponse>}
   */
  askAssistant(query, applicantId = null, context = null) {
    const body = { query };
    if (applicantId) body.applicant_id = applicantId;
    if (context) body.context = context;
    return this.client.post('/ai/assistant', body);
  }

  /**
   * Run batch risk analysis on multiple applicants
   * @param {Array<string>} applicantIds - List of applicant IDs
   * @returns {Promise<{job_id: string, status: string}>}
   */
  batchAnalyze(applicantIds) {
    return this.client.post('/ai/batch-analyze', {
      applicant_ids: applicantIds,
    });
  }

  /**
   * Get status of a batch analysis job
   * @param {string} jobId - Job ID
   * @returns {Promise<Object>}
   */
  getBatchStatus(jobId) {
    return this.client.get(`/ai/batch-analyze/${jobId}`);
  }

  /**
   * Get AI suggestions for document verification
   * @param {string} documentId - Document ID
   * @returns {Promise<Object>}
   */
  getDocumentSuggestions(documentId) {
    return this.client.get(`/ai/documents/${documentId}/suggestions`);
  }
}

export default AIService;
