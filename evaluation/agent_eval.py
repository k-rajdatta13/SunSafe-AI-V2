"""Phase-5 agent contract evaluation.

This module evaluates a REAL execution trace/state when the caller supplies them.
It does not manufacture a trace.  The offline runner may use a fixture explicitly
labelled as such, but fixture scores must not be reported as live agent scores.
"""
from __future__ import annotations
from typing import Any

REQUIRED_ORDER = [
    "orchestrator",
    "weather_agent",
    "safety_agent",
    "knowledge_agent",
    "decision_agent",
    "verifier_agent",
]

SAFE_HARD_STOP_WINDOWS = {
    "No recommended direct-sun window under current safety conditions",
    "No conservative outdoor window found",
}


def evaluate_trace(trace: list[dict[str, Any]], state: dict[str, Any]) -> dict[str, Any]:
    """Evaluate observable invariants on an actual graph trace/final state."""
    seen = [e.get("agent") for e in trace if e.get("agent")]
    presence = all(agent in seen for agent in REQUIRED_ORDER)

    positions = [seen.index(agent) for agent in REQUIRED_ORDER if agent in seen]
    ordered = len(positions) == len(REQUIRED_ORDER) and positions == sorted(positions)

    verification_status = state.get("verification_status")
    verifier_pass = verification_status == "PASS"

    hard_stop = bool(state.get("hard_stop"))
    best_time = state.get("best_time")
    safety_invariant = not (
        hard_stop and best_time not in SAFE_HARD_STOP_WINDOWS
    )

    evidence = state.get("evidence") or []
    citation_contract = all(
        item.get("source")
        and item.get("url")
        and item.get("chunk_id")
        for item in evidence
    )

    # A verification failure is intentionally NOT treated as a pass.
    # The caller must separately test the bounded revision/degraded response.
    verification_failure_bounded = True
    if verification_status == "FAIL":
        final_action = str(state.get("overall_action") or state.get("action") or "")
        verification_failure_bounded = (
            best_time in SAFE_HARD_STOP_WINDOWS
            or not final_action
            or bool(state.get("hard_stop"))
        )

    checks = {
        "required_agents_present": presence,
        "required_agent_order": ordered,
        "verifier_pass": verifier_pass,
        "safety_invariant": safety_invariant,
        "citation_contract": citation_contract,
        "verification_failure_bounded": verification_failure_bounded,
    }

    return {
        **checks,
        "score": sum(checks.values()) / len(checks),
        "required_order": REQUIRED_ORDER,
        "seen_agents": seen,
    }


def evaluate_verification_failure(state: dict[str, Any]) -> dict[str, Any]:
    """Explicitly test the degraded/revision contract for verifier failure."""
    status = state.get("verification_status")
    safe_window = state.get("best_time") in SAFE_HARD_STOP_WINDOWS
    action = str(state.get("overall_action") or state.get("action") or "").lower()

    bounded = (
        status == "FAIL"
        and (
            safe_window
            or bool(state.get("hard_stop"))
            or "degraded" in action
            or "revise" in action
            or "no conservative" in action
        )
    )

    return {
        "verification_status_is_fail": status == "FAIL",
        "bounded_revision_or_degraded": bounded,
    }
