from __future__ import annotations

from enum import StrEnum

from application.ports.alert_dispatch_ledger import AlertDispatchLedgerPort
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
        dispatch_ledger: AlertDispatchLedgerPort | None = None,
        dedup_window_minutes: int = 30,
    ) -> None:
        self._notifier = notifier
        self._formatter = formatter or AlertMessageFormatter()
        self._dispatch_ledger = dispatch_ledger
        self._dedup_window_minutes = dedup_window_minutes

    def execute(self, ticket: Ticket) -> ProcessAlertResult:
        claimed = True
        if self._dispatch_ledger is not None:
            claimed = self._dispatch_ledger.try_claim(
                ticket_id=ticket.ticket_id,
                title=ticket.title,
                queue_name=ticket.queue,
                window_minutes=self._dedup_window_minutes,
            )
            if not claimed:
                return ProcessAlertResult.SKIPPED_DUPLICATE
        payload = self._formatter.format(ticket)
        try:
            self._notifier.send(payload)
        except Exception:
            if self._dispatch_ledger is not None and claimed:
                self._dispatch_ledger.release(ticket_id=ticket.ticket_id)
            raise
        return ProcessAlertResult.SENT
