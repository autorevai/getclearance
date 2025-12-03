"""
Get Clearance - AI API
=======================
AI-powered analysis endpoints.
"""

from datetime import datetime
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy import select

from app.dependencies import TenantDB, AuthenticatedUser
from app.models import Applicant, Document, BatchJob
from app.services.ai import ai_service, AIServiceError, AIConfigError

router = APIRouter()


# ===========================================
# SCHEMAS
# ===========================================

class CitationResponse(BaseModel):
    """A citation/source for an AI claim."""
    source_type: str
    source_id: str | None
    source_name: str
    excerpt: str | None = None
    confidence: float = 1.0


class RiskFactorResponse(BaseModel):
    """An identified risk factor."""
    category: str
    severity: str
    description: str
    citations: list[CitationResponse] = []


class RiskSummaryResponse(BaseModel):
    """Complete AI-generated risk summary."""
    overall_risk: str
    risk_score: int
    summary: str
    risk_factors: list[RiskFactorResponse]
    recommendations: list[str]
    citations: list[CitationResponse]
    generated_at: datetime
    model_version: str


class AssistantRequest(BaseModel):
    """Request for the applicant-facing assistant."""
    query: str
    applicant_id: UUID | None = None


class AssistantResponse(BaseModel):
    """Response from the assistant."""
    response: str
    generated_at: datetime


# ===========================================
# GENERATE RISK SUMMARY
# ===========================================
@router.get("/applicants/{applicant_id}/risk-summary", response_model=RiskSummaryResponse)
async def get_risk_summary(
    applicant_id: UUID,
    db: TenantDB,
    user: AuthenticatedUser,
):
    """
    Generate an AI-powered risk summary for an applicant.
    
    Analyzes:
    - Identity verification results
    - Document authenticity
    - Screening hits (sanctions, PEP, adverse media)
    - Behavioral signals
    
    Returns a comprehensive risk assessment with citations.
    """
    # Verify applicant exists and belongs to tenant
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
        summary = await ai_service.generate_risk_summary(db, applicant_id)
        
        # Convert dataclasses to response models
        return RiskSummaryResponse(
            overall_risk=summary.overall_risk,
            risk_score=summary.risk_score,
            summary=summary.summary,
            risk_factors=[
                RiskFactorResponse(
                    category=rf.category,
                    severity=rf.severity,
                    description=rf.description,
                    citations=[
                        CitationResponse(
                            source_type=c.source_type,
                            source_id=c.source_id,
                            source_name=c.source_name,
                            excerpt=c.excerpt,
                            confidence=c.confidence,
                        )
                        for c in rf.citations
                    ],
                )
                for rf in summary.risk_factors
            ],
            recommendations=summary.recommendations,
            citations=[
                CitationResponse(
                    source_type=c.source_type,
                    source_id=c.source_id,
                    source_name=c.source_name,
                    excerpt=c.excerpt,
                    confidence=c.confidence,
                )
                for c in summary.citations
            ],
            generated_at=summary.generated_at,
            model_version=summary.model_version,
        )
        
    except AIConfigError:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="AI service not configured. Set ANTHROPIC_API_KEY.",
        )
    except AIServiceError as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"AI service error: {str(e)}",
        )


# ===========================================
# REGENERATE RISK SUMMARY
# ===========================================
@router.post("/applicants/{applicant_id}/risk-summary", response_model=RiskSummaryResponse)
async def regenerate_risk_summary(
    applicant_id: UUID,
    db: TenantDB,
    user: AuthenticatedUser,
):
    """
    Regenerate the risk summary for an applicant.
    
    Call this after new information is added (documents, screening results, etc.)
    to get an updated risk assessment.
    """
    # Same logic as GET, just explicit POST for regeneration
    return await get_risk_summary(applicant_id, db, user)


# ===========================================
# APPLICANT ASSISTANT
# ===========================================
@router.post("/assistant", response_model=AssistantResponse)
async def applicant_assistant(
    data: AssistantRequest,
    db: TenantDB,
    user: AuthenticatedUser,
):
    """
    Applicant-facing AI assistant.
    
    Helps applicants understand:
    - What documents they need
    - Why verification is required
    - How to resolve issues
    - What to expect in the process
    
    Note: This does NOT share internal risk assessments or
    screening details with applicants.
    """
    # Get applicant context if provided
    applicant_context = None
    
    if data.applicant_id:
        query = select(Applicant).where(
            Applicant.id == data.applicant_id,
            Applicant.tenant_id == user.tenant_id,
        )
        result = await db.execute(query)
        applicant = result.scalar_one_or_none()
        
        if applicant:
            # Only include safe-to-share information
            applicant_context = {
                "status": applicant.status,
                "current_step": None,  # TODO: Get current step
                "submitted_at": applicant.submitted_at.isoformat() if applicant.submitted_at else None,
            }
    
    try:
        response = await ai_service.generate_applicant_response(
            query=data.query,
            applicant_context=applicant_context,
        )
        
        return AssistantResponse(
            response=response,
            generated_at=datetime.utcnow(),
        )
        
    except AIServiceError as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"AI service error: {str(e)}",
        )


# ===========================================
# BATCH RISK ANALYSIS
# ===========================================
@router.post("/batch-analyze")
async def batch_analyze(
    applicant_ids: list[UUID],
    db: TenantDB,
    user: AuthenticatedUser,
):
    """
    Run batch AI analysis on multiple applicants.
    
    Returns a summary of risk scores for quick review.
    
    Note: For large batches, consider using background jobs instead.
    """
    if len(applicant_ids) > 20:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Maximum 20 applicants per batch. Use background jobs for larger batches.",
        )
    
    # Verify all applicants exist and belong to tenant
    query = select(Applicant).where(
        Applicant.id.in_(applicant_ids),
        Applicant.tenant_id == user.tenant_id,
    )
    result = await db.execute(query)
    applicants = result.scalars().all()
    
    found_ids = {a.id for a in applicants}
    missing_ids = set(applicant_ids) - found_ids
    
    if missing_ids:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Applicants not found: {[str(id) for id in missing_ids]}",
        )
    
    # Run analysis for each
    results = []
    errors = []
    
    for applicant in applicants:
        try:
            summary = await ai_service.generate_risk_summary(db, applicant.id)
            results.append({
                "applicant_id": str(applicant.id),
                "name": f"{applicant.first_name or ''} {applicant.last_name or ''}".strip(),
                "overall_risk": summary.overall_risk,
                "risk_score": summary.risk_score,
                "summary": summary.summary,
                "generated_at": summary.generated_at.isoformat(),
            })
        except AIServiceError as e:
            errors.append({
                "applicant_id": str(applicant.id),
                "error": str(e),
            })
    
    # Create a batch job record for tracking
    job = BatchJob(
        tenant_id=user.tenant_id,
        job_type="risk_analysis",
        status="completed",  # Synchronous job, already done
        progress=100,
        total_items=len(applicant_ids),
        processed_items=len(results),
        failed_items=len(errors),
        input_data={"applicant_ids": [str(id) for id in applicant_ids]},
        results=results,
        errors=errors,
        started_at=datetime.utcnow(),
        completed_at=datetime.utcnow(),
        created_by=UUID(user.id),
    )
    db.add(job)
    await db.flush()

    return {
        "job_id": str(job.id),
        "analyzed": len(results),
        "failed": len(errors),
        "results": results,
        "errors": errors,
    }


# ===========================================
# BATCH JOB STATUS
# ===========================================
class BatchJobStatusResponse(BaseModel):
    """Status of a batch analysis job."""
    job_id: UUID
    job_type: str
    status: str  # pending, processing, completed, failed
    progress: int  # 0-100
    total_items: int
    processed_items: int
    failed_items: int
    results: list[dict] = []
    errors: list[dict] = []
    started_at: datetime | None
    completed_at: datetime | None
    created_at: datetime

    model_config = {"from_attributes": True}


@router.get("/batch-analyze/{job_id}", response_model=BatchJobStatusResponse)
async def get_batch_job_status(
    job_id: UUID,
    db: TenantDB,
    user: AuthenticatedUser,
):
    """
    Get status of a batch analysis job.

    Use this to check progress of long-running batch operations.
    """
    query = select(BatchJob).where(
        BatchJob.id == job_id,
        BatchJob.tenant_id == user.tenant_id,
    )
    result = await db.execute(query)
    job = result.scalar_one_or_none()

    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Batch job not found",
        )

    return BatchJobStatusResponse(
        job_id=job.id,
        job_type=job.job_type,
        status=job.status,
        progress=job.progress,
        total_items=job.total_items,
        processed_items=job.processed_items,
        failed_items=job.failed_items,
        results=job.results or [],
        errors=job.errors or [],
        started_at=job.started_at,
        completed_at=job.completed_at,
        created_at=job.created_at,
    )


# ===========================================
# DOCUMENT SUGGESTIONS
# ===========================================
class DocumentSuggestion(BaseModel):
    """A single suggestion for a document."""
    type: str  # quality, completeness, verification, expiry
    severity: str  # info, warning, error
    message: str
    action: str | None = None  # Suggested action to take


class DocumentSuggestionsResponse(BaseModel):
    """AI-generated suggestions for a document."""
    document_id: UUID
    suggestions: list[DocumentSuggestion]
    generated_at: datetime


@router.get("/documents/{document_id}/suggestions", response_model=DocumentSuggestionsResponse)
async def get_document_suggestions(
    document_id: UUID,
    db: TenantDB,
    user: AuthenticatedUser,
):
    """
    Get AI suggestions for document issues.

    Analyzes the document and provides suggestions for:
    - Quality improvements (blur, lighting, legibility)
    - Completeness (missing fields, partial captures)
    - Verification concerns (tampering indicators, mismatches)
    - Expiry issues (expired documents)
    """
    # Verify document exists and belongs to tenant
    query = (
        select(Document)
        .where(Document.id == document_id)
        .join(Applicant)
        .where(Applicant.tenant_id == user.tenant_id)
    )
    result = await db.execute(query)
    document = result.scalar_one_or_none()

    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found",
        )

    suggestions = []

    # Check document status and generate relevant suggestions
    if document.status == "pending":
        suggestions.append(DocumentSuggestion(
            type="completeness",
            severity="info",
            message="Document is pending review",
            action="Complete document verification",
        ))

    if document.status == "rejected":
        suggestions.append(DocumentSuggestion(
            type="verification",
            severity="error",
            message=f"Document was rejected: {document.rejection_reason or 'No reason provided'}",
            action="Request new document upload",
        ))

    # Check for expiry
    if document.expiry_date:
        from datetime import date
        if document.expiry_date < date.today():
            suggestions.append(DocumentSuggestion(
                type="expiry",
                severity="error",
                message="Document has expired",
                action="Request current, unexpired document",
            ))
        elif (document.expiry_date - date.today()).days < 30:
            suggestions.append(DocumentSuggestion(
                type="expiry",
                severity="warning",
                message="Document expires within 30 days",
                action="Consider requesting updated document",
            ))

    # Check OCR confidence if available
    if document.ocr_confidence is not None:
        if document.ocr_confidence < 0.7:
            suggestions.append(DocumentSuggestion(
                type="quality",
                severity="warning",
                message=f"Low OCR confidence ({document.ocr_confidence:.0%}). Document may be unclear.",
                action="Request higher quality image",
            ))
        elif document.ocr_confidence < 0.5:
            suggestions.append(DocumentSuggestion(
                type="quality",
                severity="error",
                message=f"Very low OCR confidence ({document.ocr_confidence:.0%}). Unable to read document.",
                action="Reject and request new upload",
            ))

    # Check for missing extracted data
    extracted = document.extracted_data or {}
    if document.document_type in ["passport", "id_card", "drivers_license"]:
        required_fields = ["full_name", "date_of_birth", "document_number"]
        missing = [f for f in required_fields if not extracted.get(f)]
        if missing:
            suggestions.append(DocumentSuggestion(
                type="completeness",
                severity="warning",
                message=f"Missing extracted fields: {', '.join(missing)}",
                action="Verify manually or request re-upload",
            ))

    # Check for fraud signals
    fraud_signals = document.fraud_signals or {}
    if fraud_signals.get("tampering_detected"):
        suggestions.append(DocumentSuggestion(
            type="verification",
            severity="error",
            message="Potential document tampering detected",
            action="Flag for manual review",
        ))
    if fraud_signals.get("face_mismatch"):
        suggestions.append(DocumentSuggestion(
            type="verification",
            severity="error",
            message="Face on document does not match selfie",
            action="Escalate to investigation",
        ))

    # If no suggestions, add a positive one
    if not suggestions:
        suggestions.append(DocumentSuggestion(
            type="info",
            severity="info",
            message="No issues detected with this document",
            action=None,
        ))

    return DocumentSuggestionsResponse(
        document_id=document_id,
        suggestions=suggestions,
        generated_at=datetime.utcnow(),
    )
