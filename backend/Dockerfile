# Get Clearance Backend
# Multi-stage build for smaller production image

# ===========================================
# BUILD STAGE
# ===========================================
FROM python:3.11-slim as builder

WORKDIR /app

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip wheel --no-cache-dir --no-deps --wheel-dir /app/wheels -r requirements.txt


# ===========================================
# PRODUCTION STAGE
# ===========================================
FROM python:3.11-slim

WORKDIR /app

# Install runtime dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq5 \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Create non-root user
RUN useradd --create-home --shell /bin/bash appuser

# Copy wheels from builder
COPY --from=builder /app/wheels /wheels
RUN pip install --no-cache /wheels/*

# Copy application code
COPY --chown=appuser:appuser . .

# Switch to non-root user
USER appuser

# Expose port (Railway uses $PORT)
EXPOSE 8000

# Note: Railway manages its own healthcheck, so we disable Docker's
# to avoid conflicts. Railway healthcheck is configured in railway.json

# Run with uvicorn - use shell form to expand $PORT variable
# Railway sets $PORT automatically, fallback to 8000 for local development
CMD uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}
