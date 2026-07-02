"""Sequential orchestrator.

Wires the agents into a simple LangChain-style sequential pipeline and records a
structured audit entry at every stage:

    Ingestion -> Classification -> Retrieval (RAG) -> Decision -> Execution

Each ticket is processed independently and the full decision trail is written to
the JSON audit log for explainability.
"""
from __future__ import annotations

from typing import Any

from .agents.classification import ClassificationAgent
from .agents.decision import DecisionAgent
from .agents.execution import ExecutionAgent
from .agents.ingestion import IngestionAgent
from .agents.retrieval import RetrievalAgent
from .llm import is_available
from .logging_setup import AuditTrail, setup_logging


class Orchestrator:
    def __init__(self) -> None:
        self.log = setup_logging()
        self.audit = AuditTrail()
        self.ingestion = IngestionAgent()
        self.classifier = ClassificationAgent()
        self.retriever = RetrievalAgent()
        self.decider = DecisionAgent()
        self.executor = ExecutionAgent()

        self.llm_online = is_available()
        self.embedding_backend = self.retriever.backend
        self.log.info(
            "Runtime mode -> LLM: %s | Embeddings: %s",
            "online" if self.llm_online else "offline (keyword/runbook fallback)",
            self.embedding_backend,
        )
        # Ensure the vector index exists before processing.
        self.retriever.build_index()

    def process_ticket(self, ticket: dict[str, Any]) -> dict[str, Any]:
        tid = ticket["id"]
        self.log.info("Processing %s: %s", tid, ticket.get("short_description", ""))
        self.audit.record(tid, "ingestion", {"ticket": ticket})

        # 1. Classification
        classification = self.classifier.classify(ticket)
        self.audit.record(tid, "classification", classification)
        self.log.info(
            "  Classified as %s (severity=%s, confidence=%.2f, via %s)",
            classification["category"],
            classification["severity"],
            classification["confidence"],
            classification["method"],
        )

        # 2. Retrieval (RAG)
        hits = self.retriever.retrieve({**ticket, "category": classification["category"]})
        context = self.retriever.format_context(hits)
        self.audit.record(
            tid,
            "retrieval",
            {
                "backend": self.retriever.backend,
                "sources": [h["source"] for h in hits],
            },
        )
        self.log.info("  Retrieved: %s", ", ".join(h["source"] for h in hits) or "none")

        # 3. Decision
        decision = self.decider.decide(ticket, classification, hits, context)
        self.audit.record(tid, "decision", decision)
        self.log.info(
            "  Decision: %d step(s), confidence=%.2f (via %s)",
            len(decision["resolution_steps"]),
            decision["confidence"],
            decision["method"],
        )

        # 4. Execution
        execution = self.executor.execute(ticket, classification, decision)
        self.audit.record(
            tid,
            "execution",
            {k: v for k, v in execution.items() if k != "ticket"},
        )
        self.log.info(
            "  Outcome: %s -> status '%s' (assigned: %s)",
            execution["outcome"].upper(),
            execution["new_status"],
            execution["assigned_to"],
        )

        return {
            "ticket_id": tid,
            "short_description": ticket.get("short_description", ""),
            "classification": classification,
            "retrieved": [h["source"] for h in hits],
            "decision": decision,
            "execution": execution,
        }

    def run(self) -> list[dict[str, Any]]:
        tickets = self.ingestion.fetch()
        self.log.info("Fetched %d new ticket(s).", len(tickets))
        return [self.process_ticket(t) for t in tickets]
