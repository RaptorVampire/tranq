import pytest
from tranq import retry_if


class HttpErr(Exception):
    def __init__(self, status):
        self.status_code = status


class TestRetryPredicates:
    def test_exception_type(self):
        p = retry_if.exception_type(ValueError)
        assert p(ValueError())
        assert not p(KeyError())

    def test_not_exception_type(self):
        p = retry_if.not_exception_type(ValueError)
        assert not p(ValueError())
        assert p(KeyError())

    def test_http_status(self):
        p = retry_if.http_status((429, 503))
        assert p(HttpErr(429))
        assert p(HttpErr(503))
        assert not p(HttpErr(404))

    def test_exception_chain(self):
        p = retry_if.exception_chain(ConnectionError)
        try:
            try:
                raise ConnectionError("root")
            except ConnectionError as ce:
                raise ValueError("wrapped") from ce
        except ValueError as e:
            assert p(e)

    def test_or_composition(self):
        p = retry_if.exception_type(ValueError) | retry_if.http_status(429)
        assert p(ValueError())
        assert p(HttpErr(429))
        assert not p(KeyError())

    def test_and_composition(self):
        p = retry_if.exception_type(ValueError) & retry_if.exception(lambda e: "x" in str(e))
        assert p(ValueError("x happened"))
        assert not p(ValueError("y happened"))
