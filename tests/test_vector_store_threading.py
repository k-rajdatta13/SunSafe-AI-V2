import threading

import numpy as np

from rag.vector_store import SQLiteVectorStore


def test_sqlite_vector_store_can_search_from_worker_thread(tmp_path):
    store = SQLiteVectorStore(tmp_path / "vectors.sqlite3", dim=3)
    store.upsert(
        ["a"],
        np.asarray([[1.0, 0.0, 0.0]], dtype=np.float32),
        [{"source": "WHO", "url": "https://who.int", "chunk_id": "a"}],
    )

    result = {}

    def worker():
        result["rows"] = store.search(
            np.asarray([1.0, 0.0, 0.0], dtype=np.float32),
            top_k=1,
        )

    thread = threading.Thread(target=worker)
    thread.start()
    thread.join()

    try:
        assert result["rows"]
        assert result["rows"][0]["id"] == "a"
    finally:
        store.close()
