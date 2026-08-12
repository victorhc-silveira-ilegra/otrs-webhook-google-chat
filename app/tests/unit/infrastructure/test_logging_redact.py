from __future__ import annotations

from infrastructure.logging.redact import redact_webhook_url, truncate_preview


def test_redact_webhook_url_masks_query() -> None:
    url = "https://chat.googleapis.com/v1/spaces/ABC/messages?key=secret&token=tok"
    redacted = redact_webhook_url(url)
    assert "secret" not in redacted
    assert "tok" not in redacted
    assert redacted.endswith("?***")
    assert "chat.googleapis.com" in redacted


def test_redact_webhook_url_without_query() -> None:
    url = "http://mock-webhook:8080/v1/spaces/POC/messages"
    assert redact_webhook_url(url) == url


def test_truncate_preview_short() -> None:
    assert truncate_preview("ok") == "ok"


def test_truncate_preview_long() -> None:
    value = "x" * 100
    preview = truncate_preview(value, max_len=80)
    assert len(preview) == 80
    assert preview.endswith("...")
