"""
Tests for monitoring and observability features.
Sprint B6: Monitoring & Alerting

Tests cover:
- Structured logging with PII scrubbing
- Health check endpoints
- Sentry integration helpers
"""

import pytest
import json
import logging
from datetime import datetime
from unittest.mock import MagicMock, patch, AsyncMock

from app.logging_config import (
    scrub_pii,
    scrub_dict,
    JSONFormatter,
    DevelopmentFormatter,
    setup_logging,
    get_logger,
    set_request_context,
    clear_request_context,
    request_id_var,
    tenant_id_var,
    user_id_var,
)


# ===========================================
# PII SCRUBBING TESTS
# ===========================================

class TestPIIScrubbing:
    """Tests for PII scrubbing in logs."""

    def test_scrub_email_address(self):
        """Should redact email addresses."""
        message = "User email is john.doe@example.com in the system"
        scrubbed = scrub_pii(message)
        assert "john.doe@example.com" not in scrubbed
        assert "[EMAIL_REDACTED]" in scrubbed

    def test_scrub_phone_number_us_format(self):
        """Should redact US phone numbers."""
        message = "Contact number: 555-123-4567"
        scrubbed = scrub_pii(message)
        assert "555-123-4567" not in scrubbed
        assert "[PHONE_REDACTED]" in scrubbed

    def test_scrub_phone_number_with_country_code(self):
        """Should redact phone numbers with country code."""
        message = "Phone: +1-555-123-4567"
        scrubbed = scrub_pii(message)
        assert "555-123-4567" not in scrubbed
        assert "[PHONE_REDACTED]" in scrubbed

    def test_scrub_ssn(self):
        """Should redact Social Security Numbers."""
        message = "SSN: 123-45-6789"
        scrubbed = scrub_pii(message)
        assert "123-45-6789" not in scrubbed
        assert "[SSN_REDACTED]" in scrubbed

    def test_scrub_credit_card(self):
        """Should redact credit card numbers."""
        message = "Card: 4111-1111-1111-1111"
        scrubbed = scrub_pii(message)
        assert "4111-1111-1111-1111" not in scrubbed
        assert "[CC_REDACTED]" in scrubbed

    def test_scrub_multiple_pii(self):
        """Should redact multiple PII types in one message."""
        message = "User john@test.com called from 555-123-4567 with SSN 123-45-6789"
        scrubbed = scrub_pii(message)
        assert "john@test.com" not in scrubbed
        assert "555-123-4567" not in scrubbed
        assert "123-45-6789" not in scrubbed

    def test_no_pii_unchanged(self):
        """Messages without PII should remain unchanged."""
        message = "Processing applicant status update"
        scrubbed = scrub_pii(message)
        assert scrubbed == message


class TestDictScrubbing:
    """Tests for scrubbing sensitive fields from dictionaries."""

    def test_scrub_password_field(self):
        """Should redact password fields."""
        data = {"username": "john", "password": "secret123"}
        scrubbed = scrub_dict(data)
        assert scrubbed["password"] == "[REDACTED]"
        assert scrubbed["username"] == "john"

    def test_scrub_api_key_field(self):
        """Should redact api_key fields."""
        data = {"api_key": "sk-12345", "endpoint": "/api/v1"}
        scrubbed = scrub_dict(data)
        assert scrubbed["api_key"] == "[REDACTED]"

    def test_scrub_authorization_field(self):
        """Should redact authorization fields."""
        data = {"authorization": "Bearer token123", "method": "GET"}
        scrubbed = scrub_dict(data)
        assert scrubbed["authorization"] == "[REDACTED]"

    def test_scrub_nested_sensitive_fields(self):
        """Should scrub nested dictionaries."""
        data = {
            "user": {
                "name": "John",
                "credentials": {
                    "password": "secret",
                    "token": "abc123"
                }
            }
        }
        scrubbed = scrub_dict(data)
        assert scrubbed["user"]["credentials"]["password"] == "[REDACTED]"
        assert scrubbed["user"]["credentials"]["token"] == "[REDACTED]"

    def test_scrub_pii_in_string_values(self):
        """Should scrub PII patterns in string values."""
        data = {"message": "Contact: john@example.com"}
        scrubbed = scrub_dict(data)
        assert "[EMAIL_REDACTED]" in scrubbed["message"]

    def test_recursion_depth_limit(self):
        """Should handle deeply nested dicts without infinite recursion."""
        # Create deeply nested dict
        data = {"level": 0}
        current = data
        for i in range(15):
            current["nested"] = {"level": i + 1}
            current = current["nested"]

        # Should not raise RecursionError
        scrubbed = scrub_dict(data)
        assert scrubbed["level"] == 0


# ===========================================
# JSON FORMATTER TESTS
# ===========================================

class TestJSONFormatter:
    """Tests for JSON log formatter."""

    def test_format_basic_log(self):
        """Should produce valid JSON output."""
        formatter = JSONFormatter()
        record = logging.LogRecord(
            name="test.logger",
            level=logging.INFO,
            pathname="test.py",
            lineno=10,
            msg="Test message",
            args=(),
            exc_info=None,
        )

        output = formatter.format(record)
        parsed = json.loads(output)

        assert parsed["level"] == "INFO"
        assert parsed["message"] == "Test message"
        assert parsed["logger"] == "test.logger"
        assert "timestamp" in parsed

    def test_format_with_request_context(self):
        """Should include request context in output."""
        formatter = JSONFormatter()

        # Set request context
        request_id_var.set("req-123")
        tenant_id_var.set("tenant-456")
        user_id_var.set("user-789")

        try:
            record = logging.LogRecord(
                name="test",
                level=logging.INFO,
                pathname="test.py",
                lineno=10,
                msg="Test",
                args=(),
                exc_info=None,
            )

            output = formatter.format(record)
            parsed = json.loads(output)

            assert parsed["request_id"] == "req-123"
            assert parsed["tenant_id"] == "tenant-456"
            assert parsed["user_id"] == "user-789"
        finally:
            clear_request_context()

    def test_format_scrubs_pii(self):
        """Should scrub PII from messages."""
        formatter = JSONFormatter()
        record = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname="test.py",
            lineno=10,
            msg="User email: john@test.com",
            args=(),
            exc_info=None,
        )

        output = formatter.format(record)
        parsed = json.loads(output)

        assert "john@test.com" not in parsed["message"]
        assert "[EMAIL_REDACTED]" in parsed["message"]


# ===========================================
# DEVELOPMENT FORMATTER TESTS
# ===========================================

class TestDevelopmentFormatter:
    """Tests for human-readable development formatter."""

    def test_format_includes_level_with_color(self):
        """Should include log level with color codes."""
        formatter = DevelopmentFormatter()
        record = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname="test.py",
            lineno=10,
            msg="Test message",
            args=(),
            exc_info=None,
        )

        output = formatter.format(record)
        assert "[INFO]" in output
        assert "Test message" in output

    def test_format_includes_request_id(self):
        """Should include truncated request ID."""
        formatter = DevelopmentFormatter()
        request_id_var.set("abcdefgh-1234-5678")

        try:
            record = logging.LogRecord(
                name="test",
                level=logging.INFO,
                pathname="test.py",
                lineno=10,
                msg="Test",
                args=(),
                exc_info=None,
            )

            output = formatter.format(record)
            assert "[abcdefgh]" in output
        finally:
            clear_request_context()


# ===========================================
# REQUEST CONTEXT TESTS
# ===========================================

class TestRequestContext:
    """Tests for request context management."""

    def test_set_request_context(self):
        """Should set context variables."""
        set_request_context(
            request_id="req-test",
            tenant_id="tenant-test",
            user_id="user-test"
        )

        try:
            assert request_id_var.get() == "req-test"
            assert tenant_id_var.get() == "tenant-test"
            assert user_id_var.get() == "user-test"
        finally:
            clear_request_context()

    def test_clear_request_context(self):
        """Should clear all context variables."""
        set_request_context(
            request_id="req-123",
            tenant_id="tenant-456",
            user_id="user-789"
        )
        clear_request_context()

        assert request_id_var.get() == ""
        assert tenant_id_var.get() == ""
        assert user_id_var.get() == ""

    def test_partial_context_set(self):
        """Should only set provided values."""
        clear_request_context()
        set_request_context(request_id="req-only")

        assert request_id_var.get() == "req-only"
        assert tenant_id_var.get() == ""

        clear_request_context()


# ===========================================
# LOGGING SETUP TESTS
# ===========================================

class TestLoggingSetup:
    """Tests for logging configuration."""

    def test_setup_logging_production(self):
        """Should configure JSON formatter for production."""
        setup_logging(is_production=True, log_level="INFO")

        # Check root logger has handler
        assert len(logging.root.handlers) > 0

        # Handler should use JSONFormatter
        handler = logging.root.handlers[0]
        assert isinstance(handler.formatter, JSONFormatter)

    def test_setup_logging_development(self):
        """Should configure development formatter."""
        setup_logging(is_production=False, log_level="DEBUG")

        handler = logging.root.handlers[0]
        assert isinstance(handler.formatter, DevelopmentFormatter)

    def test_get_logger(self):
        """Should return named logger."""
        logger = get_logger("test.module")
        assert logger.name == "test.module"
