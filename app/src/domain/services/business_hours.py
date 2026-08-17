from __future__ import annotations

from collections.abc import Callable
from datetime import datetime, time
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

WEEKDAY_ALIASES = {
    "mon": 0,
    "tue": 1,
    "wed": 2,
    "thu": 3,
    "fri": 4,
    "sat": 5,
    "sun": 6,
}


class BusinessHoursError(ValueError):
    pass


def parse_weekdays(raw: str) -> frozenset[int]:
    parts = [item.strip().lower() for item in raw.split(",") if item.strip()]
    if not parts:
        raise BusinessHoursError("WINDOW_DAYS must not be empty")
    days: set[int] = set()
    for part in parts:
        if part not in WEEKDAY_ALIASES:
            raise BusinessHoursError(f"WINDOW_DAYS contains invalid day '{part}'")
        days.add(WEEKDAY_ALIASES[part])
    return frozenset(days)


def parse_clock_time(raw: str, *, field: str) -> time:
    text = raw.strip()
    if len(text) != 5 or text[2] != ":":
        raise BusinessHoursError(f"{field} must be HH:MM")
    hour_raw, minute_raw = text.split(":", 1)
    if not hour_raw.isdigit() or not minute_raw.isdigit():
        raise BusinessHoursError(f"{field} must be HH:MM")
    hour = int(hour_raw)
    minute = int(minute_raw)
    if hour > 23 or minute > 59:
        raise BusinessHoursError(f"{field} must be a valid HH:MM")
    return time(hour=hour, minute=minute)


class BusinessHoursWindow:
    def __init__(
        self,
        *,
        enabled: bool,
        weekdays: frozenset[int],
        start: time,
        end: time,
        timezone: str,
        clock: Callable[[], datetime] | None = None,
    ) -> None:
        if not weekdays:
            raise BusinessHoursError("WINDOW_DAYS must not be empty")
        if start >= end:
            raise BusinessHoursError("WINDOW_START must be before WINDOW_END")
        try:
            self._tz = ZoneInfo(timezone)
        except ZoneInfoNotFoundError as exc:
            raise BusinessHoursError("WINDOW_TIMEZONE is invalid") from exc
        self._enabled = enabled
        self._weekdays = weekdays
        self._start = start
        self._end = end
        self._clock = clock or (lambda: datetime.now(tz=self._tz))

    @classmethod
    def from_env_values(
        cls,
        *,
        enabled: bool,
        days: str,
        start: str,
        end: str,
        timezone: str,
        clock: Callable[[], datetime] | None = None,
    ) -> BusinessHoursWindow:
        return cls(
            enabled=enabled,
            weekdays=parse_weekdays(days),
            start=parse_clock_time(start, field="WINDOW_START"),
            end=parse_clock_time(end, field="WINDOW_END"),
            timezone=timezone,
            clock=clock,
        )

    def allows(self, instant: datetime | None = None) -> bool:
        if not self._enabled:
            return True
        current = instant if instant is not None else self._clock()
        if current.tzinfo is None:
            current = current.replace(tzinfo=self._tz)
        else:
            current = current.astimezone(self._tz)
        if current.weekday() not in self._weekdays:
            return False
        now_time = current.time()
        return self._start <= now_time < self._end
