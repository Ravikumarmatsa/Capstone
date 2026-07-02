"""Tests for the offline Resolution Decision Agent.

Forces the offline path and verifies the runbook step-extraction plus the
confidence heuristic (0.85 strong match, 0.7 weak match, 0.3 no steps).
"""
from __future__ import annotations

import unittest
from unittest.mock import patch

from tests.helpers import ROOT  # noqa: F401 - ensures project root on sys.path

from src.agents.decision import DecisionAgent

RUNBOOK_WITH_STEPS = (
    "# Password Reset\n\n"
    "## Symptoms\nUser cannot log in.\n\n"
    "## Resolution Steps\n"
    "1. Verify the user's identity.\n"
    "2. Reset the password in AD.\n"
    "3. Confirm the user can log in.\n\n"
    "## Verification\nUser logs in successfully.\n"
)

RUNBOOK_NO_STEPS = "# Notes\n\nThis document has no numbered resolution steps.\n"


class TestOfflineDecision(unittest.TestCase):
    def setUp(self) -> None:
        self.agent = DecisionAgent()
        self.classification = {"category": "Password Reset", "severity": "High"}

    @patch("src.agents.decision.is_available", return_value=False)
    def test_strong_match_high_confidence(self, _mock) -> None:
        hits = [{"source": "password_reset.md", "content": RUNBOOK_WITH_STEPS, "distance": 0.1}]
        result = self.agent.decide({}, self.classification, hits, "ctx")
        self.assertEqual(result["method"], "offline_runbook")
        self.assertEqual(result["confidence"], 0.85)
        self.assertEqual(
            result["resolution_steps"],
            [
                "Verify the user's identity.",
                "Reset the password in AD.",
                "Confirm the user can log in.",
            ],
        )

    @patch("src.agents.decision.is_available", return_value=False)
    def test_weak_match_medium_confidence(self, _mock) -> None:
        # Steps found, but the top runbook does not match the category.
        hits = [{"source": "vpn_connectivity.md", "content": RUNBOOK_WITH_STEPS, "distance": 0.4}]
        result = self.agent.decide({}, self.classification, hits, "ctx")
        self.assertEqual(result["confidence"], 0.7)

    @patch("src.agents.decision.is_available", return_value=False)
    def test_no_steps_low_confidence(self, _mock) -> None:
        hits = [{"source": "password_reset.md", "content": RUNBOOK_NO_STEPS, "distance": 0.9}]
        result = self.agent.decide({}, self.classification, hits, "ctx")
        self.assertEqual(result["confidence"], 0.3)
        self.assertEqual(result["resolution_steps"], [])


if __name__ == "__main__":
    unittest.main()
