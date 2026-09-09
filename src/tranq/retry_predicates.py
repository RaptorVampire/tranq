"""Retry predicates decide whether a failed attempt should be retried.

Exception predicates are callables: predicate(exception) -> bool.
Composable with ``&`` (AND) and ``|`` (OR).
"""


class retry_base:
    def __call__(self, exception: BaseException) -> bool:
        raise NotImplementedError

    def __and__(self, other):
        return retry_all(self, other)

    def __or__(self, other):
        return retry_any(self, other)


class retry_if_exception_type(retry_base):
    """Retry if the exception is one of the given types."""

    def __init__(self, exception_types):
        if isinstance(exception_types, type):
            exception_types = (exception_types,)
        self.exception_types = tuple(exception_types)

    def __call__(self, exception):
        return isinstance(exception, self.exception_types)


class retry_if_not_exception_type(retry_base):
    """Retry only if the exception is NOT one of the given types."""

    def __init__(self, exception_types):
        self._inner = retry_if_exception_type(exception_types)

    def __call__(self, exception):
        return not self._inner(exception)


class retry_if_exception(retry_base):
    """Retry based on an arbitrary predicate(exception)."""

    def __init__(self, predicate):
        self.predicate = predicate

    def __call__(self, exception):
        return self.predicate(exception)


class retry_if_result(retry_base):
    """Marker predicate applied to the RESULT (not the exception).

    The composition engine routes this to the result-checking path.
    """

    def __init__(self, predicate):
        self.predicate = predicate
        self.is_result_predicate = True

    def __call__(self, value):
        return self.predicate(value)


class retry_if_http_status(retry_base):
    """Retry when the exception carries a retryable HTTP status code.

    Looks for ``e.response.status_code``, ``e.status_code`` or ``e.status``.
    """

    def __init__(self, status_codes):
        if isinstance(status_codes, int):
            status_codes = (status_codes,)
        self.status_codes = set(status_codes)

    def _extract(self, exception):
        resp = getattr(exception, "response", None)
        if resp is not None and hasattr(resp, "status_code"):
            return resp.status_code
        for attr in ("status_code", "status"):
            v = getattr(exception, attr, None)
            if isinstance(v, int):
                return v
        return None

    def __call__(self, exception):
        code = self._extract(exception)
        return code is not None and code in self.status_codes


class retry_if_exception_chain(retry_base):
    """Retry if any exception in the __cause__/__context__ chain matches."""

    def __init__(self, exception_types):
        self._inner = retry_if_exception_type(exception_types)

    def __call__(self, exception):
        current = exception
        seen = set()
        while current is not None and id(current) not in seen:
            seen.add(id(current))
            if self._inner(current):
                return True
            current = current.__cause__ or current.__context__
        return False


class retry_if_retry_after(retry_base):
    """Retry when the exception signals a Retry-After (rate limit) condition."""

    def __call__(self, exception):
        if hasattr(exception, "retry_after"):
            return True
        resp = getattr(exception, "response", None)
        if resp is not None:
            headers = getattr(resp, "headers", None)
            if headers is not None and "Retry-After" in headers:
                return True
        return False


class retry_all(retry_base):
    def __init__(self, *preds):
        self.preds = preds

    def __call__(self, exception):
        return all(p(exception) for p in self.preds)


class retry_any(retry_base):
    def __init__(self, *preds):
        self.preds = preds

    def __call__(self, exception):
        return any(p(exception) for p in self.preds)


class retry_if:
    """Namespace with factory helpers."""
    exception_type = retry_if_exception_type
    not_exception_type = retry_if_not_exception_type
    exception = retry_if_exception
    result = retry_if_result
    http_status = retry_if_http_status
    exception_chain = retry_if_exception_chain
    retry_after = retry_if_retry_after
    all = retry_all
    any = retry_any
