"""
Get Clearance - Applicant Models
=================================
KYC applicant and verification step models.
"""

from datetime import date, datetime
from typing import TYPE_CHECKING, Any
from uuid import UUID

from sqlalchemy import (
    String, Date, DateTime, Integer, Text, 
    ForeignKey, Index, ARRAY
)
from sqlalchemy.dialects.postgresql import UUID as PG_UUID, JSONB, INET
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.models.base import UUIDMixin, TimestampMixin, TenantMixin

if TYPE_CHECKING:
    from app.models.tenant import Tenant, User
    from app.models.document import Document
    from app.models.screening import ScreeningCheck
    from app.models.case import Case


class Applicant(Base, UUIDMixin, TimestampMixin):
    """
    Individual applicant going through KYC verification.
    
    Represents a person submitting identity verification.
    """
    __tablename__ = "applicants"
    __table_args__ = (
        Index("idx_applicants_tenant_external", "tenant_id", "external_id", unique=True),
        Index("idx_applicants_tenant_status", "tenant_id", "status"),
        Index("idx_applicants_tenant_email", "tenant_id", "email"),
        Index("idx_applicants_tenant_risk", "tenant_id", "risk_score"),
        Index("idx_applicants_sla", "tenant_id", "sla_due_at",
              postgresql_where="status IN ('pending', 'in_progress', 'review')"),
    )
    
    # Tenant
    tenant_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("tenants.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    
    # Customer reference
    external_id: Mapped[str | None] = mapped_column(String(255))
    
    # Personal info (encrypted at rest via PostgreSQL)
    email: Mapped[str | None] = mapped_column(String(255))
    phone: Mapped[str | None] = mapped_column(String(50))
    first_name: Mapped[str | None] = mapped_column(String(255))
    last_name: Mapped[str | None] = mapped_column(String(255))
    date_of_birth: Mapped[date | None] = mapped_column(Date)
    nationality: Mapped[str | None] = mapped_column(String(3))  # ISO 3166-1 alpha-3
    country_of_residence: Mapped[str | None] = mapped_column(String(3))
    address: Mapped[dict[str, Any] | None] = mapped_column(JSONB)
    # address: {street, city, state, postal_code, country}
    
    # Workflow state
    workflow_id: Mapped[UUID | None] = mapped_column(PG_UUID(as_uuid=True))
    workflow_version: Mapped[int | None] = mapped_column(Integer)
    status: Mapped[str] = mapped_column(String(50), default="pending")
    # Status: pending, in_progress, review, approved, rejected, withdrawn
    
    # Risk assessment
    risk_score: Mapped[int | None] = mapped_column(Integer)  # 0-100
    risk_factors: Mapped[list[dict[str, Any]]] = mapped_column(JSONB, default=list)
    # risk_factors: [{factor, impact, source}]
    flags: Mapped[list[str]] = mapped_column(ARRAY(String(50)), default=list)
    # flags: ['pep', 'sanctions', 'adverse_media', 'high_risk_country']
    
    # Metadata
    source: Mapped[str | None] = mapped_column(String(50))  # api, web, mobile, sdk
    ip_address: Mapped[str | None] = mapped_column(INET)
    device_info: Mapped[dict[str, Any] | None] = mapped_column(JSONB)
    
    # Timestamps
    submitted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    reviewed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    reviewed_by: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
    )
    sla_due_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    
    # Relationships
    tenant: Mapped["Tenant"] = relationship("Tenant", back_populates="applicants")
    steps: Mapped[list["ApplicantStep"]] = relationship(
        "ApplicantStep", back_populates="applicant", cascade="all, delete-orphan"
    )
    documents: Mapped[list["Document"]] = relationship(
        "Document", back_populates="applicant", cascade="all, delete-orphan"
    )
    screening_checks: Mapped[list["ScreeningCheck"]] = relationship(
        "ScreeningCheck", back_populates="applicant"
    )
    cases: Mapped[list["Case"]] = relationship("Case", back_populates="applicant")
    reviewer: Mapped["User | None"] = relationship("User", foreign_keys=[reviewed_by])
    
    def __repr__(self) -> str:
        return f"<Applicant {self.id} {self.first_name} {self.last_name}>"
    
    @property
    def full_name(self) -> str:
        """Get full name."""
        parts = [self.first_name, self.last_name]
        return " ".join(p for p in parts if p) or "Unknown"
    
    @property
    def risk_level(self) -> str:
        """Get risk level category from score."""
        if self.risk_score is None:
            return "unknown"
        if self.risk_score <= 30:
            return "low"
        if self.risk_score <= 60:
            return "medium"
        return "high"
    
    @property
    def has_hits(self) -> bool:
        """Check if applicant has any screening hits."""
        return "sanctions" in self.flags or "pep" in self.flags


class ApplicantStep(Base, UUIDMixin, TimestampMixin):
    """
    Individual verification step within an applicant's KYC flow.
    
    Each step represents a discrete verification action (document upload,
    liveness check, etc.) as defined by the workflow.
    """
    __tablename__ = "applicant_steps"
    __table_args__ = (
        Index("idx_applicant_steps_applicant_step", "applicant_id", "step_id", unique=True),
    )
    
    # Parent relationship
    applicant_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("applicants.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    
    # Step identification (matches workflow config)
    step_id: Mapped[str] = mapped_column(String(100), nullable=False)
    step_type: Mapped[str] = mapped_column(String(50), nullable=False)
    # Types: document, liveness, selfie, address, phone, email, screening
    
    # Status
    status: Mapped[str] = mapped_column(String(50), default="pending")
    # Status: pending, in_progress, complete, failed, skipped
    
    # Step-specific data (varies by step type)
    data: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict)
    
    # Verification results
    verification_result: Mapped[dict[str, Any] | None] = mapped_column(JSONB)
    # verification_result: {passed: bool, confidence: float, checks: [...]}
    failure_reasons: Mapped[list[str]] = mapped_column(ARRAY(String(255)), default=list)
    
    # Resubmission
    resubmission_count: Mapped[int] = mapped_column(Integer, default=0)
    resubmission_requested_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    resubmission_message: Mapped[str | None] = mapped_column(Text)
    
    # Completion
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    
    # Relationships
    applicant: Mapped["Applicant"] = relationship("Applicant", back_populates="steps")
    documents: Mapped[list["Document"]] = relationship("Document", back_populates="step")
    
    def __repr__(self) -> str:
        return f"<ApplicantStep {self.step_id} {self.status}>"
    
    @property
    def is_complete(self) -> bool:
        """Check if step is complete."""
        return self.status == "complete"
    
    @property
    def is_failed(self) -> bool:
        """Check if step has failed."""
        return self.status == "failed"
    
    @property
    def can_retry(self) -> bool:
        """Check if step can be retried (max 3 attempts)."""
        return self.resubmission_count < 3
