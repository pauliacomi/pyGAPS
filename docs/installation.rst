============
Installation
============

The installation process should take care of the dependencies for you. If using pip all
you need to do is at the command line::

    pip install pygaps

If on windows, we reccomend using the `Anaconda/Conda <https://www.anaconda.com/>`__ environment,
as it preinstalls most required dependencies as well as making managing environemts a breeze.

Dependencies
============

The main packages that pyGAPS depends on are

    - The common data science packages `numpy`, `scipy`, `pandas` and `matplotlib`
    - The `CoolProp <http://www.coolprop.org/>`__ backend for physical properties calculation
      (can also be connected to `REFPROP <https://www.nist.gov/srd/refprop>`__ if locally available)
    - The `xlwings <https://www.xlwings.org/>`__ package for parsing to and from Excel files

The `pyIAST <https://github.com/CorySimon/pyIAST>`__ package used to be a required dependency, but
has since been integrated in the pyGAPS framework. More info about pyIAST can be found at

 \C. Simon, B. Smit, M. Haranczyk. pyIAST: Ideal Adsorbed Solution Theory (IAST) Python Package. Computer Physics Communications. (2015)

