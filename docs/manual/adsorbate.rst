.. _adsorbate-manual:

The Adsorbate class
===================

.. _adsorbate-manual-general:

Overview
--------

In order for many of the calculations included in pyGAPS to be performed,
properties of the analyte adsorbed on the material must be known. To make the
process as simple and as painless as possible, the
:class:`~pygaps.core.adsorbate.Adsorbate` class is provided.

At creation, an :ref:`isotherm<isotherms-manual>` asks for an ``adsorbate``
parameter, which pyGAPS looks up in an internal list
(``pygaps.ADSORBATE_LIST``). If any known adsorbate ``name`` matches, this
connects the isotherm object and the particular adsorbate class associated to
it. The global list is populated as import-time with the adsorbates stored in
the internal database. The user can also add their own adsorbate to the list, or
upload it to the database for permanent storage.

.. note::

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

.. code:: python

    my_adsorbate = pygaps.Adsorbate(
        'butane'                          # Required
        formula = 'C4H10',                # Recognised
        alias = ['n-butane', 'Butane']    # Recognised
        backend_name = 'butane',          # Recognised, Required for CoolProp interaction
        saturation_pressure = 2.2,        # Recognised
        carbon_number = 4,                # User specific
    )

To view a summary of the sample properties, the standard python print function
can be used.

.. code:: python

    print(my_adsorbate)

.. hint::

    All custom properties are found in the ``Adsorbate.properties`` dictionary.

    .. code:: python

        my_adsorbate.properties["carbon_number"]
        >> 4


.. _adsorbate-manual-methods:

Adsorbate class methods
-----------------------

The Adsorbate class has methods which allow the properties of the adsorbate to
be either calculated using the CoolProp or REFPROP backend or retrieved as a
string from the internal dictionary. The properties which can be calculated are:

- Molar mass: :meth:`~pygaps.core.adsorbate.Adsorbate.molar_mass`.
- Saturation pressure: :meth:`~pygaps.core.adsorbate.Adsorbate.saturation_pressure`.
- Surface tension: :meth:`~pygaps.core.adsorbate.Adsorbate.surface_tension`.
- Liquid density: :meth:`~pygaps.core.adsorbate.Adsorbate.liquid_density`.
- Molar liquid density: :meth:`~pygaps.core.adsorbate.Adsorbate.liquid_molar_density`.
- Gas density: :meth:`~pygaps.core.adsorbate.Adsorbate.gas_density`.
- Molar gas density: :meth:`~pygaps.core.adsorbate.Adsorbate.gas_molar_density`.
- Enthalpy of liquefaction: :meth:`~pygaps.core.adsorbate.Adsorbate.enthalpy_liquefaction`.

For example, for the Adsorbate created above, to get the vapour pressure at 25
degrees in bar.

.. code:: python

    my_adsorbate.saturation_pressure(298, unit='bar')
    >> 2.8

.. caution::

    The properties calculated are only valid if the backend equation of state is
    usable at the required states and is accurate enough. Be aware of the
    limitations of CoolProp and REFPROP.


The ``calculate`` boolean can also be set to ``False``, to return the value that
is present in the properties dictionary. Here the value is static and the
temperature and unit must be known by the user.

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

A selection of the most common gas and vapour adsorbates is already stored in
the internal database. At import-time, they are automatically loaded into memory
and stored in ``pygaps.ADSORBATE_LIST``. This should be enough for most uses of
the framework. To retrieve an adsorbate from the list, use the adsorbate class
method ``find``, which works with any of the aliases of the substance:

.. code:: python

    co2 = pygaps.Adsorbate.find('CO2')
    h2o = pygaps.Adsorbate.find('water')

The user can also generate their own adsorbates, or modify the ones that are in
memory.

.. code:: python

    # To store in the main list
    pyGAPS.ADSORBATE_LIST.append(my_adsorbate)

.. hint::

    To **permanently** store a custom adsorbate for later use, the user can
    upload it to the database. For info on how to do this, check out the
    :ref:`sqlite <sqlite-manual>` section of the manual.
