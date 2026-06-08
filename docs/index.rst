Flask CI/CD Demo
================

A small **task-management REST API** built with Flask, used to showcase a
complete GitHub Actions CI/CD pipeline (lint, tests, security, container scan,
docs and automated deployments).

.. note::
   This site is **auto-generated from the source code**. The :doc:`api` page is
   produced directly from the live Flask routing table with
   ``sphinxcontrib-httpdomain`` — every endpoint, parameter and status code you
   see below is read from the running application, never written by hand.

Highlights
----------

- **Application factory** pattern (:func:`app.create_app`) with per-environment config.
- **In-memory** task store — no database, zero setup.
- JSON REST API under ``/api`` plus a ``/health`` probe for deploys.

.. toctree::
   :maxdepth: 2
   :caption: Documentation

   quickstart
   api
   internals

Indices
-------

* :ref:`genindex`
* :ref:`http-routingtable`
* :ref:`modindex`
