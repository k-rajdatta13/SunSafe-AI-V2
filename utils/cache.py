"""Small thread-safe TTL cache used to reduce external API calls."""
from __future__ import annotations
import threading
import time
from dataclasses import dataclass
from typing import Any
@dataclass
class _Entry:
    value: Any
    expires_at: float
class TTLCache:
    def __init__(self, ttl_seconds: int = 300, max_items: int = 256):
        self.ttl_seconds = ttl_seconds
        self.max_items = max_items
        self._data: dict[str, _Entry] = {}
        self._lock = threading.RLock()
    def get(self, key: str) -> Any | None:
        with self._lock:
            item = self._data.get(key)
            if item is None:
                return None
            if item.expires_at <= time.monotonic():
                self._data.pop(key, None)
                return None
            return item.value
    def set(self, key: str, value: Any, ttl_seconds: int | None = None) -> None:
        with self._lock:
            if len(self._data) >= self.max_items and key not in self._data:
                oldest = min(self._data, key=lambda k: self._data[k].expires_at)
                self._data.pop(oldest, None)
            ttl = self.ttl_seconds if ttl_seconds is None else ttl_seconds
            self._data[key] = _Entry(value=value, expires_at=time.monotonic() + ttl)
    def clear(self) -> None:
        with self._lock:
            self._data.clear()
weather_cache = TTLCache(ttl_seconds=1800)
geocode_cache = TTLCache(ttl_seconds=86400)
forecast_cache = TTLCache(ttl_seconds=1800)
