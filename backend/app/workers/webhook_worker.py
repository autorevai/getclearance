"""
Get Clearance - Webhook Worker
==============================
Background worker for webhook delivery with retry logic.

Follows Sumsub webhook patterns:
- 3 retry attempts with delays: 0s, 30s, 5min
- HMAC-SHA256 signature verification
- Stores all delivery attempts

Usage (from API or other workers):
    from arq import create_pool
    from app.workers.config import get_redis_settings

    redis = await create_pool(get_redis_settings())
    job = await redis.enqueue_job(
        'deliver_webhook',
        delivery_id='uuid-here',
    )
"""

import logging
from datetime import datetime, timedelta
from typing import Any
from uuid import UUID

from sqlalchemy import select

from app.database import get_db_context
from app.models.tenant import Tenant
from app.services.webhook import (
    webhook_service,
    RETRY_DELAYS,
    MAX_ATTEMPTS,
)

logger = logging.getLogger(__name__)


async def deliver_webhook(
    ctx: dict[str, Any],
    delivery_id: str,
) -> dict[str, Any]:
    """
    Deliver a webhook notification.

    This is the main webhook delivery worker function. It:
    1. Fetches the delivery record
    2. Gets the tenant's webhook secret
    3. Attempts delivery with HMAC signing
    4. Updates status and schedules retry if needed

    Args:
        ctx: ARQ context with logger
        delivery_id: UUID of the webhook_deliveries record

    Returns:
        Dict with status, attempt_count, and next action

    Raises:
        Exception: If delivery fails and should be retried by ARQ
    """
    job_logger = ctx.get("logger", logger)
    job_logger.info(f"Starting webhook delivery: {delivery_id}")

    delivery_uuid = UUID(delivery_id)

    async with get_db_context() as db:
        # Fetch delivery record with tenant info
        result = await db.execute(
            """
            SELECT
                wd.id,
                wd.tenant_id,
                wd.webhook_url,
                wd.event_type,
                wd.payload,
                wd.attempt_count,
                wd.status,
                t.settings as tenant_settings
            FROM webhook_deliveries wd
            JOIN tenants t ON t.id = wd.tenant_id
            WHERE wd.id = :id
            """,
            {"id": delivery_uuid},
        )
        delivery = result.fetchone()

        if not delivery:
            job_logger.error(f"Webhook delivery not found: {delivery_id}")
            return {"status": "error", "error": "Delivery not found"}

        # Check if already delivered or expired
        if delivery.status == "delivered":
            job_logger.info(f"Webhook already delivered: {delivery_id}")
            return {"status": "already_delivered"}

        if delivery.status == "failed":
            job_logger.info(f"Webhook already failed (max retries): {delivery_id}")
            return {"status": "already_failed"}

        # Get webhook secret from tenant settings
        tenant_settings = delivery.tenant_settings or {}
        webhook_config = tenant_settings.get("webhook", {})
        webhook_secret = webhook_config.get("secret")

        if not webhook_secret:
            job_logger.error(
                f"No webhook secret configured for tenant {delivery.tenant_id}"
            )
            # Mark as failed - can't sign without secret
            await webhook_service.update_delivery_status(
                delivery_id=delivery_uuid,
                success=False,
                http_status=None,
                error_message="No webhook secret configured",
                attempt_count=delivery.attempt_count + 1,
            )
            return {"status": "error", "error": "No webhook secret"}

        # Increment attempt count
        attempt_count = delivery.attempt_count + 1

        job_logger.info(
            f"Attempting webhook delivery {delivery_id} "
            f"(attempt {attempt_count}/{MAX_ATTEMPTS})"
        )

        # Attempt delivery
        success, http_status, error_message = await webhook_service.deliver(
            delivery_id=delivery_uuid,
            secret=webhook_secret,
        )

        # Update delivery status
        await webhook_service.update_delivery_status(
            delivery_id=delivery_uuid,
            success=success,
            http_status=http_status,
            error_message=error_message,
            attempt_count=attempt_count,
        )

        if success:
            job_logger.info(
                f"Webhook delivered successfully: {delivery_id} "
                f"(status={http_status})"
            )
            return {
                "status": "delivered",
                "attempt_count": attempt_count,
                "http_status": http_status,
            }

        # Check if we should retry
        if attempt_count < MAX_ATTEMPTS:
            # Calculate retry delay
            retry_delay = (
                RETRY_DELAYS[attempt_count]
                if attempt_count < len(RETRY_DELAYS)
                else RETRY_DELAYS[-1]
            )

            job_logger.warning(
                f"Webhook delivery failed: {delivery_id} - "
                f"will retry in {retry_delay}s "
                f"(attempt {attempt_count}/{MAX_ATTEMPTS})"
            )

            # Schedule retry job
            await _schedule_retry(delivery_id, retry_delay)

            return {
                "status": "retry_scheduled",
                "attempt_count": attempt_count,
                "retry_delay": retry_delay,
                "error": error_message,
            }
        else:
            job_logger.error(
                f"Webhook delivery failed permanently: {delivery_id} "
                f"(max retries exhausted)"
            )
            return {
                "status": "failed",
                "attempt_count": attempt_count,
                "error": error_message,
            }


async def _schedule_retry(delivery_id: str, delay_seconds: int) -> None:
    """Schedule a retry job with the specified delay."""
    from arq import create_pool
    from app.workers.config import get_redis_settings

    try:
        redis = await create_pool(get_redis_settings())
        await redis.enqueue_job(
            "deliver_webhook",
            delivery_id=delivery_id,
            _defer_by=timedelta(seconds=delay_seconds),
        )
        logger.info(
            f"Scheduled webhook retry for {delivery_id} in {delay_seconds}s"
        )
    except Exception as e:
        logger.error(f"Failed to schedule webhook retry: {e}")


async def process_pending_webhooks(
    ctx: dict[str, Any],
) -> dict[str, Any]:
    """
    Process pending webhook deliveries.

    This is a scheduled job that picks up any webhooks that
    may have been missed (e.g., due to worker restart).

    Runs periodically to ensure no webhooks are lost.
    """
    job_logger = ctx.get("logger", logger)
    job_logger.info("Processing pending webhooks...")

    pending = await webhook_service.get_pending_deliveries(limit=100)
    enqueued = 0

    for delivery in pending:
        try:
            await _schedule_retry(str(delivery["id"]), 0)
            enqueued += 1
        except Exception as e:
            job_logger.error(
                f"Failed to enqueue pending webhook {delivery['id']}: {e}"
            )

    job_logger.info(f"Enqueued {enqueued} pending webhooks")
    return {"status": "success", "enqueued": enqueued}


async def retry_failed_webhook(
    ctx: dict[str, Any],
    delivery_id: str,
) -> dict[str, Any]:
    """
    Manually retry a failed webhook delivery.

    This can be called from an admin API to retry a specific
    webhook that has permanently failed.

    Args:
        ctx: ARQ context
        delivery_id: UUID of the delivery to retry

    Returns:
        Result of the delivery attempt
    """
    job_logger = ctx.get("logger", logger)
    job_logger.info(f"Manual retry requested for webhook: {delivery_id}")

    delivery_uuid = UUID(delivery_id)

    async with get_db_context() as db:
        # Reset the delivery for retry
        await db.execute(
            """
            UPDATE webhook_deliveries
            SET status = 'pending',
                attempt_count = 0,
                next_retry_at = NULL
            WHERE id = :id
            """,
            {"id": delivery_uuid},
        )
        await db.commit()

    # Now deliver
    return await deliver_webhook(ctx, delivery_id)
