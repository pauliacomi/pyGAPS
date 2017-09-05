"""
This module contains the t-plot calculation
"""

import warnings
from itertools import groupby

import matplotlib.pyplot as plt
import numpy
import scipy

from ..classes.adsorbate import Adsorbate
from ..classes.isotherm import Isotherm
from ..graphing.calcgraph import plot_tp
from .thickness_models import _THICKNESS_MODELS
from .thickness_models import thickness_halsey
from .thickness_models import thickness_harkins_jura
from .thickness_models import thickness_isotherm


def t_plot(isotherm, thickness_model, custom_model=False, limits=None, verbose=False):
    """
    Calculates the external surface area and adsorbed volume
    using the t-plot method

    Parameters
    ----------
    isotherm : PointIsotherm
        the isotherm of which to calculate the t-plot parameters
    thickness_model : str
        name of the thickness model to use
    custom_model : bool, optional
        if true, permits a custom thickness model to be supplied,
        starting from an isotherm or a custom thickness function
    limits : [:obj:`float`, :obj:`float`], optional
        manual limits for region selection
    verbose : bool, optional
        prints extra information and plots graphs of the calculation

    Returns
    -------
    list
        a list of dictionaries containing the calculated parameters for each
        straight section, with each dictionary of the form:

            - ``section``(array): the points of the plot chosen for the line
            - ``area``(float) : calculated surface area, from the section parameters
            - ``adsorbed_volume``(float) : the amount adsorbed in the pores as calculated
                per section
            - ``slope``(float) : slope of the straight trendline fixed through the region
            - ``intercept``(float) : intercept of the straight trendline through the region
            - ``corr_coef``(float) : correlation coefficient of the linear region

    Notes
    -----
    *Usage*

    Pass an isotherm object to the function to have the t-plot method applied to it.
    The ``thickness_model`` parameter is a string which names the thickness equation which
    should be used. Alternatively, a user can implement their own thickness model, either
    as an experimental isotherm or a function which describes the adsorbed layer. In that
    case, set the ``custom_model`` flag to ``True`` and instead of a string, pass the
    Isotherm object or the callable function as the ``thickness_model`` parameter
    The ``limits`` parameter takes the form of an array of two numbers, which are the
    upper and lower limits of the section which should be taken for analysis.

    *Description*

    The t-plot method [#]_ attempts to relate the adsorption on a material with an ideal
    curve which describes the thickness of the adsorbed layer on a surface. A plot is
    constructed, with the isotherm  loading data is plotted versus thickness values obtained
    therough the model.
    It stands to reason that, in the case that the experimental adsorption curve follows
    the model, a straight line will be obtained with its intercept through the origin.
    However, since in most cases there are differences between adsorption in the pores
    and ideal surface adsorption, the t-plot will deviate and form features which can
    be analysed to describe the material characteristics.

        - a sharp vertical deviation will indicate condensation in a type of pore
        - a gradual slope will indicate adsorption on the wall of a particular pore

    The slope of the linear section can be used to calculate the area where the adsorption
    is taking place. If it is of a linear region at the start of the curve, it will represent
    the total surface area of the material. If at the end of the curve, it will instead
    represent external surface area of the sample. The formula to calculate the area is:

    .. math::

        A = \\frac{s M_m}{\\rho_{l}}

    where :math:`\\rho_{l}` is the liquid density of the adsorbate at experimental
    conditions

    If the region selected is after a vertical deviation, the intercept of the line
    will no longer pass through the origin. This intercept be used to calculate the
    pore volume through the following equation:

    .. math::

        V_{ads} = \\frac{i M_m}{\\rho_{l}}


    *Limitations*

    Since the t-plot method is taking the differences between the isotherm and a model,
    care must be taken to ensure that the model actually describes the thickness of a
    layer of adsorbate on the surface of the adsorbent. This is more difficult than it
    appears as no universal thickness curve exists. When selecting a thickness model,
    make sure that it is applicable to both the material and the adsorbate.
    Interactions at loadings that occur on the t-plot lower than the monolayer
    thickness do not have any physical meaning.


    References
    ----------
    .. [#] “Studies on Pore Systems in Catalysts V. The t Method”,
       B. C. Lippens and J. H. de Boer, J. Catalysis, 4, 319 (1965)

    """

    # Function parameter checks
    if isotherm.mode_adsorbent != "mass":
        raise Exception("The isotherm must be in per mass of adsorbent."
                        "First convert it using implicit functions")
    if isotherm.mode_pressure != "relative":
        raise Exception("The isotherm must be in relative pressure mode."
                        "First convert it using implicit functions")
    if thickness_model is None:
        raise Exception("Specify a model to generate the thickness curve"
                        " e.g. thickness_model=\"Halsey\"")
    if thickness_model not in _THICKNESS_MODELS:
        raise Exception("Model {} not an option for t-plot.".format(thickness_model),
                        "Available models are {}".format(_THICKNESS_MODELS))

    # Get adsorbate properties
    adsorbate = Adsorbate.from_list(isotherm.gas)
    molar_mass = adsorbate.molar_mass()
    liquid_density = adsorbate.liquid_density(isotherm.t_exp)

    # Read data in
    loading = isotherm.loading_ads(unit='mol')
    pressure = isotherm.pressure_ads()

    # Thickness model definitions
    if not custom_model:
        if thickness_model == "Halsey":
            t_model = thickness_halsey
        elif thickness_model == "Harkins/Jura":
            t_model = thickness_harkins_jura
    elif issubclass(thickness_model, Isotherm):
        t_model = thickness_isotherm(thickness_model)
    else:
        t_model = thickness_model

    # Call t-plot function
    results, t_curve = t_plot_raw(
        loading, pressure, t_model, liquid_density, molar_mass, limits)

    result_dict = {
        't_curve': t_curve,
        'results': results,
    }

    if verbose:
        if len(results) == 0:
            print('Could not find linear regions, attempt a manual limit')
        else:
            for index, result in enumerate(results):
                print("For linear region {0}".format(index))
                print("The slope is {0} and the intercept is {1}"
                      " With a correlation coefficient of {2}".format(
                          round(result.get('slope'), 4),
                          round(result.get('intercept'), 4),
                          round(result.get('corr_coef'), 4)
                      ))
                print("The adsorbed volume is {0} and the area is {1}".format(
                    round(result.get('adsorbed_volume'), 4),
                    round(result.get('area'), 4)
                ))
            fig = plt.figure()
            plot_tp(fig, t_curve, loading, results)

    return result_dict


def t_plot_raw(loading, pressure, thickness_model, liquid_density, adsorbate_molar_mass, limits=None):
    """
    This is a 'bare-bones' function to calculate t-plot parameters which is
    designed as a low-level alternative to the main function.
    Designed for advanced use, its parameters have to be manually specified.

    Parameters
    ----------
    loading : array
        in mol/g
    pressure : array
        relative
    thickness_model : callable
        function which which returns the thickenss of the adsorbed layer at a pressure p
    liquid_density : float
        density of the adsorbate in the adsorbed state, in g/cm3
    adsorbate_molar_mass : float
        molar mass of the adsorbate, in g/mol

    Returns
    -------
    results : dict
        A dictionary of results with the following components

        - ``section``(array): the points of the plot chosen for the line
        - ``area``(float) : calculated surface area, from the section parameters
        - ``adsorbed_volume``(float) : the amount adsorbed in the pores as calculated
            per section
        - ``slope``(float) : slope of the straight trendline fixed through the region
        - ``intercept``(float) : intercept of the straight trendline through the region
        - ``corr_coef``(float) : correlation coefficient of the linear region

    thickness_curve : array
        The generated thickness curve at each point using the thickness model

    """

    if len(pressure) != len(loading):
        raise Exception("The length of the pressure and loading arrays"
                        " do not match")

    # Generate the thickness curve for the pressure points
    thickness_curve = numpy.array(list(map(thickness_model, pressure)))

    results = []

    # If limits are not None, then the user requested specific limits
    if limits is not None:
        section = (thickness_curve > limits[0]) & (thickness_curve < limits[1])
        results.append(t_plot_parameters(thickness_curve,
                                         section, loading,
                                         adsorbate_molar_mass, liquid_density))

    # If not, attempt to find limits manually
    else:
        # Now we need to find the linear regions in the t-plot for the
        # assesment of surface area.
        linear_sections = find_linear_sections(loading)

        # For each section we compute the linear fit
        for section in linear_sections:
            params = t_plot_parameters(thickness_curve,
                                       section, loading,
                                       adsorbate_molar_mass, liquid_density)
            if params is not None:
                results.append(params)

        if len(results) == 0:
            warnings.warn(
                'Could not find linear regions, attempt a manual limit')

    return results, thickness_curve


def find_linear_sections(loading):
    """Finds all sections of the t-plot which are linear"""
    linear_sections = []

    # To do this we calculate the second
    # derivative of the thickness plot
    second_deriv = numpy.gradient(numpy.gradient(loading))

    # We then find the points close to zero in the second derivative
    # These are the points where the graph is linear
    margin = 0.00001 / (len(loading) * max(loading))
    close_zero = numpy.abs(second_deriv) < margin

    # This snippet divides the the points in linear sections
    # where linearity holds at least for a number of measurements
    continuous_p = 3

    for k, g in groupby(enumerate(close_zero), lambda x: x[1]):
        group = list(g)
        if len(group) > continuous_p and k:
            linear_sections.append(list(map(lambda x: x[0], group)))

    return linear_sections


def t_plot_parameters(thickness_curve, section, loading, molar_mass, liquid_density):
    """Calculates the parameters from a linear section of the t-plot"""

    slope, intercept, corr_coef, p, stderr = scipy.stats.linregress(
        thickness_curve[section],
        loading[section])

    # Check if slope is good

    if slope * (max(thickness_curve) / max(loading)) < 3:
        adsorbed_volume = intercept * molar_mass / liquid_density
        area = slope * molar_mass / liquid_density * 1000

        result_dict = {
            'section': section,
            'slope': slope,
            'intercept': intercept,
            'corr_coef': corr_coef,
            'adsorbed_volume': adsorbed_volume,
            'area': area,
        }

        return result_dict
    return
