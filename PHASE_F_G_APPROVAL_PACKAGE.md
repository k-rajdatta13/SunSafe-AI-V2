# SunSafe AI V2 â€” Phase F/G Approval Package

**Project:** SunSafe AI V2
**Repository:** https://github.com/k-rajdatta13/SunSafe-AI-V2
**Production API:** https://sunsafe-ai-v2.onrender.com
**Final verified commit:** `828202892f89b6d8a0d176393ebecc8da6a33345`
**Branch:** `main`
**Verification date:** 25 August 2026

---

## 1. Purpose

SunSafe AI V2 is an evidence-grounded, safety-constrained outdoor UV/heat decision-support system.

The system combines:

- deterministic safety policy,
- live weather information,
- authoritative health evidence,
- bounded agent orchestration,
- claim-level evidence checks,
- verification before explanation,
- and a production FastAPI service.

It is intentionally bounded. It is **not** an autonomous medical diagnostic system and does not prescribe medically valid UV exposure durations or diagnose illness.

---

## 2. System Architecture

```text
User
  |
  v
FastAPI
  |
  v
LangGraph Orchestrator
  |
  +--> Weather Agent ------> Live weather / forecast
  |
  +--> Safety Agent -------> Deterministic safety policy
  |
  +--> Knowledge Agent ----> WHO/CDC evidence retrieval
  |
  +--> Decision Agent -----> Outdoor-window planning
  |
  +--> Verifier Agent ----> Consistency / safety verification
  |
  +--> Explainer Agent ---> Final user-facing explanation
```

The orchestrator selects workflow steps. The deterministic safety policy remains authoritative over the safety action.

---

## 3. Final Repository State

The final repository was verified clean.

```text
git status --short
```

returned no output.

The local and remote commit hashes are identical:

```text
HEAD       = 828202892f89b6d8a0d176393ebecc8da6a33345
origin/main = 828202892f89b6d8a0d176393ebecc8da6a33345
```

The final commit is:

```text
8282028 Update README for final approval package
```

The final commit changed only `README.md`.

---

## 4. Automated Test Evidence

Full test suite:

```text
46 passed
1 warning
```

Command:

```powershell
.\.venv\Scripts\python.exe -m pytest -q
```

Result:

```text
46 passed, 1 warning
```

The warning is a Starlette/httpx deprecation warning from the installed test dependency stack. It did not cause any test failure.

---

## 5. Deterministic Policy Regression

The Phase 5 offline evaluation contains:

```text
200 scenarios
200 passed
Consistency: 1.0
```

This represents regression consistency against the current production safety function.

It should **not** be described as clinical accuracy.

---

## 6. Failure-Case Evaluation

The offline failure-case suite contains:

```text
12 total
12 passed
Pass rate: 1.0
```

Covered cases include:

- invalid/negative UV,
- extreme UV,
- extreme heat,
- combined extreme UV and heat,
- UV boundary conditions,
- heat boundary conditions,
- invalid city validation,
- retry behavior,
- missing evidence,
- verification failure behavior.

---

## 7. Claim-Level Groundedness

Phase 5.5 groundedness evaluation:

```text
8 cases
8 passed
All cases passed: true
```

Result artifact:

```text
evaluation/results/phase5_5_groundedness_results.json
```

Mode:

```text
DETERMINISTIC_CLAIM_LEVEL_GROUNDEDNESS
```

The evaluator checks:

- citation linkage,
- authoritative-source status,
- numeric support,
- conservative lexical entailment,
- supported versus unsupported claims,
- missing/wrong citations,
- multi-evidence cases,
- negation mismatches.

Important qualification:

```text
semantic_llm_judge_used: false
```

Therefore this result should be reported as:

> **8/8 deterministic claim-level groundedness cases passed**

It should **not** be presented as semantic, clinical, or LLM-judge groundedness.

---

## 8. Live Integration Evaluation

Phase 5.3 live graph integration:

```text
5/5 cases passed
```

Cases covered:

1. normal full graph,
2. weather timeout/retry,
3. weather 429/retry,
4. missing-evidence degraded mode,
5. verifier-failure revision loop.

The successful normal full graph trace included:

```text
orchestrator
weather_agent
safety_agent
knowledge_agent
decision_agent
verifier_agent
explainer_agent
```

The verifier-failure case demonstrated a bounded revision loop rather than silently accepting the failed state.

---

## 9. Security Checks

Bandit was executed against:

```text
api
agents
rag
tools
utils
models
graph.py
app.py
```

Command:

```powershell
.\.venv\Scripts\python.exe -m bandit -q -r api agents rag tools utils models graph.py app.py -f txt
```

Result:

- no failed Bandit findings.

There was one informational warning regarding an existing `nosec` annotation (`B104`) in `api/run.py`; it was not reported as a failed test.

---

## 10. Repository Secret-Pattern Check

A repository scan for common secret/private-key patterns returned no matches.

Patterns checked included:

- Google API-key style strings,
- OpenAI-style `sk-` keys,
- RSA/EC/OpenSSH private-key headers.

Result:

```text
0 matches
```

This should be described as a **secret-pattern scan**, not as a guarantee that no secret can ever exist.

---

## 11. Prohibited Tracked-Artifact Check

The Git-tracked file list was checked for:

- `.env`,
- `.venv`,
- `__pycache__`,
- `.pytest_cache`,
- `.pem`,
- `.key`.

Result:

```text
0 matches
```

The repository contains:

```text
132 Git-tracked files
```

The larger recursive filesystem count is not used because it includes the local virtual environment and generated runtime files.

---

## 12. GitHub CI/CD

The final commit:

```text
8282028
```

was successfully validated by GitHub Actions.

CI status:

```text
SUCCESS
```

The workflow covers the repository's automated validation/build checks.

The preceding engineering commits also showed successful CI runs.

---

## 13. Docker / Cloud Deployment

The production service is deployed as a Docker service on Render.

Verified deployment:

```text
Service: SunSafe-AI-V2
Branch: main
Commit: 8282028
Status: Live
```

Production URL:

```text
https://sunsafe-ai-v2.onrender.com
```

---

## 14. Production Health Check

Endpoint:

```text
GET /health
```

Returned:

```text
HTTP 200
{
  "status": "ok",
  "service": "sunsafe-ai",
  "version": "2.0-final-audit"
}
```

Therefore the deployed API is live and responding successfully.

---

## 15. Production Readiness Check

Endpoint:

```text
GET /ready
```

Returned:

```text
HTTP 200
{
  "status": "ready",
  "rag_index": true
}
```

This confirms that the deployed service has its required bundled RAG index available.

---

## 16. Production Recommendation Test

A live request was successfully sent to:

```text
POST /v1/recommend
```

The production response returned:

```text
HTTP 200
status: success
verification_status: PASS
```

The response contained:

- weather information,
- deterministic safety output,
- outdoor-window decision,
- evidence records,
- verification status,
- agent trace,
- final explanation.

The live evidence contained four WHO records, including WHO UV-index and skin-cancer protection material.

The production trace included:

```text
orchestrator
weather_agent
safety_agent
knowledge_agent
decision_agent
verifier_agent
explainer_agent
```

---

## 17. Unsupported-Domain Safety Behavior

An intentionally unsupported request was tested:

> "Will the stock market rise tomorrow because of the weather?"

The system returned:

```text
HTTP 200
intent: unsupported
plan: ["explainer_agent"]
verification_status: NOT_REQUIRED
```

The system did not call the weather/safety decision workflow and returned a deterministic bounded response explaining that SunSafe AI does not analyze stock-market movements or unrelated domains.

This behavior is covered by automated regression tests.

---

## 18. Input Validation

An empty-city request was tested against the production API.

Result:

```text
HTTP 422
```

This confirms request validation rejects an invalid required city field before running the recommendation workflow.

---

## 19. Invalid-City Handling

A deliberately invalid city:

```text
DefinitelyNotARealCityXYZ987
```

was tested.

Result:

```text
HTTP 404
```

The server logs showed the geocoding lookup completed with no valid city result and the API returned a controlled 404 response.

---

## 20. Weather Retry Behavior

The live integration harness verified retry behavior for weather-service failures.

Both timeout and HTTP 429 scenarios passed.

The harness demonstrated multiple current-weather attempts followed by successful completion.

This confirms the retry path is exercised in integration testing rather than only being described in documentation.

---

## 21. Evidence-Degraded Mode

The live integration harness tested the absence of retrieved evidence.

Result:

```text
status: degraded
evidence_count: 0
evidence_status: UNAVAILABLE
authority notice: present
```

The system therefore does not pretend that authoritative evidence exists when retrieval is unavailable.

---

## 22. Verification Failure / Revision Loop

The live integration harness deliberately triggered a verifier failure.

Result:

```text
verifier executions: 2
verification_status: FAIL
best_time: No conservative outdoor window found
```

The trace demonstrated:

```text
... decision_agent
verifier_agent
decision_agent
verifier_agent
explainer_agent
```

This shows bounded revision behavior rather than unrestricted looping.

---

## 23. Evidence and RAG

The knowledge layer uses an official-source registry and retrieves evidence from the configured WHO/CDC corpus.

Evidence metadata includes:

- source,
- URL,
- topic,
- claim,
- chunk identifier,
- retrieval score.

The explanation layer receives the evidence metadata and is explicitly instructed not to invent sources or URLs.

The deterministic policy remains authoritative over the safety decision.

---

## 24. Performance Observations

Live production measurements varied depending on cache state and external-service behavior.

Observed examples included:

- cached production request: approximately 8 seconds,
- uncached request with Gemini generation: approximately 40 seconds,
- unsupported-domain request: approximately 17 seconds,
- live integration harness cases: approximately tens of milliseconds to approximately 1.2 seconds under mocked/local harness conditions.

These numbers should be treated as **observed measurements for the tested environment**, not as a universal latency guarantee.

External weather and LLM service latency can materially affect end-to-end response time.

---

## 25. API Boundary

The production API provides:

```text
GET  /health
GET  /ready
POST /v1/recommend
```

FastAPI provides request/response validation and the service boundary.

The agent system remains separated from the UI so the same workflow can support:

- web UI,
- API clients,
- future application integrations.

---

## 26. Safety Boundary

SunSafe AI is a bounded decision-support system.

It does not:

- diagnose illness,
- prescribe treatment,
- prescribe medically valid UV exposure durations,
- invent authoritative evidence,
- override deterministic safety policy,
- treat unsupported-domain requests as SunSafe decisions.

The explanation agent is deliberately constrained to explain verified state rather than choose the safety action.

---

## 27. Limitations

The following limitations should be disclosed during approval:

1. Claim-level groundedness is deterministic and conservative; it is not an LLM semantic judge.
2. The Phase 5 offline agent score is a fixture/contract score and is not presented as a live-agent accuracy score.
3. The 200-scenario policy result is regression consistency, not clinical accuracy.
4. External weather and LLM services affect production latency and availability.
5. The system is decision support, not medical diagnosis or treatment.
6. The decision-window score is a transparent planning heuristic, not a probability or medical confidence score.
7. The repository can operate with a lightweight bundled retrieval setup; production deployments may use the optional dense/Qdrant configuration.

---

## 28. Final Approval Evidence Summary

| Area | Verified evidence |
|---|---|
| Automated tests | **46/46 passed** |
| Deterministic policy regression | **200/200, consistency 1.0** |
| Failure-case suite | **12/12, pass rate 1.0** |
| Claim-level groundedness | **8/8 passed** |
| Live integration harness | **5/5 passed** |
| Bandit | **No failed findings** |
| Secret-pattern scan | **0 matches** |
| Prohibited tracked artifacts | **0 matches** |
| Git-tracked release files | **132** |
| GitHub CI | **PASS** |
| Docker deployment | **LIVE** |
| `/health` | **HTTP 200** |
| `/ready` | **HTTP 200, RAG index true** |
| `/v1/recommend` | **HTTP 200, verification PASS** |
| Git working tree | **Clean** |
| Local/remote commit | **Exact SHA match** |

---

## 29. Final Repository Identity

```text
Repository:
https://github.com/k-rajdatta13/SunSafe-AI-V2

Production:
https://sunsafe-ai-v2.onrender.com

Final commit:
828202892f89b6d8a0d176393ebecc8da6a33345

Branch:
main

Tracked files:
132

Working tree:
clean

HEAD == origin/main:
yes
```

---

## 30. Suggested Guide Approval Statement

SunSafe AI V2 has completed its current engineering and evaluation cycle with reproducible automated tests, deterministic policy regression, claim-level groundedness checks, live integration testing, security checks, CI validation, Docker/cloud deployment, production health/readiness verification, and a successful live recommendation request.

The system is ready for guide review and approval, subject to the documented limitations and bounded safety scope above.
