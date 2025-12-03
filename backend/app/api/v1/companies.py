"""
Get Clearance - Companies API (KYB)
===================================
Know Your Business (KYB) endpoints for company verification.

Provides:
- Company CRUD operations
- Beneficial owner management
- Company document handling
- Company + UBO screening
"""

from datetime import datetime
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select, func, or_
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies import TenantDB, AuthenticatedUser, AuditContext, require_permission
from app.models.company import Company, BeneficialOwner, CompanyDocument
from app.models.applicant import Applicant
from app.schemas.company import (
    CompanyCreate,
    CompanyUpdate,
    CompanyReview,
    CompanyListParams,
    CompanySummary,
    CompanyDetail,
    CompanyListResponse,
    BeneficialOwnerCreate,
    BeneficialOwnerUpdate,
    BeneficialOwnerResponse,
    LinkUBOToApplicant,
    CompanyDocumentCreate,
    CompanyDocumentResponse,
    CompanyDocumentVerify,
    CompanyScreeningResult,
)
from app.services.audit import record_audit_log
from app.services.storage import storage_service

router = APIRouter()


# ===========================================
# COMPANY CRUD
# ===========================================

@router.post("", response_model=CompanyDetail, status_code=status.HTTP_201_CREATED)
async def create_company(
    data: CompanyCreate,
    db: TenantDB,
    user: Annotated[AuthenticatedUser, Depends(require_permission("write:companies"))],
    ctx: AuditContext,
):
    """Create a new company for KYB verification."""
    # Check for duplicate external_id
    if data.external_id:
        existing = await db.execute(
            select(Company).where(
                Company.tenant_id == user.tenant_id,
                Company.external_id == data.external_id,
            )
        )
        if existing.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Company with external_id '{data.external_id}' already exists",
            )

    # Create company
    company = Company(
        tenant_id=user.tenant_id,
        external_id=data.external_id,
        legal_name=data.legal_name,
        trading_name=data.trading_name,
        registration_number=data.registration_number,
        tax_id=data.tax_id,
        incorporation_date=data.incorporation_date,
        incorporation_country=data.incorporation_country,
        legal_form=data.legal_form,
        registered_address=data.registered_address.model_dump() if data.registered_address else None,
        business_address=data.business_address.model_dump() if data.business_address else None,
        website=data.website,
        email=data.email,
        phone=data.phone,
        industry=data.industry,
        description=data.description,
        employee_count=data.employee_count,
        annual_revenue=data.annual_revenue,
        source=data.source or "api",
        extra_data=data.extra_data,
        status="pending",
    )

    db.add(company)
    await db.flush()

    # Audit log
    await record_audit_log(
        db=db,
        tenant_id=user.tenant_id,
        user_id=UUID(user.id),
        action="company.created",
        resource_type="company",
        resource_id=company.id,
        new_values={
            "legal_name": data.legal_name,
            "registration_number": data.registration_number,
            "incorporation_country": data.incorporation_country,
        },
        user_email=user.email,
        ip_address=ctx.ip_address,
    )

    await db.refresh(company)
    return CompanyDetail.model_validate(company)


@router.get("", response_model=CompanyListResponse)
async def list_companies(
    db: TenantDB,
    user: Annotated[AuthenticatedUser, Depends(require_permission("read:companies"))],
    status_filter: str | None = Query(None, alias="status"),
    risk_level: str | None = None,
    search: str | None = None,
    incorporation_country: str | None = None,
    has_flags: bool | None = None,
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    sort_by: str = "created_at",
    sort_order: str = "desc",
):
    """List companies with filtering and pagination."""
    query = select(Company).where(Company.tenant_id == user.tenant_id)

    # Filters
    if status_filter:
        query = query.where(Company.status == status_filter)
    if risk_level:
        query = query.where(Company.risk_level == risk_level)
    if incorporation_country:
        query = query.where(Company.incorporation_country == incorporation_country.upper())
    if has_flags is True:
        query = query.where(func.cardinality(Company.flags) > 0)
    if search:
        search_term = f"%{search}%"
        query = query.where(
            or_(
                Company.legal_name.ilike(search_term),
                Company.trading_name.ilike(search_term),
                Company.registration_number.ilike(search_term),
                Company.tax_id.ilike(search_term),
            )
        )

    # Count total
    count_query = select(func.count()).select_from(query.subquery())
    total = await db.scalar(count_query)

    # Sort
    sort_column = getattr(Company, sort_by, Company.created_at)
    if sort_order == "desc":
        query = query.order_by(sort_column.desc())
    else:
        query = query.order_by(sort_column.asc())

    # Paginate
    query = query.limit(limit).offset(offset)
    query = query.options(selectinload(Company.beneficial_owners))

    result = await db.execute(query)
    companies = result.scalars().all()

    return CompanyListResponse(
        items=[CompanySummary.model_validate(c) for c in companies],
        total=total or 0,
        limit=limit,
        offset=offset,
    )


@router.get("/{company_id}", response_model=CompanyDetail)
async def get_company(
    company_id: UUID,
    db: TenantDB,
    user: Annotated[AuthenticatedUser, Depends(require_permission("read:companies"))],
):
    """Get company details with UBOs and documents."""
    query = (
        select(Company)
        .where(Company.id == company_id, Company.tenant_id == user.tenant_id)
        .options(
            selectinload(Company.beneficial_owners),
            selectinload(Company.documents),
        )
    )
    result = await db.execute(query)
    company = result.scalar_one_or_none()

    if not company:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Company not found",
        )

    return CompanyDetail.model_validate(company)


@router.patch("/{company_id}", response_model=CompanyDetail)
async def update_company(
    company_id: UUID,
    data: CompanyUpdate,
    db: TenantDB,
    user: Annotated[AuthenticatedUser, Depends(require_permission("write:companies"))],
    ctx: AuditContext,
):
    """Update company details."""
    company = await db.get(Company, company_id)
    if not company or company.tenant_id != user.tenant_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Company not found",
        )

    # Capture old values for audit
    update_data = data.model_dump(exclude_unset=True)
    old_values = {}
    for field in update_data.keys():
        old_values[field] = getattr(company, field, None)

    # Update fields
    for field, value in update_data.items():
        if field in ("registered_address", "business_address") and value:
            setattr(company, field, value.model_dump() if hasattr(value, "model_dump") else value)
        else:
            setattr(company, field, value)

    company.updated_at = datetime.utcnow()

    # Audit log
    await record_audit_log(
        db=db,
        tenant_id=user.tenant_id,
        user_id=UUID(user.id),
        action="company.updated",
        resource_type="company",
        resource_id=company.id,
        old_values=old_values,
        new_values=update_data,
        user_email=user.email,
        ip_address=ctx.ip_address,
    )

    await db.flush()
    await db.refresh(company)
    return CompanyDetail.model_validate(company)


@router.delete("/{company_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_company(
    company_id: UUID,
    db: TenantDB,
    user: Annotated[AuthenticatedUser, Depends(require_permission("delete:companies"))],
    ctx: AuditContext,
):
    """Delete a company and all associated data."""
    company = await db.get(Company, company_id)
    if not company or company.tenant_id != user.tenant_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Company not found",
        )

    # Audit log before deletion
    await record_audit_log(
        db=db,
        tenant_id=user.tenant_id,
        user_id=UUID(user.id),
        action="company.deleted",
        resource_type="company",
        resource_id=company.id,
        old_values={
            "legal_name": company.legal_name,
            "status": company.status,
        },
        user_email=user.email,
        ip_address=ctx.ip_address,
    )

    await db.delete(company)
    await db.commit()


@router.post("/{company_id}/review", response_model=CompanyDetail)
async def review_company(
    company_id: UUID,
    data: CompanyReview,
    db: TenantDB,
    user: Annotated[AuthenticatedUser, Depends(require_permission("review:companies"))],
    ctx: AuditContext,
):
    """Approve or reject a company."""
    query = (
        select(Company)
        .where(Company.id == company_id, Company.tenant_id == user.tenant_id)
        .options(selectinload(Company.beneficial_owners))
    )
    result = await db.execute(query)
    company = result.scalar_one_or_none()

    if not company:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Company not found",
        )

    if company.status not in ("pending", "in_review"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot review company with status '{company.status}'",
        )

    old_status = company.status

    # Update status
    company.status = data.decision
    company.reviewed_at = datetime.utcnow()
    company.reviewed_by = UUID(user.id)
    company.review_notes = data.notes

    # Override risk score if provided
    if data.risk_score_override is not None:
        company.risk_score = data.risk_score_override

    company.updated_at = datetime.utcnow()

    # Audit log
    await record_audit_log(
        db=db,
        tenant_id=user.tenant_id,
        user_id=UUID(user.id),
        action="company.reviewed",
        resource_type="company",
        resource_id=company.id,
        old_values={"status": old_status},
        new_values={
            "status": data.decision,
            "notes": data.notes,
        },
        user_email=user.email,
        ip_address=ctx.ip_address,
    )

    await db.flush()
    await db.refresh(company)
    return CompanyDetail.model_validate(company)


@router.post("/{company_id}/screen", response_model=CompanyScreeningResult)
async def screen_company(
    company_id: UUID,
    db: TenantDB,
    user: Annotated[AuthenticatedUser, Depends(require_permission("write:screening"))],
    ctx: AuditContext,
):
    """Run screening on company and all beneficial owners."""
    from app.services.kyb_screening import kyb_screening_service

    query = (
        select(Company)
        .where(Company.id == company_id, Company.tenant_id == user.tenant_id)
        .options(selectinload(Company.beneficial_owners))
    )
    result = await db.execute(query)
    company = result.scalar_one_or_none()

    if not company:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Company not found",
        )

    # Run screening
    screening_result = await kyb_screening_service.screen_company(
        db=db,
        company=company,
        tenant_id=user.tenant_id,
        user_id=UUID(user.id),
    )

    # Audit log
    await record_audit_log(
        db=db,
        tenant_id=user.tenant_id,
        user_id=UUID(user.id),
        action="company.screened",
        resource_type="company",
        resource_id=company.id,
        new_values={
            "company_hits": screening_result.company_hits,
            "ubo_hits": screening_result.ubo_hits,
            "total_hits": screening_result.total_hits,
        },
        user_email=user.email,
        ip_address=ctx.ip_address,
    )

    await db.commit()
    return screening_result


# ===========================================
# BENEFICIAL OWNERS
# ===========================================

@router.get("/{company_id}/beneficial-owners", response_model=list[BeneficialOwnerResponse])
async def list_beneficial_owners(
    company_id: UUID,
    db: TenantDB,
    user: Annotated[AuthenticatedUser, Depends(require_permission("read:companies"))],
):
    """List all beneficial owners of a company."""
    company = await db.get(Company, company_id)
    if not company or company.tenant_id != user.tenant_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Company not found",
        )

    query = (
        select(BeneficialOwner)
        .where(BeneficialOwner.company_id == company_id)
        .order_by(BeneficialOwner.ownership_percentage.desc().nullslast())
    )
    result = await db.execute(query)
    ubos = result.scalars().all()

    return [BeneficialOwnerResponse.model_validate(ubo) for ubo in ubos]


@router.post("/{company_id}/beneficial-owners", response_model=BeneficialOwnerResponse, status_code=status.HTTP_201_CREATED)
async def add_beneficial_owner(
    company_id: UUID,
    data: BeneficialOwnerCreate,
    db: TenantDB,
    user: Annotated[AuthenticatedUser, Depends(require_permission("write:companies"))],
    ctx: AuditContext,
):
    """Add a beneficial owner to a company."""
    company = await db.get(Company, company_id)
    if not company or company.tenant_id != user.tenant_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Company not found",
        )

    ubo = BeneficialOwner(
        company_id=company_id,
        full_name=data.full_name,
        date_of_birth=data.date_of_birth,
        nationality=data.nationality,
        country_of_residence=data.country_of_residence,
        id_type=data.id_type,
        id_number=data.id_number,
        id_country=data.id_country,
        ownership_percentage=data.ownership_percentage,
        ownership_type=data.ownership_type,
        voting_rights_percentage=data.voting_rights_percentage,
        is_director=data.is_director,
        is_shareholder=data.is_shareholder,
        is_signatory=data.is_signatory,
        is_legal_representative=data.is_legal_representative,
        role_title=data.role_title,
        verification_status="pending",
    )

    db.add(ubo)
    await db.flush()

    # Audit log
    await record_audit_log(
        db=db,
        tenant_id=user.tenant_id,
        user_id=UUID(user.id),
        action="ubo.created",
        resource_type="beneficial_owner",
        resource_id=ubo.id,
        new_values={
            "company_id": str(company_id),
            "full_name": data.full_name,
            "ownership_percentage": data.ownership_percentage,
        },
        user_email=user.email,
        ip_address=ctx.ip_address,
    )

    await db.refresh(ubo)
    return BeneficialOwnerResponse.model_validate(ubo)


@router.patch("/{company_id}/beneficial-owners/{ubo_id}", response_model=BeneficialOwnerResponse)
async def update_beneficial_owner(
    company_id: UUID,
    ubo_id: UUID,
    data: BeneficialOwnerUpdate,
    db: TenantDB,
    user: Annotated[AuthenticatedUser, Depends(require_permission("write:companies"))],
    ctx: AuditContext,
):
    """Update a beneficial owner."""
    company = await db.get(Company, company_id)
    if not company or company.tenant_id != user.tenant_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Company not found",
        )

    ubo = await db.get(BeneficialOwner, ubo_id)
    if not ubo or ubo.company_id != company_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Beneficial owner not found",
        )

    # Update fields
    update_data = data.model_dump(exclude_unset=True)
    old_values = {}
    for field in update_data.keys():
        old_values[field] = getattr(ubo, field, None)

    for field, value in update_data.items():
        setattr(ubo, field, value)

    ubo.updated_at = datetime.utcnow()

    # Audit log
    await record_audit_log(
        db=db,
        tenant_id=user.tenant_id,
        user_id=UUID(user.id),
        action="ubo.updated",
        resource_type="beneficial_owner",
        resource_id=ubo.id,
        old_values=old_values,
        new_values=update_data,
        user_email=user.email,
        ip_address=ctx.ip_address,
    )

    await db.flush()
    await db.refresh(ubo)
    return BeneficialOwnerResponse.model_validate(ubo)


@router.delete("/{company_id}/beneficial-owners/{ubo_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_beneficial_owner(
    company_id: UUID,
    ubo_id: UUID,
    db: TenantDB,
    user: Annotated[AuthenticatedUser, Depends(require_permission("write:companies"))],
    ctx: AuditContext,
):
    """Remove a beneficial owner from a company."""
    company = await db.get(Company, company_id)
    if not company or company.tenant_id != user.tenant_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Company not found",
        )

    ubo = await db.get(BeneficialOwner, ubo_id)
    if not ubo or ubo.company_id != company_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Beneficial owner not found",
        )

    # Audit log before deletion
    await record_audit_log(
        db=db,
        tenant_id=user.tenant_id,
        user_id=UUID(user.id),
        action="ubo.deleted",
        resource_type="beneficial_owner",
        resource_id=ubo.id,
        old_values={
            "full_name": ubo.full_name,
            "ownership_percentage": ubo.ownership_percentage,
        },
        user_email=user.email,
        ip_address=ctx.ip_address,
    )

    await db.delete(ubo)
    await db.commit()


@router.post("/{company_id}/beneficial-owners/{ubo_id}/link", response_model=BeneficialOwnerResponse)
async def link_ubo_to_applicant(
    company_id: UUID,
    ubo_id: UUID,
    data: LinkUBOToApplicant,
    db: TenantDB,
    user: Annotated[AuthenticatedUser, Depends(require_permission("write:companies"))],
    ctx: AuditContext,
):
    """Link a beneficial owner to an existing applicant KYC."""
    company = await db.get(Company, company_id)
    if not company or company.tenant_id != user.tenant_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Company not found",
        )

    ubo = await db.get(BeneficialOwner, ubo_id)
    if not ubo or ubo.company_id != company_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Beneficial owner not found",
        )

    # Verify applicant exists and belongs to tenant
    applicant = await db.get(Applicant, data.applicant_id)
    if not applicant or applicant.tenant_id != user.tenant_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Applicant not found",
        )

    # Link UBO to applicant
    ubo.applicant_id = data.applicant_id
    ubo.verification_status = "linked"
    ubo.verified_at = datetime.utcnow()
    ubo.updated_at = datetime.utcnow()

    # Audit log
    await record_audit_log(
        db=db,
        tenant_id=user.tenant_id,
        user_id=UUID(user.id),
        action="ubo.linked",
        resource_type="beneficial_owner",
        resource_id=ubo.id,
        new_values={
            "applicant_id": str(data.applicant_id),
            "applicant_name": applicant.full_name,
        },
        user_email=user.email,
        ip_address=ctx.ip_address,
    )

    await db.flush()
    await db.refresh(ubo)
    return BeneficialOwnerResponse.model_validate(ubo)


# ===========================================
# COMPANY DOCUMENTS
# ===========================================

@router.get("/{company_id}/documents", response_model=list[CompanyDocumentResponse])
async def list_company_documents(
    company_id: UUID,
    db: TenantDB,
    user: Annotated[AuthenticatedUser, Depends(require_permission("read:companies"))],
):
    """List all documents for a company."""
    company = await db.get(Company, company_id)
    if not company or company.tenant_id != user.tenant_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Company not found",
        )

    query = (
        select(CompanyDocument)
        .where(CompanyDocument.company_id == company_id)
        .order_by(CompanyDocument.created_at.desc())
    )
    result = await db.execute(query)
    documents = result.scalars().all()

    return [CompanyDocumentResponse.model_validate(doc) for doc in documents]


@router.post("/{company_id}/documents/upload", status_code=status.HTTP_201_CREATED)
async def request_document_upload(
    company_id: UUID,
    data: CompanyDocumentCreate,
    db: TenantDB,
    user: Annotated[AuthenticatedUser, Depends(require_permission("write:companies"))],
):
    """Request presigned URL for company document upload."""
    company = await db.get(Company, company_id)
    if not company or company.tenant_id != user.tenant_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Company not found",
        )

    # Generate storage key
    storage_key = storage_service.generate_key(
        tenant_id=str(user.tenant_id),
        resource_type="company",
        resource_id=str(company_id),
        filename=data.file_name,
    )

    # Create document record
    document = CompanyDocument(
        company_id=company_id,
        document_type=data.document_type,
        document_subtype=data.document_subtype,
        file_name=data.file_name,
        file_type=data.file_type,
        file_size=data.file_size,
        storage_key=storage_key,
        issue_date=data.issue_date,
        expiry_date=data.expiry_date,
        issuing_authority=data.issuing_authority,
        document_number=data.document_number,
        status="pending",
    )

    db.add(document)
    await db.flush()

    # Generate presigned upload URL
    upload_url = await storage_service.create_presigned_upload(
        key=storage_key,
        content_type=data.file_type or "application/octet-stream",
        metadata={
            "document_id": str(document.id),
            "company_id": str(company_id),
            "document_type": data.document_type,
        },
    )

    await db.commit()

    return {
        "document_id": document.id,
        "upload_url": upload_url,
        "storage_key": storage_key,
    }


@router.post("/{company_id}/documents/{document_id}/verify", response_model=CompanyDocumentResponse)
async def verify_company_document(
    company_id: UUID,
    document_id: UUID,
    data: CompanyDocumentVerify,
    db: TenantDB,
    user: Annotated[AuthenticatedUser, Depends(require_permission("review:companies"))],
    ctx: AuditContext,
):
    """Verify or reject a company document."""
    company = await db.get(Company, company_id)
    if not company or company.tenant_id != user.tenant_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Company not found",
        )

    document = await db.get(CompanyDocument, document_id)
    if not document or document.company_id != company_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found",
        )

    old_status = document.status

    document.status = data.decision
    document.verification_notes = data.notes
    document.verified_at = datetime.utcnow()
    document.verified_by = UUID(user.id)
    document.updated_at = datetime.utcnow()

    # Audit log
    await record_audit_log(
        db=db,
        tenant_id=user.tenant_id,
        user_id=UUID(user.id),
        action="company_document.verified",
        resource_type="company_document",
        resource_id=document.id,
        old_values={"status": old_status},
        new_values={
            "status": data.decision,
            "notes": data.notes,
        },
        user_email=user.email,
        ip_address=ctx.ip_address,
    )

    await db.flush()
    await db.refresh(document)
    return CompanyDocumentResponse.model_validate(document)


@router.get("/{company_id}/documents/{document_id}/download")
async def download_company_document(
    company_id: UUID,
    document_id: UUID,
    db: TenantDB,
    user: Annotated[AuthenticatedUser, Depends(require_permission("read:companies"))],
):
    """Get presigned download URL for a company document."""
    company = await db.get(Company, company_id)
    if not company or company.tenant_id != user.tenant_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Company not found",
        )

    document = await db.get(CompanyDocument, document_id)
    if not document or document.company_id != company_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found",
        )

    download_url = await storage_service.create_presigned_download(
        key=document.storage_key,
        filename=document.file_name,
    )

    return {
        "download_url": download_url,
        "file_name": document.file_name,
        "file_type": document.file_type,
    }
