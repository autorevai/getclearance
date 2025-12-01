"""
Get Clearance - Background Workers
===================================
ARQ-based async task queue for background job processing.

Workers handle long-running tasks like:
- AML/Sanctions screening
- Document processing (OCR, fraud detection)
- AI risk summary generation
- Webhook delivery with retry

Start workers with:
    arq app.workers.config.WorkerSettings
"""

from app.workers.config import WorkerSettings, get_redis_settings
from app.workers.screening_worker import run_screening_check
from app.workers.document_worker import process_document
from app.workers.ai_worker import generate_risk_summary
from app.workers.webhook_worker import (
    deliver_webhook,
    process_pending_webhooks,
    retry_failed_webhook,
)

__all__ = [
    # Config
    "WorkerSettings",
    "get_redis_settings",
    # Workers
    "run_screening_check",
    "process_document",
    "generate_risk_summary",
    "deliver_webhook",
    "process_pending_webhooks",
    "retry_failed_webhook",
]
