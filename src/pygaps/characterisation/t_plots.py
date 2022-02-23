"""This module contains the t-plot calculation."""

import typing as t

import numpy
from scipy import stats

from pygaps import logger
from pygaps.characterisation.models_thickness import get_thickness_model
from pygaps.core.adsorbate import Adsorbate
from pygaps.core.modelisotherm import ModelIsotherm
from pygaps.core.pointisotherm import PointIsotherm
from pygaps.utilities.exceptions import CalculationError
from pygaps.utilities.exceptions import ParameterError
from pygaps.utilities.exceptions import pgError
from pygaps.utilities.math_utilities import find_linear_sections


def t_plot(
    isotherm: "PointIsotherm | ModelIsotherm",
    thickness_model:
    "str | PointIsotherm | ModelIsotherm | t.Callable[[float], float]" = 'Harkins/Jura',
    branch: str = 'ads',
    t_limits: "tuple[float, float]" = None,
    verbose: bool = False,
):
    r"""
    Calculate surface area and pore volume using a t-plot.

    The ``thickness_model`` parameter is a string which names the thickness
    equation which should be used. Alternatively, a user can implement their own
    thickness model, either as an Isotherm or a function which describes the
    adsorbed layer. In that case, instead of a string, pass the Isotherm object
    or the callable function as the ``thickness_model`` parameter. The
    ``t_limits`` specifies the upper and lower limits of the thickness section
    which should be taken for analysis.

    Parameters
    ----------
    isotherm : PointIsotherm, ModelIsotherm
        The isotherm of which to calculate the t-plot parameters.
    thickness_model : str, PointIsotherm, ModelIsotherm, `callable`, optional
        Name of the thickness model to use. Defaults to the Harkins and Jura
        thickness curve.
    branch : {'ads', 'des'}, optional
        Branch of the isotherm to use. It defaults to adsorption.
    t_limits : tuple[float, float], optional
        Thickness range in which to perform the calculation.
    verbose : bool, optional
        Prints extra information and plots graphs of the calculation.

    Returns
    -------
    dict
        A dictionary containing the t-plot curve, as well as a list of dictionaries
        with calculated parameters for each straight section. The basis of these
        results will be derived from the basis of the isotherm (per mass or per
        volume of adsorbent):

        - ``thickness curve`` (list) : Calculated thickness curve
        - ``results`` (list of dicts):

          - ``section`` (array) : the points of the plot chosen for the line
          - ``area`` (float) : calculated surface area, from the section parameters
          - ``adsorbed_volume`` (float) : the amount adsorbed in the pores as calculated per section
          - ``slope`` (float) : slope of the straight trendline fixed through the region
          - ``intercept`` (float) : intercept of the straight trendline through the region
          - ``corr_coef`` (float) : correlation coefficient of the linear region

    Raises
    ------
    ParameterError
        When something is wrong with the function parameters.
    CalculationError
        When the calculation itself fails.

    Notes
    -----
    *Description*

    The t-plot method [#]_ attempts to relate the adsorption on a material with an ideal
    curve which describes the thickness of the adsorbed layer on a surface. A plot is
    constructed, where the isotherm loading data is plotted versus thickness values obtained
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
    represent external surface area of the material. The formula to calculate the area is:

    .. math::

        A = \frac{s M_m}{\rho_{l}}

    where :math:`\rho_{l}` is the liquid density of the adsorbate at experimental
    conditions

    If the region selected is after a vertical deviation, the intercept of the line
    will no longer pass through the origin. This intercept be used to calculate the
    pore volume through the following equation:

    .. math::

        V_{ads} = \frac{i M_m}{\rho_{l}}


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

    See Also
    --------
    pygaps.characterisation.t_plots.t_plot_raw : low level method

    """
    # Function parameter checks
    if thickness_model is None:
        raise ParameterError(
            "Specify a model to generate the thickness curve"
            " e.g. thickness_model=\"Halsey\""
        )

    # Get adsorbate properties
    adsorbate = Adsorbate.find(isotherm.adsorbate)
    molar_mass = adsorbate.molar_mass()
    liquid_density = adsorbate.liquid_density(isotherm.temperature)

    # Read data in
    loading = isotherm.loading(
        branch=branch,
        loading_unit='mol',
        loading_basis='molar',
    )
    try:
        pressure = isotherm.pressure(
            branch=branch,
            pressure_mode='relative',
        )
    except pgError:
        raise CalculationError(
            "The isotherm cannot be converted to a relative basis. "
            "Is your isotherm supercritical?"
        )

    # If on an desorption branch, data will be reversed
    if branch == 'des':
        loading = loading[::-1]
        pressure = pressure[::-1]

    # Get thickness model
    t_model = get_thickness_model(thickness_model)

    # Call t-plot function
    results, t_curve = t_plot_raw(
        loading,
        pressure,
        t_model,
        liquid_density,
        molar_mass,
        t_limits,
    )

    if verbose:
        if not results:
            logger.info("Could not find linear regions, attempt a manual limit.")
        else:
            for index, result in enumerate(results):
                logger.info(f"For linear region {index + 1}")
                logger.info(
                    f"The slope is {result.get('slope'):.4g} "
                    f"and the intercept is {result.get('intercept'):.4g}, "
                    f"with a correlation coefficient of {result.get('corr_coef'):.4g}"
                )
                logger.info(
                    f"The adsorbed volume is {result.get('adsorbed_volume'):.3g} cm3/{isotherm.material_unit} "
                    f"and the area is {result.get('area'):.4g} m2/{isotherm.material_unit}"
                )

            from pygaps.graphing.calc_graphs import tp_plot
            tp_plot(t_curve, loading, results)

    return {
        't_curve': t_curve,
        'results': results,
    }


def t_plot_raw(
    loading: "list[float]",
    pressure: "list[float]",
    thickness_model: t.Callable[[float], float],
    liquid_density: float,
    adsorbate_molar_mass: float,
    t_limits: "tuple[float,float]" = None,
):
    """
    Calculate surface area and pore volume using a t-plot.

    This is a 'bare-bones' function to calculate t-plot parameters which is
    designed as a low-level alternative to the main function.
    Designed for advanced use, its parameters have to be manually specified.

    Parameters
    ----------
    loading : list[float]
        Amount adsorbed at the surface, mol/material.
    pressure : list[float]
        Relative pressure corresponding to the loading.
    thickness_model : callable[[float], float]
        Function which which returns the thickness of the adsorbed layer at a pressure p.
    liquid_density : float
        Density of the adsorbate in the adsorbed state, in g/cm3.
    adsorbate_molar_mass : float
        Molar mass of the adsorbate, in g/mol.
    t_limits : tuple[float, float], optional
        Thickness range in which to perform the calculation.

    Returns
    -------
    results : list
        A list of dictionaries with the following components:

        - ``section`` (array) : the indices of points chosen for the line fit
        - ``area`` (float) : calculated surface area, from the section parameters
        - ``adsorbed_volume`` (float) : the amount adsorbed in the pores as
          calculated per section
        - ``slope`` (float) : slope of the straight trendline fixed through the region
        - ``intercept`` (float) : intercept of the straight trendline through the region
        - ``corr_coef`` (float) : correlation coefficient of the linear region

    thickness_curve : array
        The generated thickness curve at each point using the thickness model.

    """
    # Check lengths
    if len(pressure) == 0:
        raise ParameterError("Empty input values!")
    if len(pressure) != len(loading):
        raise ParameterError("The length of the pressure and loading arrays do not match.")

    # Ensure numpy arrays, if not already
    loading = numpy.asarray(loading)
    pressure = numpy.asarray(pressure)

    # Generate the thickness curve for the pressure points
    thickness_curve = thickness_model(pressure)

    results = []

    # If limits are not None, then the user requested specific limits
    if t_limits is not None:
        section = numpy.flatnonzero((thickness_curve > t_limits[0])
                                    & (thickness_curve < t_limits[1]))
        result = t_plot_parameters(
            thickness_curve,
            loading,
            section,
            adsorbate_molar_mass,
            liquid_density,
        )
        if result:
            results.append(result)
        else:
            logger.warning("Could not fit a linear regression.")

    # If not, attempt to find limits manually
    else:
        # Now we need to find the linear regions in the t-plot for the
        # assessment of surface area.
        linear_sections = find_linear_sections(thickness_curve, loading)

        # For each section we compute the linear fit
        for section in linear_sections:
            result = t_plot_parameters(
                thickness_curve,
                loading,
                section,
                adsorbate_molar_mass,
                liquid_density,
            )
            if result:
                results.append(result)

        if not results:
            logger.warning("Could not determine linear regions, attempt a manual limit.")

    return results, thickness_curve


def t_plot_parameters(
    thickness_curve: list,
    loading: list,
    section: slice,
    molar_mass: float,
    liquid_density: float,
):
    """Calculate the parameters from a linear section of the t-plot."""

    slope, intercept, corr_coef, p, stderr = stats.linregress(
        thickness_curve[section], loading[section]
    )

    # Check if slope is good

    if slope * (max(thickness_curve) / max(loading)) < 3:
        adsorbed_volume = intercept * molar_mass / liquid_density
        area = slope * molar_mass / liquid_density * 1000

        return {
            'section': section,
            'slope': slope,
            'intercept': intercept,
            'corr_coef': corr_coef,
            'adsorbed_volume': adsorbed_volume,
            'area': area,
        }

    return None
