# SunSafe AI V2 — Phase 3 Complete

Evidence-grounded, safety-constrained bounded-agent UV and outdoor decision-support system.

## Phase 3 RAG stack

1. **Official-source registry** — WHO/CDC URLs in `knowledge/sources.json`.
2. **Ingestion** — `rag/ingest.py` downloads official HTML, removes navigation/script noise, and records source metadata.
3. **Chunking** — sentence-boundary chunks with configurable size/overlap in `rag/chunking.py`.
4. **Embeddings** — primary `sentence-transformers/all-MiniLM-L6-v2` dense embeddings; deterministic dense projection fallback for offline development.
5. **Persistent vector DB** — SQLite stores dense vectors and metadata on disk by default. An optional Qdrant adapter is included for a production vector-service deployment (`qdrant-client`). The Knowledge Agent contract is unchanged.
6. **Retrieval** — cosine similarity over normalized dense vectors, returning source, URL, topic, chunk ID and score.
7. **Citations** — evidence metadata flows into the explanation agent and UI.
8. **Evaluation** — Recall@5, MRR and nDCG@5 over the retrieval benchmark in `evaluation/retrieval_eval.json`.

## Commands

### Build from the bundled bootstrap corpus

```bash
python -m rag.build_index
```

### Refresh from WHO/CDC official pages and rebuild

```bash
python -m rag.build_index --refresh
```

### Evaluate retrieval

```bash
python evaluation/evaluate_retrieval.py
```

### Run the app

```bash
streamlit run app.py
```

## Dense retrieval dependency

For the intended production-quality embedding backend:

```bash
pip install -r requirements-dense-retrieval.txt
```

The project remains runnable with the bundled fallback if the model package is unavailable. For a production-style deployment, install the optional dense/Qdrant requirements and set the vector-store backend in the deployment configuration.

## Safety boundary

This system does not prescribe medically valid UV exposure durations or diagnose illness. WHO/CDC evidence is used to support protective guidance; the deterministic safety policy remains authoritative.

## Phase 4 — Production Engineering

Phase 4 adds a production-facing service boundary without changing the deterministic safety policy or RAG evidence layer.

### Production capabilities
- **Pydantic v2 contracts** for request/response validation.
- **FastAPI** REST API: `GET /health`, `POST /v1/recommend`.
- **Request IDs** propagated through API responses and agent execution logs.
- **Structured JSON logging** with latency/status metadata.
- **Retry with exponential backoff** around Open-Meteo calls.
- **TTL caching** for geocoding, current weather and hourly forecasts.
- **Stable application exceptions** for city-not-found and external-service failures.
- **Generic error boundary** that avoids leaking internal exception details to API clients.
- **Automated tests** for validation, API contracts, cache and retry behavior.

### Run API

```bash
python -m api.run
```

Then open `/docs` for the interactive OpenAPI/Swagger documentation.

### API example

```json
POST /v1/recommend
{
  "city": "Kanpur",
  "skin_type": 3,
  "body_area": 25,
  "age": 25,
  "user_query": "Can I plan outdoor activity safely today?"
}
```

The API layer is deliberately separated from the Streamlit UI. This allows the same agent system to serve a web UI, automated clients, or a future mobile application.

## Phase 5 — Evaluation

Phase 5 adds a dedicated evaluation harness under `evaluation/`.

### Evaluation capabilities
- **200-scenario regression dataset** covering UV/heat boundaries, ages, locations and user intents.
- **Deterministic safety evaluation** with exact-match accuracy and mismatch reporting.
- **Agent evaluation** for required agent presence/order, verifier status, hard-stop invariants and citation contracts.
- **Groundedness checks** for WHO/CDC source metadata and known-source citation coverage.
- **Latency measurement** with mean/p95 metrics in the optional live benchmark.
- **Cost estimation** from measured/estimated token counts using configurable per-million-token prices.
- **Failure-case suite** for invalid inputs, hard stops, API retries, missing evidence and verification failure.

Run the offline suite:

```bash
python evaluation/evaluate_phase5.py
```

Run an optional live sample benchmark:

```bash
python evaluation/live_eval.py
```

The offline build result is stored in `evaluation/results/phase5_offline_results_v2.json`.

## Phase 6 — Deployment

### Local Docker run

1. Copy `.env.example` to `.env` and add your own credentials.
2. Build and start:

```bash
docker compose up --build
```

3. API health:
`http://localhost:8000/health`

4. FastAPI documentation:
`http://localhost:8000/docs`

### CI/CD

GitHub Actions is defined in `.github/workflows/ci.yml`. Every push and
pull request runs the test suite, Python compilation checks, and a Docker
build. No secrets are committed to the repository.

### Cloud deployment

The container is designed for any managed container platform that exposes
a public HTTP port, such as Render, Railway, Fly.io, Google Cloud Run,
Azure Container Apps, or AWS App Runner. Set environment variables through
the platform's secret manager rather than committing `.env`.

### Clean repository policy

Do not commit `.env`, API keys, `__pycache__`, `.pytest_cache`, local logs,
or generated secrets. Keep `.env.example` as the configuration template.


## Final engineering audit notes

- The agent system is intentionally **bounded and policy-constrained**: the orchestrator selects workflow steps, while deterministic safety policy remains authoritative. It is not marketed as an unconstrained autonomous medical agent.
- `/health` is a liveness probe; `/ready` verifies that the bundled RAG index exists.
- API requests have a configurable in-process rate limit. Production deployments should also enforce rate limiting at the cloud/API gateway layer.
- The default repository includes a lightweight SQLite vector store for reproducibility. Qdrant is an optional production adapter; install `requirements-dense-retrieval.txt` and configure the deployment if using a managed vector service.
- The bundled index may use the explicitly labeled offline embedding fallback. For a production-quality semantic benchmark, install the dense retrieval dependencies and rebuild the index with `python -m rag.build_index`.
- The decision window score is a transparent planning heuristic, **not** a probability or medical confidence score.
