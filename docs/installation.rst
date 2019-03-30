============
Installation
============

Command line
============

The installation process should take care of the dependencies for you. If using pip all
you need to do is at the command line::

    pip install pygaps

If on windows, we recommend using the `Anaconda/Conda <https://www.anaconda.com/>`__ environment,
as it preinstalls most required dependencies as well as making managing environments a breeze.

Alternatively, to install the development branch, clone the repository from Github.
Then install the package, either in regular or developer mode

::

    git clone https://github.com/pauliacomi/pyGAPS

    // then install

    pip install ./              # pip
    python setup.py install     # setuptools

    // or developer mode

    pip install -e ./           # pip
    python setup.py develop     # setuptools

Dependencies
============

The main packages that pyGAPS depends on are

    - The common data science packages `numpy`, `scipy`, `pandas` and `matplotlib`.
    - The `CoolProp <http://www.coolprop.org/>`__ backend for physical properties calculation
      (can also be connected to `REFPROP <https://www.nist.gov/srd/refprop>`__ if locally available).
    - The `xlrd` and `xlwt` packages for parsing to and from Excel files.

The `pyIAST <https://github.com/CorySimon/pyIAST>`__ package used to be a required dependency, but
has since been integrated in the pyGAPS framework. More info about pyIAST can be found at:

 \C. Simon, B. Smit, M. Haranczyk. pyIAST: Ideal Adsorbed Solution Theory (IAST) Python Package. Computer Physics Communications. (2015)

