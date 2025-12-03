"""
Get Clearance - Monitoring Worker
==================================
Background worker for ongoing AML monitoring.

This worker:
1. Runs scheduled daily re-screening of monitored applicants
2. Creates alerts for new hits
3. Sends webhooks for new alerts

Usage (scheduled):
    This worker runs via ARQ cron schedule defined in config.py

Usage (manual):
    from arq import create_pool
    from app.workers.config import get_redis_settings

    redis = await create_pool(get_redis_settings())
    job = await redis.enqueue_job(
        'run_monitoring_batch',
        tenant_id='uuid-here'  # optional
    )
"""

import logging
from datetime import datetime
from typing import Any
from uuid import UUID

from sqlalchemy import select

from app.database import get_db_context
from app.services.monitoring import monitoring_service

logger = logging.getLogger(__name__)


async def run_monitoring_batch(
    ctx: dict[str, Any],
    tenant_id: str | None = None,
) -> dict[str, Any]:
    """
    Run AML monitoring batch for all monitored applicants.

    This is the main monitoring worker function. It:
    1. Gets all applicants with monitoring enabled
    2. Re-screens each against current sanctions/PEP lists
    3. Compares results with previous screening
    4. Creates alerts for new hits
    5. Triggers webhooks for alerts

    Args:
        ctx: ARQ context with logger
        tenant_id: Optional tenant UUID to filter (string)

    Returns:
        Dict with batch results
    """
    job_logger = ctx.get("logger", logger)
    job_logger.info(
        f"Starting monitoring batch"
        f"{' for tenant ' + tenant_id if tenant_id else ' for all tenants'}"
    )

    start_time = datetime.utcnow()

    async with get_db_context() as db:
        try:
            # Parse tenant_id if provided
            parsed_tenant_id = UUID(tenant_id) if tenant_id else None

            # Run the monitoring batch
            result = await monitoring_service.run_monitoring_batch(
                db=db,
                tenant_id=parsed_tenant_id,
            )

            await db.commit()

            duration = (datetime.utcnow() - start_time).total_seconds()

            job_logger.info(
                f"Monitoring batch complete in {duration:.2f}s: "
                f"screened={result.screened}, "
                f"new_alerts={result.new_alerts}, "
                f"errors={result.errors}"
            )

            # Trigger webhooks for new alerts
            if result.new_alerts > 0:
                await _send_alert_webhooks(db, result.details, job_logger)

            return {
                "status": "success",
                "screened": result.screened,
                "new_alerts": result.new_alerts,
                "errors": result.errors,
                "skipped": result.skipped,
                "duration_seconds": duration,
            }

        except Exception as e:
            job_logger.error(f"Monitoring batch error: {e}", exc_info=True)
            await db.rollback()
            raise


async def run_single_applicant_monitoring(
    ctx: dict[str, Any],
    applicant_id: str,
) -> dict[str, Any]:
    """
    Run monitoring for a single applicant.

    Useful for on-demand re-screening after enabling monitoring
    or when triggered by external event.

    Args:
        ctx: ARQ context
        applicant_id: UUID of applicant to screen

    Returns:
        Dict with screening results
    """
    job_logger = ctx.get("logger", logger)
    job_logger.info(f"Running single applicant monitoring: {applicant_id}")

    async with get_db_context() as db:
        try:
            from app.models import Applicant

            # Fetch applicant
            result = await db.execute(
                select(Applicant).where(Applicant.id == UUID(applicant_id))
            )
            applicant = result.scalar_one_or_none()

            if not applicant:
                return {
                    "status": "error",
                    "error": "Applicant not found",
                }

            # Check if monitoring is enabled
            if not await monitoring_service.is_monitoring_enabled(db, applicant.id):
                return {
                    "status": "error",
                    "error": "Monitoring not enabled for this applicant",
                }

            # Run screening - use internal method
            result = await monitoring_service._screen_and_compare(db, applicant)

            await db.commit()

            job_logger.info(
                f"Single applicant monitoring complete: "
                f"status={result.get('status')}, "
                f"new_hits={result.get('new_hits', 0)}"
            )

            return {
                "status": "success",
                **result,
            }

        except Exception as e:
            job_logger.error(
                f"Single applicant monitoring error for {applicant_id}: {e}",
                exc_info=True,
            )
            await db.rollback()
            raise


async def _send_alert_webhooks(
    db: Any,
    batch_details: list[dict[str, Any]],
    job_logger: logging.Logger,
) -> None:
    """
    Send webhooks for new monitoring alerts.

    Args:
        db: Database session
        batch_details: List of screening results from batch
        job_logger: Logger instance
    """
    try:
        from arq import create_pool
        from app.workers.config import get_redis_settings

        # Get alerts that were created
        alert_ids = [
            d.get("alert_id")
            for d in batch_details
            if d.get("new_alert") and d.get("alert_id")
        ]

        if not alert_ids:
            return

        job_logger.info(f"Sending webhooks for {len(alert_ids)} new alerts")

        # Queue webhook deliveries
        redis = await create_pool(get_redis_settings())

        for alert_id in alert_ids:
            # Queue webhook delivery
            await redis.enqueue_job(
                "deliver_webhook",
                event_type="monitoring.alert_created",
                resource_type="monitoring_alert",
                resource_id=alert_id,
            )

        await redis.close()

    except Exception as e:
        job_logger.error(f"Error sending alert webhooks: {e}", exc_info=True)
        # Don't re-raise - webhooks are secondary


async def get_monitoring_status(
    ctx: dict[str, Any],
    tenant_id: str,
) -> dict[str, Any]:
    """
    Get monitoring status for a tenant.

    Returns statistics about monitored applicants and alerts.

    Args:
        ctx: ARQ context
        tenant_id: Tenant UUID

    Returns:
        Dict with monitoring stats
    """
    job_logger = ctx.get("logger", logger)

    async with get_db_context() as db:
        try:
            stats = await monitoring_service.get_monitoring_stats(
                db=db,
                tenant_id=UUID(tenant_id),
            )

            return {
                "status": "success",
                **stats,
            }

        except Exception as e:
            job_logger.error(f"Error getting monitoring status: {e}")
            return {
                "status": "error",
                "error": str(e),
            }
