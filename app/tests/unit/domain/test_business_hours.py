from __future__ import annotations

from datetime import datetime, time, tzinfo
from zoneinfo import ZoneInfo

import pytest

from domain.services.business_hours import (
    BusinessHoursError,
    BusinessHoursWindow,
    parse_clock_time,
    parse_weekdays,
)

TZ = ZoneInfo("America/Sao_Paulo")


def _window(**kwargs: object) -> BusinessHoursWindow:
    values: dict[str, object] = {
        "enabled": True,
        "weekdays": frozenset({0, 1, 2, 3, 4}),
        "start": time(9, 0),
        "end": time(18, 0),
        "timezone": "America/Sao_Paulo",
    }
    values.update(kwargs)
    return BusinessHoursWindow(**values)  # type: ignore[arg-type]


def test_parse_weekdays_monday_to_friday() -> None:
    assert parse_weekdays("mon,tue,wed,thu,fri") == frozenset({0, 1, 2, 3, 4})


def test_parse_weekdays_rejects_empty() -> None:
    with pytest.raises(BusinessHoursError, match="WINDOW_DAYS"):
        parse_weekdays("  ,  ")


def test_parse_weekdays_rejects_invalid_day() -> None:
    with pytest.raises(BusinessHoursError, match="invalid day"):
        parse_weekdays("mon,foo")


def test_parse_clock_time_rejects_bad_format() -> None:
    with pytest.raises(BusinessHoursError, match="WINDOW_START"):
        parse_clock_time("9:00", field="WINDOW_START")
    with pytest.raises(BusinessHoursError, match="WINDOW_START"):
        parse_clock_time("09-00", field="WINDOW_START")


def test_parse_clock_time_rejects_out_of_range() -> None:
    with pytest.raises(BusinessHoursError, match="WINDOW_END"):
        parse_clock_time("24:00", field="WINDOW_END")


def test_parse_clock_time_rejects_non_digits() -> None:
    with pytest.raises(BusinessHoursError, match="WINDOW_START"):
        parse_clock_time("ab:cd", field="WINDOW_START")


def test_window_rejects_empty_weekdays() -> None:
    with pytest.raises(BusinessHoursError, match="WINDOW_DAYS"):
        _window(weekdays=frozenset())


def test_window_rejects_start_not_before_end() -> None:
    with pytest.raises(BusinessHoursError, match="WINDOW_START"):
        _window(start=time(18, 0), end=time(9, 0))


def test_window_rejects_invalid_timezone() -> None:
    with pytest.raises(BusinessHoursError, match="WINDOW_TIMEZONE"):
        _window(timezone="Not/AZone")


def test_allows_weekday_inside_hours() -> None:
    window = _window()
    instant = datetime(2026, 8, 17, 9, 0, tzinfo=TZ)
    assert window.allows(instant) is True


def test_rejects_weekday_before_start() -> None:
    window = _window()
    instant = datetime(2026, 8, 17, 8, 59, tzinfo=TZ)
    assert window.allows(instant) is False


def test_rejects_weekday_at_end() -> None:
    window = _window()
    instant = datetime(2026, 8, 17, 18, 0, tzinfo=TZ)
    assert window.allows(instant) is False


def test_rejects_weekend() -> None:
    window = _window()
    instant = datetime(2026, 8, 15, 10, 0, tzinfo=TZ)
    assert window.allows(instant) is False


def test_disabled_allows_weekend() -> None:
    window = _window(enabled=False)
    instant = datetime(2026, 8, 15, 10, 0, tzinfo=TZ)
    assert window.allows(instant) is True


def test_naive_datetime_uses_configured_timezone() -> None:
    window = _window()
    instant = datetime(2026, 8, 17, 10, 0)
    assert window.allows(instant) is True


def test_from_env_values_and_clock() -> None:
    window = BusinessHoursWindow.from_env_values(
        enabled=True,
        days="mon,tue,wed,thu,fri",
        start="09:00",
        end="18:00",
        timezone="America/Sao_Paulo",
        clock=lambda: datetime(2026, 8, 17, 10, 0, tzinfo=TZ),
    )
    assert window.allows() is True


def test_default_clock_uses_timezone(monkeypatch: pytest.MonkeyPatch) -> None:
    class FakeDateTime(datetime):
        @classmethod
        def now(cls, tz: tzinfo | None = None) -> datetime:
            return datetime(2026, 8, 17, 10, 0, tzinfo=tz)

    monkeypatch.setattr("domain.services.business_hours.datetime", FakeDateTime)
    window = _window()
    assert window.allows() is True
