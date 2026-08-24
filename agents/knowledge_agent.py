"""Evidence-grounded RAG Knowledge Agent for SunSafe AI."""
from state import SunState
from agents.common import mark_complete
from rag.retriever import LocalVectorRetriever

retriever = LocalVectorRetriever(top_k=4)

def knowledge_agent_node(state: SunState) -> SunState:
    results = retriever.retrieve_for_state(state)
    evidence = [
        {
            "source": item["source"],
            "url": item["url"],
            "topic": item["topic"],
            "claim": item["text"],
            "score": item["score"],
            "chunk_id": item["id"],
        }
        for item in results
    ]
    state["evidence"] = evidence
    state["evidence_summary"] = [item["claim"] for item in evidence]
    state["retrieval_backend"] = retriever.backend
    state["retrieval_query"] = " ".join([
        state.get("user_query", ""),
        f"UV index {state.get('uv_index', '')}",
        state.get("uv_level", ""),
        state.get("heat_caution", ""),
    ]).strip()
    state["retrieval_count"] = len(evidence)

    # Evidence availability is an explicit safety/grounding state, not inferred
    # later from list length. A missing corpus result must be visible to the
    # downstream decision/explanation layers.
    state["evidence_status"] = "AVAILABLE" if evidence else "UNAVAILABLE"
    event = "rag_retrieval_complete" if evidence else "rag_evidence_unavailable"
    return mark_complete(state, "knowledge_agent", event)
