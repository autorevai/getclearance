"""
Get Clearance - Full Applicant Flow Integration Tests
======================================================
End-to-end tests for complete KYC verification workflow.

Tests the full applicant lifecycle:
1. Create applicant
2. Upload document
3. Run screening
4. Generate risk summary
5. Review and approve/reject

NOTE: These tests require PostgreSQL because the models use PostgreSQL-specific
types (JSONB, ARRAY). They are skipped when running with SQLite.
"""

import pytest

# Skip all tests in this module - requires PostgreSQL
pytestmark = pytest.mark.skip(reason="Requires PostgreSQL (models use JSONB/ARRAY types)")
from datetime import date, datetime
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4, UUID

from httpx import AsyncClient


# ===========================================
# APPLICANT CREATION FLOW
# ===========================================

class TestApplicantCreationFlow:
    """Test applicant creation and initial setup."""

    @pytest.mark.asyncio
    async def test_create_applicant_success(self, db_with_data):
        """Create new applicant with valid data."""
        from app.models import Applicant, Tenant
        from sqlalchemy import select

        # Get test tenant
        result = await db_with_data.execute(select(Tenant))
        tenant = result.scalar_one()

        # Create applicant
        applicant = Applicant(
            tenant_id=tenant.id,
            external_id="TEST-001",
            email="newuser@example.com",
            first_name="Jane",
            last_name="Smith",
            date_of_birth=date(1985, 6, 15),
            nationality="GBR",
            country_of_residence="GBR",
            status="pending",
        )
        db_with_data.add(applicant)
        await db_with_data.commit()

        # Verify creation
        result = await db_with_data.execute(
            select(Applicant).where(Applicant.external_id == "TEST-001")
        )
        created = result.scalar_one()

        assert created.first_name == "Jane"
        assert created.last_name == "Smith"
        assert created.status == "pending"
        assert created.full_name == "Jane Smith"

    @pytest.mark.asyncio
    async def test_create_applicant_with_flags(self, db_with_data):
        """Create applicant with initial risk flags."""
        from app.models import Applicant, Tenant
        from sqlalchemy import select

        result = await db_with_data.execute(select(Tenant))
        tenant = result.scalar_one()

        applicant = Applicant(
            tenant_id=tenant.id,
            external_id="HIGH-RISK-001",
            email="risky@example.com",
            first_name="High",
            last_name="Risk",
            status="pending",
            risk_score=75,
            flags=["high_risk_country", "adverse_media"],
        )
        db_with_data.add(applicant)
        await db_with_data.commit()

        result = await db_with_data.execute(
            select(Applicant).where(Applicant.external_id == "HIGH-RISK-001")
        )
        created = result.scalar_one()

        assert created.risk_score == 75
        assert "high_risk_country" in created.flags
        assert "adverse_media" in created.flags
        assert created.risk_level == "high"

    @pytest.mark.asyncio
    async def test_applicant_idempotency(self, db_with_data):
        """Creating applicant with same external_id returns existing."""
        from app.models import Applicant, Tenant
        from sqlalchemy import select

        result = await db_with_data.execute(select(Tenant))
        tenant = result.scalar_one()

        # Create first applicant
        applicant1 = Applicant(
            tenant_id=tenant.id,
            external_id="IDEM-001",
            email="first@example.com",
            first_name="First",
            last_name="User",
            status="pending",
        )
        db_with_data.add(applicant1)
        await db_with_data.commit()
        first_id = applicant1.id

        # Query by external_id (simulating idempotent create)
        result = await db_with_data.execute(
            select(Applicant).where(
                Applicant.tenant_id == tenant.id,
                Applicant.external_id == "IDEM-001"
            )
        )
        existing = result.scalar_one_or_none()

        assert existing is not None
        assert existing.id == first_id


# ===========================================
# DOCUMENT UPLOAD FLOW
# ===========================================

class TestDocumentUploadFlow:
    """Test document upload and processing."""

    @pytest.mark.asyncio
    async def test_document_upload_creates_record(self, db_with_data, mock_storage):
        """Document upload creates database record."""
        from app.models import Document, Applicant
        from sqlalchemy import select

        # Get test applicant
        result = await db_with_data.execute(select(Applicant))
        applicant = result.scalar_one()

        # Create document record
        document = Document(
            tenant_id=applicant.tenant_id,
            applicant_id=applicant.id,
            type="passport",
            storage_path=f"{applicant.tenant_id}/applicants/{applicant.id}/passport.jpg",
            file_name="my_passport.jpg",
            mime_type="image/jpeg",
            file_size=1024 * 500,  # 500KB
            status="pending",
        )
        db_with_data.add(document)
        await db_with_data.commit()

        # Verify
        result = await db_with_data.execute(
            select(Document).where(Document.applicant_id == applicant.id)
        )
        doc = result.scalar_one()

        assert doc.type == "passport"
        assert doc.status == "pending"
        assert "passport.jpg" in doc.storage_key

    @pytest.mark.asyncio
    async def test_document_verification_updates_status(self, db_with_data):
        """Document verification updates status and adds checks."""
        from app.models import Document, Applicant
        from sqlalchemy import select

        result = await db_with_data.execute(select(Applicant))
        applicant = result.scalar_one()

        # Create and then "verify" document
        document = Document(
            tenant_id=applicant.tenant_id,
            applicant_id=applicant.id,
            type="passport",
            storage_path=f"test/passport.jpg",
            file_name="passport.jpg",
            mime_type="image/jpeg",
            file_size=1024 * 500,
            status="pending",
        )
        db_with_data.add(document)
        await db_with_data.flush()

        # Simulate verification
        document.status = "verified"
        document.ocr_confidence = 95.5
        document.verification_checks = {
            "mrz_valid": True,
            "expiry_valid": True,
            "face_detected": True,
        }
        document.extracted_data = {
            "document_number": "AB123456",
            "nationality": "USA",
            "date_of_birth": "1990-01-15",
        }
        await db_with_data.commit()

        # Verify
        result = await db_with_data.execute(
            select(Document).where(Document.id == document.id)
        )
        verified_doc = result.scalar_one()

        assert verified_doc.status == "verified"
        assert verified_doc.ocr_confidence == 95.5
        assert verified_doc.verification_checks["mrz_valid"] is True


# ===========================================
# SCREENING FLOW
# ===========================================

class TestScreeningFlow:
    """Test AML/sanctions screening flow."""

    @pytest.mark.asyncio
    async def test_screening_check_clear(self, db_with_data):
        """Screening with no hits marks applicant as clear."""
        from app.models import ScreeningCheck, ScreeningList, Applicant
        from sqlalchemy import select

        result = await db_with_data.execute(select(Applicant))
        applicant = result.scalar_one()

        # Create screening list
        screening_list = ScreeningList(
            source="opensanctions",
            version_id="OS-2024-01-15",
            list_type="sanctions",
            fetched_at=datetime.utcnow(),
        )
        db_with_data.add(screening_list)
        await db_with_data.flush()

        # Create screening check with no hits
        check = ScreeningCheck(
            tenant_id=applicant.tenant_id,
            applicant_id=applicant.id,
            entity_type="individual",
            screened_name=applicant.full_name,
            screened_dob=applicant.date_of_birth,
            screened_country=applicant.nationality,
            check_types=["sanctions", "pep"],
            status="clear",
            hit_count=0,
            started_at=datetime.utcnow(),
            completed_at=datetime.utcnow(),
        )
        db_with_data.add(check)
        await db_with_data.commit()

        # Verify
        result = await db_with_data.execute(
            select(ScreeningCheck).where(ScreeningCheck.applicant_id == applicant.id)
        )
        saved_check = result.scalar_one()

        assert saved_check.status == "clear"
        assert saved_check.hit_count == 0

    @pytest.mark.asyncio
    async def test_screening_check_with_hit(self, db_with_data):
        """Screening with hit creates hit record and updates applicant."""
        from app.models import ScreeningCheck, ScreeningHit, ScreeningList, Applicant
        from sqlalchemy import select, update

        result = await db_with_data.execute(select(Applicant))
        applicant = result.scalar_one()

        # Create screening list
        screening_list = ScreeningList(
            source="opensanctions",
            version_id="OS-2024-01-15",
            list_type="sanctions",
            fetched_at=datetime.utcnow(),
        )
        db_with_data.add(screening_list)
        await db_with_data.flush()

        # Create screening check with hit
        check = ScreeningCheck(
            tenant_id=applicant.tenant_id,
            applicant_id=applicant.id,
            entity_type="individual",
            screened_name=applicant.full_name,
            check_types=["sanctions"],
            status="hit",
            hit_count=1,
            started_at=datetime.utcnow(),
            completed_at=datetime.utcnow(),
        )
        db_with_data.add(check)
        await db_with_data.flush()

        # Create hit record
        hit = ScreeningHit(
            check_id=check.id,
            list_id=screening_list.id,
            list_source="us_ofac_sdn",
            list_version_id="OS-2024-01-15",
            hit_type="sanctions",
            matched_entity_id="ofac-12345",
            matched_name="John Doe",
            confidence=92.5,
            matched_fields=["name", "date_of_birth"],
            match_data={"score": 0.925},
            resolution_status="pending",
        )
        db_with_data.add(hit)

        # Update applicant flags
        await db_with_data.execute(
            update(Applicant)
            .where(Applicant.id == applicant.id)
            .values(
                flags=["sanctions"],
                risk_score=75,
                status="review",
            )
        )
        await db_with_data.commit()

        # Verify check
        result = await db_with_data.execute(
            select(ScreeningCheck).where(ScreeningCheck.applicant_id == applicant.id)
        )
        saved_check = result.scalar_one()
        assert saved_check.status == "hit"
        assert saved_check.hit_count == 1

        # Verify hit
        result = await db_with_data.execute(
            select(ScreeningHit).where(ScreeningHit.check_id == check.id)
        )
        saved_hit = result.scalar_one()
        assert saved_hit.hit_type == "sanctions"
        assert saved_hit.confidence == 92.5
        assert saved_hit.resolution_status == "pending"

        # Verify applicant updated
        result = await db_with_data.execute(
            select(Applicant).where(Applicant.id == applicant.id)
        )
        updated_applicant = result.scalar_one()
        assert "sanctions" in updated_applicant.flags
        assert updated_applicant.risk_score == 75
        assert updated_applicant.status == "review"


# ===========================================
# REVIEW AND APPROVAL FLOW
# ===========================================

class TestReviewApprovalFlow:
    """Test manual review and approval workflow."""

    @pytest.mark.asyncio
    async def test_approve_applicant(self, db_with_data):
        """Approve applicant updates status and records reviewer."""
        from app.models import Applicant, User
        from sqlalchemy import select, update

        result = await db_with_data.execute(select(Applicant))
        applicant = result.scalar_one()

        result = await db_with_data.execute(select(User))
        user = result.scalar_one()

        # Approve applicant
        await db_with_data.execute(
            update(Applicant)
            .where(Applicant.id == applicant.id)
            .values(
                status="approved",
                reviewed_at=datetime.utcnow(),
                reviewed_by=user.id,
            )
        )
        await db_with_data.commit()

        # Verify
        result = await db_with_data.execute(
            select(Applicant).where(Applicant.id == applicant.id)
        )
        approved = result.scalar_one()

        assert approved.status == "approved"
        assert approved.reviewed_at is not None
        assert approved.reviewed_by == user.id

    @pytest.mark.asyncio
    async def test_reject_applicant(self, db_with_data):
        """Reject applicant updates status."""
        from app.models import Applicant, User
        from sqlalchemy import select, update

        result = await db_with_data.execute(select(Applicant))
        applicant = result.scalar_one()

        result = await db_with_data.execute(select(User))
        user = result.scalar_one()

        # Reject applicant
        await db_with_data.execute(
            update(Applicant)
            .where(Applicant.id == applicant.id)
            .values(
                status="rejected",
                reviewed_at=datetime.utcnow(),
                reviewed_by=user.id,
            )
        )
        await db_with_data.commit()

        # Verify
        result = await db_with_data.execute(
            select(Applicant).where(Applicant.id == applicant.id)
        )
        rejected = result.scalar_one()

        assert rejected.status == "rejected"


# ===========================================
# CASE MANAGEMENT FLOW
# ===========================================

class TestCaseManagementFlow:
    """Test case creation and resolution workflow."""

    @pytest.mark.asyncio
    async def test_create_case_for_screening_hit(self, db_with_data):
        """Create case when screening hit needs review."""
        from app.models import Case, CaseNote, Applicant, User
        from sqlalchemy import select

        result = await db_with_data.execute(select(Applicant))
        applicant = result.scalar_one()

        result = await db_with_data.execute(select(User))
        user = result.scalar_one()

        # Create case
        case = Case(
            tenant_id=applicant.tenant_id,
            applicant_id=applicant.id,
            case_number=f"CASE-{datetime.utcnow().strftime('%Y')}-001",
            title="Screening Review: Potential OFAC Match",
            type="sanctions",
            priority="high",
            status="open",
            description="Potential match to OFAC sanctions list",
        )
        db_with_data.add(case)
        await db_with_data.commit()

        # Verify
        result = await db_with_data.execute(
            select(Case).where(Case.applicant_id == applicant.id)
        )
        saved_case = result.scalar_one()

        assert saved_case.type == "sanctions"
        assert saved_case.priority == "high"
        assert saved_case.status == "open"

    @pytest.mark.asyncio
    async def test_add_case_note(self, db_with_data):
        """Add note to case with investigation findings."""
        from app.models import Case, CaseNote, Applicant, User
        from sqlalchemy import select

        result = await db_with_data.execute(select(Applicant))
        applicant = result.scalar_one()

        result = await db_with_data.execute(select(User))
        user = result.scalar_one()

        # Create case
        case = Case(
            tenant_id=applicant.tenant_id,
            applicant_id=applicant.id,
            case_number=f"CASE-{datetime.utcnow().strftime('%Y')}-002",
            title="Screening Review",
            type="sanctions",
            priority="high",
            status="open",
            description="Screening hit review",
        )
        db_with_data.add(case)
        await db_with_data.flush()

        # Add note
        note = CaseNote(
            case_id=case.id,
            author_id=user.id,
            content="Reviewed screening hit. Name match but different DOB. Confirmed false positive.",
        )
        db_with_data.add(note)
        await db_with_data.commit()

        # Verify
        result = await db_with_data.execute(
            select(CaseNote).where(CaseNote.case_id == case.id)
        )
        saved_note = result.scalar_one()

        assert "false positive" in saved_note.content.lower()

    @pytest.mark.asyncio
    async def test_resolve_case(self, db_with_data):
        """Resolve case and update status."""
        from app.models import Case, Applicant, User
        from sqlalchemy import select, update

        result = await db_with_data.execute(select(Applicant))
        applicant = result.scalar_one()

        result = await db_with_data.execute(select(User))
        user = result.scalar_one()

        # Create and resolve case
        case = Case(
            tenant_id=applicant.tenant_id,
            applicant_id=applicant.id,
            case_number=f"CASE-{datetime.utcnow().strftime('%Y')}-003",
            title="Screening Review",
            type="sanctions",
            priority="high",
            status="open",
            description="Screening hit review",
        )
        db_with_data.add(case)
        await db_with_data.flush()

        # Resolve
        case.status = "resolved"
        case.resolution = "cleared"
        case.resolution_notes = "False positive - different person"
        case.resolved_at = datetime.utcnow()
        await db_with_data.commit()

        # Verify
        result = await db_with_data.execute(
            select(Case).where(Case.id == case.id)
        )
        resolved_case = result.scalar_one()

        assert resolved_case.status == "resolved"
        assert resolved_case.resolution == "cleared"


# ===========================================
# COMPLETE FLOW INTEGRATION
# ===========================================

class TestCompleteKYCFlow:
    """Test complete KYC verification flow."""

    @pytest.mark.asyncio
    async def test_happy_path_approval(self, db_with_data, mock_storage, mock_claude):
        """Complete flow: create -> screen (clear) -> verify doc -> approve."""
        from app.models import Applicant, Document, ScreeningCheck, Tenant, User
        from sqlalchemy import select, update

        result = await db_with_data.execute(select(Tenant))
        tenant = result.scalar_one()

        result = await db_with_data.execute(select(User))
        user = result.scalar_one()

        # 1. Create applicant
        applicant = Applicant(
            tenant_id=tenant.id,
            external_id="HAPPY-PATH-001",
            email="happy@example.com",
            first_name="Happy",
            last_name="Customer",
            date_of_birth=date(1992, 3, 20),
            nationality="CAN",
            country_of_residence="CAN",
            status="pending",
        )
        db_with_data.add(applicant)
        await db_with_data.flush()

        # 2. Upload document
        document = Document(
            tenant_id=tenant.id,
            applicant_id=applicant.id,
            type="passport",
            storage_path=f"{tenant.id}/applicants/{applicant.id}/passport.jpg",
            file_name="passport.jpg",
            mime_type="image/jpeg",
            file_size=1024 * 800,
            status="pending",
        )
        db_with_data.add(document)
        await db_with_data.flush()

        # 3. Verify document
        document.status = "verified"
        document.ocr_confidence = 97.0
        document.verification_checks = {"mrz_valid": True, "expiry_valid": True}

        # 4. Run screening (clear result)
        check = ScreeningCheck(
            tenant_id=tenant.id,
            applicant_id=applicant.id,
            entity_type="individual",
            screened_name=applicant.full_name,
            check_types=["sanctions", "pep"],
            status="clear",
            hit_count=0,
            started_at=datetime.utcnow(),
            completed_at=datetime.utcnow(),
        )
        db_with_data.add(check)

        # 5. Auto-approve (no hits, verified docs)
        applicant.status = "approved"
        applicant.reviewed_at = datetime.utcnow()
        applicant.risk_score = 15  # Low risk

        await db_with_data.commit()

        # Verify final state
        result = await db_with_data.execute(
            select(Applicant).where(Applicant.external_id == "HAPPY-PATH-001")
        )
        final_applicant = result.scalar_one()

        assert final_applicant.status == "approved"
        assert final_applicant.risk_score == 15
        assert final_applicant.risk_level == "low"

    @pytest.mark.asyncio
    async def test_hit_path_review(self, db_with_data):
        """Complete flow: create -> screen (hit) -> case -> review -> resolve."""
        from app.models import (
            Applicant, ScreeningCheck, ScreeningHit, ScreeningList, Case, Tenant, User
        )
        from sqlalchemy import select

        result = await db_with_data.execute(select(Tenant))
        tenant = result.scalar_one()

        result = await db_with_data.execute(select(User))
        user = result.scalar_one()

        # 1. Create applicant
        applicant = Applicant(
            tenant_id=tenant.id,
            external_id="HIT-PATH-001",
            email="hit@example.com",
            first_name="Suspicious",
            last_name="Person",
            date_of_birth=date(1975, 8, 10),
            nationality="RUS",
            country_of_residence="USA",
            status="pending",
        )
        db_with_data.add(applicant)
        await db_with_data.flush()

        # 2. Create screening list
        screening_list = ScreeningList(
            source="opensanctions",
            version_id="OS-2024-01-15",
            list_type="sanctions",
            fetched_at=datetime.utcnow(),
        )
        db_with_data.add(screening_list)
        await db_with_data.flush()

        # 3. Run screening (hit found)
        check = ScreeningCheck(
            tenant_id=tenant.id,
            applicant_id=applicant.id,
            entity_type="individual",
            screened_name=applicant.full_name,
            check_types=["sanctions", "pep"],
            status="hit",
            hit_count=1,
            started_at=datetime.utcnow(),
            completed_at=datetime.utcnow(),
        )
        db_with_data.add(check)
        await db_with_data.flush()

        # 4. Create hit
        hit = ScreeningHit(
            check_id=check.id,
            list_id=screening_list.id,
            list_source="us_ofac_sdn",
            list_version_id="OS-2024-01-15",
            hit_type="sanctions",
            matched_entity_id="ofac-99999",
            matched_name="Suspicious Person",
            confidence=88.0,
            matched_fields=["name"],
            match_data={},
            resolution_status="pending",
        )
        db_with_data.add(hit)

        # Update applicant
        applicant.status = "review"
        applicant.flags = ["sanctions"]
        applicant.risk_score = 80

        # 5. Create case for review
        case = Case(
            tenant_id=tenant.id,
            applicant_id=applicant.id,
            case_number=f"CASE-{datetime.utcnow().strftime('%Y')}-004",
            title="OFAC Sanctions Match Review",
            type="sanctions",
            priority="high",
            status="open",
            description="OFAC sanctions match",
        )
        db_with_data.add(case)
        await db_with_data.flush()

        # 6. Resolve hit as false positive
        hit.resolution_status = "confirmed_false"
        hit.resolved_by = user.id
        hit.resolved_at = datetime.utcnow()
        hit.resolution_notes = "Different person - DOB mismatch"

        # 7. Resolve case
        case.status = "resolved"
        case.resolution = "cleared"
        case.resolution_notes = "False positive confirmed"
        case.resolved_at = datetime.utcnow()

        # 8. Approve applicant
        applicant.status = "approved"
        applicant.reviewed_at = datetime.utcnow()
        applicant.reviewed_by = user.id

        await db_with_data.commit()

        # Verify final state
        result = await db_with_data.execute(
            select(Applicant).where(Applicant.external_id == "HIT-PATH-001")
        )
        final_applicant = result.scalar_one()

        assert final_applicant.status == "approved"

        result = await db_with_data.execute(
            select(ScreeningHit).where(ScreeningHit.check_id == check.id)
        )
        final_hit = result.scalar_one()

        assert final_hit.resolution_status == "confirmed_false"

        result = await db_with_data.execute(
            select(Case).where(Case.applicant_id == applicant.id)
        )
        final_case = result.scalar_one()

        assert final_case.status == "resolved"
