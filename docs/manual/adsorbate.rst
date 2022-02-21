.. _adsorbate-manual:

The Adsorbate class
===================

.. _adsorbate-manual-general:

Overview
--------

In order for many of the calculations included in pyGAPS to be performed,
properties of the adsorbed phase must be known. To make the process as simple
and as painless as possible, the :class:`~pygaps.core.adsorbate.Adsorbate` class
is provided.

At creation, an :ref:`isotherm<isotherms-manual>` asks for an ``adsorbate``
parameter, a string which pyGAPS looks up in an internal list
(``pygaps.ADSORBATE_LIST``). If any known adsorbate ``name``/``alias`` matches,
this connects the isotherm object and the existing adsorbate class. This global
list is populated as import-time with the adsorbates stored in the internal
database. The user can also add their own adsorbate to the list, or upload it to
the database for permanent storage.

Any calculations/conversions then rely on the
:class:`~pygaps.core.adsorbate.Adsorbate` for providing parameters such as
saturation pressure, molar mass and density.

.. note::

    For a complete list of methods and individual descriptions look at the
    :class:`~pygaps.core.adsorbate.Adsorbate` class reference.


.. _adsorbate-manual-create:

Creating an Adsorbate
---------------------

The creation process of an :class:`~pygaps.core.adsorbate.Adsorbate` is similar
to that of other pyGAPS classes. Some parameters are strictly required for
instantiation, while others are recognised and can then be accessed by class
members. All other parameters passed are saved as well in an internal dictionary
called ``properties``.

An example of how to create an adsorbate:

.. code:: python

    my_adsorbate = pygaps.Adsorbate(
        'butane',                         # Required
        formula = 'C4H10',                # Recognised
        alias = ['n-butane', 'Butane'],   # Recognised
        backend_name = 'butane',          # Recognised, Required for CoolProp interaction
        saturation_pressure = 2.2,        # Recognised
        carbon_number = 4,                # User specific
    )

To view a summary of the adsorbate properties:

.. code:: python

    my_adsorbate.print_info()

.. hint::

    Some properties are recognised and available from the class:

    .. code:: python

        my_adsorbate.formula
        >> 'C4H10'

    All other custom properties are found in the ``Adsorbate.properties``
    dictionary.

    .. code:: python

        my_adsorbate.properties["carbon_number"]
        >> 4

.. note::

    It is unlikely that you will need to manually create an adsorbate, as more
    than 150 compounds are already included with pyGAPS.



Retrieving an Adsorbate
-----------------------

A selection of the most common gas and vapour adsorbates is already stored in
the internal database. At import-time, they are automatically loaded into memory
and stored in ``pygaps.ADSORBATE_LIST``.

.. code:: python

    len(pygaps.ADSORBATE_LIST)
    >> 176

To retrieve an :class:`~pygaps.core.adsorbate.Adsorbate` from this list, the
easiest way is by using the class method:
:meth:`~pygaps.core.adsorbate.Adsorbate.find` which works with any of the
compound aliases.

.. code:: python

    # all return the same Adsorbate instance
    ads = pygaps.Adsorbate.find("butane")
    ads = pygaps.Adsorbate.find("n-butane")
    ads = pygaps.Adsorbate.find("c4h10")


.. _adsorbate-manual-methods:

Adsorbate class methods
-----------------------

The :class:`~pygaps.core.adsorbate.Adsorbate` class has methods which allow the
properties of the adsorbate to be either calculated using the CoolProp or
REFPROP backend or retrieved as a string from the internal dictionary. The
properties which can be calculated are:

- Molar mass: :meth:`~pygaps.core.adsorbate.Adsorbate.molar_mass`.
- Saturation pressure: :meth:`~pygaps.core.adsorbate.Adsorbate.saturation_pressure`.
- Surface tension: :meth:`~pygaps.core.adsorbate.Adsorbate.surface_tension`.
- Liquid density: :meth:`~pygaps.core.adsorbate.Adsorbate.liquid_density`.
- Molar liquid density: :meth:`~pygaps.core.adsorbate.Adsorbate.liquid_molar_density`.
- Gas density: :meth:`~pygaps.core.adsorbate.Adsorbate.gas_density`.
- Molar gas density: :meth:`~pygaps.core.adsorbate.Adsorbate.gas_molar_density`.
- Enthalpy of liquefaction: :meth:`~pygaps.core.adsorbate.Adsorbate.enthalpy_liquefaction`.

For example, for the :class:`~pygaps.core.adsorbate.Adsorbate` created above, to
get the vapour pressure at 25 degrees in bar.

.. code:: python

    my_adsorbate.saturation_pressure(298, unit='bar')
    >> 2.8

.. caution::

    The properties calculated are only valid if the backend equation of state is
    usable at the required states and is accurate enough. Be aware of the
    limitations of CoolProp and REFPROP. More info :ref:`here<eqstate-manual>`.

Each method also accepts a bool parameter ``calculate``, ``True`` by default. If
set to ``False``, the property will **not** be calculated by the thermodynamic
backend. Instead, the value from the ``properties`` dictionary will be returned.
This is static and supplied by the user, but can be useful for adsorbates
without a thermodynamic backend.

.. code:: python

    my_adsorbate.saturation_pressure(298, calculate=False)
    >> 2.2              # Value in the `properties` dictionary

For calculations of other properties, the
`CoolProp backend <https://www.coolprop.org/coolprop/wrappers/Python/index.html>`__
can be accessed directly using the ``backend`` property. To calculate the
critical temperature for example.

.. code:: python

    my_adsorbate.backend.T_critical()


.. _adsorbate-manual-manage:

Adsorbate management
--------------------

If an :class:`~pygaps.core.adsorbate.Adsorbate` is manually created, a user can
add it to the list of adsorbates by appending it.

.. code:: python

    # To store in the main list
    pygaps.ADSORBATE_LIST.append(my_adsorbate)

A useful shorthand is to pass an optional parameter ``store`` at creation

.. code:: python

    # Automatically stored in ADSORBATE_LIST
    ads = pygaps.Adsorbate("acetylene", store=True)

.. warning::

    This makes the adsorbate available **only** in the current session. No
    permanent changes to the internal adsorbates are made this way.

To **permanently** store a custom adsorbate for later use or make modifications
to exiting adsorbates, the user must upload it to the internal database. This
can be done as:

.. code:: python

    import pygaps.parsing as pgp

    # To permanently store in the database
    pgp.adsorbate_to_db(ads_new)

    # To store any modifications to an adsorbate in the database
    pgp.adsorbate_to_db(ads_modified, overwrite=True)

For more info, check out the :ref:`sqlite <sqlite-manual>` section of the
manual.

