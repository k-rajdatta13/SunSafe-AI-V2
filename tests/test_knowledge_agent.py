from agents.knowledge_agent import knowledge_agent_node


def test_knowledge_agent_retrieves_ranked_authoritative_sources():
    state = {
        "user_query": "Can I go outside when UV is high?",
        "uv_index": 6.0,
        "uv_level": "HIGH",
        "heat_caution": "LOW",
        "completed_agents": [],
        "trace": [],
    }
    result = knowledge_agent_node(state)
    assert len(result["evidence"]) >= 3
    assert any("WHO" in item["source"] for item in result["evidence"])
    assert all(item["url"].startswith("https://") for item in result["evidence"])
    assert all("score" in item for item in result["evidence"])
    assert result["retrieval_count"] == len(result["evidence"])
    assert "sqlite-vector-db" in result["retrieval_backend"]
    assert "knowledge_agent" in result["completed_agents"]
