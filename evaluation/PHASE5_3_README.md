# Phase 5.3 — Evidence availability invariant

The RAG layer now exposes `evidence_status` explicitly:
- `AVAILABLE`: retrieval returned evidence.
- `UNAVAILABLE`: retrieval returned zero evidence.

Zero evidence is no longer represented as a normal grounded success. The API
returns HTTP 200 with `status="degraded"` so deterministic environmental safety
guidance can remain available while the response explicitly discloses that
authoritative evidence was unavailable.

The explainer prompt forbids invented sources and requires an evidence-unavailable
notice.

The live integration evaluator now tests the production behavior itself:
missing evidence must produce degraded status, UNAVAILABLE evidence status, zero
evidence, and an explanation containing the authority-unavailable disclosure.

This preserves the key separation:
deterministic safety policy remains authoritative; RAG supplies authoritative
context but cannot silently disappear while the response is presented as grounded.
