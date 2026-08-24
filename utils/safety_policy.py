"""Evidence-aligned safety policy for SunSafe AI V2.

This module intentionally does NOT calculate a medically valid UV exposure dose.
It converts environmental observations into conservative public-health guidance.

Primary source basis:
- WHO UV guidance: sun-protection measures are recommended at UVI >= 3;
  UVI 0-2 is low, 3-7 requires protection, and 8+ calls for extra caution.
- WHO heat guidance: avoid strenuous activity during the hottest part of the day,
  stay cool/hydrated, and seek care for symptoms of heat illness.

This is a decision-support policy, not a medical diagnostic or treatment engine.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

UVLevel = Literal["LOW", "MODERATE", "HIGH", "VERY_HIGH"]
RiskLevel = Literal["LOW", "CAUTION", "HIGH"]


@dataclass(frozen=True)
class SafetyAssessment:
    uv_level: UVLevel
    protection_required: bool
    heat_caution: RiskLevel
    overall_action: str
    reasons: tuple[str, ...]
    protective_actions: tuple[str, ...]
    hard_stop: bool


def classify_uv(uv_index: float) -> UVLevel:
    """Classify UVI using WHO's public UV Index bands."""
    if uv_index < 0:
        raise ValueError("UV index cannot be negative.")
    if uv_index <= 2:
        return "LOW"
    if uv_index <= 5:
        return "MODERATE"
    if uv_index <= 7:
        return "HIGH"
    return "VERY_HIGH"


def protection_required(uv_index: float) -> bool:
    """WHO recommends sun protection when UVI reaches 3."""
    return uv_index >= 3


def classify_heat_caution(temperature_c: float) -> RiskLevel:
    """Conservative environmental screening, not a heatstroke diagnosis.

    Temperature alone cannot determine heatstroke risk. V2 therefore labels this
    as a heat-condition screening signal rather than a medical risk prediction.
    """
    if temperature_c < 30:
        return "LOW"
    if temperature_c <= 35:
        return "CAUTION"
    return "HIGH"


def build_safety_assessment(
    *,
    uv_index: float,
    temperature_c: float,
    age: int,
) -> SafetyAssessment:
    """Build a conservative action recommendation from environmental inputs."""
    uv_level = classify_uv(uv_index)
    protection = protection_required(uv_index)
    heat = classify_heat_caution(temperature_c)

    reasons: list[str] = []
    actions: list[str] = [
        "Seek shade and avoid prolonged direct sun when UV is elevated.",
        "Use protective clothing, a broad-brimmed hat and UV-protective eyewear outdoors.",
    ]

    if uv_level == "LOW":
        reasons.append("UV Index is 0–2, a low-UV range.")
    elif uv_level in {"MODERATE", "HIGH"}:
        reasons.append("UV Index is 3–7; WHO recommends sun-protection measures.")
        actions.append("Use broad-spectrum sunscreen on exposed skin that cannot be covered.")
    else:
        reasons.append("UV Index is 8 or higher; UV exposure can cause harm more quickly.")
        actions.append("Avoid deliberate direct-sun exposure around the strongest UV period when possible.")

    if heat == "LOW":
        reasons.append("Ambient temperature is below the project's heat-caution threshold.")
    elif heat == "CAUTION":
        reasons.append("Ambient temperature is elevated; heat precautions are warranted.")
        actions.append("Stay hydrated and avoid strenuous activity during the hottest part of the day.")
    else:
        reasons.append("Ambient temperature is high; heat illness is a concern.")
        actions.extend([
            "Prefer a cool/shaded environment and avoid strenuous outdoor activity.",
            "If dizziness, confusion, nausea or other concerning symptoms occur, stop activity and seek medical help.",
        ])

    # Age is retained as a caution context, not used as a medical risk multiplier.
    if age < 18 or age >= 65:
        reasons.append("Age is in a group that may require additional heat/UV caution.")

    hard_stop = heat == "HIGH" or uv_level == "VERY_HIGH"

    if heat == "HIGH":
        overall_action = "AVOID_PROLONGED_OUTDOOR_EXPOSURE"
    elif uv_level == "VERY_HIGH":
        overall_action = "MINIMIZE_DIRECT_SUN_EXPOSURE"
    elif protection:
        overall_action = "OUTDOOR_ACTIVITY_WITH_PROTECTION"
    else:
        overall_action = "OUTDOOR_ACTIVITY_WITH_STANDARD_PRECAUTIONS"

    return SafetyAssessment(
        uv_level=uv_level,
        protection_required=protection,
        heat_caution=heat,
        overall_action=overall_action,
        reasons=tuple(reasons),
        protective_actions=tuple(actions),
        hard_stop=hard_stop,
    )
