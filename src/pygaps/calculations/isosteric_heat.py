"""
This module calculates the isosteric heat for isotherms at different temperatures.
"""

import numpy
import scipy.constants as constants
import scipy.stats

from ..graphing.calcgraph import isosteric_heat_plot
from ..utilities.exceptions import ParameterError


def isosteric_heat(isotherms, loading_points=None, branch='ads', verbose=False):
    """
    Calculation of the isosteric heat of adsorption using several isotherms
    taken at different temperatures on the same material.

    Parameters
    ----------
    isotherms : iterable of Isotherms
        The isotherms to use in calculation of the isosteric heat. They should all
        be measured on the same material.
    loading_points : array, optional
        The loading points at which the isosteric heat should be calculated. Take care,
        as the points must be within the range of loading of all passed isotherms, or
        else the calculation cannot complete.
    branch : str
        The branch of the isotherms to take, defaults to adsorption branch.
    verbose : bool
        Whether to print out extra information and generate a graph.

    Returns
    -------
    result_dict : dict
        A dictionary with the isosteric heats per loading, with the form:

            - ``isosteric_heat(array)`` : the isosteric heat of adsorption in kj/mmol
            - ``loading(array)`` : the loading for each point of the isosteric heat, in mmol

    Notes
    -----

    *Description*

    The isosteric heats are calculated from experimental data using the Clausius-Clapeyron
    equation as the starting point:

    .. math::

        \\Big( \\frac{\\partial \\ln P}{\\partial T} \\Big)_{n_a} = -\\frac{\\Delta H_{ads}}{R T^2}

    Where :math:`\\Delta H_{ads}` is the enthalpy of adsorption. In order to approximate the
    partial differential, two or more isotherms are measured at different temperatures. The
    assumption made is that the heat of adsorption does not vary in the temperature range
    chosen. Therefore, the isosteric heat of adsorption can be calculated by using the pressures
    at which the loading is identical using the following equation for each point:

    .. math::

        \\Delta H_{ads} = - R \\frac{\\partial \\ln P}{\\partial 1 / T}

    and plotting the values of :math:`\\ln P` against :math:`1 / T` we should obtain a straight
    line with a slope of :math:`- \\Delta H_{ads} / R.`

    *Limitations*

    The isosteric heat is sensitive to the differences in pressure between the two isotherms. If
    the isotherms measured are too close together, the error margin will increase.

    The method also assumes that enthalpy of adsorption does not vary with temperature. If the
    variation is large for the system in question, the isosteric heat calculation will give
    unrealistic values.

    Even with carefully measured experimental data, there are two assumptions used in deriving
    the Clausius-Clapeyron equation: an ideal bulk gas phase and a negligible adsorbed phase
    molar volume. These have a significant effect on the calculated isosteric heats of adsorption,
    especially at high relative pressures and for heavy adsorbates.

    """

    # Check more than one isotherm
    if len(isotherms) < 2:
        raise ParameterError('Pass at least two isotherms.')

    # Check same sample
    if not all(x.sample_name == isotherms[0].sample_name
               and x.sample_batch == isotherms[0].sample_batch
               for x in isotherms):
        raise ParameterError(
            'Isotherms passed are not measured on the same material and batch.')

    # Check same basis
    if not all(x.adsorbent_basis == isotherms[0].adsorbent_basis for x in isotherms):
        raise ParameterError(
            'Isotherm passed are in a different adsorbent basis.')

    # Get minimum and maximum loading for each isotherm
    min_loading = 1.01 * max(
        [min(x.loading(loading_basis='molar', loading_unit='mmol', branch=branch)) for x in isotherms])
    max_loading = 0.99 * min(
        [max(x.loading(loading_basis='molar', loading_unit='mmol', branch=branch)) for x in isotherms])

    # Get temperatures
    temperatures = list(x.t_exp for x in isotherms)

    # Loading
    if loading_points is None:
        loading = numpy.linspace(min_loading, max_loading, 50)
    else:
        loading = loading_points

    # Get pressure point for each isotherm at loading
    pressures = numpy.array(
        [[numpy.asscalar(i.pressure_at(
            l, pressure_unit='bar',
            pressure_mode='absolute',
            loading_unit='mmol', branch=branch)) for i in isotherms]
            for l in loading])

    iso_heat, slopes, correlation = isosteric_heat_raw(pressures, temperatures)

    result_dict = {
        'loading': loading,
        'isosteric_heat': iso_heat,
        'slopes': slopes,
        'correlation': correlation,
    }

    if verbose:
        isosteric_heat_plot(loading, iso_heat)

    return result_dict


def isosteric_heat_raw(pressures, temperatures):
    """
    This is a 'bare-bones' function to calculate isosteric heat which is
    designed as a low-level alternative to the main function.
    Designed for advanced use, its parameters have to be manually specified.

    Parameters
    ----------
    pressure : array or arrays
        An array of arrays of pressures for each isotherm, in bar.
        For example, if using two isotherms to calculate the isosteric heat:
        [[l1_iso1, l1_iso2], [l2_iso1, l2_iso2], [l3_iso1, l3_iso2], ...]
    temperatures : array
        Temperatures at which the isotherms are taken, kelvin.

    Returns
    -------
    iso_heat : array
        Calculated isosteric heat.
    slopes : array
        Slopes fitted for each point.
    correlations : array
        The correlation of the straight line of each fit.

    """

    # Check same lengths
    if len(pressures[0]) != len(temperatures):
        raise ParameterError(
            "There are a different number of pressure points than temperature points")

    # Convert to numpy arrays, just in case
    pressures = numpy.array(pressures)
    temperatures = numpy.array(temperatures)

    # Calculate inverse temperatures
    inv_t = 1 / temperatures

    iso_heat = []
    slopes = []
    correlations = []

    # Calculate heat for each point
    for pressure in pressures:

        slope, intercept, corr_coef, p, stderr = scipy.stats.linregress(
            inv_t, numpy.log(pressure))

        iso_heat.append(-constants.gas_constant * slope / 1000)
        slopes.append(slope)
        correlations.append(corr_coef)

    return iso_heat, slopes, correlations
