"""
Get Clearance - Screening Service Tests
========================================
Unit tests for AML/Sanctions/PEP screening service.

Tests:
- OpenSanctions API integration
- Fuzzy matching confidence scoring
- Hit type classification (sanctions, PEP, adverse media)
- Error handling (timeouts, rate limits)
- List version tracking
"""

import pytest
from datetime import date
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import httpx

from app.services.screening import (
    ScreeningService,
    ScreeningResult,
    ScreeningHitResult,
    ScreeningServiceError,
    ScreeningConfigError,
    OpenSanctionsAPIError,
)


# ===========================================
# SCREENING SERVICE INITIALIZATION
# ===========================================

class TestScreeningServiceInit:
    """Test screening service initialization and configuration."""

    def test_is_configured_with_api_key(self):
        """Service is configured when API key is provided."""
        service = ScreeningService(
            api_key="test-key",
            api_url="https://api.opensanctions.org/match/default"
        )
        assert service.is_configured is True

    def test_is_not_configured_without_api_key(self):
        """Service is not configured without API key."""
        service = ScreeningService(api_key="", api_url="")
        assert service.is_configured is False

    def test_default_timeout(self):
        """Service has sensible default timeout."""
        service = ScreeningService(api_key="test", api_url="test")
        assert service.timeout == 30.0

    def test_custom_timeout(self):
        """Service accepts custom timeout."""
        service = ScreeningService(api_key="test", api_url="test", timeout=60.0)
        assert service.timeout == 60.0


# ===========================================
# MATCH QUERY BUILDING
# ===========================================

class TestMatchQueryBuilding:
    """Test query construction for OpenSanctions API."""

    def test_build_basic_query(self, screening_service):
        """Build basic query with name only."""
        query = screening_service._build_match_query(
            schema="Person",
            name="John Doe",
        )

        assert "queries" in query
        assert "q1" in query["queries"]
        assert query["queries"]["q1"]["schema"] == "Person"
        assert query["queries"]["q1"]["properties"]["name"] == ["John Doe"]

    def test_build_query_with_dob(self, screening_service):
        """Build query with date of birth."""
        query = screening_service._build_match_query(
            schema="Person",
            name="John Doe",
            birth_date=date(1990, 1, 15),
        )

        assert query["queries"]["q1"]["properties"]["birthDate"] == ["1990-01-15"]

    def test_build_query_with_countries(self, screening_service):
        """Build query with country codes."""
        query = screening_service._build_match_query(
            schema="Person",
            name="John Doe",
            countries=["US", "GB"],
        )

        assert query["queries"]["q1"]["properties"]["country"] == ["US", "GB"]
        assert query["queries"]["q1"]["properties"]["nationality"] == ["US", "GB"]

    def test_build_query_with_identifiers(self, screening_service):
        """Build query with passport and ID numbers."""
        query = screening_service._build_match_query(
            schema="Person",
            name="John Doe",
            identifiers={
                "passport": "ABC123456",
                "national_id": "123-45-6789",
                "tax_id": "TAX12345",
            },
        )

        props = query["queries"]["q1"]["properties"]
        assert props["passportNumber"] == ["ABC123456"]
        assert props["idNumber"] == ["123-45-6789"]
        assert props["taxNumber"] == ["TAX12345"]

    def test_build_company_query(self, screening_service):
        """Build query for company screening."""
        query = screening_service._build_match_query(
            schema="Company",
            name="Acme Corp",
            countries=["US"],
        )

        assert query["queries"]["q1"]["schema"] == "Company"
        assert query["queries"]["q1"]["properties"]["name"] == ["Acme Corp"]


# ===========================================
# RESPONSE PARSING
# ===========================================

class TestResponseParsing:
    """Test parsing of OpenSanctions API responses."""

    def test_parse_sanctions_hit(self, screening_service, mock_opensanctions_response):
        """Parse response with sanctions hit."""
        hits = screening_service._parse_match_response(
            mock_opensanctions_response,
            list_version_id="OS-2024-01-01"
        )

        assert len(hits) == 1
        hit = hits[0]
        assert hit.hit_type == "sanctions"
        assert hit.matched_entity_id == "nk-abc123"
        assert hit.matched_name == "John Doe"
        assert hit.confidence == 95.0  # 0.95 * 100
        assert hit.list_source == "us_ofac_sdn"
        assert hit.list_version_id == "OS-2024-01-01"

    def test_parse_pep_hit(self, screening_service, mock_opensanctions_pep):
        """Parse response with PEP hit."""
        hits = screening_service._parse_match_response(
            mock_opensanctions_pep,
            list_version_id="OS-2024-01-01"
        )

        assert len(hits) == 1
        hit = hits[0]
        assert hit.hit_type == "pep"
        assert hit.pep_tier == 1  # National level = Tier 1
        assert hit.pep_position == "Minister of Finance"
        assert "pep" in hit.categories

    def test_parse_empty_response(self, screening_service, mock_opensanctions_clear):
        """Parse response with no hits."""
        hits = screening_service._parse_match_response(
            mock_opensanctions_clear,
            list_version_id="OS-2024-01-01"
        )

        assert len(hits) == 0

    def test_parse_matched_fields(self, screening_service):
        """Extract matched fields from hit."""
        properties = {
            "name": ["John Doe"],
            "birthDate": ["1990-01-15"],
            "nationality": ["US"],
        }

        matched = screening_service._extract_matched_fields(properties)

        assert "name" in matched
        assert "date_of_birth" in matched
        assert "nationality" in matched


# ===========================================
# HIT TYPE CLASSIFICATION
# ===========================================

class TestHitTypeClassification:
    """Test classification of hit types."""

    def test_classify_ofac_sanctions(self, screening_service):
        """OFAC dataset classified as sanctions."""
        hit_type = screening_service._determine_hit_type(
            datasets=["us_ofac_sdn"],
            topics=[]
        )
        assert hit_type == "sanctions"

    def test_classify_eu_sanctions(self, screening_service):
        """EU sanctions list classified as sanctions."""
        hit_type = screening_service._determine_hit_type(
            datasets=["eu_fsf"],
            topics=[]
        )
        assert hit_type == "sanctions"

    def test_classify_un_sanctions(self, screening_service):
        """UN Security Council list classified as sanctions."""
        hit_type = screening_service._determine_hit_type(
            datasets=["un_sc_sanctions"],
            topics=[]
        )
        assert hit_type == "sanctions"

    def test_classify_pep_from_topics(self, screening_service):
        """PEP classification from topics."""
        hit_type = screening_service._determine_hit_type(
            datasets=["everypolitician"],
            topics=["role.pep.national"]
        )
        assert hit_type == "pep"

    def test_classify_adverse_media(self, screening_service):
        """Crime indicators classified as adverse media."""
        hit_type = screening_service._determine_hit_type(
            datasets=["interpol_wanted"],
            topics=["crime"]
        )
        assert hit_type == "adverse_media"


# ===========================================
# PEP TIER CLASSIFICATION
# ===========================================

class TestPEPTierClassification:
    """Test PEP tier assignment."""

    def test_tier1_national(self, screening_service):
        """National level PEPs are Tier 1."""
        tier = screening_service._get_pep_tier(["role.pep.national"])
        assert tier == 1

    def test_tier1_head(self, screening_service):
        """Head of state PEPs are Tier 1."""
        tier = screening_service._get_pep_tier(["role.pep.head"])
        assert tier == 1

    def test_tier2_regional(self, screening_service):
        """Regional level PEPs are Tier 2."""
        tier = screening_service._get_pep_tier(["role.pep.regional"])
        assert tier == 2

    def test_tier2_ministry(self, screening_service):
        """Ministry level PEPs are Tier 2."""
        tier = screening_service._get_pep_tier(["role.pep.ministry"])
        assert tier == 2

    def test_tier3_local(self, screening_service):
        """Local level PEPs are Tier 3."""
        tier = screening_service._get_pep_tier(["role.pep.local"])
        assert tier == 3

    def test_default_tier2(self, screening_service):
        """Generic PEP defaults to Tier 2."""
        tier = screening_service._get_pep_tier(["role.pep"])
        assert tier == 2

    def test_no_tier_for_non_pep(self, screening_service):
        """Non-PEP returns None."""
        tier = screening_service._get_pep_tier(["sanction"])
        assert tier is None


# ===========================================
# CATEGORY EXTRACTION
# ===========================================

class TestCategoryExtraction:
    """Test extraction of hit categories."""

    def test_extract_financial_crime(self, screening_service):
        """Extract financial crime category."""
        categories = screening_service._extract_categories(["crime.fin"])
        assert "financial_crime" in categories

    def test_extract_fraud(self, screening_service):
        """Extract fraud category."""
        categories = screening_service._extract_categories(["crime.fraud"])
        assert "fraud" in categories

    def test_extract_terrorism(self, screening_service):
        """Extract terrorism category."""
        categories = screening_service._extract_categories(["crime.terror"])
        assert "terrorism" in categories

    def test_extract_multiple_categories(self, screening_service):
        """Extract multiple categories."""
        categories = screening_service._extract_categories([
            "crime.fin",
            "crime.fraud",
            "role.pep",
        ])
        assert "financial_crime" in categories
        assert "fraud" in categories
        assert "pep" in categories

    def test_no_duplicate_categories(self, screening_service):
        """Categories are deduplicated."""
        categories = screening_service._extract_categories([
            "crime.fin.fraud",  # Contains both patterns
            "crime.fin",
            "crime.fraud",
        ])
        assert categories.count("financial_crime") == 1


# ===========================================
# PRIMARY SOURCE SELECTION
# ===========================================

class TestPrimarySourceSelection:
    """Test selection of primary/authoritative source."""

    def test_ofac_highest_priority(self, screening_service):
        """OFAC is highest priority source."""
        source = screening_service._get_primary_source([
            "opensanctions",
            "us_ofac_sdn",
            "eu_fsf",
        ])
        assert source == "us_ofac_sdn"

    def test_eu_second_priority(self, screening_service):
        """EU is second priority after OFAC."""
        source = screening_service._get_primary_source([
            "opensanctions",
            "eu_fsf",
            "gb_hmt_sanctions",
        ])
        assert source == "eu_fsf"

    def test_fallback_to_first(self, screening_service):
        """Fallback to first dataset if no priority match."""
        source = screening_service._get_primary_source([
            "some_other_list",
            "another_list",
        ])
        assert source == "some_other_list"

    def test_empty_defaults_to_opensanctions(self, screening_service):
        """Empty list defaults to opensanctions."""
        source = screening_service._get_primary_source([])
        assert source == "opensanctions"


# ===========================================
# INDIVIDUAL SCREENING
# ===========================================

class TestIndividualScreening:
    """Test individual screening workflow."""

    @pytest.mark.asyncio
    async def test_check_individual_with_hit(self, mock_opensanctions):
        """Individual screening with hit result."""
        service = ScreeningService(
            api_key="test-key",
            api_url="https://api.opensanctions.org/match/default"
        )

        # Create a proper mock
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.headers = {"X-OpenSanctions-Version": "2024-01-01"}
        mock_response.json.return_value = {
            "responses": {
                "q1": {
                    "results": [
                        {
                            "id": "hit-123",
                            "caption": "John Doe",
                            "score": 0.9,
                            "datasets": ["us_ofac_sdn"],
                            "properties": {
                                "name": ["John Doe"],
                                "topics": ["sanction"],
                            },
                        }
                    ]
                }
            }
        }

        with patch.object(service, '_get_client') as mock_get_client:
            mock_client = AsyncMock()
            mock_client.post = AsyncMock(return_value=mock_response)
            mock_get_client.return_value = mock_client

            result = await service.check_individual(
                name="John Doe",
                birth_date=date(1990, 1, 15),
            )

        assert result.status == "hit"
        assert len(result.hits) == 1
        assert result.hits[0].hit_type == "sanctions"

    @pytest.mark.asyncio
    async def test_check_individual_clear(self):
        """Individual screening with clear result."""
        service = ScreeningService(
            api_key="test-key",
            api_url="https://api.opensanctions.org/match/default"
        )

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.headers = {}
        mock_response.json.return_value = {
            "responses": {"q1": {"results": []}}
        }

        with patch.object(service, '_get_client') as mock_get_client:
            mock_client = AsyncMock()
            mock_client.post = AsyncMock(return_value=mock_response)
            mock_get_client.return_value = mock_client

            result = await service.check_individual(name="Jane Smith")

        assert result.status == "clear"
        assert len(result.hits) == 0

    @pytest.mark.asyncio
    async def test_check_individual_not_configured(self):
        """Screening fails when not configured."""
        service = ScreeningService(api_key="", api_url="")

        with pytest.raises(ScreeningConfigError) as exc_info:
            await service.check_individual(name="Test")

        assert "not configured" in str(exc_info.value)


# ===========================================
# COMPANY SCREENING
# ===========================================

class TestCompanyScreening:
    """Test company screening workflow."""

    @pytest.mark.asyncio
    async def test_check_company_with_hit(self):
        """Company screening with hit result."""
        service = ScreeningService(
            api_key="test-key",
            api_url="https://api.opensanctions.org/match/default"
        )

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.headers = {}
        mock_response.json.return_value = {
            "responses": {
                "q1": {
                    "results": [
                        {
                            "id": "company-123",
                            "caption": "Evil Corp",
                            "score": 0.85,
                            "datasets": ["eu_fsf"],
                            "properties": {
                                "name": ["Evil Corporation"],
                                "topics": ["sanction"],
                            },
                        }
                    ]
                }
            }
        }

        with patch.object(service, '_get_client') as mock_get_client:
            mock_client = AsyncMock()
            mock_client.post = AsyncMock(return_value=mock_response)
            mock_get_client.return_value = mock_client

            result = await service.check_company(
                name="Evil Corp",
                jurisdiction="US",
            )

        assert result.status == "hit"
        assert len(result.hits) == 1


# ===========================================
# ERROR HANDLING
# ===========================================

class TestErrorHandling:
    """Test error handling for various failure modes."""

    @pytest.mark.asyncio
    async def test_handle_401_unauthorized(self):
        """Handle invalid API key error."""
        service = ScreeningService(
            api_key="invalid-key",
            api_url="https://api.opensanctions.org/match/default"
        )

        mock_response = MagicMock()
        mock_response.status_code = 401
        mock_response.text = "Unauthorized"

        with patch.object(service, '_get_client') as mock_get_client:
            mock_client = AsyncMock()
            mock_client.post = AsyncMock(return_value=mock_response)
            mock_get_client.return_value = mock_client

            with pytest.raises(OpenSanctionsAPIError) as exc_info:
                await service.check_individual(name="Test")

            assert exc_info.value.status_code == 401
            assert "Invalid API key" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_handle_429_rate_limit(self):
        """Handle rate limit error."""
        service = ScreeningService(
            api_key="test-key",
            api_url="https://api.opensanctions.org/match/default"
        )

        mock_response = MagicMock()
        mock_response.status_code = 429
        mock_response.text = "Rate limit exceeded"

        with patch.object(service, '_get_client') as mock_get_client:
            mock_client = AsyncMock()
            mock_client.post = AsyncMock(return_value=mock_response)
            mock_get_client.return_value = mock_client

            with pytest.raises(OpenSanctionsAPIError) as exc_info:
                await service.check_individual(name="Test")

            assert exc_info.value.status_code == 429

    @pytest.mark.asyncio
    async def test_handle_timeout(self):
        """Handle request timeout gracefully."""
        service = ScreeningService(
            api_key="test-key",
            api_url="https://api.opensanctions.org/match/default",
            timeout=1.0,
        )

        with patch.object(service, '_get_client') as mock_get_client:
            mock_client = AsyncMock()
            mock_client.post = AsyncMock(side_effect=httpx.TimeoutException("Timeout"))
            mock_get_client.return_value = mock_client

            result = await service.check_individual(name="Test")

        assert result.status == "error"
        assert "timed out" in result.error_message

    @pytest.mark.asyncio
    async def test_handle_connection_error(self):
        """Handle connection error gracefully."""
        service = ScreeningService(
            api_key="test-key",
            api_url="https://api.opensanctions.org/match/default"
        )

        with patch.object(service, '_get_client') as mock_get_client:
            mock_client = AsyncMock()
            mock_client.post = AsyncMock(
                side_effect=httpx.RequestError("Connection failed")
            )
            mock_get_client.return_value = mock_client

            result = await service.check_individual(name="Test")

        assert result.status == "error"
        assert result.error_message is not None


# ===========================================
# LIST VERSION TRACKING
# ===========================================

class TestListVersionTracking:
    """Test list version extraction and tracking."""

    def test_extract_version_from_header(self, screening_service):
        """Extract version from X-OpenSanctions-Version header."""
        mock_response = MagicMock()
        mock_response.headers = {"X-OpenSanctions-Version": "2024-01-15"}

        version = screening_service._get_list_version(mock_response, {})

        assert version == "OS-2024-01-15"

    def test_fallback_to_current_date(self, screening_service):
        """Fallback to current date when header missing."""
        mock_response = MagicMock()
        mock_response.headers = {}

        version = screening_service._get_list_version(mock_response, {"datasets": []})

        assert version.startswith("OS-")
        # Should be today's date in YYYY-MM-DD format
        import re
        assert re.match(r"OS-\d{4}-\d{2}-\d{2}", version)


# ===========================================
# CONFIDENCE SCORE VALIDATION
# ===========================================

class TestConfidenceScoring:
    """Test confidence score calculation and validation."""

    def test_confidence_scaled_to_percentage(self, screening_service, mock_opensanctions_response):
        """Confidence score is scaled from 0-1 to 0-100."""
        hits = screening_service._parse_match_response(
            mock_opensanctions_response,
            list_version_id="OS-2024-01-01"
        )

        # Original score is 0.95, should become 95.0
        assert hits[0].confidence == 95.0

    def test_confidence_rounded(self, screening_service):
        """Confidence score is rounded to 2 decimal places."""
        response = {
            "responses": {
                "q1": {
                    "results": [
                        {
                            "id": "test",
                            "caption": "Test",
                            "score": 0.8567,
                            "datasets": ["us_ofac_sdn"],
                            "properties": {"name": ["Test"], "topics": []},
                        }
                    ]
                }
            }
        }

        hits = screening_service._parse_match_response(response, "OS-test")

        assert hits[0].confidence == 85.67


# ===========================================
# INTEGRATION-LIKE TESTS
# ===========================================

class TestScreeningWorkflow:
    """Test complete screening workflows."""

    @pytest.mark.asyncio
    async def test_full_screening_workflow_with_hit(self):
        """Test complete workflow: query -> parse -> result."""
        service = ScreeningService(
            api_key="test-key",
            api_url="https://api.opensanctions.org/match/default"
        )

        # Simulate full API response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.headers = {"X-OpenSanctions-Version": "2024-01-15"}
        mock_response.json.return_value = {
            "responses": {
                "q1": {
                    "results": [
                        {
                            "id": "ofac-12345",
                            "caption": "John Doe",
                            "score": 0.92,
                            "datasets": ["us_ofac_sdn", "opensanctions"],
                            "properties": {
                                "name": ["John Doe", "Johnny Doe"],
                                "birthDate": ["1990-01-15"],
                                "nationality": ["us"],
                                "topics": ["sanction", "crime.fin"],
                            },
                        }
                    ]
                }
            }
        }

        with patch.object(service, '_get_client') as mock_get_client:
            mock_client = AsyncMock()
            mock_client.post = AsyncMock(return_value=mock_response)
            mock_get_client.return_value = mock_client

            result = await service.check_individual(
                name="John Doe",
                birth_date=date(1990, 1, 15),
                countries=["US"],
            )

        # Validate complete result
        assert result.status == "hit"
        assert result.list_version_id == "OS-2024-01-15"
        assert len(result.hits) == 1

        hit = result.hits[0]
        assert hit.matched_entity_id == "ofac-12345"
        assert hit.matched_name == "John Doe"
        assert hit.confidence == 92.0
        assert hit.hit_type == "sanctions"
        assert hit.list_source == "us_ofac_sdn"
        assert "financial_crime" in hit.categories
        assert "name" in hit.matched_fields
        assert "date_of_birth" in hit.matched_fields
