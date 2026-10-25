"""Small local-only ``.env`` loader for the browser demo entry point.

It intentionally has no third-party dependency, never logs values, and leaves
already-exported process environment variables authoritative.
"""

from __future__ import annotations

import os
from pathlib import Path


REPOSITORY_ROOT = Path(__file__).resolve().parents[3]


def load_local_env(path: Path | None = None) -> None:
    """Load simple ``KEY=value`` entries from an ignored local ``.env`` file."""

    env_path = path or REPOSITORY_ROOT / ".env"
    if not env_path.is_file():
        return
    for raw_line in env_path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        if line.startswith("export "):
            line = line.removeprefix("export ").lstrip()
        if "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        if not key.isidentifier():
            continue
        value = value.strip()
        if len(value) >= 2 and value[0] == value[-1] and value[0] in {"'", '"'}:
            value = value[1:-1]
        os.environ.setdefault(key, value)
