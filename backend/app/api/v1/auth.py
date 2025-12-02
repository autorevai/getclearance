"""
Get Clearance - Auth API
=========================
Authentication-related endpoints for user provisioning and management.

These endpoints are called by Auth0 Actions during the login flow.
"""

import secrets
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException, Header, status
from pydantic import BaseModel, EmailStr
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.tenant import Tenant, User


router = APIRouter()


class ProvisionRequest(BaseModel):
    """Request body for user provisioning."""
    auth0_id: str
    email: EmailStr
    name: str | None = None


class ProvisionResponse(BaseModel):
    """Response from user provisioning."""
    user_id: str
    tenant_id: str
    role: str
    permissions: list[str]


@router.post(
    "/provision",
    response_model=ProvisionResponse,
    summary="Provision user on first login",
    description="""
    Called by Auth0 Action during first login to create tenant and user.

    This endpoint:
    1. Checks if user already exists by auth0_id
    2. If not, creates a new tenant and user
    3. Returns tenant_id, role, and permissions for JWT claims

    Security: This endpoint is called by Auth0 Action with X-Auth0-User-Id header.
    """,
)
async def provision_user(
    request: ProvisionRequest,
    db: AsyncSession = Depends(get_db),
    x_auth0_user_id: str | None = Header(None),
) -> ProvisionResponse:
    """
    Provision a new user on first login.

    Creates a new tenant and user if they don't exist.
    Returns user context for JWT claims.
    """
    # Basic validation - the header should match the request
    if x_auth0_user_id and x_auth0_user_id != request.auth0_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Auth0 ID mismatch",
        )

    # Check if user already exists
    result = await db.execute(
        select(User).where(User.auth0_id == request.auth0_id)
    )
    existing_user = result.scalar_one_or_none()

    if existing_user:
        # User exists, return their context
        return ProvisionResponse(
            user_id=str(existing_user.id),
            tenant_id=str(existing_user.tenant_id),
            role=existing_user.role,
            permissions=existing_user.permissions or get_default_permissions(existing_user.role),
        )

    # Check if user exists by email (maybe created before Auth0 link)
    result = await db.execute(
        select(User).where(User.email == request.email)
    )
    existing_by_email = result.scalar_one_or_none()

    if existing_by_email:
        # Link Auth0 ID to existing user
        existing_by_email.auth0_id = request.auth0_id
        if request.name and not existing_by_email.name:
            existing_by_email.name = request.name
        await db.commit()

        return ProvisionResponse(
            user_id=str(existing_by_email.id),
            tenant_id=str(existing_by_email.tenant_id),
            role=existing_by_email.role,
            permissions=existing_by_email.permissions or get_default_permissions(existing_by_email.role),
        )

    # Create new tenant and user
    # Generate a unique slug from email domain or name
    email_prefix = request.email.split("@")[0]
    slug_base = email_prefix.replace(".", "-").replace("_", "-").lower()
    slug = f"{slug_base}-{secrets.token_hex(4)}"

    tenant = Tenant(
        id=uuid4(),
        name=request.name or email_prefix,
        slug=slug,
        settings={
            "api_key": f"gc_live_{secrets.token_urlsafe(32)}",
        },
        plan="starter",
        status="active",
    )
    db.add(tenant)

    # First user in tenant is admin
    user = User(
        id=uuid4(),
        tenant_id=tenant.id,
        auth0_id=request.auth0_id,
        email=request.email,
        name=request.name,
        role="admin",
        permissions=get_default_permissions("admin"),
        status="active",
    )
    db.add(user)

    await db.commit()

    return ProvisionResponse(
        user_id=str(user.id),
        tenant_id=str(tenant.id),
        role=user.role,
        permissions=user.permissions,
    )


def get_default_permissions(role: str) -> list[str]:
    """Get default permissions for a role."""
    permissions_by_role = {
        "admin": [
            "read:applicants",
            "write:applicants",
            "delete:applicants",
            "read:documents",
            "write:documents",
            "read:screening",
            "write:screening",
            "read:cases",
            "write:cases",
            "read:settings",
            "write:settings",
            "admin:*",
        ],
        "reviewer": [
            "read:applicants",
            "write:applicants",
            "read:documents",
            "write:documents",
            "read:screening",
            "write:screening",
            "read:cases",
            "write:cases",
        ],
        "analyst": [
            "read:applicants",
            "read:documents",
            "read:screening",
            "read:cases",
            "write:cases",
        ],
        "viewer": [
            "read:applicants",
            "read:documents",
            "read:screening",
            "read:cases",
        ],
    }
    return permissions_by_role.get(role, permissions_by_role["viewer"])
