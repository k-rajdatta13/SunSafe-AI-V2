"""Retry utility with exponential backoff and jitter."""
from __future__ import annotations
import random
import time
from collections.abc import Callable
from typing import TypeVar
T = TypeVar("T")
def with_retry(
    fn: Callable[[], T],
    *,
    attempts: int = 3,
    base_delay: float = 0.4,
    retry_exceptions: tuple[type[BaseException], ...] = (Exception,),
    jitter: float = 0.1,
) -> T:
    if attempts < 1:
        raise ValueError("attempts must be >= 1")
    last_error: BaseException | None = None
    for attempt in range(attempts):
        try:
            return fn()
        except retry_exceptions as exc:
            last_error = exc
            if attempt == attempts - 1:
                raise
            # Jitter is for retry timing, not cryptographic randomness.
            delay = base_delay * (2 ** attempt) + random.uniform(0, jitter)  # nosec B311
            time.sleep(delay)
    if last_error is None:
        raise RuntimeError("Retry loop exited without a result or exception")
    raise last_error
