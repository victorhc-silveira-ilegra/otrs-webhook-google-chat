from __future__ import annotations

from typing import Any
from unittest.mock import MagicMock

import pytest
from pymysql.err import IntegrityError

from infrastructure.adapters.otrs_db_alert_dispatch_ledger import (
    OTRSDatabaseAlertDispatchLedger,
    build_dedup_hash,
)
from infrastructure.logging.events import ALERT_DISPATCH_CLAIM_FAILED


def _db_config() -> dict[str, str | int]:
    return {
        "host": "mariadb",
        "port": 3306,
        "database": "otrs",
        "user": "otrs",
        "password": "otrssecret",
    }


def test_build_dedup_hash_is_stable() -> None:
    left = build_dedup_hash(title="CPU Alta", queue_name="CloudTeam")
    right = build_dedup_hash(title="CPU Alta", queue_name="CloudTeam")
    other = build_dedup_hash(title="CPU Alta", queue_name="Raw")
    assert left == right
    assert left != other
    assert len(left) == 64


def test_try_claim_returns_true_on_insert(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    cursor = MagicMock()
    conn = MagicMock()
    conn.cursor.return_value = cursor
    monkeypatch.setattr(
        "infrastructure.adapters.otrs_db_alert_dispatch_ledger.pymysql.connect",
        lambda **_: conn,
    )
    ledger = OTRSDatabaseAlertDispatchLedger(_db_config())

    assert (
        ledger.try_claim(
            ticket_id=10,
            title="CPU Alta",
            queue_name="CloudTeam",
            window_minutes=30,
        )
        is True
    )
    assert cursor.execute.call_count == 2
    insert_sql = cursor.execute.call_args_list[1].args[0]
    assert "INSERT INTO gchat_alert_dispatch" in insert_sql
    conn.commit.assert_called_once()
    cursor.close.assert_called_once()
    conn.close.assert_called_once()


def test_try_claim_returns_false_when_integrity_error_before_connect(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def boom(**_: Any) -> None:
        raise IntegrityError(1062, "Duplicate entry")

    monkeypatch.setattr(
        "infrastructure.adapters.otrs_db_alert_dispatch_ledger.pymysql.connect",
        boom,
    )
    ledger = OTRSDatabaseAlertDispatchLedger(_db_config())

    assert (
        ledger.try_claim(
            ticket_id=10,
            title="CPU Alta",
            queue_name="CloudTeam",
            window_minutes=30,
        )
        is False
    )


def test_try_claim_returns_false_on_integrity_error(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    cursor = MagicMock()
    cursor.execute.side_effect = [None, IntegrityError(1062, "Duplicate entry")]
    conn = MagicMock()
    conn.cursor.return_value = cursor
    monkeypatch.setattr(
        "infrastructure.adapters.otrs_db_alert_dispatch_ledger.pymysql.connect",
        lambda **_: conn,
    )
    ledger = OTRSDatabaseAlertDispatchLedger(_db_config())

    assert (
        ledger.try_claim(
            ticket_id=10,
            title="CPU Alta",
            queue_name="CloudTeam",
            window_minutes=30,
        )
        is False
    )
    conn.rollback.assert_called_once()


def test_try_claim_fail_open_on_connection_error(
    monkeypatch: pytest.MonkeyPatch,
    caplog: pytest.LogCaptureFixture,
) -> None:
    def boom(**_: Any) -> None:
        raise RuntimeError("db down")

    monkeypatch.setattr(
        "infrastructure.adapters.otrs_db_alert_dispatch_ledger.pymysql.connect",
        boom,
    )
    ledger = OTRSDatabaseAlertDispatchLedger(_db_config())

    with caplog.at_level("WARNING"):
        result = ledger.try_claim(
            ticket_id=10,
            title="CPU Alta",
            queue_name="CloudTeam",
            window_minutes=30,
        )

    assert result is True
    assert any(
        getattr(record, "semantic", {}).get("event") == ALERT_DISPATCH_CLAIM_FAILED
        for record in caplog.records
        if hasattr(record, "semantic")
    )


def test_try_claim_rolls_back_on_non_integrity_error(
    monkeypatch: pytest.MonkeyPatch,
    caplog: pytest.LogCaptureFixture,
) -> None:
    cursor = MagicMock()
    cursor.execute.side_effect = [None, RuntimeError("disk full")]
    conn = MagicMock()
    conn.cursor.return_value = cursor
    monkeypatch.setattr(
        "infrastructure.adapters.otrs_db_alert_dispatch_ledger.pymysql.connect",
        lambda **_: conn,
    )
    ledger = OTRSDatabaseAlertDispatchLedger(_db_config())

    with caplog.at_level("WARNING"):
        result = ledger.try_claim(
            ticket_id=10,
            title="CPU Alta",
            queue_name="CloudTeam",
            window_minutes=30,
        )

    assert result is True
    conn.rollback.assert_called_once()
    assert any(
        getattr(record, "semantic", {}).get("event") == ALERT_DISPATCH_CLAIM_FAILED
        for record in caplog.records
        if hasattr(record, "semantic")
    )


def test_release_rolls_back_on_execute_error(
    monkeypatch: pytest.MonkeyPatch,
    caplog: pytest.LogCaptureFixture,
) -> None:
    cursor = MagicMock()
    cursor.execute.side_effect = RuntimeError("disk full")
    conn = MagicMock()
    conn.cursor.return_value = cursor
    monkeypatch.setattr(
        "infrastructure.adapters.otrs_db_alert_dispatch_ledger.pymysql.connect",
        lambda **_: conn,
    )
    ledger = OTRSDatabaseAlertDispatchLedger(_db_config())

    with caplog.at_level("WARNING"):
        ledger.release(ticket_id=10)

    conn.rollback.assert_called_once()
    assert any(
        getattr(record, "semantic", {}).get("event") == ALERT_DISPATCH_CLAIM_FAILED
        for record in caplog.records
        if hasattr(record, "semantic")
    )


def test_release_deletes_claim(monkeypatch: pytest.MonkeyPatch) -> None:
    cursor = MagicMock()
    conn = MagicMock()
    conn.cursor.return_value = cursor
    monkeypatch.setattr(
        "infrastructure.adapters.otrs_db_alert_dispatch_ledger.pymysql.connect",
        lambda **_: conn,
    )
    ledger = OTRSDatabaseAlertDispatchLedger(_db_config())

    ledger.release(ticket_id=10)

    cursor.execute.assert_called_once()
    sql = cursor.execute.call_args.args[0]
    assert "DELETE FROM gchat_alert_dispatch WHERE ticket_id" in sql
    assert cursor.execute.call_args.args[1] == (10,)
    conn.commit.assert_called_once()


def test_release_logs_and_swallows_errors(
    monkeypatch: pytest.MonkeyPatch,
    caplog: pytest.LogCaptureFixture,
) -> None:
    def boom(**_: Any) -> None:
        raise RuntimeError("db down")

    monkeypatch.setattr(
        "infrastructure.adapters.otrs_db_alert_dispatch_ledger.pymysql.connect",
        boom,
    )
    ledger = OTRSDatabaseAlertDispatchLedger(_db_config())

    with caplog.at_level("WARNING"):
        ledger.release(ticket_id=10)

    assert any(
        getattr(record, "semantic", {}).get("event") == ALERT_DISPATCH_CLAIM_FAILED
        for record in caplog.records
        if hasattr(record, "semantic")
    )
