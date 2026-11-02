"""BET area calculations."""

import textwrap
from typing import TYPE_CHECKING
from typing import cast

import numpy
from scipy import constants
from scipy import stats

if TYPE_CHECKING:
    from pygaps.core.modelisotherm import ModelIsotherm
    from pygaps.core.pointisotherm import PointIsotherm

from pygaps import logger
from pygaps.core.adsorbate import Adsorbate
from pygaps.utilities.exceptions import CalculationError
from pygaps.utilities.exceptions import ParameterError
from pygaps.utilities.pygaps_utilities import get_iso_loading_and_pressure_ordered
from pygaps.utilities.pygaps_utilities import get_pressure_limit_indices


def area_BET(
    isotherm: "PointIsotherm | ModelIsotherm",
    branch: str = 'ads',
    p_limits: "tuple[float, float]" = None,
    verbose: bool = False,
):
    r"""
    Calculate BET area from an isotherm.

    The optional ``p_limits`` parameter allows to specify the upper and lower
    pressure limits to calculate the BET area, otherwise the limits will be
    automatically selected based on the Rouquerol rules.

    Parameters
    ----------
    isotherm : PointIsotherm, ModelIsotherm
        The isotherm of which to calculate the BET surface area.
    branch : {'ads', 'des'}, optional
        Branch of the isotherm to use. It defaults to adsorption.
    p_limits : tuple[float, float], optional
        Inclusive pressure range in which to perform the calculation.
    verbose : bool, optional
        Prints extra information and plots graphs of the calculation.

    Returns
    -------
    dict
        A dictionary of results with the following components. The basis of these
        results will be derived from the basis of the isotherm (per mass, per
        volume, or per mole of adsorbent):

        - ``area`` (float) : calculated BET surface area, in m2/unit of adsorbent
        - ``c_const`` (float) : the C constant in the BET equation, unitless
        - ``n_monolayer`` (float) : the amount adsorbed at statistical monolayer, in mol/unit of adsorbent
        - ``p_monolayer`` (float) : the pressure at which statistical monolayer is chosen, relative
        - ``bet_slope`` (float) : slope of the BET plot, in unit of adsorbent/mol
        - ``bet_intercept`` (float) : intercept of the BET plot, in unit of adsorbent/mol
        - ``corr_coef`` (float) : correlation coefficient of the linear region in the BET plot
        - ``area_stderr`` (float) : delta-method standard error of the area from the linear fit
        - ``bet_slope_stderr`` (float) : standard error of the BET plot slope
        - ``bet_intercept_stderr`` (float) : standard error of the BET plot intercept
        - ``cross_sectional_area`` (float) : adsorbate cross-sectional area used, in nm^2

    Raises
    ------
    ParameterError
        When something is wrong with the function parameters.
    CalculationError
        When the calculation itself fails.

    Notes
    -----
    *Description*

    The BET method [#]_ is one of the first standardised methods to calculate the
    surface area of a porous material. It is generally applied on isotherms obtained
    through N2 adsorption at 77K, although other adsorbates (Ar, Kr) have been used.

    It assumes that the adsorption happens on the surface of the material in
    incremental layers according to the BET theory. Even if the adsorbent is mesoporous,
    the initial amount adsorbed (usually between 0.05 - 0.4 :math:`p/p_0`) can be
    modelled through the BET equation:

    .. math::

        \frac{p/p_0}{n_{ads} (1-p/p_0)} = \frac{1}{n_{m} C} + \frac{C - 1}{n_{m} C}(p/p_0)

    If we plot the isotherm points as :math:`\frac{p/p_0}{n_{ads}(1-p/p_0)}` versus
    :math:`p/p_0`, a linear region can usually be found. The slope and intercept of this line
    can then be used to calculate :math:`n_{m}`, the amount adsorbed at the statistical
    monolayer, as well as :math:`C`, the BET constant.

    .. math::

        n_{m} = \frac{1}{s+i}

        C = \frac{s}{i} + 1

    The surface area can then be calculated by using the moles adsorbed at the statistical
    monolayer. If the specific area taken by one of the adsorbate molecules on the surface
    is known, it is inserted in the following equation together with Avogadro's number:

    .. math::

        a_{BET} = n_m A_N \sigma


    *Limitations*

    While a standard for surface area determinations, the BET area should be
    used with care, as there are many assumptions made in the calculation. To
    augment the validity of the BET method, Rouquerol [#]_ proposed several
    checks to ensure that the BET region selected is valid:

    * The BET constant (:math:`C`) obtained should be positive.
    * In the corresponding Rouquerol plot where :math:`n_{ads}(1-p/p_0)` is plotted
      with respect to :math:`p/p_0`, the points chosen for BET analysis should be
      strictly increasing.
    * The loading at the statistical monolayer should be situated within the
      limits of the BET region.

    This module implements all these checks.

    Regardless, the BET surface area should still be interpreted carefully. The following
    assumptions are implicitly made in this approach:

    * Adsorption takes place on the pore surface. Microporous materials which have pores
      in similar size as the molecule adsorbed cannot posses a realistic surface area.
    * The cross-sectional area of the molecule on the surface cannot be guaranteed
      For example, nitrogen has been known to adopt different orientations on the
      surface of some materials due to inter-molecular forces, which effectively
      lowers its cross-sectional area.
    * No account is made for heterogeneous adsorbate-adsorbent interaction in the BET theory.

    The returned fit standard errors assume ordinary least squares in the BET
    plot. The area standard error is a first-order propagation of that fit
    covariance, conditional on the selected pressure range and fixed molecular
    cross-sectional area. It does not include uncertainty in the isotherm,
    model selection, or cross-sectional area; the latter is an approximation.

    References
    ----------
    .. [#] "Adsorption of Gases in Multimolecular Layers", S. Brunauer,
       P. H. Emmett and E. Teller, J. Amer. Chem. Soc., 60, 309 (1938)
    .. [#] "Adsorption by Powders & Porous Solids", F. Rouquerol, J Rouquerol
       and K. Sing, Academic Press, 1999

    See Also
    --------
    pygaps.characterisation.area_bet.area_BET_raw : low level method

    """
    # get adsorbate properties
    adsorbate = Adsorbate.find(isotherm.adsorbate)
    cross_section = adsorbate.get_prop("cross_sectional_area")

    # Read data in
    pressure, loading = get_iso_loading_and_pressure_ordered(
        isotherm, branch, {"loading_basis": "molar", "loading_unit": "mol"}, {"pressure_mode": "relative"}
    )

    # use the bet function
    result = area_BET_raw(
        {
            'pressure': pressure,
            'loading': loading,
            'cross_section': cross_section,
            'p_limits': p_limits,
        }
    )
    minimum, maximum = result['p_limit_indices']
    bet_area = result['area']
    n_monolayer = result['n_monolayer']
    p_monolayer = result['p_monolayer']
    slope = result['bet_slope']
    intercept = result['bet_intercept']

    if verbose:
        logger.info(
            textwrap.dedent(
                f"""\
            BET area: a = {bet_area:.4g} m2/{isotherm.material_unit}
            The BET constant is: C = {result['c_const']:.1f}
            Minimum pressure point is {pressure[minimum]:.3g} and maximum is {pressure[maximum]:.3g}
            Statistical monolayer at: n = {n_monolayer:.3g} mol/{isotherm.material_unit}
            The slope of the BET fit: s = {slope:.3g}
            The intercept of the BET fit: i = {intercept:.3g}
            """
            )
        )

        # Generate plot of the BET points chosen
        from pygaps.graphing.calc_graphs import bet_plot

        bet_plot(
            pressure,
            bet_transform(pressure, loading),
            minimum,
            maximum,
            slope,
            intercept,
            p_monolayer,
            bet_transform(p_monolayer, n_monolayer),
        )

        # Generate plot of the Rouquerol points chosen
        from pygaps.graphing.calc_graphs import roq_plot

        roq_plot(
            pressure,
            roq_transform(pressure, loading),
            minimum,
            maximum,
            p_monolayer,
            roq_transform(p_monolayer, n_monolayer),
        )

    return result


def area_BET_raw(data: dict):
    """
    Calculate BET-determined surface area.

    This is a 'bare-bones' function to calculate BET surface area which is
    designed as a low-level alternative to the main function. Supply a
    dictionary containing ``pressure``, ``loading``, and ``cross_section``;
    ``p_limits`` is optional.

    Parameters
    ----------
    data : dict
        Calculation inputs:

        - ``pressure`` : relative pressures.
        - ``loading`` : loadings in mol/basis.
        - ``cross_section`` : molecular cross-sectional area in nm^2.
        - ``p_limits`` : optional inclusive pressure range.

    Returns
    -------
    dict
        Dictionary containing:

        - ``area`` (float): BET surface area in m² per adsorbent basis.
        - ``c_const`` (float): dimensionless BET constant.
        - ``n_monolayer`` (float): monolayer loading in mol per adsorbent basis.
        - ``p_monolayer`` (float): relative pressure at the monolayer.
        - ``bet_slope`` (float): BET plot slope in adsorbent basis/mol.
        - ``bet_intercept`` (float): BET plot intercept in adsorbent basis/mol.
        - ``corr_coef`` (float): correlation coefficient of the BET linear fit.
        - ``p_limit_indices`` (tuple[int, int]): inclusive start and end indices
          of the points used from the supplied pressure and loading arrays.
        - ``area_stderr`` (float): first-order propagated standard error of
          area, in m² per adsorbent basis.
        - ``bet_slope_stderr`` (float): standard error of ``bet_slope``.
        - ``bet_intercept_stderr`` (float): standard error of ``bet_intercept``.
        - ``cross_sectional_area`` (float): supplied molecular cross-sectional
          area in nm², treated as exact in the reported area uncertainty.

        The regression standard errors and propagated area standard error are
        conditional on the selected pressure range and ordinary least squares
        assumptions. They do not include uncertainty in the isotherm,
        pressure-range selection, or molecular cross-sectional area.

    """
    if not isinstance(data, dict):
        raise ParameterError("BET raw inputs must be supplied as a dictionary.")
    missing = {'pressure', 'loading', 'cross_section'} - data.keys()
    if missing:
        raise ParameterError(f"Missing required BET input keys: {', '.join(sorted(missing))}.")

    pressure = data['pressure']
    loading = data['loading']
    cross_section = data['cross_section']
    p_limits = data.get('p_limits')

    # Check lengths
    if len(pressure) == 0:
        raise ParameterError("Empty input values!")
    if len(pressure) != len(loading):
        raise ParameterError("The length of the pressure and loading arrays do not match.")

    # Ensure numpy arrays, if not already
    loading = numpy.asarray(loading)
    pressure = numpy.asarray(pressure)

    # select the maximum and minimum of the points and the pressure associated
    minimum = 0
    maximum = len(pressure) - 1  # As we want absolute position

    if p_limits is None:
        # Generate the Rouquerol array
        roq_t_array = roq_transform(pressure, loading)

        # Stop before the first non-increasing Rouquerol value.
        for index, value in enumerate(roq_t_array[:-1]):
            if value >= roq_t_array[index + 1]:
                maximum = index
                break

        # Min pressure is taken as 10% of max
        min_p = pressure[maximum] * 0.1
        minimum = numpy.searchsorted(pressure, min_p)

    else:
        minimum, maximum = get_pressure_limit_indices(pressure, p_limits)

    if maximum - minimum < 2:  # (for 3 point minimum)
        raise CalculationError("The isotherm does not have enough points (at least 3) in the BET region. Unable to calculate BET area.")
    pressure = pressure[minimum : maximum + 1]
    loading = loading[minimum : maximum + 1]

    # calculate the BET transform, slope and intercept
    bet_t_array = bet_transform(
        pressure,
        loading,
    )
    slope, intercept, corr_coef, slope_stderr, intercept_stderr = bet_fit(
        pressure,
        bet_t_array,
    )

    # calculate the BET parameters
    n_monolayer, p_monolayer, c_const, bet_area = bet_parameters(
        slope,
        intercept,
        cross_section,
    )

    # Checks for consistency
    if c_const < 0:
        logger.warning("The C constant is negative.")
    if corr_coef < 0.99:
        logger.warning("The correlation is not linear.")
    if not loading[0] < n_monolayer < loading[-1]:
        logger.warning("The monolayer point is not within the BET region")

    slope_intercept_covariance = -numpy.mean(pressure) * slope_stderr**2
    monolayer_variance = n_monolayer**4 * (
        slope_stderr**2 + intercept_stderr**2 + 2 * slope_intercept_covariance
    )
    area_stderr = (
        cross_section
        * (10 ** (-18))
        * constants.Avogadro
        * numpy.sqrt(numpy.maximum(monolayer_variance, 0))
    )

    return {
        'area': bet_area,
        'c_const': c_const,
        'n_monolayer': n_monolayer,
        'p_monolayer': p_monolayer,
        'bet_slope': slope,
        'bet_intercept': intercept,
        'corr_coef': corr_coef,
        'p_limit_indices': (minimum, maximum),
        'area_stderr': area_stderr,
        'bet_slope_stderr': slope_stderr,
        'bet_intercept_stderr': intercept_stderr,
        'cross_sectional_area': cross_section,
    }


def roq_transform(pressure, loading):
    """Rouquerol transform function."""
    return loading * (1 - pressure)


def bet_transform(pressure, loading):
    """BET transform function."""
    return pressure / roq_transform(pressure, loading)


def bet_fit(pressure, bet_points) -> tuple[float, float, float, float, float]:
    """Return BET fit coefficients, correlation, and slope/intercept errors."""
    slope, intercept, corr_coef, _, slope_stderr = stats.linregress(pressure, bet_points)
    slope = cast(float, slope)
    intercept = cast(float, intercept)
    corr_coef = cast(float, corr_coef)
    slope_stderr = cast(float, slope_stderr)
    intercept_stderr = slope_stderr * numpy.sqrt(numpy.mean(numpy.square(pressure)))
    intercept_stderr = cast(float, intercept_stderr)
    return (
        slope,
        intercept,
        corr_coef,
        slope_stderr,
        intercept_stderr,
    )


def bet_parameters(slope, intercept, cross_section):
    """Calculate the BET parameters from slope and intercept."""
    c_const = (slope / intercept) + 1
    n_monolayer = 1 / (intercept * c_const)
    p_monolayer = 1 / (numpy.sqrt(c_const) + 1)
    bet_area = n_monolayer * cross_section * (10 ** (-18)) * constants.Avogadro
    return n_monolayer, p_monolayer, c_const, bet_area


def simple_bet(pressure, n_monolayer, c_const):
    """Return loading at a pressure using a simple BET equation."""
    return n_monolayer * c_const * pressure / (1 - pressure) / (1 - pressure + c_const * pressure)
