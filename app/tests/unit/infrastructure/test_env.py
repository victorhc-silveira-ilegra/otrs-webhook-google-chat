from __future__ import annotations

import pytest

from infrastructure.config.env import env_get


def test_env_get_returns_value(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("SAMPLE_VAR", "value")
    assert env_get("SAMPLE_VAR", default="fallback") == "value"


def test_env_get_skips_blank_and_uses_default(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("SAMPLE_VAR", "  ")
    assert env_get("SAMPLE_VAR", default="fallback") == "fallback"


def test_env_get_default_when_missing(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("SAMPLE_VAR", raising=False)
    assert env_get("SAMPLE_VAR", default="fallback") == "fallback"
