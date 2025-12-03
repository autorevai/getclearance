"""
Get Clearance - Webhook Models
===============================
Webhook configuration and delivery tracking models.
"""

from datetime import datetime
from typing import TYPE_CHECKING, Any
from uuid import UUID

from sqlalchemy import String, Integer, Boolean, DateTime, Text, ForeignKey, Index
from sqlalchemy.dialects.postgresql import UUID as PG_UUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.models.base import UUIDMixin, TimestampMixin

if TYPE_CHECKING:
    from app.models.tenant import Tenant


class WebhookConfig(Base, UUIDMixin, TimestampMixin):
    """
    Webhook configuration for event notifications.

    Each tenant can have multiple webhook endpoints configured
    to receive notifications about different event types.
    """

    __tablename__ = "webhook_configs"
    __table_args__ = (
        Index("idx_webhook_configs_tenant", "tenant_id"),
        Index("idx_webhook_configs_active", "tenant_id", "active"),
    )

    # Tenant ownership
    tenant_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("tenants.id", ondelete="CASCADE"),
        nullable=False,
    )

    # Configuration
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    url: Mapped[str] = mapped_column(String(2048), nullable=False)
    secret: Mapped[str] = mapped_column(String(64), nullable=False)
    # Secret used for HMAC-SHA256 signature

    # Event subscriptions
    events: Mapped[list[str]] = mapped_column(JSONB, default=list)
    # Events: applicant.created, applicant.approved, applicant.rejected,
    #         screening.completed, screening.hit, document.uploaded, etc.

    # Status
    active: Mapped[bool] = mapped_column(Boolean, default=True)
    failure_count: Mapped[int] = mapped_column(Integer, default=0)
    # Reset on successful delivery, increment on failure
    # Disable after 10 consecutive failures

    # Tracking
    last_success_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    last_failure_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    # Relationships
    tenant: Mapped["Tenant"] = relationship("Tenant")
    deliveries: Mapped[list["WebhookDelivery"]] = relationship(
        "WebhookDelivery", back_populates="webhook", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<WebhookConfig {self.name} ({self.url})>"

    @property
    def is_healthy(self) -> bool:
        """Check if webhook is healthy (active and not failing)."""
        return self.active and self.failure_count < 10

    @property
    def status(self) -> str:
        """Get webhook status string."""
        if not self.active:
            return "paused"
        if self.failure_count >= 10:
            return "failing"
        if self.failure_count > 0:
            return "degraded"
        return "active"


class WebhookDelivery(Base, UUIDMixin):
    """
    Individual webhook delivery attempt.

    Tracks each webhook delivery for debugging and audit purposes.
    """

    __tablename__ = "webhook_deliveries"
    __table_args__ = (
        Index("idx_webhook_deliveries_webhook", "webhook_id"),
        Index("idx_webhook_deliveries_created", "created_at"),
    )

    # Parent webhook
    webhook_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("webhook_configs.id", ondelete="CASCADE"),
        nullable=False,
    )

    # Event details
    event_type: Mapped[str] = mapped_column(String(100), nullable=False)
    payload: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False)

    # Response
    response_code: Mapped[int | None] = mapped_column(Integer)
    response_body: Mapped[str | None] = mapped_column(Text)
    response_time_ms: Mapped[int | None] = mapped_column(Integer)
    # Response time in milliseconds

    # Status
    success: Mapped[bool] = mapped_column(Boolean, default=False)
    error_message: Mapped[str | None] = mapped_column(Text)

    # Timestamp
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=datetime.utcnow,
    )
    delivered_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    # Relationships
    webhook: Mapped["WebhookConfig"] = relationship("WebhookConfig", back_populates="deliveries")

    def __repr__(self) -> str:
        return f"<WebhookDelivery {self.event_type} -> {self.response_code}>"
