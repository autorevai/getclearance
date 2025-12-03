"""
Get Clearance - Billing API
============================
Endpoints for subscription management, usage tracking, and invoices.

Endpoints:
- GET  /usage              - Current period usage
- GET  /usage/history      - Historical usage
- GET  /subscription       - Current subscription
- POST /subscription       - Create/update subscription
- DELETE /subscription     - Cancel subscription
- GET  /invoices           - Invoice list
- GET  /invoices/{id}/pdf  - Download invoice PDF
- POST /payment-method     - Create setup intent for adding payment
- GET  /payment-methods    - List payment methods
- DELETE /payment-methods/{id} - Remove payment method
- GET  /plans              - List available plans
- POST /portal             - Create customer portal session
"""

from typing import Annotated, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies import TenantDB, AuthenticatedUser, require_permission
from app.services.usage import usage_service
from app.services.billing import billing_service, BillingError, PLANS


router = APIRouter()


# ===========================================
# REQUEST/RESPONSE SCHEMAS
# ===========================================

class UsageResponse(BaseModel):
    """Current usage metrics response."""
    tenant_id: str
    period_start: str
    period_end: str
    metrics: dict


class UsageHistoryResponse(BaseModel):
    """Historical usage response."""
    history: list[dict]


class SubscriptionRequest(BaseModel):
    """Create/update subscription request."""
    plan_id: str = Field(..., description="Plan ID: starter, professional, or enterprise")
    payment_method_id: Optional[str] = Field(None, description="Stripe payment method ID")


class SubscriptionResponse(BaseModel):
    """Subscription details response."""
    id: str
    status: str
    plan_id: str
    plan_name: str
    current_period_start: str
    current_period_end: str
    cancel_at_period_end: bool
    canceled_at: Optional[str]
    amount: int
    amount_formatted: str
    interval: str
    payment_method: Optional[dict]


class InvoiceResponse(BaseModel):
    """Invoice details response."""
    id: str
    number: str
    status: str
    amount_due: int
    amount_due_formatted: str
    amount_paid: int
    currency: str
    created: str
    due_date: Optional[str]
    paid_at: Optional[str]
    pdf_url: Optional[str]
    hosted_invoice_url: Optional[str]


class SetupIntentResponse(BaseModel):
    """Setup intent for adding payment method."""
    id: str
    client_secret: str


class PaymentMethodResponse(BaseModel):
    """Payment method details."""
    id: str
    type: str
    brand: str
    last4: str
    exp_month: int
    exp_year: int
    is_default: bool


class PlanResponse(BaseModel):
    """Subscription plan details."""
    id: str
    name: str
    amount: int
    amount_formatted: str
    interval: str
    features: list[str]


class PortalRequest(BaseModel):
    """Customer portal session request."""
    return_url: str = Field(..., description="URL to redirect to after portal session")


class PortalResponse(BaseModel):
    """Customer portal session response."""
    url: str


# ===========================================
# USAGE ENDPOINTS
# ===========================================

@router.get("/usage", response_model=UsageResponse)
async def get_current_usage(
    db: TenantDB,
    user: Annotated[AuthenticatedUser, Depends(require_permission("read:settings"))],
):
    """
    Get usage metrics for the current billing period.

    Returns counts for applicants, documents, screenings, device scans, and API calls
    along with plan limits and percentage used.
    """
    # Get current plan from tenant (default to starter)
    # In production, this would come from the subscription
    plan = "starter"

    usage = await usage_service.get_current_usage(
        db=db,
        tenant_id=user.tenant_id,
        plan=plan,
    )

    return usage.to_dict()


@router.get("/usage/history", response_model=UsageHistoryResponse)
async def get_usage_history(
    db: TenantDB,
    user: Annotated[AuthenticatedUser, Depends(require_permission("read:settings"))],
    months: int = Query(6, ge=1, le=12, description="Number of months to retrieve"),
):
    """
    Get historical usage for the last N months.

    Returns usage counts and estimated costs for each month.
    """
    history = await usage_service.get_usage_history(
        db=db,
        tenant_id=user.tenant_id,
        months=months,
    )

    return {"history": history}


# ===========================================
# SUBSCRIPTION ENDPOINTS
# ===========================================

@router.get("/subscription", response_model=Optional[SubscriptionResponse])
async def get_subscription(
    db: TenantDB,
    user: Annotated[AuthenticatedUser, Depends(require_permission("read:settings"))],
):
    """
    Get current subscription details.

    Returns None if no active subscription.
    """
    try:
        # Get or create Stripe customer
        customer_id = await billing_service.get_or_create_customer(
            db=db,
            tenant_id=user.tenant_id,
            email=user.email,
        )

        subscription = await billing_service.get_subscription(
            db=db,
            tenant_id=user.tenant_id,
            customer_id=customer_id,
        )

        if not subscription:
            return None

        return SubscriptionResponse(
            id=subscription.id,
            status=subscription.status,
            plan_id=subscription.plan_id,
            plan_name=subscription.plan_name,
            current_period_start=subscription.current_period_start.isoformat(),
            current_period_end=subscription.current_period_end.isoformat(),
            cancel_at_period_end=subscription.cancel_at_period_end,
            canceled_at=subscription.canceled_at.isoformat() if subscription.canceled_at else None,
            amount=subscription.amount,
            amount_formatted=f"${subscription.amount / 100:.2f}",
            interval=subscription.interval,
            payment_method=subscription.payment_method,
        )

    except BillingError as e:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=str(e),
        )


@router.post("/subscription", response_model=SubscriptionResponse, status_code=status.HTTP_201_CREATED)
async def create_or_update_subscription(
    data: SubscriptionRequest,
    db: TenantDB,
    user: Annotated[AuthenticatedUser, Depends(require_permission("write:settings"))],
):
    """
    Create a new subscription or update existing one.

    If a subscription exists, it will be updated to the new plan.
    If no subscription exists, a new one will be created.
    """
    try:
        # Get or create Stripe customer
        customer_id = await billing_service.get_or_create_customer(
            db=db,
            tenant_id=user.tenant_id,
            email=user.email,
        )

        # Check for existing subscription
        existing = await billing_service.get_subscription(
            db=db,
            tenant_id=user.tenant_id,
            customer_id=customer_id,
        )

        if existing and existing.status in ["active", "trialing"]:
            # Update existing subscription
            subscription = await billing_service.update_subscription(
                subscription_id=existing.id,
                new_plan_id=data.plan_id,
            )
        else:
            # Create new subscription
            subscription = await billing_service.create_subscription(
                customer_id=customer_id,
                plan_id=data.plan_id,
                payment_method_id=data.payment_method_id,
            )

        return SubscriptionResponse(
            id=subscription.id,
            status=subscription.status,
            plan_id=subscription.plan_id,
            plan_name=subscription.plan_name,
            current_period_start=subscription.current_period_start.isoformat(),
            current_period_end=subscription.current_period_end.isoformat(),
            cancel_at_period_end=subscription.cancel_at_period_end,
            canceled_at=subscription.canceled_at.isoformat() if subscription.canceled_at else None,
            amount=subscription.amount,
            amount_formatted=f"${subscription.amount / 100:.2f}",
            interval=subscription.interval,
            payment_method=subscription.payment_method,
        )

    except BillingError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


@router.delete("/subscription", response_model=SubscriptionResponse)
async def cancel_subscription(
    db: TenantDB,
    user: Annotated[AuthenticatedUser, Depends(require_permission("write:settings"))],
    immediately: bool = Query(False, description="Cancel immediately instead of at period end"),
):
    """
    Cancel the current subscription.

    By default, cancels at the end of the current billing period.
    Set immediately=true to cancel right away.
    """
    try:
        # Get Stripe customer
        customer_id = await billing_service.get_or_create_customer(
            db=db,
            tenant_id=user.tenant_id,
            email=user.email,
        )

        # Get current subscription
        existing = await billing_service.get_subscription(
            db=db,
            tenant_id=user.tenant_id,
            customer_id=customer_id,
        )

        if not existing:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No active subscription found",
            )

        subscription = await billing_service.cancel_subscription(
            subscription_id=existing.id,
            at_period_end=not immediately,
        )

        return SubscriptionResponse(
            id=subscription.id,
            status=subscription.status,
            plan_id=subscription.plan_id,
            plan_name=subscription.plan_name,
            current_period_start=subscription.current_period_start.isoformat(),
            current_period_end=subscription.current_period_end.isoformat(),
            cancel_at_period_end=subscription.cancel_at_period_end,
            canceled_at=subscription.canceled_at.isoformat() if subscription.canceled_at else None,
            amount=subscription.amount,
            amount_formatted=f"${subscription.amount / 100:.2f}",
            interval=subscription.interval,
            payment_method=subscription.payment_method,
        )

    except BillingError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


# ===========================================
# INVOICE ENDPOINTS
# ===========================================

@router.get("/invoices", response_model=list[InvoiceResponse])
async def list_invoices(
    db: TenantDB,
    user: Annotated[AuthenticatedUser, Depends(require_permission("read:settings"))],
    limit: int = Query(10, ge=1, le=100),
):
    """
    List invoices for the current tenant.
    """
    try:
        # Get Stripe customer
        customer_id = await billing_service.get_or_create_customer(
            db=db,
            tenant_id=user.tenant_id,
            email=user.email,
        )

        invoices = await billing_service.get_invoices(
            customer_id=customer_id,
            limit=limit,
        )

        return [
            InvoiceResponse(
                id=inv.id,
                number=inv.number,
                status=inv.status,
                amount_due=inv.amount_due,
                amount_due_formatted=f"${inv.amount_due / 100:.2f}",
                amount_paid=inv.amount_paid,
                currency=inv.currency,
                created=inv.created.isoformat(),
                due_date=inv.due_date.isoformat() if inv.due_date else None,
                paid_at=inv.paid_at.isoformat() if inv.paid_at else None,
                pdf_url=inv.pdf_url,
                hosted_invoice_url=inv.hosted_invoice_url,
            )
            for inv in invoices
        ]

    except BillingError as e:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=str(e),
        )


@router.get("/invoices/{invoice_id}/pdf")
async def get_invoice_pdf(
    invoice_id: str,
    db: TenantDB,
    user: Annotated[AuthenticatedUser, Depends(require_permission("read:settings"))],
):
    """
    Get PDF download URL for an invoice.

    Returns a redirect URL to the Stripe-hosted PDF.
    """
    try:
        pdf_url = await billing_service.get_invoice_pdf_url(invoice_id)
        return {"pdf_url": pdf_url}

    except BillingError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )


# ===========================================
# PAYMENT METHOD ENDPOINTS
# ===========================================

@router.post("/payment-method", response_model=SetupIntentResponse)
async def create_setup_intent(
    db: TenantDB,
    user: Annotated[AuthenticatedUser, Depends(require_permission("write:settings"))],
):
    """
    Create a SetupIntent for adding a new payment method.

    Returns a client_secret to use with Stripe.js for collecting card details.
    """
    try:
        # Get or create Stripe customer
        customer_id = await billing_service.get_or_create_customer(
            db=db,
            tenant_id=user.tenant_id,
            email=user.email,
        )

        setup_intent = await billing_service.create_setup_intent(customer_id)
        return SetupIntentResponse(**setup_intent)

    except BillingError as e:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=str(e),
        )


@router.get("/payment-methods", response_model=list[PaymentMethodResponse])
async def list_payment_methods(
    db: TenantDB,
    user: Annotated[AuthenticatedUser, Depends(require_permission("read:settings"))],
):
    """
    List payment methods for the current tenant.
    """
    try:
        # Get Stripe customer
        customer_id = await billing_service.get_or_create_customer(
            db=db,
            tenant_id=user.tenant_id,
            email=user.email,
        )

        methods = await billing_service.get_payment_methods(customer_id)
        return [PaymentMethodResponse(**m) for m in methods]

    except BillingError as e:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=str(e),
        )


@router.delete("/payment-methods/{payment_method_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_payment_method(
    payment_method_id: str,
    db: TenantDB,
    user: Annotated[AuthenticatedUser, Depends(require_permission("write:settings"))],
):
    """
    Remove a payment method.
    """
    try:
        await billing_service.delete_payment_method(payment_method_id)

    except BillingError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


# ===========================================
# PLAN & PORTAL ENDPOINTS
# ===========================================

@router.get("/plans", response_model=list[PlanResponse])
async def list_plans():
    """
    List available subscription plans.
    """
    plans = billing_service.get_available_plans()
    return [PlanResponse(**p) for p in plans]


@router.post("/portal", response_model=PortalResponse)
async def create_portal_session(
    data: PortalRequest,
    db: TenantDB,
    user: Annotated[AuthenticatedUser, Depends(require_permission("write:settings"))],
):
    """
    Create a Stripe customer portal session.

    Returns a URL to redirect the user to the Stripe-hosted customer portal
    where they can manage their subscription, payment methods, and invoices.
    """
    try:
        # Get Stripe customer
        customer_id = await billing_service.get_or_create_customer(
            db=db,
            tenant_id=user.tenant_id,
            email=user.email,
        )

        portal_url = await billing_service.create_portal_session(
            customer_id=customer_id,
            return_url=data.return_url,
        )

        return PortalResponse(url=portal_url)

    except BillingError as e:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=str(e),
        )
