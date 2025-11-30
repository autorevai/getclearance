"""
Get Clearance - Audit Log Model
================================
Immutable, chain-hashed audit log for compliance.

The audit log provides:
1. Complete history of all data changes
2. Tamper evidence via chain hashing
3. Regulatory compliance (AML/KYC audit requirements)
"""

from datetime import datetime
from typing import Any
from uuid import UUID
import hashlib
import json

from sqlalchemy import (
    BigInteger, String, DateTime, Text, Index
)
from sqlalchemy.dialects.postgresql import UUID as PG_UUID, JSONB, INET
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class AuditLog(Base):
    """
    Immutable audit log entry.
    
    Uses sequential BigInteger ID for ordering guarantees.
    Chain-hashed for tamper evidence.
    
    This table should NEVER be updated or deleted from.
    Consider partitioning by month for performance at scale.
    """
    __tablename__ = "audit_log"
    __table_args__ = (
        Index("idx_audit_log_tenant_time", "tenant_id", "created_at"),
        Index("idx_audit_log_resource", "resource_type", "resource_id"),
        Index("idx_audit_log_user", "user_id"),
        Index("idx_audit_log_action", "action"),
    )
    
    # Sequential ID for ordering
    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    
    # Tenant
    tenant_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), nullable=False)
    
    # Actor
    user_id: Mapped[UUID | None] = mapped_column(PG_UUID(as_uuid=True))
    user_email: Mapped[str | None] = mapped_column(String(255))
    ip_address: Mapped[str | None] = mapped_column(INET)
    user_agent: Mapped[str | None] = mapped_column(Text)
    
    # Action
    action: Mapped[str] = mapped_column(String(100), nullable=False)
    # Actions: applicant.created, applicant.approved, case.created, document.uploaded, etc.
    
    # Resource
    resource_type: Mapped[str] = mapped_column(String(50), nullable=False)
    # Types: applicant, company, case, document, screening_check, etc.
    resource_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), nullable=False)
    
    # Change details
    old_values: Mapped[dict[str, Any] | None] = mapped_column(JSONB)
    new_values: Mapped[dict[str, Any] | None] = mapped_column(JSONB)
    extra_data: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict)
    # extra_data: Additional context (e.g., reason, triggered_by, etc.)
    
    # Integrity (chain hash)
    checksum: Mapped[str] = mapped_column(String(64), nullable=False)
    # SHA-256 of (previous_checksum | record_json)
    
    # Timestamp
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=datetime.utcnow,
        nullable=False,
    )
    
    def __repr__(self) -> str:
        return f"<AuditLog {self.id} {self.action}>"


def compute_checksum(
    previous_checksum: str,
    tenant_id: UUID,
    user_id: UUID | None,
    action: str,
    resource_type: str,
    resource_id: UUID,
    old_values: dict | None,
    new_values: dict | None,
    created_at: datetime,
) -> str:
    """
    Compute chain hash for audit entry.
    
    The checksum includes:
    - Previous entry's checksum (for chain integrity)
    - All relevant fields of the new entry
    
    Returns:
        SHA-256 hex digest
    """
    payload = {
        "previous": previous_checksum,
        "tenant_id": str(tenant_id),
        "user_id": str(user_id) if user_id else None,
        "action": action,
        "resource_type": resource_type,
        "resource_id": str(resource_id),
        "old_values": old_values,
        "new_values": new_values,
        "created_at": created_at.isoformat(),
    }
    
    # Deterministic JSON serialization
    payload_str = json.dumps(payload, sort_keys=True, default=str)
    
    return hashlib.sha256(payload_str.encode()).hexdigest()


# Genesis checksum for first entry in a tenant
GENESIS_CHECKSUM = "GENESIS"
