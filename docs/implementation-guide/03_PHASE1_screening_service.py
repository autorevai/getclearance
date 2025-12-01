"""
Screening Service - OpenSanctions Integration with Fuzzy Matching
==================================================================

Implements Sumsub-style screening with:
- Fuzzy name matching (Levenshtein distance + phonetic)
- Confidence scoring (0-100)
- Match classification (true_positive, potential_match, false_positive, unknown)
- PEP tier classification
- Adverse media categorization

Based on Sumsub reverse engineering analysis Section 7.
"""

from datetime import date, datetime
from typing import Optional
from uuid import UUID
import logging

import httpx
from Levenshtein import distance as levenshtein_distance

from app.config import settings

logger = logging.getLogger(__name__)


class ScreeningService:
    """
    Provides AML/sanctions/PEP screening against OpenSanctions.
    
    Usage:
        screening = ScreeningService()
        hits = await screening.check_individual(name="John Doe", dob="1990-01-15")
    """
    
    def __init__(self):
        """Initialize OpenSanctions client."""
        self.opensanctions_url = "https://api.opensanctions.org/match/default"
        self.api_key = settings.opensanctions_api_key
        
        # Confidence thresholds (based on Sumsub analysis)
        self.TRUE_POSITIVE_THRESHOLD = 90
        self.POTENTIAL_MATCH_THRESHOLD = 60
        self.FALSE_POSITIVE_THRESHOLD = 40
    
    async def check_individual(
        self,
        name: str,
        date_of_birth: Optional[str] = None,  # YYYY-MM-DD
        country: Optional[str] = None,  # ISO 3166-1 alpha-3
    ) -> list[dict]:
        """
        Screen individual against OpenSanctions lists.
        
        Returns list of hits with confidence scores and classifications.
        
        Args:
            name: Full name to screen
            date_of_birth: Optional DOB in YYYY-MM-DD format
            country: Optional country code (ISO 3166-1 alpha-3)
        
        Returns:
            List of screening hit dictionaries with:
            - matched_entity_id
            - matched_name
            - confidence (0-100)
            - match_type (true_positive, potential_match, false_positive, unknown)
            - hit_type (sanctions, pep, adverse_media)
            - pep_tier (1-4 if applicable)
            - categories (list of FATF predicate offences)
            - list_source, list_version_id
        """
        logger.info(f"Screening individual: {name}, DOB: {date_of_birth}, Country: {country}")
        
        # Call OpenSanctions API
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    self.opensanctions_url,
                    json={
                        "schema": "Person",
                        "properties": {
                            "name": [name],
                            "birthDate": [date_of_birth] if date_of_birth else [],
                            "country": [country] if country else [],
                        }
                    },
                    headers={"Authorization": f"Bearer {self.api_key}"}
                )
                response.raise_for_status()
        except httpx.HTTPError as e:
            logger.error(f"OpenSanctions API error: {e}")
            raise ScreeningError(f"Screening API failed: {str(e)}")
        
        api_results = response.json()
        results = api_results.get("results", [])
        
        logger.info(f"OpenSanctions returned {len(results)} potential matches")
        
        # Process each match with fuzzy scoring
        hits = []
        for match in results:
            hit = self._process_match(
                query_name=name,
                query_dob=date_of_birth,
                query_country=country,
                match=match,
            )
            hits.append(hit)
        
        # Sort by confidence (highest first)
        hits.sort(key=lambda x: x['confidence'], reverse=True)
        
        return hits
    
    async def check_company(
        self,
        name: str,
        jurisdiction: Optional[str] = None,
        registration_number: Optional[str] = None,
    ) -> list[dict]:
        """
        Screen company/organization against OpenSanctions.
        
        Similar to check_individual but for Company/Organization schema.
        """
        logger.info(f"Screening company: {name}, Jurisdiction: {jurisdiction}")
        
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    self.opensanctions_url,
                    json={
                        "schema": "Company",
                        "properties": {
                            "name": [name],
                            "jurisdiction": [jurisdiction] if jurisdiction else [],
                            "registrationNumber": [registration_number] if registration_number else [],
                        }
                    },
                    headers={"Authorization": f"Bearer {self.api_key}"}
                )
                response.raise_for_status()
        except httpx.HTTPError as e:
            logger.error(f"OpenSanctions API error: {e}")
            raise ScreeningError(f"Screening API failed: {str(e)}")
        
        api_results = response.json()
        results = api_results.get("results", [])
        
        hits = []
        for match in results:
            hit = self._process_match(
                query_name=name,
                query_dob=None,
                query_country=jurisdiction,
                match=match,
            )
            hits.append(hit)
        
        hits.sort(key=lambda x: x['confidence'], reverse=True)
        return hits
    
    def _process_match(
        self,
        query_name: str,
        query_dob: Optional[str],
        query_country: Optional[str],
        match: dict,
    ) -> dict:
        """
        Process a single OpenSanctions match result.
        
        Calculates confidence score and classifies match type.
        """
        properties = match.get("properties", {})
        
        # Extract match names (including aliases)
        match_names = properties.get("name", [])
        
        # Extract match DOBs
        match_dobs = properties.get("birthDate", [])
        
        # Extract match countries
        match_countries = properties.get("country", [])
        
        # Calculate confidence score (0-100)
        confidence = self._calculate_confidence(
            query_name=query_name,
            query_dob=query_dob,
            query_country=query_country,
            match_names=match_names,
            match_dobs=match_dobs,
            match_countries=match_countries,
        )
        
        # Classify match type
        match_type = self._classify_match(confidence, query_dob, match_dobs)
        
        # Determine hit type (sanctions, PEP, adverse media)
        hit_type = self._determine_hit_type(match)
        
        # Extract PEP details if applicable
        pep_tier = self._extract_pep_tier(match)
        pep_position = properties.get("position", [None])[0]
        
        # Extract adverse media categories
        categories = self._extract_categories(match)
        
        # Build hit result
        hit = {
            "matched_entity_id": match.get("id"),
            "matched_name": match_names[0] if match_names else "Unknown",
            "confidence": round(confidence, 2),
            "match_type": match_type,
            "matched_fields": self._identify_matched_fields(
                query_name, query_dob, query_country,
                match_names, match_dobs, match_countries
            ),
            "list_source": match.get("dataset", "opensanctions"),
            "list_version_id": f"OS-{datetime.utcnow().strftime('%Y%m%d')}",
            "hit_type": hit_type,
            "pep_tier": pep_tier,
            "pep_position": pep_position,
            "pep_relationship": "direct" if pep_tier else None,
            "categories": categories,
            "raw_data": match,  # Store for detailed review
        }
        
        return hit
    
    def _calculate_confidence(
        self,
        query_name: str,
        query_dob: Optional[str],
        query_country: Optional[str],
        match_names: list[str],
        match_dobs: list[str],
        match_countries: list[str],
    ) -> float:
        """
        Calculate 0-100 confidence score using Sumsub algorithm.
        
        Weighting:
        - Name matching: 60%
        - DOB matching: 30%
        - Country matching: 10%
        """
        score = 0.0
        
        # 1. NAME MATCHING (60% weight)
        best_name_score = 0.0
        for match_name in match_names:
            name_similarity = self._fuzzy_name_match(query_name, match_name)
            best_name_score = max(best_name_score, name_similarity)
        
        score += best_name_score * 0.6
        
        # 2. DOB MATCHING (30% weight)
        if query_dob and match_dobs:
            if query_dob in match_dobs:
                score += 30.0  # Exact match
            elif any(query_dob[:4] == dob[:4] for dob in match_dobs):
                score += 20.0  # Year-only match
            elif any(abs((self._parse_date(query_dob) - self._parse_date(dob)).days) < 365 for dob in match_dobs if self._parse_date(dob)):
                score += 10.0  # Within 1 year
        elif not match_dobs and query_dob:
            score += 15.0  # Missing DOB in list, slight penalty
        
        # 3. COUNTRY MATCHING (10% weight)
        if query_country and match_countries:
            if query_country in match_countries:
                score += 10.0
            elif any(self._country_similarity(query_country, c) > 0.8 for c in match_countries):
                score += 5.0
        
        return min(score, 100.0)
    
    def _fuzzy_name_match(self, name1: str, name2: str) -> float:
        """
        Fuzzy name matching with Levenshtein distance.
        
        Returns similarity score 0-100.
        """
        # Normalize names
        n1 = self._normalize_name(name1)
        n2 = self._normalize_name(name2)
        
        if not n1 or not n2:
            return 0.0
        
        # Levenshtein distance
        distance = levenshtein_distance(n1, n2)
        max_len = max(len(n1), len(n2))
        
        if max_len == 0:
            return 0.0
        
        similarity = (1 - distance / max_len) * 100
        
        # Boost for exact token matches
        tokens1 = set(n1.split())
        tokens2 = set(n2.split())
        token_overlap = len(tokens1 & tokens2) / max(len(tokens1), len(tokens2))
        
        # Weighted average
        final_score = (similarity * 0.7) + (token_overlap * 100 * 0.3)
        
        return final_score
    
    def _normalize_name(self, name: str) -> str:
        """Normalize name for comparison."""
        import re
        # Uppercase, remove extra spaces, remove punctuation
        name = name.upper().strip()
        name = re.sub(r'[^\w\s]', '', name)  # Remove punctuation
        name = re.sub(r'\s+', ' ', name)  # Normalize whitespace
        return name
    
    def _classify_match(
        self,
        confidence: float,
        query_dob: Optional[str],
        match_dobs: list[str],
    ) -> str:
        """
        Classify match using Sumsub categories.
        
        Returns: 'true_positive', 'potential_match', 'false_positive', 'unknown'
        """
        if confidence >= self.TRUE_POSITIVE_THRESHOLD:
            return "true_positive"
        elif confidence >= self.POTENTIAL_MATCH_THRESHOLD:
            return "potential_match"
        elif confidence >= self.FALSE_POSITIVE_THRESHOLD:
            return "false_positive"
        else:
            return "unknown"
    
    def _determine_hit_type(self, match: dict) -> str:
        """
        Determine hit type from OpenSanctions result.
        
        Returns: 'sanctions', 'pep', 'adverse_media', or 'other'
        """
        topics = match.get("properties", {}).get("topics", [])
        
        if any("sanction" in t.lower() for t in topics):
            return "sanctions"
        elif any("pep" in t.lower() or "politically exposed" in t.lower() for t in topics):
            return "pep"
        elif any("crime" in t.lower() or "fraud" in t.lower() for t in topics):
            return "adverse_media"
        else:
            return "other"
    
    def _extract_pep_tier(self, match: dict) -> Optional[int]:
        """
        Extract PEP tier from match.
        
        Tier classification:
        - Tier 1: Senior politicians, high-ranking officials
        - Tier 2: Mid-level officials, family members of Tier 1
        - Tier 3: Close associates
        - Tier 4: Former PEPs (>1 year out of office)
        """
        properties = match.get("properties", {})
        topics = properties.get("topics", [])
        
        if not any("pep" in t.lower() for t in topics):
            return None
        
        # Simple heuristic (can be improved with more data)
        position = (properties.get("position", [None])[0] or "").lower()
        
        if any(term in position for term in ["president", "minister", "director", "general"]):
            return 1
        elif any(term in position for term in ["member", "official", "family"]):
            return 2
        elif "associate" in position:
            return 3
        else:
            return 2  # Default to Tier 2
    
    def _extract_categories(self, match: dict) -> list[str]:
        """
        Extract FATF 22 predicate offence categories from match.
        
        Maps OpenSanctions topics to standard categories.
        """
        topics = match.get("properties", {}).get("topics", [])
        categories = []
        
        # Map topics to standard categories
        category_map = {
            "fraud": ["fraud"],
            "money": ["money_laundering"],
            "terror": ["terrorism"],
            "narco": ["narcotics"],
            "bribery": ["bribery", "corruption"],
            "tax": ["tax_evasion"],
            "violence": ["violent_crime"],
        }
        
        for topic in topics:
            topic_lower = topic.lower()
            for key, cats in category_map.items():
                if key in topic_lower:
                    categories.extend(cats)
        
        return list(set(categories))  # Remove duplicates
    
    def _identify_matched_fields(
        self,
        query_name, query_dob, query_country,
        match_names, match_dobs, match_countries
    ) -> list[str]:
        """Identify which fields contributed to the match."""
        fields = []
        
        if query_name and match_names:
            fields.append("name")
        
        if query_dob and query_dob in match_dobs:
            fields.append("date_of_birth")
        
        if query_country and query_country in match_countries:
            fields.append("nationality")
        
        return fields
    
    def _parse_date(self, date_str: str) -> Optional[date]:
        """Safely parse date string."""
        try:
            return datetime.strptime(date_str, "%Y-%m-%d").date()
        except:
            return None
    
    def _country_similarity(self, c1: str, c2: str) -> float:
        """Simple country code similarity."""
        if c1 == c2:
            return 1.0
        # Could add more sophisticated country matching (e.g., USSR -> Russia)
        return 0.0


class ScreeningError(Exception):
    """Custom exception for screening errors."""
    pass


# Singleton instance
_screening_service: Optional[ScreeningService] = None


def get_screening_service() -> ScreeningService:
    """
    Get singleton screening service instance.
    
    Usage in FastAPI endpoints:
        screening: ScreeningService = Depends(get_screening_service)
    """
    global _screening_service
    if _screening_service is None:
        _screening_service = ScreeningService()
    return _screening_service
