/**
 * Get Clearance - k6 Smoke Test
 * ==============================
 * Quick verification that endpoints are working.
 *
 * Usage:
 *   k6 run smoke.js
 */

import http from 'k6/http';
import { check, sleep } from 'k6';

const BASE_URL = __ENV.K6_BASE_URL || 'http://localhost:8000';

export const options = {
  vus: 1,
  duration: '10s',
  thresholds: {
    http_req_duration: ['p(95)<1000'],
    http_req_failed: ['rate<0.1'],
  },
};

export default function() {
  // Health check
  let res = http.get(`${BASE_URL}/health`);
  check(res, {
    'health check status 200': (r) => r.status === 200,
    'health check has status': (r) => {
      try {
        const body = JSON.parse(r.body);
        return body.status === 'healthy' || body.status === 'ok';
      } catch {
        return r.status === 200;
      }
    },
  });

  sleep(1);

  // API docs
  res = http.get(`${BASE_URL}/docs`);
  check(res, {
    'docs available': (r) => r.status === 200,
  });

  sleep(1);

  // OpenAPI schema
  res = http.get(`${BASE_URL}/openapi.json`);
  check(res, {
    'openapi available': (r) => r.status === 200,
  });
}
