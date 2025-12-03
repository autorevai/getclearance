"""
Get Clearance - Company Models (KYB)
====================================
Know Your Business (KYB) models for company verification.

Supports:
- Company registration and verification
- Beneficial owner tracking (UBOs)
- Corporate document management
- Company screening against sanctions/PEP lists
"""

from datetime import date, datetime
from typing import TYPE_CHECKING, Any
from uuid import UUID

from sqlalchemy import (
    String, Date, DateTime, Integer, Text, Float, Boolean,
    ForeignKey, Index, ARRAY, CheckConstraint
)
from sqlalchemy.dialects.postgresql import UUID as PG_UUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.models.base import UUIDMixin, TimestampMixin

if TYPE_CHECKING:
    from app.models.tenant import Tenant, User
    from app.models.applicant import Applicant
    from app.models.screening import ScreeningCheck


class Company(Base, UUIDMixin, TimestampMixin):
    """
    Business entity undergoing KYB verification.

    Represents a company/organization that needs verification of its
    legal status, ownership structure, and beneficial owners.
    """
    __tablename__ = "companies"
    __table_args__ = (
        Index("idx_companies_tenant_external", "tenant_id", "external_id", unique=True),
        Index("idx_companies_tenant_status", "tenant_id", "status"),
        Index("idx_companies_registration", "tenant_id", "registration_number"),
        Index("idx_companies_tax_id", "tenant_id", "tax_id"),
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

    # Company identification
    legal_name: Mapped[str] = mapped_column(String(500), nullable=False)
    trading_name: Mapped[str | None] = mapped_column(String(500))
    registration_number: Mapped[str | None] = mapped_column(String(100))
    tax_id: Mapped[str | None] = mapped_column(String(100))
    incorporation_date: Mapped[date | None] = mapped_column(Date)
    incorporation_country: Mapped[str | None] = mapped_column(String(2))  # ISO 3166-1 alpha-2
    legal_form: Mapped[str | None] = mapped_column(String(100))  # LLC, Corp, Ltd, GmbH, etc.

    # Addresses
    registered_address: Mapped[dict[str, Any] | None] = mapped_column(JSONB)
    # {street, city, state, postal_code, country}
    business_address: Mapped[dict[str, Any] | None] = mapped_column(JSONB)
    # {street, city, state, postal_code, country}

    # Contact
    website: Mapped[str | None] = mapped_column(String(500))
    email: Mapped[str | None] = mapped_column(String(255))
    phone: Mapped[str | None] = mapped_column(String(50))

    # Business information
    industry: Mapped[str | None] = mapped_column(String(255))
    description: Mapped[str | None] = mapped_column(Text)
    employee_count: Mapped[str | None] = mapped_column(String(50))  # Range: 1-10, 11-50, etc.
    annual_revenue: Mapped[str | None] = mapped_column(String(50))  # Range: <1M, 1-10M, etc.

    # Status
    status: Mapped[str] = mapped_column(String(50), default="pending")
    # Status: pending, in_review, approved, rejected, withdrawn
    risk_level: Mapped[str | None] = mapped_column(String(20))  # low, medium, high
    risk_score: Mapped[int | None] = mapped_column(Integer)  # 0-100

    # Screening
    screening_status: Mapped[str | None] = mapped_column(String(50))
    # pending, clear, hits_pending, hits_resolved
    last_screened_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    flags: Mapped[list[str]] = mapped_column(ARRAY(String(50)), default=list)
    # flags: ['sanctions', 'pep_ubo', 'adverse_media', 'high_risk_country', 'high_risk_industry']

    # Review
    reviewed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    reviewed_by: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
    )
    review_notes: Mapped[str | None] = mapped_column(Text)

    # Metadata
    source: Mapped[str | None] = mapped_column(String(50))  # api, web, manual
    extra_data: Mapped[dict[str, Any] | None] = mapped_column(JSONB)

    # Relationships
    tenant: Mapped["Tenant"] = relationship("Tenant", back_populates="companies")
    beneficial_owners: Mapped[list["BeneficialOwner"]] = relationship(
        "BeneficialOwner", back_populates="company", cascade="all, delete-orphan"
    )
    documents: Mapped[list["CompanyDocument"]] = relationship(
        "CompanyDocument", back_populates="company", cascade="all, delete-orphan"
    )
    screening_checks: Mapped[list["ScreeningCheck"]] = relationship(
        "ScreeningCheck",
        foreign_keys="ScreeningCheck.company_id",
        back_populates="company"
    )
    reviewer: Mapped["User | None"] = relationship("User", foreign_keys=[reviewed_by])

    def __repr__(self) -> str:
        return f"<Company {self.id} {self.legal_name}>"

    @property
    def display_name(self) -> str:
        """Get display name (trading name if available, else legal name)."""
        return self.trading_name or self.legal_name

    @property
    def ubo_count(self) -> int:
        """Count of beneficial owners."""
        return len(self.beneficial_owners) if self.beneficial_owners else 0

    @property
    def has_pending_ubos(self) -> bool:
        """Check if any UBOs have pending verification."""
        if not self.beneficial_owners:
            return False
        return any(ubo.verification_status == "pending" for ubo in self.beneficial_owners)

    @property
    def has_hits(self) -> bool:
        """Check if company or any UBOs have screening hits."""
        return bool(self.flags) or any(
            ubo.screening_status == "hits"
            for ubo in (self.beneficial_owners or [])
        )


class BeneficialOwner(Base, UUIDMixin, TimestampMixin):
    """
    Beneficial owner (UBO) of a company.

    Represents an individual who owns or controls a significant
    portion of a company (typically >25% ownership or control).
    """
    __tablename__ = "beneficial_owners"
    __table_args__ = (
        Index("idx_ubos_company", "company_id"),
        Index("idx_ubos_applicant", "applicant_id"),
        CheckConstraint(
            "ownership_percentage >= 0 AND ownership_percentage <= 100",
            name="ck_ownership_percentage_range"
        ),
    )

    # Parent company
    company_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("companies.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Link to individual KYC (if verified as an applicant)
    applicant_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("applicants.id", ondelete="SET NULL"),
        index=True,
    )

    # Person identification
    full_name: Mapped[str] = mapped_column(String(500), nullable=False)
    date_of_birth: Mapped[date | None] = mapped_column(Date)
    nationality: Mapped[str | None] = mapped_column(String(2))  # ISO 3166-1 alpha-2
    country_of_residence: Mapped[str | None] = mapped_column(String(2))

    # Government ID (for verification)
    id_type: Mapped[str | None] = mapped_column(String(50))  # passport, national_id, etc.
    id_number: Mapped[str | None] = mapped_column(String(100))
    id_country: Mapped[str | None] = mapped_column(String(2))

    # Ownership details
    ownership_percentage: Mapped[float | None] = mapped_column(Float)
    ownership_type: Mapped[str] = mapped_column(String(50), default="direct")
    # ownership_type: direct, indirect, control
    voting_rights_percentage: Mapped[float | None] = mapped_column(Float)

    # Role in company
    is_director: Mapped[bool] = mapped_column(Boolean, default=False)
    is_shareholder: Mapped[bool] = mapped_column(Boolean, default=False)
    is_signatory: Mapped[bool] = mapped_column(Boolean, default=False)
    is_legal_representative: Mapped[bool] = mapped_column(Boolean, default=False)
    role_title: Mapped[str | None] = mapped_column(String(255))
    # role_title: CEO, Director, Chairman, etc.

    # Verification status
    verification_status: Mapped[str] = mapped_column(String(50), default="pending")
    # pending, verified, failed, linked (linked to applicant KYC)
    verified_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    # Screening
    screening_status: Mapped[str | None] = mapped_column(String(50))
    # pending, clear, hits
    last_screened_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    flags: Mapped[list[str]] = mapped_column(ARRAY(String(50)), default=list)

    # Relationships
    company: Mapped["Company"] = relationship("Company", back_populates="beneficial_owners")
    applicant: Mapped["Applicant | None"] = relationship("Applicant")

    def __repr__(self) -> str:
        return f"<BeneficialOwner {self.id} {self.full_name} ({self.ownership_percentage}%)>"

    @property
    def is_verified(self) -> bool:
        """Check if UBO is verified."""
        return self.verification_status in ("verified", "linked")

    @property
    def is_linked_to_kyc(self) -> bool:
        """Check if UBO is linked to individual KYC."""
        return self.applicant_id is not None

    @property
    def control_percentage(self) -> float:
        """Get effective control percentage (max of ownership or voting)."""
        ownership = self.ownership_percentage or 0
        voting = self.voting_rights_percentage or 0
        return max(ownership, voting)


class CompanyDocument(Base, UUIDMixin, TimestampMixin):
    """
    Document associated with a company for KYB verification.

    Different from applicant documents - these are corporate documents
    like registration certificates, articles of incorporation, etc.
    """
    __tablename__ = "company_documents"
    __table_args__ = (
        Index("idx_company_docs_company", "company_id"),
        Index("idx_company_docs_type", "company_id", "document_type"),
    )

    # Parent company
    company_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("companies.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Document details
    document_type: Mapped[str] = mapped_column(String(100), nullable=False)
    # Types: registration_certificate, articles_of_incorporation,
    #        shareholder_register, board_resolution, proof_of_address,
    #        tax_certificate, bank_statement, annual_report, other
    document_subtype: Mapped[str | None] = mapped_column(String(100))

    # File information
    file_name: Mapped[str] = mapped_column(String(500), nullable=False)
    file_type: Mapped[str | None] = mapped_column(String(100))  # MIME type
    file_size: Mapped[int | None] = mapped_column(Integer)  # bytes
    storage_key: Mapped[str] = mapped_column(String(1000), nullable=False)

    # Document metadata
    issue_date: Mapped[date | None] = mapped_column(Date)
    expiry_date: Mapped[date | None] = mapped_column(Date)
    issuing_authority: Mapped[str | None] = mapped_column(String(255))
    document_number: Mapped[str | None] = mapped_column(String(100))

    # Verification
    status: Mapped[str] = mapped_column(String(50), default="pending")
    # pending, verified, rejected, expired
    verification_notes: Mapped[str | None] = mapped_column(Text)
    verified_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    verified_by: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
    )

    # OCR/Analysis results
    extracted_data: Mapped[dict[str, Any] | None] = mapped_column(JSONB)
    confidence_score: Mapped[float | None] = mapped_column(Float)

    # Relationships
    company: Mapped["Company"] = relationship("Company", back_populates="documents")
    verifier: Mapped["User | None"] = relationship("User", foreign_keys=[verified_by])

    def __repr__(self) -> str:
        return f"<CompanyDocument {self.id} {self.document_type}>"

    @property
    def is_expired(self) -> bool:
        """Check if document has expired."""
        if not self.expiry_date:
            return False
        return self.expiry_date < date.today()

    @property
    def is_verified(self) -> bool:
        """Check if document is verified."""
        return self.status == "verified"
