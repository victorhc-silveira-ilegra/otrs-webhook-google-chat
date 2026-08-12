from __future__ import annotations

import json
import logging

from presentation.logging.formatters import JsonSemanticFormatter, TextSemanticFormatter


def _record(
    *,
    msg: str = "alert.run.started",
    semantic: dict[str, object] | None = None,
    level: int = logging.INFO,
) -> logging.LogRecord:
    record = logging.LogRecord(
        name="test",
        level=level,
        pathname=__file__,
        lineno=1,
        msg=msg,
        args=(),
        exc_info=None,
    )
    if semantic is not None:
        record.semantic = semantic  # type: ignore[attr-defined]
    return record


def test_text_formatter_with_semantic_fields() -> None:
    formatter = TextSemanticFormatter()
    line = formatter.format(
        _record(semantic={"event": "alert.run.started", "ticket_id": 1})
    )
    assert "event=alert.run.started" in line
    assert "ticket_id=1" in line
    assert "INFO" in line


def test_text_formatter_without_semantic_falls_back_to_message() -> None:
    formatter = TextSemanticFormatter()
    line = formatter.format(_record(msg="plain-message"))
    assert "event=plain-message" in line


def test_json_formatter_emits_event_and_fields() -> None:
    formatter = JsonSemanticFormatter()
    payload = json.loads(
        formatter.format(
            _record(semantic={"event": "alert.webhook.sent", "http_status": 200})
        )
    )
    assert payload["event"] == "alert.webhook.sent"
    assert payload["http_status"] == 200
    assert payload["level"] == "INFO"


def test_json_formatter_includes_exc_info() -> None:
    formatter = JsonSemanticFormatter()
    try:
        raise RuntimeError("boom")
    except RuntimeError:
        record = _record(semantic={"event": "alert.run.failed"})
        record.exc_info = sys_exc_info()
    payload = json.loads(formatter.format(record))
    assert "exc_info" in payload
    assert "RuntimeError" in payload["exc_info"]


def sys_exc_info() -> tuple[type[BaseException], BaseException, object] | None:
    import sys

    return sys.exc_info()
