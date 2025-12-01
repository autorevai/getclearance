"""
Get Clearance - AI API
=======================
AI-powered analysis endpoints.
"""

from datetime import datetime
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy import select

from app.dependencies import TenantDB, AuthenticatedUser
from app.models import Applicant
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
    
    return {
        "analyzed": len(results),
        "failed": len(errors),
        "results": results,
        "errors": errors,
    }
