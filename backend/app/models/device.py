"""
Get Clearance - Device Intelligence Models
===========================================
Device fingerprinting and fraud detection models.

Captures device/browser/network data for risk analysis using IPQualityScore.
"""

from datetime import datetime
from typing import TYPE_CHECKING, Any
from uuid import UUID

from sqlalchemy import (
    String, DateTime, Integer, Float, Boolean, Text,
    ForeignKey, Index
)
from sqlalchemy.dialects.postgresql import UUID as PG_UUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.models.base import UUIDMixin, TimestampMixin

if TYPE_CHECKING:
    from app.models.tenant import Tenant
    from app.models.applicant import Applicant


class DeviceFingerprint(Base, UUIDMixin, TimestampMixin):
    """
    Device fingerprint captured during verification session.

    Stores device/browser/network data and IPQualityScore analysis results
    for fraud detection and risk assessment.
    """
    __tablename__ = "device_fingerprints"
    __table_args__ = (
        Index("idx_device_tenant", "tenant_id"),
        Index("idx_device_applicant", "applicant_id"),
        Index("idx_device_session", "session_id"),
        Index("idx_device_ip", "ip_address"),
        Index("idx_device_fingerprint", "fingerprint_hash"),
        Index("idx_device_risk", "risk_level"),
    )

    # Tenant association
    tenant_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("tenants.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Applicant association (optional - device can be captured before applicant exists)
    applicant_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("applicants.id", ondelete="SET NULL"),
        index=True,
    )

    # Session tracking
    session_id: Mapped[str] = mapped_column(String(255), nullable=False)
    fingerprint_hash: Mapped[str | None] = mapped_column(String(255))

    # Device/Browser Information
    ip_address: Mapped[str] = mapped_column(String(45), nullable=False)  # IPv6 max length
    user_agent: Mapped[str | None] = mapped_column(Text)
    browser: Mapped[str | None] = mapped_column(String(100))
    browser_version: Mapped[str | None] = mapped_column(String(50))
    operating_system: Mapped[str | None] = mapped_column(String(100))
    os_version: Mapped[str | None] = mapped_column(String(50))
    device_type: Mapped[str | None] = mapped_column(String(50))  # desktop, mobile, tablet
    device_brand: Mapped[str | None] = mapped_column(String(100))
    device_model: Mapped[str | None] = mapped_column(String(100))
    screen_resolution: Mapped[str | None] = mapped_column(String(20))  # e.g., "1920x1080"
    timezone: Mapped[str | None] = mapped_column(String(100))
    language: Mapped[str | None] = mapped_column(String(20))

    # Location (from IP geolocation)
    country_code: Mapped[str | None] = mapped_column(String(2))
    city: Mapped[str | None] = mapped_column(String(255))
    region: Mapped[str | None] = mapped_column(String(255))
    isp: Mapped[str | None] = mapped_column(String(255))
    asn: Mapped[int | None] = mapped_column(Integer)
    organization: Mapped[str | None] = mapped_column(String(255))

    # Network flags (from IPQualityScore)
    is_vpn: Mapped[bool] = mapped_column(Boolean, default=False)
    is_proxy: Mapped[bool] = mapped_column(Boolean, default=False)
    is_tor: Mapped[bool] = mapped_column(Boolean, default=False)
    is_bot: Mapped[bool] = mapped_column(Boolean, default=False)
    is_crawler: Mapped[bool] = mapped_column(Boolean, default=False)
    is_mobile: Mapped[bool] = mapped_column(Boolean, default=False)
    is_datacenter: Mapped[bool] = mapped_column(Boolean, default=False)
    active_vpn: Mapped[bool] = mapped_column(Boolean, default=False)
    active_tor: Mapped[bool] = mapped_column(Boolean, default=False)
    recent_abuse: Mapped[bool] = mapped_column(Boolean, default=False)
    connection_type: Mapped[str | None] = mapped_column(String(50))  # residential, corporate, education, mobile

    # Risk scoring
    fraud_score: Mapped[int | None] = mapped_column(Integer)  # 0-100 from IPQualityScore
    risk_score: Mapped[int | None] = mapped_column(Integer)  # Our calculated score with adjustments
    risk_level: Mapped[str | None] = mapped_column(String(20))  # low, medium, high
    risk_signals: Mapped[dict[str, Any] | None] = mapped_column(JSONB)
    # risk_signals example: {"vpn": true, "proxy": false, "tor": false, "bot": false, "abuse": false}

    # Raw API response (for debugging/auditing)
    ip_check_response: Mapped[dict[str, Any] | None] = mapped_column(JSONB)
    email_check_response: Mapped[dict[str, Any] | None] = mapped_column(JSONB)
    phone_check_response: Mapped[dict[str, Any] | None] = mapped_column(JSONB)
    device_check_response: Mapped[dict[str, Any] | None] = mapped_column(JSONB)

    # Email/Phone validation results (if checked)
    email_valid: Mapped[bool | None] = mapped_column(Boolean)
    email_disposable: Mapped[bool | None] = mapped_column(Boolean)
    email_fraud_score: Mapped[int | None] = mapped_column(Integer)
    phone_valid: Mapped[bool | None] = mapped_column(Boolean)
    phone_fraud_score: Mapped[int | None] = mapped_column(Integer)
    phone_line_type: Mapped[str | None] = mapped_column(String(50))  # landline, mobile, voip

    # Status
    status: Mapped[str] = mapped_column(String(50), default="completed")
    # pending, completed, error
    error_message: Mapped[str | None] = mapped_column(Text)

    # Relationships
    tenant: Mapped["Tenant"] = relationship("Tenant")
    applicant: Mapped["Applicant | None"] = relationship("Applicant")

    def __repr__(self) -> str:
        return f"<DeviceFingerprint {self.id} {self.ip_address} risk={self.risk_level}>"

    @property
    def has_high_risk_signals(self) -> bool:
        """Check if device has high-risk signals."""
        return any([
            self.is_tor,
            self.is_bot,
            self.recent_abuse,
            (self.fraud_score or 0) >= 85,
        ])

    @property
    def has_proxy_signals(self) -> bool:
        """Check if device is using proxy/VPN."""
        return any([
            self.is_vpn,
            self.is_proxy,
            self.active_vpn,
            self.is_datacenter,
        ])

    @property
    def risk_flags(self) -> list[str]:
        """Get list of active risk flags."""
        flags = []
        if self.is_vpn or self.active_vpn:
            flags.append("vpn")
        if self.is_proxy:
            flags.append("proxy")
        if self.is_tor or self.active_tor:
            flags.append("tor")
        if self.is_bot:
            flags.append("bot")
        if self.is_crawler:
            flags.append("crawler")
        if self.is_datacenter:
            flags.append("datacenter")
        if self.recent_abuse:
            flags.append("abuse")
        if self.email_disposable:
            flags.append("disposable_email")
        return flags
