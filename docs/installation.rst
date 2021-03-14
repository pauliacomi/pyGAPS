============
Installation
============

Command line
============

The installation process should take care of the dependencies for you.
If using pip all you need to do is::

    pip install pygaps

We recommend using the `Anaconda/Conda <https://www.anaconda.com/>`__ environment,
as it preinstalls most required dependencies as well as making
managing environments a breeze.

.. code-block:: bash

    conda create -n py3 python=3 numpy scipy pandas matplotlib CoolProp
    conda activate py3
    pip install pygaps

Alternatively, to install the development branch,
clone the repository from Github. Then install the package,
either in regular or developer mode

.. code-block:: bash

    git clone https://github.com/pauliacomi/pyGAPS

    # then install
    pip install pyGAPS/

    # alternatively in developer mode
    pip install -e pyGAPS/

Dependencies
============

The main packages that pyGAPS depends on are

    - Common data science packages: `numpy`, `scipy`, `pandas` and `matplotlib`.
    - The `CoolProp <http://www.coolprop.org/>`__ backend for physical
      properties calculation (can also be connected to
      `REFPROP <https://www.nist.gov/srd/refprop>`__ if locally available).
    - The `xlrd` and `xlwt` packages for parsing to and from Excel files.
    - The `requests` package for communicating with the NIST ISODB.

The `pyIAST <https://github.com/CorySimon/pyIAST>`__ package used to be a
required dependency, but has since been integrated in the pyGAPS framework. More
info about pyIAST can be found in the manuscript:

 \C. Simon, B. Smit, M. Haranczyk. pyIAST: Ideal Adsorbed Solution
 Theory (IAST) Python Package. Computer Physics Communications. (2015)

