"""
Get Clearance - Auth API
=========================
Authentication-related endpoints for user provisioning and management.

These endpoints are called by Auth0 Actions during the login flow.
"""

import secrets
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException, Header, Request, status
from pydantic import BaseModel, EmailStr
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.database import get_db
from app.models.tenant import Tenant, User


router = APIRouter()


# ===========================================
# RATE LIMITING (import limiter from main)
# ===========================================
# Rate limits are applied via decorator to sensitive endpoints


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
    Rate limited to 10 requests per minute per IP.
    """,
)
async def provision_user(
    request_body: ProvisionRequest,
    request: Request,  # For rate limiting
    db: AsyncSession = Depends(get_db),
    x_auth0_user_id: str | None = Header(None),
) -> ProvisionResponse:
    """
    Provision a new user on first login.

    Creates a new tenant and user if they don't exist.
    Returns user context for JWT claims.
    """
    # Basic validation - the header should match the request body
    if x_auth0_user_id and x_auth0_user_id != request_body.auth0_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Auth0 ID mismatch",
        )

    # Check if user already exists
    result = await db.execute(
        select(User).where(User.auth0_id == request_body.auth0_id)
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
        select(User).where(User.email == request_body.email)
    )
    existing_by_email = result.scalar_one_or_none()

    if existing_by_email:
        # Link Auth0 ID to existing user
        existing_by_email.auth0_id = request_body.auth0_id
        if request_body.name and not existing_by_email.name:
            existing_by_email.name = request_body.name
        await db.commit()

        return ProvisionResponse(
            user_id=str(existing_by_email.id),
            tenant_id=str(existing_by_email.tenant_id),
            role=existing_by_email.role,
            permissions=existing_by_email.permissions or get_default_permissions(existing_by_email.role),
        )

    # Create new tenant and user
    # Generate a unique slug from email domain or name
    email_prefix = request_body.email.split("@")[0]
    slug_base = email_prefix.replace(".", "-").replace("_", "-").lower()
    slug = f"{slug_base}-{secrets.token_hex(4)}"

    tenant = Tenant(
        id=uuid4(),
        name=request_body.name or email_prefix,
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
        auth0_id=request_body.auth0_id,
        email=request_body.email,
        name=request_body.name,
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


# ===========================================
# SEED TEST DATA (Development/Demo only)
# ===========================================
# These endpoints are ONLY available in development mode
import random
from datetime import date, datetime, timedelta, timezone

FIRST_NAMES = ["James", "Mary", "John", "Patricia", "Robert", "Jennifer", "Michael", "Linda", "Wei", "Priya"]
LAST_NAMES = ["Smith", "Johnson", "Williams", "Brown", "Jones", "Garcia", "Miller", "Chen", "Patel", "Kim"]
COUNTRIES = ["USA", "GBR", "CAN", "AUS", "DEU", "FRA", "JPN", "SGP"]


# Development-only router for debug/seed endpoints
dev_router = APIRouter(tags=["Development"])


class SeedResponse(BaseModel):
    """Response from seed endpoint."""
    message: str
    tenant_id: str
    applicants_created: int


@dev_router.post(
    "/seed-demo-data",
    response_model=SeedResponse,
    summary="Seed demo applicants for a tenant (DEV ONLY)",
)
async def seed_demo_data(
    tenant_id: str,
    count: int = 10,
    db: AsyncSession = Depends(get_db),
) -> SeedResponse:
    """
    Seed demo applicant data for testing.

    Only works if tenant has < 5 applicants (prevents duplicate seeding).
    """
    from app.models.applicant import Applicant

    # Verify tenant exists
    result = await db.execute(
        select(Tenant).where(Tenant.id == tenant_id)
    )
    tenant = result.scalar_one_or_none()
    if not tenant:
        raise HTTPException(status_code=404, detail="Tenant not found")

    # Check if already seeded
    result = await db.execute(
        select(func.count(Applicant.id)).where(Applicant.tenant_id == tenant_id)
    )
    existing_count = result.scalar() or 0
    if existing_count >= 5:
        return SeedResponse(
            message=f"Tenant already has {existing_count} applicants, skipping seed",
            tenant_id=tenant_id,
            applicants_created=0,
        )

    # Seed applicants
    statuses = ["pending", "in_progress", "review", "approved", "rejected"]
    status_weights = [0.1, 0.15, 0.15, 0.45, 0.15]

    created = 0
    for i in range(count):
        first_name = random.choice(FIRST_NAMES)
        last_name = random.choice(LAST_NAMES)
        status = random.choices(statuses, weights=status_weights)[0]

        risk_score = random.randint(0, 100)
        if status == "rejected":
            risk_score = random.randint(70, 100)
        elif status == "approved":
            risk_score = random.randint(0, 40)

        flags = []
        if risk_score > 60:
            if random.random() > 0.5:
                flags.append("pep")
            if random.random() > 0.7:
                flags.append("sanctions")

        created_at = datetime.now(timezone.utc) - timedelta(days=random.randint(1, 60))

        applicant = Applicant(
            tenant_id=uuid4().hex if not tenant_id else tenant_id,
            external_id=f"demo_{secrets.token_hex(6)}",
            email=f"{first_name.lower()}.{last_name.lower()}{random.randint(1, 99)}@example.com",
            phone=f"+1{random.randint(2000000000, 9999999999)}",
            first_name=first_name,
            last_name=last_name,
            date_of_birth=date(random.randint(1960, 2000), random.randint(1, 12), random.randint(1, 28)),
            nationality=random.choice(COUNTRIES),
            country_of_residence=random.choice(COUNTRIES),
            status=status,
            risk_score=risk_score,
            flags=flags,
            source="demo_seed",
            created_at=created_at,
        )
        db.add(applicant)
        created += 1

    await db.commit()

    return SeedResponse(
        message=f"Successfully seeded {created} demo applicants",
        tenant_id=tenant_id,
        applicants_created=created,
    )


# ===========================================
# DEBUG ENDPOINTS (Development/Testing only)
# ===========================================

class DebugUserResponse(BaseModel):
    """Response from debug user lookup."""
    found: bool
    user_id: str | None = None
    tenant_id: str | None = None
    email: str | None = None
    role: str | None = None
    auth0_id: str | None = None


class DebugTokenResponse(BaseModel):
    """Response showing decoded token claims."""
    raw_claims: dict
    sub: str | None = None
    email: str | None = None
    tenant_id_claim: str | None = None
    user_found_by_sub: bool = False
    user_found_by_email: bool = False
    user_tenant_id: str | None = None


@dev_router.get(
    "/debug/token-claims",
    response_model=DebugTokenResponse,
    summary="Debug: Show token claims and user lookup result (DEV ONLY)",
)
async def debug_token_claims(
    authorization: str = Header(None),
    db: AsyncSession = Depends(get_db),
) -> DebugTokenResponse:
    """
    Debug endpoint to see what's in the token and if user can be found.
    """
    from jose import jwt

    if not authorization or not authorization.startswith("Bearer "):
        return DebugTokenResponse(raw_claims={"error": "No Bearer token provided"})

    token = authorization.replace("Bearer ", "")

    try:
        # Decode without verification to see claims
        claims = jwt.get_unverified_claims(token)
    except Exception as e:
        return DebugTokenResponse(raw_claims={"error": f"Failed to decode token: {str(e)}"})

    sub = claims.get("sub")
    email = claims.get("email") or claims.get("https://getclearance.dev/email")
    tenant_id = claims.get("https://getclearance.dev/tenant_id") or claims.get("tenant_id")

    # Try to find user by sub
    user_by_sub = None
    user_by_email = None

    if sub:
        result = await db.execute(
            select(User).where(User.auth0_id == sub)
        )
        user_by_sub = result.scalar_one_or_none()

    if email and not user_by_sub:
        result = await db.execute(
            select(User).where(User.email == email)
        )
        user_by_email = result.scalar_one_or_none()

    user = user_by_sub or user_by_email

    return DebugTokenResponse(
        raw_claims=claims,
        sub=sub,
        email=email,
        tenant_id_claim=tenant_id,
        user_found_by_sub=user_by_sub is not None,
        user_found_by_email=user_by_email is not None,
        user_tenant_id=str(user.tenant_id) if user else None,
    )


@dev_router.get(
    "/debug/user-lookup",
    response_model=DebugUserResponse,
    summary="Debug: Look up user by email (DEV ONLY)",
)
async def debug_user_lookup(
    email: str,
    db: AsyncSession = Depends(get_db),
) -> DebugUserResponse:
    """
    Debug endpoint to verify user exists in database.

    This is used to test that the user/tenant was created correctly.
    """
    result = await db.execute(
        select(User).where(User.email == email)
    )
    user = result.scalar_one_or_none()

    if not user:
        return DebugUserResponse(found=False)

    return DebugUserResponse(
        found=True,
        user_id=str(user.id),
        tenant_id=str(user.tenant_id),
        email=user.email,
        role=user.role,
        auth0_id=user.auth0_id,
    )


class DebugApplicantsResponse(BaseModel):
    """Response from debug applicants count."""
    tenant_id: str
    count: int
    sample: list[dict] = []


class FullSeedResponse(BaseModel):
    """Response from full seed endpoint."""
    message: str
    tenant_id: str
    counts: dict


@dev_router.get(
    "/debug/applicants-count",
    response_model=DebugApplicantsResponse,
    summary="Debug: Count applicants for a tenant (DEV ONLY)",
)
async def debug_applicants_count(
    tenant_id: str,
    db: AsyncSession = Depends(get_db),
) -> DebugApplicantsResponse:
    """
    Debug endpoint to verify applicants exist for a tenant.
    """
    from app.models.applicant import Applicant

    result = await db.execute(
        select(func.count(Applicant.id)).where(Applicant.tenant_id == tenant_id)
    )
    count = result.scalar() or 0

    # Get sample of 3 applicants
    result = await db.execute(
        select(Applicant).where(Applicant.tenant_id == tenant_id).limit(3)
    )
    applicants = result.scalars().all()
    sample = [
        {"id": str(a.id), "name": f"{a.first_name} {a.last_name}", "status": a.status}
        for a in applicants
    ]

    return DebugApplicantsResponse(
        tenant_id=tenant_id,
        count=count,
        sample=sample,
    )


@dev_router.post(
    "/seed-full-data",
    response_model=FullSeedResponse,
    summary="Seed full demo data including documents, screening, and cases (DEV ONLY)",
)
async def seed_full_data(
    tenant_id: str,
    count: int = 10,
    db: AsyncSession = Depends(get_db),
) -> FullSeedResponse:
    """
    Seed comprehensive demo data for a tenant.

    Creates:
    - Applicants with full details
    - Documents (1-3 per applicant)
    - Screening checks and hits
    - Cases and case notes
    """
    from app.models.applicant import Applicant
    from app.models.document import Document
    from app.models.screening import ScreeningList, ScreeningCheck, ScreeningHit
    from app.models.case import Case, CaseNote

    # Verify tenant exists
    result = await db.execute(select(Tenant).where(Tenant.id == tenant_id))
    tenant = result.scalar_one_or_none()
    if not tenant:
        raise HTTPException(status_code=404, detail="Tenant not found")

    # Get user for assignments
    result = await db.execute(select(User).where(User.tenant_id == tenant_id).limit(1))
    user = result.scalar_one_or_none()
    user_id = user.id if user else None

    # Check existing applicant count
    result = await db.execute(
        select(func.count(Applicant.id)).where(Applicant.tenant_id == tenant_id)
    )
    existing_count = result.scalar() or 0

    counts = {
        "applicants": 0,
        "documents": 0,
        "screening_checks": 0,
        "screening_hits": 0,
        "cases": 0,
        "case_notes": 0,
    }

    # Create screening list
    screening_list = ScreeningList(
        id=uuid4(),
        source="opensanctions",
        version_id=f"OS-{date.today().strftime('%Y%m%d')}-001",
        list_type="combined",
        entity_count=random.randint(50000, 100000),
        published_at=datetime.now(timezone.utc) - timedelta(days=1),
        fetched_at=datetime.now(timezone.utc),
        checksum=secrets.token_hex(32),
    )
    db.add(screening_list)

    case_counter = 1
    DOC_TYPES = ["passport", "drivers_license", "national_id", "utility_bill"]
    DOC_STATUSES = ["pending", "processing", "verified", "rejected"]
    CASE_TYPES = ["sanctions", "pep", "fraud", "verification"]
    CASE_PRIORITIES = ["low", "medium", "high", "critical"]

    for i in range(count):
        first_name = random.choice(FIRST_NAMES)
        last_name = random.choice(LAST_NAMES)
        status = random.choices(["pending", "in_progress", "review", "approved", "rejected"],
                               weights=[0.1, 0.15, 0.15, 0.45, 0.15])[0]

        risk_score = random.randint(0, 100)
        if status == "rejected":
            risk_score = random.randint(70, 100)
        elif status == "approved":
            risk_score = random.randint(0, 40)

        flags = []
        if risk_score > 60:
            if random.random() > 0.5:
                flags.append("pep")
            if random.random() > 0.7:
                flags.append("sanctions")

        created_at = datetime.now(timezone.utc) - timedelta(days=random.randint(1, 60))

        applicant = Applicant(
            tenant_id=tenant_id,
            external_id=f"full_{secrets.token_hex(6)}",
            email=f"{first_name.lower()}.{last_name.lower()}{random.randint(1, 99)}@example.com",
            phone=f"+1{random.randint(2000000000, 9999999999)}",
            first_name=first_name,
            last_name=last_name,
            date_of_birth=date(random.randint(1960, 2000), random.randint(1, 12), random.randint(1, 28)),
            nationality=random.choice(COUNTRIES),
            country_of_residence=random.choice(COUNTRIES),
            status=status,
            risk_score=risk_score,
            flags=flags,
            source="full_seed",
            created_at=created_at,
        )
        db.add(applicant)
        counts["applicants"] += 1

        # Add 1-3 documents
        for _ in range(random.randint(1, 3)):
            doc_type = random.choice(DOC_TYPES)
            doc = Document(
                id=uuid4(),
                tenant_id=tenant_id,
                applicant_id=applicant.id,
                type=doc_type,
                file_name=f"{doc_type}_{secrets.token_hex(4)}.pdf",
                file_size=random.randint(100000, 5000000),
                mime_type="application/pdf",
                storage_path=f"{tenant_id}/applicants/{applicant.id}/{uuid4()}.pdf",
                status=random.choice(DOC_STATUSES),
                uploaded_at=created_at + timedelta(hours=random.randint(0, 24)),
            )
            db.add(doc)
            counts["documents"] += 1

        # Add screening check
        has_hits = len(flags) > 0
        check = ScreeningCheck(
            id=uuid4(),
            tenant_id=tenant_id,
            applicant_id=applicant.id,
            entity_type="individual",
            screened_name=f"{first_name} {last_name}",
            screened_dob=applicant.date_of_birth,
            screened_country=applicant.nationality,
            check_types=["sanctions", "pep", "adverse_media"],
            status="hit" if has_hits else "clear",
            hit_count=len(flags) if has_hits else 0,
            started_at=created_at + timedelta(hours=1),
            completed_at=created_at + timedelta(hours=2),
        )
        db.add(check)
        counts["screening_checks"] += 1

        # Add hits if flagged
        for flag in flags:
            if flag in ["pep", "sanctions"]:
                hit = ScreeningHit(
                    id=uuid4(),
                    check_id=check.id,
                    list_id=screening_list.id,
                    list_source=screening_list.source,
                    list_version_id=screening_list.version_id,
                    hit_type=flag,
                    matched_entity_id=f"os-{secrets.token_hex(8)}",
                    matched_name=f"{random.choice(FIRST_NAMES)} {last_name}",
                    confidence=random.uniform(60, 95),
                    matched_fields=["name", "dob"] if random.random() > 0.5 else ["name"],
                    match_type=random.choice(["true_positive", "potential_match", "false_positive"]),
                    resolution_status=random.choice(["pending", "confirmed_true", "confirmed_false"]),
                    created_at=check.completed_at,
                )
                db.add(hit)
                counts["screening_hits"] += 1

        # Add case for high-risk applicants (30% chance)
        if risk_score > 50 and random.random() > 0.7:
            case_status = random.choice(["open", "in_progress", "resolved", "closed"])
            case = Case(
                id=uuid4(),
                tenant_id=tenant_id,
                applicant_id=applicant.id,
                case_number=f"CASE-2025-{case_counter:03d}",
                type=random.choice(CASE_TYPES),
                title=f"Review - {first_name} {last_name}",
                description=f"Auto-generated case for risk review",
                priority=random.choice(CASE_PRIORITIES),
                status=case_status,
                assignee_id=user_id if case_status in ["in_progress", "resolved"] else None,
                source="screening_hit" if has_hits else "manual",
                opened_at=created_at + timedelta(days=1),
                resolved_at=created_at + timedelta(days=3) if case_status in ["resolved", "closed"] else None,
            )
            db.add(case)
            counts["cases"] += 1
            case_counter += 1

            # Add case note
            if case_status in ["in_progress", "resolved", "closed"]:
                note = CaseNote(
                    id=uuid4(),
                    case_id=case.id,
                    author_id=user_id,
                    content=f"Investigation note: Reviewed risk factors. Status: {case_status}",
                    created_at=created_at + timedelta(days=2),
                )
                db.add(note)
                counts["case_notes"] += 1

    await db.commit()

    return FullSeedResponse(
        message=f"Successfully seeded full data (tenant had {existing_count} applicants before)",
        tenant_id=tenant_id,
        counts=counts,
    )


# ===========================================
# CONDITIONAL INCLUDE OF DEV ROUTER
# ===========================================
# Only include debug/seed endpoints in development mode
if settings.is_development():
    router.include_router(dev_router)
