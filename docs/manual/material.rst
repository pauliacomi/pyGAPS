.. _material-manual:

The Material class
==================

.. _material-manual-general:

Overview
--------

Similarly to :class:`~pygaps.core.adsorbate.Adsorbate`, a
:class:`~pygaps.core.material.Material` is a helper wrapper class around pyGAPS
concepts. The user might want to store details about adsorbent materials they
use. The information can range from date of synthesis, material density, etc.
For this case, pyGAPS provides the Material class.

The isotherm required property of ``material`` is used to connect an Isotherm
instance to a specific :class:`~pygaps.core.material.Material`. Each time an
isotherm is created, pyGAPS looks in the main material list
(``pygaps.MATERIAL_LIST``) for an object with the same name. This list is
populated as import-time with materials stored in the internal database. The
user can also add their own material to the list, or upload it to the database
for permanent storage.

.. note::

    For a complete list of methods and individual descriptions look at the
    :class:`~pygaps.core.material.Material` reference.


.. _material-manual-create:

Creating a Material
-------------------

To create an instance of the Material class, the material parameters are passed
directly. The parameters must contain a value for the material ``name``, with
the rest of the parameters being optional.

An example of how to create a material:

.. code:: python

    my_material = pygaps.Material(
        'carbon',                   # Name
        batch='X1',                 # User specific
        owner='Test User',          # User specific
        form='powder',              # User specific
        density=1,                  # User specific
        treatment='acid etching'    # User specific
    )


To view a summary of the material properties, the standard python print function
can be used.

.. code:: python

    print(my_material)

.. hint::

    All custom properties are found in the ``Material.properties`` dictionary.

    .. code:: python

        my_material.properties["form"]
        >> "powder"


.. _material-manual-manage:

Material management
-------------------

In pyGAPS, materials can be stored in the internal sqlite database. At
import-time, the list of all materials is automatically loaded into memory and
stored in ``pygaps.MATERIAL_LIST``. The easiest way to retrieve a material from
the list is to use the :meth:`~pygaps.core.material.Material.find` class method.
It takes the material name as parameter.

.. code:: python

    carbon = pygaps.Material.find('carbon')

At first use the database will be empty. To populate the database with
materials, the user should create the materials first and then append them to
the list for temporary storage, or upload them to a database for permanent
storage.

.. code:: python

    # To store in the main list
    pyGAPS.MATERIAL_LIST.append(my_material)

For more info, check out the :ref:`sqlite <sqlite-manual>` section of the
manual.
