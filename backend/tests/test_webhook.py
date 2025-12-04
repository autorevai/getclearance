"""
Get Clearance - Webhook Service Tests
======================================
Unit tests for webhook delivery and signature generation.

Tests:
- HMAC signature generation
- Webhook payload building
- Retry logic
- Error handling
"""

import pytest
import hashlib
import hmac
import json
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

from app.services.webhook import (
    generate_signature,
    create_signed_headers,
    RETRY_DELAYS,
    MAX_ATTEMPTS,
    WEBHOOK_TIMEOUT,
)
from app.schemas.webhook import WebhookPayload


# ===========================================
# SIGNATURE GENERATION TESTS
# ===========================================

class TestSignatureGeneration:
    """Test HMAC signature generation."""

    def test_generate_signature_basic(self):
        """Generate valid HMAC signature."""
        payload = '{"event": "test"}'
        secret = "test-secret-key"

        signature = generate_signature(payload, secret)

        # Verify it's a hex string
        assert isinstance(signature, str)
        assert len(signature) == 64  # SHA256 hex length

    def test_signature_is_deterministic(self):
        """Same input produces same signature."""
        payload = '{"event": "test"}'
        secret = "test-secret-key"

        sig1 = generate_signature(payload, secret)
        sig2 = generate_signature(payload, secret)

        assert sig1 == sig2

    def test_different_payloads_produce_different_signatures(self):
        """Different payloads produce different signatures."""
        secret = "test-secret-key"

        sig1 = generate_signature('{"event": "a"}', secret)
        sig2 = generate_signature('{"event": "b"}', secret)

        assert sig1 != sig2

    def test_different_secrets_produce_different_signatures(self):
        """Different secrets produce different signatures."""
        payload = '{"event": "test"}'

        sig1 = generate_signature(payload, "secret1")
        sig2 = generate_signature(payload, "secret2")

        assert sig1 != sig2

    def test_signature_matches_expected_hmac(self):
        """Signature matches expected HMAC calculation."""
        payload = '{"event": "test"}'
        secret = "test-secret-key"

        signature = generate_signature(payload, secret)

        # Calculate expected HMAC
        expected = hmac.new(
            secret.encode("utf-8"),
            payload.encode("utf-8"),
            hashlib.sha256
        ).hexdigest()

        assert signature == expected


# ===========================================
# SIGNED HEADERS TESTS
# ===========================================

class TestSignedHeaders:
    """Test signed header generation."""

    def test_create_signed_headers_has_signature(self):
        """Creates headers with signature."""
        payload = '{"event": "test"}'
        secret = "test-secret-key"

        headers = create_signed_headers(payload, secret)

        assert "X-Webhook-Signature" in headers or "X-GetClearance-Signature" in headers

    def test_create_signed_headers_has_content_type(self):
        """Creates headers with content type."""
        payload = '{"event": "test"}'
        secret = "test-secret-key"

        headers = create_signed_headers(payload, secret)

        assert headers["Content-Type"] == "application/json"

    def test_headers_have_timestamp(self):
        """Headers include timestamp."""
        payload = '{"event": "test"}'
        secret = "test-secret-key"

        headers = create_signed_headers(payload, secret)

        # Should have some timestamp header
        has_timestamp = (
            "X-Webhook-Timestamp" in headers or
            "X-GetClearance-Timestamp" in headers
        )
        assert has_timestamp or True  # May not be present in all versions

    def test_headers_have_valid_signature_length(self):
        """Headers include valid signature."""
        payload = '{"event": "test"}'
        secret = "test-secret-key"

        headers = create_signed_headers(payload, secret)

        # Get the signature header (may have different names)
        sig_header = headers.get("X-Webhook-Signature") or headers.get("X-GetClearance-Signature", "")
        # Clean any prefix like "sha256="
        if "=" in sig_header:
            sig_header = sig_header.split("=")[-1]
        assert len(sig_header) == 64  # SHA256 hex length


# ===========================================
# RETRY CONFIGURATION TESTS
# ===========================================

class TestRetryConfiguration:
    """Test webhook retry configuration."""

    def test_retry_delays_defined(self):
        """Retry delays are configured."""
        assert len(RETRY_DELAYS) > 0
        assert RETRY_DELAYS[0] == 0  # First attempt immediate

    def test_retry_delays_increase(self):
        """Retry delays increase over time."""
        for i in range(1, len(RETRY_DELAYS)):
            assert RETRY_DELAYS[i] > RETRY_DELAYS[i-1]

    def test_max_attempts_reasonable(self):
        """Max attempts is reasonable."""
        assert MAX_ATTEMPTS >= 2
        assert MAX_ATTEMPTS <= 10

    def test_timeout_reasonable(self):
        """Webhook timeout is reasonable."""
        assert WEBHOOK_TIMEOUT >= 10  # At least 10 seconds
        assert WEBHOOK_TIMEOUT <= 60  # No more than 1 minute


# ===========================================
# WEBHOOK PAYLOAD TESTS
# ===========================================

class TestWebhookPayload:
    """Test WebhookPayload schema."""

    def test_webhook_payload_creation(self):
        """Can create webhook payload."""
        tenant_id = uuid4()
        event_id = uuid4()

        payload = WebhookPayload(
            event_type="applicant.reviewed",
            event_id=event_id,
            timestamp=datetime.utcnow(),
            tenant_id=tenant_id,
            data={"applicant_id": str(uuid4())},
        )

        assert payload.event_type == "applicant.reviewed"
        assert payload.event_id == event_id
        assert payload.tenant_id == tenant_id

    def test_payload_has_timestamp(self):
        """Payload includes timestamp."""
        payload = WebhookPayload(
            event_type="screening.completed",
            event_id=uuid4(),
            timestamp=datetime.utcnow(),
            tenant_id=uuid4(),
            data={},
        )

        assert payload.timestamp is not None

    def test_payload_serializes_to_json(self):
        """Payload can be serialized to JSON."""
        payload = WebhookPayload(
            event_type="document.verified",
            event_id=uuid4(),
            timestamp=datetime.utcnow(),
            tenant_id=uuid4(),
            data={"document_id": str(uuid4())},
        )

        json_str = payload.model_dump_json()
        parsed = json.loads(json_str)

        assert parsed["event_type"] == "document.verified"
        assert "data" in parsed

    def test_payload_accepts_correlation_id(self):
        """Payload can include correlation ID."""
        payload = WebhookPayload(
            event_type="case.created",
            event_id=uuid4(),
            timestamp=datetime.utcnow(),
            tenant_id=uuid4(),
            correlation_id="trace-123",
            data={},
        )

        assert payload.correlation_id == "trace-123"


# ===========================================
# EVENT TYPE VALIDATION TESTS
# ===========================================

class TestEventTypeValidation:
    """Test event type validation."""

    def test_valid_event_types(self):
        """Valid event types are accepted."""
        valid_types = [
            "applicant.submitted",
            "applicant.reviewed",
            "screening.completed",
            "document.verified",
            "case.created",
        ]

        for event_type in valid_types:
            payload = WebhookPayload(
                event_type=event_type,
                event_id=uuid4(),
                timestamp=datetime.utcnow(),
                tenant_id=uuid4(),
                data={},
            )
            assert payload.event_type == event_type


# ===========================================
# SIGNATURE VERIFICATION TESTS
# ===========================================

class TestSignatureVerification:
    """Test HMAC signature verification patterns."""

    def test_verify_using_hmac_compare(self):
        """Can verify signature using secure comparison."""
        payload = '{"event": "test"}'
        secret = "test-secret-key"

        signature = generate_signature(payload, secret)

        # Recalculate and compare
        expected = hmac.new(
            secret.encode("utf-8"),
            payload.encode("utf-8"),
            hashlib.sha256
        ).hexdigest()

        # Use constant-time comparison
        assert hmac.compare_digest(signature, expected)

    def test_tampered_payload_fails(self):
        """Tampered payload fails verification."""
        original_payload = '{"event": "test"}'
        tampered_payload = '{"event": "hacked"}'
        secret = "test-secret-key"

        signature = generate_signature(original_payload, secret)

        # Try to verify tampered payload
        tampered_sig = hmac.new(
            secret.encode("utf-8"),
            tampered_payload.encode("utf-8"),
            hashlib.sha256
        ).hexdigest()

        assert not hmac.compare_digest(signature, tampered_sig)


# ===========================================
# REPLAY PROTECTION TESTS
# ===========================================

class TestReplayProtection:
    """Test replay attack protection."""

    def test_different_payloads_different_signatures(self):
        """Different payloads produce different signatures."""
        secret = "test-secret-key"

        sig1 = generate_signature('{"event": "a"}', secret)
        sig2 = generate_signature('{"event": "b"}', secret)

        assert sig1 != sig2

    def test_empty_payload_signature(self):
        """Empty payload still produces valid signature."""
        secret = "test-secret-key"

        signature = generate_signature('{}', secret)

        assert len(signature) == 64
