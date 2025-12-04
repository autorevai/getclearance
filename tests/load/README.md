# Load Testing with k6

Performance and load testing for the Get Clearance API.

## Prerequisites

Install k6:

```bash
# macOS
brew install k6

# Linux
sudo apt install k6

# Windows
choco install k6

# Docker
docker pull grafana/k6
```

## Running Tests

### Smoke Test (Quick Verification)

```bash
k6 run smoke.js
```

### Standard Load Test

```bash
# Default settings
k6 run script.js

# Custom settings
k6 run script.js --vus 50 --duration 5m

# Against production
K6_BASE_URL=https://api.getclearance.com K6_API_KEY=your-api-key k6 run script.js
```

### Stress Test (Find Breaking Points)

```bash
k6 run stress.js
```

## Test Scenarios

### script.js (Standard Load Test)

- Simulates typical production traffic
- 10 → 20 → 50 VUs over 5 minutes
- Tests applicants, screening, cases, and analytics endpoints
- Thresholds:
  - p95 response time < 500ms
  - Error rate < 1%

### smoke.js (Quick Verification)

- 1 VU for 10 seconds
- Verifies endpoints are responsive
- Good for CI/CD pipelines

### stress.js (Extreme Load)

- 100 → 200 → 300 VUs over 26 minutes
- Finds system breaking points
- Higher error tolerance (10%)

## Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| K6_BASE_URL | API base URL | http://localhost:8000 |
| K6_API_KEY | API authentication key | test-api-key |

## Performance Targets

| Metric | Target | Critical |
|--------|--------|----------|
| Response time (p95) | < 500ms | < 2000ms |
| Error rate | < 1% | < 5% |
| Throughput | > 100 req/min | > 50 req/min |

## Interpreting Results

```
✓ applicant list status 200
✓ http_req_duration...........: avg=145ms  p(95)=320ms
✓ http_req_failed.............: 0.12%
✓ errors......................: 0.08%
```

- **http_req_duration**: Response times (lower is better)
- **http_req_failed**: Percentage of failed HTTP requests
- **errors**: Custom error metric
- **vus**: Virtual users (concurrent connections)

## CI/CD Integration

```yaml
# GitHub Actions example
- name: Run load tests
  run: |
    k6 run tests/load/smoke.js \
      --out json=results.json \
      -e K6_BASE_URL=${{ secrets.API_URL }}
```

## Docker Usage

```bash
docker run -i grafana/k6 run - < script.js
```
