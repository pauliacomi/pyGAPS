.. _units-manual:

Units in pyGAPS
===============

.. _units-manual-general:

Overview
--------

When computers work with physical data, units are always a variable that introduces confusion to the
human users. This page attempts to explain how pyGAPS handles units and other such real world concepts
such as relative pressure and mass or volume basis.

Units can be specified for the following properties:

    - Isotherm pressure: *bar*, *Pa*, *atm*, *mmHg*
    - Isotherm loading: *mol*, *mmol*, *ml*, *cm3 STP*
    - Adsorbent mass, if working on a mass basis: *g*, *kg*
    - Adsorbent volume, if working on a volume basis: *cm3*, *ml*, *dm3*, *l*, *m3*

Two special physical concepts are handled by pyGAPS, relative pressure and adsorbent basis.

    - In adsorption terms, relative pressure is a dimensionless value which is obtained by
      dividing the absolute pressure by the critical pressure / vapour pressure of the
      adsorbent at the measurement temperature. Relative pressure only has meaning when
      the isotherm is recorded in a sub-critical regime. In order to calculate it, a
      property of the specific adsorbate is required. Therefore, relative pressure
      calculation is bundled in the :ref:`Adsorbate class <adsorbate-ref>`.

    - Adsorbent basis refers to whether the loading is calculated on the adsorbent in a
      "per mass" or "per volume" way. The scientific community regularly uses the mass
      basis, while volume basis is more important in industry where adsorbent bed design
      sizing is required. In order to convert between the two basis, the density of the
      sample is needed. Therefore, adsorbent basis conversions are bundled with the
      :ref:`Sample class <sample-ref>`.



.. _units-manual-low-level:

Low-level unit convert
----------------------

The way units are converted under the hood is through the use of dictionaries to store conversion factors
between the different unit types. The user can use the functions as well by importing the
:meth:`pygaps.utilities.unit_converter` module.

::

    from pygaps.utilities.unit_converter import convert_pressure
    convert_pressure(1, 'bar', 'Pa')

    100000


.. _units-manual-high-level:

High-level use of units
-----------------------

In regular usage, the framework handles units for the user, with no need to use the low-level functions.
At :ref:`raw isotherm creation <isotherms-manual-create>`, the units can be specified through the use of
keywords.

From the creation of the isotherm, it internally keeps the units it was created in. In order to access the
data in a different unit than specified at instantiation, most methods can accept the same keywords.

The isotherm internal data can also be permanently converted into another unit, pressure mode or basis.
This is not normally required, but can be done if the isotherm is to be exported in different units.
To do this, use the provided methods such as :meth:`~pygaps.classes.PointIsotherm.convert_unit_loading`.


.. _units-manual-impact:

How units impact characterisation and modelling
-----------------------------------------------

Most characterisation methods automatically take the required form of the units without the user having to
convert it beforehand. Therefore, if for example the BET area function is called, the conversion will be made
automatically in order to return the surface area in square metres.

The basis of the adsorbent is unchanged however. Therefore, if the isotherm was in a volume basis with units
of *cm3* before the calculation above, the returned surface area will be in **square meters per cubic centimetre
of adsorbent**.


