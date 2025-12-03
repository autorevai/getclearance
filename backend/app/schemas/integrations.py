"""
Get Clearance - Integrations Schemas
=====================================
Pydantic schemas for API keys and webhooks.
"""

from datetime import datetime
from uuid import UUID
from pydantic import BaseModel, Field, HttpUrl


# API Key Schemas
# ===============

class ApiKeyCreate(BaseModel):
    """Request to create a new API key."""

    name: str = Field(min_length=1, max_length=255, description="Display name for the key")
    permissions: list[str] = Field(default=[], description="List of permissions")
    expires_at: datetime | None = Field(default=None, description="Optional expiration date")


class ApiKeyResponse(BaseModel):
    """API key response (without the full key)."""

    id: UUID
    name: str
    key_prefix: str = Field(description="First 12 characters of the key")
    permissions: list[str]
    last_used_at: datetime | None
    last_used_ip: str | None
    expires_at: datetime | None
    revoked_at: datetime | None
    created_at: datetime
    is_active: bool

    model_config = {"from_attributes": True}


class ApiKeyCreatedResponse(BaseModel):
    """
    Response after creating a new API key.

    IMPORTANT: The full key is ONLY shown once at creation.
    It cannot be retrieved again.
    """

    id: UUID
    name: str
    key: str = Field(description="The full API key - shown only once!")
    key_prefix: str
    permissions: list[str]
    expires_at: datetime | None
    created_at: datetime

    model_config = {"from_attributes": True}


class ApiKeyListResponse(BaseModel):
    """List of API keys."""

    items: list[ApiKeyResponse]
    total: int


# Webhook Schemas
# ===============

class WebhookCreate(BaseModel):
    """Request to create a new webhook."""

    name: str = Field(min_length=1, max_length=255, description="Display name")
    url: str = Field(description="Webhook endpoint URL")
    events: list[str] = Field(default=[], description="Events to subscribe to")
    active: bool = Field(default=True, description="Whether webhook is active")


class WebhookUpdate(BaseModel):
    """Request to update a webhook."""

    name: str | None = None
    url: str | None = None
    events: list[str] | None = None
    active: bool | None = None


class WebhookResponse(BaseModel):
    """Webhook configuration response."""

    id: UUID
    name: str
    url: str
    events: list[str]
    active: bool
    status: str = Field(description="Webhook status: active, paused, degraded, failing")
    failure_count: int
    last_success_at: datetime | None
    last_failure_at: datetime | None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class WebhookCreatedResponse(BaseModel):
    """
    Response after creating a webhook.

    Includes the webhook secret which should be stored securely by the client.
    """

    id: UUID
    name: str
    url: str
    secret: str = Field(description="Webhook secret for signature verification")
    events: list[str]
    active: bool
    created_at: datetime

    model_config = {"from_attributes": True}


class WebhookListResponse(BaseModel):
    """List of webhooks."""

    items: list[WebhookResponse]
    total: int


class WebhookDeliveryResponse(BaseModel):
    """Webhook delivery log entry."""

    id: UUID
    event_type: str
    response_code: int | None
    response_time_ms: int | None
    success: bool
    error_message: str | None
    created_at: datetime
    delivered_at: datetime | None

    model_config = {"from_attributes": True}


class WebhookLogsResponse(BaseModel):
    """Webhook delivery logs."""

    items: list[WebhookDeliveryResponse]
    total: int


class WebhookTestResult(BaseModel):
    """Result of testing a webhook."""

    success: bool
    response_code: int | None
    response_time_ms: int | None
    error_message: str | None


class AvailableEventsResponse(BaseModel):
    """List of available webhook events."""

    events: list[str]


class AvailablePermissionsResponse(BaseModel):
    """List of available API key permissions."""

    permissions: list[str]
