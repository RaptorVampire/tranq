.. _contributing:

============
Contributing
============

Contributions are welcome! This page explains how to contribute to tranq.


Development Setup
=================

.. code-block:: bash

   git clone https://github.com/RaptorVampire/tranq.git
   cd tranq
   pip install -e ".[dev]"


Run Tests
=========

.. code-block:: bash

   pytest tests/ -v


Build Documentation
===================

.. code-block:: bash

   cd docs
   pip install -r requirements.txt
   make html

Open ``docs/build/html/index.html`` in your browser.


Code Style
==========

* Use `Black <https://github.com/psf/black>`_ for formatting
* Use `isort <https://github.com/PyCQA/isort>`_ for imports

.. code-block:: bash

   black src/ tests/
   isort src/ tests/


Pull Request Process
====================

1. Fork the repo and create a branch from ``main``.
2. Add tests for any new functionality.
3. Update documentation for any API changes.
4. Ensure ``pytest tests/`` passes.
5. Run ``black`` and ``isort``.
6. Open a pull request.


Reporting Bugs
==============

Open an issue on `GitHub <https://github.com/RaptorVampire/tranq/issues>`_
with:

* A clear description of the bug
* Steps to reproduce
* Expected vs actual behavior
* Python version and tranq version
* Minimal reproducible example (if possible)


License
=======

By contributing, you agree that your contributions will be licensed under the
MIT License.
