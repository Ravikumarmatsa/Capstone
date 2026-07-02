"""Scenario tests for the offline keyword Classification Agent.

Forces the offline path (patching ``is_available`` to False) so the tests are
deterministic and do not depend on the LLM endpoint. Verifies that a
representative ticket for every category is classified correctly.
"""
from __future__ import annotations

import unittest
from unittest.mock import patch

from tests.helpers import ROOT  # noqa: F401 - ensures project root on sys.path

from src.agents.classification import ClassificationAgent

# One representative ticket per category (short_description text).
SCENARIOS = [
    ("Cannot log in - forgot my password", "Password Reset"),
    ("VPN keeps disconnecting when working from home", "VPN Connectivity"),
    ("Low disk space warning on C drive", "Disk Space Cleanup"),
    ("Need admin access to the finance shared folder", "Access Request"),
    ("Please install Node.js and VS Code on my machine", "Software Installation"),
    ("Outlook not sending or receiving emails", "Email Issue"),
    ("Office printer shows offline", "Printer Issue"),
]


class TestOfflineClassification(unittest.TestCase):
    def setUp(self) -> None:
        self.agent = ClassificationAgent()

    @patch("src.agents.classification.is_available", return_value=False)
    def test_each_category_is_classified_correctly(self, _mock) -> None:
        for text, expected in SCENARIOS:
            with self.subTest(category=expected):
                ticket = {"short_description": text, "description": "", "priority": "Medium"}
                result = self.agent.classify(ticket)
                self.assertEqual(result["category"], expected)
                self.assertEqual(result["method"], "offline_keywords")
                # Offline confidence is deliberately capped.
                self.assertLessEqual(result["confidence"], 0.75)
                self.assertGreater(result["confidence"], 0.0)

    @patch("src.agents.classification.is_available", return_value=False)
    def test_unknown_when_no_signal(self, _mock) -> None:
        result = self.agent.classify(
            {"short_description": "xyzzy foobar", "description": "", "priority": "Low"}
        )
        self.assertEqual(result["category"], "Unknown")
        self.assertEqual(result["confidence"], 0.3)


if __name__ == "__main__":
    unittest.main()
