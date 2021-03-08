.. _iast-manual:

Ideal Adsorbed Solution Theory
==============================

.. _iast-manual-general:

Overview
--------

By using the Ideal Adsorbed Solution Theory (IAST), the adsorption behaviour of
gas mixtures can be predicted from pure component isotherms.

The main IAST code was written by Cory Simon [#]_, and was then incorporated in
pyGAPS. A very good explanation of the method, complete with use cases and
recommendations can still be found on the pyIAST
`documentation <https://pyiast.readthedocs.io/en/latest/>`__

With the inclusion of the source code, several changes have been introduced, to
improve the usability of the method and to conform it to the rest of the code. A
tutorial of IAST within pyGAPS follows.

.. [#] C. Simon, B. Smit, M. Haranczyk. pyIAST: Ideal Adsorbed Solution Theory (IAST) Python Package. Computer Physics Communications. (2015)


.. _iast-manual-tutorial:

IAST calculations in pyGAPS
---------------------------

To use the IAST functionality, a list of pure component isotherms is needed. The
isotherms can be either:

    - A ModelIsotherm class, where the model will be used for the calculation of
      spreading pressure. Some models cannot be used for IAST calculations.
    - A PointIsotherm class, where the spreading pressure calculation will use
      interpolated data.

The original pyIAST functions still exist, as
:func:`~pygaps.iast.iast.iast` and
:func:`~pygaps.iast.iast.reverse_iast`. They can be used to
determine the adsorbed fraction of each adsorbate given their partial pressures,
or vice-versa.

To use:

::

    isotherms = [iso1, iso2, iso3]
    mole_fractions = [0.1, 0.4, 0.5]
    total_pressure = 2

    iast_loadings = pygaps.iast(isotherms, mole_fractions, total_pressure)


Since IAST is often used for binary mixture adsorption prediction, several new
functions have been introduced which make it easier to do common calculations
and generate graphs:

    - :func:`~pygaps.iast.iast.iast_binary_svp` is a function to
      calculate the selectivity of a known composition mixture as a function of
      pressure.

      For example, this will plot selectivities over a pressure range of 0.01 to
      10 of an equimolar mixture of methane and ethane:

      ::

        import numpy
        import matplotlib.pyplot as plt

        partial_pressures = [0.5, 0.5]
        pressure_range = numpy.linspace(0.01, 10, 30)

        result_dict = pygaps.iast_binary_svp(
            [ch4, c2h6], partial_pressures, pressure_range, verbose=True,
        )

    - :func:`~pygaps.iast.iast.iast_binary_vle` is a function to
      calculate the gas-adsorbed equilibrium at a constant pressure, over the
      entire range of molar fractions.

      For example, this will plot the gas-adsorbed equilibrium for all molar
      fractions of methane in ethane at a pressure of 2 bar:

      ::

        import matplotlib.pyplot as plt

        result_dict = pygaps.iast_binary_vle([ch4, c2h6], 2, verbose=True)



.. _iast-manual-examples:

IAST example
------------

Check it out in the Jupyter notebook in the `examples <../examples/iast.ipynb>`_
section for a demonstration.
