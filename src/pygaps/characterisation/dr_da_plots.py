"""Dubinin-Radushkevich equation and related plots."""

import logging

logger = logging.getLogger('pygaps')

import numpy

from .. import scipy
from ..core.adsorbate import Adsorbate
from ..graphing.calc_graphs import dra_plot
from ..utilities.exceptions import CalculationError
from ..utilities.exceptions import ParameterError
from ..utilities.exceptions import pgError


def dr_plot(isotherm, limits=None, verbose=False):
    r"""
    Calculate pore volume and effective adsorption potential
    through a Dubinin-Radushkevich (DR) plot.

    The function accepts a pyGAPS isotherm, and has the ability
    to select the pressure limits for point selection.

    Parameters
    ----------
    isotherm : PointIsotherm
        The isotherm to use for the DR plot.
    limits : [float, float], optional
        Manual limits for pressure selection.
    verbose : bool, optional
        Prints extra information and plots the resulting fit graph.

    Returns
    -------
    dict
        Dictionary of results with the following parameters:

        - ``pore_volume`` (float) : calculated total micropore volume, cm3/material unit
        - ``adsorption_potential`` (float) : calculated adsorption potential, in kJ/mol

    Notes
    -----
    The Dubinin-Radushkevich equation [#]_ is an extension of the
    potential theory of Polanyi, which asserts that molecules
    near a surface are subjected to a potential field.
    The adsorbate at the surface is in a liquid state and
    its local pressure is conversely equal to the vapour pressure
    at the adsorption temperature.

    Pore filling progresses as a function of total adsorbed volume :math:`V_{t}`.

    .. math::

        V_{ads} = V_{t} \exp\Big[\Big(\frac{\Delta G}{\varepsilon}\Big)^{2}\Big]

    Here :math:`\Delta G` is the change in Gibbs free energy
    :math:`\Delta G = - RT \ln(p_0/p)` and :math:`\varepsilon`
    is a characteristic energy of adsorption.

    If an experimental isotherm is consistent with the DR model,
    the equation can be used to obtain the total pore volume
    and energy of adsorption. The DR equation is first linearised:

    .. math::

        \log_{10}{V_{ads}} = \log_{10}{V_{t}} -
        \ln10\Big(\frac{RT}{\varepsilon}\Big)^2 \Big[\log_{10}{\frac{p_0}{p}}\Big]^2

    Isotherm loading is converted to volume adsorbed by
    assuming that the density of the adsorbed phase is equal to
    bulk liquid density at the isotherm temperature.
    Afterwards :math:`\log_{10}{V_{ads}}` is plotted
    against :math:`\log^2_{10}{p_0/p}`,
    and fitted with a best-fit line. The intercept of this
    line can be used to calculate the total pore volume,
    while the slope is proportional to the characteristic
    energy of adsorption :math:`\varepsilon`.

    References
    ----------
    .. [#] B. P. Bering, M. M. Dubinin, and V. V. Serpinsky,
       “Theory of volume filling for vapor adsorption,”
       Journal of Colloid and Interface Science, vol. 21, no. 4, pp. 378–393, Apr. 1966.

    """
    return da_plot(isotherm, exp=2, limits=limits, verbose=verbose)


def da_plot(isotherm, exp=None, limits=None, verbose=False):
    r"""
    Calculate pore volume and effective adsorption potential
    through a Dubinin-Astakov (DA) plot.
    Optionally find a best exponent fit to the DA line.

    The function accepts a pyGAPS isotherm, with an ability
    to select the pressure limits for point selection.

    Parameters
    ----------
    isotherm : PointIsotherm
        The isotherm to use for the DA plot.
    exp : float, optional
        The exponent to use in the DA equation.
        If not specified a best fit exponent will be calculated
        between 1 and 3.
    limits : [float, float], optional
        Manual limits for pressure selection.
    verbose : bool, optional
        Prints extra information and plots the resulting fit graph.

    Returns
    -------
    dict
        Dictionary of results with the following parameters:

        - ``pore_volume`` (float) : calculated total micropore volume, cm3/material unit
        - ``adsorption_potential`` (float) : calculated adsorption potential, in kJ/mol
        - ``exponent`` (float) : the exponent, only if not specified, unitless

    Notes
    -----
    The Dubinin-Astakov equation [#]_ is an expanded form
    of the Dubinin-Radushkevich model. It is an extension of the
    potential theory of Polanyi, which asserts that molecules
    near a surface are subjected to a potential field.
    The adsorbate at the surface is in a liquid state and
    its local pressure is conversely equal to the vapour pressure
    at the adsorption temperature.

    Pore filling progresses as a function of total adsorbed volume :math:`V_{t}`.

    .. math::

        V_{ads} = V_{t} \exp\Big[\Big(\frac{\Delta G}{\varepsilon}\Big)^{n}\Big]

    Here :math:`\Delta G` is the change in Gibbs free energy
    :math:`\Delta G = - RT \ln(p_0/p)` and :math:`\varepsilon`
    is a characteristic energy of adsorption.
    The exponent :math:`n` is a fitting coefficient, often taken between
    1 (described as surface adsorption) and 3 (micropore adsorption).
    The exponent can also be related to surface heterogeneity.

    If an experimental isotherm is consistent with the DA model,
    the equation can be used to obtain the total pore volume
    and energy of adsorption. The DA equation is first linearised:

    .. math::

        \log_{10}{V_{ads}} = \log_{10}{V_{t}} -
        (\ln10)^{n-1}\Big(\frac{RT}{\varepsilon}\Big)^n \Big[\log_{10}{\frac{p_0}{p}}\Big]^n

    Isotherm loading is converted to volume adsorbed by
    assuming that the density of the adsorbed phase is equal to
    bulk liquid density at the isotherm temperature.
    Afterwards :math:`\log_{10}{V_{ads}}` is plotted
    against :math:`\log^n_{10}{p_0/p}`,
    and fitted with a best-fit line. The intercept of this
    line can be used to calculate the total pore volume,
    while the slope is proportional to the characteristic
    energy of adsorption :math:`\varepsilon`.

    References
    ----------
    .. [#] M. M. Dubinin, “Physical Adsorption of Gases and Vapors in Micropores,”
       in Progress in Surface and Membrane Science, vol. 9, Elsevier, 1975, pp. 1–70.

    """

    # Check consistency of exponent
    find_exp = False
    if not exp:
        find_exp = True
    elif exp < 0:
        raise ParameterError("Exponent cannot be negative.")

    # Get adsorbate properties
    adsorbate = Adsorbate.find(isotherm.adsorbate)
    molar_mass = adsorbate.molar_mass()
    liquid_density = adsorbate.liquid_density(isotherm.temperature)
    iso_temp = isotherm.temperature

    # Read data in
    loading = isotherm.loading(
        branch='ads', loading_unit='mol', loading_basis='molar'
    )
    try:
        pressure = isotherm.pressure(
            branch='ads',
            pressure_mode='relative',
        )
    except pgError:
        raise CalculationError(
            "The isotherm cannot be converted to a relative basis. "
            "Is your isotherm supercritical?"
        )

    # Call the raw function
    (
        microp_volume,
        potential,
        exp,
        slope,
        intercept,
        minimum,
        maximum,
        corr_coef,
    ) = da_plot_raw(
        pressure, loading, iso_temp, molar_mass, liquid_density, exp, limits
    )

    if verbose:
        if find_exp:
            logger.info(f"Exponent is: {exp:.2f}")
        logger.info(f"Micropore volume is: {microp_volume:.3f} cm3")
        logger.info(
            f"Effective adsorption potential is : {potential:.3f} kJ/mol"
        )
        # Plot
        dra_plot(
            log_v_adj(loading, molar_mass, liquid_density),
            log_p_exp(pressure, exp), minimum, maximum, slope, intercept, exp
        )

    res = {
        "pore_volume": microp_volume,
        "adsorption_potential": potential,
        'corr_coef': corr_coef,
        'limits': [minimum, maximum],
    }

    if find_exp:
        res["exponent"] = exp

    return res


def da_plot_raw(
    pressure,
    loading,
    iso_temp,
    molar_mass,
    liquid_density,
    exp=None,
    limits=None
):
    """
    Calculate a DA fit, a 'bare-bones' function.

    Designed as a low-level alternative to the main function.
    For advanced use.

    Parameters
    ----------
    pressure : array
        Pressure, relative.
    loading : array
        Loading, in mol/basis.
    iso_temp : float
        Isotherm temperature, in K
    molar_mass : float
        Molar mass of adsorbate, in g/mol.
    liquid_density : float
        Mass liquid density of the adsorbed phase, in g/cm3.
    exp : float, None
        Exponent used in the DA equation.
        Pass None to automatically calculate.
    limits : [float, float], optional
        Manual limits for region selection.

    Returns
    -------
    microp_volume : float
        Calculated DA pore volume.
    potential : float
        Effective DA adsorption potential.
    exp : float
        The exponent (useful if fitting was desired).
    slope : float
        Slope of the fitted DA line.
    intercept : float
        Intercept of the DA line.
    minimum : float
        Minimum point taken.
    maximum : float
        Maximum point taken.
    corr_coef : float
        Correlation coefficient of the fit line.

    """
    # Check lengths
    if len(pressure) != len(loading):
        raise ParameterError(
            "The length of the pressure and loading arrays do not match."
        )
    # Ensure numpy arrays, if not already
    loading = numpy.asarray(loading)
    pressure = numpy.asarray(pressure)

    maximum = len(pressure)
    minimum = 0
    if limits:

        if limits[1]:
            maximum = numpy.searchsorted(pressure, limits[1])

        if limits[0]:
            minimum = numpy.searchsorted(pressure, limits[0])

        if maximum - minimum < 2:  # (for 2 point minimum)
            raise CalculationError(
                "The desired limits are infeasible (at least 2 points selected)."
            )

        pressure = pressure[minimum:maximum]
        loading = loading[minimum:maximum]

    # Calculate x-axis points
    logv = log_v_adj(loading, molar_mass, liquid_density)

    def fit(exp, ret=False):
        """Linear fit."""
        slope, intercept, corr_coef, p_val, stderr = scipy.stats.linregress(
            log_p_exp(pressure, exp), logv
        )

        if ret:
            return slope, intercept, corr_coef
        return stderr

    if exp is None:

        res = scipy.optimize.minimize_scalar(
            fit, bounds=[1, 3], method='bounded'
        )

        if not res.success:
            raise CalculationError(
                """Could not obtain a linear fit on the data provided."""
            )

        exp = res.x

    slope, intercept, corr_coef = fit(exp, True)

    # Calculate final result values
    microp_volume = 10**intercept
    potential = (
        -numpy.log(10)**(exp - 1) *
        (scipy.const.gas_constant * iso_temp)**(exp) / slope
    )**(1 / exp) / 1000

    return (
        microp_volume,
        potential,
        exp,
        slope,
        intercept,
        minimum,
        maximum,
        corr_coef,
    )


def log_v_adj(loading, molar_mass, liquid_density):
    """Base 10 logarithm of volumetric uptake."""
    return numpy.log10(loading * molar_mass / liquid_density)


def log_p_exp(pressure, exp):
    """Base 10 logarithm of p_0/p raised to the DA exponent."""
    return (-numpy.log10(pressure))**exp
