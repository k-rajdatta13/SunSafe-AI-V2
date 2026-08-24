"""Persistent local vector database using SQLite + numpy.

SQLite is accessed from FastAPI/Starlette worker threads during the live
integration tests. The connection is therefore configured for cross-thread
use and all operations are serialized with a re-entrant lock. WAL and a busy
timeout improve read/write behavior without changing the Knowledge Agent API.
"""
from __future__ import annotations

import json
import sqlite3
import threading
from pathlib import Path

import numpy as np


class SQLiteVectorStore:
    def __init__(self, path: Path, dim: int):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.dim = dim
        self._lock = threading.RLock()

        # The FastAPI TestClient/Starlette worker can execute graph nodes in a
        # different thread from the one that constructed the retriever.
        self.conn = sqlite3.connect(
            self.path,
            check_same_thread=False,
            timeout=30.0,
        )
        self.conn.execute("PRAGMA busy_timeout=30000")
        self.conn.execute("PRAGMA journal_mode=WAL")
        self.conn.execute(
            """CREATE TABLE IF NOT EXISTS vectors (
                id TEXT PRIMARY KEY,
                embedding BLOB NOT NULL,
                metadata TEXT NOT NULL
            )"""
        )
        self.conn.commit()

    def reset(self) -> None:
        with self._lock:
            self.conn.execute("DELETE FROM vectors")
            self.conn.commit()

    def upsert(
        self,
        ids: list[str],
        vectors: np.ndarray,
        metadata: list[dict],
    ) -> None:
        rows = []
        for i, vec in enumerate(vectors):
            arr = np.asarray(vec, dtype=np.float32)
            rows.append(
                (
                    ids[i],
                    arr.tobytes(),
                    json.dumps(metadata[i], ensure_ascii=False),
                )
            )

        with self._lock:
            self.conn.executemany(
                "INSERT OR REPLACE INTO vectors(id, embedding, metadata) VALUES(?,?,?)",
                rows,
            )
            self.conn.commit()

    def count(self) -> int:
        with self._lock:
            return int(
                self.conn.execute(
                    "SELECT COUNT(*) FROM vectors"
                ).fetchone()[0]
            )

    def search(
        self,
        query_vector: np.ndarray,
        top_k: int = 4,
    ) -> list[dict]:
        q = np.asarray(query_vector, dtype=np.float32)
        q /= max(np.linalg.norm(q), 1e-8)

        with self._lock:
            rows = self.conn.execute(
                "SELECT id, embedding, metadata FROM vectors"
            ).fetchall()

        scored = []
        for doc_id, blob, meta_json in rows:
            vec = np.frombuffer(blob, dtype=np.float32)
            score = float(
                np.dot(q, vec) / max(np.linalg.norm(vec), 1e-8)
            )
            meta = json.loads(meta_json)
            meta["score"] = round(score, 6)
            meta["id"] = doc_id
            scored.append(meta)

        scored.sort(key=lambda x: x["score"], reverse=True)
        return scored[:top_k]

    def close(self) -> None:
        with self._lock:
            self.conn.close()


class QdrantVectorStore:
    """Optional Qdrant adapter. Install qdrant-client to use it in deployment."""

    def __init__(
        self,
        collection: str,
        dim: int,
        path: str = "./knowledge/index/qdrant",
    ):
        try:
            from qdrant_client import QdrantClient
            from qdrant_client.models import Distance, VectorParams, PointStruct
        except ImportError as exc:
            raise RuntimeError(
                "Install qdrant-client to use the Qdrant backend"
            ) from exc

        self.PointStruct = PointStruct
        self.client = QdrantClient(path=path)
        self.collection = collection
        self.dim = dim

        if not self.client.collection_exists(collection):
            self.client.create_collection(
                collection_name=collection,
                vectors_config=VectorParams(
                    size=dim,
                    distance=Distance.COSINE,
                ),
            )

    def reset(self) -> None:
        self.client.delete_collection(self.collection)
        from qdrant_client.models import Distance, VectorParams
        self.client.create_collection(
            collection_name=self.collection,
            vectors_config=VectorParams(
                size=self.dim,
                distance=Distance.COSINE,
            ),
        )

    def upsert(
        self,
        ids: list[str],
        vectors: np.ndarray,
        metadata: list[dict],
    ) -> None:
        points = [
            self.PointStruct(
                id=i,
                vector=v.tolist(),
                payload=m,
            )
            for i, v, m in zip(ids, vectors, metadata)
        ]
        self.client.upsert(
            collection_name=self.collection,
            points=points,
        )

    def count(self) -> int:
        return self.client.count(
            collection_name=self.collection,
            exact=True,
        ).count

    def search(
        self,
        query_vector: np.ndarray,
        top_k: int = 4,
    ) -> list[dict]:
        results = self.client.query_points(
            collection_name=self.collection,
            query=query_vector.tolist(),
            limit=top_k,
        ).points

        out = []
        for r in results:
            item = dict(r.payload or {})
            item["id"] = str(r.id)
            item["score"] = round(float(r.score), 6)
            out.append(item)
        return out

    def close(self) -> None:
        pass
