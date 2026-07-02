"""Knowledge Retrieval Agent (RAG).

Builds a local ChromaDB vector index over the ``knowledge_base/`` runbooks and
retrieves the most relevant runbook snippets for a given ticket.

Embedding backend is pluggable and chosen automatically so the pipeline works
in any environment:

  * ``ollama``  - embeddings from the provided Ollama endpoint (preferred).
  * ``tfidf``   - fully offline scikit-learn TF-IDF vectors (no downloads);
                  used automatically when the endpoint is unreachable.

The backend can be forced via ``retrieval.embedding_backend`` in config
(``auto`` | ``ollama`` | ``tfidf``).
"""
from __future__ import annotations

from typing import Any, Protocol

import chromadb

from ..config import llm_settings, load_config, path

_COLLECTION = "it_runbooks"


class _Embedder(Protocol):
    backend: str

    def embed_documents(self, texts: list[str]) -> list[list[float]]: ...
    def embed_query(self, text: str) -> list[float]: ...


class _TfidfEmbedder:
    """Offline TF-IDF embedder fit on the knowledge-base corpus."""

    backend = "tfidf"

    def __init__(self, corpus: list[str]) -> None:
        from sklearn.feature_extraction.text import TfidfVectorizer

        self._vec = TfidfVectorizer(stop_words="english", max_features=1024)
        # Fit on the KB corpus so the vocabulary/vector space is fixed.
        self._vec.fit(corpus or ["placeholder"])

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        return self._vec.transform(texts).toarray().tolist()

    def embed_query(self, text: str) -> list[float]:
        return self._vec.transform([text]).toarray()[0].tolist()


class _OllamaEmbedder:
    """Embeddings via the provided Ollama endpoint."""

    backend = "ollama"

    def __init__(self, base_url: str, model: str) -> None:
        from langchain_ollama import OllamaEmbeddings

        self._emb = OllamaEmbeddings(base_url=base_url, model=model)

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        return self._emb.embed_documents(texts)

    def embed_query(self, text: str) -> list[float]:
        return self._emb.embed_query(text)


def _load_corpus(kb_dir) -> tuple[list[str], list[str], list[dict[str, str]]]:
    docs, ids, metas = [], [], []
    for md_file in sorted(kb_dir.glob("*.md")):
        docs.append(md_file.read_text(encoding="utf-8"))
        ids.append(md_file.stem)
        metas.append({"source": md_file.name})
    return docs, ids, metas


class RetrievalAgent:
    def __init__(self) -> None:
        cfg = load_config().get("retrieval", {})
        self.top_k = int(cfg.get("top_k", 3))
        self.kb_dir = path(cfg.get("knowledge_base_dir", "knowledge_base"))
        self.store_dir = path(cfg.get("vector_store_dir", "chroma_db"))
        self.requested_backend = cfg.get("embedding_backend", "auto")

        self._docs, self._ids, self._metas = _load_corpus(self.kb_dir)
        self._embedder = self._select_embedder()

        self.store_dir.mkdir(parents=True, exist_ok=True)
        self._client = chromadb.PersistentClient(path=str(self.store_dir))
        self._collection = self._client.get_or_create_collection(name=_COLLECTION)

    # --------------------------------------------------------------- backend
    def _select_embedder(self) -> _Embedder:
        settings = llm_settings()
        want = str(self.requested_backend).lower()

        if want == "tfidf":
            return _TfidfEmbedder(self._docs)

        if want in ("ollama", "auto"):
            try:
                emb = _OllamaEmbedder(settings["base_url"], settings["model"])
                emb.embed_query("connectivity check")  # fail fast if unreachable
                return emb
            except Exception:  # noqa: BLE001 - fall back to offline embedder
                if want == "ollama":
                    raise
                return _TfidfEmbedder(self._docs)

        return _TfidfEmbedder(self._docs)

    @property
    def backend(self) -> str:
        return self._embedder.backend

    # ------------------------------------------------------------------ index
    def build_index(self, force: bool = False) -> int:
        """Embed all runbooks into the vector store. Returns doc count."""
        try:
            existing_backend = (self._collection.metadata or {}).get("backend")
        except Exception:  # noqa: BLE001
            existing_backend = None

        needs_rebuild = (
            force
            or self._collection.count() == 0
            or existing_backend != self._embedder.backend
        )
        if not needs_rebuild:
            return self._collection.count()

        # Recreate the collection tagged with the active backend.
        try:
            self._client.delete_collection(_COLLECTION)
        except Exception:  # noqa: BLE001
            pass
        self._collection = self._client.get_or_create_collection(
            name=_COLLECTION, metadata={"backend": self._embedder.backend}
        )

        if self._docs:
            embeddings = self._embedder.embed_documents(self._docs)
            self._collection.add(
                ids=self._ids,
                documents=self._docs,
                embeddings=embeddings,
                metadatas=self._metas,
            )
        return self._collection.count()

    # --------------------------------------------------------------- retrieve
    def retrieve(self, ticket: dict[str, Any]) -> list[dict[str, Any]]:
        """Return the top-k most relevant runbook snippets for a ticket."""
        if self._collection.count() == 0:
            self.build_index()

        query = " ".join(
            [
                ticket.get("category", ""),
                ticket.get("short_description", ""),
                ticket.get("description", ""),
            ]
        ).strip()

        q_vec = self._embedder.embed_query(query)
        result = self._collection.query(query_embeddings=[q_vec], n_results=self.top_k)
        docs = result.get("documents", [[]])[0]
        metas = result.get("metadatas", [[]])[0]
        dists = result.get("distances", [[]])[0]

        hits: list[dict[str, Any]] = []
        for doc, meta, dist in zip(docs, metas, dists):
            hits.append(
                {
                    "source": (meta or {}).get("source", ""),
                    "content": doc,
                    "distance": dist,
                }
            )
        return hits

    @staticmethod
    def format_context(hits: list[dict[str, Any]]) -> str:
        """Join retrieved snippets into a single context string for the LLM."""
        return "\n\n---\n\n".join(
            f"[Source: {h['source']}]\n{h['content']}" for h in hits
        )
