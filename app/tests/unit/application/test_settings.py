from __future__ import annotations

from pathlib import Path

import pytest

from infrastructure.config.dotenv_loader import load_dotenv_file
from infrastructure.config.settings import Settings


def test_settings_from_env(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("WEBHOOK_URL", "http://localhost:8080/hook")
    monkeypatch.setenv("HTTP_TIMEOUT_SECONDS", "5")
    monkeypatch.setenv("LOG_LEVEL", "DEBUG")
    monkeypatch.setenv("LOG_FORMAT", "json")
    monkeypatch.setenv("LOG_FILE", "logs/otrs-gchat.log")
    monkeypatch.setenv("DEDUP_ENABLED", "true")
    monkeypatch.setenv("DEDUP_WINDOW_MINUTES", "45")
    monkeypatch.setenv("OTRS_DB_HOST", "mariadb")
    monkeypatch.setenv("OTRS_DB_PORT", "3306")
    monkeypatch.setenv("OTRS_DB_NAME", "otrs")
    monkeypatch.setenv("OTRS_DB_USER", "otrs")
    monkeypatch.setenv("OTRS_DB_PASSWORD", "otrssecret")
    monkeypatch.delenv("OTRS_BASE_URL", raising=False)
    settings = Settings.from_env()
    assert settings.webhook_url == "http://localhost:8080/hook"
    assert settings.http_timeout_seconds == 5.0
    assert settings.log_level == "DEBUG"
    assert settings.log_format == "json"
    assert settings.log_file == "logs/otrs-gchat.log"
    assert settings.dedup_enabled is True
    assert settings.dedup_window_minutes == 45
    assert settings.otrs_base_url == "https://portal.ilegra.com/otrs/index.pl"
    assert settings.otrs_db_ready() is True
    assert settings.otrs_db_config()["host"] == "mariadb"


def test_settings_requires_webhook_url(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("WEBHOOK_URL", raising=False)
    with pytest.raises(ValueError, match="WEBHOOK_URL"):
        Settings.from_env()


def test_settings_rejects_invalid_timeout(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("WEBHOOK_URL", "http://localhost:8080/hook")
    monkeypatch.setenv("HTTP_TIMEOUT_SECONDS", "abc")
    with pytest.raises(ValueError, match="HTTP_TIMEOUT_SECONDS"):
        Settings.from_env()


def test_settings_rejects_non_positive_timeout(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("WEBHOOK_URL", "http://localhost:8080/hook")
    monkeypatch.setenv("HTTP_TIMEOUT_SECONDS", "0")
    with pytest.raises(ValueError, match="greater than zero"):
        Settings.from_env()


def test_settings_default_timeout(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("WEBHOOK_URL", "http://localhost:8080/hook")
    monkeypatch.delenv("HTTP_TIMEOUT_SECONDS", raising=False)
    monkeypatch.delenv("LOG_LEVEL", raising=False)
    monkeypatch.delenv("LOG_FORMAT", raising=False)
    monkeypatch.delenv("LOG_FILE", raising=False)
    monkeypatch.delenv("DEDUP_ENABLED", raising=False)
    monkeypatch.delenv("DEDUP_WINDOW_MINUTES", raising=False)
    monkeypatch.delenv("OTRS_DB_HOST", raising=False)
    monkeypatch.delenv("OTRS_DB_PORT", raising=False)
    monkeypatch.delenv("OTRS_DB_NAME", raising=False)
    monkeypatch.delenv("OTRS_DB_USER", raising=False)
    monkeypatch.delenv("OTRS_DB_PASSWORD", raising=False)
    settings = Settings.from_env()
    assert settings.http_timeout_seconds == 10.0
    assert settings.log_level == "INFO"
    assert settings.log_format == "text"
    assert settings.log_file is None
    assert settings.dedup_enabled is False
    assert settings.dedup_window_minutes == 30
    assert settings.otrs_db_ready() is False


def test_settings_rejects_invalid_log_format(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("WEBHOOK_URL", "http://localhost:8080/hook")
    monkeypatch.setenv("LOG_FORMAT", "xml")
    with pytest.raises(ValueError, match="LOG_FORMAT"):
        Settings.from_env()


def test_settings_rejects_invalid_dedup_window(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("WEBHOOK_URL", "http://localhost:8080/hook")
    monkeypatch.setenv("DEDUP_WINDOW_MINUTES", "0")
    with pytest.raises(ValueError, match="DEDUP_WINDOW_MINUTES"):
        Settings.from_env()


def test_settings_rejects_non_integer_dedup_window(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("WEBHOOK_URL", "http://localhost:8080/hook")
    monkeypatch.setenv("DEDUP_WINDOW_MINUTES", "abc")
    with pytest.raises(ValueError, match="DEDUP_WINDOW_MINUTES"):
        Settings.from_env()


def test_settings_rejects_invalid_db_port(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("WEBHOOK_URL", "http://localhost:8080/hook")
    monkeypatch.setenv("OTRS_DB_PORT", "0")
    with pytest.raises(ValueError, match="OTRS_DB_PORT"):
        Settings.from_env()


def test_settings_rejects_non_integer_db_port(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("WEBHOOK_URL", "http://localhost:8080/hook")
    monkeypatch.setenv("OTRS_DB_PORT", "xyz")
    with pytest.raises(ValueError, match="OTRS_DB_PORT"):
        Settings.from_env()


def test_settings_otrs_db_config_requires_ready(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("WEBHOOK_URL", "http://localhost:8080/hook")
    monkeypatch.delenv("OTRS_DB_HOST", raising=False)
    settings = Settings.from_env()
    with pytest.raises(ValueError, match="incomplete"):
        settings.otrs_db_config()


def test_settings_loads_dotenv_when_enabled(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    env_file = tmp_path / ".env"
    env_file.write_text(
        "WEBHOOK_URL=https://from-dotenv/hook\nHTTP_TIMEOUT_SECONDS=7\n",
        encoding="utf-8",
    )

    def _load(*, override: bool = False) -> Path:
        load_dotenv_file(env_file, override=override)
        return env_file

    monkeypatch.delenv("OTRS_DISABLE_DOTENV", raising=False)
    monkeypatch.delenv("WEBHOOK_URL", raising=False)
    monkeypatch.delenv("HTTP_TIMEOUT_SECONDS", raising=False)
    monkeypatch.setattr(
        "infrastructure.config.settings.load_project_dotenv",
        _load,
    )
    settings = Settings.from_env()
    assert settings.webhook_url == "https://from-dotenv/hook"
    assert settings.http_timeout_seconds == 7.0
