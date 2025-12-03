"""
Get Clearance - Audit Log Schemas
==================================
Pydantic models for audit log API request/response validation.
"""

from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field


# ===========================================
# RESPONSE SCHEMAS
# ===========================================

class AuditLogResponse(BaseModel):
    """Single audit log entry response."""
    id: int
    tenant_id: UUID
    user_id: UUID | None = None
    user_email: str | None = None
    ip_address: str | None = None
    action: str
    resource_type: str
    resource_id: UUID
    old_values: dict[str, Any] | None = None
    new_values: dict[str, Any] | None = None
    extra_data: dict[str, Any] = {}
    checksum: str
    created_at: datetime

    model_config = {"from_attributes": True}


class AuditLogListResponse(BaseModel):
    """Paginated list of audit log entries."""
    items: list[AuditLogResponse]
    total: int
    limit: int
    offset: int


class AuditLogDetailResponse(AuditLogResponse):
    """Detailed audit log entry with additional context."""
    user_agent: str | None = None
    # Could include resource details if needed
    resource_name: str | None = None


# ===========================================
# FILTER SCHEMAS
# ===========================================

class AuditLogFilters(BaseModel):
    """Filter parameters for audit log queries."""
    resource_type: str | None = Field(None, description="Filter by resource type (applicant, case, document, etc.)")
    resource_id: UUID | None = Field(None, description="Filter by specific resource ID")
    user_id: UUID | None = Field(None, description="Filter by actor user ID")
    action: str | None = Field(None, description="Filter by action type")
    start_date: datetime | None = Field(None, description="Filter entries after this date")
    end_date: datetime | None = Field(None, description="Filter entries before this date")
    search: str | None = Field(None, description="Search in action or user email")


# ===========================================
# VERIFICATION SCHEMAS
# ===========================================

class ChainVerificationResult(BaseModel):
    """Result of audit chain integrity verification."""
    is_valid: bool
    total_entries: int
    entries_verified: int
    invalid_entry_ids: list[int] = []
    verified_at: datetime


# ===========================================
# STATS SCHEMAS
# ===========================================

class AuditLogStats(BaseModel):
    """Statistics about audit log entries."""
    total_entries: int
    entries_today: int
    entries_this_week: int
    entries_this_month: int
    actions_breakdown: dict[str, int] = {}
    resource_types_breakdown: dict[str, int] = {}
    top_users: list[dict[str, Any]] = []
