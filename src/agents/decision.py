"""Resolution Decision Agent.

Combines the classification and the retrieved knowledge-base context into a
concrete set of recommended resolution steps plus a confidence score.

Network-first with automatic offline fallback:
  * If the LLM endpoint is reachable, generate steps with the LLM using the
    ``prompts/resolution.txt`` template (grounded in retrieved context).
  * Otherwise, extract the "Resolution Steps" section from the top-ranked
    runbook so the pipeline still produces steps fully offline.
"""
from __future__ import annotations

import re
from typing import Any

from ..config import path
from ..llm import LLMUnavailableError, invoke_json, is_available

_PROMPT = path("prompts", "resolution.txt").read_text(encoding="utf-8")


def _clamp_confidence(value: Any) -> float:
    try:
        conf = float(value)
    except (TypeError, ValueError):
        return 0.0
    return max(0.0, min(1.0, conf))


def _extract_steps_from_runbook(content: str) -> list[str]:
    """Pull the numbered 'Resolution Steps' from a runbook markdown body."""
    # Grab the section under a "Resolution Steps" heading up to the next heading.
    match = re.search(
        r"##\s*Resolution Steps.*?\n(.*?)(?:\n##\s|\Z)",
        content,
        re.DOTALL | re.IGNORECASE,
    )
    section = match.group(1) if match else content
    steps: list[str] = []
    for line in section.splitlines():
        line = line.strip()
        m = re.match(r"^\d+\.\s+(.*)", line)
        if m:
            steps.append(m.group(1).strip())
    return steps


class DecisionAgent:
    # ------------------------------------------------------------- LLM path
    def _decide_llm(
        self, ticket: dict[str, Any], classification: dict[str, Any], context: str
    ) -> dict[str, Any]:
        prompt = _PROMPT.format(
            category=classification.get("category", ""),
            severity=classification.get("severity", ""),
            short_description=ticket.get("short_description", ""),
            description=ticket.get("description", ""),
            context=context,
        )
        result = invoke_json(prompt)
        steps = result.get("resolution_steps") or []
        if isinstance(steps, str):
            steps = [steps]
        return {
            "resolution_steps": steps,
            "confidence": _clamp_confidence(result.get("confidence")),
            "summary": result.get("summary", ""),
            "method": "llm",
        }

    # --------------------------------------------------------- offline path
    def _decide_offline(
        self, classification: dict[str, Any], hits: list[dict[str, Any]]
    ) -> dict[str, Any]:
        top = hits[0] if hits else None
        steps = _extract_steps_from_runbook(top["content"]) if top else []
        source = top["source"] if top else "none"

        # Confidence heuristic: high when the best-matching runbook corresponds
        # to the classified category (a strong, grounded match), lower otherwise.
        category = classification.get("category", "")
        expected = category.strip().lower().replace(" ", "_") + ".md"
        if steps and source == expected:
            confidence = 0.85
        elif steps:
            confidence = 0.7
        else:
            confidence = 0.3

        return {
            "resolution_steps": steps,
            "confidence": round(confidence, 2),
            "summary": f"Steps extracted from runbook '{source}' (offline).",
            "method": "offline_runbook",
        }

    # -------------------------------------------------------------- public
    def decide(
        self,
        ticket: dict[str, Any],
        classification: dict[str, Any],
        hits: list[dict[str, Any]],
        context: str,
    ) -> dict[str, Any]:
        if is_available():
            try:
                return self._decide_llm(ticket, classification, context)
            except LLMUnavailableError:
                pass
        return self._decide_offline(classification, hits)
