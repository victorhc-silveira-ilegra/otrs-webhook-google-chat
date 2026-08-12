from __future__ import annotations

import json
import logging
from typing import Any

import httpx

from infrastructure.logging import (
    ALERT_WEBHOOK_FAILED,
    ALERT_WEBHOOK_SENT,
    log_event,
    redact_webhook_url,
)

logger = logging.getLogger(__name__)


class WebhookDeliveryError(RuntimeError):
    pass


class GoogleChatWebhookAdapter:
    def __init__(
        self,
        webhook_url: str,
        timeout_seconds: float = 10.0,
        client: httpx.Client | None = None,
        ticket_id: int | None = None,
    ) -> None:
        self._webhook_url = webhook_url
        self._timeout_seconds = timeout_seconds
        self._client = client
        self._owns_client = client is None
        self._ticket_id = ticket_id
        self._webhook_host = redact_webhook_url(webhook_url)

    def send(self, payload: dict[str, Any]) -> None:
        payload_bytes = len(json.dumps(payload, ensure_ascii=True).encode("utf-8"))
        client = self._client or httpx.Client(timeout=self._timeout_seconds)
        try:
            response = client.post(self._webhook_url, json=payload)
            if response.status_code >= 400:
                log_event(
                    logger,
                    logging.ERROR,
                    ALERT_WEBHOOK_FAILED,
                    ticket_id=self._ticket_id,
                    webhook_host=self._webhook_host,
                    http_status=response.status_code,
                    error_type="http_status",
                    exc_info=logger.isEnabledFor(logging.DEBUG),
                )
                raise WebhookDeliveryError(
                    f"Webhook returned HTTP {response.status_code}: {response.text}"
                )
            fields: dict[str, Any] = {
                "ticket_id": self._ticket_id,
                "webhook_host": self._webhook_host,
                "http_status": response.status_code,
            }
            if logger.isEnabledFor(logging.DEBUG):
                fields["payload_bytes"] = payload_bytes
            log_event(logger, logging.INFO, ALERT_WEBHOOK_SENT, **fields)
        except httpx.HTTPError as exc:
            log_event(
                logger,
                logging.ERROR,
                ALERT_WEBHOOK_FAILED,
                ticket_id=self._ticket_id,
                webhook_host=self._webhook_host,
                error_type=type(exc).__name__,
                exc_info=logger.isEnabledFor(logging.DEBUG),
            )
            raise WebhookDeliveryError(f"Webhook request failed: {exc}") from exc
        finally:
            if self._owns_client:
                client.close()
