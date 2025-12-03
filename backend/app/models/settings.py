"""
Get Clearance - Settings Models
================================
Models for tenant settings and team management.
"""

from datetime import datetime
from typing import Any
from uuid import UUID

from sqlalchemy import String, DateTime, Text, ForeignKey, Index, Enum
from sqlalchemy.dialects.postgresql import UUID as PG_UUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship
import enum

from app.database import Base
from app.models.base import UUIDMixin, TimestampMixin


class SettingsCategory(str, enum.Enum):
    """Categories for tenant settings."""
    GENERAL = "general"
    NOTIFICATIONS = "notifications"
    BRANDING = "branding"
    SECURITY = "security"


class TenantSettings(Base, UUIDMixin, TimestampMixin):
    """
    Key-value settings for a tenant.

    Settings are organized by category and stored as JSONB values.
    """
    __tablename__ = "tenant_settings"
    __table_args__ = (
        Index("idx_tenant_settings_lookup", "tenant_id", "category", "key", unique=True),
    )

    # Tenant relationship
    tenant_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("tenants.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Setting identification
    category: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default=SettingsCategory.GENERAL.value,
    )
    key: Mapped[str] = mapped_column(String(100), nullable=False)

    # Setting value (JSONB for flexibility)
    value: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict)

    # Audit trail
    updated_by: Mapped[UUID | None] = mapped_column(PG_UUID(as_uuid=True))

    def __repr__(self) -> str:
        return f"<TenantSettings {self.category}/{self.key}>"


class TeamInvitationStatus(str, enum.Enum):
    """Status of a team invitation."""
    PENDING = "pending"
    ACCEPTED = "accepted"
    EXPIRED = "expired"
    CANCELLED = "cancelled"


class TeamInvitation(Base, UUIDMixin, TimestampMixin):
    """
    Team member invitation.

    Invitations expire after a configurable period (default 7 days).
    """
    __tablename__ = "team_invitations"
    __table_args__ = (
        Index("idx_team_invitations_tenant_email", "tenant_id", "email"),
    )

    # Tenant relationship
    tenant_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("tenants.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Invitation details
    email: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[str] = mapped_column(String(50), default="analyst")

    # Invitation lifecycle
    status: Mapped[str] = mapped_column(
        String(20),
        default=TeamInvitationStatus.PENDING.value,
    )
    invited_by: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    invited_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=datetime.utcnow,
    )
    accepted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    expires_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )

    # Token for invitation link (hashed)
    token_hash: Mapped[str | None] = mapped_column(String(255))

    def __repr__(self) -> str:
        return f"<TeamInvitation {self.email} ({self.status})>"

    @property
    def is_expired(self) -> bool:
        """Check if invitation has expired."""
        return datetime.utcnow() > self.expires_at

    @property
    def is_valid(self) -> bool:
        """Check if invitation is still valid (pending and not expired)."""
        return self.status == TeamInvitationStatus.PENDING.value and not self.is_expired
