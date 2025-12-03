"""
Get Clearance - KYC Share Schemas
=================================
Pydantic schemas for the Reusable KYC / Portable Identity feature.
"""

from datetime import datetime
from typing import Optional, Any
from uuid import UUID

from pydantic import BaseModel, Field, field_validator


# ===========================================
# PERMISSION CONSTANTS
# ===========================================
VALID_PERMISSIONS = {
    "basic_info",
    "id_verification",
    "address",
    "screening",
    "documents",
    "full",
}


# ===========================================
# REQUEST SCHEMAS
# ===========================================
class ShareTokenCreate(BaseModel):
    """Request to generate a new KYC share token."""

    applicant_id: UUID = Field(..., description="UUID of the applicant whose KYC to share")
    shared_with: str = Field(..., min_length=1, max_length=255, description="Name of company/entity receiving the data")
    shared_with_email: Optional[str] = Field(None, max_length=255, description="Optional contact email")
    purpose: Optional[str] = Field(None, max_length=500, description="Purpose for sharing")

    permissions: dict[str, bool] = Field(
        ...,
        description="Permissions to grant (basic_info, id_verification, address, screening, documents, full)"
    )

    expires_days: int = Field(
        default=30,
        ge=1,
        le=90,
        description="Days until token expires (max 90)"
    )
    max_uses: int = Field(
        default=1,
        ge=1,
        le=10,
        description="Maximum times token can be used (max 10)"
    )

    @field_validator("permissions")
    @classmethod
    def validate_permissions(cls, v: dict[str, bool]) -> dict[str, bool]:
        """Validate that at least one valid permission is granted."""
        valid_perms = {k: v for k, v in v.items() if k in VALID_PERMISSIONS and v}
        if not valid_perms:
            raise ValueError("At least one valid permission must be granted")
        return valid_perms

    model_config = {"json_schema_extra": {
        "example": {
            "applicant_id": "123e4567-e89b-12d3-a456-426614174000",
            "shared_with": "Acme Corp",
            "shared_with_email": "kyc@acme.com",
            "purpose": "Employment verification",
            "permissions": {
                "basic_info": True,
                "id_verification": True,
                "screening": True
            },
            "expires_days": 30,
            "max_uses": 1
        }
    }}


class ShareTokenRevoke(BaseModel):
    """Request to revoke a share token."""

    reason: Optional[str] = Field(None, max_length=255, description="Reason for revocation")


# ===========================================
# RESPONSE SCHEMAS
# ===========================================
class ShareTokenResponse(BaseModel):
    """Response after generating a new share token."""

    token: str = Field(..., description="The share token (shown only once)")
    token_id: UUID = Field(..., description="Token UUID for management")
    token_prefix: str = Field(..., description="First 8 chars for identification")
    expires_at: datetime = Field(..., description="When the token expires")
    max_uses: int = Field(..., description="Maximum allowed uses")
    permissions: dict[str, bool] = Field(..., description="Granted permissions")
    shared_with: str = Field(..., description="Recipient name")

    share_url: Optional[str] = Field(None, description="Full URL for sharing (optional)")

    model_config = {"from_attributes": True}


class ShareTokenListItem(BaseModel):
    """Token item in list response (without actual token)."""

    id: UUID
    token_prefix: str
    shared_with: str
    shared_with_email: Optional[str]
    purpose: Optional[str]
    permissions: dict[str, bool]
    expires_at: datetime
    max_uses: int
    use_count: int
    uses_remaining: int
    status: str  # active, expired, exhausted, revoked
    revoked_at: Optional[datetime]
    revoked_reason: Optional[str]
    created_at: datetime

    model_config = {"from_attributes": True}


class ShareTokenListResponse(BaseModel):
    """List of share tokens for an applicant."""

    tokens: list[ShareTokenListItem]
    total: int


# ===========================================
# SHARED KYC DATA SCHEMAS
# ===========================================
class SharedKYCDataResponse(BaseModel):
    """Filtered applicant data returned when verifying a token."""

    # Always included
    applicant_id: UUID
    verification_status: str
    verified_at: Optional[datetime]

    # Basic info (if permitted)
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    date_of_birth: Optional[str] = None

    # ID verification (if permitted)
    id_type: Optional[str] = None
    id_number: Optional[str] = None
    id_country: Optional[str] = None
    id_verified: Optional[bool] = None

    # Address (if permitted)
    address: Optional[dict[str, Any]] = None

    # Screening (if permitted)
    screening_clear: Optional[bool] = None
    screening_checked_at: Optional[datetime] = None
    has_pep: Optional[bool] = None
    has_sanctions: Optional[bool] = None

    # Documents (if permitted)
    documents: Optional[list[dict[str, Any]]] = None

    # Metadata
    token_permissions: dict[str, bool] = Field(default_factory=dict)
    uses_remaining: int = Field(default=0)


class VerifyTokenRequest(BaseModel):
    """Request to verify a share token."""

    token: str = Field(..., min_length=20, description="The share token to verify")


# ===========================================
# ACCESS HISTORY SCHEMAS
# ===========================================
class AccessLogEntry(BaseModel):
    """Single access log entry."""

    id: UUID
    token_prefix: str
    shared_with: str
    requester_ip: Optional[str]
    requester_domain: Optional[str]
    accessed_at: datetime
    success: bool
    failure_reason: Optional[str]
    accessed_permissions: list[str]

    model_config = {"from_attributes": True}


class AccessHistoryResponse(BaseModel):
    """Access history for an applicant's shared tokens."""

    logs: list[AccessLogEntry]
    total: int


# ===========================================
# PERMISSION INFO SCHEMA
# ===========================================
class PermissionInfo(BaseModel):
    """Information about a single permission."""

    key: str
    name: str
    description: str


class AvailablePermissionsResponse(BaseModel):
    """List of available permissions."""

    permissions: list[PermissionInfo]


# ===========================================
# CONSENT SCHEMAS
# ===========================================
class ConsentRequest(BaseModel):
    """Request confirming user consent for data sharing."""

    applicant_id: UUID
    shared_with: str
    permissions: dict[str, bool]
    consent_confirmed: bool = Field(..., description="Must be true to proceed")

    @field_validator("consent_confirmed")
    @classmethod
    def must_confirm_consent(cls, v: bool) -> bool:
        if not v:
            raise ValueError("Consent must be confirmed to share KYC data")
        return v
