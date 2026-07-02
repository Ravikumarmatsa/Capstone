"""IT / Ticket Auto-Resolution Agent (CP06).

Agentic AI system that ingests IT tickets, classifies them with an LLM,
retrieves similar resolutions via RAG, decides on a recommendation, and
either safely auto-resolves or escalates to a human — logging every step.
"""

# Use the OS (Windows) certificate store for HTTPS so downloads work behind
# corporate SSL-inspecting proxies. Must run before any networking imports.
try:  # pragma: no cover - environment dependent
    import truststore

    truststore.inject_into_ssl()
except Exception:  # noqa: BLE001 - truststore is a best-effort enhancement
    pass

__version__ = "0.1.0"
