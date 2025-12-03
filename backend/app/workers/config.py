"""
Get Clearance - ARQ Worker Configuration
=========================================
Configuration for ARQ background task queue.

ARQ is a Redis-based async task queue that integrates well with
FastAPI and asyncio. It provides:
- Job retry with exponential backoff
- Job timeouts
- Job result storage
- Job monitoring

Start workers with:
    arq app.workers.config.WorkerSettings

Usage from API:
    from arq import create_pool
    from app.workers.config import get_redis_settings

    redis = await create_pool(get_redis_settings())
    job = await redis.enqueue_job('run_screening_check', applicant_id=uuid)
"""

import logging
from datetime import timedelta
from typing import Any

from arq import cron
from arq.connections import RedisSettings

from app.config import settings
from app.database import create_db_pool, close_db_pool

logger = logging.getLogger(__name__)


def get_redis_settings() -> RedisSettings:
    """
    Get Redis connection settings from app config.

    Parses the Redis URL into ARQ's RedisSettings format.
    """
    # Parse redis URL: redis://user:pass@host:port/db
    url = settings.redis_url_str

    # Remove redis:// prefix
    if url.startswith("redis://"):
        url = url[8:]
    elif url.startswith("rediss://"):
        # SSL connection
        url = url[9:]

    # Default values
    host = "localhost"
    port = 6379
    database = 0
    password = None

    # Parse user:pass@host:port/db
    if "@" in url:
        auth, url = url.split("@", 1)
        if ":" in auth:
            _, password = auth.split(":", 1)

    if "/" in url:
        url, db_str = url.rsplit("/", 1)
        try:
            database = int(db_str)
        except ValueError:
            pass

    if ":" in url:
        host, port_str = url.rsplit(":", 1)
        try:
            port = int(port_str)
        except ValueError:
            pass
    else:
        host = url

    return RedisSettings(
        host=host,
        port=port,
        database=database,
        password=password,
        conn_timeout=30,
        conn_retries=5,
        conn_retry_delay=1,
    )


async def startup(ctx: dict[str, Any]) -> None:
    """
    Worker startup handler.

    Called when worker process starts. Initialize database pool
    and other resources.
    """
    logger.info("Worker starting up...")

    # Initialize database connection pool
    await create_db_pool()

    # Store logger in context for workers
    ctx["logger"] = logger

    logger.info("Worker startup complete")


async def shutdown(ctx: dict[str, Any]) -> None:
    """
    Worker shutdown handler.

    Called when worker process stops. Clean up resources.
    """
    logger.info("Worker shutting down...")

    # Close database connections
    await close_db_pool()

    logger.info("Worker shutdown complete")


class WorkerSettings:
    """
    ARQ worker settings.

    This class is passed to arq as the settings module.
    All configuration for the worker process is defined here.
    """

    # Redis connection
    redis_settings = get_redis_settings()

    # Worker lifecycle
    on_startup = startup
    on_shutdown = shutdown

    # Import worker functions
    # These are the functions that can be enqueued as jobs
    functions = [
        "app.workers.screening_worker.run_screening_check",
        "app.workers.document_worker.process_document",
        "app.workers.ai_worker.generate_risk_summary",
        "app.workers.webhook_worker.deliver_webhook",
        "app.workers.webhook_worker.process_pending_webhooks",
        "app.workers.webhook_worker.retry_failed_webhook",
        "app.workers.monitoring_worker.run_monitoring_batch",
        "app.workers.monitoring_worker.run_single_applicant_monitoring",
        "app.workers.monitoring_worker.get_monitoring_status",
    ]

    # Job configuration
    max_jobs = 10  # Max concurrent jobs per worker
    job_timeout = timedelta(seconds=300)  # 5 minute timeout per job
    max_tries = 3  # Max retry attempts
    retry_delay = timedelta(seconds=10)  # Base delay between retries (exponential backoff applied)

    # Health check
    health_check_interval = timedelta(seconds=60)

    # Queue management
    queue_name = "arq:queue"

    # Scheduled jobs (cron)
    cron_jobs = [
        # Process pending webhooks every 5 minutes to catch any missed deliveries
        cron(
            "app.workers.webhook_worker.process_pending_webhooks",
            minute={0, 5, 10, 15, 20, 25, 30, 35, 40, 45, 50, 55},
        ),
        # Run ongoing AML monitoring daily at 2 AM UTC
        cron(
            "app.workers.monitoring_worker.run_monitoring_batch",
            hour={2},
            minute=0,
        ),
    ]


# Retry configuration helper
def get_retry_delay(retry_count: int, base_delay: int = 10) -> int:
    """
    Calculate retry delay with exponential backoff.

    Args:
        retry_count: Current retry attempt (0-indexed)
        base_delay: Base delay in seconds

    Returns:
        Delay in seconds

    Examples:
        retry 0: 10 seconds
        retry 1: 20 seconds
        retry 2: 40 seconds
    """
    return base_delay * (2 ** retry_count)
