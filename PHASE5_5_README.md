# SunSafe AI V2 — Phase 5.5 Claim-Level Groundedness (Corrected)

This phase adds a deterministic claim-level groundedness evaluator. It is intentionally conservative and does not use an LLM judge.

## What it checks

For every explicit atomic knowledge claim:
- citation exists;
- cited chunk exists;
- at least one cited evidence chunk is authoritative (WHO/CDC by default);
- numeric facts are present in the cited evidence;
- substantive claim tokens have sufficient overlap with the cited authoritative evidence;
- support may be accumulated across multiple cited evidence chunks;
- explicit negation polarity conflicts are rejected.

Unsupported or ambiguous claims are not awarded partial credit. They are marked `UNSUPPORTED` or `UNVERIFIABLE`.

## Important scope boundary

The current SunSafe response contract exposes retrieved evidence, but it does not expose a separate machine-readable list of the LLM's atomic knowledge claims. Therefore this patch deliberately does **not** pretend to measure the live Gemini explanation's semantic groundedness. The fixtures establish the evaluator contract first. A later adapter can consume an explicit `knowledge_claims` field or structured explanation trace.

Do not report the fixture score as a live production groundedness score.

## Run

```powershell
.\.venv\Scripts\python.exe -m pytest tests/test_groundedness.py -q
.\.venv\Scripts\python.exe evaluation\run_groundedness.py
```

Expected corrected result:

```text
3 passed
```

and:

```json
"cases": 8,
"passed_cases": 8,
"all_cases_passed": true,
"semantic_llm_judge_used": false
```

The corrected evaluator fixes two contract bugs in the first patch:
1. support can be accumulated across multiple cited evidence chunks;
2. explicit `not X` versus positive `X` polarity conflicts are rejected.

It does not change any production SunSafe safety policy or runtime agent.
