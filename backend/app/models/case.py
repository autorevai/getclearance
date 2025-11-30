"""
Get Clearance - Case Models
============================
Investigation case management models.
"""

from datetime import datetime
from typing import TYPE_CHECKING, Any
from uuid import UUID

from sqlalchemy import (
    String, DateTime, Text, Boolean,
    ForeignKey, Index
)
from sqlalchemy.dialects.postgresql import UUID as PG_UUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.models.base import UUIDMixin, TimestampMixin

if TYPE_CHECKING:
    from app.models.applicant import Applicant
    from app.models.screening import ScreeningHit
    from app.models.tenant import Tenant, User


class Case(Base, UUIDMixin, TimestampMixin):
    """
    Investigation case for compliance review.
    
    Cases are created when hits need investigation or
    manual review is required.
    """
    __tablename__ = "cases"
    __table_args__ = (
        Index("idx_cases_tenant_number", "tenant_id", "case_number", unique=True),
        Index("idx_cases_tenant_status", "tenant_id", "status"),
        Index("idx_cases_assignee", "assignee_id"),
        Index("idx_cases_applicant", "applicant_id"),
        Index("idx_cases_due", "tenant_id", "due_at",
              postgresql_where="status IN ('open', 'in_progress')"),
    )
    
    # Ownership
    tenant_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("tenants.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    
    # Human-readable ID (e.g., CASE-2025-001)
    case_number: Mapped[str] = mapped_column(String(50), nullable=False)
    
    # Subject
    applicant_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("applicants.id", ondelete="SET NULL"),
    )
    company_id: Mapped[UUID | None] = mapped_column(PG_UUID(as_uuid=True))
    screening_hit_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("screening_hits.id", ondelete="SET NULL"),
    )
    
    # Case info
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    type: Mapped[str] = mapped_column(String(50), nullable=False)
    # Types: sanctions, pep, fraud, aml, verification
    priority: Mapped[str] = mapped_column(String(20), default="medium")
    # Priority: critical, high, medium, low
    status: Mapped[str] = mapped_column(String(50), default="open")
    # Status: open, in_progress, pending_info, resolved, escalated, closed
    
    # Assignment
    assignee_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
    )
    escalated_to: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
    )
    
    # Resolution
    resolution: Mapped[str | None] = mapped_column(String(50))
    # Resolution: cleared, confirmed, reported, escalated
    resolution_notes: Mapped[str | None] = mapped_column(Text)
    
    # Source
    source: Mapped[str | None] = mapped_column(String(100))
    # Sources: screening_hit, manual, tm_alert, system
    source_reference: Mapped[str | None] = mapped_column(String(255))
    
    # SLA
    due_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    
    # Timestamps
    opened_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=datetime.utcnow,
    )
    resolved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    
    # Relationships
    applicant: Mapped["Applicant | None"] = relationship("Applicant", back_populates="cases")
    screening_hit: Mapped["ScreeningHit | None"] = relationship("ScreeningHit")
    assignee: Mapped["User | None"] = relationship("User", foreign_keys=[assignee_id])
    escalated_to_user: Mapped["User | None"] = relationship("User", foreign_keys=[escalated_to])
    notes: Mapped[list["CaseNote"]] = relationship(
        "CaseNote", back_populates="case", cascade="all, delete-orphan"
    )
    attachments: Mapped[list["CaseAttachment"]] = relationship(
        "CaseAttachment", back_populates="case", cascade="all, delete-orphan"
    )
    
    def __repr__(self) -> str:
        return f"<Case {self.case_number} {self.status}>"
    
    @property
    def is_open(self) -> bool:
        """Check if case is still open."""
        return self.status in ("open", "in_progress", "pending_info")
    
    @property
    def is_resolved(self) -> bool:
        """Check if case is resolved."""
        return self.status in ("resolved", "closed")
    
    @property
    def is_overdue(self) -> bool:
        """Check if case is past due date."""
        if self.due_at is None:
            return False
        return datetime.utcnow() > self.due_at and self.is_open


class CaseNote(Base, UUIDMixin):
    """
    Note or comment on a case.
    
    Supports both human and AI-generated notes.
    """
    __tablename__ = "case_notes"
    __table_args__ = (
        Index("idx_case_notes_case", "case_id"),
    )
    
    # Parent case
    case_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("cases.id", ondelete="CASCADE"),
        nullable=False,
    )
    
    # Author
    author_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
    )
    
    # Content
    content: Mapped[str] = mapped_column(Text, nullable=False)
    
    # AI metadata
    is_ai_generated: Mapped[bool] = mapped_column(Boolean, default=False)
    ai_model: Mapped[str | None] = mapped_column(String(100))
    ai_citations: Mapped[list[dict[str, Any]]] = mapped_column(JSONB, default=list)
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=datetime.utcnow,
    )
    
    # Relationships
    case: Mapped["Case"] = relationship("Case", back_populates="notes")
    author: Mapped["User | None"] = relationship("User")
    
    def __repr__(self) -> str:
        return f"<CaseNote {self.id}>"


class CaseAttachment(Base, UUIDMixin):
    """
    File attachment on a case.
    """
    __tablename__ = "case_attachments"
    
    # Parent case
    case_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("cases.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    
    # Document reference (optional)
    document_id: Mapped[UUID | None] = mapped_column(PG_UUID(as_uuid=True))
    
    # File info
    file_name: Mapped[str] = mapped_column(String(500), nullable=False)
    storage_path: Mapped[str] = mapped_column(String(1000), nullable=False)
    file_size: Mapped[int | None] = mapped_column()
    mime_type: Mapped[str | None] = mapped_column(String(100))
    
    # Upload info
    uploaded_by: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=datetime.utcnow,
    )
    
    # Relationships
    case: Mapped["Case"] = relationship("Case", back_populates="attachments")
    uploader: Mapped["User | None"] = relationship("User")
    
    def __repr__(self) -> str:
        return f"<CaseAttachment {self.file_name}>"
