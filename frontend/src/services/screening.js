/**
 * Screening Service
 *
 * API methods for AML/KYC screening: checks, hits, resolutions.
 * All methods support abort signals for request cancellation.
 */

import { ApiClient, buildQueryString } from './api';

export class ScreeningService {
  constructor(getToken) {
    this.client = new ApiClient(getToken);
  }

  runCheck(data, options = {}) {
    return this.client.post('/screening/check', data, options);
  }

  listChecks(params = {}, options = {}) {
    const query = buildQueryString(params);
    return this.client.get(`/screening/checks${query}`, options);
  }

  getCheck(id, options = {}) {
    return this.client.get(`/screening/checks/${id}`, options);
  }

  resolveHit(hitId, resolution, notes = null, options = {}) {
    const body = { resolution };
    if (notes) body.notes = notes;
    return this.client.patch(`/screening/hits/${hitId}`, body, options);
  }

  getHitSuggestion(hitId, options = {}) {
    return this.client.get(`/screening/hits/${hitId}/suggestion`, options);
  }

  getUnresolvedHits(params = {}, options = {}) {
    const query = buildQueryString({ ...params, resolved: false });
    return this.client.get(`/screening/hits${query}`, options);
  }

  getLists(options = {}) {
    return this.client.get('/screening/lists', options);
  }

  syncLists(options = {}) {
    return this.client.post('/screening/lists/sync', {}, options);
  }

  getStats(options = {}) {
    return this.client.get('/screening/stats', options);
  }
}

export default ScreeningService;
