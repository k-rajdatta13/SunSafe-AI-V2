# SunSafe AI V2 — Phase 5 Evaluation v2 Patch

## What changed

This patch tightens the evaluation claims without changing the production safety
engine.

### 1. Deterministic policy regression
The existing 200 scenarios remain useful, but are reported as **policy regression
consistency**, not independent clinical accuracy. The current dataset's expected
fields were generated from the same `build_safety_assessment()` implementation.

### 2. Agent evaluation
The agent contract evaluator remains reusable, but the runner now labels its
offline fixture score as a **contract fixture**. It does not pretend that a
hand-crafted trace is a real LangGraph execution.

### 3. Failure cases
The failure runner now labels each case by what it really exercises. Timeout and
429 cases are explicitly reported as retry-utility tests until a real weather-agent
integration harness is added.

Verification failure now checks the bounded/degraded contract instead of merely
checking that the verifier agent name appears in a fabricated trace.

### 4. Groundedness
Authority detection accepts real WHO/CDC display names and authoritative domains.
The evaluator separates citation completeness from lightweight lexical support.
It explicitly reports that semantic entailment is not evaluated.

## Files

Drop these files into the existing project, replacing the corresponding Phase-5
evaluation files:

- `evaluation/agent_eval.py`
- `evaluation/groundedness.py`
- `evaluation/evaluate_phase5.py`

`evaluation/safety_eval.py` is intentionally not replaced in this patch because
an independent policy oracle requires the exact production safety-policy thresholds
and action labels. That should be implemented only after those policy definitions
are inspected and encoded independently.

## Next upgrade

The next Phase-5.2 patch should add:

1. Independent policy oracle.
2. FastAPI/TestClient integration harness.
3. Real LangGraph trace capture.
4. Mocked weather failure injection for timeout/429.
5. Real missing-evidence and verifier-failure integration tests.
6. 50–100 curated RAG+LLM cases for claim-level groundedness.
7. Latency/token/cost measurement for full-mode execution.

Do not claim those capabilities until their tests actually execute them.
