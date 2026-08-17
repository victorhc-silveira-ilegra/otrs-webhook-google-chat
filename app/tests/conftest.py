from __future__ import annotations

import pytest


@pytest.fixture(autouse=True)
def _disable_project_dotenv(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("OTRS_DISABLE_DOTENV", "1")
    monkeypatch.delenv("GCHAT_WEBHOOK_URL", raising=False)
    monkeypatch.delenv("LOG_DIR", raising=False)
    monkeypatch.delenv("WINDOW_ENABLED", raising=False)
    monkeypatch.delenv("WINDOW_DAYS", raising=False)
    monkeypatch.delenv("WINDOW_START", raising=False)
    monkeypatch.delenv("WINDOW_END", raising=False)
    monkeypatch.delenv("WINDOW_TIMEZONE", raising=False)
