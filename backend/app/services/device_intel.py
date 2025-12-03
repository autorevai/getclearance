"""
Get Clearance - Device Intelligence Service
============================================
IPQualityScore API integration for device fingerprinting and fraud detection.

API Documentation:
- Proxy Detection: https://www.ipqualityscore.com/documentation/proxy-detection-api/overview
- Device Fingerprint: https://www.ipqualityscore.com/documentation/device-fingerprint-api/overview
- Email Validation: https://www.ipqualityscore.com/documentation/email-validation-api/overview
- Phone Validation: https://www.ipqualityscore.com/documentation/phone-validation-api/overview
"""

import logging
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any
from uuid import UUID

import httpx

from app.config import settings

logger = logging.getLogger(__name__)


# ===========================================
# DATA CLASSES
# ===========================================

@dataclass
class IPCheckResult:
    """Result from IP reputation check."""
    ip_address: str
    fraud_score: int
    is_proxy: bool
    is_vpn: bool
    is_tor: bool
    is_bot: bool
    is_crawler: bool
    is_datacenter: bool
    is_mobile: bool
    active_vpn: bool
    active_tor: bool
    recent_abuse: bool
    connection_type: str | None
    country_code: str | None
    city: str | None
    region: str | None
    isp: str | None
    asn: int | None
    organization: str | None
    raw_response: dict[str, Any]


@dataclass
class EmailCheckResult:
    """Result from email validation check."""
    email: str
    valid: bool
    disposable: bool
    fraud_score: int
    recent_abuse: bool
    deliverability: str | None  # high, medium, low
    smtp_score: int | None
    domain_age_days: int | None
    first_seen_days: int | None
    raw_response: dict[str, Any]


@dataclass
class PhoneCheckResult:
    """Result from phone validation check."""
    phone: str
    valid: bool
    fraud_score: int
    line_type: str | None  # landline, mobile, voip, etc.
    carrier: str | None
    country: str | None
    active: bool
    recent_abuse: bool
    risky: bool
    raw_response: dict[str, Any]


@dataclass
class DeviceRiskResult:
    """Combined device risk assessment result."""
    risk_score: int  # 0-100, our calculated score
    risk_level: str  # low, medium, high
    fraud_score: int  # Raw IPQS fraud score
    risk_signals: dict[str, bool]
    ip_check: IPCheckResult | None
    email_check: EmailCheckResult | None
    phone_check: PhoneCheckResult | None
    flags: list[str] = field(default_factory=list)


class DeviceIntelError(Exception):
    """Base exception for device intelligence errors."""
    pass


class IPQualityScoreAPIError(DeviceIntelError):
    """IPQualityScore API returned an error."""
    def __init__(self, status_code: int, message: str):
        self.status_code = status_code
        self.message = message
        super().__init__(f"IPQualityScore API error ({status_code}): {message}")


class DeviceIntelConfigError(DeviceIntelError):
    """Configuration error (e.g., missing API key)."""
    pass


# ===========================================
# DEVICE INTELLIGENCE SERVICE
# ===========================================

class DeviceIntelService:
    """
    Service for device fingerprinting and fraud detection via IPQualityScore.

    Provides:
    - IP reputation checking (VPN, proxy, Tor, bot detection)
    - Email validation (disposable, fraud score)
    - Phone validation (VoIP detection, fraud score)
    - Combined risk scoring

    Usage:
        result = await device_intel_service.check_ip("8.8.8.8")
        if result.fraud_score > 85:
            print("High risk IP!")
    """

    BASE_URL = "https://ipqualityscore.com/api/json"

    def __init__(
        self,
        api_key: str | None = None,
        timeout: float = 30.0,
    ):
        self.api_key = api_key or settings.ipqualityscore_api_key
        self.timeout = timeout
        self._client: httpx.AsyncClient | None = None

    @property
    def is_configured(self) -> bool:
        """Check if service is properly configured."""
        return bool(self.api_key)

    async def _get_client(self) -> httpx.AsyncClient:
        """Get or create HTTP client."""
        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient(
                timeout=self.timeout,
                headers={
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

    # ===========================================
    # IP REPUTATION CHECK
    # ===========================================

    async def check_ip(
        self,
        ip_address: str,
        user_agent: str | None = None,
        user_language: str | None = None,
        strictness: int = 1,
    ) -> IPCheckResult:
        """
        Check IP address reputation using IPQualityScore.

        Args:
            ip_address: IP address to check
            user_agent: Browser user agent for enhanced detection
            user_language: Browser language for detection
            strictness: Detection strictness (0-3, higher = stricter)

        Returns:
            IPCheckResult with fraud indicators
        """
        if not self.is_configured:
            logger.warning("IPQualityScore not configured")
            raise DeviceIntelConfigError("IPQualityScore API key not configured")

        url = f"{self.BASE_URL}/ip/{self.api_key}/{ip_address}"

        params = {
            "strictness": strictness,
            "allow_public_access_points": "true",
            "fast": "false",
            "lighter_penalties": "false",
            "mobile": "true",
        }

        if user_agent:
            params["user_agent"] = user_agent
        if user_language:
            params["user_language"] = user_language

        logger.info(f"Checking IP reputation: {ip_address}")

        try:
            client = await self._get_client()
            response = await client.get(url, params=params)

            if response.status_code != 200:
                raise IPQualityScoreAPIError(
                    response.status_code,
                    response.text[:200]
                )

            data = response.json()

            if not data.get("success", False):
                error_message = data.get("message", "Unknown error")
                raise IPQualityScoreAPIError(400, error_message)

            return IPCheckResult(
                ip_address=ip_address,
                fraud_score=data.get("fraud_score", 0),
                is_proxy=data.get("proxy", False),
                is_vpn=data.get("vpn", False),
                is_tor=data.get("tor", False),
                is_bot=data.get("bot_status", False),
                is_crawler=data.get("is_crawler", False),
                is_datacenter=data.get("datacenter", False) or data.get("host", "").lower() in ["aws", "azure", "google", "digitalocean"],
                is_mobile=data.get("mobile", False),
                active_vpn=data.get("active_vpn", False),
                active_tor=data.get("active_tor", False),
                recent_abuse=data.get("recent_abuse", False),
                connection_type=data.get("connection_type"),
                country_code=data.get("country_code"),
                city=data.get("city"),
                region=data.get("region"),
                isp=data.get("ISP"),
                asn=data.get("ASN"),
                organization=data.get("organization"),
                raw_response=data,
            )

        except httpx.TimeoutException:
            logger.error(f"IP check timeout for {ip_address}")
            raise DeviceIntelError("Request timed out")
        except httpx.RequestError as e:
            logger.error(f"IP check request error: {e}")
            raise DeviceIntelError(str(e))

    # ===========================================
    # EMAIL VALIDATION
    # ===========================================

    async def check_email(
        self,
        email: str,
        fast: bool = False,
        timeout_seconds: int = 7,
    ) -> EmailCheckResult:
        """
        Validate email address using IPQualityScore.

        Args:
            email: Email address to validate
            fast: Skip SMTP verification for faster response
            timeout_seconds: Timeout for email verification

        Returns:
            EmailCheckResult with validation and fraud indicators
        """
        if not self.is_configured:
            raise DeviceIntelConfigError("IPQualityScore API key not configured")

        url = f"{self.BASE_URL}/email/{self.api_key}/{email}"

        params = {
            "fast": str(fast).lower(),
            "timeout": timeout_seconds,
            "suggest_domain": "false",
            "strictness": 0,
            "abuse_strictness": 0,
        }

        logger.info(f"Checking email: {email[:3]}***@***")

        try:
            client = await self._get_client()
            response = await client.get(url, params=params)

            if response.status_code != 200:
                raise IPQualityScoreAPIError(
                    response.status_code,
                    response.text[:200]
                )

            data = response.json()

            if not data.get("success", False):
                error_message = data.get("message", "Unknown error")
                raise IPQualityScoreAPIError(400, error_message)

            return EmailCheckResult(
                email=email,
                valid=data.get("valid", False),
                disposable=data.get("disposable", False),
                fraud_score=data.get("fraud_score", 0),
                recent_abuse=data.get("recent_abuse", False),
                deliverability=data.get("deliverability"),
                smtp_score=data.get("smtp_score"),
                domain_age_days=data.get("domain_age", {}).get("days") if isinstance(data.get("domain_age"), dict) else None,
                first_seen_days=data.get("first_seen", {}).get("days") if isinstance(data.get("first_seen"), dict) else None,
                raw_response=data,
            )

        except httpx.TimeoutException:
            logger.error(f"Email check timeout")
            raise DeviceIntelError("Request timed out")
        except httpx.RequestError as e:
            logger.error(f"Email check request error: {e}")
            raise DeviceIntelError(str(e))

    # ===========================================
    # PHONE VALIDATION
    # ===========================================

    async def check_phone(
        self,
        phone: str,
        country: str | None = None,
    ) -> PhoneCheckResult:
        """
        Validate phone number using IPQualityScore.

        Args:
            phone: Phone number to validate (with or without country code)
            country: ISO 2-letter country code for number formatting

        Returns:
            PhoneCheckResult with validation and fraud indicators
        """
        if not self.is_configured:
            raise DeviceIntelConfigError("IPQualityScore API key not configured")

        url = f"{self.BASE_URL}/phone/{self.api_key}/{phone}"

        params = {
            "strictness": 0,
        }
        if country:
            params["country"] = country.upper()

        logger.info(f"Checking phone: ***{phone[-4:] if len(phone) > 4 else phone}")

        try:
            client = await self._get_client()
            response = await client.get(url, params=params)

            if response.status_code != 200:
                raise IPQualityScoreAPIError(
                    response.status_code,
                    response.text[:200]
                )

            data = response.json()

            if not data.get("success", False):
                error_message = data.get("message", "Unknown error")
                raise IPQualityScoreAPIError(400, error_message)

            return PhoneCheckResult(
                phone=phone,
                valid=data.get("valid", False),
                fraud_score=data.get("fraud_score", 0),
                line_type=data.get("line_type"),
                carrier=data.get("carrier"),
                country=data.get("country"),
                active=data.get("active", False),
                recent_abuse=data.get("recent_abuse", False),
                risky=data.get("risky", False),
                raw_response=data,
            )

        except httpx.TimeoutException:
            logger.error(f"Phone check timeout")
            raise DeviceIntelError("Request timed out")
        except httpx.RequestError as e:
            logger.error(f"Phone check request error: {e}")
            raise DeviceIntelError(str(e))

    # ===========================================
    # COMBINED DEVICE ANALYSIS
    # ===========================================

    async def analyze_device(
        self,
        ip_address: str,
        email: str | None = None,
        phone: str | None = None,
        user_agent: str | None = None,
        phone_country: str | None = None,
    ) -> DeviceRiskResult:
        """
        Perform comprehensive device risk analysis.

        Combines IP, email, and phone checks into a single risk score.

        Args:
            ip_address: IP address to check
            email: Optional email to validate
            phone: Optional phone to validate
            user_agent: Browser user agent
            phone_country: Country code for phone formatting

        Returns:
            DeviceRiskResult with combined risk assessment
        """
        ip_check: IPCheckResult | None = None
        email_check: EmailCheckResult | None = None
        phone_check: PhoneCheckResult | None = None
        flags: list[str] = []

        # IP check (required)
        try:
            ip_check = await self.check_ip(ip_address, user_agent=user_agent)
        except DeviceIntelError as e:
            logger.error(f"IP check failed: {e}")

        # Email check (optional)
        if email:
            try:
                email_check = await self.check_email(email)
            except DeviceIntelError as e:
                logger.error(f"Email check failed: {e}")

        # Phone check (optional)
        if phone:
            try:
                phone_check = await self.check_phone(phone, country=phone_country)
            except DeviceIntelError as e:
                logger.error(f"Phone check failed: {e}")

        # Calculate combined risk score
        risk_score, risk_level, risk_signals, flags = self._calculate_risk(
            ip_check, email_check, phone_check
        )

        return DeviceRiskResult(
            risk_score=risk_score,
            risk_level=risk_level,
            fraud_score=ip_check.fraud_score if ip_check else 0,
            risk_signals=risk_signals,
            ip_check=ip_check,
            email_check=email_check,
            phone_check=phone_check,
            flags=flags,
        )

    def _calculate_risk(
        self,
        ip_check: IPCheckResult | None,
        email_check: EmailCheckResult | None,
        phone_check: PhoneCheckResult | None,
    ) -> tuple[int, str, dict[str, bool], list[str]]:
        """
        Calculate combined risk score and level.

        Risk scoring logic:
        - Base score from IP fraud_score
        - VPN/Proxy: +20 points
        - Tor: +30 points
        - Bot: +40 points
        - Disposable email: +15 points
        - VoIP phone: +10 points
        - Recent abuse: +25 points

        Risk levels:
        - HIGH: score >= 85
        - MEDIUM: score >= 70
        - LOW: score < 70

        Returns:
            Tuple of (risk_score, risk_level, risk_signals, flags)
        """
        risk_signals: dict[str, bool] = {
            "vpn": False,
            "proxy": False,
            "tor": False,
            "bot": False,
            "datacenter": False,
            "abuse": False,
            "disposable_email": False,
            "voip_phone": False,
        }
        flags: list[str] = []

        # Start with IP fraud score
        risk_score = 0
        if ip_check:
            risk_score = ip_check.fraud_score

            # VPN/Proxy detection
            if ip_check.is_vpn or ip_check.active_vpn:
                risk_signals["vpn"] = True
                flags.append("vpn")
                risk_score = min(100, risk_score + 20)

            if ip_check.is_proxy:
                risk_signals["proxy"] = True
                flags.append("proxy")
                risk_score = min(100, risk_score + 20)

            # Tor detection
            if ip_check.is_tor or ip_check.active_tor:
                risk_signals["tor"] = True
                flags.append("tor")
                risk_score = min(100, risk_score + 30)

            # Bot detection
            if ip_check.is_bot:
                risk_signals["bot"] = True
                flags.append("bot")
                risk_score = min(100, risk_score + 40)

            # Datacenter IP
            if ip_check.is_datacenter:
                risk_signals["datacenter"] = True
                flags.append("datacenter")
                risk_score = min(100, risk_score + 10)

            # Recent abuse
            if ip_check.recent_abuse:
                risk_signals["abuse"] = True
                flags.append("abuse")
                risk_score = min(100, risk_score + 25)

        # Email checks
        if email_check:
            if email_check.disposable:
                risk_signals["disposable_email"] = True
                flags.append("disposable_email")
                risk_score = min(100, risk_score + 15)

            if email_check.recent_abuse:
                risk_signals["abuse"] = True
                if "abuse" not in flags:
                    flags.append("email_abuse")
                risk_score = min(100, risk_score + 15)

        # Phone checks
        if phone_check:
            if phone_check.line_type and phone_check.line_type.lower() == "voip":
                risk_signals["voip_phone"] = True
                flags.append("voip_phone")
                risk_score = min(100, risk_score + 10)

            if phone_check.risky:
                risk_score = min(100, risk_score + 15)

        # Determine risk level
        if risk_score >= 85:
            risk_level = "high"
        elif risk_score >= 70:
            risk_level = "medium"
        else:
            risk_level = "low"

        return risk_score, risk_level, risk_signals, flags

    # ===========================================
    # STATISTICS
    # ===========================================

    async def get_stats(
        self,
        db,
        tenant_id: UUID,
        days: int = 30,
    ) -> dict[str, Any]:
        """
        Get fraud detection statistics for a tenant.

        Args:
            db: Database session
            tenant_id: Tenant ID
            days: Number of days to look back

        Returns:
            Dict with fraud statistics
        """
        from datetime import timedelta
        from sqlalchemy import select, func, and_
        from app.models.device import DeviceFingerprint

        cutoff = datetime.utcnow() - timedelta(days=days)

        # Total scans
        total_query = select(func.count(DeviceFingerprint.id)).where(
            and_(
                DeviceFingerprint.tenant_id == tenant_id,
                DeviceFingerprint.created_at >= cutoff,
            )
        )
        total = await db.scalar(total_query) or 0

        # High risk count
        high_risk_query = select(func.count(DeviceFingerprint.id)).where(
            and_(
                DeviceFingerprint.tenant_id == tenant_id,
                DeviceFingerprint.created_at >= cutoff,
                DeviceFingerprint.risk_level == "high",
            )
        )
        high_risk = await db.scalar(high_risk_query) or 0

        # VPN detected
        vpn_query = select(func.count(DeviceFingerprint.id)).where(
            and_(
                DeviceFingerprint.tenant_id == tenant_id,
                DeviceFingerprint.created_at >= cutoff,
                DeviceFingerprint.is_vpn == True,
            )
        )
        vpn_count = await db.scalar(vpn_query) or 0

        # Bot detected
        bot_query = select(func.count(DeviceFingerprint.id)).where(
            and_(
                DeviceFingerprint.tenant_id == tenant_id,
                DeviceFingerprint.created_at >= cutoff,
                DeviceFingerprint.is_bot == True,
            )
        )
        bot_count = await db.scalar(bot_query) or 0

        # Tor detected
        tor_query = select(func.count(DeviceFingerprint.id)).where(
            and_(
                DeviceFingerprint.tenant_id == tenant_id,
                DeviceFingerprint.created_at >= cutoff,
                DeviceFingerprint.is_tor == True,
            )
        )
        tor_count = await db.scalar(tor_query) or 0

        # Average fraud score
        avg_score_query = select(func.avg(DeviceFingerprint.fraud_score)).where(
            and_(
                DeviceFingerprint.tenant_id == tenant_id,
                DeviceFingerprint.created_at >= cutoff,
                DeviceFingerprint.fraud_score.isnot(None),
            )
        )
        avg_score = await db.scalar(avg_score_query) or 0

        return {
            "total_scans": total,
            "high_risk_count": high_risk,
            "high_risk_pct": round(high_risk / total * 100, 1) if total > 0 else 0,
            "vpn_detected": vpn_count,
            "vpn_pct": round(vpn_count / total * 100, 1) if total > 0 else 0,
            "bot_detected": bot_count,
            "bot_pct": round(bot_count / total * 100, 1) if total > 0 else 0,
            "tor_detected": tor_count,
            "tor_pct": round(tor_count / total * 100, 1) if total > 0 else 0,
            "avg_fraud_score": round(avg_score, 1),
            "period_days": days,
        }


# ===========================================
# SINGLETON INSTANCE
# ===========================================

device_intel_service = DeviceIntelService()
