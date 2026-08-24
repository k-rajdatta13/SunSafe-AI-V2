# Phase 5.2 SQLite thread-safety fix

The live integration harness exposed a genuine production/runtime issue:

`sqlite3.ProgrammingError: SQLite objects created in a thread can only be used in that same thread`

The RAG vector store was created on one thread and accessed by the FastAPI/Starlette
worker thread during `/v1/recommend`.

This patch:
- enables cross-thread SQLite use for the store connection;
- serializes store operations with an `RLock`;
- enables a 30-second SQLite busy timeout;
- enables WAL mode;
- adds a regression test that searches the vector store from a worker thread;
- fixes the Qdrant reset path to recreate the collection with the configured vector
  dimension rather than hard-coded dimension 1.

Replace:
`rag/vector_store.py`

Add:
`tests/test_vector_store_threading.py`

Then run:
`.\.venv\Scripts\python.exe -m pytest tests/test_vector_store_threading.py -q`

After that rerun:
`.\.venv\Scripts\python.exe evaluation\live_integration.py`

This is a real integration defect discovered by the audit, not a cosmetic change.
