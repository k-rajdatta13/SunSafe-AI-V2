SunSafe AI V2 dependency classification — final proposed split

1. requirements.txt
   Runtime dependencies. sentence-transformers is included because
   rag/embeddings.py defines sentence-transformers/all-MiniLM-L6-v2
   as the PRIMARY embedding backend. The TF-IDF projection is an
   explicitly labeled fallback.

2. requirements-dev.txt
   Test/evaluation dependency: pytest.

3. requirements-optional-qdrant.txt
   Optional Qdrant adapter only. qdrant-client is imported lazily by
   QdrantVectorStore and is not required by the default SQLite vector store.

NEXT VALIDATION ORDER
A. Back up the current .venv/project.
B. Install/verify runtime requirements:
      .\.venv\Scripts\python.exe -m pip install -r requirements.txt
C. Verify:
      .\.venv\Scripts\python.exe -c "import sentence_transformers; print(sentence_transformers.__version__)"
D. Verify the intended embedding backend actually loads:
      .\.venv\Scripts\python.exe -c "from rag.embeddings import DenseEmbedder; e=DenseEmbedder(); print(e.backend, e.dim)"
E. Run the RAG tests and full pytest suite.
F. Run the Phase 5 evaluations again.
G. Only after all of that decide whether Qdrant needs to be installed.

Do not install qdrant-client unless the Qdrant backend is intentionally being exercised.
Do not commit or distribute .env or API keys.
