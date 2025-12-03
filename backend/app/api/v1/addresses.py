"""
Get Clearance - Address Verification API
=========================================
API endpoints for verifying and standardizing addresses.

Endpoints:
    POST /api/v1/addresses/verify              - Verify an address
    POST /api/v1/applicants/{id}/address/verify - Verify and save applicant address
    GET  /api/v1/addresses/countries           - Get country list with risk levels
"""

from datetime import datetime
from typing import Any
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field
from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies import require_permission
from app.models.applicant import Applicant
from app.models.tenant import User
from app.services.address_verification import (
    AddressInput,
    AddressVerificationService,
    StandardizedAddress,
    AddressVerificationStatus,
    address_verification_service,
    verify_applicant_address,
)


router = APIRouter()


# ============================================
# PYDANTIC SCHEMAS
# ============================================

class AddressVerifyRequest(BaseModel):
    """Request to verify an address."""
    street: str = Field(..., min_length=1, max_length=500)
    street_line_2: str | None = Field(None, max_length=500)
    city: str = Field(..., min_length=1, max_length=255)
    state: str | None = Field(None, max_length=100)
    postal_code: str | None = Field(None, max_length=20)
    country: str = Field("US", min_length=2, max_length=2, description="ISO 3166-1 alpha-2 country code")


class AddressVerifyResponse(BaseModel):
    """Response from address verification."""
    # Standardized address
    street_line_1: str
    street_line_2: str | None
    city: str
    state: str
    postal_code: str
    country: str

    # Geocoding
    latitude: float | None
    longitude: float | None

    # Verification result
    verification_status: str
    verification_score: int
    verification_provider: str
    is_deliverable: bool
    address_type: str

    # Risk
    is_high_risk_area: bool
    high_risk_reason: str | None
    risk_score: int

    class Config:
        from_attributes = True


class ApplicantAddressUpdate(BaseModel):
    """Request to verify and update applicant address."""
    street: str = Field(..., min_length=1, max_length=500)
    street_line_2: str | None = Field(None, max_length=500)
    city: str = Field(..., min_length=1, max_length=255)
    state: str | None = Field(None, max_length=100)
    postal_code: str | None = Field(None, max_length=20)
    country: str = Field("US", min_length=2, max_length=2)
    skip_verification: bool = Field(False, description="Skip address verification (use raw input)")


class CountryInfo(BaseModel):
    """Country information with risk level."""
    code: str
    name: str
    risk_level: str
    is_sanctioned: bool


# ============================================
# COUNTRY DATA
# ============================================

COUNTRIES = {
    "US": ("United States", "low", False),
    "GB": ("United Kingdom", "low", False),
    "CA": ("Canada", "low", False),
    "AU": ("Australia", "low", False),
    "DE": ("Germany", "low", False),
    "FR": ("France", "low", False),
    "JP": ("Japan", "low", False),
    "SG": ("Singapore", "low", False),
    "CH": ("Switzerland", "low", False),
    "NL": ("Netherlands", "low", False),
    "SE": ("Sweden", "low", False),
    "NO": ("Norway", "low", False),
    "DK": ("Denmark", "low", False),
    "FI": ("Finland", "low", False),
    "NZ": ("New Zealand", "low", False),
    "IE": ("Ireland", "low", False),
    "BE": ("Belgium", "low", False),
    "AT": ("Austria", "low", False),
    "IT": ("Italy", "low", False),
    "ES": ("Spain", "low", False),
    "PT": ("Portugal", "low", False),
    "LU": ("Luxembourg", "low", False),
    # Medium risk
    "BR": ("Brazil", "medium", False),
    "MX": ("Mexico", "medium", False),
    "CN": ("China", "medium", False),
    "IN": ("India", "medium", False),
    "ZA": ("South Africa", "medium", False),
    "AE": ("United Arab Emirates", "medium", False),
    "SA": ("Saudi Arabia", "medium", False),
    "TR": ("Turkey", "medium", False),
    "TH": ("Thailand", "medium", False),
    "MY": ("Malaysia", "medium", False),
    "ID": ("Indonesia", "medium", False),
    "PH": ("Philippines", "medium", False),
    "VN": ("Vietnam", "medium", False),
    "EG": ("Egypt", "medium", False),
    "NG": ("Nigeria", "medium", False),
    "KE": ("Kenya", "medium", False),
    "CO": ("Colombia", "medium", False),
    "AR": ("Argentina", "medium", False),
    "CL": ("Chile", "medium", False),
    "PL": ("Poland", "medium", False),
    "CZ": ("Czech Republic", "medium", False),
    "HU": ("Hungary", "medium", False),
    "RO": ("Romania", "medium", False),
    "GR": ("Greece", "medium", False),
    # High risk (FATF grey list and elevated risk)
    "AF": ("Afghanistan", "high", False),
    "AL": ("Albania", "high", False),
    "BB": ("Barbados", "high", False),
    "BF": ("Burkina Faso", "high", False),
    "CM": ("Cameroon", "high", False),
    "KY": ("Cayman Islands", "high", False),
    "CD": ("Democratic Republic of Congo", "high", False),
    "GI": ("Gibraltar", "high", False),
    "HT": ("Haiti", "high", False),
    "JM": ("Jamaica", "high", False),
    "JO": ("Jordan", "high", False),
    "ML": ("Mali", "high", False),
    "MZ": ("Mozambique", "high", False),
    "PA": ("Panama", "high", False),
    "PK": ("Pakistan", "high", False),
    "SN": ("Senegal", "high", False),
    "SS": ("South Sudan", "high", False),
    "TZ": ("Tanzania", "high", False),
    "UG": ("Uganda", "high", False),
    "VE": ("Venezuela", "high", False),
    "YE": ("Yemen", "high", False),
    # Critical/Sanctioned (FATF black list + sanctions)
    "KP": ("North Korea", "critical", True),
    "IR": ("Iran", "critical", True),
    "MM": ("Myanmar", "critical", True),
    "RU": ("Russia", "critical", True),
    "BY": ("Belarus", "critical", True),
    "SY": ("Syria", "critical", True),
    "CU": ("Cuba", "critical", True),
}


# ============================================
# ENDPOINTS
# ============================================

@router.post("/verify", response_model=AddressVerifyResponse)
async def verify_address(
    request: AddressVerifyRequest,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_permission("applicants:read")),
):
    """
    Verify and standardize an address.

    Returns the standardized address with verification status and risk score.
    Works with both US and international addresses.
    """
    address_input = AddressInput(
        street=request.street,
        street_line_2=request.street_line_2,
        city=request.city,
        state=request.state,
        postal_code=request.postal_code,
        country=request.country.upper(),
    )

    result = await address_verification_service.verify_address(address_input)
    risk_score = address_verification_service.calculate_address_risk_score(result)

    return AddressVerifyResponse(
        street_line_1=result.street_line_1,
        street_line_2=result.street_line_2,
        city=result.city,
        state=result.state,
        postal_code=result.postal_code,
        country=result.country,
        latitude=result.latitude,
        longitude=result.longitude,
        verification_status=result.verification_status.value,
        verification_score=result.verification_score,
        verification_provider=result.verification_provider,
        is_deliverable=result.is_deliverable,
        address_type=result.address_type.value,
        is_high_risk_area=result.is_high_risk_area,
        high_risk_reason=result.high_risk_reason,
        risk_score=risk_score,
    )


@router.post("/applicants/{applicant_id}/verify", response_model=AddressVerifyResponse)
async def verify_applicant_address_endpoint(
    applicant_id: UUID,
    request: ApplicantAddressUpdate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_permission("applicants:write")),
):
    """
    Verify and update an applicant's address.

    Verifies the address, calculates risk score, and updates the applicant record.
    """
    # Get applicant
    result = await db.execute(
        select(Applicant).where(
            and_(
                Applicant.id == applicant_id,
                Applicant.tenant_id == user.tenant_id,
            )
        )
    )
    applicant = result.scalar_one_or_none()

    if not applicant:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Applicant not found"
        )

    if request.skip_verification:
        # Store raw address without verification
        applicant.address = {
            "street": request.street,
            "street_line_2": request.street_line_2,
            "city": request.city,
            "state": request.state,
            "postal_code": request.postal_code,
            "country": request.country.upper(),
            "verification_status": "skipped",
            "verification_score": 0,
            "verified_at": None,
        }

        await db.commit()

        return AddressVerifyResponse(
            street_line_1=request.street,
            street_line_2=request.street_line_2,
            city=request.city,
            state=request.state or "",
            postal_code=request.postal_code or "",
            country=request.country.upper(),
            latitude=None,
            longitude=None,
            verification_status="skipped",
            verification_score=0,
            verification_provider="none",
            is_deliverable=False,
            address_type="unknown",
            is_high_risk_area=request.country.upper() in AddressVerificationService.HIGH_RISK_COUNTRIES,
            high_risk_reason="Verification skipped" if request.country.upper() in AddressVerificationService.HIGH_RISK_COUNTRIES else None,
            risk_score=0,
        )

    # Verify address
    address_input = AddressInput(
        street=request.street,
        street_line_2=request.street_line_2,
        city=request.city,
        state=request.state,
        postal_code=request.postal_code,
        country=request.country.upper(),
    )

    verification_result = await address_verification_service.verify_address(address_input)
    risk_score = address_verification_service.calculate_address_risk_score(verification_result)

    # Update applicant address
    applicant.address = {
        "street": verification_result.street_line_1,
        "street_line_2": verification_result.street_line_2,
        "city": verification_result.city,
        "state": verification_result.state,
        "postal_code": verification_result.postal_code,
        "country": verification_result.country,
        "latitude": verification_result.latitude,
        "longitude": verification_result.longitude,
        "verification_status": verification_result.verification_status.value,
        "verification_score": verification_result.verification_score,
        "verification_provider": verification_result.verification_provider,
        "is_deliverable": verification_result.is_deliverable,
        "address_type": verification_result.address_type.value,
        "is_high_risk_area": verification_result.is_high_risk_area,
        "high_risk_reason": verification_result.high_risk_reason,
        "risk_score": risk_score,
        "verified_at": datetime.utcnow().isoformat(),
        "original_input": verification_result.original_input,
    }

    # Add address-based risk factor
    if risk_score > 0:
        risk_factors = list(applicant.risk_factors) if applicant.risk_factors else []

        # Remove existing address risk factor
        risk_factors = [rf for rf in risk_factors if rf.get("factor") != "address"]

        # Add new address risk factor
        risk_factors.append({
            "factor": "address",
            "impact": risk_score,
            "source": "address_verification",
            "details": {
                "verification_status": verification_result.verification_status.value,
                "is_high_risk_area": verification_result.is_high_risk_area,
                "country": verification_result.country,
            }
        })

        applicant.risk_factors = risk_factors

        # Update flags if high-risk
        if verification_result.is_high_risk_area:
            flags = list(applicant.flags) if applicant.flags else []
            if "high_risk_country" not in flags:
                flags.append("high_risk_country")
                applicant.flags = flags

    await db.commit()

    return AddressVerifyResponse(
        street_line_1=verification_result.street_line_1,
        street_line_2=verification_result.street_line_2,
        city=verification_result.city,
        state=verification_result.state,
        postal_code=verification_result.postal_code,
        country=verification_result.country,
        latitude=verification_result.latitude,
        longitude=verification_result.longitude,
        verification_status=verification_result.verification_status.value,
        verification_score=verification_result.verification_score,
        verification_provider=verification_result.verification_provider,
        is_deliverable=verification_result.is_deliverable,
        address_type=verification_result.address_type.value,
        is_high_risk_area=verification_result.is_high_risk_area,
        high_risk_reason=verification_result.high_risk_reason,
        risk_score=risk_score,
    )


@router.get("/countries", response_model=list[CountryInfo])
async def list_countries(
    risk_level: str | None = Query(None, description="Filter by risk level: low, medium, high, critical"),
    user: User = Depends(require_permission("applicants:read")),
):
    """
    Get list of countries with risk levels.

    Can filter by risk level (low, medium, high, critical).
    """
    countries = []

    for code, (name, level, sanctioned) in COUNTRIES.items():
        if risk_level and level != risk_level:
            continue

        countries.append(CountryInfo(
            code=code,
            name=name,
            risk_level=level,
            is_sanctioned=sanctioned,
        ))

    # Sort alphabetically by name
    countries.sort(key=lambda c: c.name)

    return countries


@router.get("/status")
async def address_service_status(
    user: User = Depends(require_permission("applicants:read")),
):
    """
    Get address verification service status.

    Returns configuration status for address providers.
    """
    return {
        "smarty_configured": address_verification_service.smarty_configured,
        "is_configured": address_verification_service.is_configured,
        "available_providers": ["smarty"] if address_verification_service.smarty_configured else ["basic"],
        "supported_countries": {
            "us": address_verification_service.smarty_configured,
            "international": address_verification_service.smarty_configured,
        }
    }


@router.get("/high-risk-countries", response_model=list[CountryInfo])
async def list_high_risk_countries(
    user: User = Depends(require_permission("applicants:read")),
):
    """
    Get list of high-risk and sanctioned countries.

    Includes FATF grey/black list countries and sanctioned jurisdictions.
    """
    countries = []

    for code, (name, level, sanctioned) in COUNTRIES.items():
        if level in ["high", "critical"]:
            countries.append(CountryInfo(
                code=code,
                name=name,
                risk_level=level,
                is_sanctioned=sanctioned,
            ))

    countries.sort(key=lambda c: (c.risk_level != "critical", c.name))

    return countries
