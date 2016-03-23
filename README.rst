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

Currently this package requires git, psql, pg_dump createdb, dropdb and unzip to function.

::

    pip install django-devfixtures

Configuration
=============

Add **devfixtures** to **INSTALLED_APPS**.

::

    settings.DEVFIXTURE_DIR         # path to directory where auto generated fixtures should be stored
    settings.DEVFIXTURE_BACKUP_DIR  # path to where backups are stored when running restore


How it works
============

When you **create** a fixture (without any arguments) the management command will zip MEDIA_FILES and database dump to
a file with naming <AUTHOR_DATE>+<COMMITID>+<CREATED_DATE>+<CREATOR>.zip.

The auto restore function will check from HEAD and backards in the commit tree, and when it finds a fixture file with
that commit id, it will restore that version after a backup of the current state has been created. If the restore for
some reason fails, it will attempt to restore the backuped fixture.

This works with the following criterias:

* You will not rebase/rewrite history, as commit ids might no longer match
* You will not delete migrations manually

It also have the limitations to unly work with PostgreSQL. And there are some current limitations, due to the fact
that the implementation uses pg_dump etc for creating dumps. Requirements:

* The database name is defined in **settings.DATABASES['default']['NAME']**
* The running user have permissions to dropdb/createdb


Storing the dev_fixtures in git
===============================

Devfixtures can become large, if you have big set of media files. If you use github, you are encouraged to use git-lfs
to store the files. Read about git lfs here: https://git-lfs.github.com/

Add devfixtures/* to your tracked git lfs files before you add your first fixture to git.

::

    # git lfs track 'dev_fixtures/*'


Usage
=====

Create fixture:

::

    # ./manage.py devfixture create

Restore fixture:

::

    # ./manage.py devfixture restore

Create manual fixture sharing, for example if you have a branch and you want some other developer to take a look
at a bug. Run this and send the zip file to the other developer:

::

    # ./manage.py devfixture create -f ~/Desktop/devfixture-for-peter-debugging.zip

To load a shared fixture:

::

    # ./manage.py devfixture restore -f ~/Desktop/devfixture-for-peter-debugging.zip

When running restore, a backup is always created. You can restore it the same way as above.

::

    # ./manage.py devfixture -h


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
