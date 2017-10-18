.. _modelling-manual:

Isotherm modelling
==================

.. _modelling-general:

Overview
--------

In adsorption, a model is a physical or empirical relationship between adsorbate pressure
and its loading. Therefore it can be expressed as a function:

.. math::

    n = f(p, ...)

Many types of models have been developed which attempt to describe the phenomenon of adsorption.
While neither can accurately describe all situations, different behaviours, interactions and pressure
ranges can be fitted quite reliably if a suitable model is chosen.

It is left to the best judgement of the user when to apply a specific model.


.. _modelling-implementation:

Modelling in pyGAPS
-------------------

In pyGAPS, the :meth:`~pygaps.classes.modelisotherm.ModelIsotherm` is the
class which contains all the model parameters. While it is instantiated
using discrete data, it does not store it. Another principal difference
from the PointIsotherm class is that, while the former can contain both
the adsorption and desorption branch of the physical isotherm, the latter
contains a model for only one branch, determined at initialisation.

Currently only several models are implemented, from the pyIAST code.

    - Henry
    - BET
    - Langmuir
    - Double Site Langmuir
    - Triple Site Langmuir
    - Quadratic
    - Temkin Approximation

Further models, as well as user-customisable versions will be added when the
modelling functionality is re-written in a latter version.



.. _modelling-examples:

Working with models
-------------------

A ModelIsotherm can be created from raw values, as detailed in the :ref:`isotherms
section <isotherms-manual-create>`. For most use case scenarios, the user will want
to create a ModelIsotherm starting from a previously created PointIsotherm class.

To do so, the class includes a specific method,
:meth:`~pygaps.classes.modelisotherm.ModelIsotherm.from_pointisotherm`,
which allows a PointIsotherm to be passed in. An example is:

::

    model_isotherm = pygaps.ModelIsotherm.from_pointisotherm(
        point_isotherm,
        branch='ads'
        model='Henry',
    )

Alternatively, the ``guess_model`` parameter allows for the ModelIsotherm to attempt
to fit all available models and then return the best fitting one. This mode should
be used carefully, as there's no guarantee that the the best fitting model is the
one with any physical significance. It it also worth noting that, since all available
models are first calculated, this option will take significantly more resources than
simply specifying the model manually. An example:

::

    model_isotherm = pygaps.ModelIsotherm.from_pointisotherm(
        point_isotherm,
        branch='des'
        guess_model=True,
    )

Once the a ModelIsotherm is generated, it can be used as a regular PointIsotherm, as
it contains the same common methods. Some slight differences exist:

    - ModelIsotherms do not contain the ``data`` function, as they contain no data.
      Instead the user can access the ``branch`` property, to get a dictionary of the
      calculated model parameters.

    - The ``loading`` and ``pressure`` functions will return equidistant points over the
      whole range of the isotherm instead of returning actual datapoints.

    - The ``pressure_at`` function has to return an inverse of the internal model. In
      certain cases, this is infeasible.




.. _modelling-compare:

Comparing models and data
-------------------------

The ModelIsotherms created can easily be plotted using the same function as PointIsotherms.
For example, to compare graphically a model and an experimental isotherm:

::

    pygaps.plot_iso([model_isotherm, point_isotherm])


One may notice that the loading is calculated at different pressure points from the PointIsotherm.
This is done to keep the plotting function general. If the user wants the pressure points to be
identical, a separate approach is needed.

First, a new PointIsotherm must be created from the ModelIsotherm. This essentially uses the
internal model of the ModelIsotherm isotherm to calculate loading at the points the user
specifies, then save them in a DataFrame. This can be achieved with the
:meth:`~pygaps.classes.pointisotherm.PointIsotherm.from_modelisotherm` method.

The class method takes as parameters a ModelIsotherm, as well as a ``pressure_points`` keyword.
This can be used to specify the array of points where the loading is calculated. If a
PointIsotherm is passed instead, the loading is calculated at each of the points of the
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


