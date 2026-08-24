"""Embedding backends.
Production/offline backend: deterministic dense projection of TF-IDF vectors.
This avoids loading PyTorch/SentenceTransformers and is suitable for the
low-memory deployment target.
"""
from __future__ import annotations
import hashlib
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
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
    @property
    def backend(self) -> str:
        return "dense-tfidf-projection-fallback"
    def fit(self, texts: list[str]) -> np.ndarray:
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
