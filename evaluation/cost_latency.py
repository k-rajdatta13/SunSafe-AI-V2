"""Latency and token/cost estimation utilities.

Costs are estimates. Set per-token prices through environment variables when a
provider/model price sheet changes; no claim is made that defaults represent a
live provider quote.
"""
from __future__ import annotations
import os
import time


def percentile(values: list[float], p: float) -> float:
    if not values:
        return 0.0
    values = sorted(values)
    idx = min(len(values) - 1, max(0, round((p / 100) * (len(values) - 1))))
    return values[idx]


def timed(fn):
    start = time.perf_counter()
    result = fn()
    return result, (time.perf_counter() - start) * 1000


def estimate_cost(input_tokens: int, output_tokens: int) -> dict:
    in_price = float(os.getenv("LLM_INPUT_USD_PER_1M", "0"))
    out_price = float(os.getenv("LLM_OUTPUT_USD_PER_1M", "0"))
    total = input_tokens * in_price / 1_000_000 + output_tokens * out_price / 1_000_000
    return {"input_tokens": input_tokens, "output_tokens": output_tokens,
            "usd_estimate": round(total, 8), "pricing_configured": bool(in_price or out_price)}
