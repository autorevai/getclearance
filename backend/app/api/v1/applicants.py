"""
Get Clearance - Applicants API
===============================
CRUD operations and workflow management for KYC applicants.
"""

from datetime import datetime
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import Response
from sqlalchemy import select, func, or_, and_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.dependencies import TenantDB, AuthenticatedUser, require_permission
from app.models import Applicant, ApplicantStep
from app.schemas.applicant import (
    ApplicantCreate,
    ApplicantUpdate,
    ApplicantReview,
    ApplicantSummary,
    ApplicantDetail,
    ApplicantListResponse,
    StepComplete,
)
from app.services.evidence import evidence_service, EvidenceServiceError
from app.services.timeline import timeline_service, TimelineServiceError

router = APIRouter()


# ===========================================
# LIST APPLICANTS
# ===========================================
@router.get("", response_model=ApplicantListResponse)
async def list_applicants(
    db: TenantDB,
    user: AuthenticatedUser,
    status: Annotated[str | None, Query()] = None,
    risk_level: Annotated[str | None, Query()] = None,
    search: Annotated[str | None, Query()] = None,
    has_flags: Annotated[bool | None, Query()] = None,
    limit: Annotated[int, Query(ge=1, le=100)] = 50,
    offset: Annotated[int, Query(ge=0)] = 0,
    sort_by: Annotated[str, Query()] = "created_at",
    sort_order: Annotated[str, Query(pattern="^(asc|desc)$")] = "desc",
):
    """
    List applicants with filtering and pagination.
    
    Filters:
    - status: Filter by status (pending, in_progress, review, approved, rejected)
    - risk_level: Filter by risk level (low, medium, high)
    - search: Search by name or email
    - has_flags: Only show applicants with flags
    
    Sorting:
    - sort_by: Field to sort by (created_at, risk_score, submitted_at)
    - sort_order: asc or desc
    """
    # Base query
    query = select(Applicant).where(Applicant.tenant_id == user.tenant_id)
    count_query = select(func.count(Applicant.id)).where(
        Applicant.tenant_id == user.tenant_id
    )
    
    # Apply filters
    if status:
        query = query.where(Applicant.status == status)
        count_query = count_query.where(Applicant.status == status)
    
    if risk_level:
        # Map risk level to score range
        if risk_level == "low":
            query = query.where(Applicant.risk_score <= 30)
            count_query = count_query.where(Applicant.risk_score <= 30)
        elif risk_level == "medium":
            query = query.where(
                and_(Applicant.risk_score > 30, Applicant.risk_score <= 60)
            )
            count_query = count_query.where(
                and_(Applicant.risk_score > 30, Applicant.risk_score <= 60)
            )
        elif risk_level == "high":
            query = query.where(Applicant.risk_score > 60)
            count_query = count_query.where(Applicant.risk_score > 60)
    
    if search:
        search_term = f"%{search}%"
        query = query.where(
            or_(
                Applicant.first_name.ilike(search_term),
                Applicant.last_name.ilike(search_term),
                Applicant.email.ilike(search_term),
                Applicant.external_id.ilike(search_term),
            )
        )
        count_query = count_query.where(
            or_(
                Applicant.first_name.ilike(search_term),
                Applicant.last_name.ilike(search_term),
                Applicant.email.ilike(search_term),
                Applicant.external_id.ilike(search_term),
            )
        )
    
    if has_flags:
        query = query.where(func.cardinality(Applicant.flags) > 0)
        count_query = count_query.where(func.cardinality(Applicant.flags) > 0)
    
    # Get total count
    total_result = await db.execute(count_query)
    total = total_result.scalar() or 0
    
    # Apply sorting
    sort_column = getattr(Applicant, sort_by, Applicant.created_at)
    if sort_order == "desc":
        query = query.order_by(sort_column.desc())
    else:
        query = query.order_by(sort_column.asc())
    
    # Apply pagination
    query = query.offset(offset).limit(limit)
    
    # Execute query
    result = await db.execute(query)
    applicants = result.scalars().all()
    
    return ApplicantListResponse(
        items=[ApplicantSummary.model_validate(a) for a in applicants],
        total=total,
        limit=limit,
        offset=offset,
    )


# ===========================================
# GET APPLICANT DETAIL
# ===========================================
@router.get("/{applicant_id}", response_model=ApplicantDetail)
async def get_applicant(
    applicant_id: UUID,
    db: TenantDB,
    user: AuthenticatedUser,
):
    """
    Get full applicant details including steps, documents, and screening results.
    """
    query = (
        select(Applicant)
        .where(
            Applicant.id == applicant_id,
            Applicant.tenant_id == user.tenant_id,
        )
        .options(selectinload(Applicant.steps))
    )
    
    result = await db.execute(query)
    applicant = result.scalar_one_or_none()
    
    if not applicant:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Applicant not found",
        )
    
    return ApplicantDetail.model_validate(applicant)


# ===========================================
# CREATE APPLICANT
# ===========================================
@router.post("", response_model=ApplicantDetail, status_code=status.HTTP_201_CREATED)
async def create_applicant(
    data: ApplicantCreate,
    db: TenantDB,
    user: Annotated[AuthenticatedUser, Depends(require_permission("write:applicants"))],
):
    """
    Create a new applicant.
    
    This creates the applicant record and initializes workflow steps
    based on the assigned workflow.
    """
    # Check for duplicate external_id
    if data.external_id:
        existing = await db.execute(
            select(Applicant).where(
                Applicant.tenant_id == user.tenant_id,
                Applicant.external_id == data.external_id,
            )
        )
        if existing.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Applicant with external_id '{data.external_id}' already exists",
            )
    
    # Create applicant
    applicant = Applicant(
        tenant_id=user.tenant_id,
        external_id=data.external_id,
        email=data.email,
        phone=data.phone,
        first_name=data.first_name,
        last_name=data.last_name,
        date_of_birth=data.date_of_birth,
        nationality=data.nationality,
        country_of_residence=data.country_of_residence,
        address=data.address.model_dump() if data.address else None,
        workflow_id=data.workflow_id,
        source=data.source or "api",
        status="pending",
    )
    
    db.add(applicant)
    await db.flush()
    
    # TODO: Initialize workflow steps based on workflow_id
    # TODO: Trigger initial screening
    # TODO: Create audit log entry
    
    await db.refresh(applicant)
    return ApplicantDetail.model_validate(applicant)


# ===========================================
# UPDATE APPLICANT
# ===========================================
@router.patch("/{applicant_id}", response_model=ApplicantDetail)
async def update_applicant(
    applicant_id: UUID,
    data: ApplicantUpdate,
    db: TenantDB,
    user: Annotated[AuthenticatedUser, Depends(require_permission("write:applicants"))],
):
    """
    Update applicant information.
    
    Note: Status changes should typically go through the review endpoint.
    """
    query = select(Applicant).where(
        Applicant.id == applicant_id,
        Applicant.tenant_id == user.tenant_id,
    )
    result = await db.execute(query)
    applicant = result.scalar_one_or_none()
    
    if not applicant:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Applicant not found",
        )
    
    # Update fields
    update_data = data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        if field == "address" and value:
            setattr(applicant, field, value)
        else:
            setattr(applicant, field, value)
    
    applicant.updated_at = datetime.utcnow()
    
    # TODO: Create audit log entry
    
    await db.flush()
    await db.refresh(applicant)
    return ApplicantDetail.model_validate(applicant)


# ===========================================
# REVIEW APPLICANT (Approve/Reject)
# ===========================================
@router.post("/{applicant_id}/review", response_model=ApplicantDetail)
async def review_applicant(
    applicant_id: UUID,
    data: ApplicantReview,
    db: TenantDB,
    user: Annotated[AuthenticatedUser, Depends(require_permission("review:applicants"))],
):
    """
    Submit a review decision (approve or reject).
    
    This is a privileged action that requires the review:applicants permission.
    """
    query = select(Applicant).where(
        Applicant.id == applicant_id,
        Applicant.tenant_id == user.tenant_id,
    )
    result = await db.execute(query)
    applicant = result.scalar_one_or_none()
    
    if not applicant:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Applicant not found",
        )
    
    # Validate current status allows review
    if applicant.status not in ("pending", "in_progress", "review"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot review applicant with status '{applicant.status}'",
        )
    
    # Update status
    applicant.status = data.decision
    applicant.reviewed_at = datetime.utcnow()
    applicant.reviewed_by = UUID(user.id) if user.id else None
    
    # Override risk score if provided
    if data.risk_score_override is not None:
        applicant.risk_score = data.risk_score_override
        applicant.risk_factors.append({
            "factor": "Manual override",
            "impact": 0,
            "source": "reviewer",
        })
    
    applicant.updated_at = datetime.utcnow()
    
    # TODO: Create audit log entry
    # TODO: Send notification webhooks
    
    await db.flush()
    await db.refresh(applicant)
    return ApplicantDetail.model_validate(applicant)


# ===========================================
# COMPLETE STEP
# ===========================================
@router.post("/{applicant_id}/steps/{step_id}/complete")
async def complete_step(
    applicant_id: UUID,
    step_id: str,
    data: StepComplete,
    db: TenantDB,
    user: AuthenticatedUser,
):
    """
    Mark a verification step as complete.
    
    Used by SDKs and frontend to submit step completion.
    """
    # Get applicant and step
    query = (
        select(ApplicantStep)
        .join(Applicant)
        .where(
            ApplicantStep.applicant_id == applicant_id,
            ApplicantStep.step_id == step_id,
            Applicant.tenant_id == user.tenant_id,
        )
    )
    result = await db.execute(query)
    step = result.scalar_one_or_none()
    
    if not step:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Step not found",
        )
    
    if step.status == "complete":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Step already completed",
        )
    
    # Update step
    step.status = "complete"
    step.data = data.data
    step.verification_result = data.verification_result
    step.completed_at = datetime.utcnow()
    step.updated_at = datetime.utcnow()
    
    # TODO: Check if all steps complete -> update applicant status
    # TODO: Trigger next steps if applicable
    # TODO: Create audit log entry

    await db.flush()

    return {"status": "completed", "step_id": step_id}


# ===========================================
# EVIDENCE EXPORT
# ===========================================
@router.get("/{applicant_id}/evidence")
async def export_evidence(
    applicant_id: UUID,
    db: TenantDB,
    user: Annotated[AuthenticatedUser, Depends(require_permission("read:applicants"))],
):
    """
    Download evidence pack PDF for an applicant.

    Generates a comprehensive PDF containing:
    - Applicant information and risk assessment
    - Document verification results
    - Screening results with hit details
    - AI risk analysis
    - Complete event timeline
    - Chain-of-custody audit trail

    Returns:
        PDF file as binary download
    """
    # Verify applicant belongs to tenant
    query = select(Applicant).where(
        Applicant.id == applicant_id,
        Applicant.tenant_id == user.tenant_id,
    )
    result = await db.execute(query)
    applicant = result.scalar_one_or_none()

    if not applicant:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Applicant not found",
        )

    try:
        # Generate evidence pack
        evidence_result = await evidence_service.generate_evidence_pack(
            db=db,
            applicant_id=applicant_id,
            generated_by=user.email or user.id,
        )

        # Log the export in timeline
        try:
            await timeline_service.record_event(
                db=db,
                tenant_id=user.tenant_id,
                applicant_id=applicant_id,
                event_type="evidence_exported",
                event_data={
                    "generated_by": user.email or user.id,
                    "page_count": evidence_result.page_count,
                    "sections": evidence_result.sections_included,
                },
                actor_type="reviewer",
                actor_id=UUID(user.id) if user.id else None,
            )
        except Exception:
            # Don't fail the export if timeline logging fails
            pass

        # Build filename
        applicant_name = evidence_result.metadata.applicant_name.replace(" ", "_")
        timestamp = evidence_result.metadata.generated_at.strftime("%Y%m%d_%H%M%S")
        filename = f"evidence_pack_{applicant_name}_{timestamp}.pdf"

        # Return PDF response
        return Response(
            content=evidence_result.pdf_bytes,
            media_type="application/pdf",
            headers={
                "Content-Disposition": f'attachment; filename="{filename}"',
                "X-Evidence-Pack-Version": evidence_result.metadata.pack_version,
                "X-Page-Count": str(evidence_result.page_count),
            },
        )

    except EvidenceServiceError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate evidence pack: {str(e)}",
        )


@router.get("/{applicant_id}/evidence/preview")
async def preview_evidence(
    applicant_id: UUID,
    db: TenantDB,
    user: Annotated[AuthenticatedUser, Depends(require_permission("read:applicants"))],
):
    """
    Get a preview of what would be included in an evidence pack.

    Useful for showing users what will be in the pack before generating.

    Returns:
        JSON object with section summaries and counts
    """
    # Verify applicant belongs to tenant
    query = select(Applicant).where(
        Applicant.id == applicant_id,
        Applicant.tenant_id == user.tenant_id,
    )
    result = await db.execute(query)
    applicant = result.scalar_one_or_none()

    if not applicant:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Applicant not found",
        )

    try:
        preview = await evidence_service.get_evidence_preview(
            db=db,
            applicant_id=applicant_id,
        )
        return preview

    except EvidenceServiceError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate preview: {str(e)}",
        )


@router.get("/{applicant_id}/timeline")
async def get_timeline(
    applicant_id: UUID,
    db: TenantDB,
    user: Annotated[AuthenticatedUser, Depends(require_permission("read:applicants"))],
    limit: Annotated[int | None, Query(ge=1, le=500)] = None,
):
    """
    Get the event timeline for an applicant.

    Returns chronological list of all events (document uploads, status changes,
    screening results, etc.) that occurred during the verification process.

    Args:
        limit: Maximum number of events to return (default: all)

    Returns:
        Timeline object with events grouped by date
    """
    # Verify applicant belongs to tenant
    query = select(Applicant).where(
        Applicant.id == applicant_id,
        Applicant.tenant_id == user.tenant_id,
    )
    result = await db.execute(query)
    applicant = result.scalar_one_or_none()

    if not applicant:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Applicant not found",
        )

    try:
        timeline = await timeline_service.get_applicant_timeline(
            db=db,
            applicant_id=applicant_id,
            limit=limit,
        )

        # Convert to dict for JSON response
        return {
            "applicant_id": timeline.applicant_id,
            "applicant_name": timeline.applicant_name,
            "total_events": timeline.total_events,
            "generated_at": timeline.generated_at.isoformat(),
            "groups": [
                {
                    "date": group.date,
                    "events": [
                        {
                            "id": event.id,
                            "timestamp": event.timestamp.isoformat(),
                            "event_type": event.event_type,
                            "description": event.description,
                            "actor_type": event.actor_type,
                            "actor_name": event.actor_name,
                            "details": event.details,
                        }
                        for event in group.events
                    ],
                }
                for group in timeline.groups
            ],
        }

    except TimelineServiceError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch timeline: {str(e)}",
        )
