"""
Get Clearance - Monitoring Alert Models
========================================
Ongoing AML monitoring alerts for approved applicants.

These alerts are generated when re-screening of monitored applicants
discovers new hits against sanctions/PEP lists.
"""

from datetime import datetime
from typing import TYPE_CHECKING, Any
from uuid import UUID

from sqlalchemy import (
    String, DateTime, Text,
    ForeignKey, Index
)
from sqlalchemy.dialects.postgresql import UUID as PG_UUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.models.base import UUIDMixin, TimestampMixin

if TYPE_CHECKING:
    from app.models.applicant import Applicant
    from app.models.screening import ScreeningCheck
    from app.models.tenant import Tenant, User


class MonitoringAlert(Base, UUIDMixin, TimestampMixin):
    """
    Alert generated when ongoing monitoring finds new hits.

    When an approved applicant with monitoring_enabled=True is re-screened
    and new hits are found (that weren't in previous screening), an alert
    is created for compliance review.
    """
    __tablename__ = "monitoring_alerts"
    __table_args__ = (
        Index("idx_monitoring_alerts_tenant_status", "tenant_id", "status"),
        Index("idx_monitoring_alerts_applicant", "applicant_id"),
        Index("idx_monitoring_alerts_severity", "tenant_id", "severity"),
        Index("idx_monitoring_alerts_open", "tenant_id", "created_at",
              postgresql_where="status IN ('open', 'reviewing')"),
    )

    # Ownership
    tenant_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("tenants.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    applicant_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("applicants.id", ondelete="CASCADE"),
        nullable=False,
    )

    # Alert classification
    alert_type: Mapped[str] = mapped_column(String(50), nullable=False)
    # Types: 'new_hit', 'upgraded_risk', 'list_update', 'reactivation'
    severity: Mapped[str] = mapped_column(String(20), default="medium")
    # Severity: 'critical', 'high', 'medium', 'low'

    # Screening references
    previous_screening_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("screening_checks.id", ondelete="SET NULL"),
    )
    new_screening_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("screening_checks.id", ondelete="CASCADE"),
        nullable=False,
    )

    # New hits details
    new_hits: Mapped[list[dict[str, Any]]] = mapped_column(JSONB, default=list)
    # Format: [
    #   {
    #     "hit_id": "uuid",
    #     "matched_name": "John Smith",
    #     "hit_type": "sanctions",
    #     "confidence": 85.5,
    #     "list_source": "ofac_sdn"
    #   }
    # ]

    # Summary for quick display
    hit_count: Mapped[int] = mapped_column(default=0)
    hit_types: Mapped[list[str]] = mapped_column(JSONB, default=list)
    # e.g., ["sanctions", "pep"]

    # Resolution workflow
    status: Mapped[str] = mapped_column(String(50), default="open")
    # Status: 'open', 'reviewing', 'resolved', 'dismissed', 'escalated'

    resolved_by: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
    )
    resolved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    resolution_notes: Mapped[str | None] = mapped_column(Text)
    resolution_action: Mapped[str | None] = mapped_column(String(50))
    # Actions: 'confirmed_match', 'false_positive', 'requires_review', 'no_action'

    # Escalation
    escalated_to: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
    )
    escalated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    escalation_reason: Mapped[str | None] = mapped_column(Text)

    # Relationships
    applicant: Mapped["Applicant"] = relationship("Applicant", foreign_keys=[applicant_id])
    previous_screening: Mapped["ScreeningCheck | None"] = relationship(
        "ScreeningCheck", foreign_keys=[previous_screening_id]
    )
    new_screening: Mapped["ScreeningCheck"] = relationship(
        "ScreeningCheck", foreign_keys=[new_screening_id]
    )
    resolver: Mapped["User | None"] = relationship("User", foreign_keys=[resolved_by])
    escalated_user: Mapped["User | None"] = relationship("User", foreign_keys=[escalated_to])

    def __repr__(self) -> str:
        return f"<MonitoringAlert {self.id} {self.alert_type} ({self.severity})>"

    @property
    def is_open(self) -> bool:
        """Check if alert is still open."""
        return self.status in ("open", "reviewing")

    @property
    def is_resolved(self) -> bool:
        """Check if alert has been resolved."""
        return self.status in ("resolved", "dismissed")

    @property
    def is_critical(self) -> bool:
        """Check if alert requires immediate attention."""
        return self.severity == "critical" or any(
            ht == "sanctions" for ht in self.hit_types
        )
