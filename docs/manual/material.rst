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
For this case, pyGAPS provides the :class:`~pygaps.core.material.Material`
class.

The :ref:`isotherm<isotherms-manual>` required property of ``material`` is used
to create or connect a :class:`~pygaps.core.baseisotherm.BaseIsotherm` instance to a
:class:`~pygaps.core.material.Material`. Each time an isotherm is created,
pyGAPS looks in the main material list (``pygaps.MATERIAL_LIST``) for an
instance with the same name. This list is populated as import-time with
materials stored in the internal database. The user can also add their own
material to the list, or upload it to a user-owned database for persistent
storage. The packaged database is not a durable personal store; changes to it
may be lost or unavailable after reinstall or upgrade. If the
material does not exist in ``pygaps.MATERIAL_LIST``, pyGAPS will create a new
instance for the isotherm.

Any calculations/conversions then rely on the
:class:`~pygaps.core.material.Material` for providing parameters such as
material molar mass and density.

.. note::

    For a complete list of methods and individual descriptions look at the
    :class:`~pygaps.core.material.Material` reference.


.. _material-manual-create:

Creating a Material
-------------------

To create an instance of a :class:`~pygaps.core.material.Material`, parameters
must contain a value for the material ``name``, with anything else being
optional. Some are recognised as special properties (``density``, ...), while
other parameters passed are saved as well in an internal dictionary called
``properties``.

An example of how to create a material:

.. code:: python

    my_material = pygaps.Material(
        'carbon',                   # Name
        density=1,                  # Recognised
        molar_mass=256,             # Recognised
        batch='X1',                 # User specific
        owner='Test User',          # User specific
        form='powder',              # User specific
        treatment='acid etching'    # User specific
    )


To view a summary of the material properties:

.. code:: python

    my_material.print_info()


.. hint::

    All custom properties are found in the ``Material.properties`` dictionary.

    .. code:: python

        my_material.properties["form"]

The expression above returns ``"powder"``.


.. _material-manual-methods:

Material class methods
----------------------

The :class:`~pygaps.core.material.Material` class exposes some recognised
properties:

- Molar mass: :attr:`~pygaps.core.material.Material.molar_mass`.
- Density: :attr:`~pygaps.core.material.Material.density`.

These are not calculated, just looked up in the ``properties`` dictionary.

.. code:: python

    my_material.molar_mass

This returns ``256`` for the example material above.

.. testcode::

    from pygaps import Material

    sample = Material("doc-example", density=1, molar_mass=256, form="powder")
    assert sample.molar_mass == 256
    assert sample.density == 1
    assert sample.properties["form"] == "powder"


.. _material-manual-manage:

Material management
-------------------

In pyGAPS, materials can be stored in a sqlite database. At import time, the
materials from the packaged database are loaded into memory and stored in
``pygaps.MATERIAL_LIST``. The easiest way to retrieve a material from
the list is to use the :meth:`~pygaps.core.material.Material.find` class method.
It takes the material name as parameter.

.. code:: python

    carbon = pygaps.Material.find('carbon')

To use a material temporarily, create it and append it to the in-memory list.
To persist it, upload it to a user-owned database copy as shown below.

.. code:: python

    # To store in the main list
    pygaps.MATERIAL_LIST.append(my_material)

A useful shorthand is to pass an optional parameter ``store`` at creation

.. code:: python

    # Automatically stored in MATERIAL_LIST
    mat = pygaps.Material("MOF", store=True)

.. warning::

    This makes the material available **only** in the current session. No
    permanent changes to the materials are made this way.

To store a custom material in a database for later use, upload it to a
user-owned copy of the packaged database. The example below creates the copy
only when the destination does not already exist. Pass ``db_path`` by keyword
for every database operation; omitting it targets the packaged database, and
passing a path positionally may also target the packaged database.

.. code-block:: python

    from pathlib import Path
    from shutil import copy2
    import pygaps
    import pygaps.parsing as pgp

    db_path = Path("my-pygaps.db")
    if not db_path.exists():
        copy2(pygaps.DATABASE, db_path)

    mat_new = pygaps.Material("my-carbon", density=1, molar_mass=256)
    pgp.material_to_db(mat_new, db_path=db_path)

    # Overwrite replaces all stored fields for this material.
    # pgp.material_to_db(mat_new, db_path=db_path, overwrite=True)

Keep backups of this user-owned database. Do not treat changes to the packaged
database as permanent.

For more info, check out the :ref:`sqlite <sqlite-manual>` section of the
manual.
