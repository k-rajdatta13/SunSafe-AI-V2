import json
from pathlib import Path

from evaluation.safety_eval import evaluate as safety_evaluate
from evaluation.agent_eval import evaluate_trace
from evaluation.groundedness import evaluate_evidence

ROOT = Path(__file__).resolve().parents[1]


def test_scenario_dataset_has_200_cases():
    rows = json.loads((ROOT / "evaluation" / "scenario_dataset_200.json").read_text())
    assert len(rows) == 200
    assert len({r["scenario_id"] for r in rows}) == 200


def test_deterministic_safety_regression_is_perfect():
    result = safety_evaluate()
    assert result["accuracy"] == 1.0


def test_agent_contract_order_and_guardrails():
    trace = [{"agent": a} for a in ["orchestrator","weather_agent","safety_agent","knowledge_agent","decision_agent","verifier_agent"]]
    state = {
        "verification_status": "PASS",
        "hard_stop": True,
        "best_time": "No conservative outdoor window found",
        "evidence": [{"source":"WHO","url":"https://www.who.int/","chunk_id":"x","claim":"y"}],
    }
    result = evaluate_trace(trace, state)
    assert result["required_agents_present"]
    assert result["required_agent_order"]
    assert result["verifier_pass"]
    assert result["safety_invariant"]
    assert result["citation_contract"]


def test_groundedness_requires_complete_citation_metadata():
    result = evaluate_evidence([
        {"source":"WHO","url":"https://www.who.int/","chunk_id":"x","claim":"UV guidance"},
        {"source":"WHO","url":"","chunk_id":"y","claim":"missing URL"},
    ])
    assert result["citation_completeness"] == 0.5
    assert result["authoritative_source_rate"] == 1.0
