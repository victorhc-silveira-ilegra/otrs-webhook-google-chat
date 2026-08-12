from __future__ import annotations

import pytest

from domain.entities.ticket import Ticket, TicketValidationError


def test_ticket_creates_with_valid_data() -> None:
    ticket = Ticket(
        ticket_id=42,
        ticket_number="20260812000001",
        title="Falha VPN",
        queue="Raw",
    )
    assert ticket.ticket_id == 42
    assert ticket.ticket_number == "20260812000001"
    assert ticket.title == "Falha VPN"
    assert ticket.queue == "Raw"


def test_ticket_rejects_non_positive_id() -> None:
    with pytest.raises(TicketValidationError, match="ticket_id"):
        Ticket(
            ticket_id=0,
            ticket_number="20260812000001",
            title="Falha VPN",
            queue="Raw",
        )


def test_ticket_rejects_empty_number() -> None:
    with pytest.raises(TicketValidationError, match="ticket_number"):
        Ticket(ticket_id=1, ticket_number="   ", title="Falha VPN", queue="Raw")


def test_ticket_rejects_empty_title() -> None:
    with pytest.raises(TicketValidationError, match="title"):
        Ticket(ticket_id=1, ticket_number="20260812000001", title="", queue="Raw")


def test_ticket_rejects_empty_queue() -> None:
    with pytest.raises(TicketValidationError, match="queue"):
        Ticket(
            ticket_id=1,
            ticket_number="20260812000001",
            title="Falha VPN",
            queue="  ",
        )
