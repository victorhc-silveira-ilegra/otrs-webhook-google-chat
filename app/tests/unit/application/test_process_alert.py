from __future__ import annotations

from typing import Any

import pytest

from application.use_cases.process_alert import ProcessAlertResult, ProcessAlertUseCase
from domain.entities.ticket import Ticket


class FakeNotifier:
    def __init__(self, *, fail: bool = False) -> None:
        self.fail = fail
        self.payloads: list[dict[str, Any]] = []

    def send(self, payload: dict[str, Any]) -> None:
        if self.fail:
            raise RuntimeError("webhook unavailable")
        self.payloads.append(payload)


class FakeDuplicateChecker:
    def __init__(self, *, duplicate: bool = False) -> None:
        self.duplicate = duplicate
        self.calls: list[dict[str, Any]] = []

    def is_duplicate(
        self,
        *,
        title: str,
        queue_name: str,
        window_minutes: int,
        exclude_ticket_id: int,
    ) -> bool:
        self.calls.append(
            {
                "title": title,
                "queue_name": queue_name,
                "window_minutes": window_minutes,
                "exclude_ticket_id": exclude_ticket_id,
            }
        )
        return self.duplicate


def test_process_alert_sends_formatted_payload() -> None:
    notifier = FakeNotifier()
    use_case = ProcessAlertUseCase(notifier=notifier)
    ticket = Ticket(
        ticket_id=9,
        ticket_number="20260812000009",
        title="Alerta",
        queue="Raw",
    )

    result = use_case.execute(ticket)

    assert result is ProcessAlertResult.SENT
    assert len(notifier.payloads) == 1
    assert "Alerta" in notifier.payloads[0]["text"]
    assert "cardsV2" not in notifier.payloads[0]
    assert "Acessar Ticket" in notifier.payloads[0]["text"]


def test_process_alert_propagates_notifier_failure() -> None:
    notifier = FakeNotifier(fail=True)
    use_case = ProcessAlertUseCase(notifier=notifier)
    ticket = Ticket(
        ticket_id=9,
        ticket_number="20260812000009",
        title="Alerta",
        queue="Raw",
    )

    with pytest.raises(RuntimeError, match="webhook unavailable"):
        use_case.execute(ticket)


def test_should_skip_alert_when_duplicate_detected() -> None:
    notifier = FakeNotifier()
    dedup = FakeDuplicateChecker(duplicate=True)
    use_case = ProcessAlertUseCase(
        notifier=notifier,
        duplicate_checker=dedup,
        dedup_window_minutes=30,
    )
    ticket = Ticket(
        ticket_id=10,
        ticket_number="20260812000010",
        title="CPU Alta em SRV-01",
        queue="CloudTeam",
    )

    result = use_case.execute(ticket)

    assert result is ProcessAlertResult.SKIPPED_DUPLICATE
    assert notifier.payloads == []
    assert dedup.calls == [
        {
            "title": "CPU Alta em SRV-01",
            "queue_name": "CloudTeam",
            "window_minutes": 30,
            "exclude_ticket_id": 10,
        }
    ]


def test_process_alert_sends_when_not_duplicate() -> None:
    notifier = FakeNotifier()
    dedup = FakeDuplicateChecker(duplicate=False)
    use_case = ProcessAlertUseCase(notifier=notifier, duplicate_checker=dedup)
    ticket = Ticket(
        ticket_id=10,
        ticket_number="20260812000010",
        title="CPU Alta em SRV-01",
        queue="CloudTeam",
    )

    result = use_case.execute(ticket)

    assert result is ProcessAlertResult.SENT
    assert len(notifier.payloads) == 1
    assert len(dedup.calls) == 1
