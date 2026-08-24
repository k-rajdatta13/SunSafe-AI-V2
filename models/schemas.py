"""Pydantic contracts for the production API layer."""
from __future__ import annotations
from typing import Any, Literal
from pydantic import BaseModel, ConfigDict, Field, field_validator

class RecommendationRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    city: str = Field(min_length=2, max_length=100)
    skin_type: int = Field(ge=1, le=6)
    body_area: int = Field(ge=1, le=100)
    age: int = Field(ge=1, le=120)
    user_query: str = Field(default="Can I plan outdoor activity safely today?", max_length=1000)
    @field_validator("city")
    @classmethod
    def clean_city(cls, value: str) -> str:
        value = " ".join(value.strip().split())
        if not value:
            raise ValueError("city must not be blank")
        return value

class EvidenceItem(BaseModel):
    source: str
    url: str
    topic: str
    claim: str
    score: float = 0.0
    chunk_id: str

class RecommendationResponse(BaseModel):
    model_config = ConfigDict(extra="allow")
    request_id: str
    status: Literal["success", "degraded", "failed"]
    city: str
    country: str | None = None
    temperature: float | None = None
    uv_index: float | None = None
    uv_level: str | None = None
    protection_required: bool | None = None
    heat_caution: str | None = None
    overall_action: str | None = None
    best_time: str | None = None
    hard_stop: bool | None = None
    decision_score: float | None = None
    evidence: list[EvidenceItem] = Field(default_factory=list)
    evidence_status: Literal["AVAILABLE", "UNAVAILABLE", "UNKNOWN"] = "UNKNOWN"
    verification_status: str = "UNKNOWN"
    verification_issues: list[str] = Field(default_factory=list)
    explanation: str | None = None
    trace: list[dict[str, Any]] = Field(default_factory=list)

class HealthResponse(BaseModel):
    status: Literal["ok"] = "ok"
    service: str = "sunsafe-ai"
    version: str = "2.0-final-audit"
