from __future__ import annotations

from typing import Protocol


class AlertDispatchLedgerPort(Protocol):
    def try_claim(
        self,
        *,
        ticket_id: int,
        title: str,
        queue_name: str,
        window_minutes: int,
    ) -> bool: ...

    def release(self, *, ticket_id: int) -> None: ...
