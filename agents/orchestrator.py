"""Policy-constrained planner for the bounded SunSafe agent workflow.

The planner is intentionally deterministic: it decides which *workflow steps*
are needed, never the safety outcome. This makes routing reproducible and safe.
"""
from __future__ import annotations

from state import SunState


UNSUPPORTED_TERMS = (
    "stock market",
    "stock price",
    "stocks",
    "share price",
    "shares",
    "investment",
    "invest",
    "trading",
    "trade stocks",
    "crypto",
    "cryptocurrency",
    "bitcoin",
    "ethereum",
    "financial market",
    "market prediction",
    "election",
    "politics",
    "political",
    "sports score",
    "football score",
    "cricket score",
    "lottery",
)

DECISION_TERMS = (
    "today",
    "now",
    "current",
    "outside",
    "outdoor",
    "exercise",
    "activity",
    "go out",
    "go outside",
    "safe",
    "safely",
    "weather",
    "plan",
    "forecast",
)

KNOWLEDGE_TERMS = (
    "what is",
    "what does",
    "why",
    "how do i protect",
    "how can i protect",
    "sunscreen",
    "uv index",
    "sun protection",
    "heat safety",
    "symptoms",
    "vitamin d",
    "skin cancer",
)

FULL_PLAN = [
    "weather_agent",
    "safety_agent",
    "knowledge_agent",
    "decision_agent",
    "verifier_agent",
    "explainer_agent",
]

KNOWLEDGE_PLAN = [
    "knowledge_agent",
    "explainer_agent",
]

UNSUPPORTED_PLAN = [
    "explainer_agent",
]


def _classify_intent(query: str) -> tuple[str, str]:
    text = " ".join((query or "").lower().split())

    # Unsupported-domain detection must happen BEFORE decision/knowledge
    # detection. Otherwise words such as "weather" inside an unrelated
    # question could incorrectly trigger the live safety workflow.
    if any(term in text for term in UNSUPPORTED_TERMS):
        return (
            "unsupported",
            "The request is outside SunSafe AI's supported UV, heat, weather, and outdoor-safety domain.",
        )

    if any(term in text for term in DECISION_TERMS):
        return (
            "decision_support",
            "Live environmental conditions are required for this request.",
        )

    if any(term in text for term in KNOWLEDGE_TERMS):
        return (
            "knowledge",
            "The request can be answered from authoritative evidence without live weather.",
        )

    # Conservative default: when intent is ambiguous, require live conditions.
    return (
        "decision_support",
        "Ambiguous request defaults to the safer live-condition workflow.",
    )


def orchestrator_node(state: SunState) -> SunState:
    intent, reason = _classify_intent(state.get("user_query", ""))

    if intent == "unsupported":
        plan = UNSUPPORTED_PLAN
    elif intent == "decision_support":
        plan = FULL_PLAN
    else:
        plan = KNOWLEDGE_PLAN

    state["intent"] = intent
    state["route_reason"] = reason
    state["plan"] = list(plan)
    state["current_agent"] = "orchestrator"
    state["completed_agents"] = []
    state["trace"] = [{
        "agent": "orchestrator",
        "event": "plan_created",
        "intent": intent,
        "plan": plan,
    }]
    state["verification_attempts"] = 0

    return state


def next_agent(state: SunState) -> str:
    """Return the next planned step that has not completed."""
    completed = set(state.get("completed_agents", []))

    for agent in state.get("plan", []):
        if agent not in completed:
            return agent

    return "explainer_agent"