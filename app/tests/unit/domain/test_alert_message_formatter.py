from __future__ import annotations

from domain.entities.ticket import Ticket
from domain.services.alert_message_formatter import AlertMessageFormatter


def test_formatter_builds_text_only_payload() -> None:
    ticket = Ticket(
        ticket_id=1,
        ticket_number="20260812000001",
        title="smoke",
        queue="Raw",
    )
    payload = AlertMessageFormatter().format(ticket)

    assert "cardsV2" not in payload
    assert list(payload.keys()) == ["text"]
    assert "20260812000001" in payload["text"]
    assert "smoke" in payload["text"]
    assert (
        "https://portal.ilegra.com/otrs/index.pl"
        "?Action=AgentTicketZoom;TicketID=1" in payload["text"]
    )
    assert "<" in payload["text"] and "|Acessar Ticket>" in payload["text"]


def test_formatter_uses_custom_otrs_base_url() -> None:
    ticket = Ticket(
        ticket_id=7,
        ticket_number="20260812000007",
        title="Disco cheio",
        queue="Raw",
    )
    payload = AlertMessageFormatter(
        otrs_base_url="https://otrs.example/index.pl"
    ).format(ticket)
    assert (
        "https://otrs.example/index.pl?Action=AgentTicketZoom;TicketID=7"
        in (payload["text"])
    )
