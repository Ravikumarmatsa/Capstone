"""Execution Agent.

Applies the resolution policy and acts on the ticket:

  * **Auto-resolve** when the category is on the whitelist, is not in the
    always-human list, and the decision confidence meets the threshold. A safe,
    simulated automated action is performed and the ticket is marked Resolved.
  * **Escalate** otherwise: recommended steps are posted and the ticket is
    assigned to a human queue.

All actions are simulated (no real infrastructure is touched) and written back
through the ServiceNow client (mock JSON store by default).
"""
from __future__ import annotations

from typing import Any

from ..config import load_config
from ..servicenow_client import ServiceNowClient

# Simulated automated actions available for whitelisted categories.
_AUTOMATED_ACTIONS: dict[str, str] = {
    "Password Reset": "reset_password",
    "VPN Connectivity": "reset_vpn_session",
    "Disk Space Cleanup": "cleanup_disk",
}


class ExecutionAgent:
    def __init__(self, client: ServiceNowClient | None = None) -> None:
        cfg = load_config().get("auto_resolution", {})
        self.threshold = float(cfg.get("confidence_threshold", 0.8))
        self.whitelist = set(cfg.get("whitelist", []))
        self.always_human = set(cfg.get("always_human", []))
        self.client = client or ServiceNowClient()

    def _may_auto_resolve(self, category: str, confidence: float) -> tuple[bool, str]:
        if category in self.always_human:
            return False, "Category always requires human approval."
        if category not in self.whitelist:
            return False, "Category is not on the auto-resolve whitelist."
        if confidence < self.threshold:
            return False, (
                f"Confidence {confidence:.2f} below threshold {self.threshold:.2f}."
            )
        return True, "Whitelisted category with sufficient confidence."

    def execute(
        self,
        ticket: dict[str, Any],
        classification: dict[str, Any],
        decision: dict[str, Any],
    ) -> dict[str, Any]:
        category = classification.get("category", "Unknown")
        confidence = float(decision.get("confidence", 0.0))
        steps = decision.get("resolution_steps", [])
        allowed, reason = self._may_auto_resolve(category, confidence)

        steps_text = "\n".join(f"{i+1}. {s}" for i, s in enumerate(steps)) or "n/a"

        if allowed:
            action = _AUTOMATED_ACTIONS.get(category, "no_op")
            comment = (
                f"[Auto-Resolution Agent] Auto-resolved via '{action}'.\n"
                f"Category: {category} (confidence {confidence:.2f}).\n"
                f"Steps applied:\n{steps_text}"
            )
            updates = {
                "status": "Resolved",
                "assigned_to": "auto-resolution-agent",
                "resolution_comment": comment,
            }
            outcome = "auto_resolved"
        else:
            action = "recommend"
            comment = (
                f"[Auto-Resolution Agent] Recommended steps (human review required).\n"
                f"Category: {category} (confidence {confidence:.2f}). Reason: {reason}\n"
                f"Recommended steps:\n{steps_text}"
            )
            updates = {
                "status": "In Progress",
                "assigned_to": "service-desk-queue",
                "resolution_comment": comment,
            }
            outcome = "escalated"

        updated_ticket = self.client.update_ticket(ticket["id"], updates)

        return {
            "outcome": outcome,
            "action": action,
            "auto_resolve_allowed": allowed,
            "reason": reason,
            "new_status": updates["status"],
            "assigned_to": updates["assigned_to"],
            "comment": comment,
            "ticket": updated_ticket,
        }
