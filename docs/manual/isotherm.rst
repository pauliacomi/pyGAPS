.. _isotherms-manual:

The Isotherm classes
====================

.. _isotherms-manual-general:

Overview
--------

In pyGAPS, an isotherm can be represented in two ways: as a
:meth:`~pygaps.core.pointisotherm.PointIsotherm` object or as a
:meth:`~pygaps.core.modelisotherm.ModelIsotherm` object. These two classes have
many common methods and attributes, but they differ in the way they represent
the relationship between pressure and loading:

    - The PointIsotherm class is a collection of discrete points, stored in a
      pandas.DataFrame object. It can contain both an adsorption and desorption
      branch, which are determined automatically at instantiation or specified
      by the user.
    - The ModelIsotherm class is a collection of parameters which are used to
      describe a model of adsorption behaviour. It can only model a single
      branch of the data, either adsorption or desorption.

Both classes are derived from the :meth:`~pygaps.core.baseisotherm.BaseIsotherm`
class. This class holds parameters of the isotherm besides data, such as the
adsorbate used, the material's name and the temperature at which the isotherm
was measured. These parameters are then inherited by the two child isotherm
objects. The user is unlikely to use this class directly.


To work with pyGAPS isotherms check out the following topics:

    - :ref:`Creating an isotherm <isotherms-manual-create>`
    - :ref:`Accessing isotherm data <isotherms-manual-data>`
    - :ref:`Isotherm units, modes and basis <isotherms-manual-convert>`
    - :ref:`Ensuring isotherm uniqueness <isotherms-manual-unique>`
    - :ref:`Exporting an isotherm <isotherms-manual-export>`

A detailed explanation of each isotherm class and methods is written in the
respective docstrings and can be accessed in the
:ref:`reference <isotherms-ref>`. Only a general overview will be given here.

.. _isotherms-manual-create:

Creating an isotherm
--------------------

Creating a PointIsotherm
::::::::::::::::::::::::

There are several ways to create a PointIsotherm object:

    - The most basic method, by using a pressure and a loading array.
    - From a pandas.DataFrame. This is the most extensible way to create a
      PointIsotherm, as other data types can be specified.
    - From a json string or file. This can be done either using the
      :meth:`~pygaps.parsing.json.isotherm_from_json`
      function which takes either string or file descriptor input.
      See :ref:`parsing from excel <parsing-manual-json>`.
    - Parsing a csv string or file of a standard format.
      See :ref:`parsing from csv <parsing-manual-csv>`.
    - Parsing an excel file of a standard format.
      See :ref:`parsing from excel <parsing-manual-excel>`.
    - From an sqlite database: pyGAPS contains functionality to
      store and retrieve constructed isotherms in an sqlite database.
      See :ref:`database <parsing-manual-sqlite>`.

This section will explain how to create an isotherm from raw data. The fastest
way to create an isotherm is to pass a pressure and a loading array to the
constructor as the ``pressure`` and ``loading`` parameters.

The code does its best to attempt to guess whether the data passed is part of an
adsorption branch, desorption branch or has both. It does this by looking at
whether pressure is increasing or decreasing between two consecutive points. It
then marks the particular branch internally. If the data isn't well conditioned,
this functionality will likely not produce good results. In this case, the user
can specify whether the data is an adsorption or desorption branch by using the
``branch`` argument. What's more, the user can specify where the branches are
located by passing an iterable as the ``branch`` parameter. See more in the
:ref:`reference <isotherms-pointisotherm>`.

.. caution::

    The data in the columns is assumed to be free of errors and anomalies.
    Negative pressures or loadings, noisy signals or erroneous points may give
    undefined behaviour.


The other information that needs to be passed to the constructor is related to
the parameters of the isotherm. This is information about the material the
isotherm was measured on, the adsorbate which was used, as well as data about
the temperature, units used and so on.

Besides data, the isotherm parameters must include:

    - The material name (``material``)
    - The adsorbate used (``adsorbate``)
    - The temperature, in K at which the data was recorded (``temperature``)

The isotherm units can also be specified here. If not specified, the framework
will assume default values: absolute pressure in *bar* and amount adsorbed in
terms of *mmol* per *g* (molar basis loading per adsorbent material mass basis).
Options are:

    - The ``pressure_mode`` parameter specifies if the pressure is absolute or
      relative (p/p0). If not passed, the pressure is assumed to be absolute.

    - The ``pressure_unit`` specifies the unit the pressure is measured in, if
      applicable. It can be *bar*, *Pa*, *kPa*, etc. and it defaults to *bar* .

    - The ``loading_basis`` parameter specifies if the amount adsorbed is
      defined in terms of moles, volume or mass. If not passed, it is assumed to
      be molar.

    - The ``loading_unit`` specifies the unit the amount adsorbed is in.
      Depending on the basis it can be a mass, volume or molar unit. By default,
      the loading is read in *mmol*.

    - The ``material_basis`` parameter specifies if the quantity of material
      is defined in terms of moles, volume or mass. If not passed, it is assumed
      to be on a mass basis.

    - The ``material_unit`` specifies the unit the material itself is in.
      Depending on the basis it can be a mass, volume or molar unit. By default,
      the material is is read in *g*.

Other user parameters can be passed as well, and will be stored in the isotherm
object as properties. Will these components, an isotherm can now be created. An
example instantiation is given below, with explanations.

::

    point_isotherm = pygaps.PointIsotherm(

        pressure=[1,2,3],               # pressure here
        loading=[1,2,3],                # loading here

        # Unit parameters can be specified

        pressure_mode='absolute',       # Working in absolute pressure
        pressure_unit='bar',            # with units of bar
        material_basis='mass',          # Working on a mass material basis
        material_unit='kg',             # with units of kg
        loading_basis='mass',           # Working on a loading mass basis
        loading_unit='g',               # with units of g

        # Finally the isotherm metadata

        material='carbon',              # Required
        adsorbate='nitrogen',           # Required
        temperature=77,                 # Required

        apparatus='X1',                 # User specific
        activation_temperature=150,     # User specific
        user='John',                    # User specific
        DOI='10.000/mydoi',             # User specific
        something='something',          # User specific
    )

Alternatively, a ``pandas.DataFrame`` can be passed in. This allows for more data
than just pressure and loading to be stored in a single isotherm. The DataFrame
should have at least two columns: the pressures at which each point was
recorded, and the loadings for each point. Other data columns can represent
calorimetry data, magnetic field strengths, or other simultaneous measurements.

If a DataFrame is used, ``loading_key`` and ``pressure_key`` are required
parameters specifying which column in the DataFrame contains what data of the
isotherm. If other columns are to be stored in the isotherm object, their names
should be passed in a list as the ``other_keys`` parameter. As an example:

::

    point_isotherm = pygaps.PointIsotherm(

        # First the pandas.DataFrame with the points
        # and the keys to what the columns represent.

        isotherm_data=pandas.DataFrame({
            'pressure' : [1, 2, 3, 4, 5, 3, 2],             # required
            'loading' : [1, 2, 3, 4, 5, 3, 2],              # required
            'enthalpy' : [15, 15, 15, 15, 15, 15, 15],
            'xrd_peak_1' : [0, 0, 1, 2, 2, 1, 0],
        }),

        loading_key='loading',          # The loading column
        pressure_key='pressure',        # The pressure column
        other_keys=['enthalpy',
                    'xrd_peak_1'],      # The columns containing the other data

        # Other required isotherm parameters

        material='carbon',              # Required
        adsorbate='nitrogen',           # Required
        temperature=77,                 # Required
    )


Creating a ModelIsotherm
::::::::::::::::::::::::

To create a ModelIsotherm, one can use either raw data, in a process similar to
the PointIsotherm creation above or, if a PointIsotherm is already created, it
can be used to fit a model.

ModelIsotherm creation from raw data is almost identical to the PointIsotherm
creation. The same data and parameters can be used, but with a few other
parameters:

    - The ``model`` parameter specifies which model/models
      to use to attempt to fit the data.
    - The ``branch`` parameter will specify which
      isotherm branch (adsorption or desorption)
      will be represented by the model, as both cannot be used
      at the same time. It defaults to the adsorption branch.
    - The ``param_guess`` specifies the initial model parameter
      guesses where optimisation should start. The parameter is optional,
      and will be automatically filled unless the user specifies it.
    - The ``optimization_params`` is a dictionary which will be passed
      to scipy.optimise.least_squares.
    - Finally, the ``verbose`` parameter can be used to
      increase the amount of information printed
      during the model fitting procedure.

.. note::

    The ModelIsotherm cannot be used to model tertiary data. Therefore, only
    loading and pressure can be used internally. Any other columns in the
    DataFrame will be ignored.

The code to generate a ModelIsotherm is then:

::

    model_isotherm = pygaps.ModelIsotherm(

        pressure=[1,2,3],               # pressure here
        loading=[1,2,3],                # loading here

        # Now the model details can be specified

        model='Henry',                  # Want to fit using the Henry model
        branch='ads',                   # on the adsorption branch
        param_guess={"K" : 2}           # from an initial guess of 2 for the constant
        verbose='True',                 # and increased verbosity.

        # Unit parameters can be specified

        pressure_mode='absolute',       # Working in absolute pressure
        pressure_unit='bar',            # with units of bar
        material_basis='mass',          # Working on a mass material basis
        material_unit='kg',             # with units of kg
        loading_basis='mass',           # Working on a loading mass basis
        loading_unit='g',               # with units of g

        # Finally the isotherm parameters

        material='carbon',              # Required
        adsorbate='nitrogen',           # Required
        temperature=77,                 # Required

        apparatus='X1',                 # User specific
        activation_temperature=150,                      # User specific
        user='John',                    # User specific
        DOI='10.000/mydoi',             # User specific
        something='something',          # User specific
    )

ModelIsotherms can also be constructed from PointIsotherms and vice-versa. The
best model can also be guessed automatically. As an example:

::

    model_isotherm = pygaps.model_iso(
        point_isotherm,                 # a PointIsotherm
        model=['Henry', 'Langmuir'],    # Want to try multiple models and fit the best
        verbose='True',                 # and increased verbosity.
    )

For more info on isotherm modelling read the :ref:`section <modelling-manual>`
of the manual.


.. _isotherms-manual-data:

Accessing isotherm data
-----------------------

Once an isotherm is created, it is useful to check if it contains the correct
parameters or make a plot of the isotherm. The isotherm classes can be inspected
using the following functions:

    - The Python ``print(iso)`` will display all isotherm properties.
    - The ``iso.plot()`` function will display an isotherm plot.
      (:meth:`~pygaps.core.pointisotherm.PointIsotherm.plot`)
    - The ``iso.print_info()`` function combines the two above
      (:meth:`~pygaps.core.pointisotherm.PointIsotherm.print_info`)

To access the isotherm data, one of several functions can be used. There are
individual methods for each data type: ``pressure``, ``loading`` and
``other_data``. The first two are applicable to both PointIsotherms and
ModelIsotherms. While PointIsotherm methods return the actual discrete data,
ModelIsotherms use their internal model to generate data with the
characteristics required.

    - For loading: PointIsotherm :meth:`~pygaps.core.pointisotherm.PointIsotherm.loading`
      and ModelIsotherm :meth:`~pygaps.core.modelisotherm.ModelIsotherm.loading`

    - For pressure: PointIsotherm :meth:`~pygaps.core.pointisotherm.PointIsotherm.pressure`
      and ModelIsotherm :meth:`~pygaps.core.modelisotherm.ModelIsotherm.pressure`

    - For tertiary data columns: PointIsotherm :meth:`~pygaps.core.pointisotherm.PointIsotherm.other_data`

All data-specific functions can return either a ``pandas.Series`` object or a
``numpy.array``, depending on the parameters passed to it. Other optional
parameters can specify the unit, the mode/basis, the branch the data is returned
from as well as a particular range the data should be selected in. For example:

::

    # Will return the loading points of the adsorption part of the
    # isotherm in the range if 0.5-0.9 cm3(STP)

    isotherm.loading(
        branch='ads',
        loading_unit='cm3(STP)',
        limits = (0.5, 0.9),
    )

The ``other_data`` function is built for accessing user-specific data stored in
the isotherm object. Its use is similar to the loading and pressure functions,
but the column of the DataFrame where the data is held should be specified in
the function call as the ``key`` parameter. It is only applicable to the
PointIsotherm object.

::

    # Will return the enthalpy points of the desorption part of the
    # isotherm in the range if 10-40 kJ/mol as an indexed
    # pandas.Series

    isotherm.other_data(
        'enthalpy',
        branch = 'des',
        limits = (10, 40),
        indexed = True,
    )

For the PointIsotherm, a special
:meth:`~pygaps.core.pointisotherm.PointIsotherm.data` function returns all or
parts of the internal pandas.DataFrame. This can be used to inspect the data
directly or retrieve the DataFrame. To access the DataFrame directly, use the
``data_raw`` parameter.

::

    # Will return the pandas.DataFrame in the PointIsotherm
    # containing the adsorption branch

    isotherm.data(branch = 'ads')

    # Or access the underlying DataFrame

    isotherm.data_raw

Besides functions which give access to the internal datapoints, the isotherm
object can also return the value of pressure and loading at any point specified
by the user. To differentiate them from the functions returning internal data,
the functions have **_at** in their name.

In the ModelIsotherm class, the internal model is used to calculate the data
required. In the PointIsotherm class, the functions rely on an internal
interpolator, which uses the ``scipy.interpolate`` module. To optimize performance
working with isotherms, the interpolator is constructed in the same units as the
isotherm. If the user requests the return values in a different unit or basis,
they will be converted **after interpolation**. If a large number of requests
are to be made in a different unit or basis, it is better to first convert the
entire isotherm data in the required mode using the conversion functions.

The point methods are:

    - For loading: PointIsotherm :meth:`~pygaps.core.pointisotherm.PointIsotherm.loading_at`
      and ModelIsotherm :meth:`~pygaps.core.modelisotherm.ModelIsotherm.loading_at`

    - For pressure: PointIsotherm :meth:`~pygaps.core.pointisotherm.PointIsotherm.pressure_at`
      and ModelIsotherm :meth:`~pygaps.core.modelisotherm.ModelIsotherm.pressure_at`

The methods take parameters that describe the unit/mode of both the input
parameters and the output parameters.

::

    isotherm.loading_at(
        1,
        pressure_unit = 'atm',      # the pressure is passed in atmospheres (= 1 atm)
        branch='des',               # use the desorption branch of the isotherm
        loading_unit='mol',         # return the loading in mol
        material_basis='mass',      # return the adsorbent in mass basis
        material_unit='g',          # with a unit of g
    )

.. caution::

    Interpolation can be dangerous. pyGAPS does not implicitly allow
    interpolation outside the bounds of the data, although the user can force it
    to by passing an ``interp_fill`` parameter to the interpolating functions,
    usually if the isotherm is known to have reached the maximum adsorption
    plateau. Otherwise, the user is responsible for making sure the data is fit
    for purpose.


.. _isotherms-manual-convert:

Converting isotherm units, modes and basis
------------------------------------------

The PointIsotherm class also includes methods which can be used to permanently
convert the internal data. This is useful in certain cases, like when you want
to export the converted isotherm in an excel or json form. To understand how
units work in pyGAPS, see :ref:`this section <units-manual>`. If what is desired
is instead a slice of data in a particular unit, it is easier to get it directly
via the data access functions :ref:`above <isotherms-manual-data>`. The
conversion functions are:

    - :meth:`~pygaps.core.pointisotherm.PointIsotherm.convert` which can
      handle any conversion quantities.
    - :meth:`~pygaps.core.pointisotherm.PointIsotherm.convert_pressure` will
      permanently convert the unit or mode of pressure, for example from *bar*
      to *atm*.
    - :meth:`~pygaps.core.pointisotherm.PointIsotherm.convert_loading` will
      permanently convert the unit or basis loading of the isotherm, for example
      from molar in *mmol* to mass in *g*.
    - :meth:`~pygaps.core.pointisotherm.PointIsotherm.convert_material` will
      permanently convert the adsorbent material units or basis, for example
      from a mass basis in *g* to a mass basis in *kg*.

These conversion functions also reset the internal interpolator to the
particular unit and basis set requested. An example of how to convert the
pressure from an relative mode into an absolute mode, with units of *atm*:

::

    isotherm.convert_pressure(
        mode_to='absolute',
        unit_to='atm',
    )

Or a complicated conversion using the convenience function.

::

    isotherm.convert(
        pressure_mode='absolute',
        pressure_unit='atm',
        loading_basis='fraction',
        material_basis='volume',
        material_unit='cm3',
    )

.. note::

    The ModelIsotherm model parameters cannot be converted permanently to new
    states (although the data can still be obtained in that state by using the
    data functions). For fast calculations, it is better to first convert the
    data in the format required in a PointIsotherm, then generate the
    ModelIsotherm.

In order for pyGAPS to correctly convert between some modes and basis, the user
might have to take some extra steps to provide the required information for
these conversions (adsorbate molar mass for instance, which is calculated
automatically for known adsorbates).

Converting to relative pressures
::::::::::::::::::::::::::::::::

To convert an absolute pressure in a relative pressure, the critical pressure of
the gas at the experiment temperature must be known. Of course, this conversion
only works when the isotherm is measured in a subcritical regime. To calculate
the vapour pressure, pyGAPS relies on the ``CoolProp`` library. Therefore, the
name of the gas in a format CoolProp understands must be passed to the CoolProp
API. pyGAPS does this by having an internal list of adsorbates, which is loaded
from the database at the moment of import. The steps are:

    - User requests conversion from absolute to relative pressure for an
      isotherm object
    - The adsorbate name is taken from the isotherm parameter and matched
      against the name of an adsorbate in the internal list.
    - CoolProp calculates the critical point pressure for the adsorbate.
    - The relative pressure is calculated by dividing by the critical point
      pressure.

If using common gasses, the user should not be worried about this process, as an
extensive list of adsorbates is stored in the internal database. However, if a
new adsorbate is to be used, the user might have to add it to the master list
themselves. For more info on this see the
:ref:`Adsorbate class manual <adsorbate-manual>`

Converting loading basis
::::::::::::::::::::::::

For loading basis conversions, the relationship between the two bases must be
known. Between a mass and a volume basis, density of the material is needed and
between mass and molar basis, the specific molar mass of the adsorbent material
is required.

For each specific adsorbate, these properties are also calculated using
CoolProp. The molar mass is independent of any variables, while the density is a
function of temperature. Here, it is assumed that the density is that of a gas,
and therefore converting an isotherm to a volumetric loading basis gives you the
volume that the gas adsorbed would occupy at the isotherm temperature.

Converting material basis
::::::::::::::::::::::::::

For the material basis, the same properties (density and molar mass) are
required, depending on the conversion requested. These properties are specific
to each material and cannot be calculated. Therefore, they have to be specified
by the user.

Similar to the list of adsorbates described above, pyGAPS includes a list of
samples, stored as Material objects. This is populated at import-time from the
database. It is this list from where the required properties are retrieved.

To specify the properties, the user must create a Material instance, populate it
with the density value and the molar mass, and then upload it either to the
internal list or the internal database. For more info on this see the
:ref:`Material class manual <material-manual>`


.. _isotherms-manual-unique:

Ensuring isotherm uniqueness
----------------------------

Each PointIsotherm can generate an id. This id is a fingerprint of the isotherm
and should be unique to each object. The id string is an md5 hash of the
isotherms parameters and data/model. The id is also used internally for database
storage.

The id is generated automatically every time the isotherm.iso_id is called. The
hashlib.md5 function is used to obtain a hash of the json string. It can be read
as:

::

    point_isotherm.iso_id

.. note::

    Both ModelIsotherm and PointIsotherm classes are supported and contain an
    ID. They are based on different data so cannot be compared.


.. _isotherms-manual-export:

Exporting an isotherm
---------------------

To export an isotherm, pyGAPS provides several choices to the user:

    - Converting the isotherm in a JSON format, using the
      :meth:`~pygaps.parsing.json.isotherm_to_json` function
    - Converting the isotherm to a CSV file, using the
      :meth:`~pygaps.parsing.csv.isotherm_to_csv` function
    - Converting the isotherm to an Excel file, using the
      :meth:`~pygaps.parsing.excel.isotherm_to_xl` function
    - Uploading the isotherm to a sqlite database, either using the internal
      database or a user-specified external one. For more info on interacting
      with the sqlite database see the respective :ref:`section<sqlite-manual>`
      of the manual.

More info can be found on the respective parsing pages of the manual.
