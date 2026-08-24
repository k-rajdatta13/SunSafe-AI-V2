"""Phase-5.4 safety evaluation using an independent policy oracle."""
from __future__ import annotations
import json
from pathlib import Path

from utils.safety_policy import build_safety_assessment
from evaluation.independent_safety_oracle import expected

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "evaluation" / "scenario_dataset_200.json"
FIELDS = ["uv_level", "protection_required", "heat_caution", "hard_stop", "overall_action"]


def _actual(uv: float, temp: float):
    a = build_safety_assessment(uv_index=uv, temperature_c=temp, age=25)
    return {f: getattr(a, f) for f in FIELDS}


def _oracle(uv: float, temp: float):
    a = expected(uv, temp)
    return {f: getattr(a, f) for f in FIELDS}


def evaluate() -> dict:
    rows = json.loads(DATA.read_text(encoding="utf-8"))
    passed = 0
    mismatches = []
    for row in rows:
        w = row["mock_weather"]
        exp = _oracle(w["uv_index"], w["temperature"])
        act = _actual(w["uv_index"], w["temperature"])
        bad = {f: (exp[f], act[f]) for f in FIELDS if exp[f] != act[f]}
        if bad:
            mismatches.append({"scenario_id": row["scenario_id"], "mismatches": bad})
        else:
            passed += 1
    return {
        "scenarios": len(rows),
        "passed": passed,
        "accuracy": passed / len(rows) if rows else 0.0,
        "mismatches": mismatches,
        "ground_truth": "independent_safety_oracle",
    }


def evaluate_boundaries() -> dict:
    # Boundary probes: immediately below, exactly at, and immediately above
    # each documented threshold.
    cases = [
        ("uv_1_9", 1.9, 25), ("uv_2", 2.0, 25), ("uv_2_1", 2.1, 25),
        ("uv_3", 3.0, 25), ("uv_3_1", 3.1, 25),
        ("uv_5", 5.0, 25), ("uv_5_1", 5.1, 25),
        ("uv_7", 7.0, 25), ("uv_7_1", 7.1, 25),
        ("uv_8", 8.0, 25), ("uv_8_1", 8.1, 25),
        ("heat_29_9", 0, 29.9), ("heat_30", 0, 30.0),
        ("heat_30_1", 0, 30.1), ("heat_35", 0, 35.0),
        ("heat_35_1", 0, 35.1),
    ]
    results = []
    for case_id, uv, temp in cases:
        try:
            exp = _oracle(uv, temp)
            act = _actual(uv, temp)
            ok = exp == act
            results.append({"id": case_id, "passed": ok})
        except Exception as exc:
            results.append({"id": case_id, "passed": False, "error": str(exc)})
    return {
        "total": len(results),
        "passed": sum(r["passed"] for r in results),
        "all_passed": all(r["passed"] for r in results),
        "results": results,
    }
