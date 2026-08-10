.. tranq documentation master file, created by sphinx-quickstart
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

🌿 tranq
========

.. image:: https://img.shields.io/badge/PyPI-tranq-blue?style=flat-square
   :target: https://pypi.org/project/tranq/
   :alt: PyPI

.. image:: https://img.shields.io/badge/GitHub-RaptorVampire/tranq-black?style=flat-square
   :target: https://github.com/RaptorVampire/tranq
   :alt: GitHub

.. image:: https://img.shields.io/badge/python-3.9%2B-green?style=flat-square
   :alt: Python 3.9+

.. image:: https://img.shields.io/badge/tests-120%2B%20passing-brightgreen?style=flat-square
   :alt: Tests

.. image:: https://img.shields.io/badge/license-MIT-orange?style=flat-square
   :alt: License

**Calm error handling for Python** – decorator-based, zero boilerplate.

.. contents:: Table of Contents
   :local:
   :depth: 2
   :backlinks: none

.. _why-tranq:

🧘 Why tranq?
--------------

Writing repetitive ``try`` / ``except`` blocks clutters your code and hides the business logic.
**tranq** gives you declarative error handling with decorators, context managers, and a rich set of retry strategies – so you can focus on **what** your code does, not **how** it recovers from failures.

.. list-table:: Features Overview
   :header-rows: 1
   :widths: 30 70

   * - Feature
     - Description
   * - 🧘 **Tranquil**
     - Clean, readable, and maintainable.
   * - 🔁 **Smart retries**
     - Exponential, linear, Fibonacci backoff, jitter, and max delay.
   * - 🚦 **Circuit Breaker**
     - Prevent cascading failures (sync & async).
   * - 🧪 **Conditional retry**
     - On specific exceptions **or** result values.
   * - 📦 **Retry groups**
     - All-or-nothing execution for multiple functions.
   * - 📊 **Built-in metrics & profiling**
     - Monitor performance and error rates.
   * - 📝 **Pluggable reporters**
     - Send errors to files (JSON), Sentry, Slack, or custom destinations.
   * - 🧩 **Context manager API**
     - Use ``tranq.retry(...)`` with all decorator features.
   * - 🔧 **Stateful retry**
     - Persist attempt count across calls (thread/async safe).
   * - 🎭 **Mock error injection**
     - Test your error handling with ease.
   * - 💉 **Dependency injection**
     - Inject dependencies into decorated functions.
   * - 🌐 **Global policy**
     - Set defaults once, override per function.

.. _installation:

📦 Installation
---------------

Install from PyPI:

.. code-block:: bash

   pip install tranq

.. note::
   Requires **Python 3.9** or later.

For rich logging output with colors:

.. code-block:: bash

   pip install tranq[rich]

For development (includes testing tools):

.. code-block:: bash

   pip install tranq[dev]

.. _quick-start:

⚡ Quick Start
--------------

Decorator (``@handle``)
~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   import tranq

   @tranq.handle(on=ValueError, retry=3, delay=0.5, backoff=2.0)
   def risky():
       ...

Async (``@handle_async``)
~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   @tranq.handle_async(on=ConnectionError, retry=2, fallback=lambda: "offline")
   async def fetch_data():
       ...

Circuit Breaker
~~~~~~~~~~~~~~~~

.. code-block:: python

   cb = tranq.CircuitBreaker(failure_threshold=5, timeout=60)

   @tranq.handle(circuit_breaker=cb)
   def call_unstable_service():
       ...

Context Manager (full feature parity)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   with tranq.retry(on=ValueError, retry=2, retry_if=lambda e: "503" in str(e)) as ctx:
       result = ctx.run(my_function, arg1, arg2)

Retry Group (all-or-nothing)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   group = tranq.retry_group(step1, step2, step3, on=Exception, retry=1)
   results = group.run()  # if any step fails, all are retried together

.. _features-in-depth:

🔍 Features in Depth
--------------------

1. Retry with Backoff
~~~~~~~~~~~~~~~~~~~~~~

Choose from **exponential**, **linear**, or **Fibonacci** backoff. Add **jitter** to avoid thundering herds.

.. code-block:: python

   @tranq.handle(
       on=TimeoutError,
       retry=5,
       delay=0.1,
       backoff=2.0,
       backoff_strategy="exponential",  # "linear", "fibonacci", or custom callable
       max_delay=10.0,
       jitter=True,
   )
   def fetch():
       ...

2. Conditional Retry
~~~~~~~~~~~~~~~~~~~~~

- ``retry_if`` – retry only when the exception matches a condition.
- ``retry_on_result`` – retry if the result is unacceptable (e.g., ``None``).

.. code-block:: python

   @tranq.handle(
       on=requests.RequestException,
       retry_if=lambda e: e.response.status_code == 429,  # rate-limit
       retry=3,
   )
   def call_api():
       ...

   @tranq.handle(
       retry_on_result=lambda result: result is None,
       retry=2,
   )
   def get_data():
       ...

3. Error Handlers (``on_error``)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Run different callbacks for different exception types.

.. code-block:: python

   def log_warning(e):
       print(f"Warning: {e}")

   @tranq.handle(
       on=(ValueError, ConnectionError),
       on_error={ValueError: log_warning},
   )
   def process():
       ...

4. Circuit Breaker (Sync & Async)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   from tranq import CircuitBreaker, AsyncCircuitBreaker

   cb = CircuitBreaker(failure_threshold=3, timeout=30, half_open_requests=1)

   @tranq.handle(circuit_breaker=cb)
   def sync_call():
       ...

   acb = AsyncCircuitBreaker(failure_threshold=3, timeout=30)

   @tranq.handle_async(circuit_breaker=acb)
   async def async_call():
       ...

5. Stateful Retry (thread-safe)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Uses ``contextvars`` to isolate counters, safe for async and threaded code.

.. code-block:: python

   @tranq.handle(on=ValueError, retry=3, stateful=True)
   def process_item(item):
       ...

6. Reporters (JSON file, Sentry, Slack)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   from tranq import FileReporter, SentryReporter, SlackReporter

   reporters = [
       FileReporter("/var/log/tranq_errors.json"),
       SentryReporter(dsn="..."),
       SlackReporter(webhook_url="..."),
   ]

   @tranq.handle(on=Exception, reporters=reporters)
   def critical_task():
       ...

``FileReporter`` writes JSON lines for easier parsing.

7. Metrics & Profiling
~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   @tranq.handle(metrics=True, metric_prefix="myapp")
   def expensive_op():
       ...

   from tranq import get_metrics, profile, get_profile

   @profile
   def heavy_computation():
       ...

   print(get_metrics())
   print(get_profile("heavy_computation"))

8. Mock Error Injection
~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   from tranq import mock_errors

   with mock_errors(ValueError, probability=0.8):
       result = my_function()

9. Dependency Injection
~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   @tranq.handle(inject={"logger": logging.getLogger("app")})
   def do_work(logger=None):
       logger.info("Working...")

10. Global Policy
~~~~~~~~~~~~~~~~~~

.. code-block:: python

   tranq.set_global_policy(tranq.Policy(
       retry=3,
       delay=0.5,
       backoff=2.0,
       reraise=False,
   ))

   # All @handle calls now inherit these defaults
   @tranq.handle(on=ValueError)
   def my_func():
       ...

.. _advanced-example:

🚀 Advanced Example
-------------------

Combining multiple features for a robust API call:

.. code-block:: python

   cb = CircuitBreaker(failure_threshold=3, timeout=60)

   @tranq.handle(
       on=requests.RequestException,
       retry=5,
       backoff_strategy="fibonacci",
       max_delay=30,
       jitter=True,
       retry_if=lambda e: e.response.status_code in (429, 503),
       circuit_breaker=cb,
       metrics=True,
       metric_prefix="api",
       reporters=[FileReporter("api_errors.json")],
       fallback=lambda: {"status": "fallback"},
   )
   def fetch_from_external_api():
       ...

.. _api-reference:

📚 API Reference
----------------

Decorators
~~~~~~~~~~

.. py:function:: tranq.handle(...)

   Decorator for synchronous functions with error handling and retry logic.

   :param on: Exception type(s) to catch
   :type on: type | tuple[type]
   :param retry: Number of retries (0 = no retry)
   :type retry: int
   :param delay: Base delay between retries (seconds)
   :type delay: float
   :param backoff: Backoff multiplier
   :type backoff: float
   :param backoff_strategy: ``"exponential"``, ``"linear"``, ``"fibonacci"``, or custom callable
   :type backoff_strategy: str | callable
   :param max_delay: Cap on delay between retries
   :type max_delay: float | None
   :param jitter: Add ±25% randomness to delays
   :type jitter: bool
   :param fallback: Function to call when all retries fail
   :type fallback: callable | None
   :param reraise: Re-raise exception after exhaustion
   :type reraise: bool
   :param log_level: Logging level for retry messages
   :type log_level: int
   :param message: Custom log format string
   :type message: str | None
   :param policy: Explicit policy object
   :type policy: Policy | None
   :param retry_if: Condition to decide if retry should happen
   :type retry_if: callable | None
   :param retry_on_result: Retry if result matches condition
   :type retry_on_result: callable | None
   :param on_error: Exception-type → handler mapping
   :type on_error: dict | None
   :param metrics: Collect metrics for this function
   :type metrics: bool
   :param metric_prefix: Prefix for metric keys
   :type metric_prefix: str
   :param circuit_breaker: Circuit breaker instance
   :type circuit_breaker: CircuitBreaker | None
   :param stateful: Persist attempt count across calls
   :type stateful: bool
   :param reporters: List of reporter instances
   :type reporters: list | None
   :param inject: Dependencies to inject
   :type inject: dict | None

.. py:function:: tranq.handle_async(...)

   Decorator for asynchronous functions. Same parameters as :func:`tranq.handle`.

Context Manager
~~~~~~~~~~~~~~~

.. py:function:: tranq.retry(...)

   Context manager offering all retry/decorator features.

   **Usage:**

   .. code-block:: python

      with tranq.retry(on=ValueError, retry=3) as ctx:
          result = ctx.run(my_function, arg1, kwarg1=val)

Retry Groups
~~~~~~~~~~~~

.. py:function:: tranq.retry_group(*funcs, **kwargs)

   All-or-nothing retry group for synchronous functions.

   **Usage:**

   .. code-block:: python

      group = tranq.retry_group(func1, func2, func3, on=Exception, retry=2)
      results = group.run()

.. py:function:: tranq.async_retry_group(*funcs, **kwargs)

   All-or-nothing retry group for asynchronous functions (supports mixed sync/async).

Circuit Breakers
~~~~~~~~~~~~~~~~

.. py:class:: tranq.CircuitBreaker(failure_threshold=5, timeout=60.0, half_open_requests=1)

   Synchronous circuit breaker.

   **States:** ``closed`` → ``open`` → ``half-open`` → ``closed``

.. py:class:: tranq.AsyncCircuitBreaker(failure_threshold=5, timeout=60.0, half_open_requests=1)

   Asynchronous circuit breaker using ``asyncio.Lock``.

Policies
~~~~~~~~

.. py:class:: tranq.Policy

   Dataclass encapsulating error-handling configuration.

.. py:function:: tranq.set_global_policy(policy: Policy)

   Set the global default policy for all ``@handle`` decorators.

.. py:function:: tranq.get_global_policy() -> Policy

   Get the current global policy.

Reporters
~~~~~~~~~

.. py:class:: tranq.Reporter

   Abstract base class for error reporters.

.. py:class:: tranq.FileReporter(file_path: str)

   Reporter that writes error details to a file as JSON lines.

.. py:class:: tranq.SentryReporter(dsn: str)

   Placeholder for Sentry error reporting.

.. py:class:: tranq.SlackReporter(webhook_url: str)

   Placeholder for Slack webhook reporting.

Utilities
~~~~~~~~~

.. py:function:: tranq.get_metrics() -> dict

   Get all collected metrics.

.. py:function:: tranq.reset_metrics() -> None

   Clear all collected metrics.

.. py:function:: tranq.profile(func: Callable) -> Callable

   Decorator to measure execution time of a sync function.

.. py:function:: tranq.async_profile(func: Callable) -> Callable

   Decorator to measure execution time of an async function.

.. py:function:: tranq.get_profile(name: str = None)

   Get profiling data for a specific function or all functions.

.. py:function:: tranq.mock_errors(exception, probability=0.5, seed=None)

   Context manager that injects the given exception with the specified probability.

Exceptions
~~~~~~~~~~

.. py:exception:: tranq.TranqError

   Base exception for all tranq errors.

.. py:exception:: tranq.RetryExhaustedError

   Raised when all retries are exhausted and ``reraise=True``.

.. py:exception:: tranq.CircuitBreakerError

   Raised when circuit breaker is open.

.. py:exception:: tranq.ResultNotAcceptedError

   Raised when ``retry_on_result`` condition is not met after all attempts.

.. py:exception:: tranq.RetryGroupError

   Raised when ``retry_group`` encounters an error in any member.

.. _examples:

📁 Examples
-----------

The ``examples/`` directory contains **20 complete, runnable examples** covering every feature:

.. list-table:: Example Scripts
   :header-rows: 1
   :widths: 40 60

   * - File
     - Topic
   * - ``01_basic_decorator.py``
     - Basic ``@handle`` usage
   * - ``02_retry_and_backoff.py``
     - All backoff strategies
   * - ``03_conditional_retry.py``
     - ``retry_if``
   * - ``04_retry_on_result.py``
     - Retry on return value
   * - ``05_error_handlers.py``
     - Multiple ``on_error`` handlers
   * - ``06_fallback.py``
     - Fallback values/functions
   * - ``07_circuit_breaker.py``
     - Sync circuit breaker
   * - ``08_async_circuit_breaker.py``
     - Async circuit breaker
   * - ``09_context_manager.py``
     - ``with tranq.retry(...)``
   * - ``10_retry_group.py``
     - Sync retry group
   * - ``11_async_retry_group.py``
     - Async retry group
   * - ``12_metrics.py``
     - Metrics collection
   * - ``13_profiling.py``
     - Function profiling
   * - ``14_reporters.py``
     - File/custom reporters
   * - ``15_mock_errors.py``
     - Mock error injection
   * - ``16_dependency_injection.py``
     - ``inject`` parameter
   * - ``17_stateful_retry.py``
     - Stateful retry
   * - ``18_global_policy.py``
     - Global policy
   * - ``19_async_decorator.py``
     - ``@handle_async``
   * - ``20_combined_advanced.py``
     - Everything combined

**Run all examples:**

.. code-block:: bash

   python examples/run_all.py

**Run a single example:**

.. code-block:: bash

   python examples/07_circuit_breaker.py

.. _testing:

🧪 Testing
----------

The ``tests/`` directory contains a comprehensive test suite with **120+ tests** covering all features:

- Circuit breaker state transitions (sync & async)
- Half-open request limits
- All backoff strategies (exponential, linear, fibonacci, custom)
- Jitter and max_delay
- Conditional retry (``retry_if``, ``retry_on_result``)
- Error handlers, fallback, dependency injection
- Stateful retry with thread isolation
- Retry groups (sync & async, mixed sync/async)
- Reporters (FileReporter JSON output)
- Metrics and profiling
- Mock error injection
- Global policy

**Run all tests:**

.. code-block:: bash

   pip install pytest pytest-asyncio
   pytest tests/ -v

**Run a specific test file:**

.. code-block:: bash

   pytest tests/test_circuit_breaker.py -v

.. _comparison:

⚖️ Comparison
-------------

.. list-table:: Feature Comparison
   :header-rows: 1
   :widths: 40 20 20 20

   * - Feature
     - tranq
     - tenacity
     - backoff
   * - Decorator
     - ✅
     - ✅
     - ✅
   * - Async support
     - ✅
     - ✅
     - ✅
   * - Circuit Breaker
     - ✅
     - ❌
     - ❌
   * - Context Manager
     - ✅
     - ❌
     - ❌
   * - Retry Groups
     - ✅
     - ❌
     - ❌
   * - Metrics
     - ✅
     - ❌
     - ❌
   * - Profiling
     - ✅
     - ❌
     - ❌
   * - Reporters
     - ✅
     - ❌
     - ❌
   * - Mock Errors
     - ✅
     - ❌
     - ❌
   * - Dependency Injection
     - ✅
     - ❌
     - ❌
   * - Global Policy
     - ✅
     - ❌
     - ❌
   * - Stateful Retry
     - ✅
     - ❌
     - ❌

.. _project-structure:

🗂️ Project Structure
---------------------

.. code-block:: text

   tranq/
   ├── examples/                    # 20 runnable examples
   │   ├── 01_basic_decorator.py
   │   ├── ...
   │   ├── 20_combined_advanced.py
   │   └── run_all.py
   ├── src/tranq/
   │   ├── __init__.py              # Public API
   │   ├── decorators.py            # @handle / @handle_async
   │   ├── context.py               # retry() context manager
   │   ├── circuit_breaker.py       # Sync circuit breaker
   │   ├── async_circuit_breaker.py # Async circuit breaker
   │   ├── retry_group.py           # Retry groups (sync/async)
   │   ├── policies.py              # Policy dataclass
   │   ├── exceptions.py            # Custom exceptions
   │   ├── metrics.py               # Metrics collection
   │   ├── profiling.py             # Function profiling
   │   ├── reporters.py             # Error reporters
   │   ├── mock.py                  # Mock error injection
   │   └── utils.py                 # Backoff, jitter, logging
   ├── tests/                       # 120+ tests
   │   ├── test_circuit_breaker.py
   │   ├── test_decorators_sync.py
   │   ├── test_decorators_async.py
   │   ├── ...
   │   └── test_thread_safety.py
   ├── pyproject.toml
   ├── pytest.ini
   ├── README.md
   ├── CONTRIBUTING.md
   └── LICENSE

.. _contributing:

🤝 Contributing
---------------

Contributions are welcome! Please see `CONTRIBUTING.md <https://github.com/RaptorVampire/tranq/blob/main/CONTRIBUTING.md>`_ for guidelines.

.. _license:

📄 License
----------

**MIT** © `RaptorVampire <https://github.com/RaptorVampire>`_

---

.. toctree::
   :maxdepth: 2
   :caption: Contents:
   :hidden:

   self

Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`