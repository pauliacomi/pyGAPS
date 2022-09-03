============
Installation
============

pyGAPS is made for modern versions of Python, currently requiring at least Python 3.7.

Command line
============

The installation process should take care of the dependencies for you.
If using ``pip`` all you need to do is::

    pip install pygaps

We recommend using the `Anaconda/Conda <https://www.anaconda.com/>`__ environment,
as it preinstalls most required dependencies as well as making
managing environments a breeze. To create a new environment with pyGAPS:

.. code-block:: bash

    conda create -n myenv python=3.8
    conda activate myenv
    conda install pygaps

To install the development branch, clone the repository from Github. Then
install the package, in regular or editable mode

.. code-block:: bash

    git clone https://github.com/pauliacomi/pyGAPS

    # then install
    pip install ./pyGAPS

    # alternatively in developer mode
    pip install -e ./pyGAPS

Dependencies
============

The main packages that pyGAPS depends on are

- The common data science packages: `numpy <https://numpy.org>`__,
  `scipy <https://scipy.org>`__, `pandas <https://pandas.pydata.org/>`__ and
  `matplotlib <https://matplotlib.org/>`__.
- The `CoolProp <http://www.coolprop.org/>`__ backend for physical
  properties calculation (can also be connected to
  `REFPROP <https://www.nist.gov/srd/refprop>`__ if locally available).
- `gemmi` for parsing AIF files.
- `xlrd`, `xlwt`, `openpyxl` for parsing to and from Excel files.
- `requests`, for communicating with the NIST ISODB.

The `pyIAST <https://github.com/CorySimon/pyIAST>`__ package used to be a
required dependency, but has since been integrated in the pyGAPS framework. More
info about pyIAST can be found in the manuscript:

 \C. Simon, B. Smit, M. Haranczyk. pyIAST: Ideal Adsorbed Solution
 Theory (IAST) Python Package. Computer Physics Communications. (2015)

