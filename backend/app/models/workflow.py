"""
Get Clearance - Workflow Models
================================
Risk-based workflow configuration for automated routing.

Workflow rules allow tenants to configure automatic actions based on:
- Risk level thresholds
- Country restrictions
- Specific screening hits
- Custom conditions

Example rules:
- Auto-approve if risk_level=low and no hits
- Escalate if sanctions hit found
- Manual review if country in high-risk list
"""

from datetime import datetime
from typing import TYPE_CHECKING, Any
from uuid import UUID

from sqlalchemy import (
    String, Integer, DateTime, Text, Boolean,
    ForeignKey, Index
)
from sqlalchemy.dialects.postgresql import UUID as PG_UUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.models.base import UUIDMixin, TimestampMixin

if TYPE_CHECKING:
    from app.models.tenant import Tenant, User


class WorkflowRule(Base, UUIDMixin, TimestampMixin):
    """
    Configurable workflow rule for applicant routing.

    Rules are evaluated in priority order (highest first).
    First matching rule determines the action.
    """
    __tablename__ = "workflow_rules"
    __table_args__ = (
        Index("idx_workflow_rules_tenant_active", "tenant_id", "is_active"),
        Index("idx_workflow_rules_priority", "tenant_id", "priority"),
    )

    # Tenant
    tenant_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("tenants.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Rule identification
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)

    # Conditions (JSONB)
    # Format: {"condition_name": value_or_list}
    # Examples:
    #   {"risk_level": ["high", "critical"]}
    #   {"country": ["IR", "KP", "SY"]}
    #   {"risk_score_min": 60}
    #   {"has_sanctions_hit": true}
    conditions: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict)

    # Action to take when conditions match
    action: Mapped[str] = mapped_column(String(50), nullable=False)
    # Actions: 'auto_approve', 'manual_review', 'auto_reject', 'escalate', 'hold'

    # Optional: assign to specific user/team for review
    assign_to_user_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
    )
    assign_to_role: Mapped[str | None] = mapped_column(String(100))
    # e.g., "compliance_officer", "senior_reviewer"

    # Notification settings
    notify_on_match: Mapped[bool] = mapped_column(Boolean, default=False)
    notification_channels: Mapped[list[str]] = mapped_column(JSONB, default=list)
    # Channels: ["email", "slack", "webhook"]

    # Priority (higher = evaluated first)
    priority: Mapped[int] = mapped_column(Integer, default=0)

    # Status
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    # Metadata
    created_by: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
    )
    last_modified_by: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
    )

    # Statistics (denormalized for quick access)
    times_matched: Mapped[int] = mapped_column(Integer, default=0)
    last_matched_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    # Relationships
    tenant: Mapped["Tenant"] = relationship("Tenant")
    assignee: Mapped["User | None"] = relationship("User", foreign_keys=[assign_to_user_id])
    creator: Mapped["User | None"] = relationship("User", foreign_keys=[created_by])

    def __repr__(self) -> str:
        return f"<WorkflowRule {self.id} {self.name}>"

    @property
    def condition_summary(self) -> str:
        """Get human-readable condition summary."""
        if not self.conditions:
            return "No conditions (always matches)"

        parts = []
        for key, value in self.conditions.items():
            if isinstance(value, list):
                parts.append(f"{key} in {value}")
            else:
                parts.append(f"{key}={value}")

        return " AND ".join(parts)


class RiskAssessmentLog(Base, UUIDMixin):
    """
    Log of risk assessments performed on applicants.

    Tracks assessment history for audit and analysis.
    """
    __tablename__ = "risk_assessment_logs"
    __table_args__ = (
        Index("idx_risk_logs_applicant", "applicant_id"),
        Index("idx_risk_logs_tenant_date", "tenant_id", "created_at"),
    )

    # References
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

    # Assessment results
    overall_level: Mapped[str] = mapped_column(String(20), nullable=False)
    # Values: 'low', 'medium', 'high', 'critical'
    overall_score: Mapped[int] = mapped_column(Integer, nullable=False)
    # Score: 0-100

    # Signals (JSONB array)
    signals: Mapped[list[dict[str, Any]]] = mapped_column(JSONB, default=list)
    # Format: [{"category": "...", "signal_name": "...", "score": 0, "weight": 0.0, ...}]

    # Recommendation
    recommended_action: Mapped[str] = mapped_column(String(50), nullable=False)
    # Actions: 'auto_approve', 'manual_review', 'auto_reject'

    # Applied workflow rule (if any)
    applied_rule_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("workflow_rules.id", ondelete="SET NULL"),
    )
    final_action: Mapped[str | None] = mapped_column(String(50))
    # May differ from recommended if workflow rule overrides

    # Timestamp
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=datetime.utcnow,
        nullable=False,
    )

    # Relationships
    applied_rule: Mapped["WorkflowRule | None"] = relationship("WorkflowRule")

    def __repr__(self) -> str:
        return f"<RiskAssessmentLog {self.id} {self.overall_level} ({self.overall_score})>"


# Default workflow rules to seed for new tenants
DEFAULT_WORKFLOW_RULES = [
    {
        "name": "Auto-approve low risk",
        "description": "Automatically approve applicants with low risk and no screening hits",
        "conditions": {
            "risk_level": ["low"],
            "has_sanctions_hit": False,
            "has_pep_hit": False,
        },
        "action": "auto_approve",
        "priority": 100,
    },
    {
        "name": "Escalate sanctions hits",
        "description": "Escalate any applicant with confirmed sanctions hits to senior compliance",
        "conditions": {
            "has_sanctions_hit": True,
        },
        "action": "escalate",
        "assign_to_role": "senior_compliance",
        "notify_on_match": True,
        "priority": 1000,  # High priority
    },
    {
        "name": "Review high risk",
        "description": "Require manual review for high and critical risk applicants",
        "conditions": {
            "risk_level": ["high", "critical"],
        },
        "action": "manual_review",
        "priority": 500,
    },
    {
        "name": "Review high-risk countries",
        "description": "Manual review for applicants from FATF grey/black list countries",
        "conditions": {
            "country": ["KP", "IR", "SY", "MM", "AF", "YE"],
        },
        "action": "manual_review",
        "notify_on_match": True,
        "priority": 800,
    },
    {
        "name": "Default manual review",
        "description": "Default: require manual review for all other applicants",
        "conditions": {},  # Matches all
        "action": "manual_review",
        "priority": 0,  # Lowest priority
    },
]
