"""This module contains BET area calculations."""

import logging

logger = logging.getLogger('pygaps')
import textwrap
import warnings

import numpy

from .. import scipy
from ..core.adsorbate import Adsorbate
from ..graphing.calc_graphs import bet_plot
from ..graphing.calc_graphs import roq_plot
from ..utilities.exceptions import CalculationError
from ..utilities.exceptions import ParameterError
from ..utilities.exceptions import pgError


def area_BET(isotherm, branch='ads', limits=None, verbose=False):
    r"""
    Calculate BET-determined surface area from an isotherm.

    Pass an isotherm object to the function to have the BET method applied to it. Since
    the function automatically takes the properties of the adsorbate from the master
    list, ensure that it contains all the adsorbates which were used in the isotherms,
    together with the properties required.

    Parameters
    ----------
    isotherm : PointIsotherm
        The isotherm of which to calculate the BET surface area.
    branch : {'ads', 'des'}, optional
        Branch of the isotherm to use. It defaults to adsorption.
    limits : [float, float], optional
        Manual limits for region selection.
    verbose : bool, optional
        Prints extra information and plots graphs of the calculation.

    Returns
    -------
    dict
        A dictionary of results with the following components. The basis of these
        results will be derived from the basis of the isotherm (per mass or per
        volume of adsorbent):

        - ``area`` (float) : calculated BET surface area, in m2/unit of adsorbent
        - ``c_const`` (float) : the C constant in the BET equation, unitless
        - ``n_monolayer`` (float) : the amount adsorbed at statistical monolayer, in mmol
        - ``p_monolayer`` (float) : the pressure at which statistical monolayer is chosen, relative
        - ``bet_slope`` (float) : slope of the BET plot
        - ``bet_intercept`` (float) : intercept of the BET plot
        - ``corr_coef`` (float) : correlation coefficient of the linear region in the BET plot

    Notes
    -----
    *Description*

    The BET method [#]_ is one of the first standardised methods to calculate the
    surface area of a porous material. It is generally applied on isotherms obtained
    through N2 adsorption at 77K, although other adsorbates (Ar, Kr) have been used.

    It assumes that the adsorption happens on the surface of the material in
    incremental layers according to the BET theory. Even if the adsorbent is porous,
    the initial amount adsorbed (usually between 0.05 - 0.4 :math:`p/p_0`) can be
    modelled through the BET equation:

    .. math::

        \frac{p/p_0}{n_{ads} (1-p/p_0)} = \frac{1}{n_{m} C} + \frac{C - 1}{n_{m} C}(p/p_0)

    Therefore, if we plot the isotherm points as :math:`\frac{p/p_0}{n_{ads}(1-p/p_0)}` versus
    :math:`p/p_0`, a linear region can usually be found. The slope and intercept of this line
    can then be used to calculate :math:`n_{m}`, the amount adsorbed at the statistical
    monolayer, as well as C, the BET constant.

    .. math::

        n_{m} = \frac{1}{s+i}

        C = \frac{s}{i} + 1

    The surface area can then be calculated by using the moles adsorbed at the statistical
    monolayer. If the specific area taken by one of the adsorbate molecules on the surface
    is known, it is inserted in the following equation together with Avogadro's number:

    .. math::

        a(BET) = n_m A_N \sigma


    *Limitations*

    While a standard for surface area determinations, the BET area should be used with care,
    as there are many assumptions made in the calculation. To augment the validity of the BET
    method, Rouquerol [#]_ proposed several checks to ensure that the BET region selected is valid

        * The BET constant (C) obtained should be positive
        * In the corresponding Rouquerol plot where :math:`n_{ads}(1-p/p_0)` is plotted
          with respect to :math:`p/p_0`, the points chosen for BET analysis should be
          strictly increasing
        * The loading at the statistical monolayer should be situated within the
          limits of the BET region

    This module implements all these checks.

    Regardless, the BET surface area should still be interpreted carefully. The following
    assumptions are implicitly made in this approach:

        * Adsorption takes place on the pore surface. Microporous materials which have pores
          in similar size as the molecule adsorbed cannot posses a realistic surface area
        * The cross-sectional area of the molecule on the surface cannot be guaranteed
          For example, nitrogen has been known to adopt different orientations on the
          surface of some materials due to inter-molecular forces, which effectively
          lowers its cross-sectional area.
        * No account is made for heterogeneous adsorbate-adsorbent interaction in the BET theory

    References
    ----------
    .. [#] “Adsorption of Gases in Multimolecular Layers”, Stephen Brunauer,
       P. H. Emmett and Edward Teller, J. Amer. Chem. Soc., 60, 309(1938)
    .. [#] "Adsorption by Powders & Porous Solids", F. Rouquerol, J Rouquerol
       and K. Sing, Academic Press, 1999

    """
    # get adsorbate properties
    adsorbate = Adsorbate.find(isotherm.adsorbate)
    cross_section = adsorbate.get_prop("cross_sectional_area")

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

    # use the bet function
    (
        bet_area, c_const, n_monolayer, p_monolayer, slope, intercept, minimum,
        maximum, corr_coef
    ) = area_BET_raw(pressure, loading, cross_section, limits=limits)

    if verbose:
        logger.info(
            textwrap.dedent(
                f"""\
            BET surface area: a = {bet_area:.2e} m2/{isotherm.material_unit}
            Minimum pressure point is {pressure[minimum]:.3f} and maximum is {pressure[maximum -1]:.3f}
            The slope of the BET fit: s = {slope:.2e}
            The intercept of the BET fit: i = {intercept:.2e}
            The BET constant is: C = {c_const:.1f}
            Amount for a monolayer: n = {n_monolayer:.2e} mol/{isotherm.material_unit}"""
            )
        )

        # Generate plot of the BET points chosen
        bet_plot(
            pressure, bet_transform(pressure, loading), minimum, maximum,
            slope, intercept, p_monolayer,
            bet_transform(p_monolayer, n_monolayer)
        )

        # Generate plot of the Rouquerol points chosen
        roq_plot(
            pressure, roq_transform(pressure, loading), minimum, maximum,
            p_monolayer, roq_transform(p_monolayer, n_monolayer)
        )

    return {
        'area': bet_area,
        'c_const': c_const,
        'n_monolayer': n_monolayer,
        'p_monolayer': p_monolayer,
        'bet_slope': slope,
        'bet_intercept': intercept,
        'corr_coef': corr_coef,
        'limits': [minimum, maximum]
    }


def area_BET_raw(pressure, loading, cross_section, limits=None):
    """
    Calculate BET-determined surface area.

    This is a 'bare-bones' function to calculate BET surface area which is
    designed as a low-level alternative to the main function.
    Designed for advanced use, its parameters have to be manually specified.

    Parameters
    ----------
    pressure : array
        Pressures, relative.
    loading : array
        Loadings, in mol/basis.
    cross_section : float
        Adsorbed cross-section of the molecule of the adsorbate, in nm.
    limits : [float, float], optional
        Manual limits for region selection.

    Returns
    -------
    area : float
        Calculated BET surface area.
    c_const : float
        C constant from the BET equation.
    n_monolayer : float
        Adsorbed quantity in the statistical monolayer.
    p_monolayer : float
        Pressure at the statistical monolayer.
    slope : float
        Calculated slope of the BET plot.
    intercept : float
        Calculated intercept of the BET plot.
    minimum : float
        Minimum point taken for the linear region.
    maximum : float
        Maximum point taken for the linear region.
    corr_coef : float
        Correlation coefficient of the straight line in the BET plot.

    """
    # Check lengths
    if len(pressure) != len(loading):
        raise ParameterError(
            "The length of the pressure and loading arrays do not match."
        )
    # Ensure numpy arrays, if not already
    loading = numpy.asarray(loading)
    pressure = numpy.asarray(pressure)

    # select the maximum and minimum of the points and the pressure associated
    maximum = len(pressure)
    minimum = 0

    if limits is None:

        # Generate the Rouquerol array
        roq_t_array = roq_transform(pressure, loading)

        # Find place where array starts decreasing
        # If none is found, maximum will be left as-is
        for index, value in enumerate(roq_t_array):
            if value > roq_t_array[index + 1]:
                maximum = index + 1
                break

        # Min pressure is initially taken as 10% of max
        min_p = pressure[maximum] / 10
        minimum = numpy.searchsorted(pressure, min_p)

        # Try to extend if not enough points
        if maximum - minimum < 3:  # (for 3 point minimum)
            if maximum > 2:  # Can only extend if enough points available
                minimum = maximum - 3
            else:
                raise CalculationError(
                    "The isotherm does not have enough points (at least 3) "
                    "in the BET region. Unable to calculate BET area."
                )

    else:

        # Determine the limits
        if limits[1]:
            maximum = numpy.searchsorted(pressure, limits[1])

        if limits[0]:
            minimum = numpy.searchsorted(pressure, limits[0])

        if maximum - minimum < 3:  # (for 3 point minimum)
            raise CalculationError(
                "The isotherm does not have enough points (at least 3) "
                "in the BET region. Unable to calculate BET area."
            )

    # calculate the BET transform, slope and intercept
    bet_t_array = bet_transform(
        pressure[minimum:maximum], loading[minimum:maximum]
    )
    slope, intercept, corr_coef = bet_optimisation(
        pressure[minimum:maximum], bet_t_array
    )

    # calculate the BET parameters
    n_monolayer, p_monolayer, c_const, bet_area = bet_parameters(
        slope, intercept, cross_section
    )

    # Checks for consistency
    if c_const < 0:
        warnings.warn("The C constant is negative.")
    if corr_coef < 0.99:
        warnings.warn("The correlation is not linear.")
    if not (loading[minimum] < n_monolayer < loading[maximum - 1]):
        warnings.warn("The monolayer point is not within the BET region")

    return (
        bet_area,
        c_const,
        n_monolayer,
        p_monolayer,
        slope,
        intercept,
        minimum,
        maximum,
        corr_coef,
    )


def roq_transform(pressure, loading):
    """Rouquerol transform function."""
    return loading * (1 - pressure)


def bet_transform(pressure, loading):
    """BET transform function."""
    return pressure / roq_transform(pressure, loading)


def bet_optimisation(pressure, bet_points):
    """Find the slope and intercept of the BET region."""
    slope, intercept, corr_coef, p, stderr = scipy.stats.linregress(
        pressure, bet_points
    )
    return slope, intercept, corr_coef


def bet_parameters(slope, intercept, cross_section):
    """Calculate the BET parameters from the slope and intercept."""

    c_const = (slope / intercept) + 1
    n_monolayer = 1 / (intercept * c_const)
    p_monolayer = 1 / (numpy.sqrt(c_const) + 1)
    bet_area = n_monolayer * cross_section * (10**(-18)) * scipy.const.Avogadro
    return n_monolayer, p_monolayer, c_const, bet_area
