"""
Get Clearance - Risk Engine Service
====================================
Automated risk assessment and scoring for KYC applicants.

Calculates risk based on:
- AML screening results (sanctions, PEP, adverse media)
- Document verification status
- Country risk
- Behavioral signals
- Device/IP signals

Usage:
    from app.services.risk_engine import risk_engine

    assessment = await risk_engine.calculate_risk(
        db=db,
        applicant=applicant,
    )
    print(f"Risk: {assessment.overall_level} ({assessment.overall_score})")
    print(f"Action: {assessment.recommended_action}")
"""

import logging
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models import Applicant, ScreeningCheck, Document

logger = logging.getLogger(__name__)


# ===========================================
# ENUMS AND DATA CLASSES
# ===========================================

class RiskLevel(str, Enum):
    """Risk level categories."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class RiskCategory(str, Enum):
    """Categories of risk signals."""
    AML = "aml"              # Sanctions/PEP/adverse media hits
    DOCUMENT = "document"    # Document verification issues
    IDENTITY = "identity"    # Identity mismatch, country risk
    DEVICE = "device"        # VPN, proxy, suspicious device
    BEHAVIOR = "behavior"    # Suspicious patterns
    ADDRESS = "address"      # Address verification status


@dataclass
class RiskSignal:
    """Individual risk signal contributing to overall score."""
    category: RiskCategory
    signal_name: str
    score: int  # 0-100 (higher = more risky)
    weight: float  # 0-1 (contribution to overall score)
    details: dict[str, Any] = field(default_factory=dict)
    description: str = ""


@dataclass
class RiskAssessment:
    """Complete risk assessment for an applicant."""
    overall_level: RiskLevel
    overall_score: int  # 0-100
    signals: list[RiskSignal]
    recommended_action: str  # 'auto_approve', 'manual_review', 'auto_reject'
    assessment_time: datetime = field(default_factory=datetime.utcnow)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for API response."""
        return {
            "overall_level": self.overall_level.value,
            "overall_score": self.overall_score,
            "recommended_action": self.recommended_action,
            "assessment_time": self.assessment_time.isoformat(),
            "signals": [
                {
                    "category": s.category.value,
                    "signal_name": s.signal_name,
                    "score": s.score,
                    "weight": s.weight,
                    "description": s.description,
                    "details": s.details,
                }
                for s in self.signals
            ],
        }


# ===========================================
# HIGH-RISK COUNTRIES
# ===========================================

# Countries with elevated KYC/AML risk (FATF grey/black list + high-risk jurisdictions)
HIGH_RISK_COUNTRIES = {
    # FATF Black List (Call for Action)
    "KP": 100,  # North Korea
    "IR": 100,  # Iran
    "MM": 90,   # Myanmar

    # FATF Grey List (Increased Monitoring) - as of 2024
    "SY": 85,   # Syria
    "YE": 80,   # Yemen
    "AF": 80,   # Afghanistan
    "PK": 70,   # Pakistan
    "VN": 60,   # Vietnam
    "PH": 60,   # Philippines
    "NG": 65,   # Nigeria
    "TZ": 60,   # Tanzania
    "UG": 55,   # Uganda
    "JM": 55,   # Jamaica
    "HT": 60,   # Haiti
    "VE": 70,   # Venezuela
    "PA": 50,   # Panama
    "AE": 45,   # UAE (financial hub risk)

    # Other elevated risk jurisdictions
    "RU": 75,   # Russia (sanctions)
    "BY": 70,   # Belarus
    "CU": 80,   # Cuba
}

# Default risk score for unlisted countries
DEFAULT_COUNTRY_RISK = 10


# ===========================================
# RISK ENGINE SERVICE
# ===========================================

class RiskEngineService:
    """
    Service for calculating applicant risk scores.

    Risk calculation weights:
    - AML screening: 40%
    - Document verification: 20%
    - Country risk: 15%
    - Address verification: 10%
    - Identity signals: 10%
    - Device/behavior: 5%
    """

    # Risk weights (must sum to 1.0)
    WEIGHT_AML = 0.40
    WEIGHT_DOCUMENT = 0.20
    WEIGHT_COUNTRY = 0.15
    WEIGHT_ADDRESS = 0.10
    WEIGHT_IDENTITY = 0.10
    WEIGHT_DEVICE = 0.05

    # Thresholds for risk levels
    THRESHOLD_CRITICAL = 80
    THRESHOLD_HIGH = 60
    THRESHOLD_MEDIUM = 40

    async def calculate_risk(
        self,
        db: AsyncSession,
        applicant: Applicant,
        screening_checks: list[ScreeningCheck] | None = None,
        documents: list[Document] | None = None,
    ) -> RiskAssessment:
        """
        Calculate comprehensive risk assessment for an applicant.

        Args:
            db: Database session
            applicant: Applicant to assess
            screening_checks: Optional pre-loaded screening checks
            documents: Optional pre-loaded documents

        Returns:
            RiskAssessment with overall score and signals
        """
        signals: list[RiskSignal] = []

        # Load screening checks if not provided
        if screening_checks is None:
            screening_checks = await self._load_screening_checks(db, applicant.id)

        # Load documents if not provided
        if documents is None:
            documents = await self._load_documents(db, applicant.id)

        # Calculate AML risk (weight: 40%)
        aml_signal = self._calculate_aml_risk(screening_checks)
        signals.append(aml_signal)

        # Calculate document risk (weight: 25%)
        doc_signal = self._calculate_document_risk(documents)
        signals.append(doc_signal)

        # Calculate country risk (weight: 15%)
        country_signal = self._calculate_country_risk(applicant)
        signals.append(country_signal)

        # Calculate address risk (weight: 10%)
        address_signal = self._calculate_address_risk(applicant)
        signals.append(address_signal)

        # Calculate identity risk (weight: 10%)
        identity_signal = self._calculate_identity_risk(applicant, documents)
        signals.append(identity_signal)

        # Calculate device/behavior risk (weight: 5%)
        device_signal = self._calculate_device_risk(applicant)
        signals.append(device_signal)

        # Calculate weighted overall score
        overall_score = sum(s.score * s.weight for s in signals)
        overall_score = min(100, max(0, int(overall_score)))

        # Determine risk level
        if overall_score >= self.THRESHOLD_CRITICAL:
            level = RiskLevel.CRITICAL
            action = "auto_reject"
        elif overall_score >= self.THRESHOLD_HIGH:
            level = RiskLevel.HIGH
            action = "manual_review"
        elif overall_score >= self.THRESHOLD_MEDIUM:
            level = RiskLevel.MEDIUM
            action = "manual_review"
        else:
            level = RiskLevel.LOW
            action = "auto_approve"

        # Override for sanctions hits (always critical)
        if any(s.signal_name == "sanctions_hit" and s.score >= 80 for s in signals):
            level = RiskLevel.CRITICAL
            action = "manual_review"  # Don't auto-reject, requires human review

        logger.info(
            f"Risk assessment for applicant {applicant.id}: "
            f"level={level.value}, score={overall_score}, action={action}"
        )

        return RiskAssessment(
            overall_level=level,
            overall_score=overall_score,
            signals=signals,
            recommended_action=action,
        )

    async def _load_screening_checks(
        self,
        db: AsyncSession,
        applicant_id: UUID,
    ) -> list[ScreeningCheck]:
        """Load screening checks for an applicant."""
        query = (
            select(ScreeningCheck)
            .where(ScreeningCheck.applicant_id == applicant_id)
            .options(selectinload(ScreeningCheck.hits))
        )
        result = await db.execute(query)
        return list(result.scalars().all())

    async def _load_documents(
        self,
        db: AsyncSession,
        applicant_id: UUID,
    ) -> list[Document]:
        """Load documents for an applicant."""
        query = select(Document).where(Document.applicant_id == applicant_id)
        result = await db.execute(query)
        return list(result.scalars().all())

    def _calculate_aml_risk(
        self,
        screening_checks: list[ScreeningCheck],
    ) -> RiskSignal:
        """
        Calculate AML risk from screening results.

        Scoring:
        - Sanctions hit: +80 points
        - PEP hit (tier 1): +60 points
        - PEP hit (tier 2-4): +40 points
        - Adverse media: +30 points
        - Multiple hits multiplier
        """
        score = 0
        details = {
            "total_checks": len(screening_checks),
            "sanctions_hits": 0,
            "pep_hits": 0,
            "adverse_media_hits": 0,
            "unresolved_hits": 0,
        }

        if not screening_checks:
            # No screening = baseline risk
            return RiskSignal(
                category=RiskCategory.AML,
                signal_name="no_screening",
                score=20,  # Some risk for unscreened
                weight=self.WEIGHT_AML,
                details=details,
                description="No AML screening completed",
            )

        for check in screening_checks:
            if check.status == "error":
                score += 10  # Screening error adds some risk
                continue

            for hit in (check.hits or []):
                # Only count unresolved or confirmed hits
                if hit.resolution_status == "confirmed_false":
                    continue  # False positive, skip

                if hit.resolution_status == "pending":
                    details["unresolved_hits"] += 1

                if hit.hit_type == "sanctions":
                    details["sanctions_hits"] += 1
                    score += 80 if hit.confidence >= 80 else 50

                elif hit.hit_type == "pep":
                    details["pep_hits"] += 1
                    tier = hit.pep_tier or 2
                    if tier == 1:
                        score += 60
                    elif tier == 2:
                        score += 40
                    else:
                        score += 25

                elif hit.hit_type == "adverse_media":
                    details["adverse_media_hits"] += 1
                    score += 30

        # Cap at 100
        score = min(100, score)

        # Determine signal name
        if details["sanctions_hits"] > 0:
            signal_name = "sanctions_hit"
            description = f"{details['sanctions_hits']} sanctions hit(s) found"
        elif details["pep_hits"] > 0:
            signal_name = "pep_hit"
            description = f"{details['pep_hits']} PEP hit(s) found"
        elif details["adverse_media_hits"] > 0:
            signal_name = "adverse_media"
            description = f"{details['adverse_media_hits']} adverse media hit(s) found"
        else:
            signal_name = "screening_clear"
            description = "AML screening clear"

        return RiskSignal(
            category=RiskCategory.AML,
            signal_name=signal_name,
            score=score,
            weight=self.WEIGHT_AML,
            details=details,
            description=description,
        )

    def _calculate_document_risk(
        self,
        documents: list[Document],
    ) -> RiskSignal:
        """
        Calculate document verification risk.

        Scoring:
        - No documents: +50 points
        - Rejected documents: +40 points each
        - Expired documents: +30 points each
        - Pending documents: +20 points
        - Low confidence verification: +15 points
        """
        score = 0
        details = {
            "total_documents": len(documents),
            "verified": 0,
            "pending": 0,
            "rejected": 0,
            "expired": 0,
        }

        if not documents:
            return RiskSignal(
                category=RiskCategory.DOCUMENT,
                signal_name="no_documents",
                score=50,
                weight=self.WEIGHT_DOCUMENT,
                details=details,
                description="No documents submitted",
            )

        for doc in documents:
            if doc.status == "verified":
                details["verified"] += 1
                # Check verification confidence if available
                if hasattr(doc, "verification_result") and doc.verification_result:
                    confidence = doc.verification_result.get("confidence", 100)
                    if confidence < 70:
                        score += 15

            elif doc.status == "rejected":
                details["rejected"] += 1
                score += 40

            elif doc.status == "pending":
                details["pending"] += 1
                score += 20

            # Check for expired documents
            if hasattr(doc, "expiry_date") and doc.expiry_date:
                from datetime import date
                if doc.expiry_date < date.today():
                    details["expired"] += 1
                    score += 30

        score = min(100, score)

        # Determine signal name
        if details["rejected"] > 0:
            signal_name = "document_rejected"
            description = f"{details['rejected']} document(s) rejected"
        elif details["pending"] > 0:
            signal_name = "documents_pending"
            description = f"{details['pending']} document(s) pending verification"
        elif details["expired"] > 0:
            signal_name = "document_expired"
            description = f"{details['expired']} document(s) expired"
        elif details["verified"] == len(documents):
            signal_name = "documents_verified"
            description = "All documents verified"
        else:
            signal_name = "documents_partial"
            description = f"{details['verified']}/{len(documents)} documents verified"

        return RiskSignal(
            category=RiskCategory.DOCUMENT,
            signal_name=signal_name,
            score=score,
            weight=self.WEIGHT_DOCUMENT,
            details=details,
            description=description,
        )

    def _calculate_country_risk(
        self,
        applicant: Applicant,
    ) -> RiskSignal:
        """
        Calculate country risk based on nationality and residence.

        Uses FATF grey/black list and other high-risk jurisdictions.
        """
        nationality = applicant.nationality
        residence = applicant.country_of_residence

        # Get risk scores for both countries
        nationality_risk = HIGH_RISK_COUNTRIES.get(nationality, DEFAULT_COUNTRY_RISK) if nationality else DEFAULT_COUNTRY_RISK
        residence_risk = HIGH_RISK_COUNTRIES.get(residence, DEFAULT_COUNTRY_RISK) if residence else DEFAULT_COUNTRY_RISK

        # Use higher of the two
        score = max(nationality_risk, residence_risk)

        details = {
            "nationality": nationality,
            "nationality_risk": nationality_risk,
            "country_of_residence": residence,
            "residence_risk": residence_risk,
        }

        if score >= 80:
            signal_name = "high_risk_country"
            description = f"High-risk jurisdiction: {nationality or residence}"
        elif score >= 50:
            signal_name = "elevated_country_risk"
            description = f"Elevated country risk: {nationality or residence}"
        else:
            signal_name = "standard_country_risk"
            description = "Standard country risk"

        return RiskSignal(
            category=RiskCategory.IDENTITY,
            signal_name=signal_name,
            score=score,
            weight=self.WEIGHT_COUNTRY,
            details=details,
            description=description,
        )

    def _calculate_address_risk(
        self,
        applicant: Applicant,
    ) -> RiskSignal:
        """
        Calculate address verification risk.

        Scoring based on address data stored in applicant.address JSONB:
        - No address: +40 points
        - Invalid/unverified address: +30 points
        - Partial match: +15 points
        - High-risk area: +25 points
        - Verification skipped: +20 points
        - Verified, deliverable: 0 points
        """
        score = 0
        address = applicant.address or {}
        details = {
            "has_address": bool(address),
            "verification_status": address.get("verification_status", "none"),
            "verification_score": address.get("verification_score", 0),
            "is_deliverable": address.get("is_deliverable", False),
            "is_high_risk_area": address.get("is_high_risk_area", False),
            "country": address.get("country"),
        }

        if not address:
            return RiskSignal(
                category=RiskCategory.ADDRESS,
                signal_name="no_address",
                score=40,
                weight=self.WEIGHT_ADDRESS,
                details=details,
                description="No address provided",
            )

        verification_status = address.get("verification_status", "none")

        # Score based on verification status
        if verification_status == "invalid":
            score += 35
        elif verification_status == "error":
            score += 30
        elif verification_status == "unverified":
            score += 25
        elif verification_status == "partial_match":
            score += 15
        elif verification_status == "skipped":
            score += 20
        elif verification_status == "verified":
            score += 0  # Good!
        else:
            score += 30  # Unknown status

        # High-risk area
        if address.get("is_high_risk_area"):
            score += 25
            details["high_risk_reason"] = address.get("high_risk_reason", "High-risk jurisdiction")

        # Not deliverable (but verified)
        if verification_status == "verified" and not address.get("is_deliverable"):
            score += 10

        # Low verification score (even if status is ok)
        verification_score = address.get("verification_score", 0)
        if 0 < verification_score < 50:
            score += 15
        elif 50 <= verification_score < 70:
            score += 5

        score = min(100, score)

        # Determine signal name and description
        if score >= 50:
            signal_name = "address_high_risk"
            description = "High address risk"
        elif score >= 25:
            signal_name = "address_issues"
            description = "Address verification issues"
        elif score > 0:
            signal_name = "address_minor_issues"
            description = "Minor address concerns"
        else:
            signal_name = "address_verified"
            description = "Address verified and deliverable"

        return RiskSignal(
            category=RiskCategory.ADDRESS,
            signal_name=signal_name,
            score=score,
            weight=self.WEIGHT_ADDRESS,
            details=details,
            description=description,
        )

    def _calculate_identity_risk(
        self,
        applicant: Applicant,
        documents: list[Document],
    ) -> RiskSignal:
        """
        Calculate identity verification risk.

        Checks for:
        - Missing identity information
        - Age-related risks (very young/old)
        - Name/DOB mismatches with documents
        """
        score = 0
        details = {
            "has_name": bool(applicant.first_name and applicant.last_name),
            "has_dob": bool(applicant.date_of_birth),
            "has_nationality": bool(applicant.nationality),
            "age": None,
            "mismatches": [],
        }

        # Missing information
        if not applicant.first_name or not applicant.last_name:
            score += 30

        if not applicant.date_of_birth:
            score += 20
        else:
            # Calculate age
            from datetime import date
            today = date.today()
            age = today.year - applicant.date_of_birth.year
            if today.month < applicant.date_of_birth.month or (
                today.month == applicant.date_of_birth.month and today.day < applicant.date_of_birth.day
            ):
                age -= 1
            details["age"] = age

            # Age-based risk
            if age < 18:
                score += 40  # Under 18 = high risk
            elif age < 21:
                score += 15  # Very young adult
            elif age > 85:
                score += 20  # Elderly = potential vulnerability

        if not applicant.nationality:
            score += 15

        # Check for document mismatches (if we have document data)
        for doc in documents:
            if hasattr(doc, "extracted_data") and doc.extracted_data:
                extracted = doc.extracted_data

                # Name mismatch
                if extracted.get("full_name"):
                    doc_name = extracted["full_name"].lower()
                    app_name = f"{applicant.first_name} {applicant.last_name}".lower()
                    if doc_name != app_name and not self._fuzzy_name_match(doc_name, app_name):
                        score += 25
                        details["mismatches"].append("name")

                # DOB mismatch
                if extracted.get("date_of_birth") and applicant.date_of_birth:
                    if str(extracted["date_of_birth"]) != str(applicant.date_of_birth):
                        score += 30
                        details["mismatches"].append("dob")

        score = min(100, score)

        if score >= 40:
            signal_name = "identity_issues"
            description = "Identity verification issues detected"
        elif score > 0:
            signal_name = "incomplete_identity"
            description = "Some identity information missing"
        else:
            signal_name = "identity_verified"
            description = "Identity information complete"

        return RiskSignal(
            category=RiskCategory.IDENTITY,
            signal_name=signal_name,
            score=score,
            weight=self.WEIGHT_IDENTITY,
            details=details,
            description=description,
        )

    def _calculate_device_risk(
        self,
        applicant: Applicant,
    ) -> RiskSignal:
        """
        Calculate device/behavioral risk.

        Checks for:
        - VPN/proxy usage
        - Device fingerprint anomalies
        - Suspicious IP patterns
        """
        score = 0
        details = {
            "ip_address": str(applicant.ip_address) if applicant.ip_address else None,
            "device_info": applicant.device_info,
            "signals": [],
        }

        device_info = applicant.device_info or {}

        # Check for VPN/proxy indicators
        if device_info.get("is_vpn") or device_info.get("is_proxy"):
            score += 30
            details["signals"].append("vpn_detected")

        # Check for TOR
        if device_info.get("is_tor"):
            score += 50
            details["signals"].append("tor_detected")

        # Check for datacenter IP
        if device_info.get("is_datacenter"):
            score += 25
            details["signals"].append("datacenter_ip")

        # Check for device fingerprint issues
        if device_info.get("device_id_mismatch"):
            score += 20
            details["signals"].append("device_mismatch")

        # Check for suspicious patterns
        if device_info.get("multiple_submissions"):
            score += 35
            details["signals"].append("multiple_submissions")

        score = min(100, score)

        if score >= 40:
            signal_name = "suspicious_device"
            description = "Suspicious device/network signals detected"
        elif score > 0:
            signal_name = "device_flags"
            description = f"{len(details['signals'])} device flag(s)"
        else:
            signal_name = "device_normal"
            description = "No device anomalies detected"

        return RiskSignal(
            category=RiskCategory.DEVICE,
            signal_name=signal_name,
            score=score,
            weight=self.WEIGHT_DEVICE,
            details=details,
            description=description,
        )

    def _fuzzy_name_match(self, name1: str, name2: str) -> bool:
        """Simple fuzzy name matching."""
        # Normalize
        n1 = set(name1.lower().split())
        n2 = set(name2.lower().split())

        # Check for significant overlap
        overlap = n1 & n2
        return len(overlap) >= min(len(n1), len(n2)) * 0.6

    async def apply_workflow_rules(
        self,
        db: AsyncSession,
        applicant: Applicant,
        assessment: RiskAssessment,
        tenant_id: UUID,
    ) -> str:
        """
        Apply tenant workflow rules to determine final action.

        Rules are evaluated in priority order. First matching rule wins.

        Args:
            db: Database session
            applicant: The applicant
            assessment: Risk assessment result
            tenant_id: Tenant ID

        Returns:
            Final action: 'auto_approve', 'manual_review', 'auto_reject', 'escalate'
        """
        from app.models.workflow import WorkflowRule

        # Get active rules ordered by priority
        query = (
            select(WorkflowRule)
            .where(
                WorkflowRule.tenant_id == tenant_id,
                WorkflowRule.is_active == True,
            )
            .order_by(WorkflowRule.priority.desc())
        )
        result = await db.execute(query)
        rules = result.scalars().all()

        for rule in rules:
            if self._rule_matches(rule, applicant, assessment):
                logger.info(
                    f"Workflow rule '{rule.name}' matched for applicant {applicant.id}: "
                    f"action={rule.action}"
                )
                return rule.action

        # No rules matched, use assessment recommendation
        return assessment.recommended_action

    def _rule_matches(
        self,
        rule: "WorkflowRule",
        applicant: Applicant,
        assessment: RiskAssessment,
    ) -> bool:
        """Check if a workflow rule matches the applicant."""
        conditions = rule.conditions or {}

        for key, expected in conditions.items():
            actual = None

            if key == "risk_level":
                actual = assessment.overall_level.value
            elif key == "risk_score_min":
                return assessment.overall_score >= expected
            elif key == "risk_score_max":
                return assessment.overall_score <= expected
            elif key == "country":
                actual = applicant.nationality or applicant.country_of_residence
            elif key == "has_sanctions_hit":
                actual = any(
                    s.signal_name == "sanctions_hit"
                    for s in assessment.signals
                )
            elif key == "has_pep_hit":
                actual = any(
                    s.signal_name == "pep_hit"
                    for s in assessment.signals
                )
            else:
                # Try to get from applicant
                actual = getattr(applicant, key, None)

            # Check match
            if isinstance(expected, list):
                if actual not in expected:
                    return False
            elif actual != expected:
                return False

        return True


# Singleton instance
risk_engine = RiskEngineService()
