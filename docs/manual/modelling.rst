.. _modelling-manual:

Isotherm modelling
==================

.. _modelling-general:

Overview
--------

In adsorption, a model is a physical or empirical relationship
between adsorbate pressure and its loading.
Therefore it can be expressed as a function:

.. math::

    n = f(p, ...)

    or

    p = f(n, ...)

Many types of models have been developed which attempt to
describe the phenomenon of adsorption. While none can accurately describe
all situations, different behaviours, interactions and pressure
ranges, the data can be fitted reliably if a suitable model is chosen.

It is left to the best judgement of the user when to apply a specific model.


.. _modelling-implementation:

Modelling in pyGAPS
-------------------

In pyGAPS, the :meth:`~pygaps.core.modelisotherm.ModelIsotherm` is the
class which contains all the model parameters. While it is instantiated
using discrete data, it does not store it directly. Another principal
difference from the PointIsotherm class is that, while the former can
contain both the adsorption and desorption branch of the physical
isotherm, the latter
contains a model for only one branch, determined at initialisation.

Currently the models implemented are:

    - :mod:`~pygaps.modelling.henry` - Henry
    - :mod:`~pygaps.modelling.langmuir` - Langmuir
    - :mod:`~pygaps.modelling.dslangmuir` -
      Double Site Langmuir
    - :mod:`~pygaps.modelling.tslangmuir` -
      Triple Site Langmuir
    - :mod:`~pygaps.modelling.bet` -
      Brunnauer-Emmet-Teller (BET)
    - :mod:`~pygaps.modelling.gab` -
      Guggenheim-Anderson-de Boer (GAB)
    - :mod:`~pygaps.modelling.freundlich` - Freundlich
    - :mod:`~pygaps.modelling.dr` -
      Dubinin-Radushkevitch (DR)
    - :mod:`~pygaps.modelling.da` - Dubinin-Astakov (DA)
    - :mod:`~pygaps.modelling.quadratic` - Quadratic
    - :mod:`~pygaps.modelling.temkinapprox` -
      Temkin Approximation
    - :mod:`~pygaps.modelling.toth` - Toth
    - :mod:`~pygaps.modelling.jensenseaton` - Jensen-Seaton
    - :mod:`~pygaps.modelling.wvst` -
      Wilson Vacancy Solution Theory (W-VST)
    - :mod:`~pygaps.modelling.fhvst` -
      Flory-Huggins Vacancy Solution Theory (FH-VST)

For an explanation of each model, visit its respective reference page.
Custom models can also be added to the list if you are willing to write them.
See the procedure :ref:`below <modelling-custom>`.


.. _modelling-examples:

Working with models
-------------------

A ModelIsotherm can be created from raw values, as detailed
in the :ref:`isotherms section <isotherms-manual-create>`.
However, for most use case scenarios, the user will want
to create a ModelIsotherm starting from a previously created
PointIsotherm class.

To do so, the class includes a specific method,
:meth:`~pygaps.core.modelisotherm.ModelIsotherm.from_pointisotherm`,
which allows a PointIsotherm to be used. An example is:

::

    model_isotherm = pygaps.ModelIsotherm.from_pointisotherm(
        point_isotherm,
        branch='ads'
        model='Henry',
    )

Alternatively, the ``guess_model`` parameter allows for the
ModelIsotherm to attempt to fit some of the available models
and then return the best fitting one. This mode should
be used carefully, as there's no guarantee that the the best
fitting model is the one with any physical significance.
It it also worth noting that, since a lot of
models may be evaluated, this option will take significantly more
resources than simply specifying the model manually.
As a consequence, some models which require
a lot of overhead, such as the
virial model, have been excluded from this option.

Alternatively, the user can specify a list of models
to the ``guess_model`` parameter. An example:

::

    # Attempting all basic models
    model_isotherm = pygaps.ModelIsotherm.from_pointisotherm(
        point_isotherm,
        branch='des'
        guess_model='all',
    )

    # With a subset of models instead
    model_isotherm = pygaps.ModelIsotherm.from_pointisotherm(
        point_isotherm,
        branch='des'
        guess_model=['Henry', 'Langmuir', 'BET', 'Virial'],
    )

Once the a ModelIsotherm is generated, it can be used as a regular
PointIsotherm, as it contains the same common methods.
Some slight differences exist:

    - ModelIsotherms do not contain the ``data`` function,
      as they contain no data.
      Instead the user can access the ``model.params``
      property, to get a dictionary of the
      calculated model parameters.

    - The ``loading`` and ``pressure`` functions will return
      equidistant points over the whole range of the isotherm
      instead of returning actual datapoints.

    - While loading is calculated directly in most cases,
      in others it has to be
      computed using numerical fitting methods. Depending on
      the model, the minimisation may or may not converge.


.. _modelling-compare:

Comparing models and data
-------------------------

The ModelIsotherms created can easily be plotted using
the same function as PointIsotherms. For example, to graphically
compare a model and an experimental isotherm:

::

    pygaps.plot_iso([model_isotherm, point_isotherm])


One may notice that the loading is calculated at different
pressure points from the PointIsotherm. This is done to keep
the plotting function general. If the user wants the pressure points to be
identical, a separate approach is needed.

First, a new PointIsotherm must be created from the ModelIsotherm.
This essentially uses the internal model of the ModelIsotherm
isotherm to calculate loading at the points the user
specifies, then save them in a DataFrame. This can be achieved with the
:meth:`~pygaps.core.pointisotherm.PointIsotherm.from_modelisotherm` method.

The class method takes as parameters a ModelIsotherm, as well as
a ``pressure_points`` keyword. This can be used to specify the array
of points where the loading is calculated. If a PointIsotherm is passed
instead, the loading is calculated at each of the points of the
isotherm.

::

    # Create the model isotherm
    model_isotherm = pygaps.ModelIsotherm.from_pointisotherm(
        point_isotherm,
        guess_model=True,
    )

    # Now create a new PointIsotherm from the model
    new_point_isotherm = pygaps.PointIsotherm.from_modelisotherm(
        model_isotherm,
        pressure_points=point_isotherm
    )

    # Direct comparison is now possible
    pygaps.plot_iso([new_point_isotherm, point_isotherm])


.. _modelling-manual-examples:

Modelling examples
------------------

Check out in Jupyter notebook in the `examples <../examples/modelling.ipynb>`_ section


.. _modelling-custom:

Custom models
-------------

Custom models can be implemented as well. In the `./modelling/`
folder, there is a model template (`IsothermBaseModel` in *base_model.py*)
which contains the functions which should be inherited by
a custom model.

The things to be specified are the following:

    - The model name.
    - A dictionary with the model parameters names and possible bounds.
    - A function that returns an initial guess for the
      model parameters (``initial_guess()``).
    - A fitting function that determines the model parameters
      starting from the loading and pressure data (``fit()``).
      Alternatively, the template fitting function can be used
      if inherited.
    - Functions that return the loading and pressure
      calculated from the model parameters (``loading(pressure)``
      and ``pressure(loading)``). These can be calculated analytically
      or numerically.
    - A function which returns the spreading pressure, if the model
      is to be used for IAST calculations (``spreading_pressure(pressure)``).

Once the model is written, it should be added to the list of usable models.
This can be found in the */pygaps/modelling/__init__.py* file.

Don't forget to write some tests to make sure that the model works as
intended. You can find the current parametrised tests in
*tests/modelling/test_models_isotherm.py*.
