.. _units-manual:

Units in pyGAPS
===============

.. _units-manual-general:

Overview
--------

When computers work with physical data, units are always a variable that
introduces confusion. This page attempts to explain how pyGAPS handles units and
other such real world concepts such as relative pressure and mass or volume
basis.

Units can be specified for the following isotherm properties:

- :ref:`Pressure<units-manual-pressure>`.
- :ref:`Adsorbate loading<units-manual-loading>`, or the amount of gas adsorbed.
- :ref:`Material<units-manual-material>`, or the adsorbent on which adsorption takes place.
- :ref:`Temperature<units-manual-temperature>`.

An explanation follows of the concepts follows.


.. _units-manual-pressure:

Pressure
::::::::

Pressure is commonly represented as an absolute value. in units such as *bar*,
*atm*, *Pa*, etc. This is known as the **absolute pressure mode**. You can convert
freely between different units:

.. code:: python

    # convert to torr
    isotherm.convert_pressure(
        unit_to='torr',
    )

Another common option in adsorption is having the pressure represented relative
to the saturation pressure of the adsorbate, or **relative pressure mode**. In
precise terms, relative pressure is a dimensionless value which is obtained by
dividing absolute pressure (:math:`p`) by the saturation / vapour pressure of
the adsorbate at the measurement temperature (:math:`p^0_T`). For its
calculation, pyGAPS uses equations of state from a thermodynamic backend like
CoolProp or REFPROP. More info :ref:`here<eqstate-manual>`.

.. note::

    Relative pressure only has meaning when the isotherm is recorded in a
    sub-critical regime.

Some example isotherm conversions with different pressure modes / units:

.. code:: python

    # relative pressure mode
    isotherm.convert_pressure(
        mode_to='relative',
    )

    # or to relative percent mode
    isotherm.convert_pressure(
        mode_to='relative%',
    )

    # absolute pressure mode
    # unit must be specified here
    isotherm.convert_pressure(
        mode_to='absolute',
        unit_to='torr',
    )

Internally, pressure conversions are handled by the
:func:`~pygaps.units.converter_mode.c_pressure` function.


.. _units-manual-loading:

Adsorbate loading
:::::::::::::::::

Adsorbate loading refers to the quantity of gas (adsorbate) which is contained
in the material on which the isotherm is measured i.e. "moles of nitrogen
adsorbed" or "grams of CO2 captured" or "percent weight adsorbed".

.. note::

    Currently pyGAPS does not differentiate between excess and absolute amount
    adsorbed.

The adsorbate loading is usually given in *mmol* or *cm3(STP)*, both of which
are representations of a **molar basis**. Sometimes it is useful if, instead of
a molar basis, loading is represented in terms on a **mass basis** or **volume
basis**. It is also possible to represent uptake as a **fraction** or
**percent** of the material basis.

For these conversions, properties such as molar mass and density of the
adsorbate are required. This info is obtained automatically using an equation of
state from either CoolProp or REFPROP.

.. note::

    The thermodynamic backends cannot predict properties outside in the critical
    adsorbate regime.

Examples of isotherm conversion on loading:

.. code:: python

    # to a mass basis
    isotherm.convert_loading(
        basis_to='mass',
        unit_to='g',
    )

    # to percentage
    isotherm.convert_loading(
        basis_to='percent',
    )

Internally, loading conversions are handled by the
:func:`~pygaps.units.converter_mode.c_loading` function.


.. _units-manual-material:

Material quantity
:::::::::::::::::

Material quantity refers to the amount of material that the adsorption takes
place on, i.e. amount adsorbed "per gram of carbon" or "per centimetre cube of
zeolite" or "per mole of MOF". The scientific community regularly uses a mass
basis, while a volumetric basis is more important in industry where adsorbent
bed design sizing is required. pyGAPS allows the basis to be changed to either
**mass**, **volume** or **molar**.

Depending on the conversion, the density or molar mass of the material is needed
and should be provided by the user. To specify this in a material see below and,
check out the :ref:`Material <material-manual-general>` manual.

Example of isotherm conversion on material:

.. code:: python

    # must be specified, in g/cm3
    isotherm.material.properties['density'] = 2

    # now conversion is possible
    isotherm.convert_material(
        basis_to='volume',
        unit_to='cm3',
    )


Internally, material conversions are handled by the
:func:`~pygaps.units.converter_mode.c_material`.


.. _units-manual-temperature:

Temperature
:::::::::::

For convenience, isotherm temperatures can also be converted between Kelvin or
Celsius. This is done as:

.. code:: python

    isotherm.convert_temperature(unit_to='°C')


.. _units-manual-impact:

How units impact characterisation and modelling
-----------------------------------------------

Most characterisation methods automatically take the required form of the units
without the user having to convert it beforehand. Therefore, if for example the
:func:`~pygaps.characterisation.area_bet` function is called, the conversion
will be made automatically in order to return the surface area in square metres.

.. warning::

    The basis of the material is unchanged however. Therefore, if the isotherm
    was in a volume basis with units of *cm3* before the calculation above, the
    returned surface area will be in **square meters per cubic centimetre of
    material**.

.. _units-manual-low-level:

Low-level convert
-----------------

The way units are converted under the hood is through the use of dictionaries
that store conversion factors between the different unit types. The user can use
the functions directly by importing the :mod:`pygaps.units.converter_mode`
and :mod:`pygaps.units.converter_unit` modules.

An example pressure conversion:

.. code:: python

    from pygaps.units.converter_mode import c_pressure

    converted = c_pressure(
        1,
        mode_from='absolute',
        unit_from='bar',
        mode_to='absolute',
        unit_to='Pa',
    )


An example loading conversion:

.. code:: python

    from pygaps.units.converter_mode import c_loading

    converted = c_loading(
        1,
        mode_from='molar',
        unit_from='mol',
        mode_to='mass',
        unit_to='mg',
    )

An example material conversion:

.. code:: python

    from pygaps.units.converter_mode import c_material

    converted = c_material(
        1,
        mode_from='mass',
        unit_from='g',
        mode_to='volume',
        unit_to='cm3',
    )



.. _units-manual-high-level:

High-level convert
------------------

In regular usage, the framework handles units for the user, with no need to use
the low-level functions. At :ref:`isotherm creation <isotherms-manual-create>`,
the units can be specified through the use of keywords.

In order to :ref:`access the data <isotherms-manual-data>` in a different unit
than specified at instantiation, most methods can accept the same keywords.

The isotherm internal data can also be permanently converted into another unit,
pressure mode or basis. This is not normally required, but can be done if the
isotherm is to be exported in different units. To do this, check out
:ref:`this section of the manual <isotherms-manual-convert>`.
