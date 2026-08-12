from __future__ import annotations

from domain.entities.ticket import Ticket


class AlertMessageFormatter:
    def __init__(
        self,
        otrs_base_url: str = "https://portal.ilegra.com/otrs/index.pl",
    ) -> None:
        self._otrs_base_url = otrs_base_url.rstrip("?&")

    def format(self, ticket: Ticket) -> dict[str, str]:
        ticket_link = (
            f"{self._otrs_base_url}?Action=AgentTicketZoom;TicketID={ticket.ticket_id}"
        )
        text = (
            f"*Novo ticket OTRS*\n"
            f"*Numero:* `{ticket.ticket_number}`\n"
            f"*ID:* `{ticket.ticket_id}`\n"
            f"*Titulo:* {ticket.title}\n"
            f"*Link:* <{ticket_link}|Acessar Ticket>"
        )
        return {"text": text}
