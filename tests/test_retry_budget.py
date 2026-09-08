from tranq import RetryBudget, get_default_retry_budget, set_default_retry_budget


class TestRetryBudget:
    def test_initial_budget_allows_min_tokens(self):
        b = RetryBudget(ttl=60, ratio=0.2, min_tokens=3)
        assert b.allow_retry()
        assert b.allow_retry()
        assert b.allow_retry()
        assert not b.allow_retry()

    def test_record_call_adds_tokens(self):
        b = RetryBudget(ttl=60, ratio=0.5, min_tokens=0)
        for _ in range(10):
            b.record_call()
        allowed = sum(1 for _ in range(10) if b.allow_retry())
        assert allowed == 5

    def test_stats(self):
        b = RetryBudget()
        b.record_call()
        b.allow_retry()
        s = b.stats()
        assert s["calls"] == 1
        assert s["retries"] == 1

    def test_default_budget(self):
        b = RetryBudget()
        set_default_retry_budget(b)
        assert get_default_retry_budget() is b
        set_default_retry_budget(None)
