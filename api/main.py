"""FastAPI production API for SunSafe AI."""
from __future__ import annotations
import time
import uuid
import os
from collections import defaultdict, deque
from typing import Callable
from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from pydantic import ValidationError
from api.exceptions import CityNotFoundError, ExternalServiceError, SunSafeError
from api.service import generate_recommendation
from models.schemas import HealthResponse, RecommendationRequest, RecommendationResponse
from utils.logging_config import configure_logging, get_logger, log_event

configure_logging()
logger = get_logger("sunsafe.api")
_RATE_LIMIT = int(os.getenv("RATE_LIMIT_PER_MINUTE", "60"))
_rate_windows: dict[str, deque[float]] = defaultdict(deque)

def _rate_limited(client_key: str) -> bool:
    now = time.monotonic()
    window = _rate_windows[client_key]
    while window and window[0] <= now - 60:
        window.popleft()
    if len(window) >= _RATE_LIMIT:
        return True
    window.append(now)
    return False

app = FastAPI(
    title="SunSafe AI API",
    version="2.0-final-audit",
    description="Evidence-grounded UV and outdoor safety decision-support API.",
)

@app.middleware("http")
async def request_context(request: Request, call_next: Callable):
    request_id = request.headers.get("X-Request-ID", str(uuid.uuid4()))
    started = time.perf_counter()
    request.state.request_id = request_id
    client_key = request.client.host if request.client else "unknown"
    if request.url.path.startswith("/v1/") and _rate_limited(client_key):
        return JSONResponse(status_code=429, content={"error":"RATE_LIMITED","message":"Too many requests. Please retry later.","request_id":request_id}, headers={"Retry-After":"60","X-Request-ID":request_id})
    try:
        response = await call_next(request)
        response.headers["X-Request-ID"] = request_id
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["Referrer-Policy"] = "no-referrer"
        log_event(logger, 20, "request_completed", request_id=request_id, method=request.method, path=request.url.path, status_code=response.status_code, latency_ms=round((time.perf_counter()-started)*1000,2))
        return response
    except Exception:
        log_event(logger, 40, "request_failed", request_id=request_id, method=request.method, path=request.url.path, latency_ms=round((time.perf_counter()-started)*1000,2))
        raise

@app.exception_handler(SunSafeError)
async def sunsafe_error_handler(request: Request, exc: SunSafeError):
    status = 404 if isinstance(exc, CityNotFoundError) else 502 if isinstance(exc, ExternalServiceError) else 400
    return JSONResponse(status_code=status, content={"error":exc.code,"message":str(exc),"request_id":getattr(request.state,"request_id",None)})

@app.exception_handler(RequestValidationError)
async def request_validation_error_handler(request: Request, exc: RequestValidationError):
    return JSONResponse(status_code=422, content={"error":"VALIDATION_ERROR","message":"Request validation failed","details":exc.errors(),"request_id":getattr(request.state,"request_id",None)})

@app.exception_handler(Exception)
async def unexpected_error_handler(request: Request, exc: Exception):
    log_event(logger,40,"unhandled_exception",request_id=getattr(request.state,"request_id",None),error=str(exc))
    return JSONResponse(status_code=500, content={"error":"INTERNAL_ERROR","message":"An unexpected error occurred.","request_id":getattr(request.state,"request_id",None)})

@app.get("/health", response_model=HealthResponse)
def health() -> HealthResponse:
    return HealthResponse(version="2.0-final-audit")

@app.get("/ready")
def ready() -> dict:
    from pathlib import Path
    index_path = Path(__file__).resolve().parents[1] / "knowledge" / "index" / "vectors.sqlite3"
    ready = index_path.exists() and index_path.stat().st_size > 0
    return {"status":"ready" if ready else "not_ready","rag_index":ready}

@app.post("/v1/recommend", response_model=RecommendationResponse)
def recommend(payload: RecommendationRequest, request: Request) -> RecommendationResponse:
    request_id = request.state.request_id
    log_event(logger,20,"recommendation_started",request_id=request_id,city=payload.city)
    result = generate_recommendation(payload)
    result["request_id"] = request_id
    # Evidence unavailability is a successful, bounded degraded mode—not an
    # internal error and not a grounded success.
    result["status"] = "degraded" if result.get("evidence_status") == "UNAVAILABLE" else "success"
    return RecommendationResponse.model_validate(result)
