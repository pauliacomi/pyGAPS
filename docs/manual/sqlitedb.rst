.. _sqlite-manual:

Sqlite database
===============

.. _sqlite-manual-general:

Overview
--------

The framework provides capabilities to interact with an sqlite database, in order to store objects such as
isotherms, samples, adsorbates and so on.

The database was initially envisioned as a centralised data storage for the MADIREL Laboratory in
Marseilles. To generalize the concept for a this framework, the
database has been simplified to what the authors consider a bare bones, but still extensible, functionality.
Suggests for further improvements are welcome.

.. note::

    For most purposes, the internal database is adequate for storage and retrieval. However, it can be
    difficult to locate it on the disk, and, depending on the amount of data it stores, it can grow to
    a considerable size. Consider using a separate database file.


.. _sqlite-manual-structure:

Database structure
------------------

The database is configured to use foreign keys, in order to prevent data redundancy and to enforce some
error checking. An example is connecting the isotherm  to an adsorbate which already exists in the
database. This will make sure that no stored isotherm has an unknown or misspelled adsorbate but it also
means that some groundwork is required before uploading the first isotherm.

A diagram of the database schema can be seen below:

.. image:: /figures/db_schema.png
    :scale: 30%
    :alt: Database schema.
    :align: center


.. _sqlite-manual-methods:

Database methods
----------------

All the functions which interact with a database, take the database path as their first argument. If the
internal database is to be used, the parameter passed should be the ``pygaps.DATABASE`` constant.

There are a few types of database functions:

    - :class:`~pygaps.classes.adsorbate.Adsorbate` management functions
    - :class:`~pygaps.classes.sample.Sample` management functions.
    - :class:`~pygaps.classes.pointisotherm.PointIsotherm` management functions,
      here called `experiment`
    - Functions which manage the `sources` table. This table is supposed to have a list of
      laboratories, papers or any similar source where the sample is from
    - Functions which manage the `contacts` table. This table is used for both sample
      connections (for example who is the sample responsible, the synthesiser, the paper
      author, etc...) and for experiment connections (who performed the experiment, who
      is the simulation author, etc...)
    - Functions which manage the `machines` table. This table is supposed to store a
      list of the machines where the experiments could be performed.

A complete list of methods can be found in the :mod:`~pygaps.parsing.sqliteinterface` reference.

.. note::

    For now, ModelIsotherms cannot be stored in the database.


.. _sqlite-manual-examples:

Database example
----------------

Check it out in the ipython notebook in the `examples <../examples/database.ipynb>`_ section


.. _sqlite-manual-creation:

Blank database creation
-----------------------

The internal database is already created and usable when pyGAPS is installed. If the user decides to have
an external database, they can either copy the internal database (located in the `/pygaps/database`
directory) or generate an empty one using the ``db_create`` command.

::

    import pygaps.utilities.sqlite_db_creator as creator

    creator.db_create(path_to_database)

