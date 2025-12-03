"""
Get Clearance - Audit Log API
==============================
API endpoints for viewing and verifying audit logs.
"""

from datetime import datetime, timedelta
from io import StringIO
import csv
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import StreamingResponse
from sqlalchemy import select, func, or_, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies import TenantDB, AuthenticatedUser, require_permission
from app.models.audit import AuditLog
from app.services.audit import verify_audit_chain
from app.schemas.audit import (
    AuditLogResponse,
    AuditLogListResponse,
    AuditLogDetailResponse,
    ChainVerificationResult,
    AuditLogStats,
)

router = APIRouter()


# ===========================================
# LIST AUDIT LOGS
# ===========================================

@router.get("", response_model=AuditLogListResponse)
async def list_audit_logs(
    db: TenantDB,
    user: Annotated[AuthenticatedUser, Depends(require_permission("read:settings"))],
    resource_type: Annotated[str | None, Query()] = None,
    resource_id: Annotated[UUID | None, Query()] = None,
    user_id: Annotated[UUID | None, Query(alias="actor_id")] = None,
    action: Annotated[str | None, Query()] = None,
    start_date: Annotated[datetime | None, Query()] = None,
    end_date: Annotated[datetime | None, Query()] = None,
    search: Annotated[str | None, Query()] = None,
    limit: Annotated[int, Query(ge=1, le=100)] = 50,
    offset: Annotated[int, Query(ge=0)] = 0,
    sort_order: Annotated[str, Query(pattern="^(asc|desc)$")] = "desc",
):
    """
    List audit log entries with filtering and pagination.

    Filters:
    - resource_type: Filter by resource type (applicant, case, document, screening_hit)
    - resource_id: Filter by specific resource UUID
    - actor_id: Filter by user who performed the action
    - action: Filter by action type (e.g., applicant.created, case.resolved)
    - start_date: Filter entries after this date
    - end_date: Filter entries before this date
    - search: Search in action or user email

    Sorting:
    - sort_order: asc or desc (default: desc - newest first)
    """
    # Base query
    query = select(AuditLog).where(AuditLog.tenant_id == user.tenant_id)
    count_query = select(func.count(AuditLog.id)).where(AuditLog.tenant_id == user.tenant_id)

    # Apply filters
    if resource_type:
        query = query.where(AuditLog.resource_type == resource_type)
        count_query = count_query.where(AuditLog.resource_type == resource_type)

    if resource_id:
        query = query.where(AuditLog.resource_id == resource_id)
        count_query = count_query.where(AuditLog.resource_id == resource_id)

    if user_id:
        query = query.where(AuditLog.user_id == user_id)
        count_query = count_query.where(AuditLog.user_id == user_id)

    if action:
        query = query.where(AuditLog.action == action)
        count_query = count_query.where(AuditLog.action == action)

    if start_date:
        query = query.where(AuditLog.created_at >= start_date)
        count_query = count_query.where(AuditLog.created_at >= start_date)

    if end_date:
        query = query.where(AuditLog.created_at <= end_date)
        count_query = count_query.where(AuditLog.created_at <= end_date)

    if search:
        search_term = f"%{search}%"
        query = query.where(
            or_(
                AuditLog.action.ilike(search_term),
                AuditLog.user_email.ilike(search_term),
            )
        )
        count_query = count_query.where(
            or_(
                AuditLog.action.ilike(search_term),
                AuditLog.user_email.ilike(search_term),
            )
        )

    # Get total count
    total_result = await db.execute(count_query)
    total = total_result.scalar() or 0

    # Apply sorting
    if sort_order == "desc":
        query = query.order_by(AuditLog.id.desc())
    else:
        query = query.order_by(AuditLog.id.asc())

    # Apply pagination
    query = query.offset(offset).limit(limit)

    # Execute query
    result = await db.execute(query)
    entries = result.scalars().all()

    return AuditLogListResponse(
        items=[AuditLogResponse.model_validate(e) for e in entries],
        total=total,
        limit=limit,
        offset=offset,
    )


# ===========================================
# GET SINGLE AUDIT LOG ENTRY
# ===========================================

@router.get("/{entry_id}", response_model=AuditLogDetailResponse)
async def get_audit_log_entry(
    entry_id: int,
    db: TenantDB,
    user: Annotated[AuthenticatedUser, Depends(require_permission("read:settings"))],
):
    """
    Get a single audit log entry by ID.
    """
    query = select(AuditLog).where(
        AuditLog.id == entry_id,
        AuditLog.tenant_id == user.tenant_id,
    )
    result = await db.execute(query)
    entry = result.scalar_one_or_none()

    if not entry:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Audit log entry not found",
        )

    return AuditLogDetailResponse.model_validate(entry)


# ===========================================
# EXPORT AUDIT LOGS
# ===========================================

@router.get("/export/csv")
async def export_audit_logs(
    db: TenantDB,
    user: Annotated[AuthenticatedUser, Depends(require_permission("read:settings"))],
    resource_type: Annotated[str | None, Query()] = None,
    resource_id: Annotated[UUID | None, Query()] = None,
    user_id: Annotated[UUID | None, Query(alias="actor_id")] = None,
    action: Annotated[str | None, Query()] = None,
    start_date: Annotated[datetime | None, Query()] = None,
    end_date: Annotated[datetime | None, Query()] = None,
):
    """
    Export audit logs to CSV format.

    Applies the same filters as the list endpoint.
    Limited to 10,000 entries for performance.
    """
    # Base query
    query = select(AuditLog).where(AuditLog.tenant_id == user.tenant_id)

    # Apply filters
    if resource_type:
        query = query.where(AuditLog.resource_type == resource_type)

    if resource_id:
        query = query.where(AuditLog.resource_id == resource_id)

    if user_id:
        query = query.where(AuditLog.user_id == user_id)

    if action:
        query = query.where(AuditLog.action == action)

    if start_date:
        query = query.where(AuditLog.created_at >= start_date)

    if end_date:
        query = query.where(AuditLog.created_at <= end_date)

    # Order by newest first, limit to 10k
    query = query.order_by(AuditLog.id.desc()).limit(10000)

    result = await db.execute(query)
    entries = result.scalars().all()

    # Generate CSV
    output = StringIO()
    writer = csv.writer(output)

    # Write header
    writer.writerow([
        "ID",
        "Timestamp",
        "User Email",
        "User ID",
        "IP Address",
        "Action",
        "Resource Type",
        "Resource ID",
        "Old Values",
        "New Values",
        "Checksum",
    ])

    # Write data
    for entry in entries:
        writer.writerow([
            entry.id,
            entry.created_at.isoformat(),
            entry.user_email or "",
            str(entry.user_id) if entry.user_id else "",
            entry.ip_address or "",
            entry.action,
            entry.resource_type,
            str(entry.resource_id),
            str(entry.old_values) if entry.old_values else "",
            str(entry.new_values) if entry.new_values else "",
            entry.checksum,
        ])

    output.seek(0)
    timestamp = datetime.utcnow().strftime("%Y-%m-%d")
    filename = f"audit_log_export_{timestamp}.csv"

    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={
            "Content-Disposition": f'attachment; filename="{filename}"',
            "X-Total-Count": str(len(entries)),
        },
    )


# ===========================================
# VERIFY CHAIN INTEGRITY
# ===========================================

@router.get("/verify/chain", response_model=ChainVerificationResult)
async def verify_chain_integrity(
    db: TenantDB,
    user: Annotated[AuthenticatedUser, Depends(require_permission("read:settings"))],
    limit: Annotated[int, Query(ge=100, le=10000)] = 1000,
):
    """
    Verify the integrity of the audit log chain.

    Recalculates checksums and compares to stored values.
    Any mismatch indicates potential tampering.

    Returns verification result with list of any invalid entry IDs.
    """
    # Get total count first
    count_query = select(func.count(AuditLog.id)).where(AuditLog.tenant_id == user.tenant_id)
    count_result = await db.execute(count_query)
    total_entries = count_result.scalar() or 0

    # Verify the chain
    is_valid, invalid_ids = await verify_audit_chain(
        db=db,
        tenant_id=user.tenant_id,
        limit=limit,
    )

    return ChainVerificationResult(
        is_valid=is_valid,
        total_entries=total_entries,
        entries_verified=min(limit, total_entries),
        invalid_entry_ids=invalid_ids,
        verified_at=datetime.utcnow(),
    )


# ===========================================
# GET AUDIT STATS
# ===========================================

@router.get("/stats/summary", response_model=AuditLogStats)
async def get_audit_stats(
    db: TenantDB,
    user: Annotated[AuthenticatedUser, Depends(require_permission("read:settings"))],
):
    """
    Get statistics about audit log entries.

    Returns counts, breakdowns by action and resource type, and top users.
    """
    now = datetime.utcnow()
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    week_start = today_start - timedelta(days=now.weekday())
    month_start = today_start.replace(day=1)

    # Total entries
    total_query = select(func.count(AuditLog.id)).where(AuditLog.tenant_id == user.tenant_id)
    total_result = await db.execute(total_query)
    total_entries = total_result.scalar() or 0

    # Entries today
    today_query = select(func.count(AuditLog.id)).where(
        AuditLog.tenant_id == user.tenant_id,
        AuditLog.created_at >= today_start,
    )
    today_result = await db.execute(today_query)
    entries_today = today_result.scalar() or 0

    # Entries this week
    week_query = select(func.count(AuditLog.id)).where(
        AuditLog.tenant_id == user.tenant_id,
        AuditLog.created_at >= week_start,
    )
    week_result = await db.execute(week_query)
    entries_this_week = week_result.scalar() or 0

    # Entries this month
    month_query = select(func.count(AuditLog.id)).where(
        AuditLog.tenant_id == user.tenant_id,
        AuditLog.created_at >= month_start,
    )
    month_result = await db.execute(month_query)
    entries_this_month = month_result.scalar() or 0

    # Actions breakdown (last 30 days)
    actions_query = (
        select(AuditLog.action, func.count(AuditLog.id))
        .where(
            AuditLog.tenant_id == user.tenant_id,
            AuditLog.created_at >= now - timedelta(days=30),
        )
        .group_by(AuditLog.action)
        .order_by(func.count(AuditLog.id).desc())
        .limit(10)
    )
    actions_result = await db.execute(actions_query)
    actions_breakdown = {row[0]: row[1] for row in actions_result.fetchall()}

    # Resource types breakdown (last 30 days)
    resources_query = (
        select(AuditLog.resource_type, func.count(AuditLog.id))
        .where(
            AuditLog.tenant_id == user.tenant_id,
            AuditLog.created_at >= now - timedelta(days=30),
        )
        .group_by(AuditLog.resource_type)
        .order_by(func.count(AuditLog.id).desc())
    )
    resources_result = await db.execute(resources_query)
    resource_types_breakdown = {row[0]: row[1] for row in resources_result.fetchall()}

    # Top users (last 30 days)
    users_query = (
        select(AuditLog.user_email, AuditLog.user_id, func.count(AuditLog.id))
        .where(
            AuditLog.tenant_id == user.tenant_id,
            AuditLog.created_at >= now - timedelta(days=30),
            AuditLog.user_email.isnot(None),
        )
        .group_by(AuditLog.user_email, AuditLog.user_id)
        .order_by(func.count(AuditLog.id).desc())
        .limit(5)
    )
    users_result = await db.execute(users_query)
    top_users = [
        {"email": row[0], "user_id": str(row[1]) if row[1] else None, "count": row[2]}
        for row in users_result.fetchall()
    ]

    return AuditLogStats(
        total_entries=total_entries,
        entries_today=entries_today,
        entries_this_week=entries_this_week,
        entries_this_month=entries_this_month,
        actions_breakdown=actions_breakdown,
        resource_types_breakdown=resource_types_breakdown,
        top_users=top_users,
    )


# ===========================================
# GET DISTINCT VALUES FOR FILTERS
# ===========================================

@router.get("/filters/options")
async def get_filter_options(
    db: TenantDB,
    user: Annotated[AuthenticatedUser, Depends(require_permission("read:settings"))],
):
    """
    Get distinct values for filter dropdowns.

    Returns unique actions, resource types, and users.
    """
    # Get distinct actions
    actions_query = (
        select(AuditLog.action)
        .where(AuditLog.tenant_id == user.tenant_id)
        .distinct()
        .order_by(AuditLog.action)
    )
    actions_result = await db.execute(actions_query)
    actions = [row[0] for row in actions_result.fetchall()]

    # Get distinct resource types
    resources_query = (
        select(AuditLog.resource_type)
        .where(AuditLog.tenant_id == user.tenant_id)
        .distinct()
        .order_by(AuditLog.resource_type)
    )
    resources_result = await db.execute(resources_query)
    resource_types = [row[0] for row in resources_result.fetchall()]

    # Get distinct users (with email)
    users_query = (
        select(AuditLog.user_id, AuditLog.user_email)
        .where(
            AuditLog.tenant_id == user.tenant_id,
            AuditLog.user_email.isnot(None),
        )
        .distinct()
        .order_by(AuditLog.user_email)
    )
    users_result = await db.execute(users_query)
    users = [
        {"id": str(row[0]) if row[0] else None, "email": row[1]}
        for row in users_result.fetchall()
    ]

    return {
        "actions": actions,
        "resource_types": resource_types,
        "users": users,
    }
