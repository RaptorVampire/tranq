.. _examples:

========
Examples
========

The ``examples/`` directory contains **38 complete, runnable scripts** that
cover every feature in depth. Each file is self-contained and can be run
independently.

.. list-table::
   :header-rows: 1
   :widths: 30 70

   * - File
     - Topic
   * - ``01_basic_decorator.py``
     - Basic ``@handle`` usage, pass-through, reraise behavior
   * - ``02_retry_and_backoff.py``
     - All backoff strategies with delay visualization
   * - ``03_conditional_retry.py``
     - ``retry_if`` with status code inspection
   * - ``04_retry_on_result.py``
     - Retry on return value (None, 0, etc.)
   * - ``05_error_handlers.py``
     - Multiple ``on_error`` handlers for different types
   * - ``06_fallback.py``
     - Static, argument-aware, and post-retry fallbacks
   * - ``07_circuit_breaker.py``
     - Full state machine demo
   * - ``08_async_circuit_breaker.py``
     - Async circuit breaker lifecycle
   * - ``09_context_manager.py``
     - ``tranq.retry(...)`` with all features
   * - ``10_retry_group.py``
     - All-or-nothing sync group
   * - ``11_async_retry_group.py``
     - Mixed sync/async group
   * - ``12_metrics.py``
     - Metrics collection and retrieval
   * - ``13_profiling.py``
     - Sync and async profiling
   * - ``14_reporters.py``
     - File, custom, and multi-reporter
   * - ``15_mock_errors.py``
     - Error injection for testing
   * - ``16_dependency_injection.py``
     - ``inject`` parameter
   * - ``17_stateful_retry.py``
     - Persistent attempt counter
   * - ``18_global_policy.py``
     - Global defaults with per-function overrides
   * - ``19_async_decorator.py``
     - ``@handle_async`` full demo
   * - ``20_combined_advanced.py``
     - Everything combined in a realistic scenario
   * - ``21_timeout.py``
     - Sync and async timeout enforcement
   * - ``22_event_hooks.py``
     - Lifecycle hooks (on_retry/success/failure/complete)
   * - ``23_rate_limiter.py``
     - Token bucket rate limiting
   * - ``24_bulkhead.py``
     - Concurrency isolation with threads
   * - ``25_retry_budget.py``
     - Retry storm prevention
   * - ``26_hedged_requests.py``
     - Hedged async requests
   * - ``27_sliding_window_cb.py``
     - Failure-rate circuit breaker
   * - ``28_statistics_report.py``
     - Summary tables and health reports
   * - ``29_async_retry_context.py``
     - ``async with tranq.retry_async(...)``
   * - ``30_wait_stop.py``
     - Composable wait strategies and stop conditions
   * - ``31_cache.py``
     - Cache with stampede prevention and stale-if-error
   * - ``32_policy_builder.py``
     - Policy composition DSL
   * - ``33_adaptive.py``
     - Adaptive resilience controller
   * - ``34_chaos.py``
     - Chaos testing framework
   * - ``35_presets.py``
     - Policy presets for common backends
   * - ``36_event_bus.py``
     - Unified event bus
   * - ``37_diagnostics.py``
     - Automatic health analysis
   * - ``38_auto_llm.py``
     - Auto detection & LLM resilience


Run All Examples
================

.. code-block:: bash

   python examples/run_all.py


Run a Single Example
====================

.. code-block:: bash

   python examples/07_circuit_breaker.py
