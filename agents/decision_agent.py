"""Deterministic outdoor-window selection under hard safety constraints."""
from __future__ import annotations

from datetime import datetime

from state import SunState
from agents.common import mark_complete


def _requested_hour_window(user_query: str) -> tuple[int, int] | None:
    """Return a local-hour window for explicit temporal phrases.

    None means no explicit time constraint was requested, so the planner
    retains its existing full-forecast behavior.
    """
    query = user_query.lower()

    if "this morning" in query or "tomorrow morning" in query:
        return 6, 11

    if "this afternoon" in query or "tomorrow afternoon" in query:
        return 12, 17

    if "this evening" in query or "tomorrow evening" in query:
        return 18, 21

    if "tonight" in query:
        return 18, 23

    return None


def decision_agent_node(state: SunState) -> SunState:
    forecast = state.get("hourly_forecast", [])

    if state.get("hard_stop"):
        state["best_time"] = "No recommended direct-sun window under current safety conditions"
        state["decision_basis"] = ["Hard safety constraint active"]
        return mark_complete(state, "decision_agent", "hard_stop_applied")

    hour_window = _requested_hour_window(state.get("user_query", ""))

    candidates = []

    for hour in forecast:
        dt = datetime.fromisoformat(hour["time"])

        # Respect an explicitly requested time period.
        if hour_window is not None:
            start_hour, end_hour = hour_window
            if not start_hour <= dt.hour <= end_hour:
                continue

        uv = float(hour["uv_index"])
        temp = float(hour["temperature"])

        if uv >= 8 or temp > 35:
            continue

        score = (
            100
            - min(uv, 8) * 8
            - max(temp - 28, 0) * 3
            - float(hour.get("cloud_cover", 0)) * 0.05
        )

        candidates.append((score, hour))

    if not candidates:
        if hour_window is not None:
            start_hour, end_hour = hour_window
            state["best_time"] = "No conservative outdoor window found in requested time period"
            state["decision_basis"] = [
                f"No forecast hour in the requested {start_hour:02d}:00–{end_hour:02d}:59 window "
                "satisfied conservative safety constraints"
            ]
        else:
            state["best_time"] = "No conservative outdoor window found"
            state["decision_basis"] = [
                "No forecast hour satisfied conservative constraints"
            ]
    else:
        score, best_hour = max(candidates, key=lambda item: item[0])
        dt = datetime.fromisoformat(best_hour["time"])

        state["best_time"] = dt.strftime("%I:%M %p").lstrip("0")
        state["decision_score"] = round(float(score), 2)

        basis = [
            "Selected from forecast hours satisfying hard safety constraints",
            "Lower UV and lower heat conditions receive higher planning scores",
            "This score is a planning heuristic, not a probability or medical confidence score",
        ]

        if hour_window is not None:
            start_hour, end_hour = hour_window
            basis.insert(
                0,
                f"Restricted candidate hours to the requested "
                f"{start_hour:02d}:00–{end_hour:02d}:59 time period",
            )

        state["decision_basis"] = basis

    return mark_complete(state, "decision_agent")