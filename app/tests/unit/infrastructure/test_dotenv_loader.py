from __future__ import annotations

import os
from pathlib import Path

import pytest

from infrastructure.config.dotenv_loader import load_dotenv_file, load_project_dotenv


def test_load_dotenv_file_sets_missing_keys(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    env_file = tmp_path / ".env"
    env_file.write_text(
        "SAMPLE_KEY=https://example.test/hook\nLOG_LEVEL=DEBUG\n",
        encoding="utf-8",
    )
    monkeypatch.delenv("SAMPLE_KEY", raising=False)
    monkeypatch.delenv("LOG_LEVEL", raising=False)
    load_dotenv_file(env_file, override=False)
    assert os.environ["SAMPLE_KEY"] == "https://example.test/hook"
    assert os.environ["LOG_LEVEL"] == "DEBUG"


def test_load_dotenv_file_does_not_override_existing(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    env_file = tmp_path / ".env"
    env_file.write_text("SAMPLE_KEY=https://from-file/hook\n", encoding="utf-8")
    monkeypatch.setenv("SAMPLE_KEY", "https://from-env/hook")
    load_dotenv_file(env_file, override=False)
    assert os.environ["SAMPLE_KEY"] == "https://from-env/hook"


def test_load_dotenv_file_override_replaces_existing(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    env_file = tmp_path / ".env"
    env_file.write_text(
        'SAMPLE_KEY="https://from-file/hook"\n# comment\n\n=bad\n',
        encoding="utf-8",
    )
    monkeypatch.setenv("SAMPLE_KEY", "https://from-env/hook")
    load_dotenv_file(env_file, override=True)
    assert os.environ["SAMPLE_KEY"] == "https://from-file/hook"


def test_load_dotenv_file_missing_path(tmp_path: Path) -> None:
    load_dotenv_file(tmp_path / "missing.env", override=True)


def test_load_project_dotenv_finds_env_in_parents(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    env_file = tmp_path / ".env"
    env_file.write_text(
        "SAMPLE_KEY=https://ci-dotenv/hook\n",
        encoding="utf-8",
    )
    start = tmp_path / "pkg" / "nested" / "mod.py"
    start.parent.mkdir(parents=True)
    start.write_text("x = 1\n", encoding="utf-8")
    monkeypatch.delenv("SAMPLE_KEY", raising=False)
    found = load_project_dotenv(override=True, start=start)
    assert found == env_file
    assert os.environ["SAMPLE_KEY"] == "https://ci-dotenv/hook"


def test_load_project_dotenv_returns_none_without_file(tmp_path: Path) -> None:
    start = tmp_path / "pkg" / "module.py"
    start.parent.mkdir(parents=True)
    start.write_text("x = 1\n", encoding="utf-8")
    assert load_project_dotenv(override=True, start=start) is None
