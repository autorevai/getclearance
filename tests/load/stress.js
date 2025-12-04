/**
 * Get Clearance - k6 Stress Test
 * ===============================
 * Test system behavior under extreme load.
 *
 * Usage:
 *   k6 run stress.js
 */

import http from 'k6/http';
import { check, sleep } from 'k6';
import { Rate } from 'k6/metrics';

const errorRate = new Rate('errors');
const BASE_URL = __ENV.K6_BASE_URL || 'http://localhost:8000';
const API_KEY = __ENV.K6_API_KEY || 'test-api-key';

export const options = {
  // Stress test stages - push system to breaking point
  stages: [
    { duration: '2m', target: 100 },  // Ramp up aggressively
    { duration: '5m', target: 100 },  // Hold at 100 VUs
    { duration: '2m', target: 200 },  // Push to 200 VUs
    { duration: '5m', target: 200 },  // Hold at 200 VUs
    { duration: '2m', target: 300 },  // Extreme load
    { duration: '5m', target: 300 },  // Hold at 300 VUs
    { duration: '5m', target: 0 },    // Ramp down
  ],

  // Monitor but don't fail on thresholds (stress test)
  thresholds: {
    http_req_duration: ['p(95)<2000'],  // Allow higher latency under stress
    errors: ['rate<0.1'],                // Allow up to 10% errors
  },
};

const headers = {
  'Content-Type': 'application/json',
  'Authorization': `Bearer ${API_KEY}`,
};

export default function() {
  // Mix of read operations
  const endpoints = [
    '/api/v1/applicants?limit=10',
    '/api/v1/cases?limit=10',
    '/api/v1/screening/checks?limit=10',
    '/api/v1/analytics/dashboard',
    '/health',
  ];

  const endpoint = endpoints[Math.floor(Math.random() * endpoints.length)];
  const res = http.get(`${BASE_URL}${endpoint}`, { headers });

  const isError = res.status !== 200 && res.status !== 404;
  errorRate.add(isError);

  check(res, {
    'status is acceptable': (r) => r.status === 200 || r.status === 404 || r.status === 401,
    'response received': (r) => r.body !== null,
  });

  // Minimal think time for stress testing
  sleep(Math.random() * 0.5);
}
