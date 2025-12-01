"""
Get Clearance - Webhook Service
================================
Webhook delivery service with HMAC signing and retry support.

Follows Sumsub webhook patterns:
- HMAC-SHA256 signature for payload verification
- 3 retry attempts with delays: 0s, 30s, 5min
- Stores all delivery attempts in webhook_deliveries table

Usage:
    from app.services.webhook import webhook_service

    # Send a webhook (queued for background delivery)
    delivery_id = await webhook_service.send_webhook(
        tenant_id=tenant.id,
        event_type="applicant.reviewed",
        event_id=uuid4(),
        data={"applicant_id": str(applicant.id), ...}
    )
"""

import hashlib
import hmac
import json
import logging
from datetime import datetime, timedelta
from typing import Any
from uuid import UUID, uuid4

import httpx
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db_context
from app.schemas.webhook import (
    EventType,
    WebhookPayload,
    create_webhook_payload,
)

logger = logging.getLogger(__name__)


# ===========================================
# RETRY CONFIGURATION (Following Sumsub)
# ===========================================

# Retry delays in seconds: 0s, 30s, 5min
RETRY_DELAYS = [0, 30, 300]
MAX_ATTEMPTS = 3

# HTTP timeout for webhook delivery
WEBHOOK_TIMEOUT = 30.0  # seconds


# ===========================================
# HMAC SIGNATURE GENERATION
# ===========================================

def generate_signature(payload: str, secret: str) -> str:
    """
    Generate HMAC-SHA256 signature for webhook payload.

    This allows recipients to verify the webhook came from us
    and wasn't tampered with in transit.

    Args:
        payload: JSON string of the webhook payload
        secret: Tenant's webhook secret key

    Returns:
        Hex-encoded HMAC-SHA256 signature
    """
    return hmac.new(
        secret.encode("utf-8"),
        payload.encode("utf-8"),
        hashlib.sha256
    ).hexdigest()


def generate_timestamp() -> int:
    """Generate Unix timestamp for webhook request."""
    return int(datetime.utcnow().timestamp())


def create_signed_headers(payload: str, secret: str) -> dict[str, str]:
    """
    Create HTTP headers for signed webhook delivery.

    Headers follow standard webhook patterns:
    - X-Webhook-Signature: HMAC signature of payload
    - X-Webhook-Timestamp: Unix timestamp (for replay protection)
    - X-Webhook-ID: Unique delivery ID (for idempotency)
    """
    timestamp = generate_timestamp()
    # Sign payload + timestamp to prevent replay attacks
    signature_payload = f"{timestamp}.{payload}"
    signature = generate_signature(signature_payload, secret)

    return {
        "Content-Type": "application/json",
        "X-Webhook-Signature": signature,
        "X-Webhook-Timestamp": str(timestamp),
        "X-GetClearance-Signature": f"sha256={signature}",  # GitHub-style header
        "User-Agent": "GetClearance-Webhook/1.0",
    }


# ===========================================
# WEBHOOK SERVICE CLASS
# ===========================================

class WebhookService:
    """
    Service for sending and managing webhook deliveries.

    This service handles:
    1. Creating webhook delivery records
    2. Enqueueing delivery jobs
    3. Fetching tenant webhook configuration
    4. Tracking delivery status
    """

    async def get_tenant_webhook_config(
        self,
        db: AsyncSession,
        tenant_id: UUID
    ) -> dict[str, Any] | None:
        """
        Get webhook configuration for a tenant.

        Returns None if webhooks not configured.
        """
        # Fetch from tenants.settings JSONB field
        from app.models.tenant import Tenant

        result = await db.execute(
            select(Tenant).where(Tenant.id == tenant_id)
        )
        tenant = result.scalar_one_or_none()

        if not tenant or not tenant.settings:
            return None

        webhook_config = tenant.settings.get("webhook")
        if not webhook_config or not webhook_config.get("enabled"):
            return None

        return webhook_config

    async def send_webhook(
        self,
        tenant_id: UUID,
        event_type: EventType,
        event_id: UUID | None = None,
        data: dict[str, Any] = None,
        correlation_id: str | None = None,
    ) -> UUID | None:
        """
        Send a webhook notification.

        Creates a webhook_deliveries record and enqueues a background
        job to actually deliver the webhook.

        Args:
            tenant_id: Tenant to send webhook for
            event_type: Type of event (applicant.reviewed, etc.)
            event_id: Unique event ID (generated if not provided)
            data: Event-specific data payload
            correlation_id: Optional correlation ID for tracing

        Returns:
            UUID of the webhook_deliveries record, or None if tenant
            has no webhook configured.
        """
        if event_id is None:
            event_id = uuid4()

        if data is None:
            data = {}

        async with get_db_context() as db:
            # Get tenant webhook config
            config = await self.get_tenant_webhook_config(db, tenant_id)

            if not config:
                logger.debug(f"No webhook configured for tenant {tenant_id}")
                return None

            # Check if this event type is subscribed
            subscribed_events = config.get("events", [])
            if subscribed_events and event_type not in subscribed_events:
                logger.debug(
                    f"Tenant {tenant_id} not subscribed to {event_type}"
                )
                return None

            # Create webhook payload
            payload = create_webhook_payload(
                event_type=event_type,
                event_id=event_id,
                tenant_id=tenant_id,
                data=data,
                correlation_id=correlation_id,
            )

            # Create webhook_deliveries record
            delivery_id = uuid4()
            webhook_url = config.get("url")

            await db.execute(
                """
                INSERT INTO webhook_deliveries (
                    id, tenant_id, webhook_url, event_type, event_id,
                    payload, status, attempt_count, created_at
                ) VALUES (
                    :id, :tenant_id, :webhook_url, :event_type, :event_id,
                    :payload, 'pending', 0, NOW()
                )
                """,
                {
                    "id": delivery_id,
                    "tenant_id": tenant_id,
                    "webhook_url": webhook_url,
                    "event_type": event_type,
                    "event_id": event_id,
                    "payload": json.dumps(payload),
                },
            )

            await db.commit()

            # Enqueue delivery job
            await self._enqueue_delivery(delivery_id)

            logger.info(
                f"Webhook queued: {event_type} for tenant {tenant_id} "
                f"(delivery_id={delivery_id})"
            )

            return delivery_id

    async def _enqueue_delivery(self, delivery_id: UUID) -> None:
        """Enqueue webhook delivery job to ARQ."""
        from arq import create_pool
        from app.workers.config import get_redis_settings

        try:
            redis = await create_pool(get_redis_settings())
            await redis.enqueue_job(
                "deliver_webhook",
                delivery_id=str(delivery_id),
            )
        except Exception as e:
            logger.error(f"Failed to enqueue webhook delivery: {e}")
            # Don't raise - the webhook can still be picked up by retry logic

    async def deliver(
        self,
        delivery_id: UUID,
        secret: str,
    ) -> tuple[bool, int | None, str | None]:
        """
        Attempt to deliver a webhook.

        This is called by the webhook worker. It:
        1. Sends the HTTP POST request
        2. Handles the response
        3. Returns success/failure status

        Args:
            delivery_id: ID of the webhook_deliveries record
            secret: Tenant's webhook signing secret

        Returns:
            Tuple of (success, http_status, error_message)
        """
        async with get_db_context() as db:
            # Fetch delivery record
            result = await db.execute(
                """
                SELECT id, webhook_url, payload, attempt_count
                FROM webhook_deliveries
                WHERE id = :id
                """,
                {"id": delivery_id},
            )
            delivery = result.fetchone()

            if not delivery:
                logger.error(f"Webhook delivery not found: {delivery_id}")
                return False, None, "Delivery record not found"

            webhook_url = delivery.webhook_url
            payload_str = (
                delivery.payload
                if isinstance(delivery.payload, str)
                else json.dumps(delivery.payload)
            )

            # Generate signed headers
            headers = create_signed_headers(payload_str, secret)

            # Send request
            try:
                async with httpx.AsyncClient(timeout=WEBHOOK_TIMEOUT) as client:
                    response = await client.post(
                        webhook_url,
                        content=payload_str,
                        headers=headers,
                    )

                http_status = response.status_code
                response_body = response.text[:1000]  # Truncate for storage

                if 200 <= http_status < 300:
                    # Success
                    logger.info(
                        f"Webhook delivered successfully: {delivery_id} "
                        f"(status={http_status})"
                    )
                    return True, http_status, None
                elif 400 <= http_status < 500:
                    # Permanent failure (client error)
                    logger.warning(
                        f"Webhook permanent failure: {delivery_id} "
                        f"(status={http_status})"
                    )
                    return False, http_status, f"HTTP {http_status}: {response_body}"
                else:
                    # Retryable failure (5xx server error)
                    logger.warning(
                        f"Webhook retryable failure: {delivery_id} "
                        f"(status={http_status})"
                    )
                    return False, http_status, f"HTTP {http_status}: {response_body}"

            except httpx.TimeoutException:
                logger.warning(f"Webhook timeout: {delivery_id}")
                return False, None, "Request timed out"
            except httpx.ConnectError as e:
                logger.warning(f"Webhook connection error: {delivery_id} - {e}")
                return False, None, f"Connection error: {str(e)}"
            except Exception as e:
                logger.error(f"Webhook delivery error: {delivery_id} - {e}")
                return False, None, f"Delivery error: {str(e)}"

    async def update_delivery_status(
        self,
        delivery_id: UUID,
        success: bool,
        http_status: int | None,
        error_message: str | None,
        attempt_count: int,
    ) -> None:
        """
        Update webhook delivery status after an attempt.

        Args:
            delivery_id: ID of the delivery record
            success: Whether delivery was successful
            http_status: HTTP response status code
            error_message: Error message if failed
            attempt_count: Current attempt number (1-indexed)
        """
        async with get_db_context() as db:
            now = datetime.utcnow()

            if success:
                # Mark as delivered
                await db.execute(
                    """
                    UPDATE webhook_deliveries
                    SET status = 'delivered',
                        attempt_count = :attempt_count,
                        last_attempt_at = :now,
                        http_status = :http_status,
                        next_retry_at = NULL
                    WHERE id = :id
                    """,
                    {
                        "id": delivery_id,
                        "attempt_count": attempt_count,
                        "now": now,
                        "http_status": http_status,
                    },
                )
            elif attempt_count >= MAX_ATTEMPTS:
                # Max retries exhausted - mark as failed
                await db.execute(
                    """
                    UPDATE webhook_deliveries
                    SET status = 'failed',
                        attempt_count = :attempt_count,
                        last_attempt_at = :now,
                        http_status = :http_status,
                        response_body = :error,
                        next_retry_at = NULL
                    WHERE id = :id
                    """,
                    {
                        "id": delivery_id,
                        "attempt_count": attempt_count,
                        "now": now,
                        "http_status": http_status,
                        "error": error_message,
                    },
                )
            else:
                # Schedule retry
                retry_delay = RETRY_DELAYS[attempt_count] if attempt_count < len(RETRY_DELAYS) else RETRY_DELAYS[-1]
                next_retry = now + timedelta(seconds=retry_delay)

                await db.execute(
                    """
                    UPDATE webhook_deliveries
                    SET status = 'pending',
                        attempt_count = :attempt_count,
                        last_attempt_at = :now,
                        http_status = :http_status,
                        response_body = :error,
                        next_retry_at = :next_retry
                    WHERE id = :id
                    """,
                    {
                        "id": delivery_id,
                        "attempt_count": attempt_count,
                        "now": now,
                        "http_status": http_status,
                        "error": error_message,
                        "next_retry": next_retry,
                    },
                )

            await db.commit()

    async def get_pending_deliveries(
        self,
        limit: int = 100,
    ) -> list[dict[str, Any]]:
        """
        Get pending webhook deliveries that are ready for retry.

        Used by a scheduled job to pick up failed deliveries.
        """
        async with get_db_context() as db:
            result = await db.execute(
                """
                SELECT id, tenant_id, webhook_url, payload, attempt_count
                FROM webhook_deliveries
                WHERE status = 'pending'
                  AND (next_retry_at IS NULL OR next_retry_at <= NOW())
                ORDER BY created_at ASC
                LIMIT :limit
                """,
                {"limit": limit},
            )
            return [dict(row._mapping) for row in result.fetchall()]


# ===========================================
# SERVICE INSTANCE
# ===========================================

webhook_service = WebhookService()


# ===========================================
# CONVENIENCE FUNCTIONS FOR COMMON EVENTS
# ===========================================

async def send_applicant_reviewed_webhook(
    tenant_id: UUID,
    applicant_id: UUID,
    external_id: str | None,
    status: str,
    risk_score: int | None = None,
    risk_level: str | None = None,
    review_decision: str | None = None,
    reviewed_by: UUID | None = None,
    flags: list[str] | None = None,
) -> UUID | None:
    """
    Send applicant.reviewed webhook.

    Called when an applicant is approved or rejected.
    """
    return await webhook_service.send_webhook(
        tenant_id=tenant_id,
        event_type="applicant.reviewed",
        data={
            "applicant_id": str(applicant_id),
            "external_id": external_id,
            "status": status,
            "risk_score": risk_score,
            "risk_level": risk_level,
            "review_decision": review_decision,
            "reviewed_by": str(reviewed_by) if reviewed_by else None,
            "reviewed_at": datetime.utcnow().isoformat(),
            "flags": flags or [],
        },
    )


async def send_screening_completed_webhook(
    tenant_id: UUID,
    applicant_id: UUID,
    external_id: str | None,
    screening_check_id: UUID,
    status: str,
    hit_count: int = 0,
    check_types: list[str] | None = None,
    list_version: str | None = None,
) -> UUID | None:
    """
    Send screening.completed webhook.

    Called when AML/sanctions screening finishes.
    """
    return await webhook_service.send_webhook(
        tenant_id=tenant_id,
        event_type="screening.completed",
        data={
            "applicant_id": str(applicant_id),
            "external_id": external_id,
            "screening_check_id": str(screening_check_id),
            "status": status,
            "hit_count": hit_count,
            "check_types": check_types or [],
            "list_version": list_version,
            "completed_at": datetime.utcnow().isoformat(),
        },
    )


async def send_document_verified_webhook(
    tenant_id: UUID,
    applicant_id: UUID,
    external_id: str | None,
    document_id: UUID,
    document_type: str,
    status: str,
    ocr_confidence: float | None = None,
    fraud_signals: list[str] | None = None,
    security_features: list[str] | None = None,
) -> UUID | None:
    """
    Send document.verified webhook.

    Called when document verification completes.
    """
    return await webhook_service.send_webhook(
        tenant_id=tenant_id,
        event_type="document.verified",
        data={
            "applicant_id": str(applicant_id),
            "external_id": external_id,
            "document_id": str(document_id),
            "document_type": document_type,
            "status": status,
            "ocr_confidence": ocr_confidence,
            "fraud_signals": fraud_signals or [],
            "security_features_detected": security_features or [],
            "verified_at": datetime.utcnow().isoformat(),
        },
    )


async def send_case_created_webhook(
    tenant_id: UUID,
    applicant_id: UUID,
    external_id: str | None,
    case_id: UUID,
    case_type: str,
    priority: str,
    reason: str,
    auto_created: bool = True,
) -> UUID | None:
    """
    Send case.created webhook.

    Called when a manual review case is created.
    """
    return await webhook_service.send_webhook(
        tenant_id=tenant_id,
        event_type="case.created",
        data={
            "applicant_id": str(applicant_id),
            "external_id": external_id,
            "case_id": str(case_id),
            "case_type": case_type,
            "priority": priority,
            "reason": reason,
            "auto_created": auto_created,
            "created_at": datetime.utcnow().isoformat(),
        },
    )
