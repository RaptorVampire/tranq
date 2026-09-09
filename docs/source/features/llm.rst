.. _feature-llm:

================
LLM Resilience
================

.. versionadded:: 1.1.0

LLM APIs have unique resilience requirements: rate limits, Retry-After
headers, provider fallbacks, long timeouts, and token budgets. tranq's
``@llm`` decorator handles all of them.


Basic Usage
===========

.. code-block:: python

   from tranq import llm

   @llm(max_attempts=5, timeout=60.0)
   async def ask(prompt):
       return await openai_client.complete(prompt)


Provider Failover
=================

Provide an ordered list of alternative providers:

.. code-block:: python

   @llm(
       max_attempts=2,
       providers=[anthropic_client, local_model, cache],
   )
   async def ask(prompt):
       return await primary_client.complete(prompt)

If the primary fails repeatedly, each provider is tried in sequence.


Built-In Behavior
=================

The ``@llm`` decorator automatically:

* Uses the ``llm`` preset (rate-limit + Retry-After aware)
* Honors ``Retry-After`` and ``X-RateLimit-Reset`` headers
* Retries on 429, 500, 502, 503
* Applies jittered exponential backoff with 60s cap
* Times out at 60 seconds per attempt
* Falls back through the provider chain


See Also
========

* :doc:`../api/llm`
* :doc:`presets` — the ``llm`` preset
* :doc:`fallback` — FallbackChain for provider failover
