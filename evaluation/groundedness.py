"""Phase 5 groundedness evaluators with backwards-compatible public APIs."""
from __future__ import annotations

from dataclasses import dataclass
import re
from typing import Any, Iterable


@dataclass(frozen=True)
class Claim:
    claim_id: str
    text: str
    cited_chunk_ids: tuple[str, ...] = ()


@dataclass(frozen=True)
class Evidence:
    chunk_id: str
    claim: str
    source: str
    url: str
    score: float | None = None


_AUTHORITATIVE_DOMAINS = ("who.int", "cdc.gov")
_AUTHORITATIVE_SOURCES = ("WHO", "CDC")


def _authoritative(url: str, source: str = "") -> bool:
    source_value = (source or "").strip().upper()
    if source_value in _AUTHORITATIVE_SOURCES:
        return True
    url_value = (url or "").lower()
    return any(domain in url_value for domain in _AUTHORITATIVE_DOMAINS)


def _numbers(text: str) -> list[str]:
    return re.findall(
        r"(?<!\w)\d+(?:\.\d+)?(?:\s*°?\s*[cf])?(?!\w)",
        text.lower(),
    )


def _negative(text: str) -> bool:
    return bool(re.search(
        r"\b(?:not|no|never|without|cannot|can't|shouldn't|mustn't)\b",
        text.lower(),
    ))


def _lexical_support(claim: str, evidence: str) -> bool:
    claim_tokens = re.findall(r"[a-z0-9]+", claim.lower())
    evidence_tokens = set(re.findall(r"[a-z0-9]+", evidence.lower()))
    stop = {
        "the", "a", "an", "and", "or", "to", "of", "in", "on", "for",
        "with", "is", "are", "be", "can", "may", "should", "must", "use",
        "when", "that", "this", "it", "as", "at", "by", "from", "than",
        "into", "your", "you", "will",
    }
    keywords = [x for x in claim_tokens if x not in stop and len(x) > 2]
    if not keywords:
        return False
    return sum(x in evidence_tokens for x in keywords) / len(keywords) >= 0.75


def _claim_supported(claim: Claim, cited: list[Evidence]) -> bool:
    if not cited:
        return False
    combined = " ".join(x.claim for x in cited)
    if _negative(claim.text) != _negative(combined):
        return False
    nums = _numbers(claim.text)
    if nums and not all(n in _numbers(combined) for n in nums):
        return False
    return _lexical_support(claim.text, combined)


def evaluate_claims(claims: Iterable[Claim], evidence: Iterable[Evidence]) -> dict[str, Any]:
    evidence_by_id = {x.chunk_id: x for x in evidence}
    verdicts = []
    for claim in claims:
        if not claim.cited_chunk_ids:
            status, score, reason = "UNSUPPORTED", 0.0, "missing_citation"
        else:
            cited = [evidence_by_id[x] for x in claim.cited_chunk_ids if x in evidence_by_id]
            if len(cited) != len(claim.cited_chunk_ids):
                status, score, reason = "UNVERIFIABLE", 0.0, "citation_not_found"
            elif not all(_authoritative(x.url, x.source) for x in cited):
                status, score, reason = "UNVERIFIABLE", 0.0, "non_authoritative_source"
            elif _claim_supported(claim, cited):
                status, score, reason = "SUPPORTED", 1.0, "supported_by_cited_evidence"
            else:
                status, score, reason = "UNSUPPORTED", 0.0, "evidence_does_not_support_claim"
        verdicts.append({
            "claim_id": claim.claim_id,
            "status": status,
            "groundedness_score": score,
            "reason": reason,
        })
    return {
        "verdicts": verdicts,
        "groundedness_score": round(
            sum(v["groundedness_score"] for v in verdicts) / len(verdicts)
            if verdicts else 0.0, 4),
        "claims": len(verdicts),
        "all_claims_supported": bool(verdicts) and all(
            v["status"] == "SUPPORTED" for v in verdicts
        ),
    }


def evaluate_evidence(evidence: Iterable[Any]) -> dict[str, Any]:
    items = list(evidence or [])
    if not items:
        return {
            "evidence_count": 0,
            "citation_completeness": 0.0,
            "authoritative_source_rate": 0.0,
            "source_authority": 0.0,
            "groundedness_score": 0.0,
        }
    total = len(items)
    complete = 0
    authoritative = 0
    for item in items:
        if isinstance(item, dict):
            source = str(item.get("source", ""))
            url = str(item.get("url", ""))
            chunk_id = str(item.get("chunk_id", item.get("id", "")))
        else:
            source = str(getattr(item, "source", ""))
            url = str(getattr(item, "url", ""))
            chunk_id = str(getattr(item, "chunk_id", getattr(item, "id", "")))
        if source and url and chunk_id:
            complete += 1
        if _authoritative(url, source):
            authoritative += 1
    citation_completeness = complete / total
    authoritative_source_rate = authoritative / total
    return {
        "evidence_count": total,
        "citation_completeness": round(citation_completeness, 4),
        "authoritative_source_rate": round(authoritative_source_rate, 4),
        "source_authority": round(authoritative_source_rate, 4),
        "groundedness_score": round(citation_completeness * authoritative_source_rate, 4),
    }


def evaluate_explanation(explanation: str | None, evidence: Iterable[Any]) -> dict[str, Any]:
    """Backward-compatible deterministic explanation smoke check.

    This is a contract check, not an LLM semantic-truth judge.
    """
    text = explanation or ""
    items = list(evidence or [])
    known_urls = set()
    for item in items:
        url = item.get("url") if isinstance(item, dict) else getattr(item, "url", None)
        if url:
            known_urls.add(str(url))
    cited_known = sum(1 for url in known_urls if url in text)
    return {
        "has_explanation": bool(text.strip()),
        "evidence_count": len(items),
        "known_source_urls_cited": cited_known,
        "citation_completeness": (
            cited_known / len(known_urls) if known_urls else 0.0
        ),
        "semantic_entailment": "NOT_EVALUATED",
    }
