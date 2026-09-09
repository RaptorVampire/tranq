.. _installation:

============
Installation
============

Basic Installation
==================

.. code-block:: bash

   pip install tranq

.. note::

   **tranq** requires **Python 3.9** or later. The core library has
   **zero runtime dependencies** — it will never pull in anything you
   did not ask for.


Optional Extras
===============

tranq integrates with common observability and distribution tools via
optional extras. Install only the ones you need.

.. code-block:: bash

   pip install tranq[rich]         # Colored, formatted logging with Rich
   pip install tranq[sentry]       # Sentry error reporting (sentry-sdk)
   pip install tranq[slack]        # Slack webhook notifications (requests)
   pip install tranq[prometheus]   # Prometheus counters (prometheus-client)
   pip install tranq[redis]        # Distributed state backends (redis)
   pip install tranq[telemetry]    # OpenTelemetry spans + metrics
   pip install tranq[all]          # Everything above
   pip install tranq[dev]          # Development tools

.. list-table:: Extras Reference
   :header-rows: 1
   :widths: 20 40 40

   * - Extra
     - Installs
     - Enables
   * - ``rich``
     - ``rich``
     - Colored, formatted retry logs
   * - ``sentry``
     - ``sentry-sdk``
     - :class:`~tranq.SentryReporter`
   * - ``slack``
     - ``requests``
     - :class:`~tranq.SlackReporter`
   * - ``prometheus``
     - ``prometheus-client``
     - :class:`~tranq.PrometheusReporter`
   * - ``redis``
     - ``redis``
     - :class:`~tranq.RedisBackend` (distributed state)
   * - ``telemetry``
     - ``opentelemetry-api``, ``opentelemetry-sdk``
     - :class:`~tranq.Telemetry` (spans + counters)
   * - ``all``
     - All of the above
     - All integrations at once
   * - ``dev``
     - ``pytest``, ``pytest-asyncio``, ``black``, ``isort``, ``rich``, ``build``, ``twine``
     - Development and testing


Verify Installation
===================

.. code-block:: bash

   python -m tranq
   # Output: tranq v1.1.0 - Calm error handling with advanced resilience features.


Upgrade
=======

.. code-block:: bash

   pip install --upgrade tranq


Uninstall
=========

.. code-block:: bash

   pip uninstall tranq


Source Install
==============

To install the latest development version directly from GitHub:

.. code-block:: bash

   git clone https://github.com/RaptorVampire/tranq.git
   cd tranq
   pip install -e ".[dev]"

Run the test suite to verify:

.. code-block:: bash

   pytest tests/ -v
