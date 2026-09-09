import time
import pytest
from tranq import TranqCache, cache


class TestTranqCache:
    def test_set_get(self):
        c = TranqCache(ttl=10)
        c.set("k", "v")
        hit, val = c.get("k")
        assert hit and val == "v"

    def test_ttl_expiry(self):
        c = TranqCache(ttl=0.05)
        c.set("k", "v")
        time.sleep(0.06)
        hit, _ = c.get("k")
        assert not hit

    def test_stale_get(self):
        c = TranqCache(ttl=0.05)
        c.set("k", "v")
        time.sleep(0.06)
        hit, val = c.get_stale("k")
        assert hit and val == "v"

    def test_lru_eviction(self):
        c = TranqCache(maxsize=2)
        c.set("a", 1)
        c.set("b", 2)
        c.set("c", 3)
        hit, _ = c.get("a")
        assert not hit

    def test_negative_caching(self):
        c = TranqCache(ttl=10, negative_ttl=1)
        c.set("k", None, negative=True)
        hit, val = c.get("k")
        assert hit
        assert c.stats["negative_hits"] == 1

    def test_single_flight(self):
        c = TranqCache(ttl=10)
        calls = [0]

        def loader():
            calls[0] += 1
            return "loaded"

        r1 = c.single_flight("k", loader)
        r2 = c.get("k")
        assert r1 == "loaded"
        assert calls[0] == 1

    def test_metrics(self):
        c = TranqCache(ttl=10)
        c.set("k", "v")
        c.get("k")
        c.get("missing")
        m = c.metrics()
        assert m["hits"] == 1
        assert m["misses"] == 1


class TestCacheDecorator:
    def test_caches_result(self):
        calls = [0]

        @cache(ttl=10)
        def compute(x):
            calls[0] += 1
            return x * 2

        assert compute(5) == 10
        assert compute(5) == 10
        assert calls[0] == 1
