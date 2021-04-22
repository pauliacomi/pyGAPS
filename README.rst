========
Overview
========

pyGAPS (Python General Adsorption Processing Suite) is a framework for
adsorption data analysis and fitting, written in Python 3.

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
      - | |GHA| |travis|
        | |codecov|
        | |requires|
    * - package
      - | |version| |wheel|
        | |supported-versions| |supported-implementations|

.. |status| image:: https://www.repostatus.org/badges/latest/active.svg
    :target: https://www.repostatus.org/#active
    :alt: Project Status: Active – The project has reached a stable, usable state and is being actively developed.

.. |commits-since| image:: https://img.shields.io/github/commits-since/pauliacomi/pygaps/v3.1.0/develop.svg
    :alt: Commits since latest release
    :target: https://github.com/pauliacomi/pygaps/compare/v3.1.0...develop

.. |docs| image:: https://readthedocs.org/projects/pygaps/badge/?style=flat
    :target: https://readthedocs.org/projects/pygaps
    :alt: Documentation Status

.. |license| image:: https://img.shields.io/badge/License-MIT-yellow.svg
    :target: https://opensource.org/licenses/MIT
    :alt: Project License

.. |GHA| image:: https://github.com/pauliacomi/pyGAPS/workflows/CI/badge.svg
    :alt: GHA-CI Build Status
    :target: https://github.com/pauliacomi/pyGAPS/actions

.. |travis| image:: https://api.travis-ci.org/pauliacomi/pyGAPS.svg?branch=master
    :alt: Travis-CI Build Status
    :target: https://travis-ci.org/pauliacomi/pyGAPS

.. |requires| image:: https://requires.io/github/pauliacomi/pyGAPS/requirements.svg?branch=master
    :alt: Requirements Status
    :target: https://requires.io/github/pauliacomi/pyGAPS/requirements/?branch=master

.. |codecov| image:: https://img.shields.io/codecov/c/github/pauliacomi/pygaps.svg
    :alt: Coverage Status
    :target: https://codecov.io/gh/pauliacomi/pyGAPS

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

    - Advanced adsorption data import and manipulation.
    - Routine analysis such as BET/Langmuir surface area, t-plot, alpha-s,
      Dubinin plots etc.
    - Pore size distribution calculations for mesopores (BJH, Dollimore-Heal).
    - Pore size distribution calculations for micropores (Horvath-Kawazoe).
    - Pore size distribution calculations using DFT kernels
    - Isotherm model fitting (Henry, Langmuir, DS/TS Langmuir, etc..)
    - Isosteric enthalpy of adsorption calculation.
    - IAST calculations for binary and multicomponent adsorption.
    - Parsing to and from multiple formats such as Excel, CSV and JSON.
    - An sqlite database backend for storing and retrieving data.
    - Simple methods for isotherm graphing and comparison.

Documentation
=============

pyGAPS is built with three key mantras in mind:

    - **opinionated**: There are many places where the code will suggest or
      default to what the it considers a good practice. As examples: the
      standard units, pore size distribution methods and BET calculation limits.
    - **flexible**: While the defaults are there for a reason, you can override
      pretty much any parameter. Want to pass a custom adsorbate thickness
      function or use volumetric bases? Can do!
    - **transparency**: All code is well documented and open source. There are
      no black boxes.

In-depth explanations, examples and theory can be found in the
`online documentation <https://pygaps.readthedocs.io/>`__. If you are familiar
with Python and adsorption theory and want to jump right in, look at the
`quickstart section
<https://pygaps.readthedocs.io/en/master/examples/quickstart.html>`__. Examples
on each of the capabilities specified above can be found in the
`examples <https://pygaps.readthedocs.io/en/master/examples/index.html>`__. Most
of the pages in the documentation are actually Jupyter Notebooks. You can
download them and run them yourself from the
`/docs/examples <https://github.com/pauliacomi/pyGAPS/tree/master/docs/examples>`__
folder.

To become well familiarised with the concepts introduced by pyGAPS, such as what
is an Isotherm, how units work, what data is required and can be stored etc., a
deep dive is available in the
`manual <https://pygaps.readthedocs.io/en/master/manual/index.html>`__.

Finally, having a strong grasp of the science of adsorption is recommended, to
understand the strengths and shortcomings of various methods. We have done our
best to explain the theory and application range of each capability and model.
To learn more, look at the
`reference <https://pygaps.readthedocs.io/en/master/reference/index.html>`__ or
simply call ``help()`` from a python interpreter (for example
``help(pygaps.area_BET)``.

Citing
======

Please consider citing the related paper we published if you use
the program in your research.

    Paul Iacomi, Philip L. Llewellyn, *Adsorption* (2019).
    pyGAPS: A Python-Based Framework for Adsorption Isotherm
    Processing and Material Characterisation.
    DOI: https://doi.org/10.1007/s10450-019-00168-5

Installation
============

The easiest way to install pyGAPS is from the command line.
Make sure that you have ``numpy``, ``scipy``, ``pandas`` and ``matplotlib``,
as well as ``CoolProp`` already installed.

.. code-block:: bash

    pip install pygaps

`Anaconda/Conda <https://www.anaconda.com/>`__ is your best bet since it manages
environments for you. First create a new environment and use conda to
install the dependencies (or start with one that already has a full
instalation). Then use pip inside your environment.

.. code-block:: bash

    conda create -n myenv python=3 numpy scipy pandas matplotlib
    conda activate myenv
    pip install pygaps

To install the development branch, clone the repository from GitHub.
Then install the package with pip either in regular or developer mode.

.. code-block:: bash

    git clone https://github.com/pauliacomi/pyGAPS

    # then install
    pip install pyGAPS/

    # or developer mode
    pip install -e pyGAPS/

Development
===========

If you want to contribute to pyGAPS or develop your own code from the package,
check out the detailed information in CONTRIBUTING.rst.

Bugs or questions?
==================

For any bugs found, please open an
`issue <https://github.com/pauliacomi/pyGAPS/issues/>`__ or, even better, submit
a `pull request <https://github.com/pauliacomi/pyGAPS/pulls/>`__. It'll make my
life easier. This also applies to any features which you think might benefit the
project. I'm also more than happy to answer any questions. Shoot an email to
mail( at )pauliacomi.com or find me at https://pauliacomi.com or on
`Twitter <https://twitter.com/iacomip>`__.
