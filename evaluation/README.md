# Phase 5 — Evaluation

Phase 5 adds a reproducible evaluation layer around the deterministic safety policy, agent graph contract, RAG grounding, latency, cost estimation, and failure handling.

## What is evaluated

### 1. Scenario regression dataset
`scenario_dataset_200.json` contains 200 reproducibly generated environmental/user scenarios covering UV 0–12, temperatures 18–43°C, ages, skin types, locations and common outdoor-safety intents.

**Important:** these are synthetic policy-regression scenarios, not clinical ground truth. Expected labels are generated from the explicit deterministic safety policy so that policy changes create measurable regressions.

### 2. Deterministic safety
`python evaluation/safety_eval.py` checks every scenario against the safety policy.

Metrics:
- exact scenario accuracy
- mismatch list

### 3. Agent evaluation
`agent_eval.py` validates the observable graph contract:
- required agents present
- required execution order
- verifier approval
- hard-stop invariant
- citation metadata contract

### 4. Groundedness
`groundedness.py` checks that retrieved evidence contains:
- source
- URL
- chunk ID
- claim text
- WHO/CDC source attribution

It also supports checking whether known source URLs appear in generated explanations.

### 5. Latency and cost
`live_eval.py` optionally runs a sample through the real graph and records:
- mean latency
- p95 latency
- success count
- estimated input/output tokens
- estimated USD cost

Set `LLM_INPUT_USD_PER_1M` and `LLM_OUTPUT_USD_PER_1M` to the pricing you want to benchmark. The project does not hard-code a claim about live provider pricing.

### 6. Failure cases
`failure_cases.json` covers invalid inputs, UV/heat hard stops, boundary conditions, retries, missing evidence and verification failure.

## Run offline evaluation

```bash
python evaluation/evaluate_phase5.py
```

The result is written to:

`evaluation/results/phase5_offline_results_v2.json`

## Run the live benchmark

Only after configuring the local environment:

```bash
python evaluation/live_eval.py
```

This benchmark uses a small sample by default. Do not run hundreds of live weather/LLM calls just for regression testing.
