"""
Get Clearance - Structured Logging Configuration
=================================================
JSON-formatted logging with request context propagation.

Features:
- JSON output for log aggregation (Railway, Datadog, etc.)
- Request ID correlation across log entries
- Automatic context propagation
- PII scrubbing in log messages
"""

import logging
import json
import re
from datetime import datetime
from contextvars import ContextVar
from typing import Any

# Context variables for request-scoped data
request_id_var: ContextVar[str] = ContextVar("request_id", default="")
tenant_id_var: ContextVar[str] = ContextVar("tenant_id", default="")
user_id_var: ContextVar[str] = ContextVar("user_id", default="")

# PII patterns to redact from log messages
PII_PATTERNS = [
    # Email addresses
    (re.compile(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'), '[EMAIL_REDACTED]'),
    # Phone numbers (various formats)
    (re.compile(r'(\+?1?[-.\s]?)?\(?[0-9]{3}\)?[-.\s]?[0-9]{3}[-.\s]?[0-9]{4}'), '[PHONE_REDACTED]'),
    # SSN
    (re.compile(r'\b\d{3}[-.\s]?\d{2}[-.\s]?\d{4}\b'), '[SSN_REDACTED]'),
    # Credit card numbers (basic pattern)
    (re.compile(r'\b(?:\d{4}[-.\s]?){3}\d{4}\b'), '[CC_REDACTED]'),
    # IP addresses (for sensitive contexts)
    # (re.compile(r'\b\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}\b'), '[IP_REDACTED]'),
]

# Fields to redact in JSON data
REDACTED_FIELDS = {
    'password', 'secret', 'token', 'api_key', 'apikey',
    'authorization', 'auth', 'credit_card', 'ssn',
    'social_security', 'secret_key', 'private_key',
}


def scrub_pii(message: str) -> str:
    """
    Remove PII from a log message.

    Args:
        message: Log message to scrub

    Returns:
        Message with PII patterns replaced
    """
    for pattern, replacement in PII_PATTERNS:
        message = pattern.sub(replacement, message)
    return message


def scrub_dict(data: dict[str, Any], depth: int = 0) -> dict[str, Any]:
    """
    Recursively scrub sensitive fields from a dictionary.

    Args:
        data: Dictionary to scrub
        depth: Current recursion depth (prevents infinite recursion)

    Returns:
        Dictionary with sensitive values redacted
    """
    if depth > 10:  # Prevent infinite recursion
        return data

    result = {}
    for key, value in data.items():
        lower_key = key.lower()
        if any(sensitive in lower_key for sensitive in REDACTED_FIELDS):
            result[key] = "[REDACTED]"
        elif isinstance(value, dict):
            result[key] = scrub_dict(value, depth + 1)
        elif isinstance(value, str):
            result[key] = scrub_pii(value)
        else:
            result[key] = value
    return result


class JSONFormatter(logging.Formatter):
    """
    JSON log formatter for structured logging.

    Output format:
    {
        "timestamp": "2025-12-02T10:30:45.123456",
        "level": "INFO",
        "message": "Request completed",
        "logger": "app.api",
        "request_id": "abc-123",
        "tenant_id": "tenant-456",
        "user_id": "user-789",
        "exception": null,
        "extra": {}
    }
    """

    def format(self, record: logging.LogRecord) -> str:
        """Format log record as JSON."""
        log_record: dict[str, Any] = {
            "timestamp": datetime.utcnow().isoformat(),
            "level": record.levelname,
            "message": scrub_pii(record.getMessage()),
            "logger": record.name,
            "request_id": request_id_var.get() or None,
            "tenant_id": tenant_id_var.get() or None,
            "user_id": user_id_var.get() or None,
        }

        # Add exception info if present
        if record.exc_info:
            log_record["exception"] = self.formatException(record.exc_info)

        # Add any extra fields (scrubbed)
        extra = {}
        for key, value in record.__dict__.items():
            if key not in {
                'name', 'msg', 'args', 'created', 'filename', 'funcName',
                'levelname', 'levelno', 'lineno', 'module', 'msecs',
                'pathname', 'process', 'processName', 'relativeCreated',
                'stack_info', 'exc_info', 'exc_text', 'thread', 'threadName',
                'message', 'taskName',
            }:
                if isinstance(value, dict):
                    extra[key] = scrub_dict(value)
                elif isinstance(value, str):
                    extra[key] = scrub_pii(value)
                else:
                    extra[key] = value

        if extra:
            log_record["extra"] = extra

        return json.dumps(log_record, default=str)


class DevelopmentFormatter(logging.Formatter):
    """
    Human-readable log formatter for development.

    Output format:
    2025-12-02 10:30:45 [INFO] app.api [req-abc123] Request completed
    """

    COLORS = {
        'DEBUG': '\033[36m',     # Cyan
        'INFO': '\033[32m',      # Green
        'WARNING': '\033[33m',   # Yellow
        'ERROR': '\033[31m',     # Red
        'CRITICAL': '\033[41m',  # Red background
    }
    RESET = '\033[0m'

    def format(self, record: logging.LogRecord) -> str:
        """Format log record for human readability."""
        timestamp = datetime.fromtimestamp(record.created).strftime('%Y-%m-%d %H:%M:%S')
        level = record.levelname
        color = self.COLORS.get(level, '')

        request_id = request_id_var.get()
        request_id_str = f" [{request_id[:8]}]" if request_id else ""

        message = scrub_pii(record.getMessage())

        formatted = f"{timestamp} {color}[{level}]{self.RESET} {record.name}{request_id_str} {message}"

        if record.exc_info:
            formatted += "\n" + self.formatException(record.exc_info)

        return formatted


def setup_logging(is_production: bool = False, log_level: str = "INFO") -> None:
    """
    Configure application logging.

    Args:
        is_production: Whether to use JSON format (production) or human-readable (development)
        log_level: Minimum log level to output
    """
    # Create handler
    handler = logging.StreamHandler()

    # Choose formatter based on environment
    if is_production:
        handler.setFormatter(JSONFormatter())
    else:
        handler.setFormatter(DevelopmentFormatter())

    # Configure root logger
    logging.root.handlers = [handler]
    logging.root.setLevel(getattr(logging, log_level.upper(), logging.INFO))

    # Reduce noise from noisy libraries
    logging.getLogger("urllib3").setLevel(logging.WARNING)
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)
    logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)
    logging.getLogger("asyncio").setLevel(logging.WARNING)


def get_logger(name: str) -> logging.Logger:
    """
    Get a logger instance with the given name.

    Args:
        name: Logger name (typically __name__)

    Returns:
        Configured logger instance
    """
    return logging.getLogger(name)


# Convenience function for setting request context
def set_request_context(
    request_id: str | None = None,
    tenant_id: str | None = None,
    user_id: str | None = None,
) -> None:
    """
    Set context variables for the current request.

    Should be called at the start of request handling.

    Args:
        request_id: Unique request identifier
        tenant_id: Current tenant ID
        user_id: Current user ID
    """
    if request_id:
        request_id_var.set(request_id)
    if tenant_id:
        tenant_id_var.set(tenant_id)
    if user_id:
        user_id_var.set(user_id)


def clear_request_context() -> None:
    """
    Clear context variables after request completion.

    Should be called at the end of request handling.
    """
    request_id_var.set("")
    tenant_id_var.set("")
    user_id_var.set("")
