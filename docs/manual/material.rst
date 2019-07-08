.. _material-manual:

The Material class
==================

.. _material-manual-general:

Overview
--------

The Isotherm classes only the name of the material they are measured on.
However, the user might want to store a list of materials they use
with various other information in the database.
The information can range from the date of synthesis,
the material density, the machine used to make the
measurement, etc. For this case, pyGAPS provides the Material class.

The isotherm required property of ``material`` is used to connect
an Isotherm instance to a specific Material. The adsorbate class
also contains a property called ``name`` which should be identical
for a successful match.

Each time an adsorbate property is needed, pyGAPS looks in the
main material list (``pygaps.MATERIAL_LIST``)
for an object which corresponds to the criteria above.
This list is populated as import-time with the materials
stored in the internal database. The user can also
add their own material to the list, or upload it to
the database for permanent storage.

For a complete list of methods and individual descriptions
look at the :class:`~pygaps.core.material.Material` reference.

.. _material-manual-create:

Creating a Material
-------------------

To create an instance of the Material class, the material parameters
are passed directly. The parameters must contain a value for the material
``name``, with the rest of the parameters being optional.

An example of how to create a material:

::

    my_material = pygaps.Material(
        'carbon',                   # Name
        batch='X1',                 # User specific
        owner='Test User',          # User specific
        type='powder',              # User specific
        density=1,                  # User specific
        treatment='acid etching'    # User specific
    )


To view a summary of the material properties, the standard python
print function can be used.

::

    print(my_material)


.. _material-manual-manage:

Material management
-------------------

In pyGAPS, the materials can be stored in the internal
sqlite database. At import-time, the list of all materials is automatically
loaded into memory and stored in ``pygaps.MATERIAL_LIST``.
The easiest way to retrieve a material from the list is to use
the :meth:`~pygaps.core.material.Material.find` class method. It takes the
material name as parameter.

::

    my_material2 = pygaps.Material.find('carbon x1')

At first use the database will be empty. To populate the database
with materials, the user should create the materials first and then
upload them to the list for temporary storage, or to database for
permanent storage.

::

    # To store in the main list
    pyGAPS.MATERIAL_LIST.append(my_material)

For more info, check out the :ref:`sqlite <sqlite-manual>` section of
the manual.
