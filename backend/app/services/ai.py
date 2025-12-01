"""
Get Clearance - AI Service
===========================
Claude AI integration for intelligent compliance analysis.

Provides:
- Risk summaries with citations
- Document analysis and fraud detection
- Screening hit resolution suggestions
- Natural language applicant assistance
"""

import json
import logging
from dataclasses import dataclass, field
from datetime import date, datetime
from typing import Any
from uuid import UUID

import anthropic
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.config import settings

logger = logging.getLogger(__name__)


# ===========================================
# DATA CLASSES
# ===========================================

@dataclass
class Citation:
    """A citation/source for an AI claim."""
    source_type: str  # document, screening, step, external
    source_id: str | None
    source_name: str
    excerpt: str | None = None
    confidence: float = 1.0


@dataclass
class RiskFactor:
    """An identified risk factor."""
    category: str  # identity, financial, regulatory, behavioral
    severity: str  # low, medium, high, critical
    description: str
    citations: list[Citation] = field(default_factory=list)


@dataclass
class RiskSummary:
    """Complete AI-generated risk summary."""
    overall_risk: str  # low, medium, high, critical
    risk_score: int  # 0-100
    summary: str
    risk_factors: list[RiskFactor]
    recommendations: list[str]
    citations: list[Citation]
    generated_at: datetime = field(default_factory=datetime.utcnow)
    model_version: str = ""


@dataclass
class DocumentAnalysis:
    """AI analysis of a document."""
    document_id: str
    document_type: str
    authenticity_score: float  # 0-100
    fraud_indicators: list[dict[str, Any]]
    extracted_data: dict[str, Any]
    confidence: float
    notes: str
    generated_at: datetime = field(default_factory=datetime.utcnow)


@dataclass
class HitResolutionSuggestion:
    """AI suggestion for resolving a screening hit."""
    hit_id: str
    suggested_resolution: str  # confirmed_true, confirmed_false
    confidence: float  # 0-100
    reasoning: str
    evidence: list[Citation]
    generated_at: datetime = field(default_factory=datetime.utcnow)


class AIServiceError(Exception):
    """Base exception for AI service errors."""
    pass


class AIConfigError(AIServiceError):
    """Configuration error (e.g., missing API key)."""
    pass


class AIRateLimitError(AIServiceError):
    """Rate limit exceeded."""
    pass


# ===========================================
# AI SERVICE
# ===========================================

class AIService:
    """
    Service for AI-powered compliance analysis using Claude.
    
    All AI outputs include citations to source data, ensuring
    transparency and auditability of AI-assisted decisions.
    
    Usage:
        summary = await ai_service.generate_risk_summary(
            db=session,
            applicant_id=uuid
        )
        
        print(f"Risk: {summary.overall_risk}")
        for factor in summary.risk_factors:
            print(f"  - {factor.description}")
    """
    
    def __init__(
        self,
        api_key: str | None = None,
        model: str | None = None,
        max_tokens: int | None = None,
    ):
        self.api_key = api_key or settings.anthropic_api_key
        self.model = model or settings.anthropic_model
        self.max_tokens = max_tokens or settings.anthropic_max_tokens
        self._client: anthropic.AsyncAnthropic | None = None
    
    @property
    def is_configured(self) -> bool:
        """Check if service is properly configured."""
        return bool(self.api_key)
    
    def _get_client(self) -> anthropic.AsyncAnthropic:
        """Get or create Anthropic client."""
        if self._client is None:
            if not self.is_configured:
                raise AIConfigError("Anthropic API key not configured")
            self._client = anthropic.AsyncAnthropic(api_key=self.api_key)
        return self._client
    
    async def generate_risk_summary(
        self,
        db: AsyncSession,
        applicant_id: UUID,
    ) -> RiskSummary:
        """
        Generate a comprehensive risk summary for an applicant.
        
        Analyzes:
        - Identity verification results
        - Document authenticity
        - Screening hits (sanctions, PEP, adverse media)
        - Behavioral signals (session, device, etc.)
        
        Args:
            db: Database session
            applicant_id: Applicant UUID
            
        Returns:
            RiskSummary with overall risk, factors, and recommendations
        """
        # Import here to avoid circular imports
        from app.models import Applicant, Document, ScreeningCheck
        
        # Fetch applicant with related data
        query = (
            select(Applicant)
            .where(Applicant.id == applicant_id)
            .options(
                selectinload(Applicant.steps),
                selectinload(Applicant.documents),
                selectinload(Applicant.screening_checks).selectinload(
                    ScreeningCheck.hits
                ),
            )
        )
        result = await db.execute(query)
        applicant = result.scalar_one_or_none()
        
        if not applicant:
            raise AIServiceError(f"Applicant not found: {applicant_id}")
        
        # Build context for AI
        context = self._build_applicant_context(applicant)
        
        # Generate summary using Claude
        try:
            client = self._get_client()
            
            system_prompt = self._get_risk_assessment_system_prompt()
            user_prompt = self._get_risk_assessment_user_prompt(context)
            
            response = await client.messages.create(
                model=self.model,
                max_tokens=self.max_tokens,
                system=system_prompt,
                messages=[{"role": "user", "content": user_prompt}],
            )
            
            # Parse structured response
            content = response.content[0].text
            summary = self._parse_risk_summary(content, context)
            summary.model_version = self.model
            
            logger.info(
                f"Generated risk summary for applicant {applicant_id}: "
                f"{summary.overall_risk} ({summary.risk_score})"
            )
            
            return summary
            
        except anthropic.RateLimitError:
            logger.error("Claude API rate limit exceeded")
            raise AIRateLimitError("Rate limit exceeded, please retry later")
        except anthropic.APIError as e:
            logger.error(f"Claude API error: {e}")
            raise AIServiceError(f"AI service error: {e}")
    
    def _build_applicant_context(self, applicant: Any) -> dict[str, Any]:
        """Build context dict from applicant data for AI analysis."""
        context: dict[str, Any] = {
            "applicant": {
                "id": str(applicant.id),
                "name": f"{applicant.first_name or ''} {applicant.last_name or ''}".strip(),
                "email": applicant.email,
                "nationality": applicant.nationality,
                "country_of_residence": applicant.country_of_residence,
                "date_of_birth": (
                    applicant.date_of_birth.isoformat()
                    if applicant.date_of_birth else None
                ),
                "status": applicant.status,
                "source": applicant.source,
                "flags": applicant.flags or [],
            },
            "steps": [],
            "documents": [],
            "screening_checks": [],
        }
        
        # Add verification steps
        for step in applicant.steps:
            context["steps"].append({
                "id": str(step.id),
                "step_type": step.step_type,
                "status": step.status,
                "verification_result": step.verification_result,
                "failure_reasons": step.failure_reasons or [],
            })
        
        # Add documents
        for doc in applicant.documents:
            context["documents"].append({
                "id": str(doc.id),
                "type": doc.type,
                "status": doc.status,
                "ocr_confidence": float(doc.ocr_confidence) if doc.ocr_confidence else None,
                "verification_checks": doc.verification_checks,
                "fraud_signals": doc.fraud_signals,
            })
        
        # Add screening checks and hits
        for check in applicant.screening_checks:
            check_data = {
                "id": str(check.id),
                "status": check.status,
                "check_types": check.check_types,
                "hits": [],
            }
            
            for hit in check.hits:
                check_data["hits"].append({
                    "id": str(hit.id),
                    "hit_type": hit.hit_type,
                    "matched_name": hit.matched_name,
                    "confidence": float(hit.confidence),
                    "list_source": hit.list_source,
                    "resolution_status": hit.resolution_status,
                    "pep_tier": hit.pep_tier,
                    "categories": hit.categories or [],
                })
            
            context["screening_checks"].append(check_data)
        
        return context
    
    def _get_risk_assessment_system_prompt(self) -> str:
        """Get system prompt for risk assessment."""
        return """You are a KYC/AML compliance analyst AI assistant for Get Clearance, 
a compliance platform. Your role is to analyze applicant data and provide 
risk assessments with clear citations to source data.

IMPORTANT GUIDELINES:
1. Always cite specific evidence for any risk factor identified
2. Be objective and consistent in risk scoring
3. Consider both direct and indirect risk indicators
4. Provide actionable recommendations
5. Never make claims without supporting evidence

RISK SCORING:
- 0-25: Low risk - Standard processing appropriate
- 26-50: Medium risk - Enhanced due diligence recommended
- 51-75: High risk - Senior review required
- 76-100: Critical risk - Escalation to compliance officer

OUTPUT FORMAT:
Respond with a JSON object containing:
{
  "overall_risk": "low|medium|high|critical",
  "risk_score": <0-100>,
  "summary": "<2-3 sentence summary>",
  "risk_factors": [
    {
      "category": "identity|financial|regulatory|behavioral",
      "severity": "low|medium|high|critical",
      "description": "<clear description>",
      "source_type": "<document|screening|step|external>",
      "source_id": "<id if applicable>",
      "source_name": "<readable source name>",
      "excerpt": "<relevant excerpt if applicable>"
    }
  ],
  "recommendations": ["<actionable recommendation>", ...]
}"""
    
    def _get_risk_assessment_user_prompt(self, context: dict[str, Any]) -> str:
        """Build user prompt with applicant context."""
        return f"""Analyze the following applicant data and provide a comprehensive 
risk assessment. Consider all available evidence including verification steps, 
document analysis, and screening results.

APPLICANT DATA:
{json.dumps(context, indent=2, default=str)}

Provide your risk assessment in the specified JSON format. Ensure all risk 
factors have clear citations to the source data provided above."""
    
    def _parse_risk_summary(
        self,
        response_text: str,
        context: dict[str, Any],
    ) -> RiskSummary:
        """Parse AI response into RiskSummary object."""
        try:
            # Extract JSON from response (handle markdown code blocks)
            json_text = response_text
            if "```json" in response_text:
                json_text = response_text.split("```json")[1].split("```")[0]
            elif "```" in response_text:
                json_text = response_text.split("```")[1].split("```")[0]
            
            data = json.loads(json_text.strip())
            
            # Build risk factors with citations
            risk_factors = []
            all_citations = []
            
            for rf in data.get("risk_factors", []):
                citation = Citation(
                    source_type=rf.get("source_type", "unknown"),
                    source_id=rf.get("source_id"),
                    source_name=rf.get("source_name", "Unknown source"),
                    excerpt=rf.get("excerpt"),
                )
                all_citations.append(citation)
                
                risk_factors.append(RiskFactor(
                    category=rf.get("category", "other"),
                    severity=rf.get("severity", "medium"),
                    description=rf.get("description", ""),
                    citations=[citation],
                ))
            
            return RiskSummary(
                overall_risk=data.get("overall_risk", "medium"),
                risk_score=data.get("risk_score", 50),
                summary=data.get("summary", ""),
                risk_factors=risk_factors,
                recommendations=data.get("recommendations", []),
                citations=all_citations,
            )
            
        except (json.JSONDecodeError, KeyError) as e:
            logger.error(f"Failed to parse AI response: {e}")
            # Return a safe default
            return RiskSummary(
                overall_risk="medium",
                risk_score=50,
                summary="Unable to generate automated summary. Manual review required.",
                risk_factors=[],
                recommendations=["Manual review recommended due to AI processing error"],
                citations=[],
            )
    
    async def analyze_document(
        self,
        db: AsyncSession,
        document_id: UUID,
    ) -> DocumentAnalysis:
        """
        Analyze a document for authenticity and extract data.
        
        This would typically involve:
        1. OCR text analysis
        2. Format consistency checks
        3. Data extraction and validation
        4. Fraud signal detection
        
        Args:
            db: Database session
            document_id: Document UUID
            
        Returns:
            DocumentAnalysis with findings and extracted data
        """
        from app.models import Document
        
        query = select(Document).where(Document.id == document_id)
        result = await db.execute(query)
        document = result.scalar_one_or_none()
        
        if not document:
            raise AIServiceError(f"Document not found: {document_id}")
        
        # Build context for analysis
        context = {
            "document_id": str(document.id),
            "type": document.type,
            "ocr_text": document.ocr_text,
            "ocr_confidence": float(document.ocr_confidence) if document.ocr_confidence else None,
            "existing_checks": document.verification_checks,
            "extracted_data": document.extracted_data,
        }
        
        try:
            client = self._get_client()
            
            system_prompt = """You are a document fraud detection specialist. 
Analyze the provided document data and identify:
1. Potential fraud indicators
2. Data extraction from OCR text
3. Consistency issues
4. Authenticity score (0-100)

Respond with JSON:
{
  "authenticity_score": <0-100>,
  "fraud_indicators": [
    {"indicator": "<description>", "severity": "low|medium|high", "evidence": "<evidence>"}
  ],
  "extracted_data": {<key-value pairs extracted from document>},
  "confidence": <0-100>,
  "notes": "<summary notes>"
}"""
            
            response = await client.messages.create(
                model=self.model,
                max_tokens=self.max_tokens,
                system=system_prompt,
                messages=[{
                    "role": "user",
                    "content": f"Analyze this document:\n{json.dumps(context, indent=2, default=str)}"
                }],
            )
            
            # Parse response
            content = response.content[0].text
            json_text = content
            if "```json" in content:
                json_text = content.split("```json")[1].split("```")[0]
            elif "```" in content:
                json_text = content.split("```")[1].split("```")[0]
            
            data = json.loads(json_text.strip())
            
            return DocumentAnalysis(
                document_id=str(document_id),
                document_type=document.type,
                authenticity_score=data.get("authenticity_score", 50),
                fraud_indicators=data.get("fraud_indicators", []),
                extracted_data=data.get("extracted_data", {}),
                confidence=data.get("confidence", 50),
                notes=data.get("notes", ""),
            )
            
        except (anthropic.APIError, json.JSONDecodeError) as e:
            logger.error(f"Document analysis error: {e}")
            return DocumentAnalysis(
                document_id=str(document_id),
                document_type=document.type,
                authenticity_score=50,
                fraud_indicators=[],
                extracted_data={},
                confidence=0,
                notes="Analysis failed, manual review required",
            )
    
    async def suggest_hit_resolution(
        self,
        db: AsyncSession,
        hit_id: UUID,
    ) -> HitResolutionSuggestion:
        """
        Suggest a resolution for a screening hit.
        
        Analyzes the hit data against applicant information to determine
        if it's likely a true match or false positive.
        
        Args:
            db: Database session
            hit_id: Screening hit UUID
            
        Returns:
            HitResolutionSuggestion with reasoning and evidence
        """
        from app.models import ScreeningHit, ScreeningCheck, Applicant
        
        query = (
            select(ScreeningHit)
            .where(ScreeningHit.id == hit_id)
            .options(
                selectinload(ScreeningHit.check).selectinload(ScreeningCheck.applicant)
            )
        )
        result = await db.execute(query)
        hit = result.scalar_one_or_none()
        
        if not hit:
            raise AIServiceError(f"Screening hit not found: {hit_id}")
        
        applicant = hit.check.applicant if hit.check else None
        
        # Build context
        context = {
            "hit": {
                "id": str(hit.id),
                "hit_type": hit.hit_type,
                "matched_name": hit.matched_name,
                "confidence": float(hit.confidence),
                "matched_fields": hit.matched_fields,
                "list_source": hit.list_source,
                "match_data": hit.match_data,
                "pep_tier": hit.pep_tier,
                "pep_position": hit.pep_position,
                "categories": hit.categories,
            },
            "applicant": None,
        }
        
        if applicant:
            context["applicant"] = {
                "name": f"{applicant.first_name or ''} {applicant.last_name or ''}".strip(),
                "date_of_birth": (
                    applicant.date_of_birth.isoformat()
                    if applicant.date_of_birth else None
                ),
                "nationality": applicant.nationality,
                "country_of_residence": applicant.country_of_residence,
            }
        
        try:
            client = self._get_client()
            
            system_prompt = """You are a sanctions screening analyst. 
Compare the screening hit against the applicant data and determine if this 
is likely a TRUE MATCH or FALSE POSITIVE.

Consider:
1. Name similarity and variations
2. Date of birth match
3. Nationality/country match
4. Other identifying information

Respond with JSON:
{
  "suggested_resolution": "confirmed_true|confirmed_false",
  "confidence": <0-100>,
  "reasoning": "<detailed reasoning>",
  "evidence": [
    {"type": "<match|mismatch>", "field": "<field name>", "details": "<explanation>"}
  ]
}"""
            
            response = await client.messages.create(
                model=self.model,
                max_tokens=self.max_tokens,
                system=system_prompt,
                messages=[{
                    "role": "user",
                    "content": f"Analyze this screening hit:\n{json.dumps(context, indent=2, default=str)}"
                }],
            )
            
            # Parse response
            content = response.content[0].text
            json_text = content
            if "```json" in content:
                json_text = content.split("```json")[1].split("```")[0]
            elif "```" in content:
                json_text = content.split("```")[1].split("```")[0]
            
            data = json.loads(json_text.strip())
            
            # Build citations from evidence
            citations = []
            for ev in data.get("evidence", []):
                citations.append(Citation(
                    source_type="screening",
                    source_id=str(hit_id),
                    source_name=f"{ev.get('field', 'Unknown')} comparison",
                    excerpt=ev.get("details"),
                ))
            
            return HitResolutionSuggestion(
                hit_id=str(hit_id),
                suggested_resolution=data.get("suggested_resolution", "confirmed_false"),
                confidence=data.get("confidence", 50),
                reasoning=data.get("reasoning", ""),
                evidence=citations,
            )
            
        except (anthropic.APIError, json.JSONDecodeError) as e:
            logger.error(f"Hit resolution suggestion error: {e}")
            return HitResolutionSuggestion(
                hit_id=str(hit_id),
                suggested_resolution="confirmed_false",
                confidence=0,
                reasoning="Unable to generate suggestion, manual review required",
                evidence=[],
            )
    
    async def generate_applicant_response(
        self,
        query: str,
        applicant_context: dict[str, Any] | None = None,
    ) -> str:
        """
        Generate a response for the applicant-facing assistant.
        
        This helps applicants understand what's needed and guides them
        through the verification process.
        
        Args:
            query: Applicant's question
            applicant_context: Optional context about their application
            
        Returns:
            Helpful response string
        """
        try:
            client = self._get_client()
            
            system_prompt = """You are a helpful assistant for Get Clearance, 
a KYC verification platform. Help applicants understand:
1. What documents they need
2. Why verification is required
3. How to resolve issues
4. What to expect in the process

Be friendly, clear, and professional. Never share internal risk 
assessments or screening details with applicants."""
            
            context_text = ""
            if applicant_context:
                context_text = f"\n\nApplicant context:\n{json.dumps(applicant_context, indent=2, default=str)}"
            
            response = await client.messages.create(
                model=self.model,
                max_tokens=1024,
                system=system_prompt,
                messages=[{
                    "role": "user",
                    "content": f"{query}{context_text}"
                }],
            )
            
            return response.content[0].text
            
        except anthropic.APIError as e:
            logger.error(f"Applicant assistant error: {e}")
            return "I apologize, but I'm having trouble processing your request right now. Please try again or contact support for assistance."


# ===========================================
# SINGLETON INSTANCE
# ===========================================

ai_service = AIService()
