from __future__ import annotations

import logging

import pytest

from infrastructure.logging.emit import log_event


def test_log_event_attaches_semantic_payload(caplog: pytest.LogCaptureFixture) -> None:
    logger = logging.getLogger("emit-test")
    with caplog.at_level(logging.INFO, logger="emit-test"):
        log_event(logger, logging.INFO, "alert.run.started", ticket_id=1)
    assert caplog.records
    assert caplog.records[0].semantic["event"] == "alert.run.started"
    assert caplog.records[0].semantic["ticket_id"] == 1
