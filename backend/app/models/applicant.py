"""
Get Clearance - Applicant Models
=================================
KYC applicant and verification step models.

PII Fields Encryption:
- email, phone, first_name, last_name use EncryptedString type
- These fields are encrypted at application level using Fernet (AES-128-CBC)
- email_hash provides a searchable SHA-256 hash for exact lookups
"""

import hashlib
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
from app.models.types import EncryptedString

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
        Index("idx_applicants_tenant_email_hash", "tenant_id", "email_hash"),
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

    # Personal info (ENCRYPTED at application level via Fernet/AES-128-CBC)
    # Note: Encrypted values are longer than plaintext, hence larger column sizes
    email: Mapped[str | None] = mapped_column(EncryptedString(512))
    email_hash: Mapped[str | None] = mapped_column(String(64))  # SHA-256 for lookups
    phone: Mapped[str | None] = mapped_column(EncryptedString(256))
    first_name: Mapped[str | None] = mapped_column(EncryptedString(512))
    last_name: Mapped[str | None] = mapped_column(EncryptedString(512))
    date_of_birth: Mapped[date | None] = mapped_column(Date)

    # Non-PII fields - not encrypted
    nationality: Mapped[str | None] = mapped_column(String(3))  # ISO 3166-1 alpha-3
    country_of_residence: Mapped[str | None] = mapped_column(String(3))
    address: Mapped[dict[str, Any] | None] = mapped_column(JSONB)
    # address: {street, city, state, postal_code, country}
    # Note: Consider encrypting address if storing full street addresses
    
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

    # GDPR & Compliance
    legal_hold: Mapped[bool] = mapped_column(default=False)
    legal_hold_reason: Mapped[str | None] = mapped_column(String(500))
    legal_hold_set_by: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
    )
    legal_hold_set_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    # Consent tracking (GDPR Article 6/7)
    consent_given: Mapped[bool] = mapped_column(default=False)
    consent_given_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    consent_ip_address: Mapped[str | None] = mapped_column(String(45))  # IPv4 or IPv6
    consent_withdrawn_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    # Data retention
    retention_expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    
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

    def set_email(self, email: str | None) -> None:
        """
        Set email and update the searchable hash.

        Use this method instead of directly setting self.email
        to ensure the hash stays in sync.

        Args:
            email: Email address to set, or None to clear
        """
        self.email = email
        if email:
            # Store lowercase hash for case-insensitive lookups
            self.email_hash = hashlib.sha256(email.lower().encode()).hexdigest()
        else:
            self.email_hash = None

    @staticmethod
    def hash_email(email: str) -> str:
        """
        Generate SHA-256 hash of email for lookups.

        Use this for querying by email:
            email_hash = Applicant.hash_email("user@example.com")
            query.where(Applicant.email_hash == email_hash)

        Args:
            email: Email address to hash

        Returns:
            SHA-256 hex digest of lowercase email
        """
        return hashlib.sha256(email.lower().encode()).hexdigest()


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
