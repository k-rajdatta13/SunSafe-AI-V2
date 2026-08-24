"""Evaluation metrics used by the Phase-5 harness."""
from __future__ import annotations
import math
from typing import Iterable


def recall_at_k(results: list[str], relevant: set[str], k: int) -> float:
    if not relevant:
        return 1.0
    return 1.0 if relevant.intersection(results[:k]) else 0.0


def reciprocal_rank(results: list[str], relevant: set[str]) -> float:
    for i, item in enumerate(results, 1):
        if item in relevant:
            return 1.0 / i
    return 0.0


def ndcg_at_k(results: list[str], relevant: set[str], k: int) -> float:
    gains = [1.0 if x in relevant else 0.0 for x in results[:k]]
    dcg = sum(g / math.log2(i + 2) for i, g in enumerate(gains))
    ideal = sum(1.0 / math.log2(i + 2) for i in range(min(len(relevant), k)))
    return dcg / ideal if ideal else 1.0


def mean(values: Iterable[float]) -> float:
    vals = list(values)
    return sum(vals) / len(vals) if vals else 0.0
