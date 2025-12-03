"""
Get Clearance - Settings Schemas
=================================
Pydantic models for settings API request/response validation.
"""

from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, EmailStr, Field


# ===========================================
# SETTINGS SCHEMAS
# ===========================================

class SettingValue(BaseModel):
    """Single setting key-value pair."""
    key: str
    value: Any


class SettingsUpdate(BaseModel):
    """Update settings for a category."""
    settings: list[SettingValue]


class SettingResponse(BaseModel):
    """Single setting response."""
    id: UUID
    category: str
    key: str
    value: Any
    updated_at: datetime
    updated_by: UUID | None = None

    model_config = {"from_attributes": True}


class SettingsResponse(BaseModel):
    """All settings for a tenant grouped by category."""
    general: dict[str, Any] = {}
    notifications: dict[str, Any] = {}
    branding: dict[str, Any] = {}
    security: dict[str, Any] = {}


# ===========================================
# GENERAL SETTINGS
# ===========================================

class GeneralSettingsUpdate(BaseModel):
    """Update general settings."""
    company_name: str | None = Field(None, max_length=255)
    timezone: str | None = Field(None, max_length=50)
    date_format: str | None = Field(None, max_length=20)
    language: str | None = Field(None, max_length=10)


# ===========================================
# NOTIFICATION SETTINGS
# ===========================================

class NotificationPreferences(BaseModel):
    """Notification preferences."""
    email_new_applicant: bool = True
    email_review_required: bool = True
    email_high_risk_alert: bool = True
    email_screening_hit: bool = True
    email_case_assigned: bool = True
    email_daily_digest: bool = False
    email_weekly_report: bool = True


class NotificationSettingsUpdate(BaseModel):
    """Update notification settings."""
    preferences: NotificationPreferences


# ===========================================
# SECURITY SETTINGS
# ===========================================

class SecuritySettingsUpdate(BaseModel):
    """Update security settings."""
    session_timeout_minutes: int | None = Field(None, ge=5, le=480)
    require_2fa: bool | None = None
    password_min_length: int | None = Field(None, ge=8, le=128)
    password_require_uppercase: bool | None = None
    password_require_number: bool | None = None
    password_require_special: bool | None = None
    allowed_ip_ranges: list[str] | None = None


class SecuritySettingsResponse(BaseModel):
    """Security settings response."""
    session_timeout_minutes: int = 60
    require_2fa: bool = False
    password_min_length: int = 12
    password_require_uppercase: bool = True
    password_require_number: bool = True
    password_require_special: bool = True
    allowed_ip_ranges: list[str] = []


# ===========================================
# BRANDING SETTINGS
# ===========================================

class BrandingSettingsUpdate(BaseModel):
    """Update branding settings."""
    logo_url: str | None = Field(None, max_length=1000)
    primary_color: str | None = Field(None, pattern=r"^#[0-9A-Fa-f]{6}$")
    accent_color: str | None = Field(None, pattern=r"^#[0-9A-Fa-f]{6}$")
    favicon_url: str | None = Field(None, max_length=1000)
    custom_css: str | None = None


class BrandingSettingsResponse(BaseModel):
    """Branding settings response."""
    logo_url: str | None = None
    primary_color: str = "#6366f1"
    accent_color: str = "#818cf8"
    favicon_url: str | None = None
    custom_css: str | None = None


# ===========================================
# TEAM MEMBER SCHEMAS
# ===========================================

class TeamMemberResponse(BaseModel):
    """Team member details."""
    id: UUID
    email: str
    name: str | None = None
    role: str
    avatar_url: str | None = None
    status: str
    last_login_at: datetime | None = None
    created_at: datetime

    model_config = {"from_attributes": True}


class TeamMemberListResponse(BaseModel):
    """List of team members."""
    items: list[TeamMemberResponse]
    total: int


class TeamMemberRoleUpdate(BaseModel):
    """Update a team member's role."""
    role: str = Field(..., pattern="^(admin|reviewer|analyst|viewer)$")


# ===========================================
# TEAM INVITATION SCHEMAS
# ===========================================

class TeamInviteRequest(BaseModel):
    """Request to invite a new team member."""
    email: EmailStr
    role: str = Field(default="analyst", pattern="^(admin|reviewer|analyst|viewer)$")
    message: str | None = Field(None, max_length=500)


class TeamInvitationResponse(BaseModel):
    """Team invitation details."""
    id: UUID
    email: str
    role: str
    status: str
    invited_at: datetime
    expires_at: datetime
    accepted_at: datetime | None = None

    model_config = {"from_attributes": True}


class TeamInvitationListResponse(BaseModel):
    """List of team invitations."""
    items: list[TeamInvitationResponse]
    total: int
