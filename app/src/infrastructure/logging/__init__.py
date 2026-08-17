from __future__ import annotations

from infrastructure.logging.emit import log_event
from infrastructure.logging.events import (
    ALERT_DISPATCH_CLAIM_FAILED,
    ALERT_RUN_FAILED,
    ALERT_RUN_FINISHED,
    ALERT_RUN_SKIPPED_DUPLICATE,
    ALERT_RUN_SKIPPED_OUTSIDE_HOURS,
    ALERT_RUN_STARTED,
    ALERT_WEBHOOK_FAILED,
    ALERT_WEBHOOK_SENT,
)
from infrastructure.logging.redact import redact_webhook_url, truncate_preview

__all__ = [
    "ALERT_DISPATCH_CLAIM_FAILED",
    "ALERT_RUN_FAILED",
    "ALERT_RUN_FINISHED",
    "ALERT_RUN_SKIPPED_DUPLICATE",
    "ALERT_RUN_SKIPPED_OUTSIDE_HOURS",
    "ALERT_RUN_STARTED",
    "ALERT_WEBHOOK_FAILED",
    "ALERT_WEBHOOK_SENT",
    "log_event",
    "redact_webhook_url",
    "truncate_preview",
]
