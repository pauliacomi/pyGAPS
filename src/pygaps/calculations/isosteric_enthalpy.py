"""Module calculating the isosteric enthalpy for isotherms at different temperatures."""

import numpy
import scipy.constants as const
import scipy.stats as stats

from ..graphing.calcgraph import isosteric_enthalpy_plot
from ..utilities.exceptions import ParameterError


def isosteric_enthalpy(isotherms, loading_points=None, branch='ads', verbose=False):
    r"""
    Calculate the isosteric enthalpy of adsorption using several isotherms
    recorded at different temperatures on the same material.

    Parameters
    ----------
    isotherms : iterable of Isotherms
        The isotherms to use in calculation of the isosteric enthalpy. They should all
        be measured on the same material.
    loading_points : array, optional
        The loading points at which the isosteric enthalpy should be calculated. Take care,
        as the points must be within the range of loading of all passed isotherms, or
        else the calculation cannot complete.
    branch : str
        The branch of the isotherms to take, defaults to adsorption branch.
    verbose : bool
        Whether to print out extra information and generate a graph.

    Returns
    -------
    result_dict : dict
        A dictionary with the isosteric enthalpies per loading, with the form:

            - ``isosteric_enthalpy`` (array) : the isosteric enthalpy of adsorption in kj/mmol
            - ``loading`` (array) : the loading for each point of the isosteric enthalpy, in mmol

    Notes
    -----

    *Description*

    The isosteric enthalpies are calculated from experimental data using the Clausius-Clapeyron
    equation as the starting point:

    .. math::

        \Big( \frac{\partial \ln P}{\partial T} \Big)_{n_a} = -\frac{\Delta H_{ads}}{R T^2}

    Where :math:`\Delta H_{ads}` is the enthalpy of adsorption. In order to approximate the
    partial differential, two or more isotherms are measured at different temperatures. The
    assumption made is that the enthalpy of adsorption does not vary in the temperature range
    chosen. Therefore, the isosteric enthalpy of adsorption can be calculated by using the pressures
    at which the loading is identical using the following equation for each point:

    .. math::

        \Delta H_{ads} = - R \frac{\partial \ln P}{\partial 1 / T}

    and plotting the values of :math:`\ln P` against :math:`1 / T` we should obtain a straight
    line with a slope of :math:`- \Delta H_{ads} / R.`

    *Limitations*

    The isosteric enthalpy is sensitive to the differences in pressure between the two isotherms. If
    the isotherms measured are too close together, the error margin will increase.

    The method also assumes that enthalpy of adsorption does not vary with temperature. If the
    variation is large for the system in question, the isosteric enthalpy calculation will give
    unrealistic values.

    Even with carefully measured experimental data, there are two assumptions used in deriving
    the Clausius-Clapeyron equation: an ideal bulk gas phase and a negligible adsorbed phase
    molar volume. These have a significant effect on the calculated isosteric enthalpies of adsorption,
    especially at high relative pressures and for heavy adsorbates.

    """
    # Check more than one isotherm
    if len(isotherms) < 2:
        raise ParameterError('Pass at least two isotherms.')

    # Check same sample
    if not all(x.material_name == isotherms[0].material_name
               and x.material_batch == isotherms[0].material_batch
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
    temperatures = list(x.t_iso for x in isotherms)

    # Loading
    if loading_points is None:
        loading = numpy.linspace(min_loading, max_loading, 50)
    else:
        loading = loading_points

    # Get pressure point for each isotherm at loading
    pressures = numpy.array(
        [[i.pressure_at(
            l, pressure_unit='bar',
            pressure_mode='absolute',
            loading_unit='mmol', branch=branch).item() for i in isotherms]
            for l in loading])

    iso_enthalpy, slopes, correlation = isosteric_enthalpy_raw(pressures, temperatures)

    result_dict = {
        'loading': loading,
        'isosteric_enthalpy': iso_enthalpy,
        'slopes': slopes,
        'correlation': correlation,
    }

    if verbose:
        isosteric_enthalpy_plot(loading, iso_enthalpy)

    return result_dict


def isosteric_enthalpy_raw(pressures, temperatures):
    """
    Calculate the isosteric enthalpy of adsorption using several isotherms
    recorded at different temperatures on the same material.

    This is a 'bare-bones' function to calculate isosteric enthalpy which is
    designed as a low-level alternative to the main function.
    Designed for advanced use, its parameters have to be manually specified.

    Parameters
    ----------
    pressure : array of arrays
        An array of arrays of pressures for each isotherm, in bar.
        For example, if using two isotherms to calculate the isosteric enthalpy:
        [[l1_iso1, l1_iso2], [l2_iso1, l2_iso2], [l3_iso1, l3_iso2], ...]
    temperatures : array
        Temperatures at which the isotherms are taken, kelvin.

    Returns
    -------
    isosteric_enthalpy : array
        Calculated isosteric enthalpy.
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
    pressures = numpy.asarray(pressures)
    temperatures = numpy.asarray(temperatures)

    # Calculate inverse temperatures
    inv_t = 1 / temperatures

    isosteric_enthalpy = []
    slopes = []
    correlations = []

    # Calculate enthalpy for each point
    for pressure in pressures:

        slope, intercept, corr_coef, p, stderr = stats.linregress(
            inv_t, numpy.log(pressure))

        isosteric_enthalpy.append(-const.gas_constant * slope / 1000)
        slopes.append(slope)
        correlations.append(corr_coef)

    return isosteric_enthalpy, slopes, correlations
