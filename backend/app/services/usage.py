"""
Get Clearance - Usage Tracking Service
======================================
Tracks and aggregates usage metrics for billing purposes.

Metrics tracked:
- Applicant verifications
- Document verifications
- Screening checks (AML/Sanctions/PEP)
- Device intelligence scans
- API calls
"""

from dataclasses import dataclass
from datetime import datetime, date
from typing import Optional
from uuid import UUID

from sqlalchemy import select, func, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.applicant import Applicant
from app.models.document import Document
from app.models.screening import ScreeningCheck
from app.models.device import DeviceFingerprint
from app.models.audit import AuditLog


@dataclass
class UsageMetric:
    """Single usage metric."""
    name: str
    count: int
    limit: Optional[int] = None  # None = unlimited
    unit: str = "count"

    @property
    def percentage_used(self) -> Optional[float]:
        """Calculate percentage of limit used."""
        if self.limit is None or self.limit == 0:
            return None
        return min(100.0, (self.count / self.limit) * 100)


@dataclass
class UsagePeriod:
    """Usage for a billing period."""
    tenant_id: UUID
    period_start: date
    period_end: date
    applicants: UsageMetric
    documents: UsageMetric
    screenings: UsageMetric
    device_scans: UsageMetric
    api_calls: UsageMetric

    def to_dict(self) -> dict:
        """Convert to dictionary for API response."""
        return {
            "tenant_id": str(self.tenant_id),
            "period_start": self.period_start.isoformat(),
            "period_end": self.period_end.isoformat(),
            "metrics": {
                "applicants": {
                    "name": self.applicants.name,
                    "count": self.applicants.count,
                    "limit": self.applicants.limit,
                    "unit": self.applicants.unit,
                    "percentage_used": self.applicants.percentage_used,
                },
                "documents": {
                    "name": self.documents.name,
                    "count": self.documents.count,
                    "limit": self.documents.limit,
                    "unit": self.documents.unit,
                    "percentage_used": self.documents.percentage_used,
                },
                "screenings": {
                    "name": self.screenings.name,
                    "count": self.screenings.count,
                    "limit": self.screenings.limit,
                    "unit": self.screenings.unit,
                    "percentage_used": self.screenings.percentage_used,
                },
                "device_scans": {
                    "name": self.device_scans.name,
                    "count": self.device_scans.count,
                    "limit": self.device_scans.limit,
                    "unit": self.device_scans.unit,
                    "percentage_used": self.device_scans.percentage_used,
                },
                "api_calls": {
                    "name": self.api_calls.name,
                    "count": self.api_calls.count,
                    "limit": self.api_calls.limit,
                    "unit": self.api_calls.unit,
                    "percentage_used": self.api_calls.percentage_used,
                },
            },
        }


@dataclass
class UsageHistoryItem:
    """Historical usage for a single period."""
    period_start: date
    period_end: date
    applicants: int
    documents: int
    screenings: int
    device_scans: int
    api_calls: int
    total_cost: float  # Estimated cost in cents


# Plan limits (can be moved to database later)
PLAN_LIMITS = {
    "free": {
        "applicants": 10,
        "documents": 50,
        "screenings": 20,
        "device_scans": 50,
        "api_calls": 1000,
    },
    "starter": {
        "applicants": 100,
        "documents": 500,
        "screenings": 200,
        "device_scans": 500,
        "api_calls": 10000,
    },
    "professional": {
        "applicants": 1000,
        "documents": 5000,
        "screenings": 2000,
        "device_scans": 5000,
        "api_calls": 100000,
    },
    "enterprise": {
        "applicants": None,  # Unlimited
        "documents": None,
        "screenings": None,
        "device_scans": None,
        "api_calls": None,
    },
}

# Per-unit pricing in cents (for overage calculation)
UNIT_PRICING = {
    "applicants": 50,  # $0.50 per applicant
    "documents": 10,  # $0.10 per document
    "screenings": 25,  # $0.25 per screening
    "device_scans": 5,  # $0.05 per scan
    "api_calls": 1,  # $0.01 per 100 API calls (0.01 cents per call)
}


class UsageService:
    """Service for tracking and reporting usage metrics."""

    async def get_current_usage(
        self,
        db: AsyncSession,
        tenant_id: UUID,
        plan: str = "starter",
        period_start: Optional[date] = None,
        period_end: Optional[date] = None,
    ) -> UsagePeriod:
        """
        Get usage metrics for the current billing period.

        Args:
            db: Database session
            tenant_id: Tenant UUID
            plan: Subscription plan name
            period_start: Start of billing period (default: 1st of current month)
            period_end: End of billing period (default: last day of current month)
        """
        # Default to current month
        today = date.today()
        if period_start is None:
            period_start = today.replace(day=1)
        if period_end is None:
            # Last day of current month
            if today.month == 12:
                period_end = today.replace(year=today.year + 1, month=1, day=1)
            else:
                period_end = today.replace(month=today.month + 1, day=1)

        # Get plan limits
        limits = PLAN_LIMITS.get(plan, PLAN_LIMITS["starter"])

        # Count applicants created in period
        applicants_count = await db.scalar(
            select(func.count(Applicant.id)).where(
                and_(
                    Applicant.tenant_id == tenant_id,
                    func.date(Applicant.created_at) >= period_start,
                    func.date(Applicant.created_at) < period_end,
                )
            )
        ) or 0

        # Count documents created in period
        documents_count = await db.scalar(
            select(func.count(Document.id)).where(
                and_(
                    Document.tenant_id == tenant_id,
                    func.date(Document.created_at) >= period_start,
                    func.date(Document.created_at) < period_end,
                )
            )
        ) or 0

        # Count screening checks in period
        screenings_count = await db.scalar(
            select(func.count(ScreeningCheck.id)).where(
                and_(
                    ScreeningCheck.tenant_id == tenant_id,
                    func.date(ScreeningCheck.created_at) >= period_start,
                    func.date(ScreeningCheck.created_at) < period_end,
                )
            )
        ) or 0

        # Count device scans in period
        device_scans_count = await db.scalar(
            select(func.count(DeviceFingerprint.id)).where(
                and_(
                    DeviceFingerprint.tenant_id == tenant_id,
                    func.date(DeviceFingerprint.created_at) >= period_start,
                    func.date(DeviceFingerprint.created_at) < period_end,
                )
            )
        ) or 0

        # Count API calls from audit log
        api_calls_count = await db.scalar(
            select(func.count(AuditLog.id)).where(
                and_(
                    AuditLog.tenant_id == tenant_id,
                    func.date(AuditLog.created_at) >= period_start,
                    func.date(AuditLog.created_at) < period_end,
                )
            )
        ) or 0

        return UsagePeriod(
            tenant_id=tenant_id,
            period_start=period_start,
            period_end=period_end,
            applicants=UsageMetric(
                name="Applicant Verifications",
                count=applicants_count,
                limit=limits["applicants"],
            ),
            documents=UsageMetric(
                name="Document Verifications",
                count=documents_count,
                limit=limits["documents"],
            ),
            screenings=UsageMetric(
                name="Screening Checks",
                count=screenings_count,
                limit=limits["screenings"],
            ),
            device_scans=UsageMetric(
                name="Device Intelligence Scans",
                count=device_scans_count,
                limit=limits["device_scans"],
            ),
            api_calls=UsageMetric(
                name="API Calls",
                count=api_calls_count,
                limit=limits["api_calls"],
            ),
        )

    async def get_usage_history(
        self,
        db: AsyncSession,
        tenant_id: UUID,
        months: int = 6,
    ) -> list[dict]:
        """
        Get historical usage for the last N months.

        Args:
            db: Database session
            tenant_id: Tenant UUID
            months: Number of months to include
        """
        history = []
        today = date.today()

        for i in range(months):
            # Calculate period for each month
            if today.month - i <= 0:
                year = today.year - 1
                month = 12 + (today.month - i)
            else:
                year = today.year
                month = today.month - i

            period_start = date(year, month, 1)
            if month == 12:
                period_end = date(year + 1, 1, 1)
            else:
                period_end = date(year, month + 1, 1)

            # Get counts for this period
            applicants = await db.scalar(
                select(func.count(Applicant.id)).where(
                    and_(
                        Applicant.tenant_id == tenant_id,
                        func.date(Applicant.created_at) >= period_start,
                        func.date(Applicant.created_at) < period_end,
                    )
                )
            ) or 0

            documents = await db.scalar(
                select(func.count(Document.id)).where(
                    and_(
                        Document.tenant_id == tenant_id,
                        func.date(Document.created_at) >= period_start,
                        func.date(Document.created_at) < period_end,
                    )
                )
            ) or 0

            screenings = await db.scalar(
                select(func.count(ScreeningCheck.id)).where(
                    and_(
                        ScreeningCheck.tenant_id == tenant_id,
                        func.date(ScreeningCheck.created_at) >= period_start,
                        func.date(ScreeningCheck.created_at) < period_end,
                    )
                )
            ) or 0

            device_scans = await db.scalar(
                select(func.count(DeviceFingerprint.id)).where(
                    and_(
                        DeviceFingerprint.tenant_id == tenant_id,
                        func.date(DeviceFingerprint.created_at) >= period_start,
                        func.date(DeviceFingerprint.created_at) < period_end,
                    )
                )
            ) or 0

            api_calls = await db.scalar(
                select(func.count(AuditLog.id)).where(
                    and_(
                        AuditLog.tenant_id == tenant_id,
                        func.date(AuditLog.created_at) >= period_start,
                        func.date(AuditLog.created_at) < period_end,
                    )
                )
            ) or 0

            # Calculate estimated cost
            total_cost = (
                applicants * UNIT_PRICING["applicants"]
                + documents * UNIT_PRICING["documents"]
                + screenings * UNIT_PRICING["screenings"]
                + device_scans * UNIT_PRICING["device_scans"]
                + (api_calls // 100) * UNIT_PRICING["api_calls"]
            )

            history.append({
                "period_start": period_start.isoformat(),
                "period_end": period_end.isoformat(),
                "month_name": period_start.strftime("%B %Y"),
                "applicants": applicants,
                "documents": documents,
                "screenings": screenings,
                "device_scans": device_scans,
                "api_calls": api_calls,
                "total_cost_cents": total_cost,
                "total_cost_formatted": f"${total_cost / 100:.2f}",
            })

        return history

    def calculate_overage_cost(
        self,
        usage: UsagePeriod,
        plan: str = "starter",
    ) -> dict:
        """
        Calculate overage costs for usage exceeding plan limits.

        Args:
            usage: Current usage metrics
            plan: Subscription plan name
        """
        limits = PLAN_LIMITS.get(plan, PLAN_LIMITS["starter"])
        overages = {}
        total_overage = 0

        # Check each metric
        metrics = [
            ("applicants", usage.applicants),
            ("documents", usage.documents),
            ("screenings", usage.screenings),
            ("device_scans", usage.device_scans),
            ("api_calls", usage.api_calls),
        ]

        for name, metric in metrics:
            limit = limits.get(name)
            if limit is not None and metric.count > limit:
                overage_count = metric.count - limit
                overage_cost = overage_count * UNIT_PRICING.get(name, 0)
                if name == "api_calls":
                    overage_cost = (overage_count // 100) * UNIT_PRICING["api_calls"]
                overages[name] = {
                    "overage_count": overage_count,
                    "overage_cost_cents": overage_cost,
                    "overage_cost_formatted": f"${overage_cost / 100:.2f}",
                }
                total_overage += overage_cost

        return {
            "has_overage": total_overage > 0,
            "total_overage_cents": total_overage,
            "total_overage_formatted": f"${total_overage / 100:.2f}",
            "details": overages,
        }


# Singleton instance
usage_service = UsageService()
