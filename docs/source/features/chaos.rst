.. _feature-chaos:

==============
Chaos Testing
==============

.. versionadded:: 1.1.0

Inject latency, errors and timeouts into your tests to validate resilience.


Basic Usage
===========

.. code-block:: python

   from tranq import chaos

   with chaos(latency=0.3, error_rate=0.2, timeout_rate=0.1) as inj:
       for _ in range(100):
           inj.maybe_inject()
           call_service()


Injectable Chaos
================

.. list-table::
   :header-rows: 1
   :widths: 30 70

   * - Parameter
     - Effect
   * - ``latency``
     - Sleep this many seconds on every inject
   * - ``error_rate``
     - Probability of raising ``error_type``
   * - ``timeout_rate``
     - Probability of raising :class:`TimeoutError`
   * - ``error_type``
     - Exception class to raise (default :class:`RuntimeError`)
   * - ``seed``
     - Reproducibility seed


Decorator Form
==============

.. code-block:: python

   from tranq import chaos, ChaosInjector, chaos_wrapped

   cfg = chaos(error_rate=0.5)
   # inject manually
   with cfg as inj:
       decorated = chaos_wrapped(inj)(my_function)


Reports
=======

Every chaos session produces a report:

.. code-block:: python

   from tranq import chaos_report, reset_chaos_reports

   reset_chaos_reports()

   with chaos(...) as inj:
       ...

   print(chaos_report())
   # [{"latency": 100, "errors": 47, "timeouts": 12, "clean": 41}]


See Also
========

* :doc:`../api/chaos`
* :doc:`testing` — integration with pytest
