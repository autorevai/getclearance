"""
Get Clearance - Screening Service
==================================
OpenSanctions API integration for AML/Sanctions/PEP screening.

API Documentation: https://api.opensanctions.org/
"""

import logging
from dataclasses import dataclass, field
from datetime import date, datetime
from typing import Any
from uuid import UUID

import httpx

from app.config import settings

logger = logging.getLogger(__name__)


# ===========================================
# DATA CLASSES
# ===========================================

@dataclass
class ScreeningHitResult:
    """Result from screening match."""
    hit_type: str  # sanctions, pep, adverse_media
    matched_entity_id: str
    matched_name: str
    confidence: float  # 0-100
    matched_fields: list[str]
    list_source: str
    list_version_id: str
    match_data: dict[str, Any]
    # PEP-specific
    pep_tier: int | None = None
    pep_position: str | None = None
    pep_relationship: str | None = None
    # Adverse media
    article_url: str | None = None
    article_title: str | None = None
    article_date: date | None = None
    categories: list[str] = field(default_factory=list)


@dataclass
class ScreeningResult:
    """Complete screening result."""
    status: str  # clear, hit, error
    list_version_id: str
    hits: list[ScreeningHitResult]
    error_message: str | None = None
    checked_at: datetime = field(default_factory=datetime.utcnow)


class ScreeningServiceError(Exception):
    """Base exception for screening service errors."""
    pass


class OpenSanctionsAPIError(ScreeningServiceError):
    """OpenSanctions API returned an error."""
    def __init__(self, status_code: int, message: str):
        self.status_code = status_code
        self.message = message
        super().__init__(f"OpenSanctions API error ({status_code}): {message}")


class ScreeningConfigError(ScreeningServiceError):
    """Configuration error (e.g., missing API key)."""
    pass


# ===========================================
# SCREENING SERVICE
# ===========================================

class ScreeningService:
    """
    Service for AML/Sanctions/PEP screening via OpenSanctions.
    
    OpenSanctions provides a unified API across multiple sanctions lists:
    - OFAC SDN (US)
    - EU Consolidated List
    - UN Security Council
    - UK Sanctions
    - Plus PEP and adverse media databases
    
    Usage:
        result = await screening_service.check_individual(
            name="John Smith",
            birth_date=date(1980, 1, 15),
            countries=["US", "GB"]
        )
        
        if result.status == "hit":
            for hit in result.hits:
                print(f"Match: {hit.matched_name} ({hit.confidence}%)")
    """
    
    def __init__(
        self,
        api_key: str | None = None,
        api_url: str | None = None,
        timeout: float = 30.0,
    ):
        self.api_key = api_key or settings.opensanctions_api_key
        self.api_url = api_url or settings.opensanctions_api_url
        self.timeout = timeout
        self._client: httpx.AsyncClient | None = None
    
    @property
    def is_configured(self) -> bool:
        """Check if service is properly configured."""
        return bool(self.api_key and self.api_url)
    
    async def _get_client(self) -> httpx.AsyncClient:
        """Get or create HTTP client."""
        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient(
                timeout=self.timeout,
                headers={
                    "Authorization": f"ApiKey {self.api_key}",
                    "Content-Type": "application/json",
                    "Accept": "application/json",
                },
            )
        return self._client
    
    async def close(self) -> None:
        """Close HTTP client."""
        if self._client and not self._client.is_closed:
            await self._client.aclose()
            self._client = None
    
    def _build_match_query(
        self,
        schema: str,  # Person, Company, LegalEntity
        name: str,
        birth_date: date | None = None,
        countries: list[str] | None = None,
        identifiers: dict[str, str] | None = None,
    ) -> dict[str, Any]:
        """
        Build query payload for OpenSanctions /match endpoint.
        
        See: https://api.opensanctions.org/docs#/Matching/match_default_match_default_post
        """
        properties: dict[str, list[Any]] = {
            "name": [name],
        }
        
        if birth_date:
            properties["birthDate"] = [birth_date.isoformat()]
        
        if countries:
            properties["country"] = countries
            properties["nationality"] = countries
        
        if identifiers:
            for id_type, id_value in identifiers.items():
                if id_type == "passport":
                    properties["passportNumber"] = [id_value]
                elif id_type == "national_id":
                    properties["idNumber"] = [id_value]
                elif id_type == "tax_id":
                    properties["taxNumber"] = [id_value]
        
        return {
            "queries": {
                "q1": {
                    "schema": schema,
                    "properties": properties,
                }
            }
        }
    
    def _parse_match_response(
        self,
        response_data: dict[str, Any],
        list_version_id: str,
    ) -> list[ScreeningHitResult]:
        """Parse OpenSanctions match response into hits."""
        hits: list[ScreeningHitResult] = []
        
        # Response structure: {"responses": {"q1": {"query": {...}, "results": [...]}}}
        responses = response_data.get("responses", {})
        q1_response = responses.get("q1", {})
        results = q1_response.get("results", [])
        
        for result in results:
            # Extract score (0-1) and convert to percentage
            score = result.get("score", 0) * 100
            
            # Get matched entity properties
            properties = result.get("properties", {})
            
            # Determine hit type from datasets and topics
            datasets = result.get("datasets", [])
            topics = properties.get("topics", [])
            
            hit_type = self._determine_hit_type(datasets, topics)
            
            # Extract matched fields
            matched_fields = self._extract_matched_fields(properties)
            
            # Get the best name match
            names = properties.get("name", [])
            matched_name = names[0] if names else result.get("caption", "Unknown")
            
            # Create hit result
            hit = ScreeningHitResult(
                hit_type=hit_type,
                matched_entity_id=result.get("id", ""),
                matched_name=matched_name,
                confidence=round(score, 2),
                matched_fields=matched_fields,
                list_source=self._get_primary_source(datasets),
                list_version_id=list_version_id,
                match_data=result,
            )
            
            # Add PEP-specific fields
            if hit_type == "pep":
                hit.pep_tier = self._get_pep_tier(topics)
                positions = properties.get("position", [])
                hit.pep_position = positions[0] if positions else None
            
            # Add categories
            hit.categories = self._extract_categories(topics)
            
            hits.append(hit)
        
        return hits
    
    def _determine_hit_type(
        self,
        datasets: list[str],
        topics: list[str],
    ) -> str:
        """Determine the type of hit based on datasets and topics."""
        # Check for sanctions lists
        sanctions_indicators = [
            "ofac", "sdn", "eu_fsf", "un_sc", "uk_hmt", "sanctions"
        ]
        for ds in datasets:
            if any(ind in ds.lower() for ind in sanctions_indicators):
                return "sanctions"
        
        # Check for PEP
        if any("pep" in topic.lower() for topic in topics):
            return "pep"
        
        if any("role.pep" in topic.lower() for topic in topics):
            return "pep"
        
        # Check for crime/adverse media
        crime_indicators = ["crime", "wanted", "interpol"]
        if any(ind in str(datasets).lower() for ind in crime_indicators):
            return "adverse_media"
        
        # Default to sanctions if in any sanctions list
        return "sanctions"
    
    def _get_primary_source(self, datasets: list[str]) -> str:
        """Get the primary/most authoritative source from datasets."""
        # Priority order for sources
        priority = [
            "us_ofac_sdn",
            "eu_fsf",
            "un_sc_sanctions",
            "gb_hmt_sanctions",
            "opensanctions",
        ]
        
        for source in priority:
            if source in datasets:
                return source
        
        return datasets[0] if datasets else "opensanctions"
    
    def _extract_matched_fields(self, properties: dict[str, Any]) -> list[str]:
        """Extract which fields matched in the result."""
        matched = []
        
        field_mapping = {
            "name": "name",
            "alias": "name",
            "birthDate": "date_of_birth",
            "birthPlace": "birth_place",
            "country": "country",
            "nationality": "nationality",
            "passportNumber": "passport",
            "idNumber": "national_id",
            "address": "address",
        }
        
        for prop_key, field_name in field_mapping.items():
            if prop_key in properties and properties[prop_key]:
                if field_name not in matched:
                    matched.append(field_name)
        
        return matched
    
    def _get_pep_tier(self, topics: list[str]) -> int | None:
        """Determine PEP tier from topics."""
        # OpenSanctions uses role.pep.national, role.pep.local, etc.
        for topic in topics:
            topic_lower = topic.lower()
            if "role.pep" in topic_lower:
                if "national" in topic_lower or "head" in topic_lower:
                    return 1
                elif "regional" in topic_lower or "ministry" in topic_lower:
                    return 2
                elif "local" in topic_lower:
                    return 3
                else:
                    return 2  # Default to tier 2 for generic PEP
        return None
    
    def _extract_categories(self, topics: list[str]) -> list[str]:
        """Extract relevant categories from topics."""
        category_mapping = {
            "crime.fin": "financial_crime",
            "crime.fraud": "fraud",
            "crime.terror": "terrorism",
            "crime.theft": "theft",
            "crime.cyber": "cybercrime",
            "crime.traffic": "trafficking",
            "crime.war": "war_crimes",
            "sanction": "sanctions",
            "role.pep": "pep",
            "role.rca": "relative_close_associate",
        }
        
        categories = []
        for topic in topics:
            for pattern, category in category_mapping.items():
                if pattern in topic.lower() and category not in categories:
                    categories.append(category)
        
        return categories
    
    async def check_individual(
        self,
        name: str,
        birth_date: date | None = None,
        countries: list[str] | None = None,
        identifiers: dict[str, str] | None = None,
        threshold: float = 0.5,
    ) -> ScreeningResult:
        """
        Screen an individual against sanctions and PEP lists.
        
        Args:
            name: Full name to screen
            birth_date: Date of birth for better matching
            countries: List of country codes (ISO 3166-1 alpha-2)
            identifiers: Dict of identifier types to values
            threshold: Minimum score threshold (0-1), default 0.5
            
        Returns:
            ScreeningResult with status and any hits
            
        Raises:
            ScreeningConfigError: If API key is not configured
            OpenSanctionsAPIError: If API returns an error
        """
        if not self.is_configured:
            logger.warning("OpenSanctions not configured, returning mock result")
            raise ScreeningConfigError("OpenSanctions API key not configured")
        
        # Build query
        query = self._build_match_query(
            schema="Person",
            name=name,
            birth_date=birth_date,
            countries=countries,
            identifiers=identifiers,
        )
        
        logger.info(f"Screening individual: {name}")
        
        try:
            client = await self._get_client()
            
            response = await client.post(
                self.api_url,
                json=query,
                params={"threshold": threshold},
            )
            
            if response.status_code == 401:
                raise OpenSanctionsAPIError(401, "Invalid API key")
            elif response.status_code == 429:
                raise OpenSanctionsAPIError(429, "Rate limit exceeded")
            elif response.status_code != 200:
                raise OpenSanctionsAPIError(
                    response.status_code,
                    response.text[:200]
                )
            
            data = response.json()
            
            # Get list version from response headers or metadata
            list_version_id = self._get_list_version(response, data)
            
            # Parse hits
            hits = self._parse_match_response(data, list_version_id)
            
            # Determine overall status
            status = "hit" if hits else "clear"
            
            logger.info(
                f"Screening complete for {name}: "
                f"{status} ({len(hits)} hits)"
            )
            
            return ScreeningResult(
                status=status,
                list_version_id=list_version_id,
                hits=hits,
            )
            
        except httpx.TimeoutException:
            logger.error(f"Screening timeout for {name}")
            return ScreeningResult(
                status="error",
                list_version_id="",
                hits=[],
                error_message="Request timed out",
            )
        except httpx.RequestError as e:
            logger.error(f"Screening request error for {name}: {e}")
            return ScreeningResult(
                status="error",
                list_version_id="",
                hits=[],
                error_message=str(e),
            )
    
    async def check_company(
        self,
        name: str,
        jurisdiction: str | None = None,
        registration_number: str | None = None,
        threshold: float = 0.5,
    ) -> ScreeningResult:
        """
        Screen a company against sanctions lists.
        
        Args:
            name: Company name to screen
            jurisdiction: Country code for jurisdiction
            registration_number: Company registration number
            threshold: Minimum score threshold (0-1)
            
        Returns:
            ScreeningResult with status and any hits
        """
        if not self.is_configured:
            raise ScreeningConfigError("OpenSanctions API key not configured")
        
        # Build identifiers
        identifiers = {}
        if registration_number:
            identifiers["registration"] = registration_number
        
        countries = [jurisdiction] if jurisdiction else None
        
        # Build query for Organization/Company
        query = self._build_match_query(
            schema="Company",
            name=name,
            countries=countries,
            identifiers=identifiers,
        )
        
        logger.info(f"Screening company: {name}")
        
        try:
            client = await self._get_client()
            
            response = await client.post(
                self.api_url,
                json=query,
                params={"threshold": threshold},
            )
            
            if response.status_code != 200:
                raise OpenSanctionsAPIError(
                    response.status_code,
                    response.text[:200]
                )
            
            data = response.json()
            list_version_id = self._get_list_version(response, data)
            hits = self._parse_match_response(data, list_version_id)
            
            status = "hit" if hits else "clear"
            
            logger.info(
                f"Company screening complete for {name}: "
                f"{status} ({len(hits)} hits)"
            )
            
            return ScreeningResult(
                status=status,
                list_version_id=list_version_id,
                hits=hits,
            )
            
        except httpx.TimeoutException:
            logger.error(f"Company screening timeout for {name}")
            return ScreeningResult(
                status="error",
                list_version_id="",
                hits=[],
                error_message="Request timed out",
            )
        except httpx.RequestError as e:
            logger.error(f"Company screening request error: {e}")
            return ScreeningResult(
                status="error",
                list_version_id="",
                hits=[],
                error_message=str(e),
            )
    
    def _get_list_version(
        self,
        response: httpx.Response,
        data: dict[str, Any],
    ) -> str:
        """Extract list version from response."""
        # Try to get from response headers
        version = response.headers.get("X-OpenSanctions-Version")
        if version:
            return f"OS-{version}"
        
        # Try to get from response body
        # OpenSanctions includes dataset info in responses
        if "datasets" in data:
            # Use current date as version fallback
            return f"OS-{datetime.utcnow().strftime('%Y-%m-%d')}"
        
        return f"OS-{datetime.utcnow().strftime('%Y-%m-%d')}"
    
    async def get_entity_details(self, entity_id: str) -> dict[str, Any] | None:
        """
        Fetch full entity details from OpenSanctions.
        
        Useful for getting complete information after a hit.
        """
        if not self.is_configured:
            return None
        
        try:
            client = await self._get_client()
            
            # OpenSanctions entity endpoint
            url = f"https://api.opensanctions.org/entities/{entity_id}"
            
            response = await client.get(url)
            
            if response.status_code == 200:
                return response.json()
            elif response.status_code == 404:
                logger.warning(f"Entity not found: {entity_id}")
                return None
            else:
                logger.error(
                    f"Error fetching entity {entity_id}: "
                    f"{response.status_code}"
                )
                return None
                
        except httpx.RequestError as e:
            logger.error(f"Error fetching entity details: {e}")
            return None


# ===========================================
# SINGLETON INSTANCE
# ===========================================

screening_service = ScreeningService()
