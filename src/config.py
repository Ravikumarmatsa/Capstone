"""Configuration loading for the auto-resolution agent.

Loads YAML config from ``config/`` and secrets from the environment (``.env``).
Credentials are never hard-coded — they come from environment variables.
"""
from __future__ import annotations

import os
from functools import lru_cache
from pathlib import Path
from typing import Any

import yaml
from dotenv import load_dotenv

# Project root = parent of this file's parent (src/ -> project root).
ROOT = Path(__file__).resolve().parent.parent

# Load environment variables from .env (if present).
load_dotenv(ROOT / ".env")


def _read_yaml(path: Path) -> dict[str, Any]:
    with open(path, "r", encoding="utf-8") as fh:
        return yaml.safe_load(fh) or {}


@lru_cache(maxsize=1)
def load_config() -> dict[str, Any]:
    """Return the merged application configuration."""
    servicenow = _read_yaml(ROOT / "config" / "servicenow_config.yaml")
    logging_cfg = _read_yaml(ROOT / "config" / "logging_config.yaml")
    return {
        "root": str(ROOT),
        "servicenow": servicenow.get("servicenow", {}),
        "categories": servicenow.get("categories", []),
        "auto_resolution": servicenow.get("auto_resolution", {}),
        "retrieval": servicenow.get("retrieval", {}),
        "logging": logging_cfg,
    }


def get_env(name: str, default: str | None = None) -> str | None:
    """Read an environment variable (used for secrets/endpoints)."""
    value = os.getenv(name)
    return value if value not in (None, "") else default


def llm_settings() -> dict[str, str]:
    """LLM connection settings from the environment."""
    return {
        "base_url": get_env("OLLAMA_BASE_URL", "http://34.207.216.209:11434"),
        "model": get_env("OLLAMA_MODEL", "llama3.2"),
    }


def path(*parts: str) -> Path:
    """Build an absolute path under the project root."""
    return ROOT.joinpath(*parts)
