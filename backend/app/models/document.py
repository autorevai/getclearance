"""
Get Clearance - Document Models
================================
Document storage and processing models.
"""

from datetime import datetime
from typing import TYPE_CHECKING, Any
from uuid import UUID

from sqlalchemy import String, Integer, Text, DateTime, ForeignKey, Index, Numeric
from sqlalchemy.dialects.postgresql import UUID as PG_UUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.models.base import UUIDMixin, TimestampMixin

if TYPE_CHECKING:
    from app.models.applicant import Applicant, ApplicantStep
    from app.models.tenant import Tenant


class Document(Base, UUIDMixin, TimestampMixin):
    """
    Uploaded document (ID, proof of address, etc.).
    
    Documents are stored in Cloudflare R2 with metadata here.
    """
    __tablename__ = "documents"
    __table_args__ = (
        Index("idx_documents_applicant", "applicant_id"),
        Index("idx_documents_company", "company_id"),
        Index("idx_documents_tenant_type", "tenant_id", "type"),
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
    company_id: Mapped[UUID | None] = mapped_column(PG_UUID(as_uuid=True))  # FK added when companies table exists
    step_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("applicant_steps.id", ondelete="SET NULL"),
    )
    
    # Document info
    type: Mapped[str] = mapped_column(String(100), nullable=False)
    # Types: passport, drivers_license, national_id, utility_bill, bank_statement, etc.
    
    # File info
    file_name: Mapped[str | None] = mapped_column(String(500))
    file_size: Mapped[int | None] = mapped_column(Integer)  # bytes
    mime_type: Mapped[str | None] = mapped_column(String(100))
    storage_path: Mapped[str] = mapped_column(String(1000), nullable=False)
    # Path format: {tenant_id}/{resource_type}/{resource_id}/{document_id}
    
    # Processing status
    status: Mapped[str] = mapped_column(String(50), default="pending")
    # Status: pending, processing, verified, rejected
    
    # OCR & extraction
    ocr_text: Mapped[str | None] = mapped_column(Text)
    ocr_confidence: Mapped[float | None] = mapped_column(Numeric(5, 2))
    extracted_data: Mapped[dict[str, Any] | None] = mapped_column(JSONB)
    # extracted_data: {document_number, expiry_date, issuing_country, mrz, etc.}
    
    # Verification
    verification_checks: Mapped[list[dict[str, Any]]] = mapped_column(JSONB, default=list)
    # verification_checks: [{check, passed, confidence, details}]
    fraud_signals: Mapped[list[dict[str, Any]]] = mapped_column(JSONB, default=list)
    # fraud_signals: [{signal, severity, details}]
    security_features_detected: Mapped[list[str]] = mapped_column(JSONB, default=list)
    # Example: ["hologram", "mrz", "watermark", "microprint"]
    
    # Translation (if non-English)
    original_language: Mapped[str | None] = mapped_column(String(10))
    translated_text: Mapped[str | None] = mapped_column(Text)

    # Biometrics (face matching & liveness)
    face_match_score: Mapped[float | None] = mapped_column(Numeric(5, 2))
    # Face similarity score 0-100 when compared to selfie
    liveness_score: Mapped[float | None] = mapped_column(Numeric(5, 2))
    # Liveness detection confidence 0-100
    biometrics_checked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    # When biometric verification was performed
    verification_result: Mapped[dict[str, Any] | None] = mapped_column(JSONB)
    # Full biometric verification result including quality metrics

    # Timestamps
    uploaded_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=datetime.utcnow,
    )
    processed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    
    # Relationships
    applicant: Mapped["Applicant | None"] = relationship("Applicant", back_populates="documents")
    step: Mapped["ApplicantStep | None"] = relationship("ApplicantStep", back_populates="documents")
    
    def __repr__(self) -> str:
        return f"<Document {self.type} {self.id}>"
    
    @property
    def is_verified(self) -> bool:
        """Check if document is verified."""
        return self.status == "verified"
    
    @property
    def has_fraud_signals(self) -> bool:
        """Check if document has any fraud signals."""
        return len(self.fraud_signals) > 0
    
    @property
    def file_size_mb(self) -> float:
        """Get file size in MB."""
        if self.file_size is None:
            return 0.0
        return self.file_size / (1024 * 1024)
