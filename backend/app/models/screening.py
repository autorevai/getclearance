"""
Get Clearance - Screening Models
=================================
AML/sanctions/PEP screening check and hit models.
"""

from datetime import date, datetime
from typing import TYPE_CHECKING, Any
from uuid import UUID

from sqlalchemy import (
    String, Integer, Date, DateTime, Text, 
    ForeignKey, Index, ARRAY, Numeric
)
from sqlalchemy.dialects.postgresql import UUID as PG_UUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.models.base import UUIDMixin, TimestampMixin

if TYPE_CHECKING:
    from app.models.applicant import Applicant
    from app.models.tenant import Tenant, User


class ScreeningList(Base, UUIDMixin):
    """
    Screening list version tracking.
    
    Tracks which version of each sanctions/PEP list was used
    for each screening check (critical for compliance audit).
    """
    __tablename__ = "screening_lists"
    __table_args__ = (
        Index("idx_screening_lists_source_version", "source", "version_id", unique=True),
    )
    
    # List identification
    source: Mapped[str] = mapped_column(String(100), nullable=False)
    # Sources: ofac_sdn, eu_consolidated, un_sc, opensanctions, etc.
    version_id: Mapped[str] = mapped_column(String(100), nullable=False)
    # Version format: OFAC-2025-11-27
    list_type: Mapped[str] = mapped_column(String(50), nullable=False)
    # Types: sanctions, pep, adverse_media
    
    # Metadata
    entity_count: Mapped[int | None] = mapped_column(Integer)
    published_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    fetched_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=datetime.utcnow,
    )
    checksum: Mapped[str | None] = mapped_column(String(64))
    
    # Relationships
    hits: Mapped[list["ScreeningHit"]] = relationship("ScreeningHit", back_populates="list")
    
    def __repr__(self) -> str:
        return f"<ScreeningList {self.source} {self.version_id}>"


class ScreeningCheck(Base, UUIDMixin, TimestampMixin):
    """
    Individual screening check run against an applicant/company.
    
    A check may produce multiple hits that need resolution.
    """
    __tablename__ = "screening_checks"
    __table_args__ = (
        Index("idx_screening_checks_applicant", "applicant_id"),
        Index("idx_screening_checks_company", "company_id"),
        Index("idx_screening_checks_tenant_status", "tenant_id", "status"),
    )
    
    # Ownership
    tenant_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("tenants.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    applicant_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("applicants.id", ondelete="CASCADE"),
    )
    company_id: Mapped[UUID | None] = mapped_column(PG_UUID(as_uuid=True))
    
    # What was screened
    entity_type: Mapped[str] = mapped_column(String(20), nullable=False)
    # Types: individual, company
    screened_name: Mapped[str] = mapped_column(String(500), nullable=False)
    screened_dob: Mapped[date | None] = mapped_column(Date)
    screened_country: Mapped[str | None] = mapped_column(String(3))
    
    # Check configuration
    check_types: Mapped[list[str]] = mapped_column(ARRAY(String(50)), nullable=False)
    # Types: sanctions, pep, adverse_media
    
    # Results
    status: Mapped[str] = mapped_column(String(50), default="pending")
    # Status: pending, clear, hit, error
    hit_count: Mapped[int] = mapped_column(Integer, default=0)
    
    # Timestamps
    started_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=datetime.utcnow,
    )
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    
    # Relationships
    applicant: Mapped["Applicant | None"] = relationship("Applicant", back_populates="screening_checks")
    hits: Mapped[list["ScreeningHit"]] = relationship(
        "ScreeningHit", back_populates="check", cascade="all, delete-orphan"
    )
    
    def __repr__(self) -> str:
        return f"<ScreeningCheck {self.screened_name} {self.status}>"
    
    @property
    def is_clear(self) -> bool:
        """Check if screening found no hits."""
        return self.status == "clear"
    
    @property
    def has_unresolved_hits(self) -> bool:
        """Check if there are unresolved hits."""
        return any(h.resolution_status == "pending" for h in self.hits)


class ScreeningHit(Base, UUIDMixin):
    """
    Individual hit from a screening check.
    
    Each hit represents a potential match against a sanctions/PEP list
    that needs to be resolved (confirmed as true match or cleared as false positive).
    """
    __tablename__ = "screening_hits"
    __table_args__ = (
        Index("idx_screening_hits_check", "check_id"),
        Index("idx_screening_hits_resolution", "resolution_status"),
    )
    
    # Parent check
    check_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("screening_checks.id", ondelete="CASCADE"),
        nullable=False,
    )
    
    # Source tracking (CRITICAL for compliance)
    list_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("screening_lists.id", ondelete="SET NULL"),
    )
    list_source: Mapped[str] = mapped_column(String(100), nullable=False)
    list_version_id: Mapped[str] = mapped_column(String(100), nullable=False)
    # Denormalized for query speed and audit trail
    
    # Match details
    hit_type: Mapped[str] = mapped_column(String(50), nullable=False)
    # Types: sanctions, pep, adverse_media
    matched_entity_id: Mapped[str | None] = mapped_column(String(255))
    matched_name: Mapped[str] = mapped_column(String(500), nullable=False)
    confidence: Mapped[float] = mapped_column(Numeric(5, 2), nullable=False)
    # Confidence: 0-100 (fuzzy match score)
    matched_fields: Mapped[list[str]] = mapped_column(ARRAY(String(100)), default=list)
    # Fields: name, dob, country, nationality, etc.
    
    # Raw match data from source
    match_data: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict)
    
    # PEP-specific fields
    pep_tier: Mapped[int | None] = mapped_column(Integer)  # 1, 2, 3, 4
    pep_position: Mapped[str | None] = mapped_column(Text)
    pep_relationship: Mapped[str | None] = mapped_column(String(100))
    # Relationships: direct, family, associate
    
    # Adverse media specific
    article_url: Mapped[str | None] = mapped_column(Text)
    article_title: Mapped[str | None] = mapped_column(Text)
    article_date: Mapped[date | None] = mapped_column(Date)
    categories: Mapped[list[str]] = mapped_column(ARRAY(String(100)), default=list)
    # Categories: fraud, bribery, money_laundering, terrorism, etc.
    
    # Resolution
    resolution_status: Mapped[str] = mapped_column(String(50), default="pending")
    # Status: pending, confirmed_true, confirmed_false
    resolution_notes: Mapped[str | None] = mapped_column(Text)
    resolved_by: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
    )
    resolved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=datetime.utcnow,
    )
    
    # Relationships
    check: Mapped["ScreeningCheck"] = relationship("ScreeningCheck", back_populates="hits")
    list: Mapped["ScreeningList | None"] = relationship("ScreeningList", back_populates="hits")
    resolver: Mapped["User | None"] = relationship("User", foreign_keys=[resolved_by])
    
    def __repr__(self) -> str:
        return f"<ScreeningHit {self.matched_name} ({self.confidence}%)>"
    
    @property
    def is_resolved(self) -> bool:
        """Check if hit has been resolved."""
        return self.resolution_status != "pending"
    
    @property
    def is_true_match(self) -> bool:
        """Check if hit was confirmed as true match."""
        return self.resolution_status == "confirmed_true"
    
    @property
    def is_false_positive(self) -> bool:
        """Check if hit was cleared as false positive."""
        return self.resolution_status == "confirmed_false"
    
    @property
    def confidence_level(self) -> str:
        """Get confidence level category."""
        if self.confidence >= 90:
            return "very_high"
        if self.confidence >= 75:
            return "high"
        if self.confidence >= 50:
            return "medium"
        return "low"
