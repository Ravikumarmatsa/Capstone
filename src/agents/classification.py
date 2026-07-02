"""Classification Agent.

Determines the issue category, severity, and a confidence score for an incoming
ticket.

Network-first with automatic offline fallback:
  * If the LLM endpoint is reachable, classify with the LLM using the
    ``prompts/classification.txt`` template.
  * Otherwise, fall back to a deterministic keyword-based classifier so the
    pipeline still runs fully offline.
"""
from __future__ import annotations

from typing import Any

from ..config import load_config, path
from ..llm import LLMUnavailableError, invoke_json, is_available

_PROMPT = path("prompts", "classification.txt").read_text(encoding="utf-8")

# Keyword signals for the offline fallback classifier.
_KEYWORDS: dict[str, list[str]] = {
    "Password Reset": ["password", "forgot", "locked out", "lockout", "unlock",
                        "sign in", "log in", "login"],
    "VPN Connectivity": ["vpn", "disconnect", "tunnel", "remote", "globalconnect"],
    "Disk Space Cleanup": ["disk space", "low disk", "c drive", "c:", "storage",
                           "cleanup", "temp files"],
    "Access Request": ["access", "permission", "shared folder", "admin rights",
                       "write access", "role"],
    "Software Installation": ["install", "installation", "node.js", "vs code",
                              "software", "application"],
    "Email Issue": ["outlook", "email", "mail", "outbox", "exchange", "disconnected"],
    "Printer Issue": ["printer", "print", "spooler", "offline", "laserjet", "queue"],
}


def _clamp_confidence(value: Any) -> float:
    try:
        conf = float(value)
    except (TypeError, ValueError):
        return 0.0
    return max(0.0, min(1.0, conf))


class ClassificationAgent:
    def __init__(self) -> None:
        self.allowed = set(load_config().get("categories", []))

    # ------------------------------------------------------------- LLM path
    def _classify_llm(self, ticket: dict[str, Any]) -> dict[str, Any]:
        prompt = _PROMPT.format(
            short_description=ticket.get("short_description", ""),
            description=ticket.get("description", ""),
            priority=ticket.get("priority", ""),
        )
        result = invoke_json(prompt)
        category = result.get("category", "")
        if category not in self.allowed:
            category = category or "Unknown"
            confidence = min(_clamp_confidence(result.get("confidence")), 0.4)
        else:
            confidence = _clamp_confidence(result.get("confidence"))
        return {
            "category": category,
            "severity": result.get("severity", "Medium"),
            "confidence": confidence,
            "reasoning": result.get("reasoning", ""),
            "method": "llm",
        }

    # --------------------------------------------------------- offline path
    def _classify_offline(self, ticket: dict[str, Any]) -> dict[str, Any]:
        text = (
            f"{ticket.get('short_description', '')} "
            f"{ticket.get('description', '')}"
        ).lower()

        scores: dict[str, int] = {}
        for category, words in _KEYWORDS.items():
            score = sum(1 for w in words if w in text)
            if score:
                scores[category] = score

        if scores:
            best = max(scores, key=lambda k: scores[k])
            # Confidence for an offline heuristic: capped, scales with signal count.
            confidence = round(min(0.75, 0.5 + 0.08 * scores[best]), 2)
            reasoning = f"Offline keyword match ({scores[best]} signal(s))."
        else:
            best = "Unknown"
            confidence = 0.3
            reasoning = "No keyword signals matched."

        return {
            "category": best,
            "severity": ticket.get("priority", "Medium"),
            "confidence": confidence,
            "reasoning": reasoning,
            "method": "offline_keywords",
        }

    # -------------------------------------------------------------- public
    def classify(self, ticket: dict[str, Any]) -> dict[str, Any]:
        if is_available():
            try:
                return self._classify_llm(ticket)
            except LLMUnavailableError:
                pass  # endpoint went away mid-run -> use offline path
        return self._classify_offline(ticket)
