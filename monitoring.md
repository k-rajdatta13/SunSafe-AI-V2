# Monitoring

## Health
`GET /health` provides a lightweight application health check.

## Logs
The API emits structured JSON logs with request/correlation identifiers,
latency and error context. Secrets are not logged.

## Production monitoring
For cloud deployment, connect application logs and `/health` to the
platform's log/health monitoring. A production deployment can additionally
export OpenTelemetry metrics/traces without changing the core agent graph.

## Recommended alerts
- Health endpoint unavailable
- HTTP 5xx rate above baseline
- External weather API timeout/retry spike
- Request latency p95 above target
- RAG retrieval/evaluation regression in CI
