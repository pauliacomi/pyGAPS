.. _units-manual:

Units in pyGAPS
===============

.. _units-manual-general:

Overview
--------

When computers work with physical data, units are always
a variable that introduces confusion.
This page attempts to explain how pyGAPS handles
units and other such real world concepts
such as relative pressure and mass or volume basis.

Units can be specified for the following properties:

    - Isotherm pressure
    - Adsorbate loading, or the amount of gas adsorbed
    - Adsorbent quantity, or the amount of material
      on which the adsorption takes place

An explanation follows of the concepts follows.

Pressure
::::::::

For the isotherm pressure, some of the units which can be specified
are: *bar*, *atm*, *Pa*, etc.

Another option is having the pressure represented as *relative pressure*.
In adsorption terms, relative pressure is a dimensionless value
which is obtained by dividing the absolute pressure by the
critical pressure / vapour pressure of the adsorbent at the measurement
temperature. Relative pressure only has meaning when
the isotherm is recorded in a sub-critical regime. In order to calculate it, a
info of the specific adsorbate is required. This info is obtained
internally using an equation of state from either CoolProp or REFPROP.

Pressure conversions are handled by the
:func:`~pygaps.utilities.unit_converter.c_pressure` function.


Adsorbate loading
:::::::::::::::::

Adsorbate loading refers to the quantity of gas (adsorbate)
which is contained in the
material on which the isotherm is measured.
Currently pyGAPS does not differentiate between
excess and total amount adsorbed.

The adsorbate loading is usually represented in *mmol* or
*cm3 STP*, both of which are representations of a molar basis.
Sometimes it is useful if, instead of a mole basis,
the loading is represented in terms of mass or volume. pyGAPS allows for both
unit and basis conversions.

For these conversions, properties such as molar mass and
density of the adsorbate are required. This info is obtained
internally using an equation of state from either CoolProp or REFPROP.

Loading conversions are handled by the
:func:`~pygaps.utilities.unit_converter.c_loading` function.

Adsorbent quantity
:::::::::::::::::::

Adsorbent quantity refers to the amount of material that the
adsorption takes place on. The scientific community regularly
refers to a mass basis, while a volumetric basis is
more important in industry where adsorbent bed design sizing is required.
pyGAPS allows the basis to be changed to either mass, volume or molar.

Depending on the conversion basis, the density or molar mass of the
material is needed and should be provided by the user. To specify this in a
material, check out the :ref:`Material <material-manual-manage>` manual.

Adsorbent conversions are handled by the
:func:`~pygaps.utilities.unit_converter.c_adsorbent` function.


.. _units-manual-low-level:

Low-level convert
-----------------

The way units are converted under the hood is through
the use of dictionaries to store conversion factors
between the different unit types. The user can use the
functions directly by importing the
:mod:`pygaps.utilities.unit_converter` module.

An example pressure conversion:

::

    from pygaps.utilities.unit_converter import c_pressure

    c_pressure(1,
               mode_from='absolute', unit_from='bar',
               mode_from='absolute', unit_to='Pa')


An example loading conversion:

::

    from pygaps.utilities.unit_converter import c_loading

    c_loading(1,
              mode_from='molar', unit_from='mol',
              mode_from='mass', unit_to='mg')


An example pressure conversion:

::

    from pygaps.utilities.unit_converter import c_adsorbent

    c_adsorbent(1,
                mode_from='mass', unit_from='g',
                mode_from='volume', unit_to='cm3')



.. _units-manual-high-level:

High-level convert
------------------

In regular usage, the framework handles units for the user,
with no need to use the low-level functions.
At :ref:`raw isotherm creation <isotherms-manual-create>`,
the units can be specified through the use of
keywords.

From the creation of the isotherm, it internally keeps the units
it was created in. In order to :ref:`access the data <isotherms-manual-data>`
in a different unit than specified at instantiation, most methods
can accept the same keywords.


The isotherm internal data can also be permanently converted into
another unit, pressure mode or basis. This is not normally required,
but can be done if the isotherm is to be exported in different units.
To do this, check out
:ref:`this section of the manual <isotherms-manual-convert>`.


.. _units-manual-impact:

How units impact characterisation and modelling
-----------------------------------------------

Most characterisation methods automatically take the required
form of the units without the user having to convert it beforehand.
Therefore, if for example the BET area function is called, the conversion
will be made automatically in order to return the surface area in
square metres.

The basis of the adsorbent is unchanged however. Therefore,
if the isotherm was in a volume basis with units of *cm3* before the
calculation above, the returned surface area will be in
**square meters per cubic centimetre of adsorbent**.


