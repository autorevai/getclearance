"""
Get Clearance - Analytics API
==============================
Analytics endpoints for compliance metrics, trends, and visualizations.
"""

from datetime import date, timedelta
from typing import Annotated

from fastapi import APIRouter, Depends, Query, Response
from fastapi.responses import StreamingResponse

from app.dependencies import TenantDB, AuthenticatedUser
from app.schemas.analytics import (
    OverviewMetrics,
    FunnelData,
    TrendsResponse,
    TrendPoint,
    GeographyResponse,
    GeographyItem,
    RiskDistributionResponse,
    RiskBucket,
    SLAPerformance,
)
from app.services import analytics as analytics_service


router = APIRouter()


def get_default_dates(days: int = 30) -> tuple[date, date]:
    """Get default date range (last N days)."""
    end_date = date.today()
    start_date = end_date - timedelta(days=days)
    return start_date, end_date


# ===========================================
# OVERVIEW METRICS
# ===========================================
@router.get("/overview", response_model=OverviewMetrics)
async def get_overview(
    db: TenantDB,
    user: AuthenticatedUser,
    start_date: Annotated[date | None, Query(description="Start date")] = None,
    end_date: Annotated[date | None, Query(description="End date")] = None,
):
    """
    Get overview KPI metrics for the analytics dashboard.

    Returns key metrics including:
    - Total verifications completed
    - Approval rate
    - Average processing time
    - Average risk score
    - Screening hit rate
    """
    if not start_date or not end_date:
        start_date, end_date = get_default_dates(30)

    result = await analytics_service.get_overview_metrics(
        db, user.tenant_id, start_date, end_date
    )

    return OverviewMetrics(**result)


# ===========================================
# VERIFICATION FUNNEL
# ===========================================
@router.get("/funnel", response_model=FunnelData)
async def get_funnel(
    db: TenantDB,
    user: AuthenticatedUser,
    start_date: Annotated[date | None, Query(description="Start date")] = None,
    end_date: Annotated[date | None, Query(description="End date")] = None,
):
    """
    Get verification funnel data showing conversion at each stage.

    Shows drop-off from submission through approval/rejection.
    """
    if not start_date or not end_date:
        start_date, end_date = get_default_dates(30)

    result = await analytics_service.get_verification_funnel(
        db, user.tenant_id, start_date, end_date
    )

    return FunnelData(**result)


# ===========================================
# TIME SERIES TRENDS
# ===========================================
@router.get("/trends", response_model=TrendsResponse)
async def get_trends(
    db: TenantDB,
    user: AuthenticatedUser,
    start_date: Annotated[date | None, Query(description="Start date")] = None,
    end_date: Annotated[date | None, Query(description="End date")] = None,
    granularity: Annotated[str, Query(description="Granularity: day, week, month")] = "day",
):
    """
    Get time series data for applications over time.

    Returns submitted, approved, and rejected counts by period.
    """
    if not start_date or not end_date:
        start_date, end_date = get_default_dates(30)

    if granularity not in ["day", "week", "month"]:
        granularity = "day"

    data = await analytics_service.get_trends(
        db, user.tenant_id, start_date, end_date, granularity
    )

    return TrendsResponse(
        granularity=granularity,
        data=[TrendPoint(**point) for point in data]
    )


# ===========================================
# GEOGRAPHIC DISTRIBUTION
# ===========================================
@router.get("/geography", response_model=GeographyResponse)
async def get_geography(
    db: TenantDB,
    user: AuthenticatedUser,
    start_date: Annotated[date | None, Query(description="Start date")] = None,
    end_date: Annotated[date | None, Query(description="End date")] = None,
):
    """
    Get distribution of applicants by country.

    Returns top 20 countries by applicant count.
    """
    if not start_date or not end_date:
        start_date, end_date = get_default_dates(30)

    data = await analytics_service.get_geographic_distribution(
        db, user.tenant_id, start_date, end_date
    )

    return GeographyResponse(
        data=[GeographyItem(**item) for item in data]
    )


# ===========================================
# RISK DISTRIBUTION
# ===========================================
@router.get("/risk", response_model=RiskDistributionResponse)
async def get_risk_distribution(
    db: TenantDB,
    user: AuthenticatedUser,
    start_date: Annotated[date | None, Query(description="Start date")] = None,
    end_date: Annotated[date | None, Query(description="End date")] = None,
):
    """
    Get risk score distribution as histogram.

    Returns count of applicants in each risk bucket (0-20, 21-40, etc.).
    """
    if not start_date or not end_date:
        start_date, end_date = get_default_dates(30)

    data = await analytics_service.get_risk_distribution(
        db, user.tenant_id, start_date, end_date
    )

    return RiskDistributionResponse(
        data=[RiskBucket(**bucket) for bucket in data]
    )


# ===========================================
# SLA PERFORMANCE
# ===========================================
@router.get("/sla", response_model=SLAPerformance)
async def get_sla_performance(
    db: TenantDB,
    user: AuthenticatedUser,
    start_date: Annotated[date | None, Query(description="Start date")] = None,
    end_date: Annotated[date | None, Query(description="End date")] = None,
):
    """
    Get SLA performance metrics.

    Returns on-time rate, average resolution time, and at-risk counts.
    """
    if not start_date or not end_date:
        start_date, end_date = get_default_dates(30)

    result = await analytics_service.get_sla_performance(
        db, user.tenant_id, start_date, end_date
    )

    return SLAPerformance(**result)


# ===========================================
# EXPORT
# ===========================================
@router.get("/export")
async def export_analytics(
    db: TenantDB,
    user: AuthenticatedUser,
    start_date: Annotated[date | None, Query(description="Start date")] = None,
    end_date: Annotated[date | None, Query(description="End date")] = None,
    format: Annotated[str, Query(description="Export format: csv")] = "csv",
):
    """
    Export analytics data.

    Currently supports CSV export of daily metrics.
    """
    if not start_date or not end_date:
        start_date, end_date = get_default_dates(30)

    if format == "csv":
        csv_content = await analytics_service.export_analytics_csv(
            db, user.tenant_id, start_date, end_date
        )

        return Response(
            content=csv_content,
            media_type="text/csv",
            headers={
                "Content-Disposition": f"attachment; filename=analytics_{start_date}_{end_date}.csv"
            }
        )

    # For other formats, return JSON of all data
    overview = await analytics_service.get_overview_metrics(
        db, user.tenant_id, start_date, end_date
    )
    funnel = await analytics_service.get_verification_funnel(
        db, user.tenant_id, start_date, end_date
    )
    trends = await analytics_service.get_trends(
        db, user.tenant_id, start_date, end_date, "day"
    )

    return {
        "period": {"start_date": start_date.isoformat(), "end_date": end_date.isoformat()},
        "overview": overview,
        "funnel": funnel,
        "trends": trends,
    }
