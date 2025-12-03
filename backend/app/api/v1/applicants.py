"""
Get Clearance - Applicants API
===============================
CRUD operations and workflow management for KYC applicants.
"""

from datetime import datetime
from io import StringIO
import csv
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from fastapi.responses import Response, StreamingResponse
from sqlalchemy import select, func, or_, and_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.dependencies import TenantDB, AuthenticatedUser, AuditContext, require_permission
from app.models import Applicant, ApplicantStep, Document, ScreeningCheck, ScreeningHit, Case, AuditLog
from app.schemas.applicant import (
    ApplicantCreate,
    ApplicantUpdate,
    ApplicantReview,
    ApplicantSummary,
    ApplicantDetail,
    ApplicantListResponse,
    StepComplete,
    ConsentRequest,
    ConsentResponse,
    LegalHoldRequest,
    LegalHoldResponse,
    GDPRExportResponse,
    GDPRExportMetadata,
    GDPRDeleteResponse,
)
from app.services.evidence import evidence_service, EvidenceServiceError
from app.services.timeline import timeline_service, TimelineServiceError
from app.services.audit import (
    record_audit_log,
    audit_applicant_created,
    audit_applicant_updated,
    audit_applicant_reviewed,
    audit_gdpr_data_exported,
    audit_gdpr_data_deleted,
    audit_consent_recorded,
    audit_legal_hold_set,
    audit_legal_hold_removed,
)
from app.services.retention import can_delete_for_aml

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
# EXPORT APPLICANTS TO CSV
# ===========================================
@router.get("/export")
async def export_applicants(
    db: TenantDB,
    user: Annotated[AuthenticatedUser, Depends(require_permission("read:applicants"))],
    status: Annotated[str | None, Query()] = None,
    risk_level: Annotated[str | None, Query()] = None,
    search: Annotated[str | None, Query()] = None,
    ids: Annotated[list[UUID] | None, Query()] = None,
    sort: Annotated[str, Query()] = "created_at",
    order: Annotated[str, Query(pattern="^(asc|desc)$")] = "desc",
):
    """
    Export applicants to CSV format.

    Filters:
    - status: Filter by status (pending, in_progress, review, approved, rejected)
    - risk_level: Filter by risk level (low, medium, high)
    - search: Search by name or email
    - ids: Export only specific applicant IDs (for selected exports)

    Sorting:
    - sort: Field to sort by (created_at, risk_score, last_name, review_status)
    - order: asc or desc

    Returns:
        CSV file as streaming download
    """
    # Base query
    query = select(Applicant).where(Applicant.tenant_id == user.tenant_id)

    # Apply ID filter if specific IDs requested
    if ids:
        query = query.where(Applicant.id.in_(ids))

    # Apply status filter
    if status:
        query = query.where(Applicant.status == status)

    # Apply risk level filter
    if risk_level:
        if risk_level == "low":
            query = query.where(Applicant.risk_score <= 30)
        elif risk_level == "medium":
            query = query.where(
                and_(Applicant.risk_score > 30, Applicant.risk_score <= 60)
            )
        elif risk_level == "high":
            query = query.where(Applicant.risk_score > 60)

    # Apply search filter
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

    # Apply sorting
    sort_column = getattr(Applicant, sort, Applicant.created_at)
    if order == "desc":
        query = query.order_by(sort_column.desc())
    else:
        query = query.order_by(sort_column.asc())

    # Execute query (no pagination for export)
    result = await db.execute(query)
    applicants = result.scalars().all()

    # Generate CSV
    output = StringIO()
    writer = csv.writer(output)

    # Write header
    writer.writerow([
        "ID",
        "External ID",
        "Email",
        "First Name",
        "Last Name",
        "Status",
        "Risk Score",
        "Risk Level",
        "Nationality",
        "Country of Residence",
        "Date of Birth",
        "Flags",
        "Created At",
        "Updated At",
        "Reviewed At",
        "Source",
    ])

    # Write data rows
    for applicant in applicants:
        # Determine risk level bucket
        risk_level_str = "unknown"
        if applicant.risk_score is not None:
            if applicant.risk_score <= 30:
                risk_level_str = "low"
            elif applicant.risk_score <= 60:
                risk_level_str = "medium"
            else:
                risk_level_str = "high"

        # Format flags
        flags_str = ", ".join(applicant.flags) if applicant.flags else ""

        writer.writerow([
            str(applicant.id),
            applicant.external_id or "",
            applicant.email or "",
            applicant.first_name or "",
            applicant.last_name or "",
            applicant.status or "",
            applicant.risk_score if applicant.risk_score is not None else "",
            risk_level_str,
            applicant.nationality or "",
            applicant.country_of_residence or "",
            applicant.date_of_birth.isoformat() if applicant.date_of_birth else "",
            flags_str,
            applicant.created_at.isoformat() if applicant.created_at else "",
            applicant.updated_at.isoformat() if applicant.updated_at else "",
            applicant.reviewed_at.isoformat() if applicant.reviewed_at else "",
            applicant.source or "",
        ])

    # Prepare response
    output.seek(0)
    timestamp = datetime.utcnow().strftime("%Y-%m-%d")
    filename = f"applicants_export_{timestamp}.csv"

    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={
            "Content-Disposition": f'attachment; filename="{filename}"',
            "X-Total-Count": str(len(applicants)),
        },
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
    ctx: AuditContext,
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

    # Create audit log entry
    await audit_applicant_created(
        db=db,
        tenant_id=user.tenant_id,
        user_id=UUID(user.id),
        applicant_id=applicant.id,
        applicant_data={
            "email": data.email,
            "first_name": data.first_name,
            "last_name": data.last_name,
            "external_id": data.external_id,
            "source": data.source or "api",
        },
        user_email=user.email,
        ip_address=ctx.ip_address,
    )

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
    ctx: AuditContext,
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

    # Capture old values for audit
    update_data = data.model_dump(exclude_unset=True)
    old_values = {}
    for field in update_data.keys():
        old_values[field] = getattr(applicant, field, None)

    # Update fields
    for field, value in update_data.items():
        if field == "address" and value:
            setattr(applicant, field, value)
        else:
            setattr(applicant, field, value)

    applicant.updated_at = datetime.utcnow()

    # Create audit log entry
    await audit_applicant_updated(
        db=db,
        tenant_id=user.tenant_id,
        user_id=UUID(user.id),
        applicant_id=applicant.id,
        old_values=old_values,
        new_values=update_data,
        user_email=user.email,
        ip_address=ctx.ip_address,
    )

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
    ctx: AuditContext,
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

    # Capture old status for audit
    old_status = applicant.status

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

    # Create audit log entry
    await audit_applicant_reviewed(
        db=db,
        tenant_id=user.tenant_id,
        user_id=UUID(user.id),
        applicant_id=applicant.id,
        old_status=old_status,
        new_status=data.decision,
        notes=data.notes if hasattr(data, "notes") else None,
        user_email=user.email,
        ip_address=ctx.ip_address,
    )

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
    ctx: AuditContext,
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

    # Create audit log entry
    await record_audit_log(
        db=db,
        tenant_id=user.tenant_id,
        user_id=UUID(user.id),
        action="applicant.step_completed",
        resource_type="applicant",
        resource_id=applicant_id,
        new_values={
            "step_id": step_id,
            "verification_result": data.verification_result,
        },
        user_email=user.email,
        ip_address=ctx.ip_address,
    )

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


# ===========================================
# GDPR COMPLIANCE ENDPOINTS
# ===========================================

# --- Helper functions for GDPR data export ---

async def _get_applicant_documents(db: AsyncSession, applicant_id: UUID) -> list[dict]:
    """Get all documents for an applicant (for GDPR export)."""
    query = select(Document).where(Document.applicant_id == applicant_id)
    result = await db.execute(query)
    documents = result.scalars().all()

    return [
        {
            "id": str(doc.id),
            "type": doc.type,
            "file_name": doc.file_name,
            "status": doc.status,
            "uploaded_at": doc.uploaded_at.isoformat() if doc.uploaded_at else None,
            "verification_status": doc.status,
        }
        for doc in documents
    ]


async def _get_applicant_screening(db: AsyncSession, applicant_id: UUID) -> list[dict]:
    """Get all screening checks and hits for an applicant (for GDPR export)."""
    query = (
        select(ScreeningCheck)
        .where(ScreeningCheck.applicant_id == applicant_id)
        .options(selectinload(ScreeningCheck.hits))
    )
    result = await db.execute(query)
    checks = result.scalars().all()

    return [
        {
            "id": str(check.id),
            "screened_name": check.screened_name,
            "check_types": check.check_types,
            "status": check.status,
            "hit_count": check.hit_count,
            "started_at": check.started_at.isoformat() if check.started_at else None,
            "completed_at": check.completed_at.isoformat() if check.completed_at else None,
            "hits": [
                {
                    "id": str(hit.id),
                    "hit_type": hit.hit_type,
                    "matched_name": hit.matched_name,
                    "confidence": float(hit.confidence),
                    "resolution_status": hit.resolution_status,
                }
                for hit in check.hits
            ],
        }
        for check in checks
    ]


async def _get_applicant_cases(db: AsyncSession, applicant_id: UUID) -> list[dict]:
    """Get all cases for an applicant (for GDPR export)."""
    query = select(Case).where(Case.applicant_id == applicant_id)
    result = await db.execute(query)
    cases = result.scalars().all()

    return [
        {
            "id": str(case.id),
            "case_number": case.case_number,
            "title": case.title,
            "type": case.type,
            "priority": case.priority,
            "status": case.status,
            "resolution": case.resolution,
            "opened_at": case.opened_at.isoformat() if case.opened_at else None,
            "resolved_at": case.resolved_at.isoformat() if case.resolved_at else None,
        }
        for case in cases
    ]


async def _get_applicant_audit_log(db: AsyncSession, applicant_id: UUID, tenant_id: UUID) -> list[dict]:
    """Get audit log entries related to an applicant (for GDPR export)."""
    query = (
        select(AuditLog)
        .where(
            AuditLog.tenant_id == tenant_id,
            AuditLog.resource_type == "applicant",
            AuditLog.resource_id == applicant_id,
        )
        .order_by(AuditLog.created_at.desc())
        .limit(100)  # Limit for performance
    )
    result = await db.execute(query)
    logs = result.scalars().all()

    return [
        {
            "id": log.id,
            "action": log.action,
            "timestamp": log.created_at.isoformat() if log.created_at else None,
            "user_email": log.user_email,
            # Note: Don't include full old_values/new_values as they may contain sensitive data
        }
        for log in logs
    ]


async def _get_applicant_ai_assessments(db: AsyncSession, applicant_id: UUID) -> list[dict]:
    """Get AI risk assessments for an applicant (for GDPR export)."""
    # This would query AI assessment results if stored separately
    # For now, return risk factors from the applicant model
    return []


# --- GDPR Export Endpoint (SAR - Subject Access Request) ---

@router.get("/{applicant_id}/export", response_model=GDPRExportResponse)
async def export_applicant_data(
    applicant_id: UUID,
    db: TenantDB,
    user: Annotated[AuthenticatedUser, Depends(require_permission("read:applicants"))],
    ctx: AuditContext,
    format: Annotated[str, Query(pattern="^(json|pdf)$")] = "json",
):
    """
    Export all data associated with an applicant (GDPR Article 15 & 20).

    This endpoint fulfills Subject Access Requests (SAR) by returning
    all personal data held about an applicant in a portable format.

    Supported formats:
    - json: Machine-readable JSON export
    - pdf: Human-readable PDF document

    GDPR Articles:
    - Article 15: Right of access
    - Article 20: Right to data portability
    """
    # Fetch applicant
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

    # Gather all related data
    documents = await _get_applicant_documents(db, applicant_id)
    screening_results = await _get_applicant_screening(db, applicant_id)
    cases = await _get_applicant_cases(db, applicant_id)
    audit_trail = await _get_applicant_audit_log(db, applicant_id, user.tenant_id)
    ai_assessments = await _get_applicant_ai_assessments(db, applicant_id)

    export_data = GDPRExportResponse(
        personal_information={
            "first_name": applicant.first_name,
            "last_name": applicant.last_name,
            "email": applicant.email,
            "phone": applicant.phone,
            "date_of_birth": applicant.date_of_birth.isoformat() if applicant.date_of_birth else None,
            "nationality": applicant.nationality,
            "country_of_residence": applicant.country_of_residence,
            "address": applicant.address,
        },
        verification_status={
            "status": applicant.status,
            "risk_level": applicant.risk_level,
            "risk_score": applicant.risk_score,
            "flags": applicant.flags,
            "created_at": applicant.created_at.isoformat() if applicant.created_at else None,
            "updated_at": applicant.updated_at.isoformat() if applicant.updated_at else None,
            "reviewed_at": applicant.reviewed_at.isoformat() if applicant.reviewed_at else None,
        },
        documents=documents,
        screening_results=screening_results,
        cases=cases,
        audit_trail=audit_trail,
        ai_assessments=ai_assessments,
        export_metadata=GDPRExportMetadata(
            exported_at=datetime.utcnow(),
            exported_by=user.email or str(user.id),
            export_format=format,
            gdpr_articles=["15", "20"],
            applicant_id=applicant_id,
        ),
    )

    # Create audit log for the export
    sections_included = [
        "personal_information",
        "verification_status",
        "documents",
        "screening_results",
        "cases",
        "audit_trail",
        "ai_assessments",
    ]
    await audit_gdpr_data_exported(
        db=db,
        tenant_id=user.tenant_id,
        user_id=UUID(user.id),
        applicant_id=applicant_id,
        export_format=format,
        sections_included=sections_included,
        user_email=user.email,
        ip_address=ctx.ip_address,
    )

    if format == "pdf":
        # For PDF, use the evidence service which already generates PDFs
        try:
            evidence_result = await evidence_service.generate_evidence_pack(
                db=db,
                applicant_id=applicant_id,
                generated_by=user.email or user.id,
            )
            return Response(
                content=evidence_result.pdf_bytes,
                media_type="application/pdf",
                headers={
                    "Content-Disposition": f"attachment; filename=sar_{applicant_id}.pdf"
                },
            )
        except EvidenceServiceError as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to generate PDF export: {str(e)}",
            )

    return export_data


# --- GDPR Delete Endpoint (Right to Erasure) ---

@router.delete("/{applicant_id}/gdpr-delete", response_model=GDPRDeleteResponse)
async def gdpr_delete_applicant(
    applicant_id: UUID,
    db: TenantDB,
    user: Annotated[AuthenticatedUser, Depends(require_permission("delete:applicants"))],
    ctx: AuditContext,
    confirmation: Annotated[str, Query(description="Must be 'CONFIRM_DELETE'")] = ...,
    reason: Annotated[str, Query(description="Reason for deletion request")] = ...,
):
    """
    Permanently delete applicant and all associated data (GDPR Article 17).

    This action is IRREVERSIBLE. All personal data, documents, screening results,
    and related records will be permanently deleted.

    Safeguards:
    - Requires explicit confirmation string 'CONFIRM_DELETE'
    - Checks for legal hold (cannot delete if under legal hold)
    - Checks AML retention requirements (cannot delete flagged/rejected records within retention period)

    GDPR Article 17 exceptions that block deletion:
    - 17(3)(b): Legal claims
    - 17(3)(e): Legal obligations (AML requirements)
    """
    if confirmation != "CONFIRM_DELETE":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Must confirm deletion with 'CONFIRM_DELETE'",
        )

    # Fetch applicant
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

    # Check for legal hold
    if applicant.legal_hold:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Cannot delete: applicant is under legal hold. Contact compliance.",
        )

    # Check AML retention requirements
    if not can_delete_for_aml(applicant):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Cannot delete: AML regulations require retention of flagged/rejected records for the retention period.",
        )

    # Store email hash for audit before deletion
    email_hash = applicant.email_hash

    # Delete associated data
    deleted_data = []

    # Delete documents (including from storage)
    doc_query = select(Document).where(Document.applicant_id == applicant_id)
    doc_result = await db.execute(doc_query)
    documents = doc_result.scalars().all()
    for doc in documents:
        await db.delete(doc)
    if documents:
        deleted_data.append(f"documents ({len(documents)})")

    # Delete screening checks (cascade deletes hits)
    screen_query = select(ScreeningCheck).where(ScreeningCheck.applicant_id == applicant_id)
    screen_result = await db.execute(screen_query)
    checks = screen_result.scalars().all()
    for check in checks:
        await db.delete(check)
    if checks:
        deleted_data.append(f"screening_checks ({len(checks)})")

    # Delete cases
    case_query = select(Case).where(Case.applicant_id == applicant_id)
    case_result = await db.execute(case_query)
    cases = case_result.scalars().all()
    for case in cases:
        await db.delete(case)
    if cases:
        deleted_data.append(f"cases ({len(cases)})")

    # Create audit log BEFORE deleting applicant (to preserve reference)
    await audit_gdpr_data_deleted(
        db=db,
        tenant_id=user.tenant_id,
        user_id=UUID(user.id),
        applicant_id=applicant_id,
        reason=reason,
        email_hash=email_hash,
        user_email=user.email,
        ip_address=ctx.ip_address,
    )

    # Delete applicant (steps cascade automatically)
    deleted_data.append("applicant_record")
    await db.delete(applicant)
    await db.commit()

    return GDPRDeleteResponse(
        status="deleted",
        applicant_id=applicant_id,
        deleted_at=datetime.utcnow(),
        deleted_data=deleted_data,
    )


# --- Consent Tracking Endpoint ---

@router.post("/{applicant_id}/consent", response_model=ConsentResponse)
async def record_consent(
    applicant_id: UUID,
    consent: ConsentRequest,
    request: Request,
    db: TenantDB,
    user: AuthenticatedUser,
    ctx: AuditContext,
):
    """
    Record applicant's consent for data processing (GDPR Article 6/7).

    Consent must be:
    - Freely given
    - Specific
    - Informed
    - Unambiguous

    This endpoint records when consent is given or withdrawn.
    """
    # Fetch applicant
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

    # Get client IP
    client_ip = request.client.host if request.client else None

    # Update consent
    now = datetime.utcnow()
    if consent.consent:
        applicant.consent_given = True
        applicant.consent_given_at = now
        applicant.consent_ip_address = client_ip
        applicant.consent_withdrawn_at = None
    else:
        applicant.consent_given = False
        applicant.consent_withdrawn_at = now

    applicant.updated_at = now

    # Create audit log
    await audit_consent_recorded(
        db=db,
        tenant_id=user.tenant_id,
        user_id=UUID(user.id) if user.id else None,
        applicant_id=applicant_id,
        consent_given=consent.consent,
        consent_ip=client_ip,
        user_email=user.email,
        ip_address=ctx.ip_address,
    )

    await db.commit()

    return ConsentResponse(
        status="consent_recorded",
        consent_given=applicant.consent_given,
        consent_given_at=applicant.consent_given_at,
        applicant_id=applicant_id,
    )


# --- Legal Hold Endpoints ---

@router.post("/{applicant_id}/legal-hold", response_model=LegalHoldResponse)
async def set_legal_hold(
    applicant_id: UUID,
    data: LegalHoldRequest,
    db: TenantDB,
    user: Annotated[AuthenticatedUser, Depends(require_permission("admin:applicants"))],
    ctx: AuditContext,
):
    """
    Place an applicant under legal hold to prevent deletion.

    Legal hold:
    - Blocks GDPR deletion requests
    - Blocks automated retention cleanup
    - Blocks manual deletion

    Use for:
    - Pending litigation
    - Regulatory investigation
    - Law enforcement requests
    """
    # Fetch applicant
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

    if applicant.legal_hold:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Applicant is already under legal hold",
        )

    # Set legal hold
    now = datetime.utcnow()
    applicant.legal_hold = True
    applicant.legal_hold_reason = data.reason
    applicant.legal_hold_set_by = UUID(user.id)
    applicant.legal_hold_set_at = now
    applicant.updated_at = now

    # Create audit log
    await audit_legal_hold_set(
        db=db,
        tenant_id=user.tenant_id,
        user_id=UUID(user.id),
        applicant_id=applicant_id,
        reason=data.reason,
        user_email=user.email,
        ip_address=ctx.ip_address,
    )

    await db.commit()

    return LegalHoldResponse(
        status="legal_hold_set",
        legal_hold=True,
        legal_hold_reason=applicant.legal_hold_reason,
        legal_hold_set_at=applicant.legal_hold_set_at,
        applicant_id=applicant_id,
    )


@router.delete("/{applicant_id}/legal-hold", response_model=LegalHoldResponse)
async def remove_legal_hold(
    applicant_id: UUID,
    db: TenantDB,
    user: Annotated[AuthenticatedUser, Depends(require_permission("admin:applicants"))],
    ctx: AuditContext,
):
    """
    Remove legal hold from an applicant.

    After removal:
    - GDPR deletion requests can proceed
    - Automated retention cleanup will apply
    - Manual deletion is allowed
    """
    # Fetch applicant
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

    if not applicant.legal_hold:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Applicant is not under legal hold",
        )

    # Store previous reason for audit
    previous_reason = applicant.legal_hold_reason

    # Remove legal hold
    applicant.legal_hold = False
    applicant.legal_hold_reason = None
    applicant.legal_hold_set_by = None
    applicant.legal_hold_set_at = None
    applicant.updated_at = datetime.utcnow()

    # Create audit log
    await audit_legal_hold_removed(
        db=db,
        tenant_id=user.tenant_id,
        user_id=UUID(user.id),
        applicant_id=applicant_id,
        previous_reason=previous_reason,
        user_email=user.email,
        ip_address=ctx.ip_address,
    )

    await db.commit()

    return LegalHoldResponse(
        status="legal_hold_removed",
        legal_hold=False,
        legal_hold_reason=None,
        legal_hold_set_at=None,
        applicant_id=applicant_id,
    )
