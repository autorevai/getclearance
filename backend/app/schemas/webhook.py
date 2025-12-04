"""
Get Clearance - Webhook Schemas
================================
Pydantic models for webhook event payloads and API validation.

Event Types (following Sumsub patterns):
- applicant.reviewed: When applicant approved/rejected
- screening.completed: When AML screening finishes
- document.verified: When document verification completes
- case.created: When manual review case created
"""

from datetime import datetime
from typing import Any, Literal
from uuid import UUID

from pydantic import BaseModel, Field, HttpUrl


# ===========================================
# EVENT DATA SCHEMAS
# ===========================================

class ApplicantReviewedData(BaseModel):
    """Data payload for applicant.reviewed event."""
    applicant_id: UUID
    external_id: str | None = None
    status: Literal["approved", "rejected"]
    risk_score: int | None = None
    risk_level: str | None = None  # low, medium, high
    review_decision: str | None = None  # auto_approved, manual_approved, auto_rejected, manual_rejected
    reviewed_by: UUID | None = None
    reviewed_at: datetime
    flags: list[str] = Field(default_factory=list)


class ScreeningCompletedData(BaseModel):
    """Data payload for screening.completed event."""
    applicant_id: UUID
    external_id: str | None = None
    screening_check_id: UUID
    status: Literal["clear", "hit", "error"]
    hit_count: int = 0
    check_types: list[str] = Field(default_factory=list)  # sanctions, pep, adverse_media
    list_version: str | None = None
    completed_at: datetime


class DocumentVerifiedData(BaseModel):
    """Data payload for document.verified event."""
    applicant_id: UUID
    external_id: str | None = None
    document_id: UUID
    document_type: str  # passport, drivers_license, id_card, etc.
    status: Literal["verified", "rejected", "review"]
    ocr_confidence: float | None = None
    fraud_signals: list[str] = Field(default_factory=list)
    security_features_detected: list[str] = Field(default_factory=list)
    verified_at: datetime


class CaseCreatedData(BaseModel):
    """Data payload for case.created event."""
    applicant_id: UUID
    external_id: str | None = None
    case_id: UUID
    case_type: str  # screening_hit, document_review, risk_review, etc.
    priority: str  # low, medium, high, critical
    reason: str
    auto_created: bool = True
    created_at: datetime


# ===========================================
# WEBHOOK ENVELOPE (Outer payload structure)
# ===========================================

EventType = Literal[
    "applicant.submitted",
    "applicant.reviewed",
    "screening.completed",
    "document.verified",
    "case.created",
]


class WebhookPayload(BaseModel):
    """
    Standard webhook payload envelope.

    This is the structure sent to customer webhook endpoints.
    Follows Sumsub webhook patterns for consistency.
    """
    event_type: EventType
    event_id: UUID  # Unique identifier for idempotency
    timestamp: datetime
    tenant_id: UUID
    correlation_id: str | None = None  # For tracing across systems
    data: dict[str, Any]  # Event-specific data (one of the *Data schemas above)

    model_config = {"from_attributes": True}


# ===========================================
# WEBHOOK DELIVERY TRACKING
# ===========================================

DeliveryStatus = Literal["pending", "delivered", "failed", "expired"]


class WebhookDeliveryCreate(BaseModel):
    """Create a new webhook delivery record."""
    webhook_url: HttpUrl
    event_type: EventType
    event_id: UUID
    payload: dict[str, Any]


class WebhookDeliveryResponse(BaseModel):
    """Response schema for webhook delivery record."""
    id: UUID
    tenant_id: UUID
    webhook_url: str
    event_type: str
    event_id: UUID
    payload: dict[str, Any]
    attempt_count: int
    last_attempt_at: datetime | None
    next_retry_at: datetime | None
    status: DeliveryStatus
    http_status: int | None
    response_body: str | None
    created_at: datetime

    model_config = {"from_attributes": True}


class WebhookDeliveryList(BaseModel):
    """Paginated list of webhook deliveries."""
    items: list[WebhookDeliveryResponse]
    total: int
    limit: int
    offset: int


# ===========================================
# WEBHOOK CONFIGURATION (Per-Tenant)
# ===========================================

class WebhookConfigCreate(BaseModel):
    """Configure webhook endpoint for a tenant."""
    url: HttpUrl
    secret: str = Field(..., min_length=16, max_length=256)  # HMAC signing secret
    events: list[EventType] = Field(
        default_factory=lambda: [
            "applicant.reviewed",
            "screening.completed",
            "document.verified",
            "case.created",
        ]
    )
    enabled: bool = True


class WebhookConfigUpdate(BaseModel):
    """Update webhook configuration."""
    url: HttpUrl | None = None
    secret: str | None = Field(None, min_length=16, max_length=256)
    events: list[EventType] | None = None
    enabled: bool | None = None


class WebhookConfigResponse(BaseModel):
    """Tenant webhook configuration."""
    url: str
    events: list[str]
    enabled: bool
    created_at: datetime
    updated_at: datetime
    # Note: secret is never returned for security

    model_config = {"from_attributes": True}


# ===========================================
# WEBHOOK TEST / VERIFICATION
# ===========================================

class WebhookTestRequest(BaseModel):
    """Request to send a test webhook."""
    event_type: EventType = "applicant.reviewed"


class WebhookTestResponse(BaseModel):
    """Response from test webhook attempt."""
    success: bool
    http_status: int | None = None
    response_time_ms: int | None = None
    error: str | None = None


# ===========================================
# HELPER FUNCTIONS
# ===========================================

def create_webhook_payload(
    event_type: EventType,
    event_id: UUID,
    tenant_id: UUID,
    data: dict[str, Any],
    correlation_id: str | None = None,
) -> dict[str, Any]:
    """
    Create a properly formatted webhook payload.

    This is a helper to ensure consistent payload structure
    when sending webhooks from different parts of the codebase.
    """
    return WebhookPayload(
        event_type=event_type,
        event_id=event_id,
        timestamp=datetime.utcnow(),
        tenant_id=tenant_id,
        correlation_id=correlation_id,
        data=data,
    ).model_dump(mode="json")
