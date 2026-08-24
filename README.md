# SunSafe AI V2

**Evidence-grounded, safety-constrained outdoor UV and heat decision-support system.**

SunSafe AI combines live weather conditions, deterministic safety policy, authoritative WHO/CDC evidence, bounded LangGraph orchestration, verification, and a controlled explanation layer to provide transparent outdoor-safety guidance.

> **Safety boundary:** SunSafe AI is a decision-support system. It does not diagnose medical conditions, prescribe treatment, or claim medically valid individual UV-exposure durations. The deterministic safety policy has authority over the final action.

## 1. Problem

SunSafe AI is designed to answer questions about outdoor UV/heat safety, including planning outdoor activities and choosing more conservative outdoor windows. It combines current/forecast environmental conditions, deterministic safety rules, authoritative evidence, verification, and a bounded explanation layer.

The LLM does **not** choose the safety outcome. It explains a decision already produced and verified by the bounded workflow.

## 2. Architecture

```text
User
  |
  v
FastAPI API
  |
  v
LangGraph Workflow
  |
  +--> Orchestrator
          |
          +--> Weather Agent
          |
          +--> Safety Agent
          |
          +--> Knowledge Agent (WHO/CDC RAG)
          |
          +--> Decision Agent
          |
          +--> Verifier Agent
          |
          +--> Explainer Agent
                    |
                    v
                 Response
```

The system is deliberately bounded and policy-constrained:

- The orchestrator selects workflow steps.
- The deterministic safety policy determines the action.
- The verifier checks the resulting state.
- The explainer communicates the verified result.

## 3. Agent Responsibilities

| Agent | Responsibility |
|---|---|
| Orchestrator | Classifies requests and selects the bounded workflow |
| Weather Agent | Retrieves geocoding, current weather, and hourly forecast |
| Safety Agent | Applies deterministic environmental safety rules |
| Knowledge Agent | Retrieves authoritative WHO/CDC evidence |
| Decision Agent | Selects a conservative outdoor planning window |
| Verifier Agent | Checks consistency and safety invariants |
| Explainer Agent | Explains the verified result without overriding policy |

Unsupported requests outside the UV, heat, weather, and outdoor-safety domain are rejected deterministically.

## 4. Evidence and Grounding

The RAG pipeline performs official-source registration, ingestion, HTML cleaning, chunking, dense embedding, persistent storage, similarity retrieval, evidence metadata propagation, and citation-aware explanation.

Retrieved evidence includes:

```text
source
URL
topic
claim
score
chunk_id
```

The explanation layer is instructed not to invent sources or URLs.

If authoritative evidence is unavailable, the system enters degraded evidence mode and explicitly reports that evidence was unavailable.

## 5. Retrieval Stack

Primary embedding backend:

```text
sentence-transformers/all-MiniLM-L6-v2
```

A deterministic dense-projection fallback supports reproducible offline development.

The default vector store is SQLite. An optional Qdrant adapter is available for production-style vector-service deployment.

Retrieval evaluation includes Recall@5, MRR, and nDCG@5.

## 6. Safety Boundary

SunSafe AI intentionally does not:

- diagnose illness;
- prescribe medical treatment;
- prescribe individual vitamin-D exposure;
- manufacture unsupported exposure-duration claims;
- override deterministic safety policy;
- treat an LLM-generated answer as the safety decision;
- claim evidence grounding when authoritative evidence is unavailable.

It is bounded decision support, not an autonomous medical agent.

## 7. Deterministic Decision Layer

The decision layer considers environmental observations such as:

- UV index;
- temperature;
- cloud cover;
- forecast conditions;
- heat screening;
- requested activity/time period.

The planning score is a transparent heuristic, not a probability, clinical risk score, or medical confidence score.

## 8. Verification Layer

The verifier checks for inconsistencies such as unsafe recommendations under hard-stop conditions, invalid outdoor windows, missing decision information, and evidence/citation contract violations.

A failed verification can return control to the decision agent for a bounded revision:

```text
Decision Agent
      |
      v
Verifier Agent
      |
     FAIL
      |
      v
Decision Agent
      |
      v
Verifier Agent
      |
      v
Explainer Agent
```

## 9. Unsupported-Domain Safety

Unsupported-domain detection happens before normal decision routing. This prevents unrelated questions containing words such as `weather`, `market`, or `current` from accidentally entering the environmental workflow.

Example:

```text
Will the stock market rise tomorrow because of the weather?
```

is routed as:

```text
intent = unsupported
plan = ["explainer_agent"]
verification = NOT_REQUIRED
```

The system returns a scope message rather than generating an unrelated prediction.

## 10. API

FastAPI endpoints:

```http
GET /health
POST /v1/recommend
```

Example:

```json
{
  "city": "Kanpur",
  "skin_type": 3,
  "body_area": 25,
  "age": 25,
  "user_query": "I'm going hiking outdoors this afternoon. What precautions should I take?"
}
```

The response can include request ID, location, environmental conditions, UV assessment, safety result, suggested outdoor window, evidence, verification status, explanation, and workflow trace.

## 11. API Validation

Input validation is enforced at the API boundary.

Observed validation behavior includes:

```text
Empty city       -> HTTP 422
Unknown city     -> HTTP 404
```

Internal exception details are not exposed to API clients.

## 12. Request Tracing and Logging

Every API request receives a request ID. Structured JSON logging records events including:

```text
recommendation_started
agent_run_started
weather_api_request_timing
gemini_request_timing
agent_run_completed
request_completed
```

Latency is recorded for relevant operations.

## 13. Weather Integration

The weather layer supports city geocoding, current weather, and hourly forecast.

It includes:

- exponential-backoff retry;
- transient-failure handling;
- HTTP 429 handling;
- TTL caching;
- structured request timing.

The live integration harness verifies retry behavior.

## 14. Caching

Caching is used for:

- geocoding;
- current weather;
- hourly forecast.

Cache hits are also exposed through structured logs.

## 15. Evidence-Degraded Mode

If authoritative evidence retrieval is unavailable:

```text
evidence_status = UNAVAILABLE
```

The explanation explicitly states that authoritative evidence was unavailable. Unsupported public-health claims are not presented as authoritative.

## 16. Testing and Evaluation

Current local regression result:

```text
46 passed
1 warning
```

The warning is a Starlette/httpx deprecation warning from the installed test client and is not a test failure.

Groundedness benchmark:

```text
8 / 8 cases passed
```

Phase 5.3 live integration:

```text
5 / 5 harness cases passed
```

Live cases:

| Case | Result |
|---|---|
| Normal full graph | PASS |
| Weather timeout/retry | PASS |
| Weather HTTP 429 retry | PASS |
| Missing evidence degraded mode | PASS |
| Verifier failure revision loop | PASS |

## 17. Production Validation

The deployed API was tested with an unsupported request:

```text
Will the stock market rise tomorrow because of the weather?
```

Observed:

```text
HTTP 200
intent = unsupported
plan = ["explainer_agent"]
verification_status = NOT_REQUIRED
evidence = []
```

A normal Kanpur outdoor-safety request completed through the full workflow with verification status `PASS`.

Invalid-input validation was also tested:

```text
Empty city       -> HTTP 422
Unknown city     -> HTTP 404
```

## 18. Deployment

The application is containerized and suitable for managed container platforms such as Render, Railway, Fly.io, Google Cloud Run, Azure Container Apps, and AWS App Runner.

Environment variables are configured through deployment secrets rather than committed configuration.

## 19. Docker

Local Docker:

```bash
docker compose up --build
```

Health endpoint:

```text
http://localhost:8000/health
```

FastAPI documentation:

```text
http://localhost:8000/docs
```

The Docker image is also exercised by CI.

## 20. CI/CD and Security

GitHub Actions is configured under:

```text
.github/workflows/ci.yml
```

CI runs automated tests, Python compilation checks, and Docker build validation.

The repository policy excludes:

```text
.env
API keys
generated secrets
__pycache__
.pytest_cache
local logs
```

Bandit was executed against the application source with no failed findings. The run reported one informational `# nosec` warning in `api/run.py`; it did not fail the security check.

## 21. Repository and Release State

Recent release commits:

```text
5979da1 Update live integration audit measurements
4361779 Add regression coverage for afternoon UV planning
d68c14e Reject unsupported-domain requests deterministically
```

The local `main` branch is synchronized with `origin/main`, and the working tree was verified clean.

## 22. Guide Demo

The recommended guide demonstration is approximately 5–10 minutes.

1. **Problem — ~30 sec:** Explain the evidence-grounded outdoor-safety objective.
2. **Architecture — ~1 min:** Show FastAPI -> LangGraph -> Weather/Safety/RAG -> Decision -> Verifier -> Explainer.
3. **Normal request — ~2 min:** Use:
   ```text
   I'm going hiking outdoors this afternoon. What precautions should I take?
   ```
   Show weather, UV, safety guidance, evidence, and final explanation.
4. **Grounding — ~1–2 min:** Show WHO/CDC evidence and explain that evidence metadata is supplied to the explanation layer.
5. **Safety behavior — ~1 min:** Demonstrate an unsupported/problematic request and show that the system does not confidently fabricate an answer.
6. **Engineering evidence — ~1 min:** Show test, groundedness, integration, security, Docker/CI, production API, and health results.

Then stop; implementation details should only be expanded if requested.

## 23. Approval Evidence Summary

| Area | Evidence |
|---|---|
| Automated tests | 46 passed |
| Groundedness | 8/8 passed |
| Live integration | 5/5 passed |
| Unsupported-domain routing | Local + deployed API tested |
| API validation | 422 invalid input, 404 unknown city |
| Weather retry | Tested |
| HTTP 429 retry | Tested |
| Evidence degraded mode | Tested |
| Verifier revision loop | Tested |
| Security scan | Bandit, no failed findings |
| CI | GitHub Actions configured |
| Docker | Container build/run validated |
| Production endpoint | Live API tested |
| Health endpoint | `/health` |
| Request tracing | Request IDs + structured logs |
| Performance | Latency measured |
| Repository | Clean and synchronized with origin/main |

## 24. Limitations

- Weather and forecast information depend on external providers.
- External services can be delayed, unavailable, or rate-limited.
- Authoritative evidence can temporarily become unavailable.
- The deterministic planning score is a heuristic, not a clinical probability or confidence score.
- The system is not a diagnostic or treatment system.
- Geographic recommendations depend on weather-provider location resolution.
- The explanation model is constrained to the verified state, while deterministic policy and verification remain authoritative.

## 25. Local Setup

Create a Python environment:

```bash
python -m venv .venv
```

Windows:

```powershell
.\.venv\Scripts\Activate.ps1
```

Install dependencies:

```bash
pip install -r requirements.txt
```

Optional dense retrieval dependencies:

```bash
pip install -r requirements-dense-retrieval.txt
```

Configure environment variables using `.env.example`. Never commit `.env`.

## 26. Build the Knowledge Index

```bash
python -m rag.build_index
```

Refresh official WHO/CDC sources:

```bash
python -m rag.build_index --refresh
```

Evaluate retrieval:

```bash
python evaluation/evaluate_retrieval.py
```

## 27. Run the Application

Streamlit:

```bash
streamlit run app.py
```

FastAPI:

```bash
python -m api.run
```

Open `/docs` for interactive API documentation.

## 28. Run Tests and Evaluation

Full regression:

```bash
python -m pytest -q
```

Offline Phase 5:

```bash
python evaluation/evaluate_phase5.py
```

Live sample benchmark:

```bash
python evaluation/live_eval.py
```

Live integration harness:

```bash
python evaluation/live_integration.py
```

Security scan:

```bash
python -m bandit -q -r api agents rag tools utils models graph.py app.py -f txt
```

## 29. Current Project Status

SunSafe AI V2 now has:

- deterministic safety policy;
- bounded LangGraph orchestration;
- authoritative-source RAG;
- evidence metadata and citation contracts;
- environmental weather integration;
- retry and caching behavior;
- verifier-based safety checks;
- unsupported-domain rejection;
- degraded evidence handling;
- FastAPI production boundary;
- structured logging;
- automated regression tests;
- groundedness evaluation;
- live integration evaluation;
- Docker support;
- CI/CD configuration;
- cloud deployment.

The current project focus is **demonstration and guide approval**, rather than uncontrolled expansion of the agent system.

## 30. Project Boundary

SunSafe AI is an academic/project implementation of bounded outdoor UV and heat decision support.

It should be evaluated according to its documented safety boundary, deterministic policy, evidence grounding, verification behavior, and engineering test results. It should not be represented as an autonomous medical system.
