/**
 * AI Service
 *
 * API methods for AI-powered features: risk summaries, assistant, batch analysis.
 * All methods support abort signals for request cancellation.
 */

import { ApiClient } from './api';

export class AIService {
  constructor(getToken) {
    this.client = new ApiClient(getToken);
  }

  getRiskSummary(applicantId, options = {}) {
    return this.client.get(`/ai/applicants/${applicantId}/risk-summary`, options);
  }

  regenerateRiskSummary(applicantId, options = {}) {
    return this.client.post(`/ai/applicants/${applicantId}/risk-summary`, {}, options);
  }

  askAssistant(query, applicantId = null, context = null, options = {}) {
    const body = { query };
    if (applicantId) body.applicant_id = applicantId;
    if (context) body.context = context;
    return this.client.post('/ai/assistant', body, options);
  }

  batchAnalyze(applicantIds, options = {}) {
    return this.client.post('/ai/batch-analyze', { applicant_ids: applicantIds }, options);
  }

  getBatchStatus(jobId, options = {}) {
    return this.client.get(`/ai/batch-analyze/${jobId}`, options);
  }

  getDocumentSuggestions(documentId, options = {}) {
    return this.client.get(`/ai/documents/${documentId}/suggestions`, options);
  }
}

export default AIService;
