.. _testing:

=======
Testing
=======

tranq includes a comprehensive test suite with **190+ tests** covering all
features. This page shows how to run them and how to test **your own code**
that uses tranq.


Running the Test Suite
======================

.. code-block:: bash

   pip install -e ".[dev]"
   pytest tests/ -v

Run a specific test module:

.. code-block:: bash

   pytest tests/test_circuit_breaker.py -v
   pytest tests/test_composition.py -v
   pytest tests/test_cache.py -v


Test Categories
===============

- Circuit breaker state transitions (sync & async, count & sliding-window)
- All backoff strategies (exponential, linear, fibonacci, custom)
- Jitter and max_delay
- Conditional retry (``retry_if``, ``retry_on_result``)
- Error handlers, fallback, dependency injection
- Stateful retry with thread isolation
- Retry groups (sync & async, mixed)
- Reporters (FileReporter JSON output)
- Metrics and profiling
- Mock error injection
- Global policy
- Timeout (sync & async)
- Event hooks (sync & async)
- Rate limiters (5 algorithms)
- Bulkhead (4 types)
- Retry budget
- Hedged requests
- Async context manager
- Wait/stop/retry_if composition
- Policy builder
- Cache with stampede prevention
- Chaos testing
- Presets
- Diagnostics


Testing Your Own Code
=====================

Mock Error Injection
--------------------

Use :func:`tranq.mock_errors` to simulate failures in tests:

.. code-block:: python

   from tranq import mock_errors

   def test_my_function_handles_connection_error():
       with mock_errors(ConnectionError, probability=1.0):
           result = my_function()  # will raise ConnectionError
           assert result == expected_fallback


Chaos Testing
-------------

For more sophisticated resilience testing, use :func:`tranq.chaos`:

.. code-block:: python

   from tranq import chaos

   def test_service_under_load():
       with chaos(latency=0.1, error_rate=0.3, timeout_rate=0.05) as inj:
           for _ in range(100):
               inj.maybe_inject()
               result = call_service()
               assert result is not None


Verifying Resilience Policies
-----------------------------

Use pytest fixtures to share circuit breakers and caches:

.. code-block:: python

   import pytest
   from tranq import CircuitBreaker, get_registry

   @pytest.fixture
   def payment_cb():
       cb = get_registry().get("payment", failure_threshold=3)
       cb.reset()
       yield cb
       cb.reset()

   def test_payment_circuit_opens(payment_cb):
       for _ in range(3):
           with pytest.raises(RuntimeError):
               call_payment()
       assert payment_cb.state == "open"


See Also
========

* :doc:`features/chaos`
* :doc:`api/metrics` — ``mock_errors``
