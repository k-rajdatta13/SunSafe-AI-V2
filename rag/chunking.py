"""Document normalization and deterministic paragraph-aware chunking."""
from __future__ import annotations
import re
from typing import Iterable


def normalize_text(text: str) -> str:
    text = re.sub(r"\s+", " ", text or "").strip()
    return text


def split_sentences(text: str) -> list[str]:
    text = normalize_text(text)
    if not text:
        return []
    return [s.strip() for s in re.split(r"(?<=[.!?])\s+", text) if s.strip()]


def chunk_text(text: str, chunk_size: int = 900, overlap: int = 120) -> list[str]:
    """Create sentence-boundary chunks with configurable character overlap."""
    if chunk_size <= 0 or overlap < 0 or overlap >= chunk_size:
        raise ValueError("Require chunk_size > overlap >= 0")
    sentences = split_sentences(text)
    chunks: list[str] = []
    current = ""
    for sentence in sentences:
        candidate = f"{current} {sentence}".strip()
        if current and len(candidate) > chunk_size:
            chunks.append(current)
            tail = current[-overlap:] if overlap else ""
            current = f"{tail} {sentence}".strip()
        else:
            current = candidate
    if current:
        chunks.append(current)
    return [c for c in chunks if len(c) >= 40]
