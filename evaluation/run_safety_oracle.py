"""Run Phase 5.4 independent safety-oracle evaluation from any working directory."""
from __future__ import annotations
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from evaluation.safety_eval import evaluate, evaluate_boundaries


def main() -> None:
    dataset = evaluate()
    boundaries = evaluate_boundaries()
    result = {
        "phase": "5.4",
        "mode": "INDEPENDENT_SAFETY_ORACLE",
        "dataset_regression": dataset,
        "independent_boundary_suite": boundaries,
        "independent_oracle_used": True,
        "oracle_imports_production_policy": False,
        "passed": dataset["accuracy"] == 1.0 and boundaries["all_passed"],
        "interpretation": (
            "Expected outputs are computed by evaluation.independent_safety_oracle, "
            "which does not import utils.safety_policy."
        ),
    }
    out = ROOT / "evaluation" / "results" / "phase5_4_independent_oracle_results.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
