from __future__ import annotations

from enum import StrEnum

from application.ports.duplicate_checker import DuplicateCheckerPort
from application.ports.notifier import NotifierPort
from domain.entities.ticket import Ticket
from domain.services.alert_message_formatter import AlertMessageFormatter


class ProcessAlertResult(StrEnum):
    SENT = "sent"
    SKIPPED_DUPLICATE = "skipped_duplicate"


class ProcessAlertUseCase:
    def __init__(
        self,
        notifier: NotifierPort,
        formatter: AlertMessageFormatter | None = None,
        duplicate_checker: DuplicateCheckerPort | None = None,
        dedup_window_minutes: int = 30,
    ) -> None:
        self._notifier = notifier
        self._formatter = formatter or AlertMessageFormatter()
        self._duplicate_checker = duplicate_checker
        self._dedup_window_minutes = dedup_window_minutes

    def execute(self, ticket: Ticket) -> ProcessAlertResult:
        if self._duplicate_checker is not None and self._duplicate_checker.is_duplicate(
            title=ticket.title,
            queue_name=ticket.queue,
            window_minutes=self._dedup_window_minutes,
            exclude_ticket_id=ticket.ticket_id,
        ):
            return ProcessAlertResult.SKIPPED_DUPLICATE
        payload = self._formatter.format(ticket)
        self._notifier.send(payload)
        return ProcessAlertResult.SENT
