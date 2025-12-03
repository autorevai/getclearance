"""
Get Clearance - Billing Service
===============================
Stripe integration for subscription management, invoices, and payment methods.

Features:
- Subscription management (create, update, cancel)
- Invoice retrieval and PDF download
- Payment method management
- Customer portal sessions
- Webhook event handling
"""

from dataclasses import dataclass
from datetime import datetime
from typing import Optional
from uuid import UUID
import logging

import stripe
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.models.tenant import Tenant

logger = logging.getLogger(__name__)

# Initialize Stripe
stripe.api_key = settings.stripe_secret_key


class BillingError(Exception):
    """Custom exception for billing errors."""
    pass


@dataclass
class SubscriptionPlan:
    """Subscription plan details."""
    id: str
    name: str
    price_id: str
    amount: int  # in cents
    interval: str  # month or year
    features: list[str]


# Available subscription plans
PLANS = {
    "starter": SubscriptionPlan(
        id="starter",
        name="Starter",
        price_id=settings.stripe_price_id_starter,
        amount=4900,  # $49/month
        interval="month",
        features=[
            "100 applicant verifications/month",
            "500 document verifications/month",
            "200 screening checks/month",
            "Email support",
            "Basic analytics",
        ],
    ),
    "professional": SubscriptionPlan(
        id="professional",
        name="Professional",
        price_id=settings.stripe_price_id_professional,
        amount=14900,  # $149/month
        interval="month",
        features=[
            "1,000 applicant verifications/month",
            "5,000 document verifications/month",
            "2,000 screening checks/month",
            "Priority support",
            "Advanced analytics",
            "Custom workflows",
            "API access",
        ],
    ),
    "enterprise": SubscriptionPlan(
        id="enterprise",
        name="Enterprise",
        price_id=settings.stripe_price_id_enterprise,
        amount=49900,  # $499/month
        interval="month",
        features=[
            "Unlimited verifications",
            "Unlimited screenings",
            "Dedicated support",
            "Full analytics suite",
            "Custom integrations",
            "SLA guarantee",
            "On-premise option",
        ],
    ),
}


@dataclass
class SubscriptionInfo:
    """Current subscription details."""
    id: str
    status: str
    plan_id: str
    plan_name: str
    current_period_start: datetime
    current_period_end: datetime
    cancel_at_period_end: bool
    canceled_at: Optional[datetime]
    amount: int
    interval: str
    payment_method: Optional[dict]


@dataclass
class InvoiceInfo:
    """Invoice details."""
    id: str
    number: str
    status: str
    amount_due: int
    amount_paid: int
    currency: str
    created: datetime
    due_date: Optional[datetime]
    paid_at: Optional[datetime]
    pdf_url: Optional[str]
    hosted_invoice_url: Optional[str]


class BillingService:
    """Service for managing billing and subscriptions via Stripe."""

    def _ensure_stripe_configured(self):
        """Check that Stripe is properly configured."""
        if not settings.stripe_secret_key:
            raise BillingError("Stripe is not configured. Please set STRIPE_SECRET_KEY.")

    async def get_or_create_customer(
        self,
        db: AsyncSession,
        tenant_id: UUID,
        email: str,
        name: Optional[str] = None,
    ) -> str:
        """
        Get or create a Stripe customer for the tenant.

        Args:
            db: Database session
            tenant_id: Tenant UUID
            email: Customer email
            name: Customer name

        Returns:
            Stripe customer ID
        """
        self._ensure_stripe_configured()

        # Check if tenant has a Stripe customer ID
        tenant = await db.get(Tenant, tenant_id)
        if not tenant:
            raise BillingError("Tenant not found")

        # Return existing customer ID if available
        if hasattr(tenant, 'stripe_customer_id') and tenant.stripe_customer_id:
            return tenant.stripe_customer_id

        # Create new Stripe customer
        try:
            customer = stripe.Customer.create(
                email=email,
                name=name,
                metadata={
                    "tenant_id": str(tenant_id),
                },
            )

            # Store customer ID in tenant (if column exists)
            # This would need a migration to add stripe_customer_id column
            # For now, we'll just return the customer ID

            logger.info(f"Created Stripe customer {customer.id} for tenant {tenant_id}")
            return customer.id

        except stripe.error.StripeError as e:
            logger.error(f"Stripe error creating customer: {e}")
            raise BillingError(f"Failed to create customer: {str(e)}")

    async def get_subscription(
        self,
        db: AsyncSession,
        tenant_id: UUID,
        customer_id: str,
    ) -> Optional[SubscriptionInfo]:
        """
        Get current subscription for a customer.

        Args:
            db: Database session
            tenant_id: Tenant UUID
            customer_id: Stripe customer ID

        Returns:
            SubscriptionInfo or None if no active subscription
        """
        self._ensure_stripe_configured()

        try:
            subscriptions = stripe.Subscription.list(
                customer=customer_id,
                status="all",
                limit=1,
            )

            if not subscriptions.data:
                return None

            sub = subscriptions.data[0]
            price = sub["items"]["data"][0]["price"]

            # Find plan by price ID
            plan_id = "starter"
            plan_name = "Starter"
            for pid, plan in PLANS.items():
                if plan.price_id == price["id"]:
                    plan_id = pid
                    plan_name = plan.name
                    break

            # Get payment method if available
            payment_method = None
            if sub.get("default_payment_method"):
                try:
                    pm = stripe.PaymentMethod.retrieve(sub["default_payment_method"])
                    if pm.type == "card":
                        payment_method = {
                            "type": "card",
                            "brand": pm.card.brand,
                            "last4": pm.card.last4,
                            "exp_month": pm.card.exp_month,
                            "exp_year": pm.card.exp_year,
                        }
                except stripe.error.StripeError:
                    pass

            return SubscriptionInfo(
                id=sub["id"],
                status=sub["status"],
                plan_id=plan_id,
                plan_name=plan_name,
                current_period_start=datetime.fromtimestamp(sub["current_period_start"]),
                current_period_end=datetime.fromtimestamp(sub["current_period_end"]),
                cancel_at_period_end=sub.get("cancel_at_period_end", False),
                canceled_at=datetime.fromtimestamp(sub["canceled_at"]) if sub.get("canceled_at") else None,
                amount=price["unit_amount"],
                interval=price["recurring"]["interval"],
                payment_method=payment_method,
            )

        except stripe.error.StripeError as e:
            logger.error(f"Stripe error getting subscription: {e}")
            raise BillingError(f"Failed to get subscription: {str(e)}")

    async def create_subscription(
        self,
        customer_id: str,
        plan_id: str,
        payment_method_id: Optional[str] = None,
    ) -> SubscriptionInfo:
        """
        Create a new subscription for a customer.

        Args:
            customer_id: Stripe customer ID
            plan_id: Plan identifier (starter, professional, enterprise)
            payment_method_id: Stripe payment method ID

        Returns:
            SubscriptionInfo for the new subscription
        """
        self._ensure_stripe_configured()

        plan = PLANS.get(plan_id)
        if not plan or not plan.price_id:
            raise BillingError(f"Invalid plan: {plan_id}")

        try:
            # Attach payment method if provided
            if payment_method_id:
                stripe.PaymentMethod.attach(
                    payment_method_id,
                    customer=customer_id,
                )
                stripe.Customer.modify(
                    customer_id,
                    invoice_settings={"default_payment_method": payment_method_id},
                )

            # Create subscription
            subscription = stripe.Subscription.create(
                customer=customer_id,
                items=[{"price": plan.price_id}],
                payment_behavior="default_incomplete",
                expand=["latest_invoice.payment_intent"],
            )

            return SubscriptionInfo(
                id=subscription["id"],
                status=subscription["status"],
                plan_id=plan_id,
                plan_name=plan.name,
                current_period_start=datetime.fromtimestamp(subscription["current_period_start"]),
                current_period_end=datetime.fromtimestamp(subscription["current_period_end"]),
                cancel_at_period_end=False,
                canceled_at=None,
                amount=plan.amount,
                interval=plan.interval,
                payment_method=None,
            )

        except stripe.error.StripeError as e:
            logger.error(f"Stripe error creating subscription: {e}")
            raise BillingError(f"Failed to create subscription: {str(e)}")

    async def update_subscription(
        self,
        subscription_id: str,
        new_plan_id: str,
    ) -> SubscriptionInfo:
        """
        Update a subscription to a new plan.

        Args:
            subscription_id: Stripe subscription ID
            new_plan_id: New plan identifier

        Returns:
            Updated SubscriptionInfo
        """
        self._ensure_stripe_configured()

        plan = PLANS.get(new_plan_id)
        if not plan or not plan.price_id:
            raise BillingError(f"Invalid plan: {new_plan_id}")

        try:
            # Get current subscription
            subscription = stripe.Subscription.retrieve(subscription_id)

            # Update subscription item
            stripe.Subscription.modify(
                subscription_id,
                items=[{
                    "id": subscription["items"]["data"][0]["id"],
                    "price": plan.price_id,
                }],
                proration_behavior="create_prorations",
            )

            # Retrieve updated subscription
            subscription = stripe.Subscription.retrieve(subscription_id)

            return SubscriptionInfo(
                id=subscription["id"],
                status=subscription["status"],
                plan_id=new_plan_id,
                plan_name=plan.name,
                current_period_start=datetime.fromtimestamp(subscription["current_period_start"]),
                current_period_end=datetime.fromtimestamp(subscription["current_period_end"]),
                cancel_at_period_end=subscription.get("cancel_at_period_end", False),
                canceled_at=None,
                amount=plan.amount,
                interval=plan.interval,
                payment_method=None,
            )

        except stripe.error.StripeError as e:
            logger.error(f"Stripe error updating subscription: {e}")
            raise BillingError(f"Failed to update subscription: {str(e)}")

    async def cancel_subscription(
        self,
        subscription_id: str,
        at_period_end: bool = True,
    ) -> SubscriptionInfo:
        """
        Cancel a subscription.

        Args:
            subscription_id: Stripe subscription ID
            at_period_end: If True, cancel at end of period; if False, cancel immediately

        Returns:
            Updated SubscriptionInfo
        """
        self._ensure_stripe_configured()

        try:
            if at_period_end:
                subscription = stripe.Subscription.modify(
                    subscription_id,
                    cancel_at_period_end=True,
                )
            else:
                subscription = stripe.Subscription.delete(subscription_id)

            plan_id = "starter"
            plan_name = "Starter"
            price = subscription["items"]["data"][0]["price"]
            for pid, plan in PLANS.items():
                if plan.price_id == price["id"]:
                    plan_id = pid
                    plan_name = plan.name
                    break

            return SubscriptionInfo(
                id=subscription["id"],
                status=subscription["status"],
                plan_id=plan_id,
                plan_name=plan_name,
                current_period_start=datetime.fromtimestamp(subscription["current_period_start"]),
                current_period_end=datetime.fromtimestamp(subscription["current_period_end"]),
                cancel_at_period_end=subscription.get("cancel_at_period_end", False),
                canceled_at=datetime.fromtimestamp(subscription["canceled_at"]) if subscription.get("canceled_at") else None,
                amount=price["unit_amount"],
                interval=price["recurring"]["interval"],
                payment_method=None,
            )

        except stripe.error.StripeError as e:
            logger.error(f"Stripe error canceling subscription: {e}")
            raise BillingError(f"Failed to cancel subscription: {str(e)}")

    async def get_invoices(
        self,
        customer_id: str,
        limit: int = 10,
    ) -> list[InvoiceInfo]:
        """
        Get invoices for a customer.

        Args:
            customer_id: Stripe customer ID
            limit: Maximum number of invoices to retrieve

        Returns:
            List of InvoiceInfo
        """
        self._ensure_stripe_configured()

        try:
            invoices = stripe.Invoice.list(
                customer=customer_id,
                limit=limit,
            )

            return [
                InvoiceInfo(
                    id=inv["id"],
                    number=inv.get("number") or inv["id"],
                    status=inv["status"],
                    amount_due=inv["amount_due"],
                    amount_paid=inv["amount_paid"],
                    currency=inv["currency"].upper(),
                    created=datetime.fromtimestamp(inv["created"]),
                    due_date=datetime.fromtimestamp(inv["due_date"]) if inv.get("due_date") else None,
                    paid_at=datetime.fromtimestamp(inv["status_transitions"]["paid_at"]) if inv.get("status_transitions", {}).get("paid_at") else None,
                    pdf_url=inv.get("invoice_pdf"),
                    hosted_invoice_url=inv.get("hosted_invoice_url"),
                )
                for inv in invoices.data
            ]

        except stripe.error.StripeError as e:
            logger.error(f"Stripe error getting invoices: {e}")
            raise BillingError(f"Failed to get invoices: {str(e)}")

    async def get_invoice_pdf_url(
        self,
        invoice_id: str,
    ) -> str:
        """
        Get PDF download URL for an invoice.

        Args:
            invoice_id: Stripe invoice ID

        Returns:
            PDF download URL
        """
        self._ensure_stripe_configured()

        try:
            invoice = stripe.Invoice.retrieve(invoice_id)
            if not invoice.get("invoice_pdf"):
                raise BillingError("Invoice PDF not available")
            return invoice["invoice_pdf"]

        except stripe.error.StripeError as e:
            logger.error(f"Stripe error getting invoice PDF: {e}")
            raise BillingError(f"Failed to get invoice PDF: {str(e)}")

    async def create_setup_intent(
        self,
        customer_id: str,
    ) -> dict:
        """
        Create a SetupIntent for adding a payment method.

        Args:
            customer_id: Stripe customer ID

        Returns:
            SetupIntent client secret and ID
        """
        self._ensure_stripe_configured()

        try:
            setup_intent = stripe.SetupIntent.create(
                customer=customer_id,
                payment_method_types=["card"],
            )

            return {
                "id": setup_intent["id"],
                "client_secret": setup_intent["client_secret"],
            }

        except stripe.error.StripeError as e:
            logger.error(f"Stripe error creating setup intent: {e}")
            raise BillingError(f"Failed to create setup intent: {str(e)}")

    async def get_payment_methods(
        self,
        customer_id: str,
    ) -> list[dict]:
        """
        Get payment methods for a customer.

        Args:
            customer_id: Stripe customer ID

        Returns:
            List of payment method details
        """
        self._ensure_stripe_configured()

        try:
            payment_methods = stripe.PaymentMethod.list(
                customer=customer_id,
                type="card",
            )

            return [
                {
                    "id": pm["id"],
                    "type": "card",
                    "brand": pm["card"]["brand"],
                    "last4": pm["card"]["last4"],
                    "exp_month": pm["card"]["exp_month"],
                    "exp_year": pm["card"]["exp_year"],
                    "is_default": False,  # Would need to check customer default
                }
                for pm in payment_methods.data
            ]

        except stripe.error.StripeError as e:
            logger.error(f"Stripe error getting payment methods: {e}")
            raise BillingError(f"Failed to get payment methods: {str(e)}")

    async def delete_payment_method(
        self,
        payment_method_id: str,
    ) -> None:
        """
        Delete a payment method.

        Args:
            payment_method_id: Stripe payment method ID
        """
        self._ensure_stripe_configured()

        try:
            stripe.PaymentMethod.detach(payment_method_id)

        except stripe.error.StripeError as e:
            logger.error(f"Stripe error deleting payment method: {e}")
            raise BillingError(f"Failed to delete payment method: {str(e)}")

    async def create_portal_session(
        self,
        customer_id: str,
        return_url: str,
    ) -> str:
        """
        Create a Stripe customer portal session.

        Args:
            customer_id: Stripe customer ID
            return_url: URL to redirect to after portal session

        Returns:
            Portal session URL
        """
        self._ensure_stripe_configured()

        try:
            session = stripe.billing_portal.Session.create(
                customer=customer_id,
                return_url=return_url,
            )

            return session["url"]

        except stripe.error.StripeError as e:
            logger.error(f"Stripe error creating portal session: {e}")
            raise BillingError(f"Failed to create portal session: {str(e)}")

    def get_available_plans(self) -> list[dict]:
        """Get list of available subscription plans."""
        return [
            {
                "id": plan.id,
                "name": plan.name,
                "amount": plan.amount,
                "amount_formatted": f"${plan.amount / 100:.2f}",
                "interval": plan.interval,
                "features": plan.features,
            }
            for plan in PLANS.values()
            if plan.price_id  # Only include plans with configured price IDs
        ]


# Singleton instance
billing_service = BillingService()
