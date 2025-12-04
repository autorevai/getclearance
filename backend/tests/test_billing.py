"""
Get Clearance - Billing Service Tests
======================================
Unit tests for Stripe billing integration.

Tests:
- Plan configuration
- Subscription data classes
- Error handling
- Helper methods
"""

import pytest
from datetime import datetime
from uuid import uuid4
from unittest.mock import patch, MagicMock, AsyncMock

from app.services.billing import (
    BillingService,
    BillingError,
    SubscriptionPlan,
    SubscriptionInfo,
    InvoiceInfo,
    PLANS,
)


# ===========================================
# PLAN CONFIGURATION TESTS
# ===========================================

class TestSubscriptionPlan:
    """Test SubscriptionPlan dataclass."""

    def test_starter_plan_exists(self):
        """Starter plan is configured."""
        assert "starter" in PLANS
        plan = PLANS["starter"]
        assert plan.name == "Starter"
        assert plan.amount == 4900  # $49
        assert plan.interval == "month"

    def test_professional_plan_exists(self):
        """Professional plan is configured."""
        assert "professional" in PLANS
        plan = PLANS["professional"]
        assert plan.name == "Professional"
        assert plan.amount == 14900  # $149
        assert plan.interval == "month"

    def test_enterprise_plan_exists(self):
        """Enterprise plan is configured."""
        assert "enterprise" in PLANS
        plan = PLANS["enterprise"]
        assert plan.name == "Enterprise"
        assert plan.amount == 49900  # $499
        assert plan.interval == "month"

    def test_all_plans_have_features(self):
        """All plans have feature lists."""
        for plan_id, plan in PLANS.items():
            assert isinstance(plan.features, list)
            assert len(plan.features) > 0, f"{plan_id} has no features"

    def test_plan_pricing_order(self):
        """Plans are priced in ascending order."""
        assert PLANS["starter"].amount < PLANS["professional"].amount
        assert PLANS["professional"].amount < PLANS["enterprise"].amount


# ===========================================
# SUBSCRIPTION INFO TESTS
# ===========================================

class TestSubscriptionInfo:
    """Test SubscriptionInfo dataclass."""

    def test_subscription_info_creation(self):
        """Can create SubscriptionInfo."""
        info = SubscriptionInfo(
            id="sub_123",
            status="active",
            plan_id="starter",
            plan_name="Starter",
            current_period_start=datetime(2025, 1, 1),
            current_period_end=datetime(2025, 2, 1),
            cancel_at_period_end=False,
            canceled_at=None,
            amount=4900,
            interval="month",
            payment_method={"brand": "visa", "last4": "4242"},
        )

        assert info.id == "sub_123"
        assert info.status == "active"
        assert info.plan_id == "starter"
        assert info.cancel_at_period_end is False
        assert info.canceled_at is None

    def test_subscription_info_with_cancellation(self):
        """SubscriptionInfo with cancellation scheduled."""
        info = SubscriptionInfo(
            id="sub_123",
            status="active",
            plan_id="starter",
            plan_name="Starter",
            current_period_start=datetime(2025, 1, 1),
            current_period_end=datetime(2025, 2, 1),
            cancel_at_period_end=True,
            canceled_at=datetime(2025, 1, 15),
            amount=4900,
            interval="month",
            payment_method=None,
        )

        assert info.cancel_at_period_end is True
        assert info.canceled_at is not None


# ===========================================
# INVOICE INFO TESTS
# ===========================================

class TestInvoiceInfo:
    """Test InvoiceInfo dataclass."""

    def test_invoice_info_creation(self):
        """Can create InvoiceInfo."""
        info = InvoiceInfo(
            id="in_123",
            number="INV-0001",
            status="paid",
            amount_due=4900,
            amount_paid=4900,
            currency="usd",
            created=datetime(2025, 1, 1),
            due_date=datetime(2025, 1, 15),
            paid_at=datetime(2025, 1, 5),
            pdf_url="https://stripe.com/invoice.pdf",
            hosted_invoice_url="https://invoice.stripe.com/i/123",
        )

        assert info.id == "in_123"
        assert info.status == "paid"
        assert info.amount_due == info.amount_paid

    def test_invoice_info_unpaid(self):
        """InvoiceInfo for unpaid invoice."""
        info = InvoiceInfo(
            id="in_456",
            number="INV-0002",
            status="open",
            amount_due=4900,
            amount_paid=0,
            currency="usd",
            created=datetime(2025, 1, 1),
            due_date=datetime(2025, 1, 15),
            paid_at=None,
            pdf_url=None,
            hosted_invoice_url="https://invoice.stripe.com/i/456",
        )

        assert info.status == "open"
        assert info.paid_at is None
        assert info.amount_paid == 0


# ===========================================
# BILLING SERVICE TESTS
# ===========================================

class TestBillingService:
    """Test BillingService methods."""

    def test_service_instantiation(self):
        """Can create service instance."""
        service = BillingService()
        assert service is not None

    def test_ensure_stripe_not_configured(self):
        """Raises error when Stripe not configured."""
        service = BillingService()

        with patch("app.services.billing.settings") as mock_settings:
            mock_settings.stripe_secret_key = ""

            with pytest.raises(BillingError, match="not configured"):
                service._ensure_stripe_configured()

    def test_ensure_stripe_configured(self):
        """No error when Stripe is configured."""
        service = BillingService()

        with patch("app.services.billing.settings") as mock_settings:
            mock_settings.stripe_secret_key = "sk_test_123"

            # Should not raise
            service._ensure_stripe_configured()


# ===========================================
# BILLING ERROR TESTS
# ===========================================

class TestBillingError:
    """Test BillingError exception."""

    def test_billing_error_message(self):
        """BillingError contains message."""
        error = BillingError("Test error message")
        assert str(error) == "Test error message"

    def test_billing_error_is_exception(self):
        """BillingError is an Exception."""
        error = BillingError("Test")
        assert isinstance(error, Exception)


# ===========================================
# BILLING SERVICE CONFIG TESTS
# ===========================================

class TestBillingServiceConfig:
    """Test BillingService configuration checks."""

    def test_ensure_configured_raises_when_no_key(self):
        """Raises error when Stripe not configured."""
        service = BillingService()

        with patch("app.services.billing.settings") as mock_settings:
            mock_settings.stripe_secret_key = ""

            with pytest.raises(BillingError, match="not configured"):
                service._ensure_stripe_configured()


# ===========================================
# PLAN HELPER TESTS
# ===========================================

class TestPlanHelpers:
    """Test plan-related helper functions."""

    def test_get_plan_features_starter(self):
        """Get starter plan features."""
        plan = PLANS["starter"]
        assert "100 applicant verifications/month" in plan.features

    def test_get_plan_features_enterprise(self):
        """Get enterprise plan features."""
        plan = PLANS["enterprise"]
        assert "Unlimited verifications" in plan.features
        assert "SLA guarantee" in plan.features

    def test_plan_ids_are_unique(self):
        """All plan IDs are unique."""
        plan_ids = [p.id for p in PLANS.values()]
        assert len(plan_ids) == len(set(plan_ids))

    def test_plan_names_are_unique(self):
        """All plan names are unique."""
        plan_names = [p.name for p in PLANS.values()]
        assert len(plan_names) == len(set(plan_names))


# ===========================================
# PRICE FORMATTING TESTS
# ===========================================

class TestPriceFormatting:
    """Test price formatting helpers."""

    def test_starter_price_in_dollars(self):
        """Starter plan is $49/month."""
        plan = PLANS["starter"]
        price_dollars = plan.amount / 100
        assert price_dollars == 49.00

    def test_professional_price_in_dollars(self):
        """Professional plan is $149/month."""
        plan = PLANS["professional"]
        price_dollars = plan.amount / 100
        assert price_dollars == 149.00

    def test_enterprise_price_in_dollars(self):
        """Enterprise plan is $499/month."""
        plan = PLANS["enterprise"]
        price_dollars = plan.amount / 100
        assert price_dollars == 499.00
