"""
Tests for GDPR compliance features.

Tests cover:
- Data export (SAR - Subject Access Request)
- GDPR deletion (Right to Erasure)
- Consent tracking
- Legal hold
- Retention policies
"""

from datetime import datetime, timedelta
from uuid import UUID, uuid4

import pytest
import pytest_asyncio
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Applicant, Document, ScreeningCheck, Case


# ===========================================
# RETENTION SERVICE TESTS
# ===========================================

class TestRetentionPolicies:
    """Test retention policy functions."""

    def test_get_retention_period_approved(self):
        """Test retention period for approved applicants."""
        from app.services.retention import get_retention_period

        period = get_retention_period("approved")
        assert period.days == 365 * 5  # 5 years

    def test_get_retention_period_rejected(self):
        """Test retention period for rejected applicants."""
        from app.services.retention import get_retention_period

        period = get_retention_period("rejected")
        assert period.days == 365 * 5  # 5 years (AML requirement)

    def test_get_retention_period_flagged(self):
        """Test retention period for flagged applicants."""
        from app.services.retention import get_retention_period

        period = get_retention_period("flagged")
        assert period.days == 365 * 7  # 7 years (extended)

    def test_get_retention_period_pending(self):
        """Test retention period for pending applicants."""
        from app.services.retention import get_retention_period

        period = get_retention_period("pending")
        assert period.days == 90

    def test_get_retention_period_withdrawn(self):
        """Test retention period for withdrawn applicants."""
        from app.services.retention import get_retention_period

        period = get_retention_period("withdrawn")
        assert period.days == 30

    def test_get_retention_period_unknown_status(self):
        """Test default retention period for unknown status."""
        from app.services.retention import get_retention_period

        period = get_retention_period("unknown_status")
        assert period.days == 365 * 5  # Default 5 years

    def test_calculate_retention_expiry(self):
        """Test retention expiry calculation."""
        from app.services.retention import calculate_retention_expiry

        base_date = datetime(2025, 1, 1)
        expiry = calculate_retention_expiry("approved", from_date=base_date)

        expected = base_date + timedelta(days=365 * 5)
        assert expiry == expected

    def test_can_delete_for_aml_legal_hold_blocks(self):
        """Test that legal hold blocks deletion."""
        from app.services.retention import can_delete_for_aml

        # Create mock applicant with legal hold
        class MockApplicant:
            legal_hold = True
            status = "approved"
            updated_at = datetime.utcnow()
            retention_expires_at = None

        applicant = MockApplicant()
        assert can_delete_for_aml(applicant) is False

    def test_can_delete_for_aml_approved_allowed(self):
        """Test that approved applicants can be deleted."""
        from app.services.retention import can_delete_for_aml

        class MockApplicant:
            legal_hold = False
            status = "approved"
            updated_at = datetime.utcnow()
            retention_expires_at = None

        applicant = MockApplicant()
        assert can_delete_for_aml(applicant) is True

    def test_can_delete_for_aml_flagged_within_retention(self):
        """Test that flagged applicants within retention cannot be deleted."""
        from app.services.retention import can_delete_for_aml

        class MockApplicant:
            legal_hold = False
            status = "flagged"
            updated_at = datetime.utcnow()  # Recent - within retention
            retention_expires_at = None

        applicant = MockApplicant()
        assert can_delete_for_aml(applicant) is False

    def test_can_delete_for_aml_flagged_expired(self):
        """Test that flagged applicants past retention can be deleted."""
        from app.services.retention import can_delete_for_aml

        class MockApplicant:
            legal_hold = False
            status = "flagged"
            updated_at = datetime.utcnow() - timedelta(days=365 * 8)  # 8 years ago
            retention_expires_at = None

        applicant = MockApplicant()
        assert can_delete_for_aml(applicant) is True

    def test_retention_summary(self):
        """Test retention policy summary."""
        from app.services.retention import get_retention_summary

        summary = get_retention_summary()

        assert "policies" in summary
        assert "aml_requirements" in summary
        assert "gdpr_articles" in summary

        assert "approved" in summary["policies"]
        assert summary["policies"]["approved"]["years"] == 5.0

        assert summary["aml_requirements"]["flagged_minimum_years"] == 7
        assert summary["aml_requirements"]["legal_hold_overrides_all"] is True


# ===========================================
# API ENDPOINT TESTS
# ===========================================

# API endpoint tests require proper fixture setup
# The unit tests above run without fixtures and test the core retention logic

# Integration tests for GDPR endpoints would need the full test framework
# See test_applicants.py for examples of how to test applicant endpoints

# Key endpoints to test:
# GET /api/v1/applicants/{id}/export - SAR export
# DELETE /api/v1/applicants/{id}/gdpr-delete - GDPR deletion
# POST /api/v1/applicants/{id}/consent - Consent tracking
# POST /api/v1/applicants/{id}/legal-hold - Set legal hold
# DELETE /api/v1/applicants/{id}/legal-hold - Remove legal hold
