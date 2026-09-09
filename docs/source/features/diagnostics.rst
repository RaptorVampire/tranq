.. _feature-diagnostics:

===========
Diagnostics
===========

.. versionadded:: 1.1.0

Automated health analysis with recommended actions.


Render Diagnostics
==================

.. code-block:: python

   from tranq import render_diagnostics

   print(render_diagnostics())

Sample output:

.. code-block:: text

   SERVICE HEALTH
   ────────────────────────────────
   API                  HEALTHY   (calls=500, err_rate=0.002)
   Payment              DEGRADED  (calls=200, err_rate=0.080)
   Redis                HEALTHY   (calls=1000, err_rate=0.001)

   Overall: DEGRADED  (calls=1700, errors=18)

   CIRCUIT STATES
     payment_cb: open

   Recommended actions:
     - Enable jitter to avoid thundering herds
     - A circuit breaker is open; investigate downstream


Structured Output
=================

.. code-block:: python

   from tranq import diagnostics

   d = diagnostics()
   # {
   #   "services": {"API": {"status": "HEALTHY", ...}, ...},
   #   "overall": {"status": "DEGRADED", "calls": 1700, "errors": 18, "error_rate": 0.011},
   #   "circuit_states": {"payment_cb": "open"},
   #   "recommended_actions": ["Enable jitter to avoid thundering herds", ...],
   # }


Health Thresholds
=================

.. list-table::
   :header-rows: 1
   :widths: 30 70

   * - Error Rate
     - Status
   * - < 1%
     - ``HEALTHY``
   * - 1% – 10%
     - ``DEGRADED``
   * - > 10%
     - ``UNHEALTHY``


See Also
========

* :doc:`../api/diagnostics`
* :doc:`adaptive` — adaptive tuning
