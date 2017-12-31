.. _adsorbate-manual:

The Adsorbate class
===================

.. _adsorbate-manual-general:

Overview
--------

In order for many of the calculations included in pyGAPS to be performed, properties of the adsorbate used
to measure isotherm must be known. To make the process as simple and as painless as possible, the Adsorbate
class is provided.

Each isotherm must contain a required property (string) called ``adsorbate``. The adsorbate class also
contains a property called ``name``. If the two are identical, this connects the isotherm object and the
particular adsorbate class associated to it.

Each time an adsorbate property is needed, pyGAPS looks in the main adsorbate list (``pygaps.ADSORBATE_LIST``)
for an object which corresponds to the ``isotherm.adsorbate`` property.
This list is populated as import-time with the adsorbates stored in the internal database. The user can also
add their own adsorbate to the list, or upload it to the database for permanent storage.

For a complete list of methods and individual descriptions look at the :class:`~pygaps.classes.adsorbate.Adsorbate`
reference.

.. _adsorbate-manual-create:

Creating an Adsorbate
---------------------

The creation process of an adsorbate is similar to that of other pyGAPS classes, done by
directly passing the parameters. Some parameters are strictly required for instantiation,
while others are recognised and can then be accessed by class members.
All other parameters passed are saved as well in an internal dictionary called ``properties``.

An example of how to create an adsorbate:

::

    my_adsorbate = pygaps.Adsorbate(
        name = 'butane',                  # Required
        formula = 'C4H10',                # Required
        common_name = 'butane',           # Recognised, Required for CoolProp interaction
        saturation_pressure = 3,          # Recognised
        carbon_number = 4,                # Unknown / user specific
    )

To view a summary of the sample properties, the standard python print function can be used.

::

    print(my_adsorbate)

.. _adsorbate-manual-methods:

Adsorbate class methods
-----------------------

The Adsorbate class has methods which allow the properties of the adsorbate to be either calculated
using the CoolProp or REFPROP backend or retrieved as a string from the internal dictionary.
The properties which can be calculated are:

    - Molar Mass
    - Saturation Pressure
    - Surface Tension
    - Liquid Density
    - Gas Density

For example, for the Adsorbate created above, to get the vapour pressure at 25 degrees in bar.

::

    my_adsorbate.saturation_pressure(298, unit='bar')
    2.8

.. caution::

    The properties calculated are only valid if the backend equation of state is accurate enough.
    Be aware of the limitations of CoolProp and REFPROP.


The ``calculate`` boolean can also be set to ``False``, to return the value that is present in the
properties dictionary. Here the value is static and the temperature and unit must be known by the user.

::

    my_adsorbate.saturation_pressure(298, calculate=False)
    3


For all the adsorbate methods, see the :class:`~pygaps.classes.adsorbate.Adsorbate` reference

.. _adsorbate-manual-manage:


Adsorbate management
--------------------

A selection of the most common adsorbates used in experiments is already stored in the internal database.
At import-time, they are automatically loaded into memory and stored in ``pygaps.ADSORBATE_LIST``.
This should be enough for most uses of the framework. To retrieve an adsorbate from the list, use the
adsorbate class method with the name as the parameter:

::

    my_adsorbate2 = pygaps.Adsorbate.from_list('CO2')

The user can also generate their own adsorbates, or modify the ones that are in memory.

::

    # To store in the main list
    pyGAPS.ADSORBATE_LIST.append(my_adsorbate)

To permanently store a custom adsorbate for later use, the user can upload it to the database.
For info on how to do this, check out the :ref:`sqlite <sqlite-manual>` section of the manual.
