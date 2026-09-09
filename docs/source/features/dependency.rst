.. _feature-dependency:

=========================
Dependency-Aware Resilience
=========================

.. versionadded:: 1.1.0

Track the health of named dependencies (databases, caches, services) and
aggregate service health.


Graph Setup
===========

.. code-block:: python

   from tranq import DependencyGraph

   graph = DependencyGraph()
   graph.register("api", dependencies=["postgres", "redis", "payment"])
   graph.register("worker", dependencies=["postgres", "kafka"])


Record Outcomes
===============

.. code-block:: python

   # After each call to a dependency
   graph.record("payment", success=True)
   graph.record("postgres", success=False)


Query Health
============

.. code-block:: python

   print(graph.health("payment"))   # "HEALTHY", "DEGRADED", "UNHEALTHY", "UNKNOWN"
   print(graph.all_health())        # dict of all dependencies


Find Failing Dependencies
==========================

.. code-block:: python

   failing = graph.failing_dependencies("api")
   # ["payment"] if payment is unhealthy

Use this to decide whether to invoke a fallback or serve cached data.


Render Report
=============

.. code-block:: python

   print(graph.render())

Sample output:

.. code-block:: text

   DEPENDENCY HEALTH
   ────────────────────────────────
   postgres             HEALTHY
   redis                HEALTHY
   payment              UNHEALTHY
   kafka                HEALTHY


See Also
========

* :doc:`../api/dependency`
* :doc:`diagnostics` — service-level health
