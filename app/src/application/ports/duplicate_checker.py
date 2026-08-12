from __future__ import annotations

from typing import Protocol


class DuplicateCheckerPort(Protocol):
    def is_duplicate(
        self,
        *,
        title: str,
        queue_name: str,
        window_minutes: int,
        exclude_ticket_id: int,
    ) -> bool: ...
