========
Overview
========

.. start-badges

.. list-table::
    :stub-columns: 1

    * - docs
      - |docs|
    * - tests
      - | |travis| |appveyor| |requires|
        | |codecov|
    * - package
      - | |version| |wheel| |supported-versions| |supported-implementations|
        | |commits-since|

.. |docs| image:: https://readthedocs.org/projects/adsutils/badge/?style=flat
    :target: https://readthedocs.org/projects/adsutils
    :alt: Documentation Status

.. |travis| image:: https://travis-ci.org/pauliacomi/adsutils.svg?branch=master
    :alt: Travis-CI Build Status
    :target: https://travis-ci.org/pauliacomi/adsutils

.. |appveyor| image:: https://ci.appveyor.com/api/projects/status/github/pauliacomi/adsutils?branch=master&svg=true
    :alt: AppVeyor Build Status
    :target: https://ci.appveyor.com/project/pauliacomi/adsutils

.. |requires| image:: https://requires.io/github/pauliacomi/adsutils/requirements.svg?branch=master
    :alt: Requirements Status
    :target: https://requires.io/github/pauliacomi/adsutils/requirements/?branch=master

.. |codecov| image:: https://codecov.io/github/pauliacomi/adsutils/coverage.svg?branch=master
    :alt: Coverage Status
    :target: https://codecov.io/github/pauliacomi/adsutils

.. |version| image:: https://img.shields.io/pypi/v/adsutils.svg
    :alt: PyPI Package latest release
    :target: https://pypi.python.org/pypi/adsutils

.. |commits-since| image:: https://img.shields.io/github/commits-since/pauliacomi/adsutils/v0.1.0.svg
    :alt: Commits since latest release
    :target: https://github.com/pauliacomi/adsutils/compare/v0.1.0...master

.. |wheel| image:: https://img.shields.io/pypi/wheel/adsutils.svg
    :alt: PyPI Wheel
    :target: https://pypi.python.org/pypi/adsutils

.. |supported-versions| image:: https://img.shields.io/pypi/pyversions/adsutils.svg
    :alt: Supported versions
    :target: https://pypi.python.org/pypi/adsutils

.. |supported-implementations| image:: https://img.shields.io/pypi/implementation/adsutils.svg
    :alt: Supported implementations
    :target: https://pypi.python.org/pypi/adsutils


.. end-badges

An example package. Generated with cookiecutter-pylibrary.

* Free software: MIT license

Installation
============

::

    pip install adsutils

Documentation
=============

https://adsutils.readthedocs.io/

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
