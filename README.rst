========
Overview
========

pyGAPS (Python General Adsorption Processing Suite) is a framework for adsorption data analysis written in Python 3.

.. start-badges

.. list-table::
    :widths: 10 90
    :stub-columns: 1

    * - status
      - | |status|
        | |commits-since|
    * - docs
      - | |docs|
    * - license
      - | |license|
    * - tests
      - | |travis| |appveyor|
        | |codecov|
        | |requires|
    * - package
      - | |version| |wheel|
        | |supported-versions| |supported-implementations|

.. |status| image:: https://www.repostatus.org/badges/latest/wip.svg
    :target: https://www.repostatus.org/#wip
    :alt: Project Status: WIP – Initial development is in progress, but there has not yet been a stable, usable release suitable for the public.

.. |commits-since| image:: https://img.shields.io/github/commits-since/pauliacomi/pygaps/v1.5.0.svg
    :alt: Commits since latest release
    :target: https://github.com/pauliacomi/pygaps/compare/v1.5.0...master

.. |docs| image:: https://readthedocs.org/projects/pygaps/badge/?style=flat
    :target: https://readthedocs.org/projects/pygaps
    :alt: Documentation Status

.. |license| image:: https://img.shields.io/badge/License-MIT-yellow.svg
    :target: https://opensource.org/licenses/MIT
    :alt: Project License

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
    :target: https://pypi.org/project/pygaps

.. |wheel| image:: https://img.shields.io/pypi/wheel/pygaps.svg
    :alt: PyPI Wheel
    :target: https://pypi.org/project/pygaps

.. |supported-versions| image:: https://img.shields.io/pypi/pyversions/pygaps.svg
    :alt: Supported versions
    :target: https://pypi.org/project/pygaps

.. |supported-implementations| image:: https://img.shields.io/pypi/implementation/pygaps.svg
    :alt: Supported implementations
    :target: https://pypi.org/project/pygaps


.. end-badges


Features
========

    - Advanced adsorption data import and manipulation
    - Routine analysis such as BET/Langmuir surface area, t-plot, alpha-s, Dubinin plots etc.
    - Pore size distribution calculations for mesopores (BJH, Dollimore-Heal)
    - Pore size distribution calculations for micropores (Horvath-Kawazoe)
    - Pore size distribution calculations using DFT kernels
    - Isotherm model fitting (Henry, Langmuir, DS/TS Langmuir, etc..)
    - IAST calculations for binary and multicomponent adsorption
    - Isosteric heat of adsorption calculations
    - Parsing to and from multiple formats such as Excel, CSV and JSON
    - An sqlite database backend for storing and retrieving data
    - Simple methods for isotherm graphing and comparison

Documentation
=============

For more info, as well as a complete manual and reference visit:

https://pygaps.readthedocs.io/

Most of the examples in the documentation are actually in the form of Jupyter Notebooks
which are turned into webpages with nbsphinx. You can find them for download in:

https://github.com/pauliacomi/pyGAPS/tree/master/docs/examples


Installation
============

The easiest way to install pyGAPS is from the command line.
Make sure that you have `numpy`, `scipy`, `pandas` and `matplotlib`, as well as
CoolProp already installed.

.. code-block:: bash

    pip install pygaps

On Windows, `Anaconda/Conda <https://www.anaconda.com/>`__ is your best bet since it manages
environments for you.
First create a new environment and use conda to install the dependencies (or start with one
that already has a full instalation). Then use pip inside your environment.

.. code-block:: bat

    conda create -n py3 python=3 numpy scipy pandas matplotlib CoolProp
    activate py3
    pip install pygaps

Alternatively, to install the development branch, clone the repository from Github.
Then install the package with pip or setuptools, either in regular or developer mode.

.. code-block:: bash

    git clone https://github.com/pauliacomi/pyGAPS

    // then install

    pip install ./              # pip
    python setup.py install     # setuptools

    // or developer mode

    pip install -e ./           # pip
    python setup.py develop     # setuptools

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

For testing only with the environment you are currently on, run instead

.. code-block:: bash

    python setup.py test

    # or run pytest

    pytest

Alternatively, you can depend on travisCI for the testing, which will be slower overall
but should have all the environments required.

Questions?
==========

I'm more than happy to answer any questions. Shoot me an email at paul.iacomi@univ-amu or find
me on some social media.

For any bugs found, please open an `issue <https://github.com/pauliacomi/pyGAPS/issues/>`__ or, If
you feel like you can do the fix yourself, submit a `pull request <https://github.com/pauliacomi/pyGAPS/pulls/>`__.
It'll make my life easier

This also applies to any features which you think might benefit the project.
