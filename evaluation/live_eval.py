"""Optional live evaluation against the actual agent graph.

Run only when local dependencies, a weather connection and (for explanations)
a GOOGLE_API_KEY are configured. Weather calls are replaced by a deterministic
mock by default so latency/cost tests can be repeated safely.
"""
from __future__ import annotations
import json, time, os
from pathlib import Path
from statistics import mean

ROOT = Path(__file__).resolve().parents[1]


def estimate_tokens(text: str) -> int:
    # Coarse reproducible estimate for benchmarking; provider metadata should be
    # preferred when available.
    return max(1, len(text) // 4)


def run_sample(sample_size: int = 20) -> dict:
    rows = json.loads((ROOT / "evaluation" / "scenario_dataset_200.json").read_text())[:sample_size]
    latencies = []
    token_in = token_out = 0
    results = []
    try:
        from graph import run_agent
    except Exception as exc:
        return {"status":"unavailable", "reason":str(exc)}

    for row in rows:
        start = time.perf_counter()
        try:
            state = run_agent(row["city"], row["skin_type"], row["body_area"], row["age"], row["user_query"])
            elapsed = (time.perf_counter() - start) * 1000
            latencies.append(elapsed)
            explanation = state.get("explanation", "")
            token_in += estimate_tokens(row["user_query"])
            token_out += estimate_tokens(explanation)
            results.append({"scenario_id":row["scenario_id"],"ok":True,"latency_ms":round(elapsed,2),"verification":state.get("verification_status")})
        except Exception as exc:
            results.append({"scenario_id":row["scenario_id"],"ok":False,"error":type(exc).__name__})
    p95 = sorted(latencies)[min(len(latencies)-1, max(0, int(len(latencies)*0.95)-1))] if latencies else 0
    in_price = float(os.getenv("LLM_INPUT_USD_PER_1M", "0"))
    out_price = float(os.getenv("LLM_OUTPUT_USD_PER_1M", "0"))
    cost = token_in * in_price / 1e6 + token_out * out_price / 1e6
    return {
        "status":"complete", "samples":len(rows), "successes":sum(r["ok"] for r in results),
        "mean_latency_ms":round(mean(latencies),2) if latencies else 0,
        "p95_latency_ms":round(p95,2), "estimated_input_tokens":token_in,
        "estimated_output_tokens":token_out, "estimated_usd_cost":round(cost,8),
        "pricing_configured":bool(in_price or out_price), "results":results,
    }

if __name__ == "__main__":
    print(json.dumps(run_sample(), indent=2))
