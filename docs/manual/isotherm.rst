.. _isotherms-manual:

The Isotherm classes
====================

.. _isotherms-manual-general:

Overview
--------

In pyGAPS, an isotherm can be represented in two ways: as a PointIsotherm object or as a
ModelIsotherm object. These two classes have many common methods and attributes, but they
differ in the way they hold the relationship between pressure and loading:

    - The PointIsotherm class is a collection of discrete points,
      stored in a pandas.DataFrame object.
    - The ModelIsotherm class is a table of parameters which are used
      to describe a model of adsorption behaviour.

Both classes are derived from the Isotherm class. This class holds all descriptions of the
experiment, such as the adsorbate used, the material name and the temperature at which the
isotherm was taken. These parameters are inherited in the two child isotherm objects.

To work with pyGAPS isotherms check out the following topics:

    - Creating an isotherm
    - Isotherm methods
    - Exporting an isotherm

.. _isotherms-manual-create:

Creating an isotherm
--------------------

There are several ways to create a PointIsotherm object:

    - Raw construction, from a dictionary with parameters and a pandas.DataFrame. This is the
      most extensible way to create a PointIsotherm, as parameters can be manually specified.
    - A json string or file. This can be done either using the pygaps.isotherm_from_json()
      function, or with the PointIsotherm.from_json() class method, which is just a wrapper
      around the other for convenience.
    - Parsing an excel file of a standard format. See parsing from excel.
    - Parsing a csv file of a standard format. See parsing from csv.
    - From an sqlite database: pyGAPS contains functionality to store and retreive constructed
      isotherms in a sqlite database. See database interoperability.

If using a pandas DataFrame, first the two components of the isotherm should be created:
a dictionary with the parameters and a DataFrame with the data.

The isotherm parameters dictionary has to have at least four specific components: the sample
name, the sample batch, the adsorbent used and the temperature (in K) at which the data was
recorded.
Other user parameters can be passed as well, and will be stored in the isotherm object. Some
are named, and can be accessed directly, such as t_act (sample activation temperature), user
(the person who measured the isotherm) and machine (the machine on which the isotherm was
recorded). Unknown parameters which are in the parameters dictionary are stored in an internal
dictionary called isotherm_parameters. For a complete list of named internal parameters, see
the :ref:`PointIsotherm reference <pointisotherm-ref>` and the
:ref:`ModelIsotherm reference <modelisotherm-ref>`

An example parameters dictionary
::

    isotherm_parameters = {
        'sample_name' : 'carbon',       # Required
        'sample_batch' : 'X1',          # Required
        'adsorbate' : 'nitrogen',       # Required
        't_exp' : 77,                   # Required
        't_act' : 150,                  # Recognised / named
        'user'  : 'Steve',              # Recognised / named
        'DOI'   : '10.000/mydoi',       # Unknown / user specific
        'something' : 'something',      # Unknown / user specific
    }

The pandas DataFrame which contains the data should have at least two columns: the pressures
at which each point was recorded, and the loadings for each point. Other data columns, such
as calorimetry data, magnetic field strengths, or other simultaneous measurements are also
supported.

::

    isotherm_data = pandas.DataFrame({
        'pressure' : [1, 2, 3, 4, 5, 3, 2]
        'loading' : [1, 2, 3, 4, 5, 3, 2]
        'enthalpy' : [15, 15, 15, 15, 15, 15, 15]
    })

.. caution::
    The data in the columns is assumed to be free of errors and anomalies. Negative
    pressures or loadings, noisy signals or erroneous points will give undefined
    behaviour

With these two components, the isotherm can be created. This is done by passing the two
components previously created, as well as a few required or optional parameters.

    - The `loading_key` and `pressure_key` are required parameters which specify which
      column in the DataFrame contain which data of the isotherm. If other columns are to be
      stored in the isotherm object, put their names in a list and pass it as the `other_keys`
      parameter
    - The unit paramterers `unit_loading` and `unit_pressure` are optional and specify
      the unit the isotherm is created in. By default, the loading is read in *mmmol* and the
      pressure is read in *bar*.
    - The optional `mode_pressure` parameter specifies if the pressure is relative or absolute
    - The optional `basis_adsorbent` parameter specifies if the loading is measured per mass or per
      volume of adsorbent material.

::

    isotherm = pygaps.PointIsotherm(
        isotherm_data,
        loading_key='loading',
        pressure_key='pressure',
        isotherm_parameters
    )

After each construction, each isotherm generates an id. This id is supposed to be a fingerprint of the
isotherm and should be unique to each isotherm. The id string is actually an md5 hash of the isotherm
parameters and data. The way this is done is as follows:

    - After isotherm instantiation, the isotherm object calls the json converter and obtains a string
      of itself in json format
    - The hashlib.md5 function is used to obtain a hash of the json string
    - The hash is saved in the internal id parameter and the instantiation is complete

Any internal change in the isotherm, such as changing the sample activation temperature, adding a new
member in the data dictionary or converting/deleting the isotherm datapoints will lead to the id to
be regenerated from the new data. This should be taken into account if writing a function that would
modify a large number of isotherms or if repeteadly modifying each isotherm.
It can be read directly from the isotherm but should never be directly modified.

::

    isotherm.id

.. _isotherms-manual-methods:

Isotherm methods
----------------

A detailed explanation of each isotherm method is written in the docstrings and can be accessed in the
reference. Only a general overview will be given here.

Once an isotherm is created, the first thing most users will want would be to graph the data. The isotherm
class contains a useful print_info() function which, if run in an interactive environment, will display the
isotherm parameters, as well as a graph of the data.

To access isotherm data, one of several functions can be used. First, the data() function returns all or a
part of the internal pandas.DataFrame. This is generally not very useful for quick processing, therefore
the data-specific functions can be used: pressure(), loading() and other_data().

All data-specific functions can return either a pandas.Series object, or a numpy.array, depending on the
parameters passed to it. Other optional parameters can specifiy the unit, the mode/basis, the branch the
data is returned in as well as a particular pressure range if desired.

The other_data function is built for accessing user-specific data stored in the isotherm object. Its use is
similar to the loading and pressure functions, but the column of the DataFrame where the data is held should
be specified in the function call as the `key` parameter.


Besides functions which give access to the internal datapoints, the isotherm obeject can also interpolate
between points and return the value of pressure and loading at a point specified by the user. To differentiate
them from the functions returning internal data, the functions have 'at' in their name.

In the ModelIsotherm class, the internal model is used to calculate the data required.

In the PointIsotherm class, the functions rely on an internal interpolator, which uses the scipy.interpolate
module. To attempt to optimize performance of working with isotherms, the interpolator is only constructed
when needed. The internal logic is structured as follows:

    - User requests the interpolated loading at a particular pressure point.
    - Isotherm checks if the interpolator has been already constructed, for the particular units, mode
      and basis, the user has requested. If yes, it is used to calculate the required point.
    - If interpolator object was never created or if the user requested interpolation on a different
      unit/branch/mode/basis, the interpolator is first constructed and stored in the isotherm object.

.. caution::

    Interpolation can be dangerous. pyGAPS does not implicitly allow interpolation outside the bounds of the
    data, although the user can force it to by passing an `interp_fill` parameter to the interpolating
    functions, usually if the isotherm is known to have reached the maximum adsorption plateau. Otherwise,
    the user is responsible for making sure the data is fit for purpose.



The conversion functions can be used to convert the internal isotherm data to a new state. This is only useful in certain cases, like when you want to export the isotherm in a converted excel or json form.
If only the data in a particular format is desired it is easier to get it directly via the data access functions above. The conversion functions are:

    - `convert_unit_loading` will convert the unit of the loading of the isotherm, for example from the
      *mmol* to *cm3 STP*
    - `convert_unit_pressure` will convert the unit of pressure, for example from *bar* to *atm*
    - `convert_mode_pressure` will convert the pressure from a relative to an absolute mode or vice-versa
    - `convert_basis_adsorbent` will convert the adsorbent basis, for example from a mass basis to a volume
      basis

In order for pyGAPS to correctly convert between pressure mode and adsorbent basis, the user might have to
add some parameters.

To convert an absolute pressure in a relative pressure, the critical pressure of the gas at the experiment
temperature must be known. Of course this conversion only works when the isotherm is not measured in a
supercritical regime. To do the conversion, pyGAPS relies on the CoolProp library. Therefore, the name
of the gas must be somehow passed to the CoolProp backend. pyGAPS does this by having an internal list
of adsorbates, which is loaded from the database at the moment of import. The logical steps follows are:

    - User requests conversion from absolute to relative pressure for an isotherm object
    - The adsorbate name is taken from the isotherm parameter and matched against the name of an
      adsorbate in the internal list
    - If the adsorbate is found, the name of the adsorbate in the CoolProp-defined way is retreived
    - CoolProp calculates the critical point pressure for the adsorbate
    - The relative pressure is calculated by dividing by the critical point pressure

If using commmon gasses, the user should not be worried about this process, as the list of adsorbates is
stored in the internal database. However, if a new adsorbate is to be used, the user should add it to the
master list himself.

For adsorbent basis conversions, the density of the adsorbent should be known. The way the density is etreived
is very similar to property retrieval from the adsorbates. A list of Samples is kept by pyGAPS,
loaded at import-time from the database. The user must create a Sample instance, populate it with the density
parameter and then upload it either to the internal list or the internal database. For more info on this
see the :ref:`Sample class <sample-manual>`

.. _isotherms-manual-export:

Exporting an isotherm
---------------------

To export an isotherm, pyGAPS provides several choices to the user:

    - Converting the isotherm in a JSON format, using the isotherm_to_json function
    - Converting the isotherm to a CSV file, using the isotherm_to_csv function
    - Converting the isotherm to an Excel file, using the isotehrm_to_excel function
      (of course only valid if excel is installed on the system)
    - Uploading the isotherm to a sqlite database, either using the internal database or
      a user-specified external one. For more info on interacting with the sqlite database
      see the respective section of the manual.

