.. _sqlite-manual:

Sqlite database
===============

.. _sqlite-manual-general:

Overview
--------

The frameork provides capabilities to interact with an sqlite database, in order to store objects such as
isotherms, samples, adsorbates, users and so on.

All the functions which interact with a database, take the database path as their first argument. If the
internal database is to be used, the parameter passed should be the ``pygaps.DATABASE`` constant.

.. note::

    For most purposes, the internal database is adequate for storage and retrieval. However, it can be
    difficult to locate it on the disk, and, depending on the amount of data it stores, it can grow to
    a considerable size. Consider using a separate database file.


.. _sqlite-manual-structure:

Database structure
------------------

The database is configured to use foreign keys, in order to prevent data redundancy and to enforce some
error checking. An example is connecting the isotherm adsorbate to an adsorbate which already exists in the
database. This will make sure that no stored isotherm has an unknown or misspelled adsorbate but it also
means that some groundwork is required before uploading the first isotherm.

A diagram of the database schema can be seen below:



.. _sqlite-manual-methods:

Database methods
----------------

A complete list of methods can be found in the :mod:`~pygaps.parsing.sqliteinterface` reference.


.. _sqlite-manual-examples:

Database example
----------------

Let's assume we want to upload a newly created isotherm in the internal database. This isotherm
is measured on the novel adsorbent *Carbon X1*, with nitrogen at 77 K.

    - The internal database already contains nitrogen as an adsorbate therefore, there's no need to
      worry about this.

    - Since no samples are present in the internal database, we must first upload the sample object.
      We create a Sample class and then upload it to the database by using:

      ::

        pygaps.db_upload_sample(pygaps.DATABASE, my_adsorbent)

    - Finally, the isotherm can be uploaded as well.

      ::

        pygaps.db_upload_isotherm(pygaps.DATABASE, my_isotherm)


.. _sqlite-manual-creation:

Blank database creation
-----------------------

The internal database is already created and usable when pyGAPS is installed. If the user decides to have
an external database, they can either copy the internal database (located in the `/pygaps/database`
directory) or generate an empty one using the ``db_create`` command.

::

    import pygaps.utilities.sqlite_db_creator as creator

    creator.db_create(path_to_database)

