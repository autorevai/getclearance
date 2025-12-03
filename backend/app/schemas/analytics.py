"""
Get Clearance - Analytics Schemas
==================================
Pydantic schemas for analytics API responses.
"""

from datetime import date, datetime
from pydantic import BaseModel, Field


class OverviewMetrics(BaseModel):
    """Overview KPI metrics response."""

    total_verifications: int = Field(description="Total completed verifications in period")
    approval_rate: float = Field(description="Percentage approved vs total decisions")
    avg_processing_time_hours: float = Field(description="Average hours from created to reviewed")
    avg_risk_score: float = Field(description="Average risk score (0-100)")
    total_screened: int = Field(description="Total screening checks run")
    hit_rate: float = Field(description="Percentage of screenings with hits")


class FunnelData(BaseModel):
    """Verification funnel stage counts."""

    submitted: int = Field(description="Applications submitted")
    documents_uploaded: int = Field(description="Applicants with documents")
    screening_complete: int = Field(description="Applicants screened")
    approved: int = Field(description="Final approved")
    rejected: int = Field(description="Final rejected")


class TrendPoint(BaseModel):
    """Single data point in time series."""

    date: str | None = Field(description="ISO date string for the period")
    submitted: int = Field(description="Applications submitted in period")
    approved: int = Field(description="Applications approved in period")
    rejected: int = Field(description="Applications rejected in period")


class TrendsResponse(BaseModel):
    """Time series trend data."""

    granularity: str = Field(description="Granularity: day, week, or month")
    data: list[TrendPoint] = Field(description="Time series data points")


class GeographyItem(BaseModel):
    """Country distribution item."""

    country: str = Field(description="ISO 3166-1 alpha-3 country code")
    count: int = Field(description="Number of applicants from country")


class GeographyResponse(BaseModel):
    """Geographic distribution response."""

    data: list[GeographyItem] = Field(description="Countries sorted by count")


class RiskBucket(BaseModel):
    """Risk score histogram bucket."""

    bucket: str = Field(description="Risk score range (e.g. '0-20')")
    count: int = Field(description="Number of applicants in bucket")


class RiskDistributionResponse(BaseModel):
    """Risk score distribution response."""

    data: list[RiskBucket] = Field(description="Risk buckets")


class SLAPerformance(BaseModel):
    """SLA performance metrics."""

    on_time_rate: float = Field(description="Percentage resolved within SLA")
    avg_resolution_time_hours: float = Field(description="Average hours to resolution")
    at_risk_count: int = Field(description="Pending cases approaching SLA")
    breached_count: int = Field(description="Pending cases past SLA")


class DateRangeParams(BaseModel):
    """Common date range parameters."""

    start_date: date = Field(description="Start date for analytics period")
    end_date: date = Field(description="End date for analytics period")


class ExportRequest(BaseModel):
    """Analytics export request."""

    start_date: date = Field(description="Start date for export")
    end_date: date = Field(description="End date for export")
    format: str = Field(default="csv", description="Export format: csv or pdf")
