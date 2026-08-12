from __future__ import annotations

from dataclasses import dataclass


class TicketValidationError(ValueError):
    pass


@dataclass(frozen=True, slots=True)
class Ticket:
    ticket_id: int
    ticket_number: str
    title: str
    queue: str

    def __post_init__(self) -> None:
        if self.ticket_id <= 0:
            raise TicketValidationError("ticket_id must be a positive integer")
        if not self.ticket_number.strip():
            raise TicketValidationError("ticket_number must not be empty")
        if not self.title.strip():
            raise TicketValidationError("title must not be empty")
        if not self.queue.strip():
            raise TicketValidationError("queue must not be empty")
