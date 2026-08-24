"""Embedding backends.

Primary: sentence-transformers/all-MiniLM-L6-v2 (dense 384-d vectors).
Fallback: deterministic dense projection of TF-IDF vectors for offline tests.
The fallback is explicitly labeled and should not be used as the quality
benchmark for the deployed system.
"""
from __future__ import annotations

import hashlib

import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer

try:
    from sentence_transformers import SentenceTransformer
except Exception:
    SentenceTransformer = None


class DenseEmbedder:
    def __init__(
        self,
        model_name: str = "sentence-transformers/all-MiniLM-L6-v2",
        dim: int = 384,
    ):
        self.model_name = model_name
        self.dim = dim
        self.model = None
        self.vectorizer = None
        self.projection = None

        if SentenceTransformer is not None:
            try:
                self.model = SentenceTransformer(model_name)
                # sentence-transformers renamed this API. Keep a fallback
                # for older installed versions.
                if hasattr(self.model, "get_embedding_dimension"):
                    self.dim = int(self.model.get_embedding_dimension())
                else:
                    self.dim = int(
                        self.model.get_sentence_embedding_dimension()
                    )
            except Exception:
                self.model = None

    @property
    def backend(self) -> str:
        return (
            "sentence-transformers"
            if self.model is not None
            else "dense-tfidf-projection-fallback"
        )

    def fit(self, texts: list[str]) -> np.ndarray:
        if self.model is not None:
            return np.asarray(
                self.model.encode(
                    texts,
                    normalize_embeddings=True,
                    show_progress_bar=False,
                ),
                dtype=np.float32,
            )

        self.vectorizer = TfidfVectorizer(
            stop_words="english",
            ngram_range=(1, 2),
            max_features=5000,
        )
        sparse = self.vectorizer.fit_transform(texts).toarray().astype(
            np.float32
        )

        seed = int(
            hashlib.sha256(self.model_name.encode()).hexdigest()[:8],
            16,
        )
        rng = np.random.default_rng(seed)
        self.projection = rng.standard_normal(
            (sparse.shape[1], self.dim),
            dtype=np.float32,
        )
        self.projection /= max(
            np.linalg.norm(
                self.projection,
                axis=0,
                keepdims=True,
            ).max(),
            1e-8,
        )

        return self._normalize(sparse @ self.projection)

    def encode_query(self, texts: list[str]) -> np.ndarray:
        if self.model is not None:
            return np.asarray(
                self.model.encode(
                    texts,
                    normalize_embeddings=True,
                    show_progress_bar=False,
                ),
                dtype=np.float32,
            )

        if self.vectorizer is None or self.projection is None:
            raise RuntimeError(
                "Fallback embedder must be fitted before querying"
            )

        sparse = self.vectorizer.transform(texts).toarray().astype(
            np.float32
        )
        return self._normalize(sparse @ self.projection)

    @staticmethod
    def _normalize(x: np.ndarray) -> np.ndarray:
        norms = np.linalg.norm(x, axis=1, keepdims=True)
        return x / np.clip(norms, 1e-8, None)
