"""
Get Clearance - Applicant Schemas
==================================
Pydantic models for API request/response validation.
"""

from datetime import date, datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, EmailStr, Field, field_validator


# ===========================================
# BASE SCHEMAS
# ===========================================

class AddressSchema(BaseModel):
    """Address structure used in applicant profiles."""
    street: str | None = None
    city: str | None = None
    state: str | None = None
    postal_code: str | None = None
    country: str | None = Field(None, max_length=3)  # ISO 3166-1 alpha-3


class RiskFactorSchema(BaseModel):
    """Individual risk factor."""
    factor: str
    impact: int  # Points added to risk score
    source: str  # Where this factor came from


# ===========================================
# REQUEST SCHEMAS
# ===========================================

class ApplicantCreate(BaseModel):
    """Create a new applicant."""
    external_id: str | None = Field(None, max_length=255)
    email: EmailStr | None = None
    phone: str | None = Field(None, max_length=50)
    first_name: str | None = Field(None, max_length=255)
    last_name: str | None = Field(None, max_length=255)
    date_of_birth: date | None = None
    nationality: str | None = Field(None, max_length=3)
    country_of_residence: str | None = Field(None, max_length=3)
    address: AddressSchema | None = None
    workflow_id: UUID | None = None
    source: str | None = Field(None, max_length=50)
    
    @field_validator("nationality", "country_of_residence")
    @classmethod
    def validate_country_code(cls, v: str | None) -> str | None:
        if v is not None:
            return v.upper()
        return v


class ApplicantUpdate(BaseModel):
    """Update an existing applicant."""
    email: EmailStr | None = None
    phone: str | None = None
    first_name: str | None = None
    last_name: str | None = None
    date_of_birth: date | None = None
    nationality: str | None = None
    country_of_residence: str | None = None
    address: AddressSchema | None = None
    status: str | None = None


class ApplicantReview(BaseModel):
    """Submit a review decision."""
    decision: str = Field(..., pattern="^(approved|rejected)$")
    notes: str | None = None
    risk_score_override: int | None = Field(None, ge=0, le=100)


class ApplicantListParams(BaseModel):
    """Query parameters for listing applicants."""
    status: str | None = None
    risk_level: str | None = None  # low, medium, high
    search: str | None = None  # Search name/email
    date_from: date | None = None
    date_to: date | None = None
    has_flags: bool | None = None
    limit: int = Field(default=50, ge=1, le=100)
    offset: int = Field(default=0, ge=0)
    sort_by: str = Field(default="created_at")
    sort_order: str = Field(default="desc", pattern="^(asc|desc)$")


# ===========================================
# RESPONSE SCHEMAS
# ===========================================

class ApplicantStepResponse(BaseModel):
    """Applicant verification step."""
    id: UUID
    step_id: str
    step_type: str
    status: str
    data: dict[str, Any] = {}
    verification_result: dict[str, Any] | None = None
    failure_reasons: list[str] = []
    resubmission_count: int = 0
    completed_at: datetime | None = None
    created_at: datetime
    
    model_config = {"from_attributes": True}


class ApplicantSummary(BaseModel):
    """Applicant summary for list views."""
    id: UUID
    external_id: str | None
    email: str | None
    first_name: str | None
    last_name: str | None
    full_name: str
    status: str
    risk_score: int | None
    risk_level: str
    flags: list[str] = []
    source: str | None
    submitted_at: datetime | None
    created_at: datetime
    
    model_config = {"from_attributes": True}


class ApplicantDetail(BaseModel):
    """Full applicant details."""
    id: UUID
    external_id: str | None
    email: str | None
    phone: str | None
    first_name: str | None
    last_name: str | None
    full_name: str
    date_of_birth: date | None
    nationality: str | None
    country_of_residence: str | None
    address: AddressSchema | None
    
    # Workflow
    workflow_id: UUID | None
    workflow_version: int | None
    status: str
    
    # Risk
    risk_score: int | None
    risk_level: str
    risk_factors: list[RiskFactorSchema] = []
    flags: list[str] = []
    
    # Metadata
    source: str | None
    ip_address: str | None
    
    # Timestamps
    submitted_at: datetime | None
    reviewed_at: datetime | None
    sla_due_at: datetime | None
    created_at: datetime
    updated_at: datetime
    
    # Related data
    steps: list[ApplicantStepResponse] = []
    
    model_config = {"from_attributes": True}


class ApplicantListResponse(BaseModel):
    """Paginated list of applicants."""
    items: list[ApplicantSummary]
    total: int
    limit: int
    offset: int


# ===========================================
# STEP SCHEMAS
# ===========================================

class StepComplete(BaseModel):
    """Mark a step as complete."""
    data: dict[str, Any] = {}
    verification_result: dict[str, Any] | None = None


class StepResubmit(BaseModel):
    """Request step resubmission."""
    message: str = Field(..., max_length=1000)
