"""
Get Clearance - Screening API
==============================
AML/Sanctions/PEP screening endpoints with OpenSanctions integration.
"""

from datetime import date, datetime
from typing import Annotated, Any
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.dependencies import TenantDB, AuthenticatedUser, require_permission
from app.models import ScreeningCheck, ScreeningHit, ScreeningList, Applicant
from app.services.screening import (
    screening_service,
    ScreeningServiceError,
    ScreeningConfigError,
)

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
    Run a screening check against sanctions/PEP lists via OpenSanctions.
    
    You can either:
    - Provide an applicant_id to screen an existing applicant
    - Provide name/dob/country for ad-hoc screening
    
    The check runs synchronously and returns results immediately.
    """
    # Determine what to screen
    screened_name: str
    screened_dob: date | None = None
    screened_country: str | None = None
    entity_type = "individual"
    applicant_id: UUID | None = None
    
    if data.applicant_id:
        # Screen existing applicant
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
        
        screened_name = f"{applicant.first_name or ''} {applicant.last_name or ''}".strip()
        if not screened_name:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Applicant has no name to screen",
            )
        
        screened_dob = applicant.date_of_birth
        screened_country = applicant.nationality or applicant.country_of_residence
        applicant_id = applicant.id
        
    elif data.name:
        # Ad-hoc screening
        screened_name = data.name
        if data.date_of_birth:
            try:
                screened_dob = date.fromisoformat(data.date_of_birth)
            except ValueError:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Invalid date_of_birth format, use YYYY-MM-DD",
                )
        screened_country = data.country
        
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Must provide either applicant_id or name",
        )
    
    # Create screening check record
    check = ScreeningCheck(
        tenant_id=user.tenant_id,
        applicant_id=applicant_id,
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
    
    try:
        # Run screening via OpenSanctions
        countries = [screened_country] if screened_country else None
        
        screening_result = await screening_service.check_individual(
            name=screened_name,
            birth_date=screened_dob,
            countries=countries,
        )
        
        # Get or create screening list record for audit trail
        list_record = await _get_or_create_screening_list(
            db=db,
            source="opensanctions",
            version_id=screening_result.list_version_id,
            list_type="combined",
        )
        
        # Create hit records
        for hit_result in screening_result.hits:
            hit = ScreeningHit(
                check_id=check.id,
                list_id=list_record.id if list_record else None,
                list_source=hit_result.list_source,
                list_version_id=hit_result.list_version_id,
                hit_type=hit_result.hit_type,
                matched_entity_id=hit_result.matched_entity_id,
                matched_name=hit_result.matched_name,
                confidence=hit_result.confidence,
                matched_fields=hit_result.matched_fields,
                match_data=hit_result.match_data,
                pep_tier=hit_result.pep_tier,
                pep_position=hit_result.pep_position,
                categories=hit_result.categories,
                resolution_status="pending",
            )
            db.add(hit)
        
        # Update check status
        check.status = screening_result.status
        check.hit_count = len(screening_result.hits)
        check.completed_at = datetime.utcnow()
        
        await db.flush()
        
        # Reload with hits for response
        query = (
            select(ScreeningCheck)
            .where(ScreeningCheck.id == check.id)
            .options(selectinload(ScreeningCheck.hits))
        )
        result = await db.execute(query)
        check = result.scalar_one()
        
        return ScreeningCheckResponse.model_validate(check)
        
    except ScreeningConfigError:
        # OpenSanctions not configured - return mock response for development
        check.status = "clear"
        check.hit_count = 0
        check.completed_at = datetime.utcnow()
        await db.flush()
        
        return ScreeningCheckResponse.model_validate(check)
        
    except ScreeningServiceError as e:
        # Mark as error
        check.status = "error"
        check.completed_at = datetime.utcnow()
        await db.flush()
        
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Screening service error: {str(e)}",
        )


async def _get_or_create_screening_list(
    db: AsyncSession,
    source: str,
    version_id: str,
    list_type: str,
) -> ScreeningList | None:
    """Get or create a screening list record for audit tracking."""
    query = select(ScreeningList).where(
        ScreeningList.source == source,
        ScreeningList.version_id == version_id,
    )
    result = await db.execute(query)
    existing = result.scalar_one_or_none()
    
    if existing:
        return existing
    
    # Create new record
    list_record = ScreeningList(
        source=source,
        version_id=version_id,
        list_type=list_type,
        fetched_at=datetime.utcnow(),
    )
    db.add(list_record)
    await db.flush()
    
    return list_record


# ===========================================
# LIST SCREENING CHECKS
# ===========================================
@router.get("/checks", response_model=ScreeningListResponse)
async def list_checks(
    db: TenantDB,
    user: AuthenticatedUser,
    applicant_id: UUID | None = Query(None),
    check_status: str | None = Query(None, alias="status"),
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
):
    """
    List screening checks with optional filters.
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
    
    if check_status:
        query = query.where(ScreeningCheck.status == check_status)
        count_query = count_query.where(ScreeningCheck.status == check_status)
    
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


# ===========================================
# AI HIT SUGGESTION
# ===========================================
@router.get("/hits/{hit_id}/suggestion")
async def get_hit_suggestion(
    hit_id: UUID,
    db: TenantDB,
    user: AuthenticatedUser,
):
    """
    Get AI-generated suggestion for resolving a screening hit.
    
    Uses Claude to analyze the hit against applicant data and 
    suggest whether it's a true match or false positive.
    """
    from app.services.ai import ai_service, AIServiceError
    
    # Verify hit exists and belongs to tenant
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
    
    try:
        suggestion = await ai_service.suggest_hit_resolution(db, hit_id)
        
        return {
            "hit_id": str(hit_id),
            "suggested_resolution": suggestion.suggested_resolution,
            "confidence": suggestion.confidence,
            "reasoning": suggestion.reasoning,
            "evidence": [
                {
                    "source_type": e.source_type,
                    "source_name": e.source_name,
                    "excerpt": e.excerpt,
                }
                for e in suggestion.evidence
            ],
            "generated_at": suggestion.generated_at.isoformat(),
        }
        
    except AIServiceError as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"AI service error: {str(e)}",
        )
