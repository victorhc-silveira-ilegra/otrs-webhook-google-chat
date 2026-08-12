from __future__ import annotations

import os
from dataclasses import dataclass

from infrastructure.config.dotenv_loader import load_project_dotenv


def _parse_bool(raw: str) -> bool:
    return raw.strip().lower() in {"1", "true", "yes", "on"}


@dataclass(frozen=True, slots=True)
class Settings:
    webhook_url: str
    http_timeout_seconds: float
    log_level: str
    log_format: str
    log_file: str | None
    dedup_enabled: bool
    dedup_window_minutes: int
    otrs_base_url: str
    otrs_db_host: str | None
    otrs_db_port: int
    otrs_db_name: str | None
    otrs_db_user: str | None
    otrs_db_password: str | None

    def otrs_db_ready(self) -> bool:
        return bool(
            self.otrs_db_host
            and self.otrs_db_name
            and self.otrs_db_user
            and self.otrs_db_password
        )

    def otrs_db_config(self) -> dict[str, str | int]:
        if not self.otrs_db_ready():
            raise ValueError("OTRS database settings are incomplete")
        return {
            "host": self.otrs_db_host or "",
            "port": self.otrs_db_port,
            "database": self.otrs_db_name or "",
            "user": self.otrs_db_user or "",
            "password": self.otrs_db_password or "",
        }

    @classmethod
    def from_env(cls) -> Settings:
        if not _parse_bool(os.environ.get("OTRS_DISABLE_DOTENV", "false")):
            load_project_dotenv(override=True)
        webhook_url = os.environ.get("WEBHOOK_URL", "").strip()
        if not webhook_url:
            raise ValueError("WEBHOOK_URL environment variable is required")
        timeout_raw = os.environ.get("HTTP_TIMEOUT_SECONDS", "10").strip()
        try:
            timeout = float(timeout_raw)
        except ValueError as exc:
            raise ValueError("HTTP_TIMEOUT_SECONDS must be a number") from exc
        if timeout <= 0:
            raise ValueError("HTTP_TIMEOUT_SECONDS must be greater than zero")
        log_level = os.environ.get("LOG_LEVEL", "INFO").strip().upper() or "INFO"
        log_format = os.environ.get("LOG_FORMAT", "text").strip().lower() or "text"
        if log_format not in {"text", "json"}:
            raise ValueError("LOG_FORMAT must be 'text' or 'json'")
        log_file_raw = os.environ.get("LOG_FILE", "").strip()
        log_file = log_file_raw or None
        dedup_enabled = _parse_bool(os.environ.get("DEDUP_ENABLED", "false"))
        window_raw = os.environ.get("DEDUP_WINDOW_MINUTES", "30").strip()
        try:
            dedup_window_minutes = int(window_raw)
        except ValueError as exc:
            raise ValueError("DEDUP_WINDOW_MINUTES must be an integer") from exc
        if dedup_window_minutes <= 0:
            raise ValueError("DEDUP_WINDOW_MINUTES must be greater than zero")
        otrs_base_url = (
            os.environ.get(
                "OTRS_BASE_URL",
                "https://portal.ilegra.com/otrs/index.pl",
            ).strip()
            or "https://portal.ilegra.com/otrs/index.pl"
        )
        otrs_db_host = os.environ.get("OTRS_DB_HOST", "").strip() or None
        port_raw = os.environ.get("OTRS_DB_PORT", "3306").strip()
        try:
            otrs_db_port = int(port_raw)
        except ValueError as exc:
            raise ValueError("OTRS_DB_PORT must be an integer") from exc
        if otrs_db_port <= 0:
            raise ValueError("OTRS_DB_PORT must be greater than zero")
        otrs_db_name = os.environ.get("OTRS_DB_NAME", "").strip() or None
        otrs_db_user = os.environ.get("OTRS_DB_USER", "").strip() or None
        password_raw = os.environ.get("OTRS_DB_PASSWORD")
        otrs_db_password = password_raw or None
        return cls(
            webhook_url=webhook_url,
            http_timeout_seconds=timeout,
            log_level=log_level,
            log_format=log_format,
            log_file=log_file,
            dedup_enabled=dedup_enabled,
            dedup_window_minutes=dedup_window_minutes,
            otrs_base_url=otrs_base_url,
            otrs_db_host=otrs_db_host,
            otrs_db_port=otrs_db_port,
            otrs_db_name=otrs_db_name,
            otrs_db_user=otrs_db_user,
            otrs_db_password=otrs_db_password,
        )
