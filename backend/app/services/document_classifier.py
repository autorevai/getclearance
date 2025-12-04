"""
Get Clearance - Document Classifier Service
=============================================
Document type detection using Claude Vision.

Automatically classifies identity documents before OCR processing:
- Detects document type (passport, driver's license, ID card, etc.)
- Identifies country of issue
- Determines document side (front/back)
- Suggests appropriate OCR template

Usage:
    from app.services.document_classifier import document_classifier

    result = await document_classifier.classify(image_bytes)
    print(f"Type: {result.document_type}, Country: {result.country_code}")
"""

import base64
import json
import logging
import time
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any

import anthropic

from app.config import settings

logger = logging.getLogger(__name__)


# ===========================================
# ENUMS AND DATA CLASSES
# ===========================================

class DocumentType(str, Enum):
    """Supported document types."""
    PASSPORT = "passport"
    DRIVERS_LICENSE = "drivers_license"
    ID_CARD = "id_card"
    RESIDENCE_PERMIT = "residence_permit"
    VISA = "visa"
    UTILITY_BILL = "utility_bill"
    BANK_STATEMENT = "bank_statement"
    SELFIE = "selfie"
    UNKNOWN = "unknown"


class DocumentSide(str, Enum):
    """Document side for multi-page documents."""
    FRONT = "front"
    BACK = "back"
    SINGLE = "single"  # For documents that are single-sided (passports)


@dataclass
class ClassificationResult:
    """Result of document classification."""
    document_type: DocumentType
    country_code: str | None  # ISO 3166-1 alpha-2
    side: DocumentSide
    confidence: float  # 0-100
    detected_fields: list[str]  # Fields visible in document
    suggested_ocr_template: str | None
    is_identity_document: bool
    processing_time_ms: int
    raw_response: dict = field(default_factory=dict)
    error_message: str | None = None

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "document_type": self.document_type.value,
            "country_code": self.country_code,
            "side": self.side.value,
            "confidence": self.confidence,
            "detected_fields": self.detected_fields,
            "suggested_ocr_template": self.suggested_ocr_template,
            "is_identity_document": self.is_identity_document,
            "processing_time_ms": self.processing_time_ms,
            "error_message": self.error_message,
        }


# OCR template mappings based on document type and country
OCR_TEMPLATES = {
    "passport": {
        "default": "mrz_passport",
        "US": "us_passport",
        "GB": "uk_passport",
    },
    "drivers_license": {
        "default": "generic_id",
        "US": "us_drivers_license",
        "GB": "uk_drivers_license",
        "DE": "de_drivers_license",
        "AU": "au_drivers_license",
    },
    "id_card": {
        "default": "generic_id",
        "DE": "de_personalausweis",
        "ES": "es_dni",
        "IT": "it_carta_identita",
        "FR": "fr_cni",
    },
    "residence_permit": {
        "default": "generic_id",
    },
    "visa": {
        "default": "mrz_visa",
    },
    "utility_bill": {
        "default": "proof_of_address",
    },
    "bank_statement": {
        "default": "proof_of_address",
    },
}


class DocumentClassifierError(Exception):
    """Base exception for document classifier errors."""
    pass


class ClassifierConfigError(DocumentClassifierError):
    """Configuration error (e.g., missing API key)."""
    pass


# ===========================================
# DOCUMENT CLASSIFIER SERVICE
# ===========================================

class DocumentClassifier:
    """
    Document type classification using Claude Vision.

    Analyzes document images to determine:
    - Document type (passport, license, ID card, etc.)
    - Country of issue (from visual cues)
    - Document side (front/back)
    - Visible fields for OCR targeting

    Usage:
        result = await classifier.classify(image_bytes)
        if result.document_type == DocumentType.PASSPORT:
            # Use MRZ extraction
            ...
    """

    # Supported document types for classification prompt
    DOCUMENT_TYPES = [
        "passport",
        "drivers_license",
        "id_card",
        "residence_permit",
        "visa",
        "utility_bill",
        "bank_statement",
        "selfie",
        "unknown",
    ]

    # Identity documents that require ID verification
    IDENTITY_DOCUMENTS = {
        DocumentType.PASSPORT,
        DocumentType.DRIVERS_LICENSE,
        DocumentType.ID_CARD,
        DocumentType.RESIDENCE_PERMIT,
        DocumentType.VISA,
    }

    def __init__(
        self,
        api_key: str | None = None,
        model: str | None = None,
    ):
        """
        Initialize document classifier.

        Args:
            api_key: Anthropic API key (defaults to settings)
            model: Claude model to use (defaults to settings)
        """
        self.api_key = api_key or settings.anthropic_api_key
        # Use claude-sonnet-4-20250514 for vision tasks (good balance of speed/quality)
        self.model = model or "claude-sonnet-4-20250514"
        self._client: anthropic.AsyncAnthropic | None = None

    @property
    def is_configured(self) -> bool:
        """Check if service is properly configured."""
        return bool(self.api_key)

    def _get_client(self) -> anthropic.AsyncAnthropic:
        """Get or create Anthropic client."""
        if self._client is None:
            if not self.is_configured:
                raise ClassifierConfigError("Anthropic API key not configured")
            self._client = anthropic.AsyncAnthropic(api_key=self.api_key)
        return self._client

    async def classify(
        self,
        image_bytes: bytes,
        filename: str | None = None,
    ) -> ClassificationResult:
        """
        Classify a document image.

        Args:
            image_bytes: Raw image bytes (JPEG, PNG, GIF, or WebP)
            filename: Optional filename for logging

        Returns:
            ClassificationResult with document type and metadata
        """
        start_time = time.time()

        if not self.is_configured:
            logger.warning("Claude Vision not configured, using fallback classification")
            return self._fallback_classification(image_bytes, start_time)

        try:
            # Determine media type from bytes
            media_type = self._detect_media_type(image_bytes)

            # Encode image for API
            image_base64 = base64.standard_b64encode(image_bytes).decode("utf-8")

            logger.info(f"Classifying document: {filename or 'unknown'}")

            client = self._get_client()

            # Build classification prompt
            system_prompt = self._get_system_prompt()

            response = await client.messages.create(
                model=self.model,
                max_tokens=1024,
                system=system_prompt,
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "image",
                                "source": {
                                    "type": "base64",
                                    "media_type": media_type,
                                    "data": image_base64,
                                },
                            },
                            {
                                "type": "text",
                                "text": self._get_classification_prompt(),
                            },
                        ],
                    }
                ],
            )

            processing_time = int((time.time() - start_time) * 1000)

            # Parse response
            result = self._parse_response(response.content[0].text, processing_time)

            logger.info(
                f"Document classified: type={result.document_type.value}, "
                f"country={result.country_code}, confidence={result.confidence:.1f}"
            )

            return result

        except anthropic.APIError as e:
            logger.error(f"Claude Vision API error: {e}")
            processing_time = int((time.time() - start_time) * 1000)
            return ClassificationResult(
                document_type=DocumentType.UNKNOWN,
                country_code=None,
                side=DocumentSide.SINGLE,
                confidence=0.0,
                detected_fields=[],
                suggested_ocr_template="generic_id",
                is_identity_document=False,
                processing_time_ms=processing_time,
                error_message=f"API error: {str(e)}",
            )
        except Exception as e:
            logger.exception(f"Document classification error: {e}")
            processing_time = int((time.time() - start_time) * 1000)
            return ClassificationResult(
                document_type=DocumentType.UNKNOWN,
                country_code=None,
                side=DocumentSide.SINGLE,
                confidence=0.0,
                detected_fields=[],
                suggested_ocr_template="generic_id",
                is_identity_document=False,
                processing_time_ms=processing_time,
                error_message=str(e),
            )

    def _detect_media_type(self, image_bytes: bytes) -> str:
        """Detect image media type from bytes."""
        # Check magic bytes
        if image_bytes[:8] == b'\x89PNG\r\n\x1a\n':
            return "image/png"
        elif image_bytes[:2] == b'\xff\xd8':
            return "image/jpeg"
        elif image_bytes[:6] in (b'GIF87a', b'GIF89a'):
            return "image/gif"
        elif image_bytes[:4] == b'RIFF' and image_bytes[8:12] == b'WEBP':
            return "image/webp"
        else:
            # Default to JPEG
            return "image/jpeg"

    def _get_system_prompt(self) -> str:
        """Get system prompt for classification."""
        return """You are a document classification specialist. Your task is to analyze
identity document images and classify them accurately.

DOCUMENT TYPES YOU CAN IDENTIFY:
- passport: Government-issued travel document with personal details and photo
- drivers_license: Vehicle operator's license with photo and personal details
- id_card: National identity card or state ID
- residence_permit: Document proving legal residence status
- visa: Travel visa document (may be sticker or separate document)
- utility_bill: Utility service bill (electric, gas, water, phone)
- bank_statement: Bank account statement
- selfie: Photo of a person's face (for biometric verification)
- unknown: Cannot determine document type

IMPORTANT:
- Be concise and return only valid JSON
- Country codes must be ISO 3166-1 alpha-2 (e.g., US, GB, DE, FR)
- Confidence should reflect how certain you are (0-100)
- detected_fields should list visible data fields (name, dob, photo, mrz, address, etc.)
- For drivers licenses and ID cards, determine if showing front or back side"""

    def _get_classification_prompt(self) -> str:
        """Get the classification prompt for the image."""
        return """Analyze this identity document image and return JSON:
{
  "document_type": "passport|drivers_license|id_card|residence_permit|visa|utility_bill|bank_statement|selfie|unknown",
  "country_code": "US|GB|DE|...",
  "side": "front|back|single",
  "confidence": 85,
  "detected_fields": ["photo", "name", "dob", "mrz", "address", "expiry", ...]
}

Be concise. Only return valid JSON, no markdown or explanation."""

    def _parse_response(
        self,
        response_text: str,
        processing_time: int,
    ) -> ClassificationResult:
        """Parse Claude's response into ClassificationResult."""
        try:
            # Clean response - remove markdown if present
            json_text = response_text.strip()
            if json_text.startswith("```"):
                # Remove markdown code blocks
                if "```json" in json_text:
                    json_text = json_text.split("```json")[1]
                else:
                    json_text = json_text.split("```")[1]
                json_text = json_text.split("```")[0].strip()

            data = json.loads(json_text)

            # Parse document type
            doc_type_str = data.get("document_type", "unknown").lower()
            try:
                doc_type = DocumentType(doc_type_str)
            except ValueError:
                doc_type = DocumentType.UNKNOWN

            # Parse side
            side_str = data.get("side", "single").lower()
            try:
                side = DocumentSide(side_str)
            except ValueError:
                side = DocumentSide.SINGLE

            # Get country code
            country_code = data.get("country_code")
            if country_code:
                country_code = country_code.upper()[:2]

            # Get detected fields
            detected_fields = data.get("detected_fields", [])
            if isinstance(detected_fields, str):
                detected_fields = [detected_fields]

            # Get confidence
            confidence = float(data.get("confidence", 50))
            confidence = max(0, min(100, confidence))

            # Determine OCR template
            ocr_template = self._get_ocr_template(doc_type, country_code)

            # Check if identity document
            is_identity = doc_type in self.IDENTITY_DOCUMENTS

            return ClassificationResult(
                document_type=doc_type,
                country_code=country_code,
                side=side,
                confidence=confidence,
                detected_fields=detected_fields,
                suggested_ocr_template=ocr_template,
                is_identity_document=is_identity,
                processing_time_ms=processing_time,
                raw_response=data,
            )

        except (json.JSONDecodeError, KeyError) as e:
            logger.error(f"Failed to parse classification response: {e}")
            logger.debug(f"Response text: {response_text}")

            return ClassificationResult(
                document_type=DocumentType.UNKNOWN,
                country_code=None,
                side=DocumentSide.SINGLE,
                confidence=0.0,
                detected_fields=[],
                suggested_ocr_template="generic_id",
                is_identity_document=False,
                processing_time_ms=processing_time,
                error_message=f"Parse error: {str(e)}",
            )

    def _get_ocr_template(
        self,
        doc_type: DocumentType,
        country_code: str | None,
    ) -> str:
        """Get the appropriate OCR template for document type and country."""
        templates = OCR_TEMPLATES.get(doc_type.value, {})

        if country_code and country_code in templates:
            return templates[country_code]

        return templates.get("default", "generic_id")

    def _fallback_classification(
        self,
        image_bytes: bytes,
        start_time: float,
    ) -> ClassificationResult:
        """
        Fallback classification when Claude is not available.

        Uses basic heuristics (file size, dimensions) to make educated guesses.
        """
        processing_time = int((time.time() - start_time) * 1000)

        # Very basic fallback - assume it's an ID card
        return ClassificationResult(
            document_type=DocumentType.ID_CARD,
            country_code=None,
            side=DocumentSide.FRONT,
            confidence=30.0,  # Low confidence for fallback
            detected_fields=[],
            suggested_ocr_template="generic_id",
            is_identity_document=True,
            processing_time_ms=processing_time,
            error_message="Fallback classification - Claude Vision not configured",
        )

    async def classify_batch(
        self,
        images: list[tuple[bytes, str | None]],
    ) -> list[ClassificationResult]:
        """
        Classify multiple document images.

        Args:
            images: List of (image_bytes, filename) tuples

        Returns:
            List of ClassificationResult objects
        """
        results = []
        for image_bytes, filename in images:
            result = await self.classify(image_bytes, filename)
            results.append(result)
        return results


# ===========================================
# SINGLETON INSTANCE
# ===========================================

document_classifier = DocumentClassifier()


# ===========================================
# CONVENIENCE FUNCTIONS
# ===========================================

async def classify_document(
    image_bytes: bytes,
    filename: str | None = None,
) -> ClassificationResult:
    """
    Classify a document image.

    Args:
        image_bytes: Raw image bytes
        filename: Optional filename for logging

    Returns:
        ClassificationResult with document type and metadata
    """
    return await document_classifier.classify(image_bytes, filename)


def get_ocr_template(doc_type: str, country_code: str | None = None) -> str:
    """
    Get the appropriate OCR template for a document.

    Args:
        doc_type: Document type string
        country_code: ISO 3166-1 alpha-2 country code

    Returns:
        OCR template name
    """
    try:
        document_type = DocumentType(doc_type)
    except ValueError:
        return "generic_id"

    return document_classifier._get_ocr_template(document_type, country_code)
