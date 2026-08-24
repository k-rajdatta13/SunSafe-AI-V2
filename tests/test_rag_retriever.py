from rag.retriever import LocalVectorRetriever


def test_retriever_returns_ranked_evidence_with_sources():
    retriever = LocalVectorRetriever(top_k=4)
    results = retriever.retrieve("When should I use sun protection for UV index 6?")
    assert results
    assert len(results) <= 4
    assert results[0]["score"] >= results[-1]["score"]
    assert all(item["source"] for item in results)
    assert all(item["url"].startswith("https://") for item in results)


def test_retriever_finds_heat_guidance():
    retriever = LocalVectorRetriever(top_k=4)
    results = retriever.retrieve("How should I stay safe during hot outdoor activity?")
    topics = {item["topic"] for item in results}
    assert "heat_safety" in topics or "heat_illness" in topics
