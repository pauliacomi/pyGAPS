========
Overview
========

pyGAPS (Python General Adsorption Processing Suite) is a framework for adsorption data analysis written in python 3.

.. start-badges

.. list-table::
    :widths: 10 90
    :stub-columns: 1

    * - status
      - | |status|
        | |commits-since|
    * - docs
      - | |docs|
    * - tests
      - | |travis| |appveyor|
        | |codecov|
        | |requires|
    * - package
      - | |version| |wheel|
        | |supported-versions| |supported-implementations|

.. |status| image:: http://www.repostatus.org/badges/latest/wip.svg
    :target: http://www.repostatus.org/#wip
    :alt: Project Status: WIP – Initial development is in progress, but there has not yet been a stable, usable release suitable for the public.

.. |docs| image:: https://readthedocs.org/projects/pygaps/badge/?style=flat
    :target: https://readthedocs.org/projects/pygaps
    :alt: Documentation Status

.. |travis| image:: https://travis-ci.org/pauliacomi/pyGAPS.svg?branch=master
    :alt: Travis-CI Build Status
    :target: https://travis-ci.org/pauliacomi/pyGAPS

.. |appveyor| image:: https://ci.appveyor.com/api/projects/status/github/pauliacomi/pygaps?branch=master&svg=true
    :alt: AppVeyor Build Status
    :target: https://ci.appveyor.com/project/pauliacomi/pygaps

.. |requires| image:: https://requires.io/github/pauliacomi/pyGAPS/requirements.svg?branch=master
    :alt: Requirements Status
    :target: https://requires.io/github/pauliacomi/pyGAPS/requirements/?branch=master

.. |codecov| image:: https://codecov.io/github/pauliacomi/pygaps/coverage.svg?branch=master
    :alt: Coverage Status
    :target: https://codecov.io/github/pauliacomi/pygaps

.. |version| image:: https://img.shields.io/pypi/v/pygaps.svg
    :alt: PyPI Package latest release
    :target: https://pypi.python.org/pypi/pygaps

.. |commits-since| image:: https://img.shields.io/github/commits-since/pauliacomi/pygaps/v0.1.0.svg
    :alt: Commits since latest release
    :target: https://github.com/pauliacomi/pygaps/compare/v0.1.0...master

.. |wheel| image:: https://img.shields.io/pypi/wheel/pygaps.svg
    :alt: PyPI Wheel
    :target: https://pypi.python.org/pypi/pygaps

.. |supported-versions| image:: https://img.shields.io/pypi/pyversions/pygaps.svg
    :alt: Supported versions
    :target: https://pypi.python.org/pypi/pygaps

.. |supported-implementations| image:: https://img.shields.io/pypi/implementation/pygaps.svg
    :alt: Supported implementations
    :target: https://pypi.python.org/pypi/pygaps


.. end-badges

Work in progress

* Free software: MIT license

Features
========

    - Routine analysis such as BET surface area, t-plot, alpha-s method
    - Pore size distribution calculations for mesopores (BJH, Dollimore-Heal)
    - Pore size distribution calculations for micropores (Horowitz-Kawazoe)
    - Pore size distribution calculations using DFT kernels
    - Isotherm modelling (Henry, Langmuir, DS/TS Langmuir, etc..)
    - IAST predictions for binary adsorption
    - Isosteric heat of adsorption calculation
    - Parsing to and from multiple formats such as Excel, CSV and JSON
    - An sqlite database backend for storing and retrieving data
    - Simple methods for isotherm graphing and comparison

Documentation
=============

For more info, as well as a complete manual and reference visit:

https://pygaps.readthedocs.io/


Installation
============

The easiest way to install pyGAPS is from the command line.
::

    pip install pygaps

On Windows, Anaconda is your best bet since it manages environments for you.
First install the suite and then use pip inside your regular python 3 environment.


Development
===========

If you have all the python environments needed to run the entire test suite,
use tox. To run the all tests run::

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

For testing only with the environment you are currently on, run pytest instead::

    py.test --cov

Alternatively, depend travisCI for the testing, which will be slower overall.
