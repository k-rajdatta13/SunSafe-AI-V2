"""Application service boundary between FastAPI and the LangGraph runtime."""
from __future__ import annotations

from models.schemas import RecommendationRequest


def generate_recommendation(request: RecommendationRequest) -> dict:
    # Lazy import keeps the HTTP contract/test layer importable even in a
    # minimal environment; production installs langgraph from requirements.txt.
    from graph import run_agent
    return run_agent(
        request.city,
        request.skin_type,
        request.body_area,
        request.age,
        user_query=request.user_query,
    )
