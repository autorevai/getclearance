"""
Get Clearance - Pydantic Schemas
"""

from app.schemas.applicant import (
    ApplicantCreate,
    ApplicantUpdate,
    ApplicantReview,
    ApplicantListParams,
    ApplicantSummary,
    ApplicantDetail,
    ApplicantListResponse,
    ApplicantStepResponse,
    StepComplete,
    StepResubmit,
    AddressSchema,
    RiskFactorSchema,
)

from app.schemas.webhook import (
    # Event data schemas
    ApplicantReviewedData,
    ScreeningCompletedData,
    DocumentVerifiedData,
    CaseCreatedData,
    # Webhook envelope
    WebhookPayload,
    EventType,
    # Delivery tracking
    DeliveryStatus,
    WebhookDeliveryCreate,
    WebhookDeliveryResponse,
    WebhookDeliveryList,
    # Configuration
    WebhookConfigCreate,
    WebhookConfigUpdate,
    WebhookConfigResponse,
    # Testing
    WebhookTestRequest,
    WebhookTestResponse,
    # Helper
    create_webhook_payload,
)

__all__ = [
    # Applicant schemas
    "ApplicantCreate",
    "ApplicantUpdate",
    "ApplicantReview",
    "ApplicantListParams",
    "ApplicantSummary",
    "ApplicantDetail",
    "ApplicantListResponse",
    "ApplicantStepResponse",
    "StepComplete",
    "StepResubmit",
    "AddressSchema",
    "RiskFactorSchema",
    # Webhook schemas
    "ApplicantReviewedData",
    "ScreeningCompletedData",
    "DocumentVerifiedData",
    "CaseCreatedData",
    "WebhookPayload",
    "EventType",
    "DeliveryStatus",
    "WebhookDeliveryCreate",
    "WebhookDeliveryResponse",
    "WebhookDeliveryList",
    "WebhookConfigCreate",
    "WebhookConfigUpdate",
    "WebhookConfigResponse",
    "WebhookTestRequest",
    "WebhookTestResponse",
    "create_webhook_payload",
]
