# Security Testing

Security scanning and vulnerability assessment for Get Clearance.

## OWASP ZAP Scanning

### Prerequisites

Install OWASP ZAP:

```bash
# macOS
brew install zaproxy

# Docker (recommended)
docker pull owasp/zap2docker-stable

# Linux
sudo snap install zaproxy --classic
```

### Running Scans

#### Quick Scan (Docker)

```bash
# Scan local API
./run-scan.sh

# Scan specific URL
./run-scan.sh https://api.getclearance.com
```

#### Manual Docker Scan

```bash
docker run --rm \
  --network host \
  -v $(pwd):/zap/wrk/:rw \
  owasp/zap2docker-stable \
  zap-api-scan.py \
  -t http://localhost:8000/openapi.json \
  -f openapi \
  -r reports/zap-report.html
```

#### Full Scan (Takes longer)

```bash
docker run --rm \
  --network host \
  -v $(pwd):/zap/wrk/:rw \
  owasp/zap2docker-stable \
  zap-full-scan.py \
  -t http://localhost:8000 \
  -r reports/full-scan-report.html
```

## Security Checklist

### Authentication & Authorization
- [ ] JWT tokens validated correctly
- [ ] Token expiration enforced
- [ ] Multi-tenant isolation verified
- [ ] Role-based access control working

### API Security
- [ ] Input validation on all endpoints
- [ ] SQL injection prevention
- [ ] XSS prevention
- [ ] CORS configured correctly
- [ ] Rate limiting enabled

### Data Protection
- [ ] PII encrypted at rest
- [ ] Sensitive data masked in logs
- [ ] Audit logs immutable
- [ ] Secure file storage

### Infrastructure
- [ ] HTTPS enforced
- [ ] Security headers present
- [ ] Dependencies updated
- [ ] Secrets not in code

## Dependency Audit

```bash
# Python dependencies
cd backend
pip-audit

# JavaScript dependencies
cd frontend
npm audit
```

## Common Vulnerabilities

| Issue | Risk | Status |
|-------|------|--------|
| SQL Injection | High | Protected (SQLAlchemy ORM) |
| XSS | Medium | Protected (React escaping) |
| CSRF | Medium | Protected (token auth) |
| Secrets in Code | High | Check required |
| Outdated Deps | Variable | npm/pip audit |

## CI/CD Integration

```yaml
# GitHub Actions
- name: OWASP ZAP Scan
  uses: zaproxy/action-full-scan@v0.4.0
  with:
    target: 'http://localhost:8000'
    rules_file_name: '.zap/rules.tsv'
```

## Reports

After running scans, reports are saved to:
- `reports/zap-report.html` - Full HTML report
- `reports/zap-report.json` - Machine-readable JSON
- `reports/zap-report.md` - Markdown summary
