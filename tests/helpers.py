"""Shared test helpers.

Adds the project root to ``sys.path`` so ``import src...`` works when tests are
run from anywhere, and provides a fake ServiceNow client that records ticket
updates in memory (so tests never touch ``data/tickets.json``).
"""
from __future__ import annotations

import pathlib
import sys
from typing import Any

# Make the project root importable (so `from src...` works).
ROOT = pathlib.Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


class FakeServiceNowClient:
    """In-memory stand-in for ServiceNowClient used by the Execution Agent."""

    def __init__(self, tickets: list[dict[str, Any]] | None = None) -> None:
        self.tickets = {t["id"]: dict(t) for t in (tickets or [])}
        self.updates: list[tuple[str, dict[str, Any]]] = []

    def get_new_tickets(self) -> list[dict[str, Any]]:
        return [t for t in self.tickets.values() if t.get("status") == "New"]

    def update_ticket(self, ticket_id: str, updates: dict[str, Any]) -> dict[str, Any]:
        self.updates.append((ticket_id, updates))
        record = self.tickets.setdefault(ticket_id, {"id": ticket_id})
        record.update(updates)
        return record
