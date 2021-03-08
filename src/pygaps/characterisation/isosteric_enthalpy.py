"""Module calculating the isosteric enthalpy for isotherms at different temperatures."""

import numpy

from .. import scipy
from ..graphing.calc_graphs import isosteric_enthalpy_plot
from ..utilities.exceptions import ParameterError


def isosteric_enthalpy(
    isotherms, loading_points=None, branch='ads', verbose=False
):
    r"""
    Calculate the isosteric enthalpy of adsorption using several isotherms
    recorded at different temperatures on the same material and the
    Clausius-Clapeyron equation.

    Parameters
    ----------
    isotherms : iterable of Isotherms
        The isotherms to use in calculation of the isosteric enthalpy. They should all
        be measured on the same material.
    loading_points : array, optional
        The loading points at which the isosteric enthalpy should be calculated.
        Default will be 50 equally spaced points in the available range.
        The points must be within the range of loading of all passed isotherms, or
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
            - ``slopes`` (array) : the exact log(p) vs 1/T slope for each point
            - ``correlation`` (array) : correlation coefficient for each point
            - ``std_errors`` (array) : estimated standard errors for each point

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

    The isosteric enthalpy is sensitive to the differences in pressure between
    the two isotherms. If the isotherms measured are too close together, the
    error margin will increase.

    The method also assumes that enthalpy of adsorption does not vary with
    temperature. If the variation is large for the system in question, the
    isosteric enthalpy calculation will give unrealistic values.

    Even with carefully measured experimental data, there are two assumptions
    used in deriving the Clausius-Clapeyron equation: an ideal bulk gas phase
    and a negligible adsorbed phase molar volume. These have a significant
    effect on the calculated isosteric enthalpies of adsorption, especially at
    high relative pressures and for heavy adsorbates.

    """
    # Check more than one isotherm
    if len(isotherms) < 2:
        raise ParameterError('Pass at least two isotherms.')

    # Check same material
    if not all(x.material == isotherms[0].material for x in isotherms):
        raise ParameterError(
            'Isotherms passed are not measured on the same material.'
        )

    # Check same basis
    if len(set(x.material_basis for x in isotherms)) > 1:
        raise ParameterError(
            'Isotherm passed are in a different material basis.'
        )

    # Get temperatures
    temperatures = [x.temperature for x in isotherms]

    # Loading
    loading = loading_points
    if loading is None:
        load_args = dict(
            loading_basis='molar',
            loading_unit='mmol',
            branch=branch,
        )
        # Get a minimum and maximum loading common for all isotherms
        min_loading = 1.01 * max([
            min(x.loading(**load_args)) for x in isotherms
        ])
        max_loading = 0.99 * min([
            max(x.loading(**load_args)) for x in isotherms
        ])
        loading = numpy.linspace(min_loading, max_loading, 50)

    # Get pressure point for each isotherm at loading
    pressures = numpy.array([
        iso.pressure_at(
            loading,
            pressure_mode='absolute',
            pressure_unit='bar',
            loading_basis='molar',
            loading_unit='mmol',
            branch=branch
        ) for iso in isotherms
    ]).T

    iso_enthalpy, slopes, correlation, std_errs = isosteric_enthalpy_raw(
        pressures, temperatures
    )

    if verbose:
        isosteric_enthalpy_plot(loading, iso_enthalpy, std_errs)

    return {
        'loading': loading,
        'isosteric_enthalpy': iso_enthalpy,
        'slopes': slopes,
        'correlation': correlation,
        'std_errs': std_errs,
    }


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
        A two dimensional array of pressures for each isotherm at same loading point,
        in bar. For example, if using two isotherms to calculate the isosteric enthalpy::

            [[p1_iso1, p1_iso2],
            [p2_iso1, p2_iso2],
            [p3_iso1, p3_iso2],
            ...]

    temperatures : array
        Temperatures of the isotherms are taken, kelvin.

    Returns
    -------
    iso_enth : array
        Calculated isosteric enthalpy.
    slopes : array
        Slopes fitted for each point.
    correlations : array
        The correlation of the straight line of each fit.

    """
    # Check same lengths
    if len(pressures[0]) != len(temperatures):
        raise ParameterError(
            "There are a different number of pressure points than temperature points"
        )

    # Convert to numpy arrays, just in case
    pressures = numpy.asarray(pressures)
    temperatures = numpy.asarray(temperatures)

    # Calculate inverse temperatures
    inv_t = 1 / temperatures

    iso_enth = []
    slopes = []
    correlations = []
    stderrs = []
    log_pressures = numpy.log(pressures)

    # Calculate enthalpy for each point by a linear fit
    for log_p in log_pressures:

        slope, intercept, corr_coef, p, std_err = scipy.stats.linregress(
            inv_t, log_p
        )

        iso_enth.append(-scipy.const.gas_constant * slope / 1000)
        slopes.append(slope)
        correlations.append(corr_coef)
        stderrs.append(-scipy.const.gas_constant * std_err / 1000)

    return iso_enth, slopes, correlations, stderrs
