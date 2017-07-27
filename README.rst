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

.. |docs| image:: https://readthedocs.org/projects/adsorpy/badge/?style=flat
    :target: https://readthedocs.org/projects/adsorpy
    :alt: Documentation Status

.. |travis| image:: https://travis-ci.org/pauliacomi/adsorpy.svg?branch=master
    :alt: Travis-CI Build Status
    :target: https://travis-ci.org/pauliacomi/adsorpy

.. |appveyor| image:: https://ci.appveyor.com/api/projects/status/github/pauliacomi/adsorpy?branch=master&svg=true
    :alt: AppVeyor Build Status
    :target: https://ci.appveyor.com/project/pauliacomi/adsorpy

.. |requires| image:: https://requires.io/github/pauliacomi/adsorpy/requirements.svg?branch=master
    :alt: Requirements Status
    :target: https://requires.io/github/pauliacomi/adsorpy/requirements/?branch=master

.. |codecov| image:: https://codecov.io/github/pauliacomi/adsorpy/coverage.svg?branch=master
    :alt: Coverage Status
    :target: https://codecov.io/github/pauliacomi/adsorpy

.. |version| image:: https://img.shields.io/pypi/v/adsorpy.svg
    :alt: PyPI Package latest release
    :target: https://pypi.python.org/pypi/adsorpy

.. |commits-since| image:: https://img.shields.io/github/commits-since/pauliacomi/adsorpy/v0.1.0.svg
    :alt: Commits since latest release
    :target: https://github.com/pauliacomi/adsorpy/compare/v0.1.0...master

.. |wheel| image:: https://img.shields.io/pypi/wheel/adsorpy.svg
    :alt: PyPI Wheel
    :target: https://pypi.python.org/pypi/adsorpy

.. |supported-versions| image:: https://img.shields.io/pypi/pyversions/adsorpy.svg
    :alt: Supported versions
    :target: https://pypi.python.org/pypi/adsorpy

.. |supported-implementations| image:: https://img.shields.io/pypi/implementation/adsorpy.svg
    :alt: Supported implementations
    :target: https://pypi.python.org/pypi/adsorpy


.. end-badges

An example package. Generated with cookiecutter-pylibrary.

* Free software: MIT license

Installation
============

::

    pip install adsorpy

Documentation
=============

https://adsorpy.readthedocs.io/

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
