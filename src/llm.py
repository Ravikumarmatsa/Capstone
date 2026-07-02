"""LLM access via the provided Ollama endpoint (llama3.2).

Wraps ``langchain_ollama.ChatOllama`` and adds a helper that reliably parses
JSON out of the model's response (LLMs sometimes wrap JSON in prose or code
fences).
"""
from __future__ import annotations

import json
import re
from functools import lru_cache
from typing import Any

import requests
from langchain_ollama import ChatOllama

from .config import llm_settings


class LLMUnavailableError(RuntimeError):
    """Raised when the LLM endpoint cannot be reached."""


@lru_cache(maxsize=1)
def is_available(timeout: float = 4.0) -> bool:
    """Return True if the Ollama endpoint is reachable (cached per run).

    Used to decide, at runtime, whether to use the LLM or fall back to the
    offline path. Checked once and cached so we do not probe repeatedly.
    """
    base = llm_settings()["base_url"].rstrip("/")
    try:
        resp = requests.get(f"{base}/api/tags", timeout=timeout)
        return resp.status_code == 200
    except Exception:  # noqa: BLE001 - any failure means "not available"
        return False


@lru_cache(maxsize=1)
def get_llm(temperature: float = 0.0) -> ChatOllama:
    """Return a cached ChatOllama client pointed at the provided endpoint."""
    settings = llm_settings()
    return ChatOllama(
        base_url=settings["base_url"],
        model=settings["model"],
        temperature=temperature,
    )


def invoke(prompt: str, temperature: float = 0.0) -> str:
    """Send a prompt to the LLM and return the text response."""
    try:
        response = get_llm(temperature).invoke(prompt)
    except Exception as exc:  # noqa: BLE001 - normalize to a clear error type
        raise LLMUnavailableError(str(exc)) from exc
    return getattr(response, "content", str(response))



def extract_json(text: str) -> dict[str, Any]:
    """Best-effort extraction of a JSON object from an LLM response.

    Handles code fences and surrounding prose. Raises ``ValueError`` if no
    valid JSON object can be found.
    """
    # Strip ```json ... ``` or ``` ... ``` fences.
    fenced = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", text, re.DOTALL)
    candidate = fenced.group(1) if fenced else None

    if candidate is None:
        # Fall back to the first {...} block.
        brace = re.search(r"\{.*\}", text, re.DOTALL)
        candidate = brace.group(0) if brace else None

    if candidate is None:
        raise ValueError(f"No JSON object found in LLM response: {text!r}")

    return json.loads(candidate)


def invoke_json(prompt: str, temperature: float = 0.0) -> dict[str, Any]:
    """Invoke the LLM and parse a JSON object from the response."""
    return extract_json(invoke(prompt, temperature))
