.. _sqlite-manual:

Sqlite database
===============

.. _sqlite-manual-general:

Overview
--------

The framework provides capabilities to interact with an sqlite database, in
order to store objects such as PointIsotherms, ModelIsotherms, Materials,
Adsorbates.

The database was initially envisioned as a centralised data storage for the
MADIREL Laboratory in Marseille. To generalize the concept for this framework,
the database has been simplified to what the authors consider *bare bones*, but
still extensible, functionality. Suggests for further improvements are welcome.

.. note::

    For most purposes, the internal database is adequate for storage and
    retrieval. However, it can be difficult to locate it on the disk, and,
    depending on the amount of data it stores, it can grow to a considerable
    size. Consider using a separate database file.


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

All the functions which interact with a database take the database path as their
first argument. If the internal database is to be used, the parameter passed
should be the ``pygaps.DATABASE`` reference. A complete list of methods can be
found in the :mod:`~pygaps.parsing.sqlite` reference.


.. _sqlite-manual-examples:

Database example
----------------

Check out the Jupyter notebook in the `examples <../examples/database.ipynb>`_
section


.. _sqlite-manual-creation:

Blank database creation
-----------------------

The internal database is already created and usable when pyGAPS is installed. If
the user decides to have an external database, they can either copy the internal
database (located in the `/pygaps/database` directory) or generate an empty one
using the ``db_create`` command.

::

    from pygaps.utilities.sqlite_db_creator import db_create
    db_create("path/to/database")

