from __future__ import annotations

import logging
from typing import Any

import httpx
import pytest

from infrastructure.adapters.google_chat_webhook import (
    GoogleChatWebhookAdapter,
    WebhookDeliveryError,
)
from infrastructure.logging.events import ALERT_WEBHOOK_FAILED, ALERT_WEBHOOK_SENT


class _Transport(httpx.BaseTransport):
    def __init__(self, status_code: int = 200, body: str = "ok") -> None:
        self.status_code = status_code
        self.body = body
        self.requests: list[httpx.Request] = []

    def handle_request(self, request: httpx.Request) -> httpx.Response:
        self.requests.append(request)
        return httpx.Response(self.status_code, text=self.body, request=request)


def test_adapter_posts_json_payload(caplog: pytest.LogCaptureFixture) -> None:
    transport = _Transport(status_code=200)
    client = httpx.Client(transport=transport)
    adapter = GoogleChatWebhookAdapter(
        webhook_url="http://mock-webhook:8080/v1/spaces/POC/messages",
        client=client,
        ticket_id=7,
    )
    payload: dict[str, Any] = {"text": "hello"}

    with caplog.at_level(logging.INFO):
        adapter.send(payload)

    assert len(transport.requests) == 1
    request = transport.requests[0]
    assert request.method == "POST"
    assert str(request.url) == "http://mock-webhook:8080/v1/spaces/POC/messages"
    assert request.content == b'{"text":"hello"}'
    assert any(
        getattr(record, "semantic", {}).get("event") == ALERT_WEBHOOK_SENT
        and getattr(record, "semantic", {}).get("http_status") == 200
        for record in caplog.records
        if hasattr(record, "semantic")
    )


def test_adapter_raises_on_http_error_status(caplog: pytest.LogCaptureFixture) -> None:
    transport = _Transport(status_code=500, body="boom")
    client = httpx.Client(transport=transport)
    adapter = GoogleChatWebhookAdapter(
        webhook_url="http://mock-webhook:8080/hook",
        client=client,
        ticket_id=3,
    )

    with (
        caplog.at_level(logging.ERROR),
        pytest.raises(WebhookDeliveryError, match="HTTP 500"),
    ):
        adapter.send({"text": "fail"})
    assert any(
        getattr(record, "semantic", {}).get("event") == ALERT_WEBHOOK_FAILED
        for record in caplog.records
        if hasattr(record, "semantic")
    )


def test_adapter_raises_on_transport_error() -> None:
    class BrokenTransport(httpx.BaseTransport):
        def handle_request(self, request: httpx.Request) -> httpx.Response:
            raise httpx.ConnectError("refused", request=request)

    client = httpx.Client(transport=BrokenTransport())
    adapter = GoogleChatWebhookAdapter(
        webhook_url="http://mock-webhook:8080/hook",
        client=client,
    )

    with pytest.raises(WebhookDeliveryError, match="Webhook request failed"):
        adapter.send({"text": "fail"})


def test_adapter_closes_owned_client(monkeypatch: pytest.MonkeyPatch) -> None:
    closed: list[bool] = []

    class TrackingClient(httpx.Client):
        def close(self) -> None:
            closed.append(True)
            super().close()

    transport = _Transport(status_code=200)
    created: list[TrackingClient] = []

    def factory(*args: Any, **kwargs: Any) -> TrackingClient:
        client = TrackingClient(transport=transport)
        created.append(client)
        return client

    monkeypatch.setattr(
        "infrastructure.adapters.google_chat_webhook.httpx.Client",
        factory,
    )
    adapter = GoogleChatWebhookAdapter(webhook_url="http://mock-webhook:8080/hook")
    adapter.send({"text": "owned"})

    assert created
    assert closed == [True]


def test_adapter_includes_payload_bytes_on_debug(
    caplog: pytest.LogCaptureFixture,
) -> None:
    transport = _Transport(status_code=200)
    client = httpx.Client(transport=transport)
    adapter = GoogleChatWebhookAdapter(
        webhook_url="http://mock-webhook:8080/hook",
        client=client,
        ticket_id=1,
    )
    logging.getLogger("infrastructure.adapters.google_chat_webhook").setLevel(
        logging.DEBUG
    )
    with caplog.at_level(logging.DEBUG):
        adapter.send({"text": "hello"})
    sent = [
        record.semantic
        for record in caplog.records
        if getattr(record, "semantic", {}).get("event") == ALERT_WEBHOOK_SENT
    ]
    assert sent
    assert "payload_bytes" in sent[0]
