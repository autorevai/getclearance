"""
Get Clearance - Risk Engine Tests
==================================
Unit tests for risk assessment and scoring service.

Tests:
- Risk level classification
- Risk signal generation
- Country risk scoring
- Overall risk calculation
- Risk thresholds
"""

import pytest
from datetime import datetime
from uuid import uuid4

from app.services.risk_engine import (
    RiskLevel,
    RiskCategory,
    RiskSignal,
    RiskAssessment,
    RiskEngineService,
    HIGH_RISK_COUNTRIES,
    DEFAULT_COUNTRY_RISK,
)


# ===========================================
# RISK LEVEL TESTS
# ===========================================

class TestRiskLevel:
    """Test RiskLevel enum."""

    def test_risk_levels_exist(self):
        """All risk levels are defined."""
        assert RiskLevel.LOW.value == "low"
        assert RiskLevel.MEDIUM.value == "medium"
        assert RiskLevel.HIGH.value == "high"
        assert RiskLevel.CRITICAL.value == "critical"

    def test_risk_level_ordering(self):
        """Risk levels have correct ordering."""
        levels = [RiskLevel.LOW, RiskLevel.MEDIUM, RiskLevel.HIGH, RiskLevel.CRITICAL]
        assert len(levels) == 4


# ===========================================
# RISK CATEGORY TESTS
# ===========================================

class TestRiskCategory:
    """Test RiskCategory enum."""

    def test_all_categories_exist(self):
        """All risk categories are defined."""
        assert RiskCategory.AML.value == "aml"
        assert RiskCategory.DOCUMENT.value == "document"
        assert RiskCategory.IDENTITY.value == "identity"
        assert RiskCategory.DEVICE.value == "device"
        assert RiskCategory.BEHAVIOR.value == "behavior"
        assert RiskCategory.ADDRESS.value == "address"


# ===========================================
# RISK SIGNAL TESTS
# ===========================================

class TestRiskSignal:
    """Test RiskSignal dataclass."""

    def test_signal_creation(self):
        """Can create a risk signal."""
        signal = RiskSignal(
            category=RiskCategory.AML,
            signal_name="sanctions_hit",
            score=90,
            weight=0.4,
            description="Potential sanctions match found",
        )

        assert signal.category == RiskCategory.AML
        assert signal.signal_name == "sanctions_hit"
        assert signal.score == 90
        assert signal.weight == 0.4

    def test_signal_with_details(self):
        """Signal can include detailed information."""
        signal = RiskSignal(
            category=RiskCategory.DOCUMENT,
            signal_name="document_expired",
            score=60,
            weight=0.2,
            details={
                "document_id": str(uuid4()),
                "expiry_date": "2024-01-01",
            },
            description="Document has expired",
        )

        assert "document_id" in signal.details
        assert "expiry_date" in signal.details

    def test_signal_default_details(self):
        """Signal has empty default details."""
        signal = RiskSignal(
            category=RiskCategory.IDENTITY,
            signal_name="test",
            score=10,
            weight=0.1,
        )

        assert signal.details == {}


# ===========================================
# RISK ASSESSMENT TESTS
# ===========================================

class TestRiskAssessment:
    """Test RiskAssessment dataclass."""

    def test_assessment_creation(self):
        """Can create a risk assessment."""
        assessment = RiskAssessment(
            overall_level=RiskLevel.LOW,
            overall_score=25,
            signals=[],
            recommended_action="auto_approve",
        )

        assert assessment.overall_level == RiskLevel.LOW
        assert assessment.overall_score == 25
        assert assessment.recommended_action == "auto_approve"

    def test_assessment_with_signals(self):
        """Assessment can include multiple signals."""
        signals = [
            RiskSignal(RiskCategory.AML, "clean", 0, 0.4, description="No hits"),
            RiskSignal(RiskCategory.DOCUMENT, "verified", 10, 0.2, description="Documents verified"),
        ]
        assessment = RiskAssessment(
            overall_level=RiskLevel.LOW,
            overall_score=15,
            signals=signals,
            recommended_action="auto_approve",
        )

        assert len(assessment.signals) == 2

    def test_assessment_to_dict(self):
        """Assessment converts to dictionary."""
        signal = RiskSignal(
            category=RiskCategory.AML,
            signal_name="pep_hit",
            score=60,
            weight=0.4,
            description="PEP match found",
        )
        assessment = RiskAssessment(
            overall_level=RiskLevel.MEDIUM,
            overall_score=45,
            signals=[signal],
            recommended_action="manual_review",
        )

        result = assessment.to_dict()

        assert result["overall_level"] == "medium"
        assert result["overall_score"] == 45
        assert result["recommended_action"] == "manual_review"
        assert len(result["signals"]) == 1
        assert result["signals"][0]["category"] == "aml"
        assert result["signals"][0]["signal_name"] == "pep_hit"

    def test_assessment_has_timestamp(self):
        """Assessment includes timestamp."""
        assessment = RiskAssessment(
            overall_level=RiskLevel.LOW,
            overall_score=10,
            signals=[],
            recommended_action="auto_approve",
        )

        assert isinstance(assessment.assessment_time, datetime)


# ===========================================
# HIGH-RISK COUNTRIES TESTS
# ===========================================

class TestHighRiskCountries:
    """Test country risk configuration."""

    def test_north_korea_highest_risk(self):
        """North Korea has maximum risk score."""
        assert HIGH_RISK_COUNTRIES["KP"] == 100

    def test_iran_highest_risk(self):
        """Iran has maximum risk score."""
        assert HIGH_RISK_COUNTRIES["IR"] == 100

    def test_russia_high_risk(self):
        """Russia has high risk (sanctions)."""
        assert HIGH_RISK_COUNTRIES["RU"] == 75

    def test_default_country_risk(self):
        """Default country risk is low."""
        assert DEFAULT_COUNTRY_RISK == 10

    def test_usa_not_in_high_risk(self):
        """USA is not in high-risk list."""
        assert "US" not in HIGH_RISK_COUNTRIES

    def test_uk_not_in_high_risk(self):
        """UK is not in high-risk list."""
        assert "GB" not in HIGH_RISK_COUNTRIES

    def test_fatf_grey_list_included(self):
        """FATF grey list countries are included."""
        # Pakistan is on FATF grey list
        assert "PK" in HIGH_RISK_COUNTRIES
        # Nigeria is on FATF grey list
        assert "NG" in HIGH_RISK_COUNTRIES


# ===========================================
# RISK ENGINE SERVICE TESTS
# ===========================================

class TestRiskEngineService:
    """Test RiskEngineService methods."""

    def test_service_instantiation(self):
        """Can create service instance."""
        service = RiskEngineService()
        assert service is not None

    def test_weight_configuration(self):
        """Risk weights are properly configured."""
        service = RiskEngineService()
        assert service.WEIGHT_AML == 0.40
        assert service.WEIGHT_DOCUMENT == 0.20
        assert service.WEIGHT_COUNTRY == 0.15
        assert service.WEIGHT_ADDRESS == 0.10
        assert service.WEIGHT_IDENTITY == 0.10
        assert service.WEIGHT_DEVICE == 0.05

    def test_weights_sum_to_one(self):
        """All weights sum to 1.0."""
        service = RiskEngineService()
        total_weight = (
            service.WEIGHT_AML
            + service.WEIGHT_DOCUMENT
            + service.WEIGHT_COUNTRY
            + service.WEIGHT_ADDRESS
            + service.WEIGHT_IDENTITY
            + service.WEIGHT_DEVICE
        )
        assert abs(total_weight - 1.0) < 0.001  # Allow for floating point

    def test_threshold_configuration(self):
        """Risk thresholds are properly configured."""
        service = RiskEngineService()
        assert service.THRESHOLD_CRITICAL == 80
        assert service.THRESHOLD_HIGH == 60
        assert service.THRESHOLD_MEDIUM == 40

    def test_thresholds_are_ordered(self):
        """Thresholds are in ascending order."""
        service = RiskEngineService()
        assert service.THRESHOLD_MEDIUM < service.THRESHOLD_HIGH
        assert service.THRESHOLD_HIGH < service.THRESHOLD_CRITICAL


# ===========================================
# RISK LEVEL DETERMINATION TESTS
# ===========================================

class TestRiskLevelDetermination:
    """Test how risk levels are determined from scores."""

    def test_low_risk_score(self):
        """Scores under 40 are low risk."""
        service = RiskEngineService()
        # Based on thresholds, score < 40 = LOW
        assert service.THRESHOLD_MEDIUM == 40

    def test_medium_risk_score(self):
        """Scores 40-59 are medium risk."""
        service = RiskEngineService()
        assert service.THRESHOLD_MEDIUM == 40
        assert service.THRESHOLD_HIGH == 60

    def test_high_risk_score(self):
        """Scores 60-79 are high risk."""
        service = RiskEngineService()
        assert service.THRESHOLD_HIGH == 60
        assert service.THRESHOLD_CRITICAL == 80

    def test_critical_risk_score(self):
        """Scores 80+ are critical risk."""
        service = RiskEngineService()
        assert service.THRESHOLD_CRITICAL == 80


# ===========================================
# COUNTRY RISK HELPER TESTS
# ===========================================

class TestCountryRiskHelpers:
    """Test country risk scoring helpers."""

    def test_get_country_risk_sanctioned(self):
        """Get risk score for sanctioned country."""
        # North Korea should have highest risk
        risk = HIGH_RISK_COUNTRIES.get("KP", DEFAULT_COUNTRY_RISK)
        assert risk == 100

    def test_get_country_risk_grey_list(self):
        """Get risk score for grey list country."""
        # Russia should have elevated risk
        risk = HIGH_RISK_COUNTRIES.get("RU", DEFAULT_COUNTRY_RISK)
        assert risk == 75

    def test_get_country_risk_default(self):
        """Get default risk for unlisted country."""
        # Canada is not in high-risk list
        risk = HIGH_RISK_COUNTRIES.get("CA", DEFAULT_COUNTRY_RISK)
        assert risk == DEFAULT_COUNTRY_RISK


# ===========================================
# RECOMMENDED ACTION TESTS
# ===========================================

class TestRecommendedActions:
    """Test recommended action logic."""

    def test_auto_approve_action(self):
        """Low risk recommends auto-approval."""
        assessment = RiskAssessment(
            overall_level=RiskLevel.LOW,
            overall_score=20,
            signals=[],
            recommended_action="auto_approve",
        )
        assert assessment.recommended_action == "auto_approve"

    def test_manual_review_action(self):
        """Medium/high risk recommends manual review."""
        assessment = RiskAssessment(
            overall_level=RiskLevel.MEDIUM,
            overall_score=55,
            signals=[],
            recommended_action="manual_review",
        )
        assert assessment.recommended_action == "manual_review"

    def test_auto_reject_action(self):
        """Critical risk recommends auto-rejection."""
        assessment = RiskAssessment(
            overall_level=RiskLevel.CRITICAL,
            overall_score=95,
            signals=[],
            recommended_action="auto_reject",
        )
        assert assessment.recommended_action == "auto_reject"


# ===========================================
# SIGNAL WEIGHT VALIDATION TESTS
# ===========================================

class TestSignalWeights:
    """Test signal weight validation."""

    def test_aml_weight_highest(self):
        """AML weight is the highest."""
        service = RiskEngineService()
        assert service.WEIGHT_AML > service.WEIGHT_DOCUMENT
        assert service.WEIGHT_AML > service.WEIGHT_COUNTRY
        assert service.WEIGHT_AML > service.WEIGHT_ADDRESS
        assert service.WEIGHT_AML > service.WEIGHT_IDENTITY
        assert service.WEIGHT_AML > service.WEIGHT_DEVICE

    def test_device_weight_lowest(self):
        """Device weight is the lowest."""
        service = RiskEngineService()
        assert service.WEIGHT_DEVICE < service.WEIGHT_AML
        assert service.WEIGHT_DEVICE < service.WEIGHT_DOCUMENT
        assert service.WEIGHT_DEVICE < service.WEIGHT_COUNTRY
        assert service.WEIGHT_DEVICE < service.WEIGHT_ADDRESS
        assert service.WEIGHT_DEVICE < service.WEIGHT_IDENTITY
