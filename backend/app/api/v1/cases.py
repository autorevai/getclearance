"""
Get Clearance - Cases API
==========================
Investigation case management.
"""

from datetime import datetime
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.dependencies import TenantDB, AuthenticatedUser, require_permission
from app.models import Case, CaseNote

router = APIRouter()


# ===========================================
# SCHEMAS
# ===========================================

class CaseCreate(BaseModel):
    """Create a new case."""
    title: str = Field(..., max_length=500)
    description: str | None = None
    type: str = Field(..., pattern="^(sanctions|pep|fraud|aml|verification|other)$")
    priority: str = Field(default="medium", pattern="^(critical|high|medium|low)$")
    applicant_id: UUID | None = None
    company_id: UUID | None = None
    screening_hit_id: UUID | None = None
    assignee_id: UUID | None = None


class CaseUpdate(BaseModel):
    """Update case fields."""
    title: str | None = None
    description: str | None = None
    priority: str | None = None
    status: str | None = None
    assignee_id: UUID | None = None


class CaseResolve(BaseModel):
    """Resolve a case."""
    resolution: str = Field(..., pattern="^(cleared|confirmed|reported|escalated)$")
    notes: str | None = None


class AddNote(BaseModel):
    """Add a note to a case."""
    content: str = Field(..., min_length=1)


class CaseNoteResponse(BaseModel):
    """Case note response."""
    id: UUID
    content: str
    is_ai_generated: bool
    created_at: datetime
    
    model_config = {"from_attributes": True}


class CaseResponse(BaseModel):
    """Case response."""
    id: UUID
    case_number: str
    title: str
    description: str | None
    type: str
    priority: str
    status: str
    resolution: str | None
    resolution_notes: str | None
    applicant_id: UUID | None
    assignee_id: UUID | None
    due_at: datetime | None
    opened_at: datetime
    resolved_at: datetime | None
    created_at: datetime
    notes: list[CaseNoteResponse] = []
    
    model_config = {"from_attributes": True}


class CaseListResponse(BaseModel):
    """Paginated list of cases."""
    items: list[CaseResponse]
    total: int
    limit: int
    offset: int


# ===========================================
# HELPERS
# ===========================================

async def generate_case_number(db: AsyncSession, tenant_id: UUID) -> str:
    """Generate sequential case number for tenant."""
    year = datetime.utcnow().year
    
    # Get count of cases this year
    query = select(func.count(Case.id)).where(
        Case.tenant_id == tenant_id,
        func.extract("year", Case.created_at) == year,
    )
    result = await db.execute(query)
    count = (result.scalar() or 0) + 1
    
    return f"CASE-{year}-{count:04d}"


# ===========================================
# LIST CASES
# ===========================================
@router.get("", response_model=CaseListResponse)
async def list_cases(
    db: TenantDB,
    user: AuthenticatedUser,
    status: Annotated[str | None, Query()] = None,
    priority: Annotated[str | None, Query()] = None,
    type: Annotated[str | None, Query()] = None,
    assignee_id: Annotated[UUID | None, Query()] = None,
    applicant_id: Annotated[UUID | None, Query()] = None,
    limit: Annotated[int, Query(ge=1, le=100)] = 50,
    offset: Annotated[int, Query(ge=0)] = 0,
):
    """
    List cases with filtering.
    """
    query = (
        select(Case)
        .where(Case.tenant_id == user.tenant_id)
        .options(selectinload(Case.notes))
    )
    count_query = select(func.count(Case.id)).where(Case.tenant_id == user.tenant_id)
    
    # Apply filters
    if status:
        query = query.where(Case.status == status)
        count_query = count_query.where(Case.status == status)
    if priority:
        query = query.where(Case.priority == priority)
        count_query = count_query.where(Case.priority == priority)
    if type:
        query = query.where(Case.type == type)
        count_query = count_query.where(Case.type == type)
    if assignee_id:
        query = query.where(Case.assignee_id == assignee_id)
        count_query = count_query.where(Case.assignee_id == assignee_id)
    if applicant_id:
        query = query.where(Case.applicant_id == applicant_id)
        count_query = count_query.where(Case.applicant_id == applicant_id)
    
    # Get total
    total_result = await db.execute(count_query)
    total = total_result.scalar() or 0
    
    # Get items (ordered by priority and due date)
    priority_order = func.array_position(
        ["critical", "high", "medium", "low"],
        Case.priority
    )
    query = (
        query
        .order_by(priority_order, Case.due_at.asc().nullslast())
        .offset(offset)
        .limit(limit)
    )
    result = await db.execute(query)
    cases = result.scalars().all()
    
    return CaseListResponse(
        items=[CaseResponse.model_validate(c) for c in cases],
        total=total,
        limit=limit,
        offset=offset,
    )


# ===========================================
# GET CASE
# ===========================================
@router.get("/{case_id}", response_model=CaseResponse)
async def get_case(
    case_id: UUID,
    db: TenantDB,
    user: AuthenticatedUser,
):
    """
    Get case details with notes.
    """
    query = (
        select(Case)
        .where(
            Case.id == case_id,
            Case.tenant_id == user.tenant_id,
        )
        .options(selectinload(Case.notes))
    )
    result = await db.execute(query)
    case = result.scalar_one_or_none()
    
    if not case:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Case not found",
        )
    
    return CaseResponse.model_validate(case)


# ===========================================
# CREATE CASE
# ===========================================
@router.post("", response_model=CaseResponse, status_code=status.HTTP_201_CREATED)
async def create_case(
    data: CaseCreate,
    db: TenantDB,
    user: Annotated[AuthenticatedUser, Depends(require_permission("write:cases"))],
):
    """
    Create a new investigation case.
    """
    case_number = await generate_case_number(db, user.tenant_id)
    
    case = Case(
        tenant_id=user.tenant_id,
        case_number=case_number,
        title=data.title,
        description=data.description,
        type=data.type,
        priority=data.priority,
        status="open",
        applicant_id=data.applicant_id,
        company_id=data.company_id,
        screening_hit_id=data.screening_hit_id,
        assignee_id=data.assignee_id,
        source="manual",
    )
    db.add(case)
    
    # TODO: Calculate SLA based on priority
    # TODO: Create audit log entry
    # TODO: Send notification to assignee
    
    await db.flush()
    await db.refresh(case)
    
    return CaseResponse.model_validate(case)


# ===========================================
# UPDATE CASE
# ===========================================
@router.patch("/{case_id}", response_model=CaseResponse)
async def update_case(
    case_id: UUID,
    data: CaseUpdate,
    db: TenantDB,
    user: Annotated[AuthenticatedUser, Depends(require_permission("write:cases"))],
):
    """
    Update case fields.
    """
    query = (
        select(Case)
        .where(
            Case.id == case_id,
            Case.tenant_id == user.tenant_id,
        )
        .options(selectinload(Case.notes))
    )
    result = await db.execute(query)
    case = result.scalar_one_or_none()
    
    if not case:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Case not found",
        )
    
    # Update fields
    update_data = data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(case, field, value)
    
    case.updated_at = datetime.utcnow()
    
    await db.flush()
    await db.refresh(case)
    
    return CaseResponse.model_validate(case)


# ===========================================
# RESOLVE CASE
# ===========================================
@router.post("/{case_id}/resolve", response_model=CaseResponse)
async def resolve_case(
    case_id: UUID,
    data: CaseResolve,
    db: TenantDB,
    user: Annotated[AuthenticatedUser, Depends(require_permission("review:cases"))],
):
    """
    Resolve a case with a final decision.
    """
    query = (
        select(Case)
        .where(
            Case.id == case_id,
            Case.tenant_id == user.tenant_id,
        )
        .options(selectinload(Case.notes))
    )
    result = await db.execute(query)
    case = result.scalar_one_or_none()
    
    if not case:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Case not found",
        )
    
    if case.is_resolved:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Case already resolved",
        )
    
    # Resolve
    case.status = "resolved"
    case.resolution = data.resolution
    case.resolution_notes = data.notes
    case.resolved_at = datetime.utcnow()
    case.updated_at = datetime.utcnow()
    
    # TODO: Update related applicant/screening hit
    # TODO: Create audit log
    # TODO: Send notifications
    
    await db.flush()
    await db.refresh(case)
    
    return CaseResponse.model_validate(case)


# ===========================================
# ADD NOTE
# ===========================================
@router.post("/{case_id}/notes", response_model=CaseNoteResponse, status_code=status.HTTP_201_CREATED)
async def add_note(
    case_id: UUID,
    data: AddNote,
    db: TenantDB,
    user: AuthenticatedUser,
):
    """
    Add a note to a case.
    """
    # Verify case exists
    query = select(Case).where(
        Case.id == case_id,
        Case.tenant_id == user.tenant_id,
    )
    result = await db.execute(query)
    case = result.scalar_one_or_none()
    
    if not case:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Case not found",
        )
    
    note = CaseNote(
        case_id=case_id,
        author_id=UUID(user.id),
        content=data.content,
        is_ai_generated=False,
    )
    db.add(note)
    
    await db.flush()
    await db.refresh(note)
    
    return CaseNoteResponse.model_validate(note)
