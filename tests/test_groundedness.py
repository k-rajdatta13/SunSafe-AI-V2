import json
from pathlib import Path
from evaluation.groundedness import Evidence, Claim, evaluate_claims


def _load():
    p = Path(__file__).resolve().parents[1] / "evaluation" / "groundedness_fixtures.json"
    return json.loads(p.read_text(encoding="utf-8"))["cases"]


def test_fixture_groundedness_contract():
    for case in _load():
        result = evaluate_claims(
            [Claim(x["claim_id"], x["text"], tuple(x["cited_chunk_ids"])) for x in case["claims"]],
            [Evidence(x["chunk_id"], x["claim"], x["source"], x["url"]) for x in case["evidence"]],
        )
        assert result["verdicts"][0]["status"] == case["expected"], case["id"]


def test_supported_claim_scores_one():
    case = _load()[0]
    result = evaluate_claims(
        [Claim(case["claims"][0]["claim_id"], case["claims"][0]["text"], tuple(case["claims"][0]["cited_chunk_ids"]))],
        [Evidence(x["chunk_id"], x["claim"], x["source"], x["url"]) for x in case["evidence"]],
    )
    assert result["groundedness_score"] == 1.0


def test_unsupported_claim_never_scores_as_grounded():
    case = next(c for c in _load() if c["id"] == "unsupported_claim")
    result = evaluate_claims(
        [Claim(case["claims"][0]["claim_id"], case["claims"][0]["text"], tuple(case["claims"][0]["cited_chunk_ids"]))],
        [Evidence(x["chunk_id"], x["claim"], x["source"], x["url"]) for x in case["evidence"]],
    )
    assert result["all_claims_supported"] is False
