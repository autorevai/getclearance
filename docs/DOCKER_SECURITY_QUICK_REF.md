# Docker Security Quick Reference

## Quick Setup

1. **Set strong passwords** in `.env.local`:
   - `POSTGRES_PASSWORD` - Strong password for PostgreSQL
   - `REDIS_PASSWORD` - Strong password for Redis (optional for dev, required for prod)
   - `MINIO_ROOT_PASSWORD` - Strong password for MinIO

2. **For Docker Compose** (creates `.env` from `.env.local`):
   ```bash
   cp .env.local .env
   ```
   Or use: `docker-compose --env-file .env.local up`

3. **Start services**:
   ```bash
   docker-compose up -d
   ```

## Security Features Enabled

✅ **Credential Management**: All passwords via environment variables  
✅ **Version Pinning**: All images use specific versions (no `:latest`)  
✅ **Non-Root Users**: Containers run with minimal privileges  
✅ **Capability Dropping**: Only necessary Linux capabilities enabled  
✅ **Privilege Escalation Prevention**: `no-new-privileges` enabled  
✅ **Network Isolation**: Services on dedicated Docker network  

## Regular Maintenance

### Update Images Monthly

```bash
# Check for updates
docker pull postgres:15-alpine
docker pull redis:7-alpine
docker pull minio/minio:RELEASE.2025-10-15T17-29-55Z
docker pull python:3.11-slim

# Scan for vulnerabilities
docker scan postgres:15-alpine
docker scan redis:7-alpine
docker scan minio/minio:RELEASE.2025-10-15T17-29-55Z
docker scan python:3.11-slim
```

### Update MinIO Version

1. Check latest release: https://github.com/minio/minio/releases
2. Update `docker-compose.yml`:
   ```yaml
   image: minio/minio:RELEASE.YYYY-MM-DDTHH-MM-SSZ
   ```
3. Pull and test:
   ```bash
   docker-compose pull minio
   docker-compose up -d minio
   ```

## Production Checklist

Before deploying to production:

- [ ] All passwords changed from defaults
- [ ] Strong passwords (16+ chars, mixed case, numbers, symbols)
- [ ] Redis password enabled (`REDIS_PASSWORD` set)
- [ ] Images scanned for vulnerabilities
- [ ] Read-only filesystem enabled where possible
- [ ] Unnecessary ports removed from host exposure
- [ ] Secrets management system in place (not `.env` files)
- [ ] Regular update schedule established
- [ ] Monitoring and alerting configured

## Common Issues

### Redis Connection Fails
If you set `REDIS_PASSWORD`, update `REDIS_URL` in `.env.local` (and `.env` if using Docker Compose):
```
REDIS_URL=redis://:your_password@redis:6379/0
```

### Container Won't Start
Check that all required environment variables are set in `.env.local` (and `.env` for Docker Compose):
```bash
docker-compose config
```

### Permission Denied Errors
Some containers need specific capabilities. If you see errors, check the `cap_add` section in `docker-compose.yml` - only add what's absolutely necessary.

## Emergency Response

If you suspect a security breach:

1. **Stop all containers**:
   ```bash
   docker-compose down
   ```

2. **Rotate all credentials** in `.env`

3. **Review logs**:
   ```bash
   docker-compose logs > security-audit-$(date +%Y%m%d).log
   ```

4. **Update all images**:
   ```bash
   docker-compose pull
   docker-compose up -d
   ```

5. **Scan for vulnerabilities**:
   ```bash
   docker scan $(docker-compose config --images)
   ```

---

For detailed information, see [DOCKER_SECURITY.md](./DOCKER_SECURITY.md)


