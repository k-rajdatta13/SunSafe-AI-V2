"""Independent safety-policy oracle for Phase 5.4.

This module intentionally does not import utils.safety_policy.
It encodes the project's documented safety policy independently so the
production implementation can be checked against a separate specification.
"""
from __future__ import annotations
from dataclasses import dataclass
from typing import Literal

UVLevel = Literal["LOW", "MODERATE", "HIGH", "VERY_HIGH"]
HeatLevel = Literal["LOW", "CAUTION", "HIGH"]


@dataclass(frozen=True)
class OracleResult:
    uv_level: UVLevel
    protection_required: bool
    heat_caution: HeatLevel
    hard_stop: bool
    overall_action: str


def expected(uv_index: float, temperature_c: float) -> OracleResult:
    if uv_index < 0:
        raise ValueError("UV index cannot be negative.")

    # Project/WHO-aligned bands documented in utils/safety_policy.py:
    # 0-2 LOW, >2-5 MODERATE, >5-7 HIGH, >7 VERY_HIGH.
    if uv_index <= 2:
        uv = "LOW"
    elif uv_index <= 5:
        uv = "MODERATE"
    elif uv_index <= 7:
        uv = "HIGH"
    else:
        uv = "VERY_HIGH"

    protection = uv_index >= 3

    # Project heat screening: <30 LOW, 30-35 inclusive CAUTION, >35 HIGH.
    if temperature_c < 30:
        heat = "LOW"
    elif temperature_c <= 35:
        heat = "CAUTION"
    else:
        heat = "HIGH"

    hard_stop = heat == "HIGH" or uv == "VERY_HIGH"

    if heat == "HIGH":
        action = "AVOID_PROLONGED_OUTDOOR_EXPOSURE"
    elif uv == "VERY_HIGH":
        action = "MINIMIZE_DIRECT_SUN_EXPOSURE"
    elif protection:
        action = "OUTDOOR_ACTIVITY_WITH_PROTECTION"
    else:
        action = "OUTDOOR_ACTIVITY_WITH_STANDARD_PRECAUTIONS"

    return OracleResult(
        uv_level=uv,
        protection_required=protection,
        heat_caution=heat,
        hard_stop=hard_stop,
        overall_action=action,
    )
