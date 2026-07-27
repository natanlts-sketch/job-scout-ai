from __future__ import annotations

import os
from functools import lru_cache
from pathlib import Path
from typing import Any

import yaml
from dotenv import load_dotenv

from src.core import BASE_DIR


@lru_cache(maxsize=1)
def load_config() -> dict[str, Any]:
    load_dotenv(BASE_DIR / ".env")
    config_path = BASE_DIR / "config.yaml"
    with config_path.open("r", encoding="utf-8") as file:
        data = yaml.safe_load(file) or {}
    return data


def reload_config() -> dict[str, Any]:
    load_config.cache_clear()
    return load_config()


def resolve_path(relative: str | Path) -> Path:
    path = Path(relative)
    if path.is_absolute():
        return path
    return BASE_DIR / path


def get_path(key: str) -> Path:
    config = load_config()
    relative = config.get("paths", {}).get(key)
    if not relative:
        raise KeyError(f"Missing paths.{key} in config.yaml")
    return resolve_path(relative)


def env_bool(name: str, default: bool = False) -> bool:
    raw = os.getenv(name)
    if raw is None:
        return default
    return raw.strip().lower() in {"1", "true", "yes", "on"}


def env_int(name: str, default: int) -> int:
    raw = os.getenv(name)
    if raw is None or raw.strip() == "":
        return default
    return int(raw)
