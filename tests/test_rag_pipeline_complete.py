from pathlib import Path
import json

from rag.retriever import LocalVectorRetriever


def test_persistent_vector_store_exists_and_has_vectors():
    retriever = LocalVectorRetriever(top_k=3)
    assert retriever.store.path.exists()
    assert retriever.store.count() == len(retriever.documents)
    assert retriever.embedder.dim > 0


def test_citations_have_source_metadata():
    retriever = LocalVectorRetriever(top_k=3)
    results = retriever.retrieve("UV index protection")
    assert results
    for item in results:
        assert item["id"]
        assert item["url"].startswith("https://")
        assert item["source"]
        assert "score" in item
