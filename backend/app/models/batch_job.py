"""
Get Clearance - Batch Job Model
================================
Model for tracking background batch processing jobs (AI analysis, bulk operations).
"""

from datetime import datetime
from typing import TYPE_CHECKING, Any
from uuid import UUID

from sqlalchemy import String, DateTime, Integer, ForeignKey, Index
from sqlalchemy.dialects.postgresql import UUID as PG_UUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.models.base import UUIDMixin, TimestampMixin

if TYPE_CHECKING:
    from app.models.tenant import Tenant, User


class BatchJob(Base, UUIDMixin, TimestampMixin):
    """
    Background batch processing job.

    Tracks status and progress of:
    - Batch AI risk analysis
    - Bulk applicant operations
    - Data import/export jobs
    - Report generation
    """
    __tablename__ = "batch_jobs"
    __table_args__ = (
        Index("idx_batch_jobs_tenant_status", "tenant_id", "status"),
        Index("idx_batch_jobs_tenant_type", "tenant_id", "job_type"),
    )

    # Tenant
    tenant_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("tenants.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Job identification
    job_type: Mapped[str] = mapped_column(String(50), nullable=False)
    # Types: risk_analysis, bulk_screening, data_export, report_generation

    # Status tracking
    status: Mapped[str] = mapped_column(String(20), default="pending", nullable=False)
    # Status: pending, processing, completed, failed, cancelled

    # Progress tracking
    progress: Mapped[int] = mapped_column(Integer, default=0, nullable=False)  # 0-100
    total_items: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    processed_items: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    failed_items: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    # Input/output data
    input_data: Mapped[dict[str, Any] | None] = mapped_column(JSONB)
    # input_data: {applicant_ids: [...], options: {...}}

    results: Mapped[list[dict[str, Any]]] = mapped_column(JSONB, default=list)
    # results: [{applicant_id, risk_score, summary, ...}, ...]

    errors: Mapped[list[dict[str, Any]]] = mapped_column(JSONB, default=list)
    # errors: [{item_id, error_message, error_type}, ...]

    # Timing
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    # Who initiated the job
    created_by: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
    )

    # Relationships
    tenant: Mapped["Tenant"] = relationship("Tenant")
    creator: Mapped["User | None"] = relationship("User", foreign_keys=[created_by])

    def __repr__(self) -> str:
        return f"<BatchJob {self.id} {self.job_type} {self.status}>"

    @property
    def is_complete(self) -> bool:
        """Check if job has finished (successfully or not)."""
        return self.status in ("completed", "failed", "cancelled")

    @property
    def is_running(self) -> bool:
        """Check if job is currently processing."""
        return self.status == "processing"

    def update_progress(self, processed: int, failed: int = 0) -> None:
        """Update progress counters and calculate percentage."""
        self.processed_items = processed
        self.failed_items = failed
        if self.total_items > 0:
            self.progress = min(100, int((processed / self.total_items) * 100))

    def mark_started(self) -> None:
        """Mark job as started processing."""
        self.status = "processing"
        self.started_at = datetime.utcnow()

    def mark_completed(self) -> None:
        """Mark job as successfully completed."""
        self.status = "completed"
        self.progress = 100
        self.completed_at = datetime.utcnow()

    def mark_failed(self, error: str | None = None) -> None:
        """Mark job as failed."""
        self.status = "failed"
        self.completed_at = datetime.utcnow()
        if error:
            self.errors.append({
                "type": "job_failure",
                "message": error,
                "timestamp": datetime.utcnow().isoformat(),
            })

    def add_result(self, result: dict) -> None:
        """Add a result to the job."""
        if self.results is None:
            self.results = []
        self.results.append(result)

    def add_error(self, item_id: str, error_message: str, error_type: str = "processing") -> None:
        """Add an error to the job."""
        if self.errors is None:
            self.errors = []
        self.errors.append({
            "item_id": item_id,
            "error_type": error_type,
            "message": error_message,
            "timestamp": datetime.utcnow().isoformat(),
        })
