"""
Get Clearance - Integrations API
=================================
API key and webhook management endpoints.
"""

from datetime import datetime
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select, func, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies import TenantDB, AuthenticatedUser
from app.models.api_key import ApiKey
from app.models.webhook import WebhookConfig, WebhookDelivery
from app.schemas.integrations import (
    ApiKeyCreate,
    ApiKeyResponse,
    ApiKeyCreatedResponse,
    ApiKeyListResponse,
    WebhookCreate,
    WebhookUpdate,
    WebhookResponse,
    WebhookCreatedResponse,
    WebhookListResponse,
    WebhookDeliveryResponse,
    WebhookLogsResponse,
    WebhookTestResult,
    AvailableEventsResponse,
    AvailablePermissionsResponse,
)
from app.services.integrations import (
    generate_api_key,
    generate_webhook_secret,
    send_webhook,
    WEBHOOK_EVENTS,
    API_PERMISSIONS,
)


router = APIRouter()


# ===========================================
# API KEYS
# ===========================================

@router.get("/api-keys", response_model=ApiKeyListResponse)
async def list_api_keys(
    db: TenantDB,
    user: AuthenticatedUser,
):
    """
    List all API keys for the tenant.

    Only shows key prefix, not the full key.
    """
    result = await db.execute(
        select(ApiKey)
        .where(ApiKey.tenant_id == user.tenant_id)
        .order_by(ApiKey.created_at.desc())
    )
    keys = result.scalars().all()

    return ApiKeyListResponse(
        items=[
            ApiKeyResponse(
                id=key.id,
                name=key.name,
                key_prefix=key.key_prefix,
                permissions=key.permissions or [],
                last_used_at=key.last_used_at,
                last_used_ip=key.last_used_ip,
                expires_at=key.expires_at,
                revoked_at=key.revoked_at,
                created_at=key.created_at,
                is_active=key.is_active,
            )
            for key in keys
        ],
        total=len(keys),
    )


@router.post("/api-keys", response_model=ApiKeyCreatedResponse)
async def create_api_key(
    db: TenantDB,
    user: AuthenticatedUser,
    data: ApiKeyCreate,
):
    """
    Create a new API key.

    IMPORTANT: The full key is returned ONLY in this response.
    It cannot be retrieved again - store it securely!
    """
    # Validate permissions
    invalid_perms = set(data.permissions) - set(API_PERMISSIONS)
    if invalid_perms:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid permissions: {list(invalid_perms)}"
        )

    # Generate key
    full_key, key_hash, key_prefix = generate_api_key("live")

    # Create record
    api_key = ApiKey(
        tenant_id=user.tenant_id,
        name=data.name,
        key_hash=key_hash,
        key_prefix=key_prefix,
        permissions=data.permissions,
        expires_at=data.expires_at,
        created_by=user.id,
    )
    db.add(api_key)
    await db.commit()
    await db.refresh(api_key)

    return ApiKeyCreatedResponse(
        id=api_key.id,
        name=api_key.name,
        key=full_key,  # Only time the full key is returned
        key_prefix=api_key.key_prefix,
        permissions=api_key.permissions or [],
        expires_at=api_key.expires_at,
        created_at=api_key.created_at,
    )


@router.delete("/api-keys/{key_id}")
async def revoke_api_key(
    db: TenantDB,
    user: AuthenticatedUser,
    key_id: UUID,
):
    """
    Revoke an API key.

    The key will no longer be valid for authentication.
    """
    result = await db.execute(
        select(ApiKey).where(
            and_(
                ApiKey.id == key_id,
                ApiKey.tenant_id == user.tenant_id,
            )
        )
    )
    api_key = result.scalar_one_or_none()

    if not api_key:
        raise HTTPException(status_code=404, detail="API key not found")

    if api_key.revoked_at:
        raise HTTPException(status_code=400, detail="API key already revoked")

    api_key.revoked_at = datetime.utcnow()
    await db.commit()

    return {"message": "API key revoked"}


@router.post("/api-keys/{key_id}/rotate", response_model=ApiKeyCreatedResponse)
async def rotate_api_key(
    db: TenantDB,
    user: AuthenticatedUser,
    key_id: UUID,
):
    """
    Rotate an API key.

    Creates a new key with the same name/permissions and revokes the old one.
    """
    result = await db.execute(
        select(ApiKey).where(
            and_(
                ApiKey.id == key_id,
                ApiKey.tenant_id == user.tenant_id,
            )
        )
    )
    old_key = result.scalar_one_or_none()

    if not old_key:
        raise HTTPException(status_code=404, detail="API key not found")

    if old_key.revoked_at:
        raise HTTPException(status_code=400, detail="Cannot rotate revoked key")

    # Generate new key
    full_key, key_hash, key_prefix = generate_api_key("live")

    # Create new key with same properties
    new_key = ApiKey(
        tenant_id=user.tenant_id,
        name=old_key.name,
        key_hash=key_hash,
        key_prefix=key_prefix,
        permissions=old_key.permissions,
        expires_at=old_key.expires_at,
        created_by=user.id,
    )
    db.add(new_key)

    # Revoke old key
    old_key.revoked_at = datetime.utcnow()

    await db.commit()
    await db.refresh(new_key)

    return ApiKeyCreatedResponse(
        id=new_key.id,
        name=new_key.name,
        key=full_key,
        key_prefix=new_key.key_prefix,
        permissions=new_key.permissions or [],
        expires_at=new_key.expires_at,
        created_at=new_key.created_at,
    )


@router.get("/api-keys/permissions", response_model=AvailablePermissionsResponse)
async def get_available_permissions(
    user: AuthenticatedUser,
):
    """Get list of available API key permissions."""
    return AvailablePermissionsResponse(permissions=API_PERMISSIONS)


# ===========================================
# WEBHOOKS
# ===========================================

@router.get("/webhooks", response_model=WebhookListResponse)
async def list_webhooks(
    db: TenantDB,
    user: AuthenticatedUser,
):
    """List all webhooks for the tenant."""
    result = await db.execute(
        select(WebhookConfig)
        .where(WebhookConfig.tenant_id == user.tenant_id)
        .order_by(WebhookConfig.created_at.desc())
    )
    webhooks = result.scalars().all()

    return WebhookListResponse(
        items=[
            WebhookResponse(
                id=wh.id,
                name=wh.name,
                url=wh.url,
                events=wh.events or [],
                active=wh.active,
                status=wh.status,
                failure_count=wh.failure_count,
                last_success_at=wh.last_success_at,
                last_failure_at=wh.last_failure_at,
                created_at=wh.created_at,
                updated_at=wh.updated_at,
            )
            for wh in webhooks
        ],
        total=len(webhooks),
    )


@router.post("/webhooks", response_model=WebhookCreatedResponse)
async def create_webhook(
    db: TenantDB,
    user: AuthenticatedUser,
    data: WebhookCreate,
):
    """
    Create a new webhook.

    The webhook secret is returned in this response for signature verification.
    Store it securely!
    """
    # Validate events
    invalid_events = set(data.events) - set(WEBHOOK_EVENTS) - {"*"}
    if invalid_events:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid events: {list(invalid_events)}"
        )

    # Generate secret
    secret = generate_webhook_secret()

    # Create webhook
    webhook = WebhookConfig(
        tenant_id=user.tenant_id,
        name=data.name,
        url=data.url,
        secret=secret,
        events=data.events,
        active=data.active,
    )
    db.add(webhook)
    await db.commit()
    await db.refresh(webhook)

    return WebhookCreatedResponse(
        id=webhook.id,
        name=webhook.name,
        url=webhook.url,
        secret=secret,  # Show secret once
        events=webhook.events or [],
        active=webhook.active,
        created_at=webhook.created_at,
    )


@router.get("/webhooks/{webhook_id}", response_model=WebhookResponse)
async def get_webhook(
    db: TenantDB,
    user: AuthenticatedUser,
    webhook_id: UUID,
):
    """Get a single webhook by ID."""
    result = await db.execute(
        select(WebhookConfig).where(
            and_(
                WebhookConfig.id == webhook_id,
                WebhookConfig.tenant_id == user.tenant_id,
            )
        )
    )
    webhook = result.scalar_one_or_none()

    if not webhook:
        raise HTTPException(status_code=404, detail="Webhook not found")

    return WebhookResponse(
        id=webhook.id,
        name=webhook.name,
        url=webhook.url,
        events=webhook.events or [],
        active=webhook.active,
        status=webhook.status,
        failure_count=webhook.failure_count,
        last_success_at=webhook.last_success_at,
        last_failure_at=webhook.last_failure_at,
        created_at=webhook.created_at,
        updated_at=webhook.updated_at,
    )


@router.put("/webhooks/{webhook_id}", response_model=WebhookResponse)
async def update_webhook(
    db: TenantDB,
    user: AuthenticatedUser,
    webhook_id: UUID,
    data: WebhookUpdate,
):
    """Update a webhook configuration."""
    result = await db.execute(
        select(WebhookConfig).where(
            and_(
                WebhookConfig.id == webhook_id,
                WebhookConfig.tenant_id == user.tenant_id,
            )
        )
    )
    webhook = result.scalar_one_or_none()

    if not webhook:
        raise HTTPException(status_code=404, detail="Webhook not found")

    # Validate events if provided
    if data.events is not None:
        invalid_events = set(data.events) - set(WEBHOOK_EVENTS) - {"*"}
        if invalid_events:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid events: {list(invalid_events)}"
            )
        webhook.events = data.events

    if data.name is not None:
        webhook.name = data.name
    if data.url is not None:
        webhook.url = data.url
    if data.active is not None:
        webhook.active = data.active
        # Reset failure count when re-enabling
        if data.active:
            webhook.failure_count = 0

    await db.commit()
    await db.refresh(webhook)

    return WebhookResponse(
        id=webhook.id,
        name=webhook.name,
        url=webhook.url,
        events=webhook.events or [],
        active=webhook.active,
        status=webhook.status,
        failure_count=webhook.failure_count,
        last_success_at=webhook.last_success_at,
        last_failure_at=webhook.last_failure_at,
        created_at=webhook.created_at,
        updated_at=webhook.updated_at,
    )


@router.delete("/webhooks/{webhook_id}")
async def delete_webhook(
    db: TenantDB,
    user: AuthenticatedUser,
    webhook_id: UUID,
):
    """Delete a webhook and all its delivery logs."""
    result = await db.execute(
        select(WebhookConfig).where(
            and_(
                WebhookConfig.id == webhook_id,
                WebhookConfig.tenant_id == user.tenant_id,
            )
        )
    )
    webhook = result.scalar_one_or_none()

    if not webhook:
        raise HTTPException(status_code=404, detail="Webhook not found")

    await db.delete(webhook)
    await db.commit()

    return {"message": "Webhook deleted"}


@router.post("/webhooks/{webhook_id}/test", response_model=WebhookTestResult)
async def test_webhook(
    db: TenantDB,
    user: AuthenticatedUser,
    webhook_id: UUID,
):
    """
    Send a test event to a webhook.

    Sends a test.ping event to verify the webhook is receiving events correctly.
    """
    result = await db.execute(
        select(WebhookConfig).where(
            and_(
                WebhookConfig.id == webhook_id,
                WebhookConfig.tenant_id == user.tenant_id,
            )
        )
    )
    webhook = result.scalar_one_or_none()

    if not webhook:
        raise HTTPException(status_code=404, detail="Webhook not found")

    # Send test event
    test_payload = {
        "event": "test.ping",
        "timestamp": datetime.utcnow().isoformat(),
        "data": {
            "message": "This is a test webhook delivery from GetClearance",
            "webhook_id": str(webhook_id),
        },
    }

    delivery = await send_webhook(db, webhook, "test.ping", test_payload)

    return WebhookTestResult(
        success=delivery.success,
        response_code=delivery.response_code,
        response_time_ms=delivery.response_time_ms,
        error_message=delivery.error_message,
    )


@router.get("/webhooks/{webhook_id}/logs", response_model=WebhookLogsResponse)
async def get_webhook_logs(
    db: TenantDB,
    user: AuthenticatedUser,
    webhook_id: UUID,
    limit: Annotated[int, Query(ge=1, le=100)] = 50,
    offset: Annotated[int, Query(ge=0)] = 0,
):
    """Get delivery logs for a webhook."""
    # Verify webhook belongs to tenant
    result = await db.execute(
        select(WebhookConfig).where(
            and_(
                WebhookConfig.id == webhook_id,
                WebhookConfig.tenant_id == user.tenant_id,
            )
        )
    )
    webhook = result.scalar_one_or_none()

    if not webhook:
        raise HTTPException(status_code=404, detail="Webhook not found")

    # Get total count
    total = await db.scalar(
        select(func.count(WebhookDelivery.id))
        .where(WebhookDelivery.webhook_id == webhook_id)
    ) or 0

    # Get deliveries
    result = await db.execute(
        select(WebhookDelivery)
        .where(WebhookDelivery.webhook_id == webhook_id)
        .order_by(WebhookDelivery.created_at.desc())
        .limit(limit)
        .offset(offset)
    )
    deliveries = result.scalars().all()

    return WebhookLogsResponse(
        items=[
            WebhookDeliveryResponse(
                id=d.id,
                event_type=d.event_type,
                response_code=d.response_code,
                response_time_ms=d.response_time_ms,
                success=d.success,
                error_message=d.error_message,
                created_at=d.created_at,
                delivered_at=d.delivered_at,
            )
            for d in deliveries
        ],
        total=total,
    )


@router.get("/webhooks/events", response_model=AvailableEventsResponse)
async def get_available_events(
    user: AuthenticatedUser,
):
    """Get list of available webhook events."""
    return AvailableEventsResponse(events=WEBHOOK_EVENTS)
