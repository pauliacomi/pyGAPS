.. _sqlite-manual:

Database
========

.. _sqlite-manual-general:

Overview
--------

The framework provides capabilities to interact with an sqlite database, in
order to store objects such as
:class:`~pygaps.core.pointisotherm.PointIsotherm`,
:class:`~pygaps.core.modelisotherm.ModelIsotherm`,
:class:`~pygaps.core.adsorbate.Adsorbate`,
:class:`~pygaps.core.material.Material`.

The database was initially envisioned as a centralised data storage for the
MADIREL Laboratory in Marseille. To generalize the concept for this framework,
the database has been simplified to what the authors consider *bare bones*, but
still extensible, functionality. Suggests for further improvements are welcome.

.. warning::

    The default database is packaged with pyGAPS, it may not be a durable
    personal store. Changes to it may be unavailable when package resources are
    temporary or read-only, and can be lost when the package is reinstalled or
    upgraded. For data you need to keep, make and back up a user-owned copy, and
    direct every database read, write, and delete to that copy with
    ``db_path=...``.


.. _sqlite-manual-structure:

Database structure
------------------

A diagram of the database schema can be seen below:

.. image:: /figures/db_schema.png
    :scale: 30%
    :alt: Database schema.
    :align: center

The database is configured to use foreign keys, in order to prevent data
redundancy and to enforce error checking. This will make sure that no stored
isotherm has an unknown or misspelled adsorbate but it also means that some
groundwork is required before uploading the first isotherm.

.. _sqlite-manual-methods:

Database methods
----------------

Database functions accept a ``db_path`` keyword. Always pass a custom path by
keyword: for example, ``material_to_db(material, db_path=my_db)``. If
``db_path`` is omitted, the packaged database is used. A complete list of
methods can be found in the :mod:`~pygaps.parsing.sqlite` reference.


.. _sqlite-manual-examples:

Database example
----------------

Check out the Jupyter notebook in the `examples <../examples/database.ipynb>`_
section. Before running any example that writes to or deletes from a database,
it is recommended to make a user-owned copy and pass its path by the ``db_path``
keyword on every operation.


.. _sqlite-manual-creation:

Blank database creation
-----------------------

The packaged database is already created and usable when pyGAPS is installed.
To work with its reference data while keeping your changes, copy it to a
user-owned location. The path is available as ``pygaps.DATABASE``; it is a
package resource, not a ``pygaps/database`` directory. Alternatively, create an
empty database with the ``db_create`` command.

.. code-block:: python

    from pathlib import Path
    from shutil import copy2
    import pygaps
    import pygaps.parsing as pgp
    from pygaps.utilities.sqlite_db_creator import db_create

    db_path = Path("my-pygaps.db")
    if not db_path.exists():
        copy2(pygaps.DATABASE, db_path)

    # Read from the user-owned copy; writes and deletes need the same keyword.
    materials = pgp.materials_from_db(db_path=db_path)

An empty database can instead be created as follows:

.. code-block:: python

    # Use a new path; do not point this at an existing database.
    db_create("my-empty-pygaps.db")

Back up a user-owned database regularly. Copying an existing database into an
already-used path can replace that file; check the destination before copying.
