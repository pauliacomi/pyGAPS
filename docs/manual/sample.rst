.. _sample-manual:

The Sample class
================

.. _sample-manual-general:

Overview
--------

While the isotherm classes only contain the name and batch of the sample they are measured on,
the user might want to store a list of samples in the database, as well as to add other information.
This can range from the date of synthesis, the material density, the machine used to make the
measurement, etc. For this case, pyGAPS provides the Sample class.

The isotherm required properties of ``sample_name`` and ``sample_batch`` are used to connect
an Isotherm instance to a specific Sample. The adsorbate class also contains two properties
called ``name`` and ``batch`` which should be identical for a successful match.

Each time an adsorbate property is needed, pyGAPS looks in the main sample list (``pygaps.SAMPLE_LIST``)
for an object which corresponds to the criteria above.
This list is populated as import-time with the samples stored in the internal database. The user can also
add their own sample to the list, or upload it to the database for permanent storage.

For a complete list of methods and individual descriptions look at the :class:`~pygaps.classes.sample.Sample`
reference.

.. _sample-manual-create:

Creating a Sample
-----------------

To create an instance of the Sample class, the sample parameters are passed directly. The parameters
must contain a value for ``name`` and ``batch``, with the rest of the parameters being optional.

An example of how to create a sample:

::

    my_sample = pygaps.Sample(
        name='carbon',              # Required
        batch='X1',                 # Required
        owner='Test User',          # Recognised
        type='powder',              # Recognised
        density=1,                  # Recognised
        treatment='acid etching'    # Unknown / User specific
    )


To view a summary of the sample properties, the standard python print function can be used.

::

    print(my_sample)


.. _sample-manual-manage:

Sample management
-----------------

In pyGAPS, the samples can be stored in the internal sqlite database. At import-time, the list of all
samples is automatically loaded into memory and stored in ``pygaps.SAMPLE_LIST``. The easiest way to retrieve
a sample from the list is to use the :meth:`~pygaps.classes.sample.Sample.from_list` class method. It takes the
sample name and sample batch as parameters.

::

    my_sample2 = pygaps.Sample.from_list('carbon', 'X1')

At first use the database will be empty. To populate the database with samples, the user should
create the samples first and then upload them to the list for temporary storage, or to database for permanent storage.

::

    # To store in the main list
    pyGAPS.SAMPLE_LIST.append(my_sample)

For more info, check out the :ref:`sqlite <sqlite-manual>` section of the manual.
