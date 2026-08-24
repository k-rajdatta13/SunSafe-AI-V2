# Phase 5.2 — Live Integration Evaluation

This patch adds an integration harness that executes the real FastAPI endpoint and
the real LangGraph graph.

## What is real

- FastAPI routing and Pydantic validation
- `generate_recommendation()`
- LangGraph compilation and execution
- orchestrator routing
- weather agent
- deterministic safety agent
- local RAG knowledge agent
- deterministic decision agent
- verifier routing/revision loop
- explainer node
- response serialization
- actual execution trace

## What is mocked

Only nondeterministic/external providers:
- Open-Meteo HTTP
- Gemini explanation chain

This keeps CI/offline execution reproducible and prevents real API calls.

## Run

```powershell
.\.venv\Scripts\python.exe evaluation\live_integration.py
```

It writes:

`evaluation/results/phase5_live_integration_results.json`

## Important interpretation

The `missing_evidence_detection` case is deliberately different. The current
application can return HTTP 200 with zero evidence. The harness detects and reports
that behavior. That is a hardening gap, not a groundedness pass.

## What this does NOT yet prove

- production Open-Meteo reliability under real network conditions
- real Gemini generation quality
- semantic claim-level groundedness
- cloud infrastructure behavior
- independent clinical correctness

Those require separate evaluations.

## Recommended next hardening after this harness

1. Make missing evidence a bounded degraded response instead of allowing a normal
   grounded response with zero evidence.
2. Add a real `evidence_required` invariant to the verifier.
3. Add claim-to-chunk citation validation.
4. Add provider-independent policy oracle.
5. Add live benchmark only with controlled credentials.
