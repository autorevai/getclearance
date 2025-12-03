/**
 * Cases Service
 *
 * API methods for case management: CRUD, notes, resolution.
 * All methods support abort signals for request cancellation.
 */

import { ApiClient, buildQueryString } from './api';

export class CasesService {
  constructor(getToken) {
    this.client = new ApiClient(getToken);
  }

  list(params = {}, options = {}) {
    const query = buildQueryString(params);
    return this.client.get(`/cases${query}`, options);
  }

  get(id, options = {}) {
    return this.client.get(`/cases/${id}`, options);
  }

  create(data, options = {}) {
    return this.client.post('/cases', data, options);
  }

  update(id, data, options = {}) {
    return this.client.patch(`/cases/${id}`, data, options);
  }

  resolve(id, resolution, notes = null, options = {}) {
    const body = { resolution };
    if (notes) body.notes = notes;
    return this.client.post(`/cases/${id}/resolve`, body, options);
  }

  addNote(id, content, options = {}) {
    return this.client.post(`/cases/${id}/notes`, { content }, options);
  }

  assign(id, userId, options = {}) {
    return this.client.patch(`/cases/${id}`, { assigned_to: userId }, options);
  }

  getMyCases(params = {}, options = {}) {
    const query = buildQueryString({ ...params, assigned_to: 'me' });
    return this.client.get(`/cases${query}`, options);
  }

  /**
   * Get case counts by status.
   * Returns: { open, in_progress, resolved, total }
   */
  getCounts(options = {}) {
    return this.client.get('/cases/counts', options);
  }
}

export default CasesService;
