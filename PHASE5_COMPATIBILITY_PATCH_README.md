# Phase 5 compatibility patch

The full pytest run exposed a backwards-compatibility regression introduced by
the Phase 5.5 claim-level groundedness evaluator.

Older Phase 5 code imports:

    from evaluation.groundedness import evaluate_evidence

Phase 5.5 introduced `evaluate_claims` but removed the legacy public function.

This patch restores `evaluate_evidence` while retaining the new claim-level API.
It also registers the existing `integration` pytest marker.

No production safety policy is modified.

Run:

    .\.venv\Scripts\python.exe -m pytest -q

The Starlette/httpx deprecation warning is intentionally not addressed here;
that belongs in the dependency audit after the functional suite is green.
