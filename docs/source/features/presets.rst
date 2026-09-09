.. _feature-presets:

==============
Policy Presets
==============

.. versionadded:: 1.1.0

Ready-made configurations for common backends. Each preset returns a config
dict with composable ``wait``, ``stop``, ``retry_if`` and ``timeout``.


Available Presets
=================

.. list-table::
   :header-rows: 1
   :widths: 20 40 40

   * - Preset
     - Use case
     - Key settings
   * - :func:`~tranq.presets.http`
     - HTTP clients
     - Retry 429/5xx, full jitter, timeout 10s
   * - :func:`~tranq.presets.database`
     - SQL databases
     - Conservative retries, timeout 5s
   * - :func:`~tranq.presets.redis`
     - Redis/cache
     - Fast fail, minimal retries, timeout 1s
   * - :func:`~tranq.presets.kafka`
     - Message queues
     - More retries, longer backoff
   * - :func:`~tranq.presets.queue`
     - Generic queues
     - Same as kafka
   * - :func:`~tranq.presets.grpc`
     - gRPC services
     - Random exponential jitter, timeout 15s
   * - :func:`~tranq.presets.llm`
     - LLM APIs
     - Rate limits, Retry-After, timeout 60s


Usage
=====

.. code-block:: python

   from tranq import presets, resilient

   @resilient(**presets.http())
   def fetch_users():
       ...

   @resilient(**presets.database())
   def run_query():
       ...


Override Defaults
=================

.. code-block:: python

   cfg = presets.http()
   cfg["timeout"] = 30.0  # custom timeout
   cfg["stop"] = stop.after_attempt(10)

   @resilient(**cfg)
   def my_call():
       ...


See Also
========

* :doc:`../api/presets`
* :doc:`auto` — automatic preset detection
