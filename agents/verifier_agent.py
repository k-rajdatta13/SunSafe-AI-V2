"""Safety/consistency verifier agent.

This is deliberately deterministic: verification is a guardrail, not another
LLM opinion that can override the policy engine.
"""

from state import SunState
from agents.common import mark_complete


def verifier_agent_node(state: SunState) -> SunState:
    issues = []
    uv = float(state.get("uv_index", 0))
    temp = float(state.get("temperature", 0))

    if uv >= 3 and not state.get("protection_required"):
        issues.append("Protection must be required at UVI >= 3.")
    if uv >= 8 and not state.get("hard_stop"):
        issues.append("UVI >= 8 must activate the hard safety constraint.")
    if temp > 35 and not state.get("hard_stop"):
        issues.append("High heat screening must activate the hard safety constraint.")

    if state.get("hard_stop") and state.get("best_time") not in {
        "No recommended direct-sun window under current safety conditions",
        "No conservative outdoor window found",
    }:
        issues.append("Hard-stop conditions cannot produce a recommended direct-sun window.")

    state["verification_issues"] = issues
    state["verification_status"] = "PASS" if not issues else "FAIL"
    state["verification_attempts"] = state.get("verification_attempts", 0) + 1
    return mark_complete(state, "verifier_agent", "verification_passed" if not issues else "verification_failed")
