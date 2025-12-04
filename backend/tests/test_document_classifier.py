"""
Tests for Document Classifier Service
======================================
Tests for Claude Vision document classification.
"""

import base64
import json
import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from app.services.document_classifier import (
    DocumentClassifier,
    DocumentType,
    DocumentSide,
    ClassificationResult,
    document_classifier,
    classify_document,
    get_ocr_template,
    OCR_TEMPLATES,
)


# ===========================================
# FIXTURES
# ===========================================

@pytest.fixture
def classifier():
    """Create a classifier instance with test API key."""
    return DocumentClassifier(api_key="test-api-key")


@pytest.fixture
def mock_claude_response():
    """Mock Claude API response for passport."""
    return {
        "document_type": "passport",
        "country_code": "US",
        "side": "single",
        "confidence": 95,
        "detected_fields": ["photo", "name", "dob", "mrz", "expiry"],
    }


@pytest.fixture
def mock_image_bytes():
    """Create mock image bytes (minimal PNG)."""
    # Minimal PNG header
    return b'\x89PNG\r\n\x1a\n' + b'\x00' * 100


@pytest.fixture
def mock_jpeg_bytes():
    """Create mock JPEG bytes."""
    return b'\xff\xd8\xff\xe0' + b'\x00' * 100


# ===========================================
# UNIT TESTS - DocumentClassifier
# ===========================================

class TestDocumentClassifier:
    """Tests for DocumentClassifier class."""

    def test_is_configured_with_api_key(self, classifier):
        """Test is_configured returns True when API key is set."""
        assert classifier.is_configured is True

    def test_is_configured_without_api_key(self):
        """Test is_configured returns False without API key."""
        classifier = DocumentClassifier(api_key=None)
        classifier.api_key = ""  # Explicitly set to empty string
        assert classifier.is_configured is False

    def test_detect_media_type_png(self, classifier, mock_image_bytes):
        """Test PNG detection from magic bytes."""
        media_type = classifier._detect_media_type(mock_image_bytes)
        assert media_type == "image/png"

    def test_detect_media_type_jpeg(self, classifier, mock_jpeg_bytes):
        """Test JPEG detection from magic bytes."""
        media_type = classifier._detect_media_type(mock_jpeg_bytes)
        assert media_type == "image/jpeg"

    def test_detect_media_type_unknown(self, classifier):
        """Test unknown media type defaults to JPEG."""
        unknown_bytes = b'\x00\x00\x00\x00'
        media_type = classifier._detect_media_type(unknown_bytes)
        assert media_type == "image/jpeg"

    def test_get_ocr_template_passport_us(self, classifier):
        """Test OCR template selection for US passport."""
        template = classifier._get_ocr_template(DocumentType.PASSPORT, "US")
        assert template == "us_passport"

    def test_get_ocr_template_passport_default(self, classifier):
        """Test OCR template selection for generic passport."""
        template = classifier._get_ocr_template(DocumentType.PASSPORT, "XX")
        assert template == "mrz_passport"

    def test_get_ocr_template_drivers_license_gb(self, classifier):
        """Test OCR template selection for UK driver's license."""
        template = classifier._get_ocr_template(DocumentType.DRIVERS_LICENSE, "GB")
        assert template == "uk_drivers_license"

    def test_get_ocr_template_unknown_type(self, classifier):
        """Test OCR template for unknown document type."""
        template = classifier._get_ocr_template(DocumentType.UNKNOWN, None)
        assert template == "generic_id"

    def test_parse_response_valid_json(self, classifier, mock_claude_response):
        """Test parsing valid Claude response."""
        response_text = json.dumps(mock_claude_response)
        result = classifier._parse_response(response_text, processing_time=100)

        assert result.document_type == DocumentType.PASSPORT
        assert result.country_code == "US"
        assert result.side == DocumentSide.SINGLE
        assert result.confidence == 95
        assert "photo" in result.detected_fields
        assert result.is_identity_document is True
        assert result.processing_time_ms == 100

    def test_parse_response_with_markdown(self, classifier, mock_claude_response):
        """Test parsing response wrapped in markdown code blocks."""
        response_text = f"```json\n{json.dumps(mock_claude_response)}\n```"
        result = classifier._parse_response(response_text, processing_time=100)

        assert result.document_type == DocumentType.PASSPORT
        assert result.confidence == 95

    def test_parse_response_invalid_json(self, classifier):
        """Test parsing invalid JSON returns UNKNOWN type."""
        result = classifier._parse_response("not valid json", processing_time=100)

        assert result.document_type == DocumentType.UNKNOWN
        assert result.confidence == 0.0
        assert result.error_message is not None

    def test_parse_response_unknown_document_type(self, classifier):
        """Test parsing response with unrecognized document type."""
        response = {"document_type": "something_weird", "confidence": 50}
        result = classifier._parse_response(json.dumps(response), processing_time=100)

        assert result.document_type == DocumentType.UNKNOWN

    def test_fallback_classification(self, classifier):
        """Test fallback classification when Claude not available."""
        import time
        start = time.time()
        result = classifier._fallback_classification(b"test", start)

        assert result.document_type == DocumentType.ID_CARD
        assert result.confidence == 30.0  # Low confidence
        assert result.error_message is not None
        assert "Fallback" in result.error_message


class TestClassificationResult:
    """Tests for ClassificationResult dataclass."""

    def test_to_dict(self):
        """Test conversion to dictionary."""
        result = ClassificationResult(
            document_type=DocumentType.PASSPORT,
            country_code="US",
            side=DocumentSide.SINGLE,
            confidence=95.0,
            detected_fields=["photo", "mrz"],
            suggested_ocr_template="us_passport",
            is_identity_document=True,
            processing_time_ms=150,
        )

        d = result.to_dict()

        assert d["document_type"] == "passport"
        assert d["country_code"] == "US"
        assert d["side"] == "single"
        assert d["confidence"] == 95.0
        assert d["is_identity_document"] is True


# ===========================================
# ASYNC TESTS - Classification
# ===========================================

@pytest.mark.asyncio
class TestClassifyAsync:
    """Async tests for document classification."""

    async def test_classify_passport(self, classifier, mock_image_bytes):
        """Test classifying a passport image."""
        mock_response = MagicMock()
        mock_response.content = [
            MagicMock(text=json.dumps({
                "document_type": "passport",
                "country_code": "US",
                "side": "single",
                "confidence": 95,
                "detected_fields": ["photo", "mrz"],
            }))
        ]

        with patch.object(classifier, '_get_client') as mock_get_client:
            mock_client = AsyncMock()
            mock_client.messages.create = AsyncMock(return_value=mock_response)
            mock_get_client.return_value = mock_client

            result = await classifier.classify(mock_image_bytes, filename="passport.jpg")

            assert result.document_type == DocumentType.PASSPORT
            assert result.country_code == "US"
            assert result.is_identity_document is True

    async def test_classify_drivers_license(self, classifier, mock_jpeg_bytes):
        """Test classifying a driver's license image."""
        mock_response = MagicMock()
        mock_response.content = [
            MagicMock(text=json.dumps({
                "document_type": "drivers_license",
                "country_code": "GB",
                "side": "front",
                "confidence": 88,
                "detected_fields": ["photo", "name", "address"],
            }))
        ]

        with patch.object(classifier, '_get_client') as mock_get_client:
            mock_client = AsyncMock()
            mock_client.messages.create = AsyncMock(return_value=mock_response)
            mock_get_client.return_value = mock_client

            result = await classifier.classify(mock_jpeg_bytes)

            assert result.document_type == DocumentType.DRIVERS_LICENSE
            assert result.side == DocumentSide.FRONT
            assert result.suggested_ocr_template == "uk_drivers_license"

    async def test_classify_utility_bill(self, classifier, mock_image_bytes):
        """Test classifying a utility bill (non-identity document)."""
        mock_response = MagicMock()
        mock_response.content = [
            MagicMock(text=json.dumps({
                "document_type": "utility_bill",
                "country_code": "US",
                "side": "single",
                "confidence": 82,
                "detected_fields": ["address", "name", "date"],
            }))
        ]

        with patch.object(classifier, '_get_client') as mock_get_client:
            mock_client = AsyncMock()
            mock_client.messages.create = AsyncMock(return_value=mock_response)
            mock_get_client.return_value = mock_client

            result = await classifier.classify(mock_image_bytes)

            assert result.document_type == DocumentType.UTILITY_BILL
            assert result.is_identity_document is False
            assert result.suggested_ocr_template == "proof_of_address"

    async def test_classify_selfie(self, classifier, mock_jpeg_bytes):
        """Test classifying a selfie image."""
        mock_response = MagicMock()
        mock_response.content = [
            MagicMock(text=json.dumps({
                "document_type": "selfie",
                "country_code": None,
                "side": "single",
                "confidence": 98,
                "detected_fields": ["face"],
            }))
        ]

        with patch.object(classifier, '_get_client') as mock_get_client:
            mock_client = AsyncMock()
            mock_client.messages.create = AsyncMock(return_value=mock_response)
            mock_get_client.return_value = mock_client

            result = await classifier.classify(mock_jpeg_bytes)

            assert result.document_type == DocumentType.SELFIE
            assert result.is_identity_document is False

    async def test_classify_api_error(self, classifier, mock_image_bytes):
        """Test handling API errors gracefully."""
        import anthropic

        with patch.object(classifier, '_get_client') as mock_get_client:
            mock_client = AsyncMock()
            mock_client.messages.create = AsyncMock(
                side_effect=anthropic.APIError(
                    message="Test error",
                    request=MagicMock(),
                    body=None,
                )
            )
            mock_get_client.return_value = mock_client

            result = await classifier.classify(mock_image_bytes)

            assert result.document_type == DocumentType.UNKNOWN
            assert result.confidence == 0.0
            assert result.error_message is not None
            assert "API error" in result.error_message

    async def test_classify_unconfigured(self, mock_image_bytes):
        """Test classification returns fallback when not configured."""
        classifier = DocumentClassifier(api_key=None)
        classifier.api_key = ""  # Explicitly unset

        result = await classifier.classify(mock_image_bytes)

        assert result.document_type == DocumentType.ID_CARD
        assert result.confidence == 30.0
        assert "Fallback" in result.error_message


# ===========================================
# CONVENIENCE FUNCTION TESTS
# ===========================================

class TestConvenienceFunctions:
    """Tests for module-level convenience functions."""

    def test_get_ocr_template_passport(self):
        """Test get_ocr_template for passport."""
        template = get_ocr_template("passport", "US")
        assert template == "us_passport"

    def test_get_ocr_template_default(self):
        """Test get_ocr_template with no country."""
        template = get_ocr_template("passport", None)
        assert template == "mrz_passport"

    def test_get_ocr_template_invalid_type(self):
        """Test get_ocr_template with invalid type."""
        template = get_ocr_template("invalid_type", "US")
        assert template == "generic_id"


# ===========================================
# OCR TEMPLATES COVERAGE
# ===========================================

class TestOCRTemplates:
    """Tests for OCR template mappings."""

    def test_passport_templates_exist(self):
        """Test passport templates are defined."""
        assert "passport" in OCR_TEMPLATES
        assert "default" in OCR_TEMPLATES["passport"]
        assert OCR_TEMPLATES["passport"]["default"] == "mrz_passport"

    def test_drivers_license_templates(self):
        """Test driver's license templates."""
        assert "drivers_license" in OCR_TEMPLATES
        assert "US" in OCR_TEMPLATES["drivers_license"]
        assert "GB" in OCR_TEMPLATES["drivers_license"]

    def test_id_card_templates(self):
        """Test ID card templates."""
        assert "id_card" in OCR_TEMPLATES
        assert "DE" in OCR_TEMPLATES["id_card"]

    def test_proof_of_address_templates(self):
        """Test proof of address templates."""
        assert "utility_bill" in OCR_TEMPLATES
        assert "bank_statement" in OCR_TEMPLATES


# ===========================================
# DOCUMENT TYPE ENUM TESTS
# ===========================================

class TestDocumentType:
    """Tests for DocumentType enum."""

    def test_passport_value(self):
        """Test passport enum value."""
        assert DocumentType.PASSPORT.value == "passport"

    def test_drivers_license_value(self):
        """Test driver's license enum value."""
        assert DocumentType.DRIVERS_LICENSE.value == "drivers_license"

    def test_from_string(self):
        """Test creating DocumentType from string."""
        doc_type = DocumentType("passport")
        assert doc_type == DocumentType.PASSPORT

    def test_invalid_string(self):
        """Test invalid string raises ValueError."""
        with pytest.raises(ValueError):
            DocumentType("invalid_type")


class TestDocumentSide:
    """Tests for DocumentSide enum."""

    def test_front_value(self):
        """Test front side value."""
        assert DocumentSide.FRONT.value == "front"

    def test_back_value(self):
        """Test back side value."""
        assert DocumentSide.BACK.value == "back"

    def test_single_value(self):
        """Test single side value (for passports)."""
        assert DocumentSide.SINGLE.value == "single"
