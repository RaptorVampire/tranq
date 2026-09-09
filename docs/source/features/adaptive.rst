.. _feature-adaptive:

===================
Adaptive Resilience
===================

.. versionadded:: 1.1.0

Instead of hand-tuning every parameter, let tranq adapt based on observed
signals.


Controller
==========

.. code-block:: python

   from tranq import AdaptiveController

   ctrl = AdaptiveController(
       base_timeout=10.0,
       base_retry=3,
       base_rate=100.0,
       latency_target=0.5,
       error_target=0.05,
   )


Observe Signals
===============

Feed observed data into the controller:

.. code-block:: python

   # After every call
   ctrl.observe(latency=duration, success=(error is None))


Get Recommendations
===================

.. code-block:: python

   rec = ctrl.recommend()
   # {
   #   "timeout": 2.5,
   #   "retry": 1,
   #   "rate_limit": 100.0,
   #   "observed_latency": 2.0,
   #   "observed_error_rate": 0.8,
   # }


Rules
=====

The controller applies these heuristics:

.. list-table::
   :header-rows: 1
   :widths: 30 70

   * - Signal
     - Action
   * - Latency > target
     - Reduce timeout (fail faster)
   * - Error rate > target
     - Reduce retry count (avoid retry storms)
   * - Traffic up
     - (Future: reduce rate limit)


Wire into PolicyBuilder
=======================

.. code-block:: python

   ctrl.apply(policy_builder)  # mutates the builder with recommendations


See Also
========

* :doc:`../api/adaptive`
* :doc:`diagnostics` — health analysis
