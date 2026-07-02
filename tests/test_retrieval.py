"""Tests for the RAG Knowledge Retrieval Agent.

Builds the vector index over the runbooks and verifies that the correct runbook
is retrieved for representative tickets. Works with either embedding backend
(``tfidf`` offline or ``ollama`` online).
"""
from __future__ import annotations

import unittest

from tests.helpers import ROOT  # noqa: F401 - ensures project root on sys.path

from src.agents.retrieval import RetrievalAgent

EXPECTED_TOP_SOURCE = [
    ("Password Reset", "Cannot log in - forgot my password", "password_reset.md"),
    ("VPN Connectivity", "VPN keeps disconnecting", "vpn_connectivity.md"),
    ("Disk Space Cleanup", "Low disk space on C drive", "disk_space_cleanup.md"),
    ("Printer Issue", "Office printer shows offline", "printer_issue.md"),
]


class TestRetrieval(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.agent = RetrievalAgent()
        cls.count = cls.agent.build_index(force=True)

    def test_index_built(self) -> None:
        self.assertGreaterEqual(self.count, 7)
        self.assertIn(self.agent.backend, ("tfidf", "ollama"))

    def test_top_runbook_matches_category(self) -> None:
        for category, text, expected_source in EXPECTED_TOP_SOURCE:
            with self.subTest(category=category):
                hits = self.agent.retrieve(
                    {"category": category, "short_description": text, "description": ""}
                )
                self.assertTrue(hits, "expected at least one hit")
                self.assertEqual(hits[0]["source"], expected_source)

    def test_format_context_includes_sources(self) -> None:
        hits = self.agent.retrieve(
            {"category": "Password Reset", "short_description": "forgot password", "description": ""}
        )
        context = RetrievalAgent.format_context(hits)
        self.assertIn("[Source:", context)


if __name__ == "__main__":
    unittest.main()
