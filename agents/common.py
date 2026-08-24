"""Shared helpers for agent state transitions."""
from __future__ import annotations
from typing import Any
from state import SunState

def mark_complete(state: SunState, agent: str, event: str = "completed", **event_fields: Any) -> SunState:
    """Mark an agent complete and append exactly one trace event."""
    completed = list(state.get("completed_agents", []))
    if agent not in completed:
        completed.append(agent)
    state["completed_agents"] = completed
    state["current_agent"] = agent
    trace = list(state.get("trace", []))
    entry = {"agent": agent, "event": event}
    entry.update(event_fields)
    trace.append(entry)
    state["trace"] = trace
    return state
