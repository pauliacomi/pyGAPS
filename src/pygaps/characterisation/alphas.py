"""This module contains the alpha-s calculation."""

import logging

logger = logging.getLogger('pygaps')
import warnings

import numpy

from .. import scipy
from ..core.adsorbate import Adsorbate
from ..core.baseisotherm import BaseIsotherm
from ..graphing.calc_graphs import tp_plot
from ..utilities.exceptions import CalculationError
from ..utilities.exceptions import ParameterError
from ..utilities.math_utilities import find_linear_sections
from .area_bet import area_BET
from .area_langmuir import area_langmuir


def alpha_s(
    isotherm,
    reference_isotherm,
    reference_area='BET',
    reducing_pressure=0.4,
    limits=None,
    verbose=False
):
    r"""
    Calculate surface area and pore volume using the alpha-s method.

    Pass an isotherm object to the function to have the alpha-s method applied to it.
    The ``reference_isotherm`` parameter is an Isotherm class which will form the
    x-axis of the alpha-s method.
    The ``limits`` parameter takes the form of an array of two numbers, which are the
    upper and lower limits of the section which should be taken for analysis.

    Parameters
    ----------
    isotherm : PointIsotherm
        The isotherm of which to calculate the alpha-s plot parameters.
    reference_isotherm : PointIsotherm or ModelIsotherm
        The isotherm to use as reference.
    reference_area : either (area, 'BET' or 'langmuir'), optional
        Area of the reference material or function to calculate it
        using the reference isotherm.
        If not specified, the BET method is used.
    reducing_pressure : float, optional
        p/p0 value at which the loading is reduced.
        Default is 0.4 as it is the closing point for the nitrogen
        hysteresis loop.
    limits : [float, float], optional
        Manual limits for region selection.
    verbose : bool, optional
        Prints extra information and plots graphs of the calculation.

    Returns
    -------
    dict
        A dictionary containing the t-plot curve, as well as a list of dictionaries
        with calculated parameters for each straight section. The basis of these
        results will be derived from the basis of the isotherm (per mass or per
        volume of adsorbent material):

            - ``alpha curve`` (list) : Calculated alpha-s curve
            - ``results`` (list of dicts):

                - ``section`` (array) : the points of the plot chosen for the line
                - ``area`` (float) : calculated surface area, from the section parameters
                - ``adsorbed_volume`` (float) : the amount adsorbed in the pores as calculated per section
                - ``slope`` (float) : slope of the straight trendline fixed through the region
                - ``intercept`` (float) : intercept of the straight trendline through the region
                - ``corr_coef`` (float) : correlation coefficient of the linear region

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

    The slope of the linear section can be used to calculate the area where the adsorption
    is taking place. If it is of a linear region at the start of the curve, it will represent
    the total surface area of the material. If at the end of the curve, it will instead
    represent external surface area of the material.
    The calculation uses the known area of the reference material. If unknown, the area
    will be calculated here using the BET method.

    .. math::

        A = \frac{s A_{ref}}{(n_{ref})_{0.4}}

    If the region selected is after a vertical deviation, the intercept of the line
    will no longer pass through the origin. This intercept be used to calculate the
    pore volume through the following equation:

    .. math::

        V_{ads} = \frac{i M_m}{\rho_{l}}

    *Limitations*

    The reference isotherm chosen for the :math:`\alpha_s` method must be a description
    of the adsorption on a completely non-porous sample of the same material. It is
    often impossible to obtain such non-porous versions, therefore care must be taken
    how the reference isotherm is defined.

    References
    ----------
    .. [#] D.Atkinson, A.I.McLeod, K.S.W.Sing, J.Chim.Phys., 81,791(1984)

    """
    # Check to see if reference isotherm is given
    if reference_isotherm is None or not isinstance(
        reference_isotherm, BaseIsotherm
    ):
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
        raise ParameterError(
            "The reducing pressure is outside the bounds of 0-1"
        )

    # Deal with reference area
    if reference_area in ['BET', None]:
        try:
            reference_area = area_BET(reference_isotherm).get('area')
        except Exception as e:
            raise CalculationError(
                "Could not calculate a BET area for the reference isotherm. "
                "Either solve the issue or provide a value for reference_area. "
                f"BET area error is :\n{e}"
            )
    elif reference_area == 'Langmuir':
        try:
            reference_area = area_langmuir(reference_isotherm).get('area')
        except Exception as e:
            raise CalculationError(
                "Could not calculate a Langmuir area for the reference isotherm. "
                "Either solve the issue or provide a value for reference_area. "
                f"Langmuir area error is :\n{e}"
            )
    elif not isinstance(reference_area, float):
        raise ParameterError(
            "The reference area should be either a numeric value, 'BET' or 'Langmuir'. "
            f"The value specified was {reference_area}"
        )

    # Get adsorbate properties
    adsorbate = Adsorbate.find(isotherm.adsorbate)
    molar_mass = adsorbate.molar_mass()
    liquid_density = adsorbate.liquid_density(isotherm.temperature)

    # Read data in
    loading = isotherm.loading(
        branch='ads', loading_unit='mol', loading_basis='molar'
    )
    reference_loading = reference_isotherm.loading_at(
        isotherm.pressure(branch='ads', pressure_unit=isotherm.pressure_unit),
        pressure_unit=isotherm.pressure_unit,
        loading_unit='mol',
        branch='ads'
    )
    alpha_s_point = reference_isotherm.loading_at(
        0.4, loading_unit='mol', pressure_mode='relative', branch='ads'
    )

    # Call alpha s function
    results, alpha_curve = alpha_s_raw(
        loading,
        reference_loading,
        alpha_s_point,
        reference_area,
        liquid_density,
        molar_mass,
        limits=limits
    )

    if verbose:
        if not results:
            logger.info(
                "Could not find linear regions, attempt a manual limit."
            )
        else:
            for index, result in enumerate(results):
                logger.info(f"For linear region {index}")
                logger.info(
                    f"The slope is {result.get('slope'):.4f} and the intercept is {result.get('intercept'):.4f}, "
                    f"with a correlation coefficient of {result.get('corr_coef'):.4f}"
                )
                logger.info(
                    f"The adsorbed volume is {result.get('adsorbed_volume'):.4f} and the area is {result.get('area'):.4f}"
                )

            tp_plot(
                alpha_curve,
                loading,
                results,
                alpha_s=True,
                alpha_reducing_p=reducing_pressure
            )

    return {
        'alpha_curve': alpha_curve,
        'results': results,
    }


def alpha_s_raw(
    loading,
    reference_loading,
    alpha_s_point,
    reference_area,
    liquid_density,
    adsorbate_molar_mass,
    limits=None
):
    """
    Calculate surface area and pore volume using the alpha-s method.

    This is a 'bare-bones' function to calculate alpha-s parameters which is
    designed as a low-level alternative to the main function.
    Designed for advanced use, its parameters have to be manually specified.

    Parameters
    ----------
    loading : array
        Amount adsorbed at the surface, in mol/material.
    reference_loading : array
        Loading of the reference curve corresponding to the same pressures.
    alpha_s_point : float
        p/p0 value at which the loading is reduced.
    reference_area : float
        Area of the surface on which the reference isotherm is taken.
    liquid_density : float
        Density of the adsorbate in the adsorbed state, in g/cm3.
    adsorbate_molar_mass : float
        Molar mass of the adsorbate, in g/mol.
    limits : [float, float], optional
        Manual limits for region selection.

    Returns
    -------
    results : list
        A list of dictionaries with the following components:

            - ``section`` (array) : the points of the plot chosen for the line
            - ``area`` (float) : calculated surface area, from the section parameters
            - ``adsorbed_volume`` (float) : the amount adsorbed in the pores as calculated
              per section
            - ``slope`` (float) : slope of the straight trendline fixed through the region
            - ``intercept`` (float) : intercept of the straight trendline through the region
            - ``corr_coef`` (float) : correlation coefficient of the linear region

    alpha_curve : array
        The generated thickness curve at each point using the thickness model.

    """
    if len(loading) != len(reference_loading):
        raise ParameterError(
            "The length of the two loading arrays do not match."
        )

    # Ensure numpy arrays, if not already
    loading = numpy.asarray(loading)
    reference_loading = numpy.asarray(reference_loading)

    # The alpha-s method is a generalisation of the t-plot method
    # As such, we can just call the t-plot method with the required parameters

    alpha_curve = reference_loading / alpha_s_point

    results = []

    if limits is not None:
        section = numpy.flatnonzero((alpha_curve > limits[0])
                                    & (alpha_curve < limits[1]))
        results.append(
            alpha_s_plot_parameters(
                alpha_curve, section, loading, alpha_s_point, reference_area,
                adsorbate_molar_mass, liquid_density
            )
        )
    else:
        # Now we need to find the linear regions in the alpha-s for the
        # assessment of surface area.
        linear_sections = find_linear_sections(alpha_curve, loading)

        # For each section we compute the linear fit
        for section in linear_sections:
            params = alpha_s_plot_parameters(
                alpha_curve, section, loading, alpha_s_point, reference_area,
                adsorbate_molar_mass, liquid_density
            )
            if params is not None:
                results.append(params)

        if len(results) == 0:
            warnings.warn(
                'Could not find linear regions, attempt a manual limit'
            )

    return results, alpha_curve


def alpha_s_plot_parameters(
    alpha_curve, section, loading, alpha_s_point, reference_area, molar_mass,
    liquid_density
):
    """Get the parameters for the linear region of the alpha-s plot."""

    slope, intercept, corr_coef, p, stderr = scipy.stats.linregress(
        alpha_curve[section], loading[section]
    )

    # Check if slope is good

    if slope * (max(alpha_curve) / max(loading)) < 3:
        adsorbed_volume = intercept * molar_mass / liquid_density
        area = (reference_area / alpha_s_point * slope).item()

        result_dict = {
            'section': section,
            'slope': slope,
            'intercept': intercept,
            'corr_coef': corr_coef,
            'adsorbed_volume': adsorbed_volume,
            'area': area,
        }

        return result_dict

    return None
