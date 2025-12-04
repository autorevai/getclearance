"""
Get Clearance - Usage Service Tests
====================================
Unit tests for usage tracking and billing metrics.

Tests:
- Usage metric calculations
- Plan limits
- Overage cost calculations
- Period calculations
"""

import pytest
from datetime import date
from uuid import uuid4

from app.services.usage import (
    UsageMetric,
    UsagePeriod,
    UsageService,
    PLAN_LIMITS,
    UNIT_PRICING,
)


# ===========================================
# USAGE METRIC TESTS
# ===========================================

class TestUsageMetric:
    """Test UsageMetric dataclass."""

    def test_percentage_used_basic(self):
        """Calculate percentage of limit used."""
        metric = UsageMetric(name="Test", count=50, limit=100)
        assert metric.percentage_used == 50.0

    def test_percentage_used_zero(self):
        """Zero usage returns 0%."""
        metric = UsageMetric(name="Test", count=0, limit=100)
        assert metric.percentage_used == 0.0

    def test_percentage_used_at_limit(self):
        """At limit returns 100%."""
        metric = UsageMetric(name="Test", count=100, limit=100)
        assert metric.percentage_used == 100.0

    def test_percentage_used_over_limit(self):
        """Over limit caps at 100%."""
        metric = UsageMetric(name="Test", count=150, limit=100)
        assert metric.percentage_used == 100.0

    def test_percentage_used_unlimited(self):
        """Unlimited (None limit) returns None."""
        metric = UsageMetric(name="Test", count=1000, limit=None)
        assert metric.percentage_used is None

    def test_percentage_used_zero_limit(self):
        """Zero limit returns None (avoid division by zero)."""
        metric = UsageMetric(name="Test", count=10, limit=0)
        assert metric.percentage_used is None

    def test_default_unit(self):
        """Default unit is 'count'."""
        metric = UsageMetric(name="Test", count=10, limit=100)
        assert metric.unit == "count"

    def test_custom_unit(self):
        """Can set custom unit."""
        metric = UsageMetric(name="Test", count=10, limit=100, unit="calls")
        assert metric.unit == "calls"


# ===========================================
# USAGE PERIOD TESTS
# ===========================================

class TestUsagePeriod:
    """Test UsagePeriod dataclass."""

    def test_to_dict_basic(self):
        """Convert usage period to dictionary."""
        tenant_id = uuid4()
        period = UsagePeriod(
            tenant_id=tenant_id,
            period_start=date(2025, 1, 1),
            period_end=date(2025, 2, 1),
            applicants=UsageMetric("Applicants", 50, 100),
            documents=UsageMetric("Documents", 200, 500),
            screenings=UsageMetric("Screenings", 75, 200),
            device_scans=UsageMetric("Device Scans", 25, 500),
            api_calls=UsageMetric("API Calls", 5000, 10000),
        )

        result = period.to_dict()

        assert result["tenant_id"] == str(tenant_id)
        assert result["period_start"] == "2025-01-01"
        assert result["period_end"] == "2025-02-01"
        assert "metrics" in result
        assert result["metrics"]["applicants"]["count"] == 50
        assert result["metrics"]["applicants"]["limit"] == 100
        assert result["metrics"]["applicants"]["percentage_used"] == 50.0

    def test_to_dict_with_unlimited(self):
        """Convert usage period with unlimited metrics."""
        tenant_id = uuid4()
        period = UsagePeriod(
            tenant_id=tenant_id,
            period_start=date(2025, 1, 1),
            period_end=date(2025, 2, 1),
            applicants=UsageMetric("Applicants", 500, None),  # Unlimited
            documents=UsageMetric("Documents", 200, None),
            screenings=UsageMetric("Screenings", 75, None),
            device_scans=UsageMetric("Device Scans", 25, None),
            api_calls=UsageMetric("API Calls", 50000, None),
        )

        result = period.to_dict()

        assert result["metrics"]["applicants"]["limit"] is None
        assert result["metrics"]["applicants"]["percentage_used"] is None


# ===========================================
# PLAN LIMITS TESTS
# ===========================================

class TestPlanLimits:
    """Test plan configuration."""

    def test_free_plan_limits(self):
        """Free plan has strict limits."""
        limits = PLAN_LIMITS["free"]
        assert limits["applicants"] == 10
        assert limits["documents"] == 50
        assert limits["screenings"] == 20

    def test_starter_plan_limits(self):
        """Starter plan has moderate limits."""
        limits = PLAN_LIMITS["starter"]
        assert limits["applicants"] == 100
        assert limits["documents"] == 500
        assert limits["screenings"] == 200

    def test_professional_plan_limits(self):
        """Professional plan has higher limits."""
        limits = PLAN_LIMITS["professional"]
        assert limits["applicants"] == 1000
        assert limits["documents"] == 5000
        assert limits["screenings"] == 2000

    def test_enterprise_plan_unlimited(self):
        """Enterprise plan has unlimited (None) limits."""
        limits = PLAN_LIMITS["enterprise"]
        assert limits["applicants"] is None
        assert limits["documents"] is None
        assert limits["screenings"] is None
        assert limits["device_scans"] is None
        assert limits["api_calls"] is None

    def test_all_plans_have_all_metrics(self):
        """All plans have all required metrics."""
        required_metrics = ["applicants", "documents", "screenings", "device_scans", "api_calls"]
        for plan_name, limits in PLAN_LIMITS.items():
            for metric in required_metrics:
                assert metric in limits, f"Plan {plan_name} missing {metric}"


# ===========================================
# UNIT PRICING TESTS
# ===========================================

class TestUnitPricing:
    """Test pricing configuration."""

    def test_applicant_pricing(self):
        """Applicant pricing is correct."""
        assert UNIT_PRICING["applicants"] == 50  # $0.50

    def test_document_pricing(self):
        """Document pricing is correct."""
        assert UNIT_PRICING["documents"] == 10  # $0.10

    def test_screening_pricing(self):
        """Screening pricing is correct."""
        assert UNIT_PRICING["screenings"] == 25  # $0.25

    def test_device_scan_pricing(self):
        """Device scan pricing is correct."""
        assert UNIT_PRICING["device_scans"] == 5  # $0.05

    def test_api_call_pricing(self):
        """API call pricing is correct."""
        assert UNIT_PRICING["api_calls"] == 1  # $0.01 per 100 calls


# ===========================================
# OVERAGE CALCULATION TESTS
# ===========================================

class TestOverageCalculation:
    """Test overage cost calculations."""

    def test_no_overage_under_limit(self):
        """No overage when under all limits."""
        service = UsageService()
        tenant_id = uuid4()
        usage = UsagePeriod(
            tenant_id=tenant_id,
            period_start=date(2025, 1, 1),
            period_end=date(2025, 2, 1),
            applicants=UsageMetric("Applicants", 50, 100),
            documents=UsageMetric("Documents", 200, 500),
            screenings=UsageMetric("Screenings", 100, 200),
            device_scans=UsageMetric("Device Scans", 250, 500),
            api_calls=UsageMetric("API Calls", 5000, 10000),
        )

        result = service.calculate_overage_cost(usage, plan="starter")

        assert result["has_overage"] is False
        assert result["total_overage_cents"] == 0
        assert result["details"] == {}

    def test_applicant_overage(self):
        """Calculate overage for applicants."""
        service = UsageService()
        tenant_id = uuid4()
        usage = UsagePeriod(
            tenant_id=tenant_id,
            period_start=date(2025, 1, 1),
            period_end=date(2025, 2, 1),
            applicants=UsageMetric("Applicants", 150, 100),  # 50 over
            documents=UsageMetric("Documents", 200, 500),
            screenings=UsageMetric("Screenings", 100, 200),
            device_scans=UsageMetric("Device Scans", 250, 500),
            api_calls=UsageMetric("API Calls", 5000, 10000),
        )

        result = service.calculate_overage_cost(usage, plan="starter")

        assert result["has_overage"] is True
        assert "applicants" in result["details"]
        assert result["details"]["applicants"]["overage_count"] == 50
        # 50 * $0.50 = $25.00 = 2500 cents
        assert result["details"]["applicants"]["overage_cost_cents"] == 2500

    def test_multiple_overages(self):
        """Calculate overages for multiple metrics."""
        service = UsageService()
        tenant_id = uuid4()
        usage = UsagePeriod(
            tenant_id=tenant_id,
            period_start=date(2025, 1, 1),
            period_end=date(2025, 2, 1),
            applicants=UsageMetric("Applicants", 120, 100),  # 20 over
            documents=UsageMetric("Documents", 600, 500),     # 100 over
            screenings=UsageMetric("Screenings", 250, 200),   # 50 over
            device_scans=UsageMetric("Device Scans", 250, 500),
            api_calls=UsageMetric("API Calls", 5000, 10000),
        )

        result = service.calculate_overage_cost(usage, plan="starter")

        assert result["has_overage"] is True
        assert "applicants" in result["details"]
        assert "documents" in result["details"]
        assert "screenings" in result["details"]
        assert "device_scans" not in result["details"]  # Not over

    def test_no_overage_enterprise(self):
        """Enterprise plan has no limits."""
        service = UsageService()
        tenant_id = uuid4()
        usage = UsagePeriod(
            tenant_id=tenant_id,
            period_start=date(2025, 1, 1),
            period_end=date(2025, 2, 1),
            applicants=UsageMetric("Applicants", 10000, None),
            documents=UsageMetric("Documents", 50000, None),
            screenings=UsageMetric("Screenings", 25000, None),
            device_scans=UsageMetric("Device Scans", 100000, None),
            api_calls=UsageMetric("API Calls", 1000000, None),
        )

        result = service.calculate_overage_cost(usage, plan="enterprise")

        assert result["has_overage"] is False

    def test_api_call_overage_rounds_down(self):
        """API call overage uses 100-call increments."""
        service = UsageService()
        tenant_id = uuid4()
        usage = UsagePeriod(
            tenant_id=tenant_id,
            period_start=date(2025, 1, 1),
            period_end=date(2025, 2, 1),
            applicants=UsageMetric("Applicants", 50, 100),
            documents=UsageMetric("Documents", 200, 500),
            screenings=UsageMetric("Screenings", 100, 200),
            device_scans=UsageMetric("Device Scans", 250, 500),
            api_calls=UsageMetric("API Calls", 10550, 10000),  # 550 over
        )

        result = service.calculate_overage_cost(usage, plan="starter")

        # 550 over / 100 = 5 * $0.01 = $0.05 = 5 cents
        assert result["details"]["api_calls"]["overage_count"] == 550
        assert result["details"]["api_calls"]["overage_cost_cents"] == 5


# ===========================================
# USAGE SERVICE TESTS
# ===========================================

class TestUsageService:
    """Test UsageService methods."""

    def test_service_instantiation(self):
        """Can create service instance."""
        service = UsageService()
        assert service is not None

    def test_calculate_overage_unknown_plan(self):
        """Unknown plan defaults to starter limits."""
        service = UsageService()
        tenant_id = uuid4()
        usage = UsagePeriod(
            tenant_id=tenant_id,
            period_start=date(2025, 1, 1),
            period_end=date(2025, 2, 1),
            applicants=UsageMetric("Applicants", 150, 100),
            documents=UsageMetric("Documents", 200, 500),
            screenings=UsageMetric("Screenings", 100, 200),
            device_scans=UsageMetric("Device Scans", 250, 500),
            api_calls=UsageMetric("API Calls", 5000, 10000),
        )

        result = service.calculate_overage_cost(usage, plan="unknown_plan")

        # Should use starter limits
        assert result["has_overage"] is True
        assert "applicants" in result["details"]

    def test_overage_formatting(self):
        """Overage cost is properly formatted."""
        service = UsageService()
        tenant_id = uuid4()
        usage = UsagePeriod(
            tenant_id=tenant_id,
            period_start=date(2025, 1, 1),
            period_end=date(2025, 2, 1),
            applicants=UsageMetric("Applicants", 200, 100),  # 100 over
            documents=UsageMetric("Documents", 200, 500),
            screenings=UsageMetric("Screenings", 100, 200),
            device_scans=UsageMetric("Device Scans", 250, 500),
            api_calls=UsageMetric("API Calls", 5000, 10000),
        )

        result = service.calculate_overage_cost(usage, plan="starter")

        # 100 * $0.50 = $50.00
        assert result["details"]["applicants"]["overage_cost_formatted"] == "$50.00"
        assert result["total_overage_formatted"] == "$50.00"
