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


class FakeDispatchLedger:
    def __init__(self, *, claim: bool = True) -> None:
        self.claim = claim
        self.claims: list[dict[str, Any]] = []
        self.releases: list[int] = []

    def try_claim(
        self,
        *,
        ticket_id: int,
        title: str,
        queue_name: str,
        window_minutes: int,
    ) -> bool:
        self.claims.append(
            {
                "ticket_id": ticket_id,
                "title": title,
                "queue_name": queue_name,
                "window_minutes": window_minutes,
            }
        )
        return self.claim

    def release(self, *, ticket_id: int) -> None:
        self.releases.append(ticket_id)


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


def test_should_skip_alert_when_claim_rejected() -> None:
    notifier = FakeNotifier()
    ledger = FakeDispatchLedger(claim=False)
    use_case = ProcessAlertUseCase(
        notifier=notifier,
        dispatch_ledger=ledger,
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
    assert ledger.claims == [
        {
            "ticket_id": 10,
            "title": "CPU Alta em SRV-01",
            "queue_name": "CloudTeam",
            "window_minutes": 30,
        }
    ]
    assert ledger.releases == []


def test_process_alert_sends_when_claim_accepted() -> None:
    notifier = FakeNotifier()
    ledger = FakeDispatchLedger(claim=True)
    use_case = ProcessAlertUseCase(notifier=notifier, dispatch_ledger=ledger)
    ticket = Ticket(
        ticket_id=10,
        ticket_number="20260812000010",
        title="CPU Alta em SRV-01",
        queue="CloudTeam",
    )

    result = use_case.execute(ticket)

    assert result is ProcessAlertResult.SENT
    assert len(notifier.payloads) == 1
    assert len(ledger.claims) == 1
    assert ledger.releases == []


def test_process_alert_releases_claim_when_notifier_fails() -> None:
    notifier = FakeNotifier(fail=True)
    ledger = FakeDispatchLedger(claim=True)
    use_case = ProcessAlertUseCase(notifier=notifier, dispatch_ledger=ledger)
    ticket = Ticket(
        ticket_id=10,
        ticket_number="20260812000010",
        title="CPU Alta em SRV-01",
        queue="CloudTeam",
    )

    with pytest.raises(RuntimeError, match="webhook unavailable"):
        use_case.execute(ticket)

    assert ledger.releases == [10]
