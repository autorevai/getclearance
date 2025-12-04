/**
 * Get Clearance - k6 Load Test Script
 * ====================================
 * Performance and load testing for the API endpoints.
 *
 * Usage:
 *   k6 run script.js
 *   k6 run script.js --vus 50 --duration 5m
 *   K6_BASE_URL=https://api.getclearance.com k6 run script.js
 *
 * Metrics:
 *   - Response time p95 < 500ms
 *   - Error rate < 1%
 *   - Throughput > 100 req/min
 */

import http from 'k6/http';
import { check, sleep, group } from 'k6';
import { Rate, Trend } from 'k6/metrics';

// Custom metrics
const errorRate = new Rate('errors');
const applicantLatency = new Trend('applicant_latency');
const screeningLatency = new Trend('screening_latency');
const caseLatency = new Trend('case_latency');

// Configuration
const BASE_URL = __ENV.K6_BASE_URL || 'http://localhost:8000';
const API_KEY = __ENV.K6_API_KEY || 'test-api-key';

export const options = {
  // Load test stages
  stages: [
    { duration: '30s', target: 10 },  // Ramp up to 10 users
    { duration: '1m', target: 20 },   // Stay at 20 users
    { duration: '2m', target: 50 },   // Ramp up to 50 users
    { duration: '1m', target: 50 },   // Stay at 50 users
    { duration: '30s', target: 0 },   // Ramp down
  ],

  // Thresholds for pass/fail
  thresholds: {
    http_req_duration: ['p(95)<500'],  // 95% of requests under 500ms
    errors: ['rate<0.01'],              // Error rate under 1%
    http_req_failed: ['rate<0.01'],     // HTTP failure rate under 1%
    applicant_latency: ['p(95)<300'],   // Applicant API p95 under 300ms
    screening_latency: ['p(95)<400'],   // Screening API p95 under 400ms
    case_latency: ['p(95)<300'],        // Case API p95 under 300ms
  },
};

// Headers for authenticated requests
const headers = {
  'Content-Type': 'application/json',
  'Authorization': `Bearer ${API_KEY}`,
  'X-Tenant-ID': 'test-tenant',
};

/**
 * Setup - runs once before the test
 */
export function setup() {
  // Verify API is reachable
  const res = http.get(`${BASE_URL}/health`, { headers });

  if (res.status !== 200) {
    console.warn(`Warning: Health check returned ${res.status}`);
  }

  return {
    baseUrl: BASE_URL,
    headers: headers,
  };
}

/**
 * Main test function - runs for each virtual user
 */
export default function(data) {
  const { baseUrl, headers } = data;

  // Randomly choose a scenario
  const scenario = Math.random();

  if (scenario < 0.4) {
    // 40% - Applicant operations
    group('Applicant Operations', () => {
      testApplicantList(baseUrl, headers);
      testApplicantGet(baseUrl, headers);
    });
  } else if (scenario < 0.7) {
    // 30% - Screening operations
    group('Screening Operations', () => {
      testScreeningList(baseUrl, headers);
      testScreeningCheck(baseUrl, headers);
    });
  } else if (scenario < 0.9) {
    // 20% - Case operations
    group('Case Operations', () => {
      testCaseList(baseUrl, headers);
      testCaseGet(baseUrl, headers);
    });
  } else {
    // 10% - Analytics
    group('Analytics', () => {
      testDashboard(baseUrl, headers);
    });
  }

  // Think time between requests
  sleep(Math.random() * 2 + 1);
}

/**
 * Test applicant list endpoint
 */
function testApplicantList(baseUrl, headers) {
  const start = Date.now();
  const res = http.get(`${baseUrl}/api/v1/applicants?limit=20`, { headers });
  const duration = Date.now() - start;

  applicantLatency.add(duration);
  errorRate.add(res.status !== 200);

  check(res, {
    'applicant list status 200': (r) => r.status === 200,
    'applicant list has data': (r) => {
      try {
        const body = JSON.parse(r.body);
        return Array.isArray(body.items) || Array.isArray(body);
      } catch {
        return false;
      }
    },
  });
}

/**
 * Test single applicant get
 */
function testApplicantGet(baseUrl, headers) {
  // First get list to find an ID
  const listRes = http.get(`${baseUrl}/api/v1/applicants?limit=1`, { headers });

  if (listRes.status === 200) {
    try {
      const items = JSON.parse(listRes.body).items || JSON.parse(listRes.body);
      if (items && items.length > 0) {
        const id = items[0].id;
        const start = Date.now();
        const res = http.get(`${baseUrl}/api/v1/applicants/${id}`, { headers });
        const duration = Date.now() - start;

        applicantLatency.add(duration);
        errorRate.add(res.status !== 200);

        check(res, {
          'applicant get status 200': (r) => r.status === 200,
        });
      }
    } catch {
      // Skip if parsing fails
    }
  }
}

/**
 * Test screening list endpoint
 */
function testScreeningList(baseUrl, headers) {
  const start = Date.now();
  const res = http.get(`${baseUrl}/api/v1/screening?limit=20`, { headers });
  const duration = Date.now() - start;

  screeningLatency.add(duration);
  errorRate.add(res.status !== 200 && res.status !== 404);

  check(res, {
    'screening list status ok': (r) => r.status === 200 || r.status === 404,
  });
}

/**
 * Test screening check (read-only for load test)
 */
function testScreeningCheck(baseUrl, headers) {
  const start = Date.now();
  const res = http.get(`${baseUrl}/api/v1/screening/checks?limit=10`, { headers });
  const duration = Date.now() - start;

  screeningLatency.add(duration);
  errorRate.add(res.status !== 200 && res.status !== 404);

  check(res, {
    'screening checks status ok': (r) => r.status === 200 || r.status === 404,
  });
}

/**
 * Test case list endpoint
 */
function testCaseList(baseUrl, headers) {
  const start = Date.now();
  const res = http.get(`${baseUrl}/api/v1/cases?limit=20`, { headers });
  const duration = Date.now() - start;

  caseLatency.add(duration);
  errorRate.add(res.status !== 200);

  check(res, {
    'case list status 200': (r) => r.status === 200,
  });
}

/**
 * Test single case get
 */
function testCaseGet(baseUrl, headers) {
  const listRes = http.get(`${baseUrl}/api/v1/cases?limit=1`, { headers });

  if (listRes.status === 200) {
    try {
      const items = JSON.parse(listRes.body).items || JSON.parse(listRes.body);
      if (items && items.length > 0) {
        const id = items[0].id;
        const start = Date.now();
        const res = http.get(`${baseUrl}/api/v1/cases/${id}`, { headers });
        const duration = Date.now() - start;

        caseLatency.add(duration);
        errorRate.add(res.status !== 200);

        check(res, {
          'case get status 200': (r) => r.status === 200,
        });
      }
    } catch {
      // Skip if parsing fails
    }
  }
}

/**
 * Test dashboard/analytics endpoint
 */
function testDashboard(baseUrl, headers) {
  const start = Date.now();
  const res = http.get(`${baseUrl}/api/v1/analytics/dashboard`, { headers });
  const duration = Date.now() - start;

  errorRate.add(res.status !== 200 && res.status !== 404);

  check(res, {
    'dashboard status ok': (r) => r.status === 200 || r.status === 404,
    'dashboard response time ok': (r) => duration < 1000,
  });
}

/**
 * Teardown - runs once after the test
 */
export function teardown(data) {
  console.log('Load test completed');
  console.log(`Base URL: ${data.baseUrl}`);
}
