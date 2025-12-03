"""
Get Clearance - Audit Service
==============================
Tamper-evident audit logging for regulatory compliance.

Provides a simple interface to record audit log entries with automatic
chain hashing for tamper evidence. All compliance-relevant actions
(applicant status changes, case resolutions, screening decisions)
should be recorded via this service.
"""

from datetime import datetime
from typing import Any
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.audit import AuditLog, compute_checksum, GENESIS_CHECKSUM


async def record_audit_log(
    db: AsyncSession,
    tenant_id: UUID,
    user_id: UUID | None,
    action: str,
    resource_type: str,
    resource_id: UUID,
    old_values: dict[str, Any] | None = None,
    new_values: dict[str, Any] | None = None,
    extra_data: dict[str, Any] | None = None,
    user_email: str | None = None,
    ip_address: str | None = None,
    user_agent: str | None = None,
) -> AuditLog:
    """
    Create a tamper-evident audit log entry with chain hashing.

    The checksum is computed from the previous entry's checksum plus
    all relevant fields of the new entry, creating an immutable chain.

    Args:
        db: Database session (should be the same transaction as the action)
        tenant_id: Tenant UUID
        user_id: Actor's user ID (from JWT sub)
        action: Action performed (e.g., "applicant.created", "case.resolved")
        resource_type: Type of resource (applicant, case, screening_hit, document)
        resource_id: UUID of the resource
        old_values: Previous state (for updates/deletes)
        new_values: New state (for creates/updates)
        extra_data: Additional context (reason, triggered_by, etc.)
        user_email: Actor's email for display
        ip_address: Client IP address
        user_agent: Client user agent string

    Returns:
        The created AuditLog entry

    Example:
        await record_audit_log(
            db=db,
            tenant_id=user.tenant_id,
            user_id=UUID(user.id),
            action="applicant.created",
            resource_type="applicant",
            resource_id=applicant.id,
            new_values={"email": "john@example.com", "name": "John Doe"},
            user_email=user.email,
            ip_address=request.client.host,
        )
    """
    created_at = datetime.utcnow()

    # Get the most recent audit log entry for this tenant to chain from
    prev_query = (
        select(AuditLog)
        .where(AuditLog.tenant_id == tenant_id)
        .order_by(AuditLog.id.desc())
        .limit(1)
    )
    result = await db.execute(prev_query)
    prev_entry = result.scalar_one_or_none()

    # Get previous checksum for chain integrity
    previous_checksum = prev_entry.checksum if prev_entry else GENESIS_CHECKSUM

    # Compute checksum for this entry
    checksum = compute_checksum(
        previous_checksum=previous_checksum,
        tenant_id=tenant_id,
        user_id=user_id,
        action=action,
        resource_type=resource_type,
        resource_id=resource_id,
        old_values=old_values,
        new_values=new_values,
        created_at=created_at,
    )

    # Create the audit log entry
    audit_entry = AuditLog(
        tenant_id=tenant_id,
        user_id=user_id,
        user_email=user_email,
        ip_address=ip_address,
        user_agent=user_agent,
        action=action,
        resource_type=resource_type,
        resource_id=resource_id,
        old_values=old_values,
        new_values=new_values,
        extra_data=extra_data or {},
        checksum=checksum,
        created_at=created_at,
    )

    db.add(audit_entry)
    await db.flush()  # Get ID without committing (stays in same transaction)

    return audit_entry


async def verify_audit_chain(
    db: AsyncSession,
    tenant_id: UUID,
    limit: int = 1000,
) -> tuple[bool, list[int]]:
    """
    Verify the integrity of the audit log chain for a tenant.

    Recalculates checksums and compares to stored values.
    Any mismatch indicates potential tampering.

    Args:
        db: Database session
        tenant_id: Tenant to verify
        limit: Maximum entries to verify (for performance)

    Returns:
        Tuple of (is_valid, list of invalid entry IDs)

    Example:
        is_valid, invalid_ids = await verify_audit_chain(db, tenant_id)
        if not is_valid:
            alert_security_team(invalid_ids)
    """
    query = (
        select(AuditLog)
        .where(AuditLog.tenant_id == tenant_id)
        .order_by(AuditLog.id.asc())
        .limit(limit)
    )
    result = await db.execute(query)
    entries = result.scalars().all()

    if not entries:
        return True, []

    invalid_ids = []
    previous_checksum = GENESIS_CHECKSUM

    for entry in entries:
        expected_checksum = compute_checksum(
            previous_checksum=previous_checksum,
            tenant_id=entry.tenant_id,
            user_id=entry.user_id,
            action=entry.action,
            resource_type=entry.resource_type,
            resource_id=entry.resource_id,
            old_values=entry.old_values,
            new_values=entry.new_values,
            created_at=entry.created_at,
        )

        if entry.checksum != expected_checksum:
            invalid_ids.append(entry.id)

        previous_checksum = entry.checksum

    return len(invalid_ids) == 0, invalid_ids


# Convenience functions for common audit actions

async def audit_applicant_created(
    db: AsyncSession,
    tenant_id: UUID,
    user_id: UUID,
    applicant_id: UUID,
    applicant_data: dict[str, Any],
    user_email: str | None = None,
    ip_address: str | None = None,
) -> AuditLog:
    """Record applicant creation."""
    return await record_audit_log(
        db=db,
        tenant_id=tenant_id,
        user_id=user_id,
        action="applicant.created",
        resource_type="applicant",
        resource_id=applicant_id,
        new_values=applicant_data,
        user_email=user_email,
        ip_address=ip_address,
    )


async def audit_applicant_updated(
    db: AsyncSession,
    tenant_id: UUID,
    user_id: UUID,
    applicant_id: UUID,
    old_values: dict[str, Any],
    new_values: dict[str, Any],
    user_email: str | None = None,
    ip_address: str | None = None,
) -> AuditLog:
    """Record applicant update."""
    return await record_audit_log(
        db=db,
        tenant_id=tenant_id,
        user_id=user_id,
        action="applicant.updated",
        resource_type="applicant",
        resource_id=applicant_id,
        old_values=old_values,
        new_values=new_values,
        user_email=user_email,
        ip_address=ip_address,
    )


async def audit_applicant_reviewed(
    db: AsyncSession,
    tenant_id: UUID,
    user_id: UUID,
    applicant_id: UUID,
    old_status: str,
    new_status: str,
    notes: str | None = None,
    user_email: str | None = None,
    ip_address: str | None = None,
) -> AuditLog:
    """Record applicant review decision."""
    return await record_audit_log(
        db=db,
        tenant_id=tenant_id,
        user_id=user_id,
        action="applicant.reviewed",
        resource_type="applicant",
        resource_id=applicant_id,
        old_values={"status": old_status},
        new_values={"status": new_status, "notes": notes},
        user_email=user_email,
        ip_address=ip_address,
    )


async def audit_case_created(
    db: AsyncSession,
    tenant_id: UUID,
    user_id: UUID,
    case_id: UUID,
    case_data: dict[str, Any],
    user_email: str | None = None,
    ip_address: str | None = None,
) -> AuditLog:
    """Record case creation."""
    return await record_audit_log(
        db=db,
        tenant_id=tenant_id,
        user_id=user_id,
        action="case.created",
        resource_type="case",
        resource_id=case_id,
        new_values=case_data,
        user_email=user_email,
        ip_address=ip_address,
    )


async def audit_case_resolved(
    db: AsyncSession,
    tenant_id: UUID,
    user_id: UUID,
    case_id: UUID,
    old_status: str,
    resolution: str,
    notes: str | None = None,
    user_email: str | None = None,
    ip_address: str | None = None,
) -> AuditLog:
    """Record case resolution."""
    return await record_audit_log(
        db=db,
        tenant_id=tenant_id,
        user_id=user_id,
        action="case.resolved",
        resource_type="case",
        resource_id=case_id,
        old_values={"status": old_status},
        new_values={"status": "resolved", "resolution": resolution, "notes": notes},
        user_email=user_email,
        ip_address=ip_address,
    )


async def audit_case_note_added(
    db: AsyncSession,
    tenant_id: UUID,
    user_id: UUID,
    case_id: UUID,
    note_id: UUID,
    content_preview: str,
    user_email: str | None = None,
    ip_address: str | None = None,
) -> AuditLog:
    """Record note added to case."""
    return await record_audit_log(
        db=db,
        tenant_id=tenant_id,
        user_id=user_id,
        action="case.note_added",
        resource_type="case",
        resource_id=case_id,
        new_values={"note_id": str(note_id), "content_preview": content_preview[:100]},
        user_email=user_email,
        ip_address=ip_address,
    )


async def audit_screening_hit_resolved(
    db: AsyncSession,
    tenant_id: UUID,
    user_id: UUID,
    hit_id: UUID,
    old_resolution: str,
    new_resolution: str,
    notes: str | None = None,
    is_true_positive: bool = False,
    user_email: str | None = None,
    ip_address: str | None = None,
) -> AuditLog:
    """Record screening hit resolution."""
    return await record_audit_log(
        db=db,
        tenant_id=tenant_id,
        user_id=user_id,
        action="screening_hit.resolved",
        resource_type="screening_hit",
        resource_id=hit_id,
        old_values={"resolution_status": old_resolution},
        new_values={
            "resolution_status": new_resolution,
            "notes": notes,
            "is_true_positive": is_true_positive,
        },
        user_email=user_email,
        ip_address=ip_address,
    )


async def audit_applicant_flagged(
    db: AsyncSession,
    tenant_id: UUID,
    user_id: UUID,
    applicant_id: UUID,
    flag_type: str,
    hit_id: UUID,
    user_email: str | None = None,
    ip_address: str | None = None,
) -> AuditLog:
    """Record applicant flagged due to confirmed screening hit."""
    return await record_audit_log(
        db=db,
        tenant_id=tenant_id,
        user_id=user_id,
        action="applicant.flagged",
        resource_type="applicant",
        resource_id=applicant_id,
        new_values={"flag_type": flag_type, "hit_id": str(hit_id)},
        user_email=user_email,
        ip_address=ip_address,
    )


# =========================================
# GDPR-specific audit functions
# =========================================

async def audit_gdpr_data_exported(
    db: AsyncSession,
    tenant_id: UUID,
    user_id: UUID,
    applicant_id: UUID,
    export_format: str,
    sections_included: list[str],
    user_email: str | None = None,
    ip_address: str | None = None,
) -> AuditLog:
    """Record GDPR Article 15/20 data export (Subject Access Request)."""
    return await record_audit_log(
        db=db,
        tenant_id=tenant_id,
        user_id=user_id,
        action="gdpr.data_exported",
        resource_type="applicant",
        resource_id=applicant_id,
        new_values={
            "export_format": export_format,
            "sections": sections_included,
            "gdpr_articles": ["15", "20"],
        },
        user_email=user_email,
        ip_address=ip_address,
    )


async def audit_gdpr_data_deleted(
    db: AsyncSession,
    tenant_id: UUID,
    user_id: UUID,
    applicant_id: UUID,
    reason: str,
    email_hash: str | None,
    user_email: str | None = None,
    ip_address: str | None = None,
) -> AuditLog:
    """Record GDPR Article 17 data deletion (Right to Erasure)."""
    return await record_audit_log(
        db=db,
        tenant_id=tenant_id,
        user_id=user_id,
        action="gdpr.data_deleted",
        resource_type="applicant",
        resource_id=applicant_id,
        old_values={
            "email_hash": email_hash,
            "deletion_reason": reason,
        },
        new_values=None,
        extra_data={"gdpr_article": "17", "irreversible": True},
        user_email=user_email,
        ip_address=ip_address,
    )


async def audit_consent_recorded(
    db: AsyncSession,
    tenant_id: UUID,
    user_id: UUID | None,
    applicant_id: UUID,
    consent_given: bool,
    consent_ip: str | None = None,
    user_email: str | None = None,
    ip_address: str | None = None,
) -> AuditLog:
    """Record consent given or withdrawn (GDPR Article 6/7)."""
    action = "gdpr.consent_given" if consent_given else "gdpr.consent_withdrawn"
    return await record_audit_log(
        db=db,
        tenant_id=tenant_id,
        user_id=user_id,
        action=action,
        resource_type="applicant",
        resource_id=applicant_id,
        new_values={
            "consent": consent_given,
            "consent_ip": consent_ip,
        },
        extra_data={"gdpr_articles": ["6", "7"]},
        user_email=user_email,
        ip_address=ip_address,
    )


async def audit_legal_hold_set(
    db: AsyncSession,
    tenant_id: UUID,
    user_id: UUID,
    applicant_id: UUID,
    reason: str,
    user_email: str | None = None,
    ip_address: str | None = None,
) -> AuditLog:
    """Record legal hold placed on applicant data."""
    return await record_audit_log(
        db=db,
        tenant_id=tenant_id,
        user_id=user_id,
        action="gdpr.legal_hold_set",
        resource_type="applicant",
        resource_id=applicant_id,
        new_values={"legal_hold": True, "reason": reason},
        user_email=user_email,
        ip_address=ip_address,
    )


async def audit_legal_hold_removed(
    db: AsyncSession,
    tenant_id: UUID,
    user_id: UUID,
    applicant_id: UUID,
    previous_reason: str | None,
    user_email: str | None = None,
    ip_address: str | None = None,
) -> AuditLog:
    """Record legal hold removed from applicant data."""
    return await record_audit_log(
        db=db,
        tenant_id=tenant_id,
        user_id=user_id,
        action="gdpr.legal_hold_removed",
        resource_type="applicant",
        resource_id=applicant_id,
        old_values={"legal_hold": True, "reason": previous_reason},
        new_values={"legal_hold": False},
        user_email=user_email,
        ip_address=ip_address,
    )
