"""
Get Clearance - Integrations Service
=====================================
API key generation/verification and webhook delivery service.
"""

import hashlib
import hmac
import secrets
import json
import time
from datetime import datetime
from typing import Any
from uuid import UUID

import httpx
from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.api_key import ApiKey
from app.models.webhook import WebhookConfig, WebhookDelivery


# API Key Functions
# =================

def generate_api_key(environment: str = "live") -> tuple[str, str, str]:
    """
    Generate a new API key.

    Args:
        environment: 'live' or 'test'

    Returns:
        Tuple of (full_key, key_hash, key_prefix)
        The full_key should be shown to user ONCE and never stored.
    """
    # Generate random key
    random_part = secrets.token_urlsafe(32)
    full_key = f"sk_{environment}_{random_part}"

    # Create SHA-256 hash for storage
    key_hash = hashlib.sha256(full_key.encode()).hexdigest()

    # Create prefix for identification (sk_live_xxxx)
    key_prefix = full_key[:12]

    return full_key, key_hash, key_prefix


def verify_api_key(key: str, key_hash: str) -> bool:
    """
    Verify an API key against its stored hash.

    Args:
        key: The full API key to verify
        key_hash: The stored SHA-256 hash

    Returns:
        True if key matches hash
    """
    computed_hash = hashlib.sha256(key.encode()).hexdigest()
    return hmac.compare_digest(computed_hash, key_hash)


async def get_api_key_by_hash(db: AsyncSession, key_hash: str) -> ApiKey | None:
    """Get API key by its hash."""
    result = await db.execute(
        select(ApiKey).where(ApiKey.key_hash == key_hash)
    )
    return result.scalar_one_or_none()


async def record_api_key_usage(
    db: AsyncSession,
    api_key: ApiKey,
    ip_address: str | None = None,
):
    """Record API key usage for tracking."""
    api_key.last_used_at = datetime.utcnow()
    if ip_address:
        api_key.last_used_ip = ip_address
    await db.commit()


# Webhook Functions
# =================

def sign_webhook_payload(secret: str, payload: dict[str, Any]) -> str:
    """
    Create HMAC-SHA256 signature for webhook payload.

    Args:
        secret: The webhook secret
        payload: The payload to sign

    Returns:
        Hex-encoded signature
    """
    payload_bytes = json.dumps(payload, separators=(',', ':')).encode()
    signature = hmac.new(
        secret.encode(),
        payload_bytes,
        hashlib.sha256
    ).hexdigest()
    return f"sha256={signature}"


async def send_webhook(
    db: AsyncSession,
    webhook: WebhookConfig,
    event_type: str,
    payload: dict[str, Any],
) -> WebhookDelivery:
    """
    Send a webhook notification.

    Args:
        db: Database session
        webhook: The webhook configuration
        event_type: Event type (e.g., 'applicant.created')
        payload: Event payload

    Returns:
        WebhookDelivery record with result
    """
    # Create delivery record
    delivery = WebhookDelivery(
        webhook_id=webhook.id,
        event_type=event_type,
        payload=payload,
    )
    db.add(delivery)

    # Create signature
    signature = sign_webhook_payload(webhook.secret, payload)

    # Send request
    start_time = time.time()
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                webhook.url,
                json=payload,
                headers={
                    "Content-Type": "application/json",
                    "X-Webhook-Signature": signature,
                    "X-Webhook-Event": event_type,
                    "X-Webhook-Id": str(webhook.id),
                    "User-Agent": "GetClearance-Webhook/1.0",
                },
            )

            response_time_ms = int((time.time() - start_time) * 1000)

            # Update delivery record
            delivery.response_code = response.status_code
            delivery.response_body = response.text[:4000] if response.text else None
            delivery.response_time_ms = response_time_ms
            delivery.delivered_at = datetime.utcnow()
            delivery.success = 200 <= response.status_code < 300

            if delivery.success:
                # Reset failure count on success
                webhook.failure_count = 0
                webhook.last_success_at = datetime.utcnow()
            else:
                # Increment failure count
                webhook.failure_count += 1
                webhook.last_failure_at = datetime.utcnow()
                delivery.error_message = f"HTTP {response.status_code}"

    except httpx.TimeoutException:
        delivery.error_message = "Request timeout"
        delivery.response_time_ms = 30000
        webhook.failure_count += 1
        webhook.last_failure_at = datetime.utcnow()
    except httpx.RequestError as e:
        delivery.error_message = str(e)[:500]
        delivery.response_time_ms = int((time.time() - start_time) * 1000)
        webhook.failure_count += 1
        webhook.last_failure_at = datetime.utcnow()
    except Exception as e:
        delivery.error_message = f"Unexpected error: {str(e)[:400]}"
        webhook.failure_count += 1
        webhook.last_failure_at = datetime.utcnow()

    await db.commit()
    await db.refresh(delivery)

    return delivery


async def dispatch_event(
    db: AsyncSession,
    tenant_id: UUID,
    event_type: str,
    payload: dict[str, Any],
):
    """
    Dispatch an event to all subscribed webhooks for a tenant.

    Args:
        db: Database session
        tenant_id: The tenant ID
        event_type: Event type
        payload: Event payload
    """
    # Find all active webhooks subscribed to this event
    result = await db.execute(
        select(WebhookConfig).where(
            and_(
                WebhookConfig.tenant_id == tenant_id,
                WebhookConfig.active == True,
                WebhookConfig.failure_count < 10,
            )
        )
    )
    webhooks = result.scalars().all()

    # Add event metadata to payload
    full_payload = {
        "event": event_type,
        "timestamp": datetime.utcnow().isoformat(),
        "data": payload,
    }

    # Send to each subscribed webhook
    for webhook in webhooks:
        if event_type in webhook.events or "*" in webhook.events:
            await send_webhook(db, webhook, event_type, full_payload)


def generate_webhook_secret() -> str:
    """Generate a secure webhook secret."""
    return secrets.token_urlsafe(32)


# Available Events
# ================

WEBHOOK_EVENTS = [
    "applicant.created",
    "applicant.updated",
    "applicant.approved",
    "applicant.rejected",
    "applicant.withdrawn",
    "document.uploaded",
    "document.verified",
    "document.rejected",
    "screening.started",
    "screening.completed",
    "screening.hit",
    "case.created",
    "case.resolved",
    "case.assigned",
]

# Available Permissions
# =====================

API_PERMISSIONS = [
    "read:applicants",
    "write:applicants",
    "read:documents",
    "write:documents",
    "read:screening",
    "write:screening",
    "read:cases",
    "write:cases",
    "read:analytics",
]
