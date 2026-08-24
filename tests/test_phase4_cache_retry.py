import pytest

from utils.cache import TTLCache
from utils.retry import with_retry


def test_ttl_cache_round_trip():
    cache = TTLCache(ttl_seconds=60)
    cache.set("x", {"value": 1})
    assert cache.get("x") == {"value": 1}


def test_retry_eventually_succeeds():
    attempts = {"count": 0}
    def fn():
        attempts["count"] += 1
        if attempts["count"] < 3:
            raise RuntimeError("temporary")
        return "ok"
    assert with_retry(fn, attempts=3, base_delay=0) == "ok"
    assert attempts["count"] == 3


def test_retry_raises_after_limit():
    def fn():
        raise RuntimeError("permanent")
    with pytest.raises(RuntimeError):
        with_retry(fn, attempts=2, base_delay=0)
