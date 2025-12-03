/**
 * Questionnaires Service
 *
 * Handles questionnaire CRUD and response submission.
 */

import { getSharedClient } from './api';

const client = getSharedClient();

export const QuestionnairesService = {
  // Questionnaire CRUD
  async list(params = {}) {
    return client.get('/questionnaires', { params });
  },

  async get(id) {
    return client.get(`/questionnaires/${id}`);
  },

  async create(data) {
    return client.post('/questionnaires', data);
  },

  async update(id, data) {
    return client.put(`/questionnaires/${id}`, data);
  },

  async delete(id) {
    return client.delete(`/questionnaires/${id}`);
  },

  // Templates
  async getTemplates() {
    return client.get('/questionnaires/templates');
  },

  async initializeDefaults() {
    return client.post('/questionnaires/initialize-defaults');
  },

  // Responses
  async submitApplicantResponse(applicantId, data) {
    return client.post(`/questionnaires/responses/applicant/${applicantId}`, data);
  },

  async getApplicantResponses(applicantId) {
    return client.get(`/questionnaires/responses/applicant/${applicantId}`);
  },

  async submitCompanyResponse(companyId, data) {
    return client.post(`/questionnaires/responses/company/${companyId}`, data);
  },

  async getCompanyResponses(companyId) {
    return client.get(`/questionnaires/responses/company/${companyId}`);
  },

  async updateResponse(responseId, data) {
    return client.put(`/questionnaires/responses/${responseId}`, data);
  },

  async reviewResponse(responseId, status, reviewNotes = null) {
    const params = { status_update: status };
    if (reviewNotes) params.review_notes = reviewNotes;
    return client.post(`/questionnaires/responses/${responseId}/review`, null, { params });
  },
};

export default QuestionnairesService;
