from __future__ import annotations

import os
from pathlib import Path


def project_root() -> Path:
    return Path(__file__).resolve().parents[2]


def default_paths_env_path() -> Path:
    return project_root() / "configs" / "paths.env"


def parse_env_file(env_path: Path) -> dict[str, str]:
    if not env_path.exists():
        return {}

    values: dict[str, str] = {}
    for raw_line in env_path.read_text().splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        if line.startswith("export "):
            line = line[len("export ") :]
        if "=" not in line:
            continue
        key, value = line.split("=", 1)
        values[key.strip()] = value.strip().strip("'\"")
    return values


def load_runtime_env(env_path: Path | None = None) -> dict[str, str]:
    config_values = parse_env_file(env_path or default_paths_env_path())
    merged = dict(config_values)
    merged.update(os.environ)
    return merged
