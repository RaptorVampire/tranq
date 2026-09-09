.. _feature-timeout:

========
Timeouts
========

tranq supports **per-attempt**, **total-operation** and **deadline-propagated**
timeouts for both sync and async code.


Per-Attempt Timeout
===================

The simplest form: fail a single call if it takes too long.

.. code-block:: python

   @tranq.handle(on=Exception, retry=2, timeout=5.0)
   def slow_operation():
       ...

If the function does not return within 5 seconds,
:class:`~tranq.FunctionTimeoutError` is raised (which is also a
:class:`TimeoutError`, so ``on=TimeoutError`` catches it).


Implementation Details
----------------------

* **Sync functions**: executed in a worker thread via
  :class:`concurrent.futures.ThreadPoolExecutor`. The calling thread returns
  immediately on timeout.
* **Async functions**: uses :func:`asyncio.wait_for`, which cooperatively
  cancels the task.

.. warning::

   For sync functions, the worker thread continues running in the background
   after timeout. This is a fundamental limitation of thread-based timeouts
   in Python. For critical use-cases, prefer async functions where
   cancellation is cooperative.


Deadline Propagation
====================

.. versionadded:: 1.1.0

Use :class:`~tranq.Deadline` to propagate an overall deadline across nested
calls:

.. code-block:: python

   from tranq import Deadline, DeadlineExceededError

   deadline = Deadline(seconds=30.0)

   def outer():
       inner(deadline.remaining())
       deadline.remaining()  # shrinks as work proceeds
       if deadline.expired():
           raise DeadlineExceededError("out of time")

   def inner(timeout):
       # each nested call uses a shrinking timeout
       ...


Combining with Stop Conditions
==============================

.. code-block:: python

   from tranq import stop

   policy = (
       tranq.PolicyBuilder()
       .retry(max_attempts=10, stop=stop.before_deadline(deadline=60.0))
       .timeout(5.0)
   )

   @policy
   def operation():
       ...


See Also
========

* :doc:`../api/primitives` — :class:`~tranq.Deadline`
* :doc:`retry` — :func:`~tranq.stop.before_deadline`
