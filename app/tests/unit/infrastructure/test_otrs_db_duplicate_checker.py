from __future__ import annotations

from typing import Any
from unittest.mock import MagicMock

import pytest

from infrastructure.adapters.otrs_db_duplicate_checker import (
    OTRSDatabaseDuplicateChecker,
)
from infrastructure.logging.events import ALERT_DEDUP_CHECK_FAILED


def test_is_duplicate_returns_true_when_count_positive(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    cursor = MagicMock()
    cursor.fetchone.return_value = (2,)
    conn = MagicMock()
    conn.cursor.return_value = cursor
    monkeypatch.setattr(
        "infrastructure.adapters.otrs_db_duplicate_checker.pymysql.connect",
        lambda **_: conn,
    )
    checker = OTRSDatabaseDuplicateChecker(
        {
            "host": "mariadb",
            "port": 3306,
            "database": "otrs",
            "user": "otrs",
            "password": "otrssecret",
        }
    )

    assert (
        checker.is_duplicate(
            title="CPU Alta",
            queue_name="CloudTeam",
            window_minutes=30,
            exclude_ticket_id=10,
        )
        is True
    )
    cursor.execute.assert_called_once()
    args = cursor.execute.call_args.args
    assert args[1][0] == "CPU Alta"
    assert args[1][1] == "CloudTeam"
    assert args[1][3] == 10
    cursor.close.assert_called_once()
    conn.close.assert_called_once()


def test_is_duplicate_returns_false_when_count_zero(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    cursor = MagicMock()
    cursor.fetchone.return_value = (0,)
    conn = MagicMock()
    conn.cursor.return_value = cursor
    monkeypatch.setattr(
        "infrastructure.adapters.otrs_db_duplicate_checker.pymysql.connect",
        lambda **_: conn,
    )
    checker = OTRSDatabaseDuplicateChecker(
        {
            "host": "mariadb",
            "port": 3306,
            "database": "otrs",
            "user": "otrs",
            "password": "otrssecret",
        }
    )

    assert (
        checker.is_duplicate(
            title="CPU Alta",
            queue_name="CloudTeam",
            window_minutes=30,
            exclude_ticket_id=10,
        )
        is False
    )


def test_is_duplicate_fail_open_on_connection_error(
    monkeypatch: pytest.MonkeyPatch,
    caplog: pytest.LogCaptureFixture,
) -> None:
    def boom(**_: Any) -> None:
        raise RuntimeError("db down")

    monkeypatch.setattr(
        "infrastructure.adapters.otrs_db_duplicate_checker.pymysql.connect",
        boom,
    )
    checker = OTRSDatabaseDuplicateChecker(
        {
            "host": "mariadb",
            "port": 3306,
            "database": "otrs",
            "user": "otrs",
            "password": "otrssecret",
        }
    )

    with caplog.at_level("WARNING"):
        result = checker.is_duplicate(
            title="CPU Alta",
            queue_name="CloudTeam",
            window_minutes=30,
            exclude_ticket_id=10,
        )

    assert result is False
    assert any(
        getattr(record, "semantic", {}).get("event") == ALERT_DEDUP_CHECK_FAILED
        for record in caplog.records
        if hasattr(record, "semantic")
    )
