"""
Get Clearance - Analytics Service
==================================
Analytics calculations for compliance metrics, trends, and visualizations.
"""

from datetime import datetime, timedelta, date
from typing import Any
from uuid import UUID

from sqlalchemy import select, func, and_, case, extract
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Applicant, ScreeningCheck, ScreeningHit


async def get_overview_metrics(
    db: AsyncSession,
    tenant_id: UUID,
    start_date: date,
    end_date: date,
) -> dict[str, Any]:
    """
    Get overview KPI metrics for the analytics dashboard.

    Returns:
        - total_verifications: Total completed verifications in period
        - approval_rate: Percentage of approved vs total decisions
        - avg_processing_time_hours: Average time from created to reviewed
        - avg_risk_score: Average risk score of applicants
        - total_screened: Total screening checks run
        - hit_rate: Percentage of screenings with hits
    """
    start_dt = datetime.combine(start_date, datetime.min.time())
    end_dt = datetime.combine(end_date, datetime.max.time())

    # Total verifications (approved + rejected)
    total_decisions = await db.scalar(
        select(func.count(Applicant.id))
        .where(and_(
            Applicant.tenant_id == tenant_id,
            Applicant.status.in_(["approved", "rejected"]),
            Applicant.reviewed_at >= start_dt,
            Applicant.reviewed_at <= end_dt,
        ))
    ) or 0

    # Approved count
    approved_count = await db.scalar(
        select(func.count(Applicant.id))
        .where(and_(
            Applicant.tenant_id == tenant_id,
            Applicant.status == "approved",
            Applicant.reviewed_at >= start_dt,
            Applicant.reviewed_at <= end_dt,
        ))
    ) or 0

    # Calculate approval rate
    approval_rate = (approved_count / total_decisions * 100) if total_decisions > 0 else 0

    # Average processing time (in hours)
    avg_time_result = await db.execute(
        select(
            func.avg(
                extract('epoch', Applicant.reviewed_at - Applicant.created_at) / 3600
            )
        )
        .where(and_(
            Applicant.tenant_id == tenant_id,
            Applicant.status.in_(["approved", "rejected"]),
            Applicant.reviewed_at.isnot(None),
            Applicant.reviewed_at >= start_dt,
            Applicant.reviewed_at <= end_dt,
        ))
    )
    avg_processing_time = avg_time_result.scalar() or 0

    # Average risk score
    avg_risk_result = await db.execute(
        select(func.avg(Applicant.risk_score))
        .where(and_(
            Applicant.tenant_id == tenant_id,
            Applicant.risk_score.isnot(None),
            Applicant.created_at >= start_dt,
            Applicant.created_at <= end_dt,
        ))
    )
    avg_risk_score = avg_risk_result.scalar() or 0

    # Total screening checks
    total_screened = await db.scalar(
        select(func.count(ScreeningCheck.id))
        .where(and_(
            ScreeningCheck.tenant_id == tenant_id,
            ScreeningCheck.created_at >= start_dt,
            ScreeningCheck.created_at <= end_dt,
        ))
    ) or 0

    # Screenings with hits
    screenings_with_hits = await db.scalar(
        select(func.count(ScreeningCheck.id))
        .where(and_(
            ScreeningCheck.tenant_id == tenant_id,
            ScreeningCheck.status == "hit",
            ScreeningCheck.created_at >= start_dt,
            ScreeningCheck.created_at <= end_dt,
        ))
    ) or 0

    hit_rate = (screenings_with_hits / total_screened * 100) if total_screened > 0 else 0

    return {
        "total_verifications": total_decisions,
        "approval_rate": round(approval_rate, 1),
        "avg_processing_time_hours": round(float(avg_processing_time), 1),
        "avg_risk_score": round(float(avg_risk_score), 0),
        "total_screened": total_screened,
        "hit_rate": round(hit_rate, 1),
    }


async def get_verification_funnel(
    db: AsyncSession,
    tenant_id: UUID,
    start_date: date,
    end_date: date,
) -> dict[str, Any]:
    """
    Get verification funnel data showing drop-off at each stage.

    Returns counts at each stage:
        - submitted: Total applications submitted
        - documents_uploaded: Applicants with at least one document
        - screening_complete: Applicants who completed screening
        - approved: Final approved
        - rejected: Final rejected
    """
    start_dt = datetime.combine(start_date, datetime.min.time())
    end_dt = datetime.combine(end_date, datetime.max.time())

    # Total submitted (created in period)
    submitted = await db.scalar(
        select(func.count(Applicant.id))
        .where(and_(
            Applicant.tenant_id == tenant_id,
            Applicant.created_at >= start_dt,
            Applicant.created_at <= end_dt,
        ))
    ) or 0

    # With documents (using subquery)
    from app.models import Document
    applicants_with_docs = await db.scalar(
        select(func.count(func.distinct(Document.applicant_id)))
        .where(and_(
            Document.tenant_id == tenant_id,
            Document.uploaded_at >= start_dt,
            Document.uploaded_at <= end_dt,
        ))
    ) or 0

    # Screening complete
    screening_complete = await db.scalar(
        select(func.count(func.distinct(ScreeningCheck.applicant_id)))
        .where(and_(
            ScreeningCheck.tenant_id == tenant_id,
            ScreeningCheck.status.in_(["clear", "hit"]),
            ScreeningCheck.completed_at.isnot(None),
            ScreeningCheck.created_at >= start_dt,
            ScreeningCheck.created_at <= end_dt,
        ))
    ) or 0

    # Approved
    approved = await db.scalar(
        select(func.count(Applicant.id))
        .where(and_(
            Applicant.tenant_id == tenant_id,
            Applicant.status == "approved",
            Applicant.reviewed_at >= start_dt,
            Applicant.reviewed_at <= end_dt,
        ))
    ) or 0

    # Rejected
    rejected = await db.scalar(
        select(func.count(Applicant.id))
        .where(and_(
            Applicant.tenant_id == tenant_id,
            Applicant.status == "rejected",
            Applicant.reviewed_at >= start_dt,
            Applicant.reviewed_at <= end_dt,
        ))
    ) or 0

    return {
        "submitted": submitted,
        "documents_uploaded": applicants_with_docs,
        "screening_complete": screening_complete,
        "approved": approved,
        "rejected": rejected,
    }


async def get_trends(
    db: AsyncSession,
    tenant_id: UUID,
    start_date: date,
    end_date: date,
    granularity: str = "day",
) -> list[dict[str, Any]]:
    """
    Get time series data for applications over time.

    Args:
        granularity: 'day', 'week', or 'month'

    Returns list of data points with:
        - date: The date/period
        - submitted: Applications submitted
        - approved: Applications approved
        - rejected: Applications rejected
    """
    start_dt = datetime.combine(start_date, datetime.min.time())
    end_dt = datetime.combine(end_date, datetime.max.time())

    # Determine date truncation based on granularity
    if granularity == "week":
        date_trunc = func.date_trunc('week', Applicant.created_at)
    elif granularity == "month":
        date_trunc = func.date_trunc('month', Applicant.created_at)
    else:  # day
        date_trunc = func.date_trunc('day', Applicant.created_at)

    # Get submitted counts by period
    submitted_result = await db.execute(
        select(
            date_trunc.label('period'),
            func.count(Applicant.id).label('count')
        )
        .where(and_(
            Applicant.tenant_id == tenant_id,
            Applicant.created_at >= start_dt,
            Applicant.created_at <= end_dt,
        ))
        .group_by(date_trunc)
        .order_by(date_trunc)
    )
    submitted_by_period = {row.period: row.count for row in submitted_result}

    # Get approved counts by period (using reviewed_at)
    if granularity == "week":
        review_date_trunc = func.date_trunc('week', Applicant.reviewed_at)
    elif granularity == "month":
        review_date_trunc = func.date_trunc('month', Applicant.reviewed_at)
    else:
        review_date_trunc = func.date_trunc('day', Applicant.reviewed_at)

    approved_result = await db.execute(
        select(
            review_date_trunc.label('period'),
            func.count(Applicant.id).label('count')
        )
        .where(and_(
            Applicant.tenant_id == tenant_id,
            Applicant.status == "approved",
            Applicant.reviewed_at >= start_dt,
            Applicant.reviewed_at <= end_dt,
        ))
        .group_by(review_date_trunc)
        .order_by(review_date_trunc)
    )
    approved_by_period = {row.period: row.count for row in approved_result}

    # Get rejected counts by period
    rejected_result = await db.execute(
        select(
            review_date_trunc.label('period'),
            func.count(Applicant.id).label('count')
        )
        .where(and_(
            Applicant.tenant_id == tenant_id,
            Applicant.status == "rejected",
            Applicant.reviewed_at >= start_dt,
            Applicant.reviewed_at <= end_dt,
        ))
        .group_by(review_date_trunc)
        .order_by(review_date_trunc)
    )
    rejected_by_period = {row.period: row.count for row in rejected_result}

    # Combine all periods
    all_periods = set(submitted_by_period.keys()) | set(approved_by_period.keys()) | set(rejected_by_period.keys())

    trends = []
    for period in sorted(all_periods):
        trends.append({
            "date": period.isoformat() if period else None,
            "submitted": submitted_by_period.get(period, 0),
            "approved": approved_by_period.get(period, 0),
            "rejected": rejected_by_period.get(period, 0),
        })

    return trends


async def get_geographic_distribution(
    db: AsyncSession,
    tenant_id: UUID,
    start_date: date,
    end_date: date,
) -> list[dict[str, Any]]:
    """
    Get distribution of applicants by country.

    Returns list of countries with counts, sorted by count descending.
    """
    start_dt = datetime.combine(start_date, datetime.min.time())
    end_dt = datetime.combine(end_date, datetime.max.time())

    result = await db.execute(
        select(
            Applicant.country_of_residence,
            func.count(Applicant.id).label('count')
        )
        .where(and_(
            Applicant.tenant_id == tenant_id,
            Applicant.country_of_residence.isnot(None),
            Applicant.created_at >= start_dt,
            Applicant.created_at <= end_dt,
        ))
        .group_by(Applicant.country_of_residence)
        .order_by(func.count(Applicant.id).desc())
        .limit(20)
    )

    return [
        {"country": row.country_of_residence, "count": row.count}
        for row in result
    ]


async def get_risk_distribution(
    db: AsyncSession,
    tenant_id: UUID,
    start_date: date,
    end_date: date,
) -> list[dict[str, Any]]:
    """
    Get risk score distribution as histogram buckets.

    Returns buckets: 0-20, 21-40, 41-60, 61-80, 81-100
    """
    start_dt = datetime.combine(start_date, datetime.min.time())
    end_dt = datetime.combine(end_date, datetime.max.time())

    # Use CASE to bucket risk scores
    bucket = case(
        (Applicant.risk_score <= 20, "0-20"),
        (Applicant.risk_score <= 40, "21-40"),
        (Applicant.risk_score <= 60, "41-60"),
        (Applicant.risk_score <= 80, "61-80"),
        else_="81-100"
    )

    result = await db.execute(
        select(
            bucket.label('bucket'),
            func.count(Applicant.id).label('count')
        )
        .where(and_(
            Applicant.tenant_id == tenant_id,
            Applicant.risk_score.isnot(None),
            Applicant.created_at >= start_dt,
            Applicant.created_at <= end_dt,
        ))
        .group_by(bucket)
    )

    # Ensure all buckets are present
    bucket_order = ["0-20", "21-40", "41-60", "61-80", "81-100"]
    bucket_counts = {row.bucket: row.count for row in result}

    return [
        {"bucket": b, "count": bucket_counts.get(b, 0)}
        for b in bucket_order
    ]


async def get_sla_performance(
    db: AsyncSession,
    tenant_id: UUID,
    start_date: date,
    end_date: date,
) -> dict[str, Any]:
    """
    Get SLA performance metrics.

    Returns:
        - on_time_rate: Percentage of cases resolved within SLA
        - avg_resolution_time_hours: Average time to resolution
        - at_risk_count: Number of pending cases approaching SLA
        - breached_count: Number of cases that missed SLA
    """
    start_dt = datetime.combine(start_date, datetime.min.time())
    end_dt = datetime.combine(end_date, datetime.max.time())
    now = datetime.utcnow()

    # Total resolved in period
    total_resolved = await db.scalar(
        select(func.count(Applicant.id))
        .where(and_(
            Applicant.tenant_id == tenant_id,
            Applicant.status.in_(["approved", "rejected"]),
            Applicant.reviewed_at >= start_dt,
            Applicant.reviewed_at <= end_dt,
        ))
    ) or 0

    # Resolved within SLA (sla_due_at is set and reviewed_at <= sla_due_at)
    on_time = await db.scalar(
        select(func.count(Applicant.id))
        .where(and_(
            Applicant.tenant_id == tenant_id,
            Applicant.status.in_(["approved", "rejected"]),
            Applicant.reviewed_at >= start_dt,
            Applicant.reviewed_at <= end_dt,
            Applicant.sla_due_at.isnot(None),
            Applicant.reviewed_at <= Applicant.sla_due_at,
        ))
    ) or 0

    # Also count those without SLA as on-time (no SLA set = no breach)
    no_sla_count = await db.scalar(
        select(func.count(Applicant.id))
        .where(and_(
            Applicant.tenant_id == tenant_id,
            Applicant.status.in_(["approved", "rejected"]),
            Applicant.reviewed_at >= start_dt,
            Applicant.reviewed_at <= end_dt,
            Applicant.sla_due_at.is_(None),
        ))
    ) or 0

    total_on_time = on_time + no_sla_count
    on_time_rate = (total_on_time / total_resolved * 100) if total_resolved > 0 else 100

    # Average resolution time
    avg_time_result = await db.execute(
        select(
            func.avg(
                extract('epoch', Applicant.reviewed_at - Applicant.created_at) / 3600
            )
        )
        .where(and_(
            Applicant.tenant_id == tenant_id,
            Applicant.status.in_(["approved", "rejected"]),
            Applicant.reviewed_at >= start_dt,
            Applicant.reviewed_at <= end_dt,
        ))
    )
    avg_resolution_time = avg_time_result.scalar() or 0

    # At risk (pending with SLA due within 4 hours)
    at_risk_threshold = now + timedelta(hours=4)
    at_risk_count = await db.scalar(
        select(func.count(Applicant.id))
        .where(and_(
            Applicant.tenant_id == tenant_id,
            Applicant.status.in_(["pending", "in_progress", "review"]),
            Applicant.sla_due_at.isnot(None),
            Applicant.sla_due_at <= at_risk_threshold,
            Applicant.sla_due_at > now,
        ))
    ) or 0

    # Breached (pending with SLA already passed)
    breached_count = await db.scalar(
        select(func.count(Applicant.id))
        .where(and_(
            Applicant.tenant_id == tenant_id,
            Applicant.status.in_(["pending", "in_progress", "review"]),
            Applicant.sla_due_at.isnot(None),
            Applicant.sla_due_at < now,
        ))
    ) or 0

    return {
        "on_time_rate": round(on_time_rate, 1),
        "avg_resolution_time_hours": round(float(avg_resolution_time), 1),
        "at_risk_count": at_risk_count,
        "breached_count": breached_count,
    }


async def export_analytics_csv(
    db: AsyncSession,
    tenant_id: UUID,
    start_date: date,
    end_date: date,
) -> str:
    """
    Export analytics data as CSV.

    Returns CSV string with daily metrics.
    """
    trends = await get_trends(db, tenant_id, start_date, end_date, "day")

    lines = ["Date,Submitted,Approved,Rejected"]
    for point in trends:
        lines.append(f"{point['date']},{point['submitted']},{point['approved']},{point['rejected']}")

    return "\n".join(lines)
