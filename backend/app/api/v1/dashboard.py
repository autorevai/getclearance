"""
Get Clearance - Dashboard API
==============================
Dashboard KPIs, screening summary, and activity feed endpoints.
"""

from datetime import datetime, timedelta
from typing import Annotated

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel
from sqlalchemy import select, func, and_, or_, case
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies import TenantDB, AuthenticatedUser
from app.models import Applicant, ScreeningHit, ScreeningCheck, Document


router = APIRouter()


# ===========================================
# SCHEMAS
# ===========================================

class DashboardStats(BaseModel):
    """Dashboard KPI statistics."""
    today_applicants: int
    today_applicants_change: int
    approved: int
    approved_change: int
    rejected: int
    rejected_change: int
    pending_review: int
    pending_review_change: int


class ScreeningSummary(BaseModel):
    """Screening hit counts by type."""
    sanctions_matches: int
    pep_hits: int
    adverse_media: int


class ActivityItem(BaseModel):
    """Single activity feed item."""
    type: str
    applicant_name: str
    time: datetime
    reviewer: str | None = None
    detail: str | None = None


class ActivityFeed(BaseModel):
    """Activity feed response."""
    items: list[ActivityItem]


# ===========================================
# DASHBOARD STATS
# ===========================================
@router.get("/stats", response_model=DashboardStats)
async def get_dashboard_stats(
    db: TenantDB,
    user: AuthenticatedUser,
):
    """
    Get dashboard KPI statistics.

    Returns:
    - Today's applicant count with day-over-day change
    - Approved/rejected/pending counts with changes
    """
    today = datetime.utcnow().date()
    yesterday = today - timedelta(days=1)

    # Count applicants created today
    today_count = await db.scalar(
        select(func.count(Applicant.id))
        .where(and_(
            Applicant.tenant_id == user.tenant_id,
            func.date(Applicant.created_at) == today
        ))
    ) or 0

    # Count applicants created yesterday
    yesterday_count = await db.scalar(
        select(func.count(Applicant.id))
        .where(and_(
            Applicant.tenant_id == user.tenant_id,
            func.date(Applicant.created_at) == yesterday
        ))
    ) or 0

    today_change = today_count - yesterday_count

    # Count by status (approved today)
    approved_today = await db.scalar(
        select(func.count(Applicant.id))
        .where(and_(
            Applicant.tenant_id == user.tenant_id,
            Applicant.status == "approved",
            func.date(Applicant.reviewed_at) == today
        ))
    ) or 0

    # Approved yesterday for comparison
    approved_yesterday = await db.scalar(
        select(func.count(Applicant.id))
        .where(and_(
            Applicant.tenant_id == user.tenant_id,
            Applicant.status == "approved",
            func.date(Applicant.reviewed_at) == yesterday
        ))
    ) or 0

    approved_change = approved_today - approved_yesterday

    # Count rejected today
    rejected_today = await db.scalar(
        select(func.count(Applicant.id))
        .where(and_(
            Applicant.tenant_id == user.tenant_id,
            Applicant.status == "rejected",
            func.date(Applicant.reviewed_at) == today
        ))
    ) or 0

    # Rejected yesterday
    rejected_yesterday = await db.scalar(
        select(func.count(Applicant.id))
        .where(and_(
            Applicant.tenant_id == user.tenant_id,
            Applicant.status == "rejected",
            func.date(Applicant.reviewed_at) == yesterday
        ))
    ) or 0

    rejected_change = rejected_today - rejected_yesterday

    # Count pending/in_progress/review (awaiting action)
    pending_count = await db.scalar(
        select(func.count(Applicant.id))
        .where(and_(
            Applicant.tenant_id == user.tenant_id,
            Applicant.status.in_(["pending", "in_progress", "review"])
        ))
    ) or 0

    # Pending yesterday (this is trickier - we'd need historical data)
    # For now, approximate by counting created yesterday minus reviewed yesterday
    pending_change = 0  # Simplified - would need historical tracking

    return DashboardStats(
        today_applicants=today_count,
        today_applicants_change=today_change,
        approved=approved_today,
        approved_change=approved_change,
        rejected=rejected_today,
        rejected_change=rejected_change,
        pending_review=pending_count,
        pending_review_change=pending_change,
    )


# ===========================================
# SCREENING SUMMARY
# ===========================================
@router.get("/screening-summary", response_model=ScreeningSummary)
async def get_screening_summary(
    db: TenantDB,
    user: AuthenticatedUser,
):
    """
    Get screening hit counts by type.

    Returns counts of:
    - Sanctions matches
    - PEP hits
    - Adverse media hits

    Only counts unresolved (pending) hits.
    """
    # Count sanctions hits
    sanctions_count = await db.scalar(
        select(func.count(ScreeningHit.id))
        .join(ScreeningCheck)
        .where(and_(
            ScreeningCheck.tenant_id == user.tenant_id,
            ScreeningHit.hit_type == "sanctions",
            ScreeningHit.resolution_status == "pending"
        ))
    ) or 0

    # Count PEP hits
    pep_count = await db.scalar(
        select(func.count(ScreeningHit.id))
        .join(ScreeningCheck)
        .where(and_(
            ScreeningCheck.tenant_id == user.tenant_id,
            ScreeningHit.hit_type == "pep",
            ScreeningHit.resolution_status == "pending"
        ))
    ) or 0

    # Count adverse media hits
    adverse_media_count = await db.scalar(
        select(func.count(ScreeningHit.id))
        .join(ScreeningCheck)
        .where(and_(
            ScreeningCheck.tenant_id == user.tenant_id,
            ScreeningHit.hit_type == "adverse_media",
            ScreeningHit.resolution_status == "pending"
        ))
    ) or 0

    return ScreeningSummary(
        sanctions_matches=sanctions_count,
        pep_hits=pep_count,
        adverse_media=adverse_media_count,
    )


# ===========================================
# ACTIVITY FEED
# ===========================================
@router.get("/activity", response_model=ActivityFeed)
async def get_activity_feed(
    db: TenantDB,
    user: AuthenticatedUser,
    limit: Annotated[int, Query(ge=1, le=50)] = 20,
):
    """
    Get recent activity feed.

    Returns the most recent activities including:
    - Applicant status changes (approved, rejected)
    - Screening hits detected
    - Document uploads

    Items are sorted by timestamp descending.
    """
    activities: list[ActivityItem] = []

    # Get recent approved/rejected applicants
    recent_reviews = await db.execute(
        select(Applicant)
        .where(and_(
            Applicant.tenant_id == user.tenant_id,
            Applicant.status.in_(["approved", "rejected"]),
            Applicant.reviewed_at.isnot(None)
        ))
        .order_by(Applicant.reviewed_at.desc())
        .limit(limit)
    )

    for applicant in recent_reviews.scalars():
        activities.append(ActivityItem(
            type=applicant.status,
            applicant_name=applicant.full_name,
            time=applicant.reviewed_at,
            reviewer="You",  # TODO: Get actual reviewer name
            detail=None,
        ))

    # Get recent screening hits
    recent_hits = await db.execute(
        select(ScreeningHit, Applicant)
        .join(ScreeningCheck, ScreeningHit.check_id == ScreeningCheck.id)
        .outerjoin(Applicant, ScreeningCheck.applicant_id == Applicant.id)
        .where(ScreeningCheck.tenant_id == user.tenant_id)
        .order_by(ScreeningHit.created_at.desc())
        .limit(limit)
    )

    for hit, applicant in recent_hits:
        applicant_name = applicant.full_name if applicant else "Unknown"
        hit_type_display = {
            "sanctions": "Sanctions match",
            "pep": "PEP match",
            "adverse_media": "Adverse media",
        }.get(hit.hit_type, hit.hit_type)

        activities.append(ActivityItem(
            type="screening_hit",
            applicant_name=applicant_name,
            time=hit.created_at,
            reviewer=None,
            detail=f"{hit_type_display} detected",
        ))

    # Get recent document uploads
    recent_docs = await db.execute(
        select(Document, Applicant)
        .outerjoin(Applicant, Document.applicant_id == Applicant.id)
        .where(Document.tenant_id == user.tenant_id)
        .order_by(Document.uploaded_at.desc())
        .limit(limit)
    )

    for doc, applicant in recent_docs:
        applicant_name = applicant.full_name if applicant else "Unknown"
        doc_type_display = doc.type.replace("_", " ").title()

        activities.append(ActivityItem(
            type="document_uploaded",
            applicant_name=applicant_name,
            time=doc.uploaded_at,
            reviewer=None,
            detail=f"{doc_type_display} uploaded",
        ))

    # Sort all activities by time and limit
    activities.sort(key=lambda x: x.time, reverse=True)
    activities = activities[:limit]

    return ActivityFeed(items=activities)
