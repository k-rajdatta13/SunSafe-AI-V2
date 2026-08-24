"""Run Phase 5.5 deterministic claim-level groundedness evaluation."""
from __future__ import annotations
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from evaluation.groundedness import Evidence, Claim, evaluate_claims


def main():
    fixtures = json.loads(
        (ROOT / "evaluation" / "groundedness_fixtures.json").read_text(encoding="utf-8")
    )["cases"]

    case_results = []
    for case in fixtures:
        result = evaluate_claims(
            [Claim(x["claim_id"], x["text"], tuple(x["cited_chunk_ids"])) for x in case["claims"]],
            [
                Evidence(
                    x["chunk_id"],
                    x["claim"],
                    x.get("source", ""),
                    x.get("url", ""),
                    x.get("score"),
                )
                for x in case["evidence"]
            ],
        )
        observed = result["verdicts"][0]["status"]
        case_results.append({
            "id": case["id"],
            "passed": observed == case["expected"],
            "expected": case["expected"],
            "observed": observed,
            "groundedness_score": result["groundedness_score"],
        })

    result = {
        "phase": "5.5",
        "mode": "DETERMINISTIC_CLAIM_LEVEL_GROUNDEDNESS",
        "cases": len(case_results),
        "passed_cases": sum(x["passed"] for x in case_results),
        "all_cases_passed": all(x["passed"] for x in case_results),
        "case_results": case_results,
        "semantic_llm_judge_used": False,
        "interpretation": (
            "This evaluator verifies citation linkage, authoritative source, "
            "numeric support and conservative lexical entailment for explicit "
            "atomic claims. It does not claim semantic or clinical truth."
        ),
    }
    out = ROOT / "evaluation" / "results" / "phase5_5_groundedness_results.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
