"""
Get Clearance - Company Schemas (KYB)
=====================================
Pydantic models for KYB API request/response validation.
"""

from datetime import date, datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, EmailStr, Field, field_validator, HttpUrl


# ===========================================
# BASE SCHEMAS
# ===========================================

class AddressSchema(BaseModel):
    """Address structure used in company profiles."""
    street: str | None = None
    city: str | None = None
    state: str | None = None
    postal_code: str | None = None
    country: str | None = Field(None, max_length=2)  # ISO 3166-1 alpha-2


# ===========================================
# COMPANY REQUEST SCHEMAS
# ===========================================

class CompanyCreate(BaseModel):
    """Create a new company for KYB verification."""
    external_id: str | None = Field(None, max_length=255)

    # Company identification
    legal_name: str = Field(..., max_length=500)
    trading_name: str | None = Field(None, max_length=500)
    registration_number: str | None = Field(None, max_length=100)
    tax_id: str | None = Field(None, max_length=100)
    incorporation_date: date | None = None
    incorporation_country: str | None = Field(None, max_length=2)
    legal_form: str | None = Field(None, max_length=100)

    # Addresses
    registered_address: AddressSchema | None = None
    business_address: AddressSchema | None = None

    # Contact
    website: str | None = Field(None, max_length=500)
    email: EmailStr | None = None
    phone: str | None = Field(None, max_length=50)

    # Business info
    industry: str | None = Field(None, max_length=255)
    description: str | None = None
    employee_count: str | None = Field(None, max_length=50)
    annual_revenue: str | None = Field(None, max_length=50)

    # Metadata
    source: str | None = Field(None, max_length=50)
    extra_data: dict[str, Any] | None = None

    @field_validator("incorporation_country")
    @classmethod
    def validate_country_code(cls, v: str | None) -> str | None:
        if v is not None:
            return v.upper()
        return v


class CompanyUpdate(BaseModel):
    """Update an existing company."""
    legal_name: str | None = Field(None, max_length=500)
    trading_name: str | None = Field(None, max_length=500)
    registration_number: str | None = Field(None, max_length=100)
    tax_id: str | None = Field(None, max_length=100)
    incorporation_date: date | None = None
    incorporation_country: str | None = Field(None, max_length=2)
    legal_form: str | None = Field(None, max_length=100)
    registered_address: AddressSchema | None = None
    business_address: AddressSchema | None = None
    website: str | None = None
    email: EmailStr | None = None
    phone: str | None = None
    industry: str | None = None
    description: str | None = None
    employee_count: str | None = None
    annual_revenue: str | None = None
    extra_data: dict[str, Any] | None = None


class CompanyReview(BaseModel):
    """Submit a review decision for a company."""
    decision: str = Field(..., pattern="^(approved|rejected)$")
    notes: str | None = None
    risk_score_override: int | None = Field(None, ge=0, le=100)


class CompanyListParams(BaseModel):
    """Query parameters for listing companies."""
    status: str | None = None
    risk_level: str | None = None  # low, medium, high
    search: str | None = None  # Search name/registration
    incorporation_country: str | None = None
    has_flags: bool | None = None
    limit: int = Field(default=50, ge=1, le=100)
    offset: int = Field(default=0, ge=0)
    sort_by: str = Field(default="created_at")
    sort_order: str = Field(default="desc", pattern="^(asc|desc)$")


# ===========================================
# BENEFICIAL OWNER REQUEST SCHEMAS
# ===========================================

class BeneficialOwnerCreate(BaseModel):
    """Add a beneficial owner to a company."""
    full_name: str = Field(..., max_length=500)
    date_of_birth: date | None = None
    nationality: str | None = Field(None, max_length=2)
    country_of_residence: str | None = Field(None, max_length=2)

    # ID
    id_type: str | None = Field(None, max_length=50)
    id_number: str | None = Field(None, max_length=100)
    id_country: str | None = Field(None, max_length=2)

    # Ownership
    ownership_percentage: float | None = Field(None, ge=0, le=100)
    ownership_type: str = Field(default="direct", pattern="^(direct|indirect|control)$")
    voting_rights_percentage: float | None = Field(None, ge=0, le=100)

    # Roles
    is_director: bool = False
    is_shareholder: bool = False
    is_signatory: bool = False
    is_legal_representative: bool = False
    role_title: str | None = Field(None, max_length=255)

    @field_validator("nationality", "country_of_residence", "id_country")
    @classmethod
    def validate_country_code(cls, v: str | None) -> str | None:
        if v is not None:
            return v.upper()
        return v


class BeneficialOwnerUpdate(BaseModel):
    """Update a beneficial owner."""
    full_name: str | None = Field(None, max_length=500)
    date_of_birth: date | None = None
    nationality: str | None = None
    country_of_residence: str | None = None
    id_type: str | None = None
    id_number: str | None = None
    id_country: str | None = None
    ownership_percentage: float | None = Field(None, ge=0, le=100)
    ownership_type: str | None = None
    voting_rights_percentage: float | None = Field(None, ge=0, le=100)
    is_director: bool | None = None
    is_shareholder: bool | None = None
    is_signatory: bool | None = None
    is_legal_representative: bool | None = None
    role_title: str | None = None


class LinkUBOToApplicant(BaseModel):
    """Link a UBO to an existing applicant KYC."""
    applicant_id: UUID


# ===========================================
# COMPANY DOCUMENT REQUEST SCHEMAS
# ===========================================

class CompanyDocumentCreate(BaseModel):
    """Request presigned URL for company document upload."""
    document_type: str = Field(..., max_length=100)
    document_subtype: str | None = Field(None, max_length=100)
    file_name: str = Field(..., max_length=500)
    file_type: str | None = Field(None, max_length=100)
    file_size: int | None = None
    issue_date: date | None = None
    expiry_date: date | None = None
    issuing_authority: str | None = Field(None, max_length=255)
    document_number: str | None = Field(None, max_length=100)


class CompanyDocumentVerify(BaseModel):
    """Verify or reject a company document."""
    decision: str = Field(..., pattern="^(verified|rejected)$")
    notes: str | None = None


# ===========================================
# COMPANY RESPONSE SCHEMAS
# ===========================================

class BeneficialOwnerResponse(BaseModel):
    """Beneficial owner details."""
    id: UUID
    company_id: UUID
    applicant_id: UUID | None

    # Person info
    full_name: str
    date_of_birth: date | None
    nationality: str | None
    country_of_residence: str | None

    # Ownership
    ownership_percentage: float | None
    ownership_type: str
    voting_rights_percentage: float | None
    control_percentage: float

    # Roles
    is_director: bool
    is_shareholder: bool
    is_signatory: bool
    is_legal_representative: bool
    role_title: str | None

    # Status
    verification_status: str
    verified_at: datetime | None
    is_verified: bool
    is_linked_to_kyc: bool

    # Screening
    screening_status: str | None
    last_screened_at: datetime | None
    flags: list[str]

    # Timestamps
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class CompanyDocumentResponse(BaseModel):
    """Company document details."""
    id: UUID
    company_id: UUID

    # Document info
    document_type: str
    document_subtype: str | None
    file_name: str
    file_type: str | None
    file_size: int | None

    # Metadata
    issue_date: date | None
    expiry_date: date | None
    issuing_authority: str | None
    document_number: str | None

    # Status
    status: str
    verification_notes: str | None
    verified_at: datetime | None
    is_expired: bool
    is_verified: bool

    # Analysis
    extracted_data: dict[str, Any] | None
    confidence_score: float | None

    # Timestamps
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class CompanySummary(BaseModel):
    """Company summary for list views."""
    id: UUID
    external_id: str | None
    legal_name: str
    trading_name: str | None
    display_name: str
    registration_number: str | None
    incorporation_country: str | None
    legal_form: str | None

    status: str
    risk_level: str | None
    risk_score: int | None
    flags: list[str]

    ubo_count: int
    has_pending_ubos: bool
    has_hits: bool

    source: str | None
    created_at: datetime

    model_config = {"from_attributes": True}


class CompanyDetail(BaseModel):
    """Full company details."""
    id: UUID
    external_id: str | None

    # Identification
    legal_name: str
    trading_name: str | None
    display_name: str
    registration_number: str | None
    tax_id: str | None
    incorporation_date: date | None
    incorporation_country: str | None
    legal_form: str | None

    # Addresses
    registered_address: AddressSchema | None
    business_address: AddressSchema | None

    # Contact
    website: str | None
    email: str | None
    phone: str | None

    # Business info
    industry: str | None
    description: str | None
    employee_count: str | None
    annual_revenue: str | None

    # Status
    status: str
    risk_level: str | None
    risk_score: int | None
    flags: list[str]

    # Screening
    screening_status: str | None
    last_screened_at: datetime | None

    # Review
    reviewed_at: datetime | None
    review_notes: str | None

    # Counts
    ubo_count: int
    has_pending_ubos: bool
    has_hits: bool

    # Metadata
    source: str | None
    extra_data: dict[str, Any] | None

    # Timestamps
    created_at: datetime
    updated_at: datetime

    # Related data
    beneficial_owners: list[BeneficialOwnerResponse] = []
    documents: list[CompanyDocumentResponse] = []

    model_config = {"from_attributes": True}


class CompanyListResponse(BaseModel):
    """Paginated list of companies."""
    items: list[CompanySummary]
    total: int
    limit: int
    offset: int


# ===========================================
# SCREENING RESPONSE SCHEMAS
# ===========================================

class CompanyScreeningResult(BaseModel):
    """Result of company + UBO screening."""
    company_id: UUID
    company_name: str
    company_hits: int
    ubo_hits: int
    total_hits: int
    risk_level: str
    screening_status: str
    screened_at: datetime
    details: dict[str, Any]
