"""Safety-policy agent.

The agent can interpret environmental evidence, but the hard safety rules live
in utils.safety_policy and cannot be overridden by an LLM.
"""

from state import SunState
from agents.common import mark_complete
from utils.safety_policy import build_safety_assessment


def safety_agent_node(state: SunState) -> SunState:
    assessment = build_safety_assessment(
        uv_index=state["uv_index"],
        temperature_c=state["temperature"],
        age=state["age"],
    )
    state.update({
        "uv_level": assessment.uv_level,
        "protection_required": assessment.protection_required,
        "heat_caution": assessment.heat_caution,
        "overall_action": assessment.overall_action,
        "safety_reasons": list(assessment.reasons),
        "protective_actions": list(assessment.protective_actions),
        "hard_stop": assessment.hard_stop,
    })
    return mark_complete(state, "safety_agent")
