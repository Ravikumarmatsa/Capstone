"""Guardrail tests for the Execution Agent (auto-resolve vs escalate policy).

These are the safety-critical tests: they prove the agent only auto-resolves
whitelisted, high-confidence, non-sensitive tickets and escalates everything
else. A fake ServiceNow client is used so no real ticket store is touched.
"""
from __future__ import annotations

import unittest

from tests.helpers import ROOT, FakeServiceNowClient  # noqa: F401

from src.agents.execution import ExecutionAgent


class TestExecutionPolicy(unittest.TestCase):
    def setUp(self) -> None:
        self.client = FakeServiceNowClient()
        self.agent = ExecutionAgent(client=self.client)
        # Pick a whitelisted category and a confidence safely above threshold.
        self.whitelisted = sorted(self.agent.whitelist)[0] if self.agent.whitelist else "Password Reset"
        self.high_conf = min(1.0, self.agent.threshold + 0.05)
        self.low_conf = max(0.0, self.agent.threshold - 0.3)

    def _run(self, category, confidence):
        ticket = {"id": "TST0001"}
        classification = {"category": category}
        decision = {"confidence": confidence, "resolution_steps": ["do a thing"]}
        return self.agent.execute(ticket, classification, decision)

    def test_whitelisted_high_confidence_auto_resolves(self) -> None:
        result = self._run(self.whitelisted, self.high_conf)
        self.assertEqual(result["outcome"], "auto_resolved")
        self.assertEqual(result["new_status"], "Resolved")
        self.assertTrue(result["auto_resolve_allowed"])

    def test_whitelisted_low_confidence_escalates(self) -> None:
        result = self._run(self.whitelisted, self.low_conf)
        self.assertEqual(result["outcome"], "escalated")
        self.assertEqual(result["new_status"], "In Progress")
        self.assertIn("threshold", result["reason"].lower())

    def test_always_human_never_auto_resolves(self) -> None:
        if not self.agent.always_human:
            self.skipTest("no always_human categories configured")
        category = sorted(self.agent.always_human)[0]
        result = self._run(category, 0.99)  # very high confidence, still must escalate
        self.assertEqual(result["outcome"], "escalated")
        self.assertFalse(result["auto_resolve_allowed"])

    def test_non_whitelisted_escalates(self) -> None:
        result = self._run("Printer Issue", 0.99)
        # Printer Issue is intentionally not on the whitelist.
        if "Printer Issue" in self.agent.whitelist:
            self.skipTest("Printer Issue unexpectedly whitelisted")
        self.assertEqual(result["outcome"], "escalated")

    def test_ticket_update_is_written(self) -> None:
        self._run(self.whitelisted, self.high_conf)
        self.assertEqual(len(self.client.updates), 1)
        ticket_id, updates = self.client.updates[0]
        self.assertEqual(ticket_id, "TST0001")
        self.assertIn("status", updates)
        self.assertIn("resolution_comment", updates)


if __name__ == "__main__":
    unittest.main()
