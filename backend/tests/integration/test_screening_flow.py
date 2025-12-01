"""
Get Clearance - Screening Flow Integration Tests
=================================================
End-to-end tests for AML/sanctions screening workflow.

Tests:
- Individual and company screening
- Hit classification and resolution
- Fuzzy matching scenarios
- Webhook notifications
- Ongoing monitoring
"""

import pytest
from datetime import date, datetime
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

from app.services.screening import (
    ScreeningService,
    ScreeningResult,
    ScreeningHitResult,
)
from app.services.webhook import (
    webhook_service,
    send_screening_completed_webhook,
    generate_signature,
)


# ===========================================
# SCREENING SERVICE INTEGRATION
# ===========================================

class TestScreeningServiceIntegration:
    """Test screening service end-to-end."""

    @pytest.mark.asyncio
    async def test_screen_clean_individual(self):
        """Screen individual with no matches."""
        service = ScreeningService(
            api_key="test-key",
            api_url="https://api.opensanctions.org/match/default"
        )

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.headers = {"X-OpenSanctions-Version": "2024-01-15"}
        mock_response.json.return_value = {
            "responses": {"q1": {"results": []}}
        }

        with patch.object(service, '_get_client') as mock_get_client:
            mock_client = AsyncMock()
            mock_client.post = AsyncMock(return_value=mock_response)
            mock_get_client.return_value = mock_client

            result = await service.check_individual(
                name="Jane Smith",
                birth_date=date(1992, 5, 15),
                countries=["US"],
            )

        assert result.status == "clear"
        assert result.hits == []
        assert result.list_version_id == "OS-2024-01-15"

    @pytest.mark.asyncio
    async def test_screen_sanctions_hit(self):
        """Screen individual with sanctions match."""
        service = ScreeningService(
            api_key="test-key",
            api_url="https://api.opensanctions.org/match/default"
        )

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.headers = {"X-OpenSanctions-Version": "2024-01-15"}
        mock_response.json.return_value = {
            "responses": {
                "q1": {
                    "results": [
                        {
                            "id": "ofac-12345",
                            "caption": "Sanctioned Person",
                            "score": 0.95,
                            "datasets": ["us_ofac_sdn"],
                            "properties": {
                                "name": ["Sanctioned Person", "S. Person"],
                                "birthDate": ["1985-03-20"],
                                "nationality": ["ru"],
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
                name="Sanctioned Person",
                birth_date=date(1985, 3, 20),
                countries=["RU"],
            )

        assert result.status == "hit"
        assert len(result.hits) == 1

        hit = result.hits[0]
        assert hit.hit_type == "sanctions"
        assert hit.list_source == "us_ofac_sdn"
        assert hit.confidence == 95.0
        assert hit.matched_entity_id == "ofac-12345"

    @pytest.mark.asyncio
    async def test_screen_pep_hit(self):
        """Screen individual with PEP match."""
        service = ScreeningService(
            api_key="test-key",
            api_url="https://api.opensanctions.org/match/default"
        )

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.headers = {"X-OpenSanctions-Version": "2024-01-15"}
        mock_response.json.return_value = {
            "responses": {
                "q1": {
                    "results": [
                        {
                            "id": "pep-99999",
                            "caption": "Political Leader",
                            "score": 0.88,
                            "datasets": ["everypolitician"],
                            "properties": {
                                "name": ["Political Leader"],
                                "birthDate": ["1960-07-04"],
                                "position": ["Prime Minister"],
                                "topics": ["role.pep.national"],
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
                name="Political Leader",
                birth_date=date(1960, 7, 4),
            )

        assert result.status == "hit"
        assert len(result.hits) == 1

        hit = result.hits[0]
        assert hit.hit_type == "pep"
        assert hit.pep_tier == 1  # National level
        assert hit.pep_position == "Prime Minister"
        assert "pep" in hit.categories

    @pytest.mark.asyncio
    async def test_screen_multiple_hits(self):
        """Screen individual with multiple hits."""
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
                            "id": "hit-1",
                            "caption": "Person One",
                            "score": 0.92,
                            "datasets": ["us_ofac_sdn"],
                            "properties": {"name": ["Person"], "topics": ["sanction"]},
                        },
                        {
                            "id": "hit-2",
                            "caption": "Person Two",
                            "score": 0.78,
                            "datasets": ["eu_fsf"],
                            "properties": {"name": ["Person"], "topics": ["sanction"]},
                        },
                    ]
                }
            }
        }

        with patch.object(service, '_get_client') as mock_get_client:
            mock_client = AsyncMock()
            mock_client.post = AsyncMock(return_value=mock_response)
            mock_get_client.return_value = mock_client

            result = await service.check_individual(name="Person")

        assert result.status == "hit"
        assert len(result.hits) == 2

        # Verify both hits are captured
        confidences = [h.confidence for h in result.hits]
        assert 92.0 in confidences
        assert 78.0 in confidences


# ===========================================
# COMPANY SCREENING INTEGRATION
# ===========================================

class TestCompanyScreeningIntegration:
    """Test company screening end-to-end."""

    @pytest.mark.asyncio
    async def test_screen_clean_company(self):
        """Screen company with no matches."""
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

            result = await service.check_company(
                name="Acme Corporation",
                jurisdiction="US",
            )

        assert result.status == "clear"

    @pytest.mark.asyncio
    async def test_screen_sanctioned_company(self):
        """Screen company with sanctions match."""
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
                            "id": "company-sanctioned",
                            "caption": "Bad Company LLC",
                            "score": 0.91,
                            "datasets": ["us_ofac_sdn", "eu_fsf"],
                            "properties": {
                                "name": ["Bad Company LLC", "Bad Co"],
                                "country": ["ru"],
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
                name="Bad Company LLC",
                jurisdiction="RU",
            )

        assert result.status == "hit"
        assert len(result.hits) == 1
        assert result.hits[0].hit_type == "sanctions"


# ===========================================
# FUZZY MATCHING SCENARIOS
# ===========================================

class TestFuzzyMatchingScenarios:
    """Test fuzzy matching confidence scoring."""

    @pytest.mark.asyncio
    async def test_exact_name_match_high_confidence(self):
        """Exact name match should have high confidence."""
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
                            "id": "exact-match",
                            "caption": "John Doe",
                            "score": 0.98,  # Very high confidence
                            "datasets": ["us_ofac_sdn"],
                            "properties": {
                                "name": ["John Doe"],
                                "birthDate": ["1990-01-15"],
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
        assert result.hits[0].confidence >= 90

    @pytest.mark.asyncio
    async def test_partial_name_match_medium_confidence(self):
        """Partial name match should have medium confidence."""
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
                            "id": "partial-match",
                            "caption": "John Smith",  # Similar first name
                            "score": 0.65,
                            "datasets": ["us_ofac_sdn"],
                            "properties": {
                                "name": ["John Smith"],
                                "birthDate": ["1990-01-15"],
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
        assert 60 <= result.hits[0].confidence < 90

    @pytest.mark.asyncio
    async def test_name_alias_match(self):
        """Name alias should be matched."""
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
                            "id": "alias-match",
                            "caption": "Jonathan Doe",
                            "score": 0.82,
                            "datasets": ["us_ofac_sdn"],
                            "properties": {
                                "name": ["Jonathan Doe", "John Doe", "J. Doe"],  # Aliases
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

            result = await service.check_individual(name="John Doe")

        assert result.status == "hit"
        assert len(result.hits) == 1


# ===========================================
# SCREENING WITH WEBHOOKS
# ===========================================

class TestScreeningWithWebhooks:
    """Test screening workflow with webhook notifications."""

    @pytest.mark.asyncio
    async def test_send_screening_completed_webhook_clear(self, mock_httpx_success):
        """Send webhook on clear screening result."""
        tenant_id = uuid4()
        applicant_id = uuid4()
        check_id = uuid4()

        with patch("app.services.webhook.get_db_context") as mock_db_ctx:
            mock_db = AsyncMock()

            # Mock tenant with webhook config
            mock_tenant = MagicMock()
            mock_tenant.settings = {
                "webhook": {
                    "enabled": True,
                    "url": "https://example.com/webhook",
                    "secret": "test-secret",
                    "events": ["screening.completed"],
                }
            }

            mock_result = MagicMock()
            mock_result.scalar_one_or_none.return_value = mock_tenant
            mock_db.execute = AsyncMock(return_value=mock_result)
            mock_db.commit = AsyncMock()

            mock_db_ctx.return_value.__aenter__ = AsyncMock(return_value=mock_db)
            mock_db_ctx.return_value.__aexit__ = AsyncMock(return_value=None)

            with patch("app.services.webhook.WebhookService._enqueue_delivery") as mock_enqueue:
                mock_enqueue.return_value = None

                delivery_id = await send_screening_completed_webhook(
                    tenant_id=tenant_id,
                    applicant_id=applicant_id,
                    external_id="EXT-001",
                    screening_check_id=check_id,
                    status="clear",
                    hit_count=0,
                    check_types=["sanctions", "pep"],
                    list_version="OS-2024-01-15",
                )

        # Webhook should be queued
        assert delivery_id is not None or mock_enqueue.called

    @pytest.mark.asyncio
    async def test_send_screening_completed_webhook_hit(self, mock_httpx_success):
        """Send webhook on screening hit."""
        tenant_id = uuid4()
        applicant_id = uuid4()
        check_id = uuid4()

        with patch("app.services.webhook.get_db_context") as mock_db_ctx:
            mock_db = AsyncMock()

            mock_tenant = MagicMock()
            mock_tenant.settings = {
                "webhook": {
                    "enabled": True,
                    "url": "https://example.com/webhook",
                    "secret": "test-secret",
                    "events": ["screening.completed"],
                }
            }

            mock_result = MagicMock()
            mock_result.scalar_one_or_none.return_value = mock_tenant
            mock_db.execute = AsyncMock(return_value=mock_result)
            mock_db.commit = AsyncMock()

            mock_db_ctx.return_value.__aenter__ = AsyncMock(return_value=mock_db)
            mock_db_ctx.return_value.__aexit__ = AsyncMock(return_value=None)

            with patch("app.services.webhook.WebhookService._enqueue_delivery") as mock_enqueue:
                mock_enqueue.return_value = None

                delivery_id = await send_screening_completed_webhook(
                    tenant_id=tenant_id,
                    applicant_id=applicant_id,
                    external_id="EXT-002",
                    screening_check_id=check_id,
                    status="hit",
                    hit_count=2,
                    check_types=["sanctions"],
                    list_version="OS-2024-01-15",
                )


# ===========================================
# HIT RESOLUTION FLOW
# ===========================================

class TestHitResolutionFlow:
    """Test screening hit resolution workflow."""

    @pytest.mark.asyncio
    async def test_resolve_hit_as_true_positive(self, db_with_data):
        """Resolve hit as true positive (confirmed match)."""
        from app.models import ScreeningCheck, ScreeningHit, ScreeningList, Applicant, User
        from sqlalchemy import select

        result = await db_with_data.execute(select(Applicant))
        applicant = result.scalar_one()

        result = await db_with_data.execute(select(User))
        user = result.scalar_one()

        # Create screening list
        screening_list = ScreeningList(
            source="opensanctions",
            version_id="OS-2024-01-15",
            list_type="sanctions",
            fetched_at=datetime.utcnow(),
        )
        db_with_data.add(screening_list)
        await db_with_data.flush()

        # Create check and hit
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

        hit = ScreeningHit(
            check_id=check.id,
            list_id=screening_list.id,
            list_source="us_ofac_sdn",
            list_version_id="OS-2024-01-15",
            hit_type="sanctions",
            matched_entity_id="ofac-confirmed",
            matched_name=applicant.full_name,
            confidence=96.0,
            matched_fields=["name", "date_of_birth", "nationality"],
            match_data={},
            resolution_status="pending",
        )
        db_with_data.add(hit)
        await db_with_data.flush()

        # Resolve as true positive
        hit.resolution_status = "confirmed_true"
        hit.resolved_by = user.id
        hit.resolved_at = datetime.utcnow()
        hit.resolution_notes = "Identity confirmed. Same person on sanctions list."

        await db_with_data.commit()

        # Verify
        result = await db_with_data.execute(
            select(ScreeningHit).where(ScreeningHit.id == hit.id)
        )
        resolved_hit = result.scalar_one()

        assert resolved_hit.resolution_status == "confirmed_true"
        assert resolved_hit.resolved_by is not None

    @pytest.mark.asyncio
    async def test_resolve_hit_as_false_positive(self, db_with_data):
        """Resolve hit as false positive (different person)."""
        from app.models import ScreeningCheck, ScreeningHit, ScreeningList, Applicant, User
        from sqlalchemy import select

        result = await db_with_data.execute(select(Applicant))
        applicant = result.scalar_one()

        result = await db_with_data.execute(select(User))
        user = result.scalar_one()

        # Create screening list
        screening_list = ScreeningList(
            source="opensanctions",
            version_id="OS-2024-01-15",
            list_type="sanctions",
            fetched_at=datetime.utcnow(),
        )
        db_with_data.add(screening_list)
        await db_with_data.flush()

        # Create check and hit
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

        hit = ScreeningHit(
            check_id=check.id,
            list_id=screening_list.id,
            list_source="us_ofac_sdn",
            list_version_id="OS-2024-01-15",
            hit_type="sanctions",
            matched_entity_id="ofac-false",
            matched_name="John Smith",  # Similar but different name
            confidence=68.0,
            matched_fields=["name"],
            match_data={},
            resolution_status="pending",
        )
        db_with_data.add(hit)
        await db_with_data.flush()

        # Resolve as false positive
        hit.resolution_status = "confirmed_false"
        hit.resolved_by = user.id
        hit.resolved_at = datetime.utcnow()
        hit.resolution_notes = "Different person. Name match but DOB and nationality differ."

        await db_with_data.commit()

        # Verify
        result = await db_with_data.execute(
            select(ScreeningHit).where(ScreeningHit.id == hit.id)
        )
        resolved_hit = result.scalar_one()

        assert resolved_hit.resolution_status == "confirmed_false"


# ===========================================
# LIST VERSION TRACKING
# ===========================================

class TestListVersionTracking:
    """Test screening list version tracking for audits."""

    @pytest.mark.asyncio
    async def test_list_version_recorded(self, db_with_data):
        """Screening records exact list version used."""
        from app.models import ScreeningCheck, ScreeningList, Applicant
        from sqlalchemy import select

        result = await db_with_data.execute(select(Applicant))
        applicant = result.scalar_one()

        # Create screening list with specific version
        screening_list = ScreeningList(
            source="opensanctions",
            version_id="OS-2024-01-15-001",
            list_type="sanctions",
            fetched_at=datetime.utcnow(),
        )
        db_with_data.add(screening_list)
        await db_with_data.flush()

        # Create check referencing that list
        check = ScreeningCheck(
            tenant_id=applicant.tenant_id,
            applicant_id=applicant.id,
            entity_type="individual",
            screened_name=applicant.full_name,
            check_types=["sanctions"],
            status="clear",
            hit_count=0,
            started_at=datetime.utcnow(),
            completed_at=datetime.utcnow(),
        )
        db_with_data.add(check)
        await db_with_data.commit()

        # Verify list version is queryable
        result = await db_with_data.execute(
            select(ScreeningList).where(
                ScreeningList.version_id == "OS-2024-01-15-001"
            )
        )
        saved_list = result.scalar_one()

        assert saved_list.source == "opensanctions"
        assert saved_list.fetched_at is not None
