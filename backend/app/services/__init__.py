"""
Get Clearance - Services Layer
==============================
Business logic and external integrations.

Services encapsulate external API calls and complex business logic,
keeping the API layer thin and focused on request/response handling.
"""

from app.services.screening import ScreeningService, screening_service
from app.services.storage import StorageService, storage_service
from app.services.ai import AIService, ai_service
from app.services.ocr import (
    OCRService,
    ocr_service,
    OCRServiceError,
    OCRConfigError,
)
from app.services.mrz_parser import (
    MRZParser,
    mrz_parser,
    MRZValidationError,
)
from app.services.timeline import (
    TimelineService,
    timeline_service,
    TimelineServiceError,
    TimelineEvent,
    ApplicantTimeline,
)
from app.services.evidence import (
    EvidenceService,
    evidence_service,
    EvidenceServiceError,
    EvidencePackResult,
)

__all__ = [
    # Screening (OpenSanctions)
    "ScreeningService",
    "screening_service",
    # Storage (Cloudflare R2)
    "StorageService",
    "storage_service",
    # AI (Claude/Anthropic)
    "AIService",
    "ai_service",
    # OCR (AWS Textract)
    "OCRService",
    "ocr_service",
    "OCRServiceError",
    "OCRConfigError",
    # MRZ Parser (Passport validation)
    "MRZParser",
    "mrz_parser",
    "MRZValidationError",
    # Timeline (Event aggregation)
    "TimelineService",
    "timeline_service",
    "TimelineServiceError",
    "TimelineEvent",
    "ApplicantTimeline",
    # Evidence (PDF generation)
    "EvidenceService",
    "evidence_service",
    "EvidenceServiceError",
    "EvidencePackResult",
]
