.. _sample-manual:

The Sample class
================

.. _sample-manual-general:

Overview
--------

For simplicity, the isotherm class only contains the name and batch of the sample it is measured on.
However, the user might want to store a list of samples in the database, as well as to add other information
regarding the adsorbent used, such as the date of synthesis, its density, the user responsible etc. For this
case, pyGAPS provides the Sample class.

The isotherm required properties of `sample_name` and `sample_batch` are used to connect it to a
specific Sample. The adsorbate class also contains two properties called `name` and `batch`. If these
are identical, this connects the isotherm object and the particular sample class.

Each time an adsorbate property is needed, pyGAPS looks in the main sample list (pygaps.SAMPLE_LIST)
for an object which corresponds to the criteria above.
This list is populated as import-time with the samples stored in the internal database. The user can also
add their own sample to the list, or upload it to the database for permanent storage.

For a complete list of methods and individual descriptions look at the :ref:`reference <sample-ref>`.

.. _sample-manual-create:

Creating a Sample
-----------------

To create an instance of the Sample class, a dictionary with the sample parameters is required. The dictionary
has to contain a value for `name` and `batch`, with the rest of the parametrs being optional.

An example of how to create a sample:

::

    sample_info = {
        'name' : 'carbon',              # Required
        'batch' : 'X1',                 # Required
        'owner' : 'Test User',          # Recognised
        'type' : 'powder',              # Recognised
        'density' : 1,                  # Recognised
        `treatment` : 'acid etching'    # Unknown / User specific
    }

    my_sample = pygaps.Sample(sample_info)

To view a summary of the sample properties, the standard python print function can be used.

::

    print(my_sample)


.. _sample-manual-manage:

Sample management
-----------------

In pyGAPS, the samples can be stored in the internal sqlite database. At import-time, the list of all
samples is automatically loaded into memory and stored in `pygaps.SAMPLE_LIST`. The easiest way to retreive
a sample from the list is to use the Sample.from_list class method. It takes the sample name and sample batch
as parameters.

::

    my_sample = pygaps.Sample.from_list('carbon', 'X1')

However, at first use the database will be empty. To populate the database with samples, the user should
create the samples one by one and then upload them to the database. For more info, check out the sqlite
section of the manual.
