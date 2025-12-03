"""
Get Clearance - Device Intelligence Schemas
============================================
Pydantic models for device intelligence API request/response validation.
"""

from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field


# ===========================================
# REQUEST SCHEMAS
# ===========================================

class DeviceSubmission(BaseModel):
    """Device fingerprint submission from client."""
    # Required fields
    session_id: str = Field(..., max_length=255)
    ip_address: str = Field(..., max_length=45)

    # Optional device data
    fingerprint_hash: str | None = Field(None, max_length=255)
    user_agent: str | None = None
    browser: str | None = Field(None, max_length=100)
    browser_version: str | None = Field(None, max_length=50)
    operating_system: str | None = Field(None, max_length=100)
    os_version: str | None = Field(None, max_length=50)
    device_type: str | None = Field(None, max_length=50)
    device_brand: str | None = Field(None, max_length=100)
    device_model: str | None = Field(None, max_length=100)
    screen_resolution: str | None = Field(None, max_length=20)
    timezone: str | None = Field(None, max_length=100)
    language: str | None = Field(None, max_length=20)

    # Optional applicant association
    applicant_id: UUID | None = None

    # Optional contact info for additional checks
    email: str | None = None
    phone: str | None = None
    phone_country: str | None = Field(None, max_length=2)


class DeviceListParams(BaseModel):
    """Query parameters for listing device fingerprints."""
    risk_level: str | None = None
    session_id: str | None = None
    ip_address: str | None = None
    limit: int = Field(default=50, ge=1, le=100)
    offset: int = Field(default=0, ge=0)


# ===========================================
# RESPONSE SCHEMAS
# ===========================================

class IPCheckResponse(BaseModel):
    """IP reputation check result."""
    ip_address: str
    fraud_score: int
    is_proxy: bool
    is_vpn: bool
    is_tor: bool
    is_bot: bool
    is_datacenter: bool
    is_mobile: bool
    active_vpn: bool
    active_tor: bool
    recent_abuse: bool
    connection_type: str | None
    country_code: str | None
    city: str | None
    region: str | None
    isp: str | None
    asn: int | None


class EmailCheckResponse(BaseModel):
    """Email validation result."""
    email: str
    valid: bool
    disposable: bool
    fraud_score: int
    recent_abuse: bool
    deliverability: str | None


class PhoneCheckResponse(BaseModel):
    """Phone validation result."""
    phone: str
    valid: bool
    fraud_score: int
    line_type: str | None
    carrier: str | None
    active: bool
    risky: bool


class DeviceAnalysisResult(BaseModel):
    """Combined device analysis result."""
    id: UUID
    session_id: str

    # Risk assessment
    risk_score: int
    risk_level: str
    fraud_score: int
    risk_signals: dict[str, bool]
    flags: list[str]

    # IP details
    ip_address: str
    country_code: str | None
    city: str | None
    isp: str | None

    # Network flags
    is_vpn: bool
    is_proxy: bool
    is_tor: bool
    is_bot: bool
    is_datacenter: bool
    is_mobile: bool

    # Device info
    device_type: str | None
    browser: str | None
    operating_system: str | None

    # Optional check results
    ip_check: IPCheckResponse | None = None
    email_check: EmailCheckResponse | None = None
    phone_check: PhoneCheckResponse | None = None

    # Timestamps
    created_at: datetime

    model_config = {"from_attributes": True}


class DeviceSummary(BaseModel):
    """Summary of a device fingerprint for list views."""
    id: UUID
    session_id: str
    applicant_id: UUID | None

    # Risk
    risk_score: int | None
    risk_level: str | None
    fraud_score: int | None
    flags: list[str]

    # Key info
    ip_address: str
    country_code: str | None
    city: str | None

    # Flags
    is_vpn: bool
    is_proxy: bool
    is_tor: bool
    is_bot: bool

    # Device
    device_type: str | None
    browser: str | None
    operating_system: str | None

    created_at: datetime

    model_config = {"from_attributes": True}


class DeviceListResponse(BaseModel):
    """Paginated list of device fingerprints."""
    items: list[DeviceSummary]
    total: int
    limit: int
    offset: int


class DeviceStats(BaseModel):
    """Fraud detection statistics."""
    total_scans: int
    high_risk_count: int
    high_risk_pct: float
    vpn_detected: int
    vpn_pct: float
    bot_detected: int
    bot_pct: float
    tor_detected: int
    tor_pct: float
    avg_fraud_score: float
    period_days: int


class ApplicantDevicesResponse(BaseModel):
    """Device history for an applicant."""
    applicant_id: UUID
    devices: list[DeviceSummary]
    total: int
    has_high_risk: bool
    has_vpn: bool
    has_tor: bool
