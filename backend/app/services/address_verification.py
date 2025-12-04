"""
Get Clearance - Address Verification Service
=============================================
Service for validating, standardizing, and geocoding addresses.

Supports multiple providers:
- Smarty (US addresses) - Production quality
- Google Places API - International
- Mock mode for development/testing

Address verification contributes to overall risk assessment by:
- Verifying address deliverability
- Detecting high-risk locations
- Standardizing formats for consistency
"""

import re
from dataclasses import dataclass, field
from enum import Enum
from typing import Any

import httpx
from pydantic import BaseModel

from app.config import settings


class AddressType(str, Enum):
    """Type of address."""
    RESIDENTIAL = "residential"
    COMMERCIAL = "commercial"
    PO_BOX = "po_box"
    MILITARY = "military"
    UNKNOWN = "unknown"


class AddressVerificationStatus(str, Enum):
    """Verification status."""
    VERIFIED = "verified"
    PARTIAL_MATCH = "partial_match"
    UNVERIFIED = "unverified"
    INVALID = "invalid"
    ERROR = "error"


@dataclass
class StandardizedAddress:
    """A standardized, verified address."""
    # Original input
    original_input: dict

    # Standardized components
    street_line_1: str
    street_line_2: str | None = None
    city: str = ""
    state: str = ""  # State/province/region code
    postal_code: str = ""
    country: str = ""  # ISO 3166-1 alpha-2

    # Geocoding
    latitude: float | None = None
    longitude: float | None = None

    # Metadata
    address_type: AddressType = AddressType.UNKNOWN
    is_deliverable: bool = False
    dpv_match_code: str | None = None  # USPS Delivery Point Validation

    # Verification
    verification_status: AddressVerificationStatus = AddressVerificationStatus.UNVERIFIED
    verification_provider: str = "none"
    verification_score: int = 0  # 0-100

    # Risk signals
    is_high_risk_area: bool = False
    high_risk_reason: str | None = None

    # Raw response for debugging
    raw_response: dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "street_line_1": self.street_line_1,
            "street_line_2": self.street_line_2,
            "city": self.city,
            "state": self.state,
            "postal_code": self.postal_code,
            "country": self.country,
            "latitude": self.latitude,
            "longitude": self.longitude,
            "address_type": self.address_type.value,
            "is_deliverable": self.is_deliverable,
            "verification_status": self.verification_status.value,
            "verification_score": self.verification_score,
            "is_high_risk_area": self.is_high_risk_area,
        }


class AddressInput(BaseModel):
    """Input for address verification."""
    street: str
    street_line_2: str | None = None
    city: str
    state: str | None = None
    postal_code: str | None = None
    country: str = "US"  # ISO 3166-1 alpha-2


class AddressVerificationService:
    """
    Service for verifying and standardizing addresses.

    Supports multiple providers:
    - Smarty (US addresses)
    - Mock mode for development
    """

    # High-risk country codes (FATF grey/black list + sanctions)
    HIGH_RISK_COUNTRIES = {
        "AF", "BY", "CF", "CD", "CU", "GW", "HT", "IR",
        "IQ", "LB", "LY", "ML", "MM", "NI", "KP", "PK",
        "PA", "RU", "SO", "SS", "SD", "SY", "VE", "YE", "ZW"
    }

    def __init__(
        self,
        smarty_auth_id: str | None = None,
        smarty_auth_token: str | None = None,
    ):
        """
        Initialize address verification service.

        Args:
            smarty_auth_id: Smarty API auth ID
            smarty_auth_token: Smarty API auth token
        """
        self.smarty_auth_id = smarty_auth_id or getattr(settings, 'smarty_auth_id', None)
        self.smarty_auth_token = smarty_auth_token or getattr(settings, 'smarty_auth_token', None)

        # Check if Smarty is configured
        self.smarty_configured = bool(self.smarty_auth_id and self.smarty_auth_token)

        # Smarty API URLs
        self.smarty_us_url = "https://us-street.api.smarty.com/street-address"
        self.smarty_intl_url = "https://international-street.api.smarty.com/verify"

    @property
    def is_configured(self) -> bool:
        """Check if any provider is configured."""
        return self.smarty_configured

    async def verify_address(self, address: AddressInput) -> StandardizedAddress:
        """
        Verify and standardize an address.

        Automatically routes to appropriate provider based on country.

        Args:
            address: Address input to verify

        Returns:
            StandardizedAddress with verification results
        """
        country = address.country.upper()

        # Check for high-risk country first
        is_high_risk = country in self.HIGH_RISK_COUNTRIES

        # Route to appropriate provider
        if country == "US" and self.smarty_configured:
            result = await self._verify_us_smarty(address)
        elif self.smarty_configured and country != "US":
            result = await self._verify_international_smarty(address)
        else:
            # Fall back to basic validation
            result = await self._verify_basic(address)

        # Add high-risk flag
        if is_high_risk:
            result.is_high_risk_area = True
            result.high_risk_reason = "High-risk jurisdiction (FATF/sanctions)"

        return result

    async def _verify_us_smarty(self, address: AddressInput) -> StandardizedAddress:
        """Verify US address using Smarty API."""
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(
                    self.smarty_us_url,
                    params={
                        'auth-id': self.smarty_auth_id,
                        'auth-token': self.smarty_auth_token,
                        'street': address.street,
                        'street2': address.street_line_2 or '',
                        'city': address.city,
                        'state': address.state or '',
                        'zipcode': address.postal_code or '',
                        'candidates': 1,
                        'match': 'enhanced',
                    }
                )

                if response.status_code != 200:
                    return self._create_error_result(address, f"Smarty API error: {response.status_code}")

                data = response.json()

                if not data:
                    # No match found
                    return StandardizedAddress(
                        original_input=address.model_dump(),
                        street_line_1=address.street,
                        street_line_2=address.street_line_2,
                        city=address.city,
                        state=address.state or "",
                        postal_code=address.postal_code or "",
                        country="US",
                        verification_status=AddressVerificationStatus.INVALID,
                        verification_provider="smarty",
                        verification_score=0,
                    )

                candidate = data[0]
                components = candidate.get('components', {})
                metadata = candidate.get('metadata', {})
                analysis = candidate.get('analysis', {})

                # Determine address type
                addr_type = AddressType.UNKNOWN
                rdi = metadata.get('rdi', '')
                if rdi == 'Residential':
                    addr_type = AddressType.RESIDENTIAL
                elif rdi == 'Commercial':
                    addr_type = AddressType.COMMERCIAL

                # Determine deliverability
                dpv_match = analysis.get('dpv_match_code', '')
                is_deliverable = dpv_match in ['Y', 'S', 'D']

                # Calculate verification score
                score = self._calculate_smarty_score(analysis)

                # Determine status
                if dpv_match == 'Y':
                    status = AddressVerificationStatus.VERIFIED
                elif dpv_match in ['S', 'D']:
                    status = AddressVerificationStatus.PARTIAL_MATCH
                else:
                    status = AddressVerificationStatus.UNVERIFIED

                return StandardizedAddress(
                    original_input=address.model_dump(),
                    street_line_1=candidate.get('delivery_line_1', address.street),
                    street_line_2=candidate.get('delivery_line_2'),
                    city=components.get('city_name', address.city),
                    state=components.get('state_abbreviation', address.state or ''),
                    postal_code=f"{components.get('zipcode', '')}-{components.get('plus4_code', '')}" if components.get('plus4_code') else components.get('zipcode', ''),
                    country="US",
                    latitude=metadata.get('latitude'),
                    longitude=metadata.get('longitude'),
                    address_type=addr_type,
                    is_deliverable=is_deliverable,
                    dpv_match_code=dpv_match,
                    verification_status=status,
                    verification_provider="smarty",
                    verification_score=score,
                    raw_response=candidate,
                )

        except httpx.TimeoutException:
            return self._create_error_result(address, "Address verification timeout")
        except Exception as e:
            return self._create_error_result(address, str(e))

    async def _verify_international_smarty(self, address: AddressInput) -> StandardizedAddress:
        """Verify international address using Smarty API."""
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                # Build address string
                address_str = address.street
                if address.street_line_2:
                    address_str += f", {address.street_line_2}"
                address_str += f", {address.city}"
                if address.state:
                    address_str += f", {address.state}"
                if address.postal_code:
                    address_str += f" {address.postal_code}"

                response = await client.get(
                    self.smarty_intl_url,
                    params={
                        'auth-id': self.smarty_auth_id,
                        'auth-token': self.smarty_auth_token,
                        'country': address.country,
                        'address1': address.street,
                        'address2': address.street_line_2 or '',
                        'locality': address.city,
                        'administrative_area': address.state or '',
                        'postal_code': address.postal_code or '',
                    }
                )

                if response.status_code != 200:
                    return self._create_error_result(address, f"Smarty API error: {response.status_code}")

                data = response.json()

                if not data:
                    return StandardizedAddress(
                        original_input=address.model_dump(),
                        street_line_1=address.street,
                        street_line_2=address.street_line_2,
                        city=address.city,
                        state=address.state or "",
                        postal_code=address.postal_code or "",
                        country=address.country,
                        verification_status=AddressVerificationStatus.INVALID,
                        verification_provider="smarty",
                        verification_score=0,
                    )

                candidate = data[0]
                components = candidate.get('components', {})
                metadata = candidate.get('metadata', {})
                analysis = candidate.get('analysis', {})

                # International verification score
                precision = analysis.get('verification_status', '')
                if precision == 'Verified':
                    status = AddressVerificationStatus.VERIFIED
                    score = 100
                elif precision == 'Partial':
                    status = AddressVerificationStatus.PARTIAL_MATCH
                    score = 70
                elif precision == 'Ambiguous':
                    status = AddressVerificationStatus.PARTIAL_MATCH
                    score = 50
                else:
                    status = AddressVerificationStatus.UNVERIFIED
                    score = 30

                return StandardizedAddress(
                    original_input=address.model_dump(),
                    street_line_1=components.get('thoroughfare', address.street),
                    street_line_2=components.get('building'),
                    city=components.get('locality', address.city),
                    state=components.get('administrative_area', address.state or ''),
                    postal_code=components.get('postal_code', address.postal_code or ''),
                    country=components.get('country_iso_3', address.country),
                    latitude=metadata.get('latitude'),
                    longitude=metadata.get('longitude'),
                    verification_status=status,
                    verification_provider="smarty",
                    verification_score=score,
                    raw_response=candidate,
                )

        except httpx.TimeoutException:
            return self._create_error_result(address, "Address verification timeout")
        except Exception as e:
            return self._create_error_result(address, str(e))

    async def _verify_basic(self, address: AddressInput) -> StandardizedAddress:
        """
        Basic address validation without external API.

        Performs:
        - Format validation
        - Country code validation
        - Basic standardization
        """
        score = 0
        status = AddressVerificationStatus.UNVERIFIED

        # Check required fields
        if address.street and address.city:
            score += 40

        # Check postal code format (basic)
        if address.postal_code:
            if address.country == "US":
                if re.match(r'^\d{5}(-\d{4})?$', address.postal_code):
                    score += 20
            elif address.country in ["GB", "UK"]:
                if re.match(r'^[A-Z]{1,2}\d[A-Z\d]? ?\d[A-Z]{2}$', address.postal_code, re.I):
                    score += 20
            elif address.country == "CA":
                if re.match(r'^[A-Z]\d[A-Z] ?\d[A-Z]\d$', address.postal_code, re.I):
                    score += 20
            else:
                score += 10  # Some postal code is better than none

        # State/region provided
        if address.state:
            score += 15

        # Valid country code
        if address.country and len(address.country) == 2:
            score += 15

        # Determine status
        if score >= 80:
            status = AddressVerificationStatus.PARTIAL_MATCH
        elif score >= 50:
            status = AddressVerificationStatus.UNVERIFIED
        else:
            status = AddressVerificationStatus.INVALID

        # Basic standardization
        street = address.street.strip().title() if address.street else ""
        city = address.city.strip().title() if address.city else ""
        state = address.state.strip().upper() if address.state else ""
        postal = address.postal_code.strip().upper() if address.postal_code else ""
        country = address.country.strip().upper() if address.country else ""

        return StandardizedAddress(
            original_input=address.model_dump(),
            street_line_1=street,
            street_line_2=address.street_line_2.strip() if address.street_line_2 else None,
            city=city,
            state=state,
            postal_code=postal,
            country=country,
            verification_status=status,
            verification_provider="basic",
            verification_score=score,
            is_high_risk_area=country in self.HIGH_RISK_COUNTRIES,
        )

    def _calculate_smarty_score(self, analysis: dict) -> int:
        """Calculate verification score from Smarty analysis."""
        score = 50  # Base score

        dpv_match = analysis.get('dpv_match_code', '')
        if dpv_match == 'Y':
            score += 50
        elif dpv_match == 'S':
            score += 35
        elif dpv_match == 'D':
            score += 25
        elif dpv_match == 'N':
            score = 20

        # Penalize for footnotes indicating issues
        footnotes = analysis.get('dpv_footnotes', '')
        if 'AA' in footnotes:  # Street matched
            score = min(score + 5, 100)
        if 'BB' in footnotes:  # Missing secondary (apt)
            score = max(score - 10, 0)
        if 'CC' in footnotes:  # Invalid secondary
            score = max(score - 10, 0)

        return min(score, 100)

    def _create_error_result(self, address: AddressInput, error_msg: str) -> StandardizedAddress:
        """Create error result."""
        return StandardizedAddress(
            original_input=address.model_dump(),
            street_line_1=address.street,
            street_line_2=address.street_line_2,
            city=address.city,
            state=address.state or "",
            postal_code=address.postal_code or "",
            country=address.country,
            verification_status=AddressVerificationStatus.ERROR,
            verification_provider="none",
            verification_score=0,
            high_risk_reason=error_msg,
        )

    def calculate_address_risk_score(self, result: StandardizedAddress) -> int:
        """
        Calculate risk score contribution from address verification.

        Returns:
            Risk score 0-100 (higher = more risk)
        """
        risk_score = 0

        # High-risk country
        if result.is_high_risk_area:
            risk_score += 40

        # Verification status
        if result.verification_status == AddressVerificationStatus.INVALID:
            risk_score += 30
        elif result.verification_status == AddressVerificationStatus.ERROR:
            risk_score += 25
        elif result.verification_status == AddressVerificationStatus.UNVERIFIED:
            risk_score += 15
        elif result.verification_status == AddressVerificationStatus.PARTIAL_MATCH:
            risk_score += 5
        # VERIFIED adds 0

        # Not deliverable
        if not result.is_deliverable and result.verification_status == AddressVerificationStatus.VERIFIED:
            risk_score += 10

        # PO Box (higher risk for certain use cases)
        if result.address_type == AddressType.PO_BOX:
            risk_score += 5

        return min(risk_score, 100)


# Global service instance
address_verification_service = AddressVerificationService()


async def verify_applicant_address(
    street: str,
    city: str,
    state: str | None = None,
    postal_code: str | None = None,
    country: str = "US",
) -> StandardizedAddress:
    """
    Convenience function to verify an applicant's address.

    Args:
        street: Street address
        city: City name
        state: State/province code
        postal_code: ZIP/postal code
        country: ISO 3166-1 alpha-2 country code

    Returns:
        StandardizedAddress with verification results
    """
    address_input = AddressInput(
        street=street,
        city=city,
        state=state,
        postal_code=postal_code,
        country=country,
    )

    return await address_verification_service.verify_address(address_input)
