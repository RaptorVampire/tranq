from tranq import presets


def test_http_preset():
    cfg = presets.http()
    assert "wait" in cfg
    assert "stop" in cfg
    assert cfg["timeout"] == 10.0


def test_all_presets_callable():
    for name in ("http", "database", "redis", "kafka", "queue", "grpc", "llm"):
        cfg = getattr(presets, name)()
        assert callable(cfg["wait"])
        assert callable(cfg["stop"])


def test_http_retry_if_429():
    cfg = presets.http()

    class E(Exception):
        status_code = 429

    assert cfg["retry_if"](E())
