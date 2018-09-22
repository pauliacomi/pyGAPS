"""
This module contains the t-plot calculation.
"""

import warnings

import numpy
import scipy

from ..classes.adsorbate import Adsorbate
from ..graphing.calcgraph import plot_tp
from ..utilities.exceptions import ParameterError
from ..utilities.math_utilities import find_linear_sections
from .models_thickness import get_thickness_model


def t_plot(isotherm, thickness_model='Harkins/Jura', limits=None, verbose=False):
    """
    Calculates the external surface area and adsorbed volume
    using the t-plot method.


    Pass an isotherm object to the function to have the t-plot method applied to it.
    The ``thickness_model`` parameter is a string which names the thickness equation which
    should be used. Alternatively, a user can implement their own thickness model, either
    as an experimental isotherm or a function which describes the adsorbed layer. In that
    case, instead of a string, pass the Isotherm object or the callable function as the
    ``thickness_model`` parameter. The ``limits`` parameter takes the form of an array of
    two numbers, which are the upper and lower limits of the section which should be taken
    for analysis.

    Parameters
    ----------
    isotherm : PointIsotherm
        The isotherm of which to calculate the t-plot parameters.
    thickness_model : obj(`str`) or obj(`Isotherm`) or obj(`callable`), optional
        Name of the thickness model to use. Defaults to the Harkins and Jura
        thickness curve.
    limits : [float, float], optional
        Manual limits for region selection.
    verbose : bool, optional
        Prints extra information and plots graphs of the calculation.

    Returns
    -------
    list
        a list of dictionaries containing the calculated parameters for each
        straight section, with each dictionary of the form. The basis of these
        results will be derived from the basis of the isotherm (per mass or per
        volume of adsorbent)::

            - ``section(array)`` : the points of the plot chosen for the line
            - ``area(float)`` : calculated surface area, from the section parameters
            - ``adsorbed_volume(float)`` : the amount adsorbed in the pores as calculated
              per section
            - ``slope(float)`` : slope of the straight trendline fixed through the region
            - ``intercept(float)`` : intercept of the straight trendline through the region
            - ``corr_coef(float)`` : correlation coefficient of the linear region


    Notes
    -----
    *Description*

    The t-plot method [#]_ attempts to relate the adsorption on a material with an ideal
    curve which describes the thickness of the adsorbed layer on a surface. A plot is
    constructed, with the isotherm  loading data is plotted versus thickness values obtained
    through the model.
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
    if thickness_model is None:
        raise ParameterError("Specify a model to generate the thickness curve"
                             " e.g. thickness_model=\"Halsey\"")

    # Get adsorbate properties
    adsorbate = Adsorbate.from_list(isotherm.adsorbate)
    molar_mass = adsorbate.molar_mass()
    liquid_density = adsorbate.liquid_density(isotherm.t_exp)

    # Read data in
    loading = isotherm.loading(branch='ads',
                               loading_unit='mol',
                               loading_basis='molar')
    pressure = isotherm.pressure(branch='ads',
                                 pressure_mode='relative')

    # Get thickness model
    t_model = get_thickness_model(thickness_model)

    # Call t-plot function
    results, t_curve = t_plot_raw(
        loading, pressure, t_model, liquid_density, molar_mass, limits)

    result_dict = {
        't_curve': t_curve,
        'results': results,
    }

    if verbose:
        if not results:
            print('Could not find linear regions, attempt a manual limit')
        else:
            for index, result in enumerate(results):
                print("For linear region {0}".format(index + 1))
                print("The slope is {0} and the intercept is {1}"
                      ", with a correlation coefficient of {2}".format(
                          round(result.get('slope'), 4),
                          round(result.get('intercept'), 4),
                          round(result.get('corr_coef'), 4)
                      ))
                print("The adsorbed volume is {} cm3/{} and the area is {} m2/{}".format(
                    round(result.get('adsorbed_volume'), 4),
                    isotherm.adsorbent_unit,
                    round(result.get('area'), 3),
                    isotherm.adsorbent_unit,
                ))

            plot_tp(t_curve, loading, results)

    return result_dict


def t_plot_raw(loading, pressure, thickness_model, liquid_density, adsorbate_molar_mass, limits=None):
    """
    This is a 'bare-bones' function to calculate t-plot parameters which is
    designed as a low-level alternative to the main function.
    Designed for advanced use, its parameters have to be manually specified.

    Parameters
    ----------
    loading : array
        In mol/g.
    pressure : array
        Relative.
    thickness_model : callable
        Function which which returns the thickness of the adsorbed layer at a pressure p.
    liquid_density : float
        Density of the adsorbate in the adsorbed state, in g/cm3.
    adsorbate_molar_mass : float
        Molar mass of the adsorbate, in g/mol.
    limits : [float, float], optional
        Manual limits for region selection.

    Returns
    -------
    results : dict
        A dictionary of results with the following components

            - ``section(array)`` : the points of the plot chosen for the line
            - ``area(float)`` : calculated surface area, from the section parameters
            - ``adsorbed_volume(float)`` : the amount adsorbed in the pores as calculated
              per section
            - ``slope(float)`` : slope of the straight trendline fixed through the region
            - ``intercept(float)`` : intercept of the straight trendline through the region
            - ``corr_coef(float)`` : correlation coefficient of the linear region

    thickness_curve : array
        The generated thickness curve at each point using the thickness model.

    """

    if len(pressure) != len(loading):
        raise ParameterError("The length of the pressure and loading arrays"
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
        # assessment of surface area.
        linear_sections = find_linear_sections(thickness_curve, loading)

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
