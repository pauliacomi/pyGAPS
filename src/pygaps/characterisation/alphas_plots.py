"""This module contains the alpha-s calculation."""

import numpy
from scipy import stats

from pygaps import logger
from pygaps.characterisation.area_bet import area_BET
from pygaps.characterisation.area_lang import area_langmuir
from pygaps.core.adsorbate import Adsorbate
from pygaps.core.baseisotherm import BaseIsotherm
from pygaps.core.modelisotherm import ModelIsotherm
from pygaps.core.pointisotherm import PointIsotherm
from pygaps.utilities.exceptions import CalculationError
from pygaps.utilities.exceptions import ParameterError
from pygaps.utilities.exceptions import pgError
from pygaps.utilities.math_utilities import find_linear_sections


def alpha_s(
    isotherm: "PointIsotherm | ModelIsotherm",
    reference_isotherm: "PointIsotherm | ModelIsotherm",
    reference_area: str = 'BET',
    reducing_pressure: float = 0.4,
    branch: str = 'ads',
    branch_ref: str = 'ads',
    t_limits: "tuple[float, float]" = None,
    verbose: bool = False
):
    r"""
    Calculate surface area and pore volume using the alpha-s method.

    The ``reference_isotherm`` parameter is an Isotherm class which will form
    the x-axis of the alpha-s plot. The optional ``t_limits`` parameter has the
    upper and lower limits of the loading the section which should be taken for
    analysis.

    Parameters
    ----------
    isotherm : PointIsotherm, ModelIsotherm
        The isotherm of which to calculate the alpha-s plot parameters.
    reference_isotherm : PointIsotherm, ModelIsotherm
        The isotherm to use as reference.
    reference_area : float, 'BET', 'langmuir', optional
        Area of the reference material or function to calculate it
        using the reference isotherm.
        If not specified, the BET method is used.
    reducing_pressure : float, optional
        p/p0 value at which the loading is reduced.
        Default is 0.4 as it is the closing point for the nitrogen
        hysteresis loop.
    branch : {'ads', 'des'}, optional
        Branch of the isotherm to use. It defaults to adsorption.
    branch_ref : {'ads', 'des'}, optional
        Branch of the reference isotherm to use. It defaults to adsorption.
    t_limits : tuple[float, float], optional
        Reference thickness range in which to perform the calculation.
    verbose : bool, optional
        Prints extra information and plots graphs of the calculation.

    Returns
    -------
    dict
        A dictionary containing the t-plot curve, as well as a list of
        dictionaries with calculated parameters for each straight section. The
        basis of these results will be derived from the basis of the isotherm
        (per mass or per volume of adsorbent material):

        - ``alpha curve`` (list) : Calculated alpha-s curve
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

    In order to extend the t-plot analysis with other adsorbents and non-standard
    thickness curves, the :math:`\alpha_s` method was devised [#]_. Instead of
    a formula that describes the thickness of the adsorbed layer, a reference
    isotherm is used. This isotherm is measured on a non-porous version of the
    material with the same surface characteristics and with the same adsorbate.
    The :math:`\alpha_s` values are obtained from this isotherm by regularisation with
    an adsorption amount at a specific relative pressure, usually taken as 0.4 since
    nitrogen hysteresis loops theoretically close at this value

    .. math::

        \alpha_s = \frac{n_a}{n_{0.4}}

    The analysis then proceeds as in the t-plot method.

    The slope of the linear section (:math:`s`) can be used to calculate the
    area where adsorption is taking place. If it is of a linear region at the
    start of the curve, it will represent the total surface area of the
    material. If at the end of the curve, it will instead represent external
    surface area of the material. The calculation uses the known area of the
    reference material. If unknown, the area will be calculated here using the
    BET or Langmuir method.

    .. math::

        A = \frac{s A_{ref}}{(n_{ref})_{0.4}}

    If the region selected is after a vertical deviation, the intercept
    (:math:`i`) of the line will no longer pass through the origin. This
    intercept be used to calculate the pore volume through the following
    equation:

    .. math::

        V_{ads} = \frac{i M_m}{\rho_{l}}

    *Limitations*

    The reference isotherm chosen for the :math:`\alpha_s` method must be a description
    of the adsorption on a completely non-porous sample of the same material. It is
    often impossible to obtain such non-porous versions, therefore care must be taken
    how the reference isotherm is defined.

    References
    ----------
    .. [#] D. Atkinson, A.I. McLeod, K.S.W. Sing, J. Chim. Phys., 81, 791 (1984)

    See Also
    --------
    pygaps.characterisation.alphas_plots.alpha_s_raw : low level method

    """
    # Check to see if reference isotherm is given
    if reference_isotherm is None or not isinstance(reference_isotherm, BaseIsotherm):
        raise ParameterError(
            "No reference isotherm for alpha s calculation "
            "is provided. Must provide an Isotherm instance."
        )
    if reference_isotherm.adsorbate != isotherm.adsorbate:
        raise ParameterError(
            "The reference isotherm adsorbate is different than the "
            "calculated isotherm adsorbate."
        )
    if reducing_pressure < 0 or reducing_pressure > 1:
        raise ParameterError("The reducing pressure is outside the bounds of 0-1 p/p0.")

    # Deal with reference area
    if reference_area.lower() in ['bet', None]:
        try:
            reference_area = area_BET(reference_isotherm).get('area')
        except Exception as err:
            raise CalculationError(
                "Could not calculate a BET area for the reference isotherm. "
                "Either solve the issue or provide a value for reference_area. "
                f"BET area error is :\n{err}"
            ) from err
    elif reference_area.lower() == 'langmuir':
        try:
            reference_area = area_langmuir(reference_isotherm).get('area')
        except Exception as err:
            raise CalculationError(
                "Could not calculate a Langmuir area for the reference isotherm. "
                "Either solve the issue or provide a value for reference_area. "
                f"Langmuir area error is :\n{err}"
            ) from err
    elif not isinstance(reference_area, float):
        raise ParameterError(
            "The reference area should be either a numeric value, 'BET' or 'Langmuir'. "
            f"The value specified was {reference_area}."
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
    # Now for reference isotherm
    reference_loading = reference_isotherm.loading_at(
        pressure,
        pressure_unit=isotherm.pressure_unit,
        loading_unit='mol',
        branch=branch_ref,
    )
    alpha_s_point = reference_isotherm.loading_at(
        reducing_pressure,
        loading_unit='mol',
        pressure_mode='relative',
        branch=branch_ref,
    )
    # If on an desorption branch, reference data will be reversed
    if branch_ref == 'des':
        reference_loading = reference_loading[::-1]

    # Call alpha s function
    results, alpha_curve = alpha_s_raw(
        loading,
        reference_loading,
        alpha_s_point,
        reference_area,
        liquid_density,
        molar_mass,
        t_limits=t_limits,
    )

    if verbose:
        if not results:
            logger.info("Could not find linear regions, attempt a manual limit.")
        else:
            for index, result in enumerate(results):
                logger.info(f"For linear region {index}")
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
            tp_plot(alpha_curve, loading, results, alpha_s=True, alpha_reducing_p=reducing_pressure)

    return {
        'alpha_curve': alpha_curve,
        'results': results,
    }


def alpha_s_raw(
    loading: "list[float]",
    reference_loading: "list[float]",
    alpha_s_point: float,
    reference_area: float,
    liquid_density: float,
    adsorbate_molar_mass: float,
    t_limits: "tuple[float,float]" = None,
):
    """
    Calculate surface area and pore volume using the alpha-s method.

    This is a 'bare-bones' function to calculate alpha-s parameters which is
    designed as a low-level alternative to the main function. Designed for
    advanced use, its parameters have to be manually specified.

    Parameters
    ----------
    loading : list[float]
        Amount adsorbed at the surface, in mol/material.
    reference_loading : list[float]
        Loading of the reference curve corresponding to the same pressures.
    alpha_s_point : float
        p/p0 value at which the loading is reduced.
    reference_area : float
        Area of the surface on which the reference isotherm is taken.
    liquid_density : float
        Density of the adsorbate in the adsorbed state, in g/cm3.
    adsorbate_molar_mass : float
        Molar mass of the adsorbate, in g/mol.
    t_limits : tuple[float, float], optional
        Reference thickness range in which to perform the calculation.

    Returns
    -------
    results : list
        A list of dictionaries with the following components:

        - ``section`` (array[float]) : the points of the plot chosen for the line
        - ``area`` (float) : calculated surface area, from the section parameters
        - ``adsorbed_volume`` (float) : the amount adsorbed in the pores as
          calculated per section
        - ``slope`` (float) : slope of the straight trendline fixed through the region
        - ``intercept`` (float) : intercept of the straight trendline through the region
        - ``corr_coef`` (float) : correlation coefficient of the linear region

    alpha_curve : array
        The generated thickness curve at each point using the thickness model.

    """
    # Check lengths
    if len(loading) == 0:
        raise ParameterError("Empty input values!")
    if len(loading) != len(reference_loading):
        raise ParameterError("The length of the two loading arrays do not match.")

    # Ensure numpy arrays, if not already
    loading = numpy.asarray(loading)
    reference_loading = numpy.asarray(reference_loading)

    # The alpha-s method is a generalisation of the t-plot method
    # As such, we can just call the t-plot method with the required parameters

    alpha_curve = reference_loading / alpha_s_point

    results = []

    if t_limits is not None:
        section = numpy.flatnonzero((alpha_curve > t_limits[0]) & (alpha_curve < t_limits[1]))
        result = alpha_s_plot_parameters(
            alpha_curve,
            loading,
            section,
            alpha_s_point,
            reference_area,
            adsorbate_molar_mass,
            liquid_density,
        )
        if result:
            results.append(result)
        else:
            logger.warning("Could not fit a linear regression.")
    else:
        # Now we need to find the linear regions in the alpha-s for the
        # assessment of surface area.
        linear_sections = find_linear_sections(alpha_curve, loading)

        # For each section we compute the linear fit
        for section in linear_sections:
            result = alpha_s_plot_parameters(
                alpha_curve,
                loading,
                section,
                alpha_s_point,
                reference_area,
                adsorbate_molar_mass,
                liquid_density,
            )
            if result:
                results.append(result)

        if not results:
            logger.warning("Could not determine linear regions, attempt a manual limit.")

    return results, alpha_curve


def alpha_s_plot_parameters(
    alpha_curve: "list[float]",
    loading: "list[float]",
    section: "list[float]",
    alpha_s_point: float,
    reference_area: float,
    molar_mass: float,
    liquid_density: float,
):
    """Get the parameters for the linear region of the alpha-s plot."""

    slope, intercept, corr_coef, p, stderr = stats.linregress(
        alpha_curve[section], loading[section]
    )

    # Check if slope is good

    if slope * (max(alpha_curve) / max(loading)) < 3:
        adsorbed_volume = intercept * molar_mass / liquid_density
        area = (reference_area / alpha_s_point * slope).item()

        return {
            'section': section,
            'slope': slope,
            'intercept': intercept,
            'corr_coef': corr_coef,
            'adsorbed_volume': adsorbed_volume,
            'area': area,
        }

    return None
