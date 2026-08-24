def test_knowledge_agent_marks_empty_retrieval_unavailable(monkeypatch):
    import agents.knowledge_agent as module
    monkeypatch.setattr(module.retriever, "retrieve_for_state", lambda state: [])
    state = {
        "city": "Kanpur", "user_query": "test", "uv_index": 4,
        "uv_level": "MODERATE", "heat_caution": "LOW",
        "trace": [], "completed_agents": [],
    }
    result = module.knowledge_agent_node(state)
    assert result["evidence"] == []
    assert result["evidence_status"] == "UNAVAILABLE"
    assert result["retrieval_count"] == 0
