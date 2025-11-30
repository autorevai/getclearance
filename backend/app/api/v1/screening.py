"""
Get Clearance - Screening API
==============================
AML/Sanctions/PEP screening endpoints.
"""

from datetime import datetime
from typing import Annotated, Any
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.dependencies import TenantDB, AuthenticatedUser, require_permission
from app.models import ScreeningCheck, ScreeningHit, Applicant

router = APIRouter()


# ===========================================
# SCHEMAS
# ===========================================

class RunScreeningRequest(BaseModel):
    """Request to run screening check."""
    applicant_id: UUID | None = None
    company_id: UUID | None = None
    # Or manual entry:
    name: str | None = None
    date_of_birth: str | None = None  # YYYY-MM-DD
    country: str | None = None
    check_types: list[str] = Field(default=["sanctions", "pep"])


class ScreeningHitResponse(BaseModel):
    """Screening hit details."""
    id: UUID
    hit_type: str
    matched_name: str
    confidence: float
    matched_fields: list[str]
    list_source: str
    list_version_id: str
    resolution_status: str
    resolution_notes: str | None
    resolved_at: datetime | None
    # PEP fields
    pep_tier: int | None
    pep_position: str | None
    # Adverse media
    article_url: str | None
    article_title: str | None
    categories: list[str]
    created_at: datetime
    
    model_config = {"from_attributes": True}


class ScreeningCheckResponse(BaseModel):
    """Screening check with hits."""
    id: UUID
    entity_type: str
    screened_name: str
    screened_dob: str | None
    screened_country: str | None
    check_types: list[str]
    status: str
    hit_count: int
    started_at: datetime
    completed_at: datetime | None
    hits: list[ScreeningHitResponse] = []
    
    model_config = {"from_attributes": True}


class ScreeningListResponse(BaseModel):
    """List of screening checks."""
    items: list[ScreeningCheckResponse]
    total: int
    limit: int
    offset: int


class ResolveHitRequest(BaseModel):
    """Resolve a screening hit."""
    resolution: str = Field(..., pattern="^(confirmed_true|confirmed_false)$")
    notes: str | None = None


# ===========================================
# RUN SCREENING
# ===========================================
@router.post("/check", response_model=ScreeningCheckResponse)
async def run_screening(
    data: RunScreeningRequest,
    db: TenantDB,
    user: AuthenticatedUser,
):
    """
    Run a screening check against sanctions/PEP lists.
    
    You can either:
    - Provide an applicant_id to screen an existing applicant
    - Provide name/dob/country for ad-hoc screening
    
    Returns immediately with check ID. Poll for results or wait for webhook.
    """
    # Determine what we're screening
    if data.applicant_id:
        # Get applicant details
        query = select(Applicant).where(
            Applicant.id == data.applicant_id,
            Applicant.tenant_id == user.tenant_id,
        )
        result = await db.execute(query)
        applicant = result.scalar_one_or_none()
        
        if not applicant:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Applicant not found",
            )
        
        screened_name = applicant.full_name
        screened_dob = applicant.date_of_birth
        screened_country = applicant.nationality or applicant.country_of_residence
        entity_type = "individual"
    elif data.name:
        screened_name = data.name
        screened_dob = data.date_of_birth
        screened_country = data.country
        entity_type = "individual"
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Must provide either applicant_id or name",
        )
    
    # Create screening check
    check = ScreeningCheck(
        tenant_id=user.tenant_id,
        applicant_id=data.applicant_id,
        company_id=data.company_id,
        entity_type=entity_type,
        screened_name=screened_name,
        screened_dob=screened_dob,
        screened_country=screened_country,
        check_types=data.check_types,
        status="pending",
        started_at=datetime.utcnow(),
    )
    db.add(check)
    await db.flush()
    
    # TODO: Enqueue async screening job
    # For now, simulate immediate completion with mock data
    check.status = "clear"
    check.completed_at = datetime.utcnow()
    
    await db.refresh(check)
    return ScreeningCheckResponse.model_validate(check)


# ===========================================
# LIST SCREENING CHECKS
# ===========================================
@router.get("/checks", response_model=ScreeningListResponse)
async def list_checks(
    db: TenantDB,
    user: AuthenticatedUser,
    applicant_id: Annotated[UUID | None, Query()] = None,
    status: Annotated[str | None, Query()] = None,
    limit: Annotated[int, Query(ge=1, le=100)] = 50,
    offset: Annotated[int, Query(ge=0)] = 0,
):
    """
    List screening checks with optional filtering.
    """
    query = (
        select(ScreeningCheck)
        .where(ScreeningCheck.tenant_id == user.tenant_id)
        .options(selectinload(ScreeningCheck.hits))
    )
    count_query = select(func.count(ScreeningCheck.id)).where(
        ScreeningCheck.tenant_id == user.tenant_id
    )
    
    if applicant_id:
        query = query.where(ScreeningCheck.applicant_id == applicant_id)
        count_query = count_query.where(ScreeningCheck.applicant_id == applicant_id)
    
    if status:
        query = query.where(ScreeningCheck.status == status)
        count_query = count_query.where(ScreeningCheck.status == status)
    
    # Get total
    total_result = await db.execute(count_query)
    total = total_result.scalar() or 0
    
    # Get items
    query = query.order_by(ScreeningCheck.created_at.desc()).offset(offset).limit(limit)
    result = await db.execute(query)
    checks = result.scalars().all()
    
    return ScreeningListResponse(
        items=[ScreeningCheckResponse.model_validate(c) for c in checks],
        total=total,
        limit=limit,
        offset=offset,
    )


# ===========================================
# GET SCREENING CHECK
# ===========================================
@router.get("/checks/{check_id}", response_model=ScreeningCheckResponse)
async def get_check(
    check_id: UUID,
    db: TenantDB,
    user: AuthenticatedUser,
):
    """
    Get screening check details with hits.
    """
    query = (
        select(ScreeningCheck)
        .where(
            ScreeningCheck.id == check_id,
            ScreeningCheck.tenant_id == user.tenant_id,
        )
        .options(selectinload(ScreeningCheck.hits))
    )
    result = await db.execute(query)
    check = result.scalar_one_or_none()
    
    if not check:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Screening check not found",
        )
    
    return ScreeningCheckResponse.model_validate(check)


# ===========================================
# RESOLVE HIT
# ===========================================
@router.patch("/hits/{hit_id}", response_model=ScreeningHitResponse)
async def resolve_hit(
    hit_id: UUID,
    data: ResolveHitRequest,
    db: TenantDB,
    user: Annotated[AuthenticatedUser, Depends(require_permission("review:screening"))],
):
    """
    Resolve a screening hit as true match or false positive.
    
    Requires review:screening permission.
    """
    query = (
        select(ScreeningHit)
        .join(ScreeningCheck)
        .where(
            ScreeningHit.id == hit_id,
            ScreeningCheck.tenant_id == user.tenant_id,
        )
    )
    result = await db.execute(query)
    hit = result.scalar_one_or_none()
    
    if not hit:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Hit not found",
        )
    
    if hit.is_resolved:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Hit already resolved",
        )
    
    # Update hit
    hit.resolution_status = data.resolution
    hit.resolution_notes = data.notes
    hit.resolved_by = UUID(user.id)
    hit.resolved_at = datetime.utcnow()
    
    # TODO: If confirmed_true, update applicant flags
    # TODO: Create case if needed
    # TODO: Create audit log entry
    
    await db.flush()
    await db.refresh(hit)
    
    return ScreeningHitResponse.model_validate(hit)
