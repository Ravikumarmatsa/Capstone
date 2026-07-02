"""Ingestion Agent.

Fetches new IT tickets from ServiceNow (or the mock JSON store) and normalizes
them into a consistent shape the rest of the pipeline expects.
"""
from __future__ import annotations

from typing import Any

from ..servicenow_client import ServiceNowClient


def _normalize(raw: dict[str, Any]) -> dict[str, Any]:
    """Map a raw ticket (mock or ServiceNow) to the pipeline shape."""
    return {
        "id": raw.get("id") or raw.get("number") or raw.get("sys_id", ""),
        "short_description": raw.get("short_description", ""),
        "description": raw.get("description", ""),
        "priority": raw.get("priority", "Medium"),
        "status": raw.get("status", "New"),
        "assigned_to": raw.get("assigned_to"),
        "created_at": raw.get("created_at") or raw.get("sys_created_on", ""),
    }


class IngestionAgent:
    def __init__(self, client: ServiceNowClient | None = None) -> None:
        self.client = client or ServiceNowClient()

    def fetch(self) -> list[dict[str, Any]]:
        """Return normalized new tickets ready for classification."""
        return [_normalize(t) for t in self.client.get_new_tickets()]
