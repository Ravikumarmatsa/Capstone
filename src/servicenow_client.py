"""ServiceNow client.

Two modes (selected by ``config/servicenow_config.yaml`` -> mock_mode):

  * **mock mode** (default): reads/writes tickets in ``data/tickets.json`` so the
    project runs fully offline for the demo — no credential required.
  * **live mode**: a thin REST client stub for the ServiceNow Table API. It is
    functional but only used when SERVICENOW_* environment variables are set.

Credentials come from the environment, never from source or YAML.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import requests

from .config import get_env, load_config, path


class ServiceNowClient:
    def __init__(self) -> None:
        cfg = load_config()["servicenow"]
        self.mock_mode: bool = bool(cfg.get("mock_mode", True))
        self.table: str = cfg.get("table", "incident")
        self.api_version: str = cfg.get("api_version", "v2")
        self.instance_url = get_env(cfg.get("instance_url_env", "SERVICENOW_INSTANCE_URL"))
        self.username = get_env(cfg.get("username_env", "SERVICENOW_USERNAME"))
        self.password = get_env(cfg.get("password_env", "SERVICENOW_PASSWORD"))
        self._mock_file: Path = path("data", "tickets.json")

        # Fall back to mock mode if live credentials are incomplete.
        if not self.mock_mode and not all(
            [self.instance_url, self.username, self.password]
        ):
            self.mock_mode = True

    # ------------------------------------------------------------------ mock
    def _read_mock(self) -> list[dict[str, Any]]:
        with open(self._mock_file, "r", encoding="utf-8") as fh:
            return json.load(fh)

    def _write_mock(self, tickets: list[dict[str, Any]]) -> None:
        with open(self._mock_file, "w", encoding="utf-8") as fh:
            json.dump(tickets, fh, indent=2, ensure_ascii=False)

    # ------------------------------------------------------------------ live
    def _base_api(self) -> str:
        return f"{self.instance_url}/api/now/{self.api_version}/table/{self.table}"

    def _auth(self) -> tuple[str, str]:
        return (self.username or "", self.password or "")

    # --------------------------------------------------------------- public
    def get_new_tickets(self) -> list[dict[str, Any]]:
        """Return tickets with status 'New'."""
        if self.mock_mode:
            return [t for t in self._read_mock() if t.get("status") == "New"]

        resp = requests.get(
            self._base_api(),
            params={"sysparm_query": "state=1", "sysparm_limit": "50"},
            auth=self._auth(),
            headers={"Accept": "application/json"},
            timeout=30,
        )
        resp.raise_for_status()
        return resp.json().get("result", [])

    def update_ticket(self, ticket_id: str, updates: dict[str, Any]) -> dict[str, Any]:
        """Update a ticket's fields (status, comments, assignment)."""
        if self.mock_mode:
            tickets = self._read_mock()
            for t in tickets:
                if t.get("id") == ticket_id:
                    t.update(updates)
                    self._write_mock(tickets)
                    return t
            raise KeyError(f"Ticket {ticket_id} not found in mock store")

        resp = requests.patch(
            f"{self._base_api()}/{ticket_id}",
            json=updates,
            auth=self._auth(),
            headers={"Accept": "application/json", "Content-Type": "application/json"},
            timeout=30,
        )
        resp.raise_for_status()
        return resp.json().get("result", {})
