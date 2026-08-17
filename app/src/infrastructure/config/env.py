from __future__ import annotations

import os


def env_get(name: str, default: str = "") -> str:
    raw = os.environ.get(name)
    if raw is None:
        return default
    stripped = raw.strip()
    return stripped if stripped else default
