"""
Get Clearance - Worker Tests
=============================
Unit tests for ARQ background workers.

Tests:
- Screening worker job processing
- Webhook delivery and retry logic
- Worker configuration
- Error handling and retries
"""

import pytest
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4, UUID

from app.workers.config import get_redis_settings, get_retry_delay, WorkerSettings
from app.services.webhook import (
    WebhookService,
    generate_signature,
    generate_timestamp,
    create_signed_headers,
    RETRY_DELAYS,
    MAX_ATTEMPTS,
)


# ===========================================
# WORKER CONFIG TESTS
# ===========================================

class TestWorkerConfig:
    """Test ARQ worker configuration."""

    def test_get_redis_settings_parses_url(self):
        """Parse Redis URL into RedisSettings."""
        with patch("app.workers.config.settings") as mock_settings:
            mock_settings.redis_url_str = "redis://localhost:6379/0"

            settings = get_redis_settings()

            assert settings.host == "localhost"
            assert settings.port == 6379
            assert settings.database == 0
            assert settings.password is None

    def test_get_redis_settings_with_password(self):
        """Parse Redis URL with password."""
        with patch("app.workers.config.settings") as mock_settings:
            mock_settings.redis_url_str = "redis://user:secretpass@redis.example.com:6380/1"

            settings = get_redis_settings()

            assert settings.host == "redis.example.com"
            assert settings.port == 6380
            assert settings.database == 1
            assert settings.password == "secretpass"

    def test_get_redis_settings_ssl(self):
        """Parse Redis SSL URL."""
        with patch("app.workers.config.settings") as mock_settings:
            mock_settings.redis_url_str = "rediss://localhost:6379/0"

            settings = get_redis_settings()

            assert settings.host == "localhost"

    def test_retry_delay_exponential_backoff(self):
        """Retry delay increases exponentially."""
        delay0 = get_retry_delay(0)
        delay1 = get_retry_delay(1)
        delay2 = get_retry_delay(2)

        assert delay0 == 10  # 10 * 2^0 = 10
        assert delay1 == 20  # 10 * 2^1 = 20
        assert delay2 == 40  # 10 * 2^2 = 40

    def test_retry_delay_custom_base(self):
        """Custom base delay works."""
        delay = get_retry_delay(2, base_delay=5)
        assert delay == 20  # 5 * 2^2 = 20

    def test_worker_settings_functions_list(self):
        """Worker settings includes all worker functions."""
        functions = WorkerSettings.functions

        assert any("screening_worker" in f for f in functions)
        assert any("document_worker" in f for f in functions)
        assert any("ai_worker" in f for f in functions)
        assert any("webhook_worker" in f for f in functions)

    def test_worker_settings_job_timeout(self):
        """Worker has appropriate job timeout."""
        timeout = WorkerSettings.job_timeout
        assert timeout >= timedelta(seconds=60)  # At least 1 minute
        assert timeout <= timedelta(seconds=600)  # At most 10 minutes

    def test_worker_settings_max_tries(self):
        """Worker has retry configuration."""
        assert WorkerSettings.max_tries >= 1
        assert WorkerSettings.max_tries <= 5


# ===========================================
# WEBHOOK SIGNATURE TESTS
# ===========================================

class TestWebhookSignature:
    """Test webhook HMAC signature generation."""

    def test_generate_signature_deterministic(self):
        """Signature is deterministic for same input."""
        payload = '{"event": "test"}'
        secret = "test-secret"

        sig1 = generate_signature(payload, secret)
        sig2 = generate_signature(payload, secret)

        assert sig1 == sig2

    def test_generate_signature_varies_with_payload(self):
        """Different payloads produce different signatures."""
        secret = "test-secret"

        sig1 = generate_signature('{"event": "test1"}', secret)
        sig2 = generate_signature('{"event": "test2"}', secret)

        assert sig1 != sig2

    def test_generate_signature_varies_with_secret(self):
        """Different secrets produce different signatures."""
        payload = '{"event": "test"}'

        sig1 = generate_signature(payload, "secret1")
        sig2 = generate_signature(payload, "secret2")

        assert sig1 != sig2

    def test_generate_signature_is_hex(self):
        """Signature is hex-encoded."""
        sig = generate_signature("test", "secret")

        # Should be valid hex
        int(sig, 16)
        # SHA256 hex is 64 characters
        assert len(sig) == 64

    def test_generate_timestamp(self):
        """Timestamp is Unix epoch."""
        ts = generate_timestamp()

        assert isinstance(ts, int)
        # Should be roughly current time
        now = int(datetime.utcnow().timestamp())
        assert abs(ts - now) < 5  # Within 5 seconds


class TestWebhookSignedHeaders:
    """Test webhook signed headers creation."""

    def test_create_signed_headers_includes_required(self):
        """Headers include all required fields."""
        payload = '{"event": "test"}'
        secret = "test-secret"

        headers = create_signed_headers(payload, secret)

        assert "Content-Type" in headers
        assert headers["Content-Type"] == "application/json"
        assert "X-Webhook-Signature" in headers
        assert "X-Webhook-Timestamp" in headers
        assert "X-GetClearance-Signature" in headers
        assert "User-Agent" in headers

    def test_create_signed_headers_github_style(self):
        """Includes GitHub-style signature header."""
        headers = create_signed_headers('{"test": true}', "secret")

        assert headers["X-GetClearance-Signature"].startswith("sha256=")


# ===========================================
# WEBHOOK SERVICE TESTS
# ===========================================

class TestWebhookService:
    """Test webhook service functionality."""

    @pytest.mark.asyncio
    async def test_get_tenant_webhook_config_enabled(self):
        """Get webhook config for tenant with webhooks enabled."""
        service = WebhookService()

        mock_db = AsyncMock()
        mock_tenant = MagicMock()
        mock_tenant.settings = {
            "webhook": {
                "enabled": True,
                "url": "https://example.com/webhook",
                "secret": "test-secret",
                "events": ["applicant.reviewed"],
            }
        }

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_tenant
        mock_db.execute = AsyncMock(return_value=mock_result)

        config = await service.get_tenant_webhook_config(mock_db, uuid4())

        assert config is not None
        assert config["enabled"] is True
        assert config["url"] == "https://example.com/webhook"

    @pytest.mark.asyncio
    async def test_get_tenant_webhook_config_disabled(self):
        """Return None for tenant with webhooks disabled."""
        service = WebhookService()

        mock_db = AsyncMock()
        mock_tenant = MagicMock()
        mock_tenant.settings = {
            "webhook": {
                "enabled": False,
                "url": "https://example.com/webhook",
            }
        }

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_tenant
        mock_db.execute = AsyncMock(return_value=mock_result)

        config = await service.get_tenant_webhook_config(mock_db, uuid4())

        assert config is None

    @pytest.mark.asyncio
    async def test_get_tenant_webhook_config_not_configured(self):
        """Return None for tenant without webhook config."""
        service = WebhookService()

        mock_db = AsyncMock()
        mock_tenant = MagicMock()
        mock_tenant.settings = {}  # No webhook config

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_tenant
        mock_db.execute = AsyncMock(return_value=mock_result)

        config = await service.get_tenant_webhook_config(mock_db, uuid4())

        assert config is None


# ===========================================
# WEBHOOK DELIVERY TESTS
# ===========================================

class TestWebhookDelivery:
    """Test webhook delivery logic."""

    @pytest.mark.asyncio
    async def test_deliver_success(self, mock_httpx_success):
        """Successful webhook delivery returns True."""
        service = WebhookService()
        delivery_id = uuid4()

        with patch.object(service, 'get_pending_deliveries') as mock_get:
            # Mock getting delivery record
            with patch("app.services.webhook.get_db_context") as mock_db_ctx:
                mock_db = AsyncMock()
                mock_result = MagicMock()
                mock_result.fetchone.return_value = MagicMock(
                    webhook_url="https://example.com/webhook",
                    payload='{"event": "test"}',
                )
                mock_db.execute = AsyncMock(return_value=mock_result)
                mock_db_ctx.return_value.__aenter__ = AsyncMock(return_value=mock_db)
                mock_db_ctx.return_value.__aexit__ = AsyncMock(return_value=None)

                success, status, error = await service.deliver(
                    delivery_id=delivery_id,
                    secret="test-secret",
                )

        assert success is True
        assert status == 200
        assert error is None

    @pytest.mark.asyncio
    async def test_deliver_failure_4xx(self, mock_httpx_failure):
        """4xx errors are permanent failures."""
        service = WebhookService()
        delivery_id = uuid4()

        with patch("app.services.webhook.get_db_context") as mock_db_ctx:
            mock_db = AsyncMock()
            mock_result = MagicMock()
            mock_result.fetchone.return_value = MagicMock(
                webhook_url="https://example.com/webhook",
                payload='{"event": "test"}',
            )
            mock_db.execute = AsyncMock(return_value=mock_result)
            mock_db_ctx.return_value.__aenter__ = AsyncMock(return_value=mock_db)
            mock_db_ctx.return_value.__aexit__ = AsyncMock(return_value=None)

            with patch("httpx.AsyncClient") as mock_client:
                mock_response = MagicMock()
                mock_response.status_code = 400
                mock_response.text = "Bad Request"

                instance = AsyncMock()
                instance.post = AsyncMock(return_value=mock_response)
                mock_client.return_value.__aenter__ = AsyncMock(return_value=instance)
                mock_client.return_value.__aexit__ = AsyncMock(return_value=None)

                success, status, error = await service.deliver(
                    delivery_id=delivery_id,
                    secret="test-secret",
                )

        assert success is False
        assert status == 400

    @pytest.mark.asyncio
    async def test_deliver_timeout(self):
        """Timeout errors are retryable."""
        import httpx

        service = WebhookService()
        delivery_id = uuid4()

        with patch("app.services.webhook.get_db_context") as mock_db_ctx:
            mock_db = AsyncMock()
            mock_result = MagicMock()
            mock_result.fetchone.return_value = MagicMock(
                webhook_url="https://example.com/webhook",
                payload='{"event": "test"}',
            )
            mock_db.execute = AsyncMock(return_value=mock_result)
            mock_db_ctx.return_value.__aenter__ = AsyncMock(return_value=mock_db)
            mock_db_ctx.return_value.__aexit__ = AsyncMock(return_value=None)

            with patch("httpx.AsyncClient") as mock_client:
                instance = AsyncMock()
                instance.post = AsyncMock(side_effect=httpx.TimeoutException("Timeout"))
                mock_client.return_value.__aenter__ = AsyncMock(return_value=instance)
                mock_client.return_value.__aexit__ = AsyncMock(return_value=None)

                success, status, error = await service.deliver(
                    delivery_id=delivery_id,
                    secret="test-secret",
                )

        assert success is False
        assert status is None
        assert "timed out" in error.lower()


# ===========================================
# WEBHOOK STATUS UPDATE TESTS
# ===========================================

class TestWebhookStatusUpdate:
    """Test webhook delivery status updates."""

    @pytest.mark.asyncio
    async def test_update_delivery_status_success(self):
        """Update status to delivered on success."""
        service = WebhookService()
        delivery_id = uuid4()

        with patch("app.services.webhook.get_db_context") as mock_db_ctx:
            mock_db = AsyncMock()
            mock_db.execute = AsyncMock()
            mock_db.commit = AsyncMock()
            mock_db_ctx.return_value.__aenter__ = AsyncMock(return_value=mock_db)
            mock_db_ctx.return_value.__aexit__ = AsyncMock(return_value=None)

            await service.update_delivery_status(
                delivery_id=delivery_id,
                success=True,
                http_status=200,
                error_message=None,
                attempt_count=1,
            )

            mock_db.execute.assert_called()
            mock_db.commit.assert_called()

    @pytest.mark.asyncio
    async def test_update_delivery_status_max_retries(self):
        """Update status to failed after max retries."""
        service = WebhookService()
        delivery_id = uuid4()

        with patch("app.services.webhook.get_db_context") as mock_db_ctx:
            mock_db = AsyncMock()
            mock_db.execute = AsyncMock()
            mock_db.commit = AsyncMock()
            mock_db_ctx.return_value.__aenter__ = AsyncMock(return_value=mock_db)
            mock_db_ctx.return_value.__aexit__ = AsyncMock(return_value=None)

            await service.update_delivery_status(
                delivery_id=delivery_id,
                success=False,
                http_status=500,
                error_message="Server error",
                attempt_count=MAX_ATTEMPTS,  # Max retries exhausted
            )

            mock_db.execute.assert_called()

    @pytest.mark.asyncio
    async def test_update_delivery_status_schedule_retry(self):
        """Schedule retry after failed attempt."""
        service = WebhookService()
        delivery_id = uuid4()

        with patch("app.services.webhook.get_db_context") as mock_db_ctx:
            mock_db = AsyncMock()
            mock_db.execute = AsyncMock()
            mock_db.commit = AsyncMock()
            mock_db_ctx.return_value.__aenter__ = AsyncMock(return_value=mock_db)
            mock_db_ctx.return_value.__aexit__ = AsyncMock(return_value=None)

            await service.update_delivery_status(
                delivery_id=delivery_id,
                success=False,
                http_status=500,
                error_message="Server error",
                attempt_count=1,  # First attempt, can retry
            )

            mock_db.execute.assert_called()


# ===========================================
# WEBHOOK RETRY CONFIGURATION
# ===========================================

class TestWebhookRetryConfig:
    """Test webhook retry configuration."""

    def test_retry_delays_match_sumsub(self):
        """Retry delays follow Sumsub pattern: 0s, 30s, 5min."""
        assert RETRY_DELAYS == [0, 30, 300]

    def test_max_attempts(self):
        """Max attempts is 3 (matching Sumsub)."""
        assert MAX_ATTEMPTS == 3


# ===========================================
# SCREENING WORKER TESTS
# ===========================================

class TestScreeningWorker:
    """Test screening background worker."""

    @pytest.mark.asyncio
    async def test_run_screening_check_success(self):
        """Successful screening check job."""
        from app.workers.screening_worker import run_screening_check
        from app.services.screening import ScreeningResult, ScreeningHitResult

        # Mock context
        ctx = {"logger": MagicMock()}

        # Mock database context
        with patch("app.workers.screening_worker.get_db_context") as mock_db_ctx:
            mock_db = AsyncMock()

            # Mock applicant fetch
            mock_applicant = MagicMock()
            mock_applicant.id = uuid4()
            mock_applicant.tenant_id = uuid4()
            mock_applicant.full_name = "John Doe"
            mock_applicant.date_of_birth = None
            mock_applicant.nationality = "USA"
            mock_applicant.country_of_residence = "USA"
            mock_applicant.flags = []
            mock_applicant.risk_score = 0

            mock_result = MagicMock()
            mock_result.scalar_one_or_none.return_value = mock_applicant
            mock_db.execute = AsyncMock(return_value=mock_result)
            mock_db.add = MagicMock()
            mock_db.flush = AsyncMock()
            mock_db.commit = AsyncMock()
            mock_db.rollback = AsyncMock()

            mock_db_ctx.return_value.__aenter__ = AsyncMock(return_value=mock_db)
            mock_db_ctx.return_value.__aexit__ = AsyncMock(return_value=None)

            # Mock screening service
            with patch("app.workers.screening_worker.screening_service") as mock_screening:
                mock_screening.check_individual = AsyncMock(return_value=ScreeningResult(
                    status="clear",
                    list_version_id="OS-2024-01-01",
                    hits=[],
                ))

                result = await run_screening_check(
                    ctx=ctx,
                    applicant_id=str(uuid4()),
                )

        assert result["status"] == "success"
        assert result["screening_status"] == "clear"
        assert result["hit_count"] == 0

    @pytest.mark.asyncio
    async def test_run_screening_check_with_hits(self):
        """Screening check with hits creates case."""
        from app.workers.screening_worker import run_screening_check
        from app.services.screening import ScreeningResult, ScreeningHitResult

        ctx = {"logger": MagicMock()}

        with patch("app.workers.screening_worker.get_db_context") as mock_db_ctx:
            mock_db = AsyncMock()

            mock_applicant = MagicMock()
            mock_applicant.id = uuid4()
            mock_applicant.tenant_id = uuid4()
            mock_applicant.full_name = "John Doe"
            mock_applicant.date_of_birth = None
            mock_applicant.nationality = "USA"
            mock_applicant.country_of_residence = "USA"
            mock_applicant.flags = []
            mock_applicant.risk_score = 0

            mock_result = MagicMock()
            mock_result.scalar_one_or_none.return_value = mock_applicant
            mock_db.execute = AsyncMock(return_value=mock_result)
            mock_db.add = MagicMock()
            mock_db.flush = AsyncMock()
            mock_db.commit = AsyncMock()
            mock_db.rollback = AsyncMock()

            mock_db_ctx.return_value.__aenter__ = AsyncMock(return_value=mock_db)
            mock_db_ctx.return_value.__aexit__ = AsyncMock(return_value=None)

            with patch("app.workers.screening_worker.screening_service") as mock_screening:
                hit = ScreeningHitResult(
                    hit_type="sanctions",
                    matched_entity_id="hit-123",
                    matched_name="John Doe",
                    confidence=95.0,
                    matched_fields=["name"],
                    list_source="us_ofac_sdn",
                    list_version_id="OS-2024-01-01",
                    match_data={},
                )

                mock_screening.check_individual = AsyncMock(return_value=ScreeningResult(
                    status="hit",
                    list_version_id="OS-2024-01-01",
                    hits=[hit],
                ))

                result = await run_screening_check(
                    ctx=ctx,
                    applicant_id=str(uuid4()),
                )

        assert result["status"] == "success"
        assert result["screening_status"] == "hit"
        assert result["hit_count"] == 1

    @pytest.mark.asyncio
    async def test_run_screening_check_applicant_not_found(self):
        """Handle missing applicant gracefully."""
        from app.workers.screening_worker import run_screening_check

        ctx = {"logger": MagicMock()}

        with patch("app.workers.screening_worker.get_db_context") as mock_db_ctx:
            mock_db = AsyncMock()

            mock_result = MagicMock()
            mock_result.scalar_one_or_none.return_value = None  # Not found
            mock_db.execute = AsyncMock(return_value=mock_result)

            mock_db_ctx.return_value.__aenter__ = AsyncMock(return_value=mock_db)
            mock_db_ctx.return_value.__aexit__ = AsyncMock(return_value=None)

            result = await run_screening_check(
                ctx=ctx,
                applicant_id=str(uuid4()),
            )

        assert result["status"] == "error"
        assert "not found" in result["error"].lower()

    @pytest.mark.asyncio
    async def test_run_screening_check_api_error_retries(self):
        """Screening API error triggers retry."""
        from app.workers.screening_worker import run_screening_check
        from app.services.screening import ScreeningResult

        ctx = {"logger": MagicMock()}

        with patch("app.workers.screening_worker.get_db_context") as mock_db_ctx:
            mock_db = AsyncMock()

            mock_applicant = MagicMock()
            mock_applicant.id = uuid4()
            mock_applicant.tenant_id = uuid4()
            mock_applicant.full_name = "John Doe"
            mock_applicant.date_of_birth = None
            mock_applicant.nationality = "USA"
            mock_applicant.country_of_residence = "USA"
            mock_applicant.flags = []

            mock_result = MagicMock()
            mock_result.scalar_one_or_none.return_value = mock_applicant
            mock_db.execute = AsyncMock(return_value=mock_result)
            mock_db.add = MagicMock()
            mock_db.flush = AsyncMock()
            mock_db.commit = AsyncMock()
            mock_db.rollback = AsyncMock()

            mock_db_ctx.return_value.__aenter__ = AsyncMock(return_value=mock_db)
            mock_db_ctx.return_value.__aexit__ = AsyncMock(return_value=None)

            with patch("app.workers.screening_worker.screening_service") as mock_screening:
                mock_screening.check_individual = AsyncMock(return_value=ScreeningResult(
                    status="error",
                    list_version_id="",
                    hits=[],
                    error_message="API timeout",
                ))

                # Should raise exception to trigger ARQ retry
                with pytest.raises(Exception) as exc_info:
                    await run_screening_check(
                        ctx=ctx,
                        applicant_id=str(uuid4()),
                    )

                assert "Screening failed" in str(exc_info.value)


# ===========================================
# WEBHOOK WORKER TESTS
# ===========================================

class TestWebhookWorker:
    """Test webhook delivery worker."""

    @pytest.mark.asyncio
    async def test_deliver_webhook_job(self):
        """Webhook delivery job processes correctly."""
        from app.workers.webhook_worker import deliver_webhook

        ctx = {"logger": MagicMock()}
        delivery_id = str(uuid4())

        with patch("app.workers.webhook_worker.get_db_context") as mock_db_ctx:
            mock_db = AsyncMock()

            # Mock delivery record with tenant settings
            mock_delivery = MagicMock()
            mock_delivery.id = uuid4()
            mock_delivery.tenant_id = uuid4()
            mock_delivery.webhook_url = "https://example.com/webhook"
            mock_delivery.payload = '{"event": "test"}'
            mock_delivery.attempt_count = 0
            mock_delivery.status = "pending"
            mock_delivery.tenant_settings = {
                "webhook": {
                    "secret": "test-secret-key-123"
                }
            }

            mock_result = MagicMock()
            mock_result.fetchone.return_value = mock_delivery
            mock_db.execute = AsyncMock(return_value=mock_result)

            mock_db_ctx.return_value.__aenter__ = AsyncMock(return_value=mock_db)
            mock_db_ctx.return_value.__aexit__ = AsyncMock(return_value=None)

            with patch("app.workers.webhook_worker.webhook_service") as mock_service:
                mock_service.deliver = AsyncMock(return_value=(True, 200, None))
                mock_service.update_delivery_status = AsyncMock()

                result = await deliver_webhook(ctx=ctx, delivery_id=delivery_id)

        assert result["status"] == "delivered"

    @pytest.mark.asyncio
    async def test_process_pending_webhooks(self):
        """Batch process pending webhooks."""
        from app.workers.webhook_worker import process_pending_webhooks

        ctx = {"logger": MagicMock()}

        with patch("app.workers.webhook_worker.webhook_service") as mock_service:
            mock_service.get_pending_deliveries = AsyncMock(return_value=[
                {"id": uuid4(), "tenant_id": uuid4()},
                {"id": uuid4(), "tenant_id": uuid4()},
            ])

            with patch("app.workers.webhook_worker._schedule_retry") as mock_schedule:
                mock_schedule.return_value = None

                result = await process_pending_webhooks(ctx=ctx)

        assert result["status"] == "success"
        assert result["enqueued"] == 2
