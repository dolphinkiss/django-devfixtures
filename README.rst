========
Overview
========

.. start-badges

.. list-table::
    :stub-columns: 1

    * - docs
      - |docs|
    * - tests
      - | |travis|
        | |codecov|
    * - package
      - |version| |downloads| |wheel| |supported-versions| |supported-implementations|

.. |docs| image:: https://readthedocs.org/projects/django-devfixtures/badge/?style=flat
    :target: https://readthedocs.org/projects/django-devfixtures
    :alt: Documentation Status

.. |travis| image:: https://travis-ci.org/dolphinkiss/django-devfixtures.svg?branch=master
    :alt: Travis-CI Build Status
    :target: https://travis-ci.org/dolphinkiss/django-devfixtures

.. |codecov| image:: https://codecov.io/github/dolphinkiss/django-devfixtures/coverage.svg?branch=master
    :alt: Coverage Status
    :target: https://codecov.io/github/dolphinkiss/django-devfixtures

.. |version| image:: https://img.shields.io/pypi/v/django-devfixtures.svg?style=flat
    :alt: PyPI Package latest release
    :target: https://pypi.python.org/pypi/django-devfixtures

.. |downloads| image:: https://img.shields.io/pypi/dm/django-devfixtures.svg?style=flat
    :alt: PyPI Package monthly downloads
    :target: https://pypi.python.org/pypi/django-devfixtures

.. |wheel| image:: https://img.shields.io/pypi/wheel/django-devfixtures.svg?style=flat
    :alt: PyPI Wheel
    :target: https://pypi.python.org/pypi/django-devfixtures

.. |supported-versions| image:: https://img.shields.io/pypi/pyversions/django-devfixtures.svg?style=flat
    :alt: Supported versions
    :target: https://pypi.python.org/pypi/django-devfixtures

.. |supported-implementations| image:: https://img.shields.io/pypi/implementation/django-devfixtures.svg?style=flat
    :alt: Supported implementations
    :target: https://pypi.python.org/pypi/django-devfixtures


.. end-badges

Share development fixtures across your team, with git commit id tracing and autodetect.

* Free software: BSD license

Installation
============

::

    pip install django-devfixtures

Documentation
=============

https://django-devfixtures.readthedocs.org/

Development
===========

To run the all tests run::

    tox

Note, to combine the coverage data from all the tox environments run:

.. list-table::
    :widths: 10 90
    :stub-columns: 1

    - - Windows
      - ::

            set PYTEST_ADDOPTS=--cov-append
            tox

    - - Other
      - ::

            PYTEST_ADDOPTS=--cov-append tox
