.. _adsorbate-manual:

The Adsorbate class
===================

.. _adsorbate-manual-general:

Overview
--------

In order for many of the calculations included in pyGAPS to be performed,
properties of the analyte adsorbed on the material must be known. To make the
process as simple and as painless as possible, the Adsorbate class is provided.

At creation, an isotherm asks for an ``adsorbate`` parameter, which pyGAPS looks
up in an internal list (``pygaps.ADSORBATE_LIST``). If any known adsorbate
``name`` matches, this connects the isotherm object and the particular adsorbate
class associated to it. The global list is populated as import-time with the
adsorbates stored in the internal database. The user can also add their own
adsorbate to the list, or upload it to the database for permanent storage.

For a complete list of methods and individual descriptions look at the
:class:`~pygaps.core.adsorbate.Adsorbate` reference.

.. _adsorbate-manual-create:

Creating an Adsorbate
---------------------

The creation process of an adsorbate is similar to that of other pyGAPS classes.
Some parameters are strictly required for instantiation, while others are
recognised and can then be accessed by class members. All other parameters
passed are saved as well in an internal dictionary called ``properties``.

An example of how to create an adsorbate:

::

    my_adsorbate = pygaps.Adsorbate(
        'butane'                          # Required
        formula = 'C4H10',                # Recognised
        alias = [n-butane, Butane]        # Recognised
        backend_name = 'butane',          # Recognised, Required for CoolProp interaction
        saturation_pressure = 2.2,        # Recognised
        carbon_number = 4,                # User specific
    )

To view a summary of the sample properties, the standard python print function
can be used.

::

    print(my_adsorbate)

.. _adsorbate-manual-methods:

Adsorbate class methods
-----------------------

The Adsorbate class has methods which allow the properties of the adsorbate to
be either calculated using the CoolProp or REFPROP backend or retrieved as a
string from the internal dictionary. The properties which can be calculated are:

    - Molar mass
    - Saturation pressure
    - Surface tension
    - Liquid density
    - Molar liquid density
    - Gas density
    - Molar gas density
    - Enthalpy of liquefaction

For example, for the Adsorbate created above, to get the vapour pressure at 25
degrees in bar.

::

    my_adsorbate.saturation_pressure(298, unit='bar')
    >> 2.8

.. caution::

    The properties calculated are only valid if the backend equation of state is
    accurate enough. Be aware of the limitations of CoolProp and REFPROP.


The ``calculate`` boolean can also be set to ``False``, to return the value that
is present in the properties dictionary. Here the value is static and the
temperature and unit must be known by the user.

::

    my_adsorbate.saturation_pressure(298, calculate=False)
    >> 2.2              # Value in the creation dictionary

For calculations of other properties, the CoolProp backend can be accessed
directly using the ``backend`` property. To calculate the critical temperature
for example.

::

    my_adsorbate.backend.T_critical()

For all the adsorbate methods, see the :class:`~pygaps.core.adsorbate.Adsorbate`
reference

.. _adsorbate-manual-manage:


Adsorbate management
--------------------

A selection of the most common adsorbates used in experiments is already stored
in the internal database. At import-time, they are automatically loaded into
memory and stored in ``pygaps.ADSORBATE_LIST``. This should be enough for most
uses of the framework. To retrieve an adsorbate from the list, use the adsorbate
class method ``find``, which works with any of the aliases of the substance:

::

    my_adsorbate = pygaps.Adsorbate.find('CO2')
    my_adsorbate = pygaps.Adsorbate.find('water')

The user can also generate their own adsorbates, or modify the ones that are in
memory.

::

    # To store in the main list
    pyGAPS.ADSORBATE_LIST.append(my_adsorbate)

To permanently store a custom adsorbate for later use, the user can upload it to
the database. For info on how to do this, check out the
:ref:`sqlite <sqlite-manual>` section of the manual.
