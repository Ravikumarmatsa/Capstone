"""Logging & audit trail for the auto-resolution agent.

Provides:
  * a human-readable console/run logger, and
  * a structured JSON audit trail (one JSON object per line) that records every
    agent decision for explainability.
"""
from __future__ import annotations

import json
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .config import load_config, path

_CONFIGURED = False


def _level(name: str) -> int:
    return getattr(logging, str(name).upper(), logging.INFO)


def setup_logging() -> logging.Logger:
    """Configure and return the application logger (idempotent)."""
    global _CONFIGURED
    logger = logging.getLogger("auto_resolution")
    if _CONFIGURED:
        return logger

    cfg = load_config().get("logging", {})
    console_cfg = cfg.get("console", {})
    run_cfg = cfg.get("run_log", {})

    logger.setLevel(logging.DEBUG)
    logger.handlers.clear()

    # Console handler.
    ch = logging.StreamHandler()
    ch.setLevel(_level(console_cfg.get("level", "INFO")))
    ch.setFormatter(logging.Formatter("%(asctime)s | %(levelname)-7s | %(message)s",
                                      datefmt="%H:%M:%S"))
    logger.addHandler(ch)

    # Run-log file handler.
    run_path = run_cfg.get("path", "logs/run.log")
    fh_path = path(run_path)
    fh_path.parent.mkdir(parents=True, exist_ok=True)
    fh = logging.FileHandler(fh_path, encoding="utf-8")
    fh.setLevel(_level(run_cfg.get("level", "DEBUG")))
    fh.setFormatter(logging.Formatter(
        "%(asctime)s | %(levelname)-7s | %(name)s | %(message)s"))
    logger.addHandler(fh)

    _CONFIGURED = True
    return logger


class AuditTrail:
    """Append structured JSON audit records, one per line (JSONL)."""

    def __init__(self, audit_path: str | Path | None = None) -> None:
        cfg = load_config().get("logging", {}).get("audit", {})
        self.path = path(str(audit_path or cfg.get("path", "logs/audit.jsonl")))
        self.path.parent.mkdir(parents=True, exist_ok=True)

    def record(self, ticket_id: str, stage: str, data: dict[str, Any]) -> None:
        entry = {
            "timestamp": datetime.now(timezone.utc).isoformat(timespec="seconds"),
            "ticket_id": ticket_id,
            "stage": stage,
            **data,
        }
        with open(self.path, "a", encoding="utf-8") as fh:
            fh.write(json.dumps(entry, ensure_ascii=False) + "\n")
