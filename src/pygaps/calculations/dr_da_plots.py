"""Dubinin-Radushkevich equation and related plots."""

import numpy
import scipy.constants as const
import scipy.optimize as opt
import scipy.stats as stats

from ..classes.adsorbate import Adsorbate
from ..graphing.calcgraph import dra_plot
from ..utilities.exceptions import CalculationError
from ..utilities.exceptions import ParameterError


def dr_plot(isotherm, limits=None, verbose=False):
    r"""
    Calculate pore volume and effective adsorption potential
    through a Dubinin-Radushkevich (DR) plot.

    The function accepts a pyGAPS isotherm, with an ability
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

        - ``pore_volume`` (float) : calculated total micropore volume, cm3/adsorbent unit
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

        - ``pore_volume`` (float) : calculated total micropore volume, cm3/adsorbent unit
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

    find_exp = False
    if exp is None:
        find_exp = True
    elif exp < 0:
        raise ParameterError(
            """Exponent cannot be negative."""
        )

    # Get adsorbate properties
    adsorbate = Adsorbate.find(isotherm.adsorbate)
    molar_mass = adsorbate.molar_mass()
    liquid_density = adsorbate.liquid_density(isotherm.t_iso)
    iso_temp = isotherm.t_iso

    # Read data in
    loading = isotherm.loading(branch='ads',
                               loading_unit='mol',
                               loading_basis='molar')
    pressure = isotherm.pressure(branch='ads',
                                 pressure_mode='relative')

    if limits:
        maximum = len(pressure) - 1
        if limits[1]:
            for index, value in reversed(list(enumerate(pressure))):
                if value < limits[1]:
                    maximum = index
                    break

        minimum = 0
        if limits[0]:
            for index, value in enumerate(pressure):
                if value > limits[0]:
                    minimum = index
                    break

        pressure = pressure[minimum:maximum]
        loading = loading[minimum:maximum]

    # Calculate x points
    slope, intercept, log_n_p0p, logv, exp, microp_volume, potential = da_plot_raw(
        pressure, loading, iso_temp, molar_mass, liquid_density, exp)

    if verbose:

        dra_plot(logv, log_n_p0p, slope, intercept, exp)

        if find_exp:
            print("Exponent is: {:.2f}".format(exp))
        print("Micropore volume is: {:.3f} cm3".format(microp_volume))
        print("Effective adsorption potential is : {:.3f} kj/mol".format(potential))

    res = {
        "pore_volume": microp_volume,
        "adsorption_potential": potential
    }

    if find_exp:
        res["exponent"] = exp

    return res


def da_plot_raw(pressure, loading, iso_temp, molar_mass, liquid_density, exp):
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

    Returns
    -------
    slope : float
        Slope of the fitted DA line.
    intercept : float
        Intercept of the DA line.
    log_n_p0p : array
        Base 10 logarithm of p_0/p raised to the DA exponent.
    logv : array
        Base 10 logarithm of the volumetric uptake.
    exp : float
        The exponent (useful if fitting was desired)
    microp_volume : float
        Calculated DA pore volume
    potential : float
        Effective DA adsorption potential

    """
    # Calculate x points
    logv = numpy.log10(loading * molar_mass / liquid_density)

    def log_n_p0p(exp):
        """Calculate y points."""
        return (-numpy.log10(pressure))**exp

    def fit(exp, ret=False):
        """Linear fit."""
        slope, intercept, corr_coef, p_val, stderr = stats.linregress(
            log_n_p0p(exp), logv)

        if ret:
            return slope, intercept
        return stderr

    if exp is None:

        res = opt.minimize_scalar(fit, bounds=[1, 3], method='bounded')

        if not res.success:
            raise CalculationError("""Could not obtain a linear fit on the data provided.""")

        exp = res.x

    slope, intercept = fit(exp, True)

    # Obtain result values
    microp_volume = 10**intercept
    potential = (-numpy.log(10)**(exp-1) *
                 (const.gas_constant * iso_temp)**(exp)/slope)**(1/exp) / 1000

    return slope, intercept, log_n_p0p, logv, exp, microp_volume, potential
