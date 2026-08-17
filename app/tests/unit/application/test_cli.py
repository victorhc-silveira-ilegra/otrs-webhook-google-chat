from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

import httpx
import pytest

from application.use_cases.process_alert import ProcessAlertResult
from infrastructure.adapters.google_chat_webhook import (
    GoogleChatWebhookAdapter,
    WebhookDeliveryError,
)
from infrastructure.logging.events import (
    ALERT_RUN_SKIPPED_DUPLICATE,
    ALERT_WEBHOOK_FAILED,
    ALERT_WEBHOOK_SENT,
)
from presentation.cli.main import build_parser, main, run
from presentation.logging.config import reset_logging_state


class _Transport(httpx.BaseTransport):
    def __init__(self) -> None:
        self.requests: list[httpx.Request] = []

    def handle_request(self, request: httpx.Request) -> httpx.Response:
        self.requests.append(request)
        return httpx.Response(200, text="ok", request=request)


@pytest.fixture(autouse=True)
def _reset_logging() -> None:
    reset_logging_state()
    yield
    reset_logging_state()


@pytest.fixture(autouse=True)
def _stub_daily_stdio(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        "presentation.cli.main.attach_daily_stdio",
        lambda *args, **kwargs: None,
    )


def _cli_args() -> list[str]:
    return [
        "--ticket-id",
        "11",
        "--ticket-number",
        "20260812000011",
        "--title",
        "CPU alta",
        "--queue",
        "Raw",
    ]


def test_build_parser_requires_ticket_fields() -> None:
    parser = build_parser()
    with pytest.raises(SystemExit):
        parser.parse_args([])


def test_run_success_emits_semantic_events(
    monkeypatch: pytest.MonkeyPatch, caplog: pytest.LogCaptureFixture
) -> None:
    transport = _Transport()
    client = httpx.Client(transport=transport)

    def factory(*args: Any, **kwargs: Any) -> GoogleChatWebhookAdapter:
        return GoogleChatWebhookAdapter(
            webhook_url=kwargs["webhook_url"],
            timeout_seconds=kwargs["timeout_seconds"],
            client=client,
            ticket_id=kwargs.get("ticket_id"),
        )

    monkeypatch.setenv("GCHAT_WEBHOOK_URL", "http://mock-webhook:8080/hook")
    monkeypatch.setenv("LOG_LEVEL", "INFO")
    monkeypatch.setenv("DEDUP_ENABLED", "false")
    monkeypatch.setenv("WINDOW_ENABLED", "false")
    monkeypatch.setattr("presentation.cli.main.setup_logging", lambda **_: None)
    monkeypatch.setattr(
        "presentation.cli.main.GoogleChatWebhookAdapter",
        factory,
    )

    with caplog.at_level(logging.INFO):
        code = run(_cli_args())

    assert code == 0
    assert len(transport.requests) == 1
    events = [
        getattr(record, "semantic", {}).get("event")
        for record in caplog.records
        if hasattr(record, "semantic")
    ]
    assert "alert.run.started" in events
    assert ALERT_WEBHOOK_SENT in events
    assert "alert.run.finished" in events


def test_run_attaches_daily_stdio(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    captured: dict[str, object] = {}

    def fake_attach(directory: Path, timezone: object, **kwargs: object) -> None:
        captured["directory"] = directory
        captured["timezone"] = timezone

    class _UseCase:
        def __init__(self, **kwargs: Any) -> None:
            return None

        def execute(self, ticket: Any) -> ProcessAlertResult:
            return ProcessAlertResult.SKIPPED_DUPLICATE

    monkeypatch.setenv("GCHAT_WEBHOOK_URL", "http://mock-webhook:8080/hook")
    monkeypatch.setenv("DEDUP_ENABLED", "false")
    monkeypatch.setenv("WINDOW_ENABLED", "false")
    monkeypatch.setenv("LOG_DIR", str(tmp_path))
    monkeypatch.setenv("WINDOW_TIMEZONE", "UTC")
    monkeypatch.setattr("presentation.cli.main.attach_daily_stdio", fake_attach)
    monkeypatch.setattr("presentation.cli.main.setup_logging", lambda **_: None)
    monkeypatch.setattr("presentation.cli.main.ProcessAlertUseCase", _UseCase)
    monkeypatch.setattr(
        "presentation.cli.main.GoogleChatWebhookAdapter",
        lambda **kwargs: object(),
    )
    assert run(_cli_args()) == 0
    assert captured["directory"] == tmp_path


def test_run_skips_daily_stdio_when_log_dir_blank(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    called = False

    def fake_attach(*args: Any, **kwargs: Any) -> None:
        nonlocal called
        called = True

    class _UseCase:
        def __init__(self, **kwargs: Any) -> None:
            return None

        def execute(self, ticket: Any) -> ProcessAlertResult:
            return ProcessAlertResult.SKIPPED_DUPLICATE

    monkeypatch.setenv("GCHAT_WEBHOOK_URL", "http://mock-webhook:8080/hook")
    monkeypatch.setenv("DEDUP_ENABLED", "false")
    monkeypatch.setenv("WINDOW_ENABLED", "false")
    monkeypatch.setenv("LOG_DIR", "")
    monkeypatch.setattr("presentation.cli.main.attach_daily_stdio", fake_attach)
    monkeypatch.setattr("presentation.cli.main.setup_logging", lambda **_: None)
    monkeypatch.setattr("presentation.cli.main.ProcessAlertUseCase", _UseCase)
    monkeypatch.setattr(
        "presentation.cli.main.GoogleChatWebhookAdapter",
        lambda **kwargs: object(),
    )
    assert run(_cli_args()) == 0
    assert called is False


def test_run_skips_duplicate(
    monkeypatch: pytest.MonkeyPatch, caplog: pytest.LogCaptureFixture
) -> None:
    class SkippingUseCase:
        def __init__(self, *args: Any, **kwargs: Any) -> None:
            pass

        def execute(self, ticket: Any) -> ProcessAlertResult:
            return ProcessAlertResult.SKIPPED_DUPLICATE

    monkeypatch.setenv("GCHAT_WEBHOOK_URL", "http://mock-webhook:8080/hook")
    monkeypatch.setenv("DEDUP_ENABLED", "false")
    monkeypatch.setenv("WINDOW_ENABLED", "false")
    monkeypatch.setattr("presentation.cli.main.setup_logging", lambda **_: None)
    monkeypatch.setattr(
        "presentation.cli.main.GoogleChatWebhookAdapter",
        lambda *args, **kwargs: object(),
    )
    monkeypatch.setattr("presentation.cli.main.ProcessAlertUseCase", SkippingUseCase)

    with caplog.at_level(logging.INFO):
        code = run(_cli_args())

    assert code == 0
    assert any(
        getattr(record, "semantic", {}).get("event") == ALERT_RUN_SKIPPED_DUPLICATE
        for record in caplog.records
        if hasattr(record, "semantic")
    )


def test_run_skips_outside_business_hours(
    monkeypatch: pytest.MonkeyPatch, caplog: pytest.LogCaptureFixture
) -> None:
    class ClosedHoursUseCase:
        def __init__(self, *args: Any, **kwargs: Any) -> None:
            pass

        def execute(self, ticket: Any) -> ProcessAlertResult:
            return ProcessAlertResult.SKIPPED_OUTSIDE_HOURS

    monkeypatch.setenv("GCHAT_WEBHOOK_URL", "http://mock-webhook:8080/hook")
    monkeypatch.setenv("DEDUP_ENABLED", "false")
    monkeypatch.setenv("WINDOW_ENABLED", "true")
    monkeypatch.setattr("presentation.cli.main.setup_logging", lambda **_: None)
    monkeypatch.setattr(
        "presentation.cli.main.GoogleChatWebhookAdapter",
        lambda *args, **kwargs: object(),
    )
    monkeypatch.setattr("presentation.cli.main.ProcessAlertUseCase", ClosedHoursUseCase)

    with caplog.at_level(logging.INFO):
        code = run(_cli_args())

    assert code == 0
    assert any(
        getattr(record, "semantic", {}).get("event")
        == "alert.run.skipped_outside_hours"
        for record in caplog.records
        if hasattr(record, "semantic")
    )


def test_run_wires_dispatch_ledger_when_enabled(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    captured: dict[str, Any] = {}

    class CapturingUseCase:
        def __init__(self, *args: Any, **kwargs: Any) -> None:
            captured["dispatch_ledger"] = kwargs.get("dispatch_ledger")
            captured["dedup_window_minutes"] = kwargs.get("dedup_window_minutes")

        def execute(self, ticket: Any) -> ProcessAlertResult:
            return ProcessAlertResult.SENT

    class FakeLedger:
        def __init__(self, db_config: dict[str, str | int]) -> None:
            captured["db_config"] = db_config

        def try_claim(self, **kwargs: Any) -> bool:
            return True

        def release(self, **kwargs: Any) -> None:
            return None

    monkeypatch.setenv("GCHAT_WEBHOOK_URL", "http://mock-webhook:8080/hook")
    monkeypatch.setenv("DEDUP_ENABLED", "true")
    monkeypatch.setenv("DEDUP_WINDOW_MINUTES", "15")
    monkeypatch.setenv("OTRS_DB_HOST", "mariadb")
    monkeypatch.setenv("OTRS_DB_NAME", "otrs")
    monkeypatch.setenv("OTRS_DB_USER", "otrs")
    monkeypatch.setenv("OTRS_DB_PASSWORD", "otrssecret")
    monkeypatch.setenv("WINDOW_ENABLED", "false")
    monkeypatch.setattr("presentation.cli.main.setup_logging", lambda **_: None)
    monkeypatch.setattr(
        "presentation.cli.main.GoogleChatWebhookAdapter",
        lambda *args, **kwargs: object(),
    )
    monkeypatch.setattr(
        "presentation.cli.main.OTRSDatabaseAlertDispatchLedger",
        FakeLedger,
    )
    monkeypatch.setattr("presentation.cli.main.ProcessAlertUseCase", CapturingUseCase)

    code = run(_cli_args())

    assert code == 0
    assert captured["dispatch_ledger"] is not None
    assert captured["dedup_window_minutes"] == 15
    assert captured["db_config"]["host"] == "mariadb"


def test_run_returns_error_without_webhook(
    monkeypatch: pytest.MonkeyPatch, caplog: pytest.LogCaptureFixture
) -> None:
    monkeypatch.delenv("GCHAT_WEBHOOK_URL", raising=False)
    with caplog.at_level(logging.ERROR):
        code = run(_cli_args())
    assert code == 1
    assert any(
        getattr(record, "semantic", {}).get("event") == "alert.run.failed"
        for record in caplog.records
        if hasattr(record, "semantic")
    )


def test_run_returns_error_on_invalid_ticket(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("GCHAT_WEBHOOK_URL", "http://mock-webhook:8080/hook")
    monkeypatch.setattr("presentation.cli.main.setup_logging", lambda **_: None)
    code = run(
        [
            "--ticket-id",
            "0",
            "--ticket-number",
            "20260812000011",
            "--title",
            "CPU alta",
            "--queue",
            "Raw",
        ]
    )
    assert code == 1


def test_run_returns_error_on_webhook_failure(monkeypatch: pytest.MonkeyPatch) -> None:
    class FailingAdapter:
        def __init__(self, *args: Any, **kwargs: Any) -> None:
            pass

        def send(self, payload: dict[str, Any]) -> None:
            raise WebhookDeliveryError("webhook down")

    monkeypatch.setenv("GCHAT_WEBHOOK_URL", "http://mock-webhook:8080/hook")
    monkeypatch.setenv("DEDUP_ENABLED", "false")
    monkeypatch.setenv("WINDOW_ENABLED", "false")
    monkeypatch.setattr("presentation.cli.main.setup_logging", lambda **_: None)
    monkeypatch.setattr(
        "presentation.cli.main.GoogleChatWebhookAdapter",
        FailingAdapter,
    )
    code = run(_cli_args())
    assert code == 1


def test_main_exits_with_run_code(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("presentation.cli.main.run", lambda: 0)
    with pytest.raises(SystemExit) as exc:
        main()
    assert exc.value.code == 0


def test_adapter_logs_webhook_failed(
    caplog: pytest.LogCaptureFixture,
) -> None:
    class BrokenTransport(httpx.BaseTransport):
        def handle_request(self, request: httpx.Request) -> httpx.Response:
            raise httpx.ConnectError("refused", request=request)

    client = httpx.Client(transport=BrokenTransport())
    adapter = GoogleChatWebhookAdapter(
        webhook_url="http://mock-webhook:8080/hook?key=secret",
        client=client,
        ticket_id=9,
    )
    with caplog.at_level(logging.ERROR), pytest.raises(WebhookDeliveryError):
        adapter.send({"text": "fail"})
    failed = [
        record.semantic
        for record in caplog.records
        if getattr(record, "semantic", {}).get("event") == ALERT_WEBHOOK_FAILED
    ]
    assert failed
    assert failed[0]["ticket_id"] == 9
    assert "secret" not in str(failed[0]["webhook_host"])
