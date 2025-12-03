"""
Get Clearance - KYC Share Models
=================================
Models for portable identity / reusable KYC functionality.

Allows verified applicants to share their KYC data with third parties
using secure, time-limited, revocable tokens.
"""

from datetime import datetime
from typing import TYPE_CHECKING, Any
from uuid import UUID

from sqlalchemy import String, DateTime, Integer, Text, ForeignKey, Index, Boolean
from sqlalchemy.dialects.postgresql import UUID as PG_UUID, JSONB, INET
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.models.base import UUIDMixin, TimestampMixin, TenantMixin

if TYPE_CHECKING:
    from app.models.applicant import Applicant


class KYCShareToken(Base, UUIDMixin, TimestampMixin):
    """
    Token for sharing KYC verification data with third parties.

    Tokens are:
    - Time-limited (configurable expiry, max 90 days)
    - Use-limited (configurable max uses, max 10)
    - Revocable at any time
    - Permission-scoped (control what data is shared)

    The actual token is shown once at creation time.
    Only the SHA-256 hash is stored for verification.
    """
    __tablename__ = "kyc_share_tokens"
    __table_args__ = (
        Index("idx_share_tokens_tenant", "tenant_id"),
        Index("idx_share_tokens_applicant", "applicant_id"),
        Index("idx_share_tokens_hash", "token_hash", unique=True),
        Index("idx_share_tokens_prefix", "token_prefix"),
        Index("idx_share_tokens_active", "tenant_id", "applicant_id",
              postgresql_where="revoked_at IS NULL AND expires_at > now()"),
    )

    # Tenant
    tenant_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("tenants.id", ondelete="CASCADE"),
        nullable=False,
    )

    # Applicant whose KYC is being shared
    applicant_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("applicants.id", ondelete="CASCADE"),
        nullable=False,
    )

    # Token identification
    token_hash: Mapped[str] = mapped_column(String(64), nullable=False, unique=True)  # SHA-256
    token_prefix: Mapped[str] = mapped_column(String(8), nullable=False)  # First 8 chars for display

    # Recipient information
    shared_with: Mapped[str] = mapped_column(String(255), nullable=False)  # Company name or domain
    shared_with_email: Mapped[str | None] = mapped_column(String(255))  # Optional contact email
    purpose: Mapped[str | None] = mapped_column(Text)  # Why sharing (for records)

    # Permissions - what data can be accessed
    permissions: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict)
    # permissions: {
    #   basic_info: bool,      # name, DOB
    #   id_verification: bool, # ID type, number, verification status
    #   address: bool,         # verified address
    #   screening: bool,       # AML screening result
    #   documents: bool,       # access to verified documents
    #   full: bool,           # everything
    # }

    # Limits
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    max_uses: Mapped[int] = mapped_column(Integer, default=1)
    use_count: Mapped[int] = mapped_column(Integer, default=0)

    # Status
    revoked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    revoked_reason: Mapped[str | None] = mapped_column(String(255))

    # Consent tracking
    consent_given_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    consent_ip_address: Mapped[str | None] = mapped_column(String(45))  # IPv4 or IPv6

    # Relationships
    applicant: Mapped["Applicant"] = relationship("Applicant")
    access_logs: Mapped[list["KYCShareAccessLog"]] = relationship(
        "KYCShareAccessLog", back_populates="token", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<KYCShareToken {self.token_prefix}... -> {self.shared_with}>"

    @property
    def is_valid(self) -> bool:
        """Check if token is still valid (not expired, not revoked, uses remaining)."""
        now = datetime.now(self.expires_at.tzinfo)
        return (
            self.revoked_at is None
            and self.expires_at > now
            and self.use_count < self.max_uses
        )

    @property
    def is_expired(self) -> bool:
        """Check if token has expired."""
        now = datetime.now(self.expires_at.tzinfo)
        return self.expires_at <= now

    @property
    def is_revoked(self) -> bool:
        """Check if token has been revoked."""
        return self.revoked_at is not None

    @property
    def uses_remaining(self) -> int:
        """Get remaining uses."""
        return max(0, self.max_uses - self.use_count)

    @property
    def status(self) -> str:
        """Get token status string."""
        if self.is_revoked:
            return "revoked"
        if self.is_expired:
            return "expired"
        if self.use_count >= self.max_uses:
            return "exhausted"
        return "active"

    def has_permission(self, permission: str) -> bool:
        """Check if token grants a specific permission."""
        if self.permissions.get("full"):
            return True
        return self.permissions.get(permission, False)


class KYCShareAccessLog(Base, UUIDMixin):
    """
    Log of access attempts using a KYC share token.

    Records every verification attempt, successful or not,
    for audit and compliance purposes.
    """
    __tablename__ = "kyc_share_access_logs"
    __table_args__ = (
        Index("idx_share_access_token", "token_id"),
        Index("idx_share_access_date", "accessed_at"),
    )

    # Token reference
    token_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("kyc_share_tokens.id", ondelete="CASCADE"),
        nullable=False,
    )

    # Requester information
    requester_ip: Mapped[str | None] = mapped_column(String(45))  # IPv4 or IPv6
    requester_domain: Mapped[str | None] = mapped_column(String(255))
    requester_user_agent: Mapped[str | None] = mapped_column(Text)

    # Access details
    accessed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=datetime.utcnow,
        nullable=False,
    )
    success: Mapped[bool] = mapped_column(Boolean, default=True)
    failure_reason: Mapped[str | None] = mapped_column(String(255))

    # What data was accessed
    accessed_permissions: Mapped[list[str]] = mapped_column(JSONB, default=list)
    # List of permission keys that were accessed

    # Relationships
    token: Mapped["KYCShareToken"] = relationship("KYCShareToken", back_populates="access_logs")

    def __repr__(self) -> str:
        return f"<KYCShareAccessLog {self.token_id} from {self.requester_ip}>"
