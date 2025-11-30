"""
Get Clearance - Tenant & User Models
=====================================
Multi-tenant foundation with organization and user management.
"""

from datetime import datetime
from typing import TYPE_CHECKING, Any
from uuid import UUID

from sqlalchemy import String, DateTime, Text, ForeignKey, Index
from sqlalchemy.dialects.postgresql import UUID as PG_UUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.models.base import UUIDMixin, TimestampMixin

if TYPE_CHECKING:
    from app.models.applicant import Applicant


class Tenant(Base, UUIDMixin, TimestampMixin):
    """
    Organization/tenant in the multi-tenant system.
    
    Each tenant has isolated data and users.
    """
    __tablename__ = "tenants"
    
    # Basic info
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    slug: Mapped[str] = mapped_column(String(63), unique=True, nullable=False, index=True)
    
    # Configuration
    settings: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict)
    
    # Billing
    billing_customer_id: Mapped[str | None] = mapped_column(String(255))  # Stripe customer ID
    plan: Mapped[str] = mapped_column(String(50), default="starter")
    
    # Status
    status: Mapped[str] = mapped_column(String(20), default="active")
    
    # Relationships
    users: Mapped[list["User"]] = relationship("User", back_populates="tenant")
    applicants: Mapped[list["Applicant"]] = relationship("Applicant", back_populates="tenant")
    
    def __repr__(self) -> str:
        return f"<Tenant {self.slug}>"


class User(Base, UUIDMixin, TimestampMixin):
    """
    User within a tenant.
    
    Users are scoped to a single tenant (no cross-tenant access).
    Auth is handled by Auth0; this stores local user data.
    """
    __tablename__ = "users"
    __table_args__ = (
        Index("idx_users_tenant_email", "tenant_id", "email", unique=True),
    )
    
    # Tenant relationship
    tenant_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("tenants.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    
    # Auth
    auth0_id: Mapped[str | None] = mapped_column(String(255), unique=True)  # Auth0 user_id
    email: Mapped[str] = mapped_column(String(255), nullable=False)
    
    # Profile
    name: Mapped[str | None] = mapped_column(String(255))
    avatar_url: Mapped[str | None] = mapped_column(String(1000))
    
    # Role & permissions
    role: Mapped[str] = mapped_column(String(50), default="analyst")
    # Roles: admin, reviewer, analyst, viewer
    permissions: Mapped[list[str]] = mapped_column(JSONB, default=list)
    
    # Activity
    last_login_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    
    # Status
    status: Mapped[str] = mapped_column(String(20), default="active")
    
    # Relationships
    tenant: Mapped["Tenant"] = relationship("Tenant", back_populates="users")
    
    def __repr__(self) -> str:
        return f"<User {self.email}>"
    
    def has_permission(self, permission: str) -> bool:
        """Check if user has a specific permission."""
        if self.role == "admin":
            return True
        return permission in self.permissions
    
    def has_role(self, *roles: str) -> bool:
        """Check if user has one of the specified roles."""
        return self.role in roles
