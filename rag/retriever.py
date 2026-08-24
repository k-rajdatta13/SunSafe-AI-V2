"""Persistent dense-vector retrieval over the ingested WHO/CDC corpus."""
from __future__ import annotations
import json
from pathlib import Path
from typing import Any

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from rag.embeddings import DenseEmbedder
from rag.vector_store import SQLiteVectorStore

ROOT = Path(__file__).resolve().parents[1]
CORPUS_PATH = ROOT / "knowledge" / "corpus.json"
INDEX_DIR = ROOT / "knowledge" / "index"
DB_PATH = INDEX_DIR / "vectors.sqlite3"


class LocalVectorRetriever:
    def __init__(self, corpus_path: Path = CORPUS_PATH, top_k: int = 4):
        self.corpus_path = corpus_path
        self.top_k = top_k
        self.documents: list[dict[str, Any]] = json.loads(corpus_path.read_text(encoding="utf-8"))
        self.embedder = DenseEmbedder()
        self.backend = self.embedder.backend + "+sqlite-vector-db"
        self.store = SQLiteVectorStore(DB_PATH, self.embedder.dim)
        # Fit the embedding backend on the bundled corpus on every process start.
        # This keeps the offline fallback queryable without persisting a pickled
        # sklearn model, while the persistent vector DB stores the actual vectors.
        self.lexical = None
        self.lexical_matrix = None
        self._fit_runtime_embedder()
        self._ensure_index()
        self._fit_lexical_reranker()

    def _fit_runtime_embedder(self) -> None:
        if self.embedder.model is None:
            self.embedder.fit([d["text"] for d in self.documents])

    @staticmethod
    def _embedding_text(doc: dict[str, Any]) -> str:
        # Include source title/topic in the representation so short user
        # queries can match authoritative document intent as well as prose.
        return " ".join([
            doc.get("title", ""),
            doc.get("topic", ""),
            doc.get("publisher", ""),
            doc.get("text", ""),
        ])

    def _fit_lexical_reranker(self) -> None:
        # Small hybrid reranker used only when the optional dense model is unavailable.
        # It improves deterministic offline behavior without replacing the persistent vector DB.
        self.lexical = TfidfVectorizer(stop_words="english", ngram_range=(1, 2))
        self.lexical_matrix = self.lexical.fit_transform([self._embedding_text(d) for d in self.documents])

    def _ensure_index(self) -> None:
        metadata_path = INDEX_DIR / "metadata.json"
        index_matches = False
        if metadata_path.exists():
            try:
                metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
                index_matches = (
                    metadata.get("backend") == self.backend
                    and int(metadata.get("dimension", -1)) == int(self.embedder.dim)
                    and int(metadata.get("documents", -1)) == len(self.documents)
                    and self.store.count() == len(self.documents)
                    and self.store.count() > 0
                )
            except (OSError, ValueError, TypeError, json.JSONDecodeError):
                index_matches = False
        if index_matches:
            return
        texts = [self._embedding_text(d) for d in self.documents]
        vectors = self.embedder.fit(texts)
        metadata = self.documents
        self.store.reset()
        self.store.upsert(
            [d["id"] for d in self.documents],
            vectors,
            metadata,
        )
        metadata_path.write_text(
            json.dumps({
                "backend": self.backend,
                "dimension": int(vectors.shape[1]),
                "documents": len(self.documents),
            }, indent=2),
            encoding="utf-8",
        )

    @staticmethod
    def _expand_query(query: str) -> str:
        q = query.strip()
        expansions = {
            "sun safety": "sun_safety UV protection sunscreen shade protective clothing hat sunglasses",
            "protect my skin": "sun protection UV sunscreen shade clothing",
            "outdoor activity": "outdoors sun exposure shade sunscreen UV protection",
            "hot weather": "heat_safety heat illness hydration cooling shade outdoor activity",
            "hot outdoor": "heat_safety heat illness hydration cooling shade outdoor activity",
        }
        extra = " ".join(v for k, v in expansions.items() if k in q.lower())
        return f"{q} {extra}".strip()

    def retrieve(self, query: str, top_k: int | None = None) -> list[dict[str, Any]]:
        if not query.strip():
            return []
        k = top_k or self.top_k
        expanded_query = self._expand_query(query)
        q = self.embedder.encode_query([expanded_query])[0]
        candidates = self.store.search(q, min(max(k * 4, 12), len(self.documents)))
        if self.embedder.model is None and self.lexical is not None and self.lexical_matrix is not None:
            lq = self.lexical.transform([expanded_query])
            lexical_scores = cosine_similarity(lq, self.lexical_matrix).reshape(-1)
            # Hybrid retrieval: union dense-vector candidates with lexical candidates.
            lexical_order = lexical_scores.argsort()[::-1][:min(max(k * 4, 12), len(self.documents))]
            by_id = {item["id"]: item for item in candidates}
            for idx in lexical_order:
                doc = self.documents[int(idx)]
                by_id.setdefault(doc["id"], dict(doc))
            for item in by_id.values():
                idx = next((i for i, d in enumerate(self.documents) if d["id"] == item["id"]), None)
                if idx is not None:
                    dense = float(item.get("score", 0.0))
                    lex = float(lexical_scores[idx])
                    item["dense_score"] = round(dense, 6)
                    item["lexical_score"] = round(lex, 6)
                    item["score"] = round(0.45 * dense + 0.55 * lex, 6)
            candidates = list(by_id.values())
            candidates.sort(key=lambda x: x["score"], reverse=True)
        return candidates[:k]

    def retrieve_for_state(self, state: dict[str, Any]) -> list[dict[str, Any]]:
        query = " ".join([
            state.get("user_query", ""),
            f"UV index {state.get('uv_index', '')}",
            state.get("uv_level", ""),
            state.get("heat_caution", ""),
            state.get("overall_action", ""),
        ])
        return self.retrieve(query, top_k=self.top_k)
