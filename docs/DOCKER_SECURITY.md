# Docker Security Best Practices

This document outlines the security measures implemented in the Get Clearance Docker setup and provides guidance for maintaining a secure containerized environment.

## Security Measures Implemented

### 1. **Credential Management**
- ✅ **No hardcoded passwords**: All sensitive credentials are loaded from environment variables via `.env.local` file
- ✅ **Git-ignored secrets**: `.env.local` and `.env` files are excluded from version control
- ✅ **Docker Compose compatibility**: Copy `.env.local` to `.env` or use `--env-file .env.local`

### 2. **Image Version Pinning**
- ✅ **Specific versions**: All images use pinned versions instead of `:latest` tags
  - `postgres:15-alpine` - Specific PostgreSQL version
  - `redis:7-alpine` - Specific Redis version
  - `minio/minio:RELEASE.2024-01-16T16-07-38Z` - Specific MinIO release
  - `python:3.11-slim` - Specific Python version

**Why this matters**: `:latest` tags can pull in vulnerable or breaking changes. Pinned versions ensure reproducible, auditable builds.

### 3. **Non-Root User Execution**
- ✅ **API container**: Runs as `appuser` (non-root) as defined in Dockerfile
- ✅ **Redis container**: Runs as user `999:999` (redis user)
- ⚠️ **PostgreSQL & MinIO**: Run as root by default (required by their design), but with limited capabilities

### 4. **Capability Dropping**
- ✅ **Principle of least privilege**: All containers drop `ALL` capabilities by default
- ✅ **Minimal additions**: Only necessary capabilities are explicitly added:
  - API: `NET_BIND_SERVICE` (to bind to port 8000)
  - PostgreSQL: `CHOWN`, `DAC_OVERRIDE`, `FOWNER`, `SETGID`, `SETUID`
  - Redis: `SETGID`, `SETUID`
  - MinIO: `CHOWN`, `DAC_OVERRIDE`, `FOWNER`, `SETGID`, `SETUID`

### 5. **Privilege Escalation Prevention**
- ✅ **no-new-privileges**: All containers set `security_opt: no-new-privileges:true`
- ✅ **Prevents**: Containers from gaining additional privileges during execution

### 6. **Network Security**
- ✅ **Isolated network**: All services run on a dedicated bridge network (`getclearance-network`)
- ✅ **Port exposure**: Only necessary ports are exposed to the host
- ⚠️ **Development ports**: In production, consider removing port mappings and using reverse proxy

### 7. **Read-Only Filesystems** (Production)
- ⚠️ **Development**: Read-only disabled for hot-reload functionality
- ✅ **Production**: Can enable `read_only: true` when volumes aren't needed
- ✅ **Temporary files**: Use `tmpfs` for `/tmp` and `/var/tmp`

## Security Checklist

### Before Deployment

- [ ] **Change all default passwords** in `.env.local` file (and `.env` if using Docker Compose)
- [ ] **Use strong, unique passwords** (minimum 16 characters, mix of characters)
- [ ] **Update image versions** regularly and scan for vulnerabilities
- [ ] **Review exposed ports** - only expose what's necessary
- [ ] **Enable read-only filesystems** in production where possible
- [ ] **Scan images for vulnerabilities**: `docker scan <image-name>`
- [ ] **Review and limit capabilities** - remove any unnecessary `cap_add` entries
- [ ] **Use secrets management** in production (Docker Secrets, AWS Secrets Manager, etc.)

### Regular Maintenance

- [ ] **Update Docker and Docker Compose** regularly
- [ ] **Update base images** monthly or when security patches are released
- [ ] **Scan images** before deployment: `docker scan <image-name>`
- [ ] **Review logs** for suspicious activity
- [ ] **Audit container configurations** quarterly
- [ ] **Rotate credentials** every 90 days

## Vulnerability Scanning

### Scan Images Before Use

```bash
# Scan all images used in docker-compose.yml
docker scan postgres:15-alpine
docker scan redis:7-alpine
docker scan minio/minio:RELEASE.2024-01-16T16-07-38Z
docker scan python:3.11-slim

# Scan your built application image
docker build -t getclearance-api ./backend
docker scan getclearance-api
```

### Automated Scanning

Consider integrating vulnerability scanning into your CI/CD pipeline:
- GitHub Actions with `docker/build-push-action` and `docker/setup-buildx-action`
- GitLab CI with `trivy` or `clair`
- Jenkins with OWASP Dependency-Check

## Production Recommendations

### 1. **Use Docker Secrets**
Replace environment variables with Docker Swarm secrets or external secret management:

```yaml
# Example with Docker Secrets (Swarm mode)
secrets:
  postgres_password:
    external: true
  redis_password:
    external: true

services:
  db:
    secrets:
      - postgres_password
    environment:
      - POSTGRES_PASSWORD_FILE=/run/secrets/postgres_password
```

### 2. **Remove Port Exposures**
In production, don't expose database/Redis ports to the host. Use:
- Internal Docker networking only
- Reverse proxy (nginx/traefik) for API
- VPN or SSH tunnels for database access if needed

### 3. **Enable Read-Only Root Filesystem**
```yaml
api:
  read_only: true
  tmpfs:
    - /tmp
    - /var/tmp
    - /app/.cache  # If needed for your app
```

### 4. **Resource Limits**
Add resource constraints to prevent resource exhaustion attacks:

```yaml
services:
  api:
    deploy:
      resources:
        limits:
          cpus: '2'
          memory: 2G
        reservations:
          cpus: '0.5'
          memory: 512M
```

### 5. **Health Checks**
All services should have health checks (already implemented):
- API: HTTP health endpoint
- PostgreSQL: `pg_isready`
- Redis: `redis-cli ping`
- MinIO: HTTP health endpoint

### 6. **Logging and Monitoring**
- Enable Docker logging driver with rotation
- Monitor for suspicious container activity
- Set up alerts for failed health checks

### 7. **Network Policies**
Consider using Docker network policies or Kubernetes NetworkPolicies to restrict inter-container communication.

## Common Security Pitfalls to Avoid

### ❌ Don't Do This:
```yaml
# BAD: Hardcoded credentials
environment:
  - POSTGRES_PASSWORD=postgres

# BAD: Using :latest tag
image: postgres:latest

# BAD: Running with full privileges
privileged: true

# BAD: Exposing Docker socket
volumes:
  - /var/run/docker.sock:/var/run/docker.sock

# BAD: Running as root unnecessarily
user: root
```

### ✅ Do This Instead:
```yaml
# GOOD: Environment variable
environment:
  - POSTGRES_PASSWORD=${POSTGRES_PASSWORD}

# GOOD: Pinned version
image: postgres:15-alpine

# GOOD: Limited capabilities
cap_drop:
  - ALL
cap_add:
  - NET_BIND_SERVICE

# GOOD: Non-root user
user: appuser:appuser
```

## Additional Resources

- [Docker Security Best Practices](https://docs.docker.com/engine/security/)
- [OWASP Docker Security Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Docker_Security_Cheat_Sheet.html)
- [CIS Docker Benchmark](https://www.cisecurity.org/benchmark/docker)
- [Docker Security Scanning](https://docs.docker.com/docker-hub/vulnerability-scanning/)

## Reporting Security Issues

If you discover a security vulnerability in this setup, please:
1. **Do not** create a public GitHub issue
2. Contact the maintainers directly
3. Allow time for the issue to be addressed before public disclosure

---

**Last Updated**: 2024-01-16
**Maintained By**: Get Clearance Security Team



