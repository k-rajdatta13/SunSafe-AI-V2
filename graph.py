"""LangGraph orchestration for the bounded, safety-constrained agent workflow."""
from __future__ import annotations
import time
import uuid
from langgraph.graph import StateGraph, START, END
from utils.logging_config import get_logger, log_event
from state import SunState
from agents.orchestrator import orchestrator_node, next_agent
from agents.weather_agent import weather_agent_node
from agents.safety_agent import safety_agent_node
from agents.knowledge_agent import knowledge_agent_node
from agents.decision_agent import decision_agent_node
from agents.verifier_agent import verifier_agent_node
from agents.explainer_agent import explainer_agent_node

builder = StateGraph(SunState)
for name, fn in {
    "orchestrator": orchestrator_node,
    "weather_agent": weather_agent_node,
    "safety_agent": safety_agent_node,
    "knowledge_agent": knowledge_agent_node,
    "decision_agent": decision_agent_node,
    "verifier_agent": verifier_agent_node,
    "explainer_agent": explainer_agent_node,
}.items():
    builder.add_node(name, fn)

builder.add_edge(START, "orchestrator")

ROUTE_MAP = {name: name for name in [
    "weather_agent", "safety_agent", "knowledge_agent", "decision_agent", "verifier_agent", "explainer_agent"
]}


def route_to_next(state: SunState) -> str:
    return next_agent(state)

builder.add_conditional_edges("orchestrator", route_to_next, ROUTE_MAP)
for node in ["weather_agent", "safety_agent", "knowledge_agent"]:
    builder.add_conditional_edges(node, route_to_next, ROUTE_MAP)

# Decision always feeds verification when it is part of the plan.
builder.add_edge("decision_agent", "verifier_agent")


def route_after_verifier(state: SunState) -> str:
    if state.get("verification_status") == "FAIL" and state.get("verification_attempts", 0) < 2:
        return "decision_agent"
    return "explainer_agent"

builder.add_conditional_edges("verifier_agent", route_after_verifier, {
    "decision_agent": "decision_agent",
    "explainer_agent": "explainer_agent",
})
builder.add_edge("explainer_agent", END)

graph = builder.compile()
logger = get_logger("sunsafe.graph")


def run_agent(city: str, skin_type: int, body_area: int, age: int, user_query: str = ""):
    request_id = str(uuid.uuid4())
    started = time.perf_counter()
    log_event(logger, 20, "agent_run_started", request_id=request_id, city=city)
    result = graph.invoke({
        "city": city,
        "skin_type": skin_type,
        "body_area": body_area,
        "age": age,
        "user_query": user_query or "Outdoor safety guidance",
        "request_id": request_id,
    })
    result["request_id"] = request_id
    log_event(logger, 20, "agent_run_completed", request_id=request_id,
              latency_ms=round((time.perf_counter() - started) * 1000, 2),
              verification=result.get("verification_status", "NOT_REQUIRED"),
              intent=result.get("intent"))
    return result
