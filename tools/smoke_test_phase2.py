"""Phase 2 smoke test.

Verifies the core agents work end-to-end (ingestion + RAG retrieval), and
attempts an LLM classification if the Ollama endpoint is reachable.

Run from the project root:
    python tools/smoke_test_phase2.py
"""
from __future__ import annotations

import sys
from pathlib import Path

# Ensure the project root is importable when run as a script.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.agents.ingestion import IngestionAgent
from src.agents.retrieval import RetrievalAgent


def main() -> None:
    print("=== 1. Ingestion Agent ===")
    tickets = IngestionAgent().fetch()
    print(f"Fetched {len(tickets)} new tickets.")
    for t in tickets[:3]:
        print(f"  - {t['id']}: {t['short_description']}")

    print("\n=== 2. RAG Retrieval Agent ===")
    rag = RetrievalAgent()
    print(f"Embedding backend: {rag.backend}")
    count = rag.build_index(force=True)
    print(f"Indexed {count} runbooks into ChromaDB.")

    sample = tickets[0] if tickets else {
        "category": "Password Reset",
        "short_description": "forgot password",
        "description": "cannot log in",
    }
    hits = rag.retrieve(sample)
    print(f"Top-{len(hits)} runbooks for '{sample['short_description']}':")
    for h in hits:
        print(f"  - {h['source']} (distance={h['distance']:.4f})")

    print("\n=== 3. Classification Agent (LLM) ===")
    try:
        from src.agents.classification import ClassificationAgent

        result = ClassificationAgent().classify(sample)
        print(f"Classification: {result}")
    except Exception as exc:  # noqa: BLE001 - smoke test, report and continue
        print(f"[skipped/failed] LLM call error: {exc}")
        print("  (Check the Ollama endpoint in .env if this is unexpected.)")

    print("\nSmoke test complete.")


if __name__ == "__main__":
    main()
