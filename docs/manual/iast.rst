.. _iast-manual:

Ideal Adsorbed Solution Theory
==============================

.. _iast-manual-general:

Overview
--------

Adsorption behaviours of gas mixtures can be predicted from pure component
isotherms by using the Ideal Adsorbed Solution Theory (IAST).

The main IAST code was written by Cory Simon [#]_, and was then incorporated in
pyGAPS. A very good explanation of the method, complete with use cases and
recommendations can still be found on the pyIAST
`documentation <https://pyiast.readthedocs.io/en/latest/>`__

With the inclusion of the source code, several changes have been introduced, to
improve the usability of the method and to conform it to the rest of the code. A
tutorial of IAST within pyGAPS follows.

.. [#] C. Simon, B. Smit, M. Haranczyk. pyIAST: Ideal Adsorbed Solution Theory
   (IAST) Python Package. Computer Physics Communications. (2015)


.. _iast-manual-tutorial:

IAST calculations in pyGAPS
---------------------------

To use the IAST functionality, a list of pure component isotherms is needed. The
isotherms can be either:

- A :class:`~pygaps.core.modelisotherm.ModelIsotherm`, where the model will be
  used for the calculation of spreading pressure. Some models cannot be used for
  IAST calculations.
- A :class:`~pygaps.core.pointisotherm.PointIsotherm`, where the spreading
  pressure calculation will use interpolated data.

The original pyIAST functions still exist, as
:func:`~pygaps.iast.pgiast.iast_point` and
:func:`~pygaps.iast.pgiast.reverse_iast`. They can be used to
determine the adsorbed fraction of each adsorbate given their partial pressures,
or vice-versa.

To use:

.. code:: python

    import pygaps.iast as pgi
    iast_loadings = pgi.iast_point(
        isotherms=[iso1, iso2, iso3],
        partial_pressures=[0.1, 1.0, 2.3],
    )

Since IAST is often used for binary mixture adsorption prediction, several new
functions have been introduced which make it easier to do common calculations
and generate graphs:

- :func:`~pygaps.iast.pgiast.iast_point_fraction` is a version of IAST requiring
  bulk fluid fractions and total pressure instead of partial pressures for each
  component.

  .. code:: python

      import pygaps.iast as pgi

      result_dict = pgi.iast_point_fraction(
          isotherms=[iso1, iso2, iso3],
          gas_mole_fraction=[0.1, 0.5, 0.4],
          total_pressure=2,
      )

- :func:`~pygaps.iast.pgiast.iast_binary_svp` is a function to calculate the
  selectivity of a known composition mixture as a function of pressure. This
  example will plot selectivities over a pressure range of 0.01 to 10 of an
  equimolar mixture of methane and ethane:

  .. code:: python

      import numpy
      import pygaps.iast as pgi

      result_dict = pgi.iast_binary_svp(
          isotherms=[ch4, c2h6],
          mole_fractions=[0.5, 0.5],
          pressures=numpy.linspace(0.01, 10, 30),
      )

- :func:`~pygaps.iast.pgiast.iast_binary_vle` is a function to calculate the
  gas-adsorbed equilibrium at a constant pressure, over the entire range of
  molar fractions. This example will plot the gas-adsorbed equilibrium for all
  molar fractions of methane in ethane at a pressure of 2 bar:

  .. code:: python

      import pygaps.iast as pgi

      result_dict = pgi.iast_binary_vle(
          isotherms=[ch4, c2h6],
          total_pressure=2,
      )


.. _iast-manual-examples:

IAST examples
-------------

Check out the Jupyter notebook in the `examples <../examples/iast.ipynb>`_
section for a demonstration.
