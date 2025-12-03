"""
Get Clearance - Monitoring API
===============================
Ongoing AML monitoring endpoints.

Endpoints:
    POST /api/v1/applicants/{id}/monitoring/enable   - Enable monitoring
    POST /api/v1/applicants/{id}/monitoring/disable  - Disable monitoring
    GET  /api/v1/monitoring/alerts                   - List all alerts
    GET  /api/v1/monitoring/alerts/{id}              - Get alert details
    POST /api/v1/monitoring/alerts/{id}/resolve      - Resolve alert
    GET  /api/v1/monitoring/stats                    - Monitoring statistics
"""

from datetime import datetime
from typing import Annotated, Any
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.dependencies import TenantDB, AuthenticatedUser, require_permission
from app.models import Applicant
from app.models.monitoring_alert import MonitoringAlert
from app.services.monitoring import monitoring_service

router = APIRouter()


# ===========================================
# SCHEMAS
# ===========================================

class MonitoringStatusResponse(BaseModel):
    """Response for monitoring status check."""
    applicant_id: UUID
    monitoring_enabled: bool
    last_screened_at: datetime | None = None

    model_config = {"from_attributes": True}


class EnableMonitoringResponse(BaseModel):
    """Response for enable/disable monitoring."""
    success: bool
    message: str
    monitoring_enabled: bool


class MonitoringAlertHitDetail(BaseModel):
    """Detail of a hit within an alert."""
    hit_id: str
    matched_name: str
    hit_type: str
    confidence: float
    list_source: str


class MonitoringAlertResponse(BaseModel):
    """Monitoring alert details."""
    id: UUID
    tenant_id: UUID
    applicant_id: UUID
    alert_type: str
    severity: str
    status: str
    hit_count: int
    hit_types: list[str]
    new_hits: list[dict[str, Any]]
    previous_screening_id: UUID | None
    new_screening_id: UUID
    resolved_by: UUID | None
    resolved_at: datetime | None
    resolution_notes: str | None
    resolution_action: str | None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class MonitoringAlertListResponse(BaseModel):
    """List of monitoring alerts."""
    items: list[MonitoringAlertResponse]
    total: int
    limit: int
    offset: int


class ResolveAlertRequest(BaseModel):
    """Request to resolve a monitoring alert."""
    resolution_action: str = Field(
        ...,
        pattern="^(confirmed_match|false_positive|requires_review|no_action)$",
        description="Resolution action"
    )
    notes: str | None = Field(None, description="Resolution notes")


class MonitoringStatsResponse(BaseModel):
    """Monitoring statistics."""
    monitored_applicants: int
    open_alerts: int
    critical_alerts: int
    alerts_30d: int


# ===========================================
# ENABLE/DISABLE MONITORING
# ===========================================

@router.post(
    "/applicants/{applicant_id}/monitoring/enable",
    response_model=EnableMonitoringResponse,
)
async def enable_monitoring(
    applicant_id: UUID,
    db: TenantDB,
    user: Annotated[AuthenticatedUser, Depends(require_permission("admin:applicants"))],
):
    """
    Enable ongoing AML monitoring for an applicant.

    Only approved applicants can have monitoring enabled. Once enabled,
    the applicant will be re-screened daily against updated sanctions
    and PEP lists.

    Requires admin:applicants permission.
    """
    try:
        success = await monitoring_service.enable_monitoring(
            db=db,
            applicant_id=applicant_id,
            tenant_id=user.tenant_id,
        )

        if success:
            await db.commit()
            return EnableMonitoringResponse(
                success=True,
                message="Monitoring enabled successfully",
                monitoring_enabled=True,
            )
        else:
            return EnableMonitoringResponse(
                success=False,
                message="Cannot enable monitoring for non-approved applicants",
                monitoring_enabled=False,
            )

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )


@router.post(
    "/applicants/{applicant_id}/monitoring/disable",
    response_model=EnableMonitoringResponse,
)
async def disable_monitoring(
    applicant_id: UUID,
    db: TenantDB,
    user: Annotated[AuthenticatedUser, Depends(require_permission("admin:applicants"))],
):
    """
    Disable ongoing AML monitoring for an applicant.

    Requires admin:applicants permission.
    """
    try:
        success = await monitoring_service.disable_monitoring(
            db=db,
            applicant_id=applicant_id,
            tenant_id=user.tenant_id,
        )

        await db.commit()

        return EnableMonitoringResponse(
            success=True,
            message="Monitoring disabled successfully",
            monitoring_enabled=False,
        )

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )


@router.get(
    "/applicants/{applicant_id}/monitoring/status",
    response_model=MonitoringStatusResponse,
)
async def get_monitoring_status(
    applicant_id: UUID,
    db: TenantDB,
    user: AuthenticatedUser,
):
    """
    Get monitoring status for an applicant.
    """
    # Verify applicant belongs to tenant
    query = select(Applicant).where(
        Applicant.id == applicant_id,
        Applicant.tenant_id == user.tenant_id,
    )
    result = await db.execute(query)
    applicant = result.scalar_one_or_none()

    if not applicant:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Applicant not found",
        )

    is_enabled = await monitoring_service.is_monitoring_enabled(db, applicant_id)

    # Get last screening date
    from app.models import ScreeningCheck
    last_screen_query = (
        select(ScreeningCheck.created_at)
        .where(ScreeningCheck.applicant_id == applicant_id)
        .order_by(ScreeningCheck.created_at.desc())
        .limit(1)
    )
    last_screen_result = await db.execute(last_screen_query)
    last_screened_at = last_screen_result.scalar_one_or_none()

    return MonitoringStatusResponse(
        applicant_id=applicant_id,
        monitoring_enabled=is_enabled,
        last_screened_at=last_screened_at,
    )


# ===========================================
# MONITORING ALERTS
# ===========================================

@router.get("/alerts", response_model=MonitoringAlertListResponse)
async def list_alerts(
    db: TenantDB,
    user: AuthenticatedUser,
    alert_status: str | None = Query(None, alias="status"),
    severity: str | None = Query(None),
    applicant_id: UUID | None = Query(None),
    sort_by: str = Query("created_at"),
    sort_order: str = Query("desc", pattern="^(asc|desc)$"),
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
):
    """
    List monitoring alerts with optional filters.
    """
    query = (
        select(MonitoringAlert)
        .where(MonitoringAlert.tenant_id == user.tenant_id)
    )
    count_query = select(func.count(MonitoringAlert.id)).where(
        MonitoringAlert.tenant_id == user.tenant_id
    )

    if alert_status:
        query = query.where(MonitoringAlert.status == alert_status)
        count_query = count_query.where(MonitoringAlert.status == alert_status)

    if severity:
        query = query.where(MonitoringAlert.severity == severity)
        count_query = count_query.where(MonitoringAlert.severity == severity)

    if applicant_id:
        query = query.where(MonitoringAlert.applicant_id == applicant_id)
        count_query = count_query.where(MonitoringAlert.applicant_id == applicant_id)

    # Get total
    total_result = await db.execute(count_query)
    total = total_result.scalar() or 0

    # Apply sorting
    sort_column = getattr(MonitoringAlert, sort_by, MonitoringAlert.created_at)
    if sort_order == "desc":
        query = query.order_by(sort_column.desc())
    else:
        query = query.order_by(sort_column.asc())

    # Apply pagination
    query = query.offset(offset).limit(limit)
    result = await db.execute(query)
    alerts = result.scalars().all()

    return MonitoringAlertListResponse(
        items=[MonitoringAlertResponse.model_validate(a) for a in alerts],
        total=total,
        limit=limit,
        offset=offset,
    )


@router.get("/alerts/{alert_id}", response_model=MonitoringAlertResponse)
async def get_alert(
    alert_id: UUID,
    db: TenantDB,
    user: AuthenticatedUser,
):
    """
    Get monitoring alert details.
    """
    query = (
        select(MonitoringAlert)
        .where(
            MonitoringAlert.id == alert_id,
            MonitoringAlert.tenant_id == user.tenant_id,
        )
    )
    result = await db.execute(query)
    alert = result.scalar_one_or_none()

    if not alert:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Alert not found",
        )

    return MonitoringAlertResponse.model_validate(alert)


@router.post("/alerts/{alert_id}/resolve", response_model=MonitoringAlertResponse)
async def resolve_alert(
    alert_id: UUID,
    data: ResolveAlertRequest,
    db: TenantDB,
    user: Annotated[AuthenticatedUser, Depends(require_permission("review:screening"))],
):
    """
    Resolve a monitoring alert.

    Requires review:screening permission.
    """
    query = (
        select(MonitoringAlert)
        .where(
            MonitoringAlert.id == alert_id,
            MonitoringAlert.tenant_id == user.tenant_id,
        )
    )
    result = await db.execute(query)
    alert = result.scalar_one_or_none()

    if not alert:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Alert not found",
        )

    if alert.is_resolved:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Alert already resolved",
        )

    # Update alert
    alert.status = "resolved"
    alert.resolution_action = data.resolution_action
    alert.resolution_notes = data.notes
    alert.resolved_by = UUID(user.id)
    alert.resolved_at = datetime.utcnow()

    await db.commit()
    await db.refresh(alert)

    return MonitoringAlertResponse.model_validate(alert)


@router.post("/alerts/{alert_id}/dismiss", response_model=MonitoringAlertResponse)
async def dismiss_alert(
    alert_id: UUID,
    db: TenantDB,
    user: Annotated[AuthenticatedUser, Depends(require_permission("review:screening"))],
    notes: str | None = Query(None),
):
    """
    Dismiss a monitoring alert as not requiring action.

    Requires review:screening permission.
    """
    query = (
        select(MonitoringAlert)
        .where(
            MonitoringAlert.id == alert_id,
            MonitoringAlert.tenant_id == user.tenant_id,
        )
    )
    result = await db.execute(query)
    alert = result.scalar_one_or_none()

    if not alert:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Alert not found",
        )

    if alert.is_resolved:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Alert already resolved",
        )

    # Update alert
    alert.status = "dismissed"
    alert.resolution_notes = notes
    alert.resolved_by = UUID(user.id)
    alert.resolved_at = datetime.utcnow()

    await db.commit()
    await db.refresh(alert)

    return MonitoringAlertResponse.model_validate(alert)


@router.post("/alerts/{alert_id}/escalate", response_model=MonitoringAlertResponse)
async def escalate_alert(
    alert_id: UUID,
    db: TenantDB,
    user: Annotated[AuthenticatedUser, Depends(require_permission("review:screening"))],
    escalate_to: UUID | None = Query(None, description="User ID to escalate to"),
    reason: str | None = Query(None),
):
    """
    Escalate a monitoring alert for higher-level review.

    Requires review:screening permission.
    """
    query = (
        select(MonitoringAlert)
        .where(
            MonitoringAlert.id == alert_id,
            MonitoringAlert.tenant_id == user.tenant_id,
        )
    )
    result = await db.execute(query)
    alert = result.scalar_one_or_none()

    if not alert:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Alert not found",
        )

    if alert.is_resolved:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot escalate resolved alert",
        )

    # Update alert
    alert.status = "escalated"
    alert.escalated_to = escalate_to
    alert.escalated_at = datetime.utcnow()
    alert.escalation_reason = reason

    await db.commit()
    await db.refresh(alert)

    return MonitoringAlertResponse.model_validate(alert)


# ===========================================
# MONITORING STATS
# ===========================================

@router.get("/stats", response_model=MonitoringStatsResponse)
async def get_monitoring_stats(
    db: TenantDB,
    user: AuthenticatedUser,
):
    """
    Get monitoring statistics for dashboard.
    """
    stats = await monitoring_service.get_monitoring_stats(
        db=db,
        tenant_id=user.tenant_id,
    )

    return MonitoringStatsResponse(**stats)


# ===========================================
# TRIGGER MONITORING (Admin)
# ===========================================

@router.post("/run")
async def trigger_monitoring_batch(
    db: TenantDB,
    user: Annotated[AuthenticatedUser, Depends(require_permission("admin:screening"))],
):
    """
    Manually trigger a monitoring batch run.

    This runs the same job that the daily scheduler runs.
    Useful for testing or catching up after downtime.

    Requires admin:screening permission.
    """
    try:
        from arq import create_pool
        from app.workers.config import get_redis_settings

        redis = await create_pool(get_redis_settings())
        job = await redis.enqueue_job(
            "run_monitoring_batch",
            tenant_id=str(user.tenant_id),
        )
        await redis.close()

        return {
            "status": "queued",
            "message": "Monitoring batch has been queued",
            "job_id": job.job_id if job else None,
            "queued_at": datetime.utcnow().isoformat(),
        }

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Failed to queue monitoring batch: {str(e)}",
        )
