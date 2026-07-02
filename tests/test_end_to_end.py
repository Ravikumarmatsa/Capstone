"""End-to-end pipeline test.

Runs the full orchestrator over all tickets and asserts every ticket produces a
valid outcome and an updated status. The mock ticket store is snapshotted before
the run and restored afterward so the test has no lasting side effects.

Works both offline (TF-IDF + keyword/runbook fallback) and online (LLM), because
it only asserts on the pipeline's structural guarantees, not on which specific
tickets auto-resolve.
"""
from __future__ import annotations

import unittest

from tests.helpers import ROOT  # noqa: F401 - ensures project root on sys.path

import main
from src.config import path
from src.orchestrator import Orchestrator

VALID_OUTCOMES = {"auto_resolved", "escalated"}
VALID_STATUSES = {"Resolved", "In Progress"}


class TestEndToEnd(unittest.TestCase):
    def setUp(self) -> None:
        self.tickets_file = path("data", "tickets.json")
        self._snapshot = self.tickets_file.read_text(encoding="utf-8")

    def tearDown(self) -> None:
        # Restore the original ticket store.
        self.tickets_file.write_text(self._snapshot, encoding="utf-8")

    def test_full_pipeline_processes_all_tickets(self) -> None:
        n = main.reset_tickets()
        results = Orchestrator().run()

        self.assertEqual(len(results), n)
        for r in results:
            with self.subTest(ticket=r["ticket_id"]):
                self.assertIn(r["execution"]["outcome"], VALID_OUTCOMES)
                self.assertIn(r["execution"]["new_status"], VALID_STATUSES)
                self.assertIn(r["classification"]["category"], list_categories())
                self.assertTrue(r["retrieved"], "expected retrieved runbook sources")


def list_categories():
    from src.config import load_config

    return set(load_config().get("categories", [])) | {"Unknown"}


if __name__ == "__main__":
    unittest.main()
