"""
AI Service - Claude API Integration
====================================

Provides AI-powered features:
- Risk assessment summaries
- Document fraud detection via vision
- Case note generation
- Applicant assistant responses

Based on Sumsub reverse engineering - Section 10.5 (AI Integration Strategy)
"""

from datetime import datetime
from typing import Optional
from uuid import UUID
import json
import logging
import base64

from anthropic import Anthropic, HUMAN_PROMPT, AI_PROMPT

from app.config import settings

logger = logging.getLogger(__name__)


class AIService:
    """
    Claude AI integration for compliance intelligence.
    
    Usage:
        ai = AIService()
        summary = await ai.generate_risk_summary(applicant, documents, screening_hits)
    """
    
    def __init__(self):
        """Initialize Anthropic client."""
        self.client = Anthropic(api_key=settings.anthropic_api_key)
        self.model = "claude-sonnet-4-20250514"
    
    async def generate_risk_summary(
        self,
        applicant_data: dict,
        documents: list[dict],
        screening_hits: list[dict],
    ) -> dict:
        """
        Generate AI risk assessment for applicant.
        
        Returns structured summary with:
        - risk_level (low/medium/high)
        - rationale
        - key concerns
        - recommendation (approve/reject/request_additional_info)
        - confidence score
        
        Args:
            applicant_data: Dict with name, DOB, nationality, etc.
            documents: List of document metadata
            screening_hits: List of screening results
        
        Returns:
            dict with risk assessment
        """
        logger.info(f"Generating risk summary for applicant {applicant_data.get('id')}")
        
        # Build context-rich prompt
        prompt = self._build_risk_summary_prompt(applicant_data, documents, screening_hits)
        
        try:
            # Call Claude API
            response = self.client.messages.create(
                model=self.model,
                max_tokens=1500,
                messages=[{
                    "role": "user",
                    "content": prompt
                }]
            )
            
            # Extract and parse response
            response_text = response.content[0].text.strip()
            
            # Remove markdown code blocks if present
            response_text = response_text.replace("```json", "").replace("```", "").strip()
            
            result = json.loads(response_text)
            
            logger.info(f"Generated risk summary: {result.get('risk_level')} confidence: {result.get('confidence')}")
            
            return result
            
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse AI response as JSON: {e}")
            logger.error(f"Raw response: {response_text}")
            raise AIError("AI response was not valid JSON")
        except Exception as e:
            logger.error(f"AI risk summary failed: {e}")
            raise AIError(f"Risk summary generation failed: {str(e)}")
    
    def _build_risk_summary_prompt(
        self,
        applicant: dict,
        documents: list[dict],
        screening_hits: list[dict],
    ) -> str:
        """Build detailed prompt for risk assessment."""
        
        # Format documents
        docs_text = "\n".join([
            f"- {doc.get('type', 'Unknown')}: "
            f"{'✓ Verified' if doc.get('status') == 'verified' else '✗ Failed'} "
            f"(confidence: {doc.get('ocr_confidence', 0)}%)"
            for doc in documents
        ])
        
        # Format screening hits
        hits_text = "\n".join([
            f"- {hit.get('matched_name')} ({hit.get('hit_type')}): "
            f"{hit.get('confidence')}% match, {hit.get('match_type')}"
            for hit in screening_hits
        ]) if screening_hits else "No screening hits"
        
        prompt = f"""Analyze this KYC applicant and provide a risk summary.

APPLICANT INFORMATION:
- Name: {applicant.get('full_name', 'Unknown')}
- Date of Birth: {applicant.get('date_of_birth', 'Unknown')}
- Nationality: {applicant.get('nationality', 'Unknown')}
- Country of Residence: {applicant.get('country_of_residence', 'Unknown')}
- Current Risk Score: {applicant.get('risk_score', 'N/A')}
- Flags: {', '.join(applicant.get('flags', [])) or 'None'}

DOCUMENTS SUBMITTED:
{docs_text or 'No documents yet'}

SCREENING RESULTS:
{hits_text}

TASK:
Provide a comprehensive risk assessment considering:
1. Document verification quality
2. Screening match accuracy and severity
3. Applicant profile completeness
4. Any red flags or concerns
5. Missing information that could reduce risk

Respond ONLY with valid JSON in this exact format:
{{
  "risk_level": "low|medium|high",
  "rationale": "2-3 sentence explanation of the risk assessment",
  "concerns": [
    "Top concern 1",
    "Top concern 2",
    "Top concern 3"
  ],
  "recommendation": "approve|reject|request_additional_info",
  "missing_info": [
    "Missing item 1",
    "Missing item 2"
  ],
  "confidence": 85
}}

CRITICAL RULES:
- DO NOT include any text outside the JSON object
- DO NOT use markdown code blocks
- Concerns array can be empty [] if no concerns
- Missing_info array can be empty [] if nothing missing
- Confidence is 0-100
- Be factual and cite specific evidence from the data provided
"""
        
        return prompt
    
    async def analyze_document_fraud(
        self,
        document_id: UUID,
        image_data: bytes,
        document_type: str,
    ) -> dict:
        """
        Analyze document image for fraud signals using Claude vision.
        
        Checks for:
        - Image editing artifacts (Photoshop traces, inconsistent lighting)
        - Template inconsistencies (font, spacing, alignment)
        - Quality issues (blur, resolution, glare)
        - Security feature presence (holograms, watermarks, microprint)
        
        Args:
            document_id: Document UUID
            image_data: Raw image bytes
            document_type: Type of document (passport, drivers_license, etc.)
        
        Returns:
            dict with fraud_signals, overall_confidence, recommendation
        """
        logger.info(f"Analyzing document {document_id} for fraud ({document_type})")
        
        # Encode image to base64
        image_b64 = base64.b64encode(image_data).decode('utf-8')
        
        # Determine MIME type (simple heuristic)
        mime_type = "image/jpeg"
        if image_data[:4] == b'\x89PNG':
            mime_type = "image/png"
        elif image_data[:2] == b'%PDF':
            mime_type = "application/pdf"
        
        prompt = f"""Analyze this {document_type} for fraud indicators.

Examine the image carefully for:
1. **Image Editing Signs**: Photoshop artifacts, inconsistent lighting/shadows, clone stamp patterns
2. **Template Issues**: Font inconsistencies, spacing/alignment problems, wrong template for country
3. **Quality Problems**: Excessive blur, low resolution, glare/reflections obscuring data
4. **Security Features**: Presence/absence of holograms, watermarks, microprinting, UV features

Respond ONLY with valid JSON:
{{
  "fraud_signals": [
    {{"signal": "description of issue", "severity": "critical|high|medium|low", "confidence": 85}}
  ],
  "security_features_detected": ["hologram", "watermark", "microprint"],
  "overall_confidence": 90,
  "recommendation": "accept|reject|manual_review"
}}

RULES:
- fraud_signals can be empty [] if no issues found
- severity: critical = almost certainly fraud, high = likely fraud, medium = suspicious, low = minor concern
- confidence: 0-100 for each signal
- overall_confidence: 0-100 for the entire assessment
- recommendation: accept (no fraud), reject (definite fraud), manual_review (uncertain)
- DO NOT use markdown, only raw JSON
"""
        
        try:
            response = self.client.messages.create(
                model=self.model,
                max_tokens=2000,
                messages=[{
                    "role": "user",
                    "content": [
                        {
                            "type": "image",
                            "source": {
                                "type": "base64",
                                "media_type": mime_type,
                                "data": image_b64,
                            }
                        },
                        {
                            "type": "text",
                            "text": prompt
                        }
                    ]
                }]
            )
            
            response_text = response.content[0].text.strip()
            response_text = response_text.replace("```json", "").replace("```", "").strip()
            
            result = json.loads(response_text)
            
            logger.info(f"Fraud analysis complete: {result.get('recommendation')} "
                       f"({len(result.get('fraud_signals', []))} signals)")
            
            return result
            
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse AI fraud analysis: {e}")
            raise AIError("AI response was not valid JSON")
        except Exception as e:
            logger.error(f"Document fraud analysis failed: {e}")
            raise AIError(f"Fraud analysis failed: {str(e)}")
    
    async def generate_case_note(
        self,
        case_data: dict,
        screening_hit: dict,
    ) -> str:
        """
        Generate intelligent case note for manual review.
        
        Helps compliance officers by:
        - Summarizing the screening hit
        - Highlighting key decision factors
        - Suggesting next steps
        
        Args:
            case_data: Case information
            screening_hit: Screening hit details
        
        Returns:
            str: Generated case note
        """
        prompt = f"""Generate a concise case note for this screening hit requiring manual review.

CASE: {case_data.get('title')}
HIT DETAILS:
- Matched Name: {screening_hit.get('matched_name')}
- Confidence: {screening_hit.get('confidence')}%
- Match Type: {screening_hit.get('match_type')}
- Hit Type: {screening_hit.get('hit_type')}
- List Source: {screening_hit.get('list_source')}

Write a 2-3 sentence note that:
1. Summarizes why this hit requires review
2. Notes any distinguishing factors (DOB match, country match, etc.)
3. Suggests what additional info would help resolve

Be professional and factual. Do NOT include JSON formatting.
"""
        
        try:
            response = self.client.messages.create(
                model=self.model,
                max_tokens=300,
                messages=[{"role": "user", "content": prompt}]
            )
            
            note = response.content[0].text.strip()
            return note
            
        except Exception as e:
            logger.error(f"Case note generation failed: {e}")
            return f"Screening hit requires manual review. Match confidence: {screening_hit.get('confidence')}%"
    
    async def generate_applicant_assistant_response(
        self,
        user_message: str,
        applicant_context: dict,
    ) -> str:
        """
        Generate response for applicant-facing chat assistant.
        
        Helps users with:
        - Document requirements
        - Upload instructions
        - Verification status questions
        - General KYC guidance
        
        Args:
            user_message: User's question
            applicant_context: Current applicant status/step info
        
        Returns:
            str: Friendly, helpful response
        """
        prompt = f"""You are a helpful KYC onboarding assistant. Answer the user's question clearly and concisely.

APPLICANT STATUS:
- Current Step: {applicant_context.get('current_step', 'Not started')}
- Status: {applicant_context.get('status', 'pending')}
- Completed Steps: {', '.join(applicant_context.get('completed_steps', []))}

USER QUESTION:
{user_message}

Provide a helpful, friendly response (2-3 sentences max). 
- If asking about document requirements, explain what's needed
- If asking about status, explain current state
- If asking about issues, provide clear next steps
- Be reassuring but honest
"""
        
        try:
            response = self.client.messages.create(
                model=self.model,
                max_tokens=500,
                messages=[{"role": "user", "content": prompt}]
            )
            
            return response.content[0].text.strip()
            
        except Exception as e:
            logger.error(f"Assistant response generation failed: {e}")
            return "I'm having trouble right now. Please contact support for assistance."


class AIError(Exception):
    """Custom exception for AI service errors."""
    pass


# Singleton instance
_ai_service: Optional[AIService] = None


def get_ai_service() -> AIService:
    """
    Get singleton AI service instance.
    
    Usage in FastAPI endpoints:
        ai: AIService = Depends(get_ai_service)
    """
    global _ai_service
    if _ai_service is None:
        _ai_service = AIService()
    return _ai_service
