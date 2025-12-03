"""
Get Clearance - API Key Model
==============================
API key model for tenant API access.
"""

from datetime import datetime
from typing import TYPE_CHECKING, Any
from uuid import UUID

from sqlalchemy import String, DateTime, ForeignKey, Index
from sqlalchemy.dialects.postgresql import UUID as PG_UUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.models.base import UUIDMixin, TimestampMixin

if TYPE_CHECKING:
    from app.models.tenant import Tenant, User


class ApiKey(Base, UUIDMixin, TimestampMixin):
    """
    API key for programmatic access to tenant resources.

    Security:
    - Full key is NEVER stored, only SHA-256 hash
    - Key prefix (first 8 chars) stored for identification
    - Keys can be rotated or revoked
    """

    __tablename__ = "api_keys"
    __table_args__ = (
        Index("idx_api_keys_tenant", "tenant_id"),
        Index("idx_api_keys_key_hash", "key_hash", unique=True),
        Index("idx_api_keys_prefix", "key_prefix"),
    )

    # Tenant ownership
    tenant_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("tenants.id", ondelete="CASCADE"),
        nullable=False,
    )

    # Key identification
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    key_hash: Mapped[str] = mapped_column(String(64), nullable=False, unique=True)
    key_prefix: Mapped[str] = mapped_column(String(12), nullable=False)
    # Prefix format: sk_live_xxxx or sk_test_xxxx

    # Permissions
    permissions: Mapped[list[str]] = mapped_column(JSONB, default=list)
    # Permissions: read:applicants, write:applicants, read:documents, etc.

    # Usage tracking
    last_used_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    last_used_ip: Mapped[str | None] = mapped_column(String(45))

    # Lifecycle
    expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    revoked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    # Audit
    created_by: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
    )

    # Relationships
    tenant: Mapped["Tenant"] = relationship("Tenant")
    creator: Mapped["User | None"] = relationship("User", foreign_keys=[created_by])

    def __repr__(self) -> str:
        return f"<ApiKey {self.name} ({self.key_prefix}...)>"

    @property
    def is_active(self) -> bool:
        """Check if key is active (not revoked or expired)."""
        if self.revoked_at:
            return False
        if self.expires_at and self.expires_at < datetime.utcnow():
            return False
        return True

    @property
    def masked_key(self) -> str:
        """Get masked key for display."""
        return f"{self.key_prefix}{'*' * 24}"
