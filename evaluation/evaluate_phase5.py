"""Phase-5 evaluation runner v2."""
from __future__ import annotations

import json
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from evaluation.safety_eval import evaluate as evaluate_safety
from evaluation.agent_eval import evaluate_trace, evaluate_verification_failure
from evaluation.groundedness import evaluate_evidence, evaluate_explanation
from utils.safety_policy import build_safety_assessment


def failure_eval() -> dict:
    cases = json.loads(
        (ROOT / "evaluation" / "failure_cases.json").read_text(encoding="utf-8")
    )
    passed = 0
    results = []
    for case in cases:
        inp = case.get("input", {})
        expected = case.get("expected")
        ok = False
        test_type = "component_regression"
        detail = ""
        try:
            name = case["case"]
            if name == "negative_uv":
                test_type = "deterministic_policy"
                try:
                    build_safety_assessment(
                        uv_index=inp["uv_index"], temperature_c=inp["temperature"], age=25
                    )
                except ValueError:
                    ok = True
                    detail = "Negative UV rejected by safety policy."
            elif name in {"extreme_uv", "extreme_heat", "extreme_uv_and_heat"}:
                test_type = "deterministic_policy"
                assessment = build_safety_assessment(
                    uv_index=inp["uv_index"], temperature_c=inp["temperature"], age=25
                )
                ok = bool(assessment.hard_stop)
                detail = f"hard_stop={assessment.hard_stop}"
            elif name == "border_uv_2":
                test_type = "boundary_regression"
                assessment = build_safety_assessment(uv_index=2, temperature_c=25, age=25)
                ok = assessment.uv_level == "LOW" and not assessment.protection_required
            elif name == "border_uv_3":
                test_type = "boundary_regression"
                assessment = build_safety_assessment(uv_index=3, temperature_c=25, age=25)
                ok = bool(assessment.protection_required)
            elif name == "border_heat_35":
                test_type = "boundary_regression"
                assessment = build_safety_assessment(uv_index=2, temperature_c=35, age=25)
                ok = assessment.heat_caution == "CAUTION"
            elif name == "invalid_city":
                test_type = "schema_validation"
                from models.schemas import RecommendationRequest
                try:
                    RecommendationRequest(city="", skin_type=3, body_area=20, age=25)
                except Exception:
                    ok = True
                    detail = "Schema rejected empty city."
            elif name in {"api_timeout", "api_429"}:
                test_type = "retry_utility_only"
                from utils.retry import with_retry
                attempts = {"n": 0}
                def failing_call():
                    attempts["n"] += 1
                    if name == "api_timeout":
                        raise TimeoutError("timeout")
                    raise RuntimeError("429")
                try:
                    with_retry(failing_call, attempts=2, base_delay=0)
                except Exception:
                    ok = attempts["n"] == 2
                detail = "This tests retry utility semantics, not the full weather-agent recovery path."
            elif name == "missing_evidence":
                test_type = "evidence_contract"
                metrics = evaluate_evidence([])
                ok = (
                    metrics["citation_completeness"] == 0.0
                    and metrics["authoritative_source_rate"] == 0.0
                )
                detail = "No evidence correctly produces zero citation/authority completeness."
            elif name == "verification_fail":
                test_type = "verification_failure_contract"
                state = {
                    "verification_status": "FAIL",
                    "hard_stop": False,
                    "best_time": "No conservative outdoor window found",
                    "evidence": [],
                }
                outcome = evaluate_verification_failure(state)
                ok = outcome["bounded_revision_or_degraded"]
                detail = "Checks bounded/degraded verifier-failure behavior, not merely agent presence."
        except Exception as exc:
            ok = False
            detail = f"{type(exc).__name__}: {exc}"
        passed += int(ok)
        results.append({
            "id": case["id"],
            "case": case["case"],
            "test_type": test_type,
            "passed": ok,
            "expected": expected,
            "detail": detail,
        })
    return {
        "total": len(cases),
        "passed": passed,
        "pass_rate": passed / len(cases) if cases else 0.0,
        "results": results,
    }


def contract_fixture() -> dict:
    trace = [{"agent": agent} for agent in [
        "orchestrator", "weather_agent", "safety_agent",
        "knowledge_agent", "decision_agent", "verifier_agent",
    ]]
    state = {
        "verification_status": "PASS",
        "hard_stop": True,
        "best_time": "No recommended direct-sun window under current safety conditions",
        "evidence": [{
            "source": "WHO — The ultraviolet (UV) index Q&A",
            "url": "https://www.who.int/news-room/questions-and-answers/item/radiation-the-ultraviolet-(uv)-index",
            "chunk_id": "fixture",
            "claim": "UVI 8 or higher requires extra caution.",
        }],
    }
    return evaluate_trace(trace, state)


def main() -> None:
    started = time.perf_counter()
    safety = evaluate_safety()
    failures = failure_eval()
    fixture = contract_fixture()
    grounding_smoke = {
        "empty_evidence": evaluate_evidence([]),
        "empty_explanation": evaluate_explanation("", []),
    }
    elapsed_ms = (time.perf_counter() - started) * 1000
    result = {
        "phase": 5,
        "mode": "offline_evaluation_v2",
        "deterministic_policy_regression": {
            "scenarios": safety["scenarios"],
            "passed": safety["passed"],
            "consistency": safety["accuracy"],
            "interpretation": (
                "Regression consistency only; expected outcomes in the current "
                "dataset originate from the production safety function."
            ),
        },
        "failure_cases": failures,
        "agent_evaluation": {
            "status": "OFFLINE_CONTRACT_FIXTURE_ONLY",
            "fixture_score": fixture["score"],
            "fixture_details": fixture,
            "live_langgraph_evaluation": "NOT_RUN",
        },
        "groundedness": {
            "status": "DETERMINISTIC_CONTRACT_CHECKS_ONLY",
            "smoke": grounding_smoke,
            "semantic_entailment": "NOT_EVALUATED",
        },
        "harness_latency_ms": round(elapsed_ms, 2),
        "notes": [
            "Do not report fixture_score as a live agent score.",
            "Do not report policy regression consistency as clinical accuracy.",
            "Retry cases currently exercise the retry utility only; full weather-agent recovery requires integration tests with a mocked weather provider.",
            "Full groundedness requires executing retrieval + LLM generation + verifier and scoring claims against retrieved evidence.",
        ],
    }
    out = ROOT / "evaluation" / "results" / "phase5_offline_results_v2.json"
    out.write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(json.dumps({
        "policy_regression_consistency": safety["accuracy"],
        "failure_pass_rate": failures["pass_rate"],
        "agent_contract_fixture_score": fixture["score"],
        "live_agent_evaluation": "NOT_RUN",
        "semantic_groundedness": "NOT_EVALUATED",
        "harness_latency_ms": round(elapsed_ms, 2),
        "output": str(out),
    }, indent=2))


if __name__ == "__main__":
    main()
