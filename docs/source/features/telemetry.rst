.. _feature-telemetry:

========================
OpenTelemetry Integration
========================

.. versionadded:: 1.1.0

Emit spans, counters and events automatically. Degrades gracefully when
OpenTelemetry is not installed.


Basic Usage
===========

.. code-block:: python

   from tranq import telemetry

   @telemetry(service="payment")
   def process_payment():
       ...

Every call is wrapped in a span named after the function.


What Gets Emitted
=================

.. list-table::
   :header-rows: 1
   :widths: 30 70

   * - Signal
     - Content
   * - **Span**
     - One per function call, named ``<func_name>``
   * - **Counter**
     - ``tranq.events`` with labels ``service``, ``event``
   * - **Attributes**
     - All event data is attached as attributes


Install the Extra
=================

.. code-block:: bash

   pip install tranq[telemetry]

Without the extra, :class:`~tranq.Telemetry` becomes a silent no-op —
no code changes needed.


Wire into PolicyBuilder
=======================

.. code-block:: python

   policy = (
       PolicyBuilder()
       .retry(max_attempts=3)
       .observe(telemetry=True, service="payment")
   )


See Also
========

* :doc:`../api/telemetry`
* :doc:`events` — event bus for in-process subscribers
