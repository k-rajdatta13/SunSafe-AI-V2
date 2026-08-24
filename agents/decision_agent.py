"""Deterministic outdoor-window selection under hard safety constraints."""
from __future__ import annotations
from datetime import datetime
from state import SunState
from agents.common import mark_complete


def decision_agent_node(state: SunState) -> SunState:
    forecast = state.get("hourly_forecast", [])
    if state.get("hard_stop"):
        state["best_time"] = "No recommended direct-sun window under current safety conditions"
        state["decision_basis"] = ["Hard safety constraint active"]
        return mark_complete(state, "decision_agent", "hard_stop_applied")

    candidates = []
    for hour in forecast:
        uv = float(hour["uv_index"])
        temp = float(hour["temperature"])
        if uv >= 8 or temp > 35:
            continue
        score = 100 - min(uv, 8) * 8 - max(temp - 28, 0) * 3 - float(hour.get("cloud_cover", 0)) * 0.05
        candidates.append((score, hour))

    if not candidates:
        state["best_time"] = "No conservative outdoor window found"
        state["decision_basis"] = ["No forecast hour satisfied conservative constraints"]
    else:
        score, best_hour = max(candidates, key=lambda item: item[0])
        dt = datetime.fromisoformat(best_hour["time"])
        state["best_time"] = dt.strftime("%I:%M %p").lstrip("0")
        state["decision_score"] = round(float(score), 2)
        state["decision_basis"] = [
            "Selected from forecast hours satisfying hard safety constraints",
            "Lower UV and lower heat conditions receive higher planning scores",
            "This score is a planning heuristic, not a probability or medical confidence score",
        ]
    return mark_complete(state, "decision_agent")
