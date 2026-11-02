"""Langmuir area calculations."""

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


def area_langmuir(
    isotherm: "PointIsotherm | ModelIsotherm",
    branch: str = 'ads',
    p_limits: "tuple[float, float]" = None,
    verbose: bool = False,
):
    r"""
    Calculate the Langmuir area of an isotherm.

    The optional ``p_limits`` parameter allows to specify the upper and lower
    pressure limits to calculate the Langmuir area, otherwise the limits will be
    automatically set to 5-90% of isotherm pressure range.

    Parameters
    ----------
    isotherm : PointIsotherm, ModelIsotherm
        The isotherm of which to calculate the Langmuir surface area.
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

        - ``area`` (float) : calculated Langmuir surface area, in m2/unit of material
        - ``langmuir_const`` (float) : the unitless constant in the relative-pressure Langmuir fit
        - ``n_monolayer`` (float) : the amount adsorbed at the monolayer, in mol/unit of material
        - ``langmuir_slope`` (float) : slope of the Langmuir plot, in unit of material/mol
        - ``langmuir_intercept`` (float) : intercept of the Langmuir plot, in unit of material/mol
        - ``corr_coef`` (float) : correlation coefficient of the linear region in the Langmuir plot
        - ``area_stderr`` (float) : delta-method standard error of the area from the linear fit
        - ``langmuir_slope_stderr`` (float) : standard error of the Langmuir plot slope
        - ``langmuir_intercept_stderr`` (float) : standard error of the Langmuir plot intercept
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

    The Langmuir theory [#]_, proposed at the start of the 20th century, states
    that adsorption happens on individual active sites on a surface in a single
    layer. It is derived based on several assumptions.

    * All sites are equivalent and have the same chance of being occupied.
    * Each adsorbate molecule can occupy one adsorption site.
    * There are no interactions between adsorbed molecules.
    * The rates of adsorption and desorption are proportional to the number of
      sites currently free and currently occupied, respectively.
    * Adsorption is complete when all sites are filled.

    The Langmuir equation is then:

    .. math::

        n = n_m\frac{KP}{1+KP}

    The equation can be rearranged as:

    .. math::

        \frac{P}{n} = \frac{1}{K n_m} + \frac{P}{n_m}

    Assuming the data can be fitted with a Langmuir model, by plotting
    :math:`\frac{P}{n}` against pressure, a line will be obtained. The slope and
    intercept of this line can then be used to calculate :math:`n_{m}`,
    the amount adsorbed at the monolayer, as well as K, the Langmuir constant.

    .. math::

        n_m = \frac{1}{s}

        K = \frac{1}{i * n_m}

    The surface area can then be calculated by using the moles adsorbed at the
    monolayer. If the specific area taken by one of the adsorbate molecules on the surface
    is known, it is inserted in the following equation together with Avogadro's number:

    .. math::

        a(Langmuir) = n_m A_N \sigma

    *Limitations*

    The Langmuir method for determining surface area assumes that only one single
    layer is adsorbed on the surface of the material. As most adsorption processes
    (except chemisorption) don't follow this behaviour, it is important to regard
    the Langmuir surface area as an estimate.

    The returned fit standard errors assume ordinary least squares in the
    Langmuir plot. The area standard error is a first-order propagation of the
    slope uncertainty, conditional on the selected pressure range and fixed
    molecular cross-sectional area. It does not include uncertainty in the
    isotherm, model selection, or cross-sectional area; the latter is an
    approximation.

    References
    ----------
    .. [#] I. Langmuir, J. Amer. Chem. Soc., 38, 2219 (1916); 40, 1368 (1918)

    See Also
    --------
    pygaps.characterisation.area_lang.area_langmuir_raw : low level method

    """
    # get adsorbate properties
    adsorbate = Adsorbate.find(isotherm.adsorbate)
    cross_section = adsorbate.get_prop("cross_sectional_area")

    # Read data in
    pressure, loading = get_iso_loading_and_pressure_ordered(
        isotherm, branch, {"loading_basis": "molar", "loading_unit": "mol"}, {"pressure_mode": "relative"}
    )

    # use the langmuir function
    result = area_langmuir_raw(
        {
            'pressure': pressure,
            'loading': loading,
            'cross_section': cross_section,
            'p_limits': p_limits,
        }
    )
    minimum, maximum = result['p_limit_indices']
    langmuir_area = result['area']
    langmuir_const = result['langmuir_const']
    n_monolayer = result['n_monolayer']
    slope = result['langmuir_slope']
    intercept = result['langmuir_intercept']

    if verbose:
        logger.info(
            textwrap.dedent(
                f"""\
            Langmuir area: a = {langmuir_area:.4g} m2/{isotherm.material_unit}
            Minimum pressure point is {pressure[minimum]:.3g} and maximum is {pressure[maximum]:.3g}
            The Langmuir constant is: K = {langmuir_const:.3g}
            Amount Langmuir monolayer is: n = {n_monolayer:.3g} mol/{isotherm.material_unit}
            The slope of the Langmuir fit: s = {slope:.3g}
            The intercept of the Langmuir fit: i = {intercept:.3g}
            """
            )
        )

        # Generate plot of the langmuir points chosen
        from pygaps.graphing.calc_graphs import langmuir_plot

        langmuir_plot(
            pressure,
            langmuir_transform(pressure, loading),
            minimum,
            maximum,
            slope,
            intercept,
        )

    return result


def area_langmuir_raw(data: dict):
    """
    Calculate Langmuir-determined surface area.

    This is a 'bare-bones' function to calculate Langmuir surface area which is
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

        - ``area`` (float): Langmuir surface area in m² per adsorbent basis.
        - ``langmuir_const`` (float): dimensionless Langmuir constant for
          relative pressure.
        - ``n_monolayer`` (float): monolayer loading in mol per adsorbent basis.
        - ``langmuir_slope`` (float): Langmuir plot slope in adsorbent basis/mol.
        - ``langmuir_intercept`` (float): Langmuir plot intercept in adsorbent
          basis/mol.
        - ``corr_coef`` (float): correlation coefficient of the Langmuir
          linear fit.
        - ``p_limit_indices`` (tuple[int, int]): inclusive start and end indices
          of the points used from the supplied pressure and loading arrays.
        - ``area_stderr`` (float): first-order propagated standard error of
          area, in m² per adsorbent basis.
        - ``langmuir_slope_stderr`` (float): standard error of
          ``langmuir_slope``.
        - ``langmuir_intercept_stderr`` (float): standard error of
          ``langmuir_intercept``.
        - ``cross_sectional_area`` (float): supplied molecular cross-sectional
          area in nm², treated as exact in the reported area uncertainty.

        The regression standard errors and propagated area standard error are
        conditional on the selected pressure range and ordinary least squares
        assumptions. They do not include uncertainty in the isotherm,
        pressure-range selection, or molecular cross-sectional area.

    """
    if not isinstance(data, dict):
        raise ParameterError("Langmuir raw inputs must be supplied as a dictionary.")
    missing = {'pressure', 'loading', 'cross_section'} - data.keys()
    if missing:
        raise ParameterError(f"Missing required Langmuir input keys: {', '.join(sorted(missing))}.")

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
        # Give reasonable automatic limits
        # Min pressure is taken as 5% of max
        # Max pressure is taken as 90% of max
        p_limits = [
            pressure[maximum] * 0.05,
            pressure[maximum] * 0.9,
        ]

    minimum, maximum = get_pressure_limit_indices(pressure, p_limits)
    if maximum - minimum < 2:  # (for 2 point minimum)
        raise CalculationError(
            "The isotherm does not have enough points (at least 2) in selected region. Unable to calculate Langmuir area."
        )
    pressure = pressure[minimum : maximum + 1]
    loading = loading[minimum : maximum + 1]

    # calculate the Langmuir slope and intercept
    langmuir_array = langmuir_transform(
        pressure,
        loading,
    )
    slope, intercept, corr_coef, slope_stderr, intercept_stderr = langmuir_fit(
        pressure,
        langmuir_array,
    )

    # calculate the Langmuir parameters
    n_monolayer, langmuir_const, langmuir_area = langmuir_parameters(
        slope,
        intercept,
        cross_section,
    )

    # Checks for consistency
    if langmuir_const < 0:
        logger.warning("The Langmuir constant is negative.")
    if corr_coef < 0.99:
        logger.warning("The correlation is not linear.")

    area_stderr = (
        cross_section
        * (10 ** (-18))
        * constants.Avogadro
        * n_monolayer**2
        * slope_stderr
    )

    return {
        'area': langmuir_area,
        'langmuir_const': langmuir_const,
        'n_monolayer': n_monolayer,
        'langmuir_slope': slope,
        'langmuir_intercept': intercept,
        'corr_coef': corr_coef,
        'p_limit_indices': (minimum, maximum),
        'area_stderr': area_stderr,
        'langmuir_slope_stderr': slope_stderr,
        'langmuir_intercept_stderr': intercept_stderr,
        'cross_sectional_area': cross_section,
    }


def langmuir_transform(pressure, loading):
    """Langmuir transform function."""
    return pressure / loading


def langmuir_fit(pressure, langmuir_points) -> tuple[float, float, float, float, float]:
    """Return Langmuir fit coefficients, correlation, and slope/intercept errors."""
    slope, intercept, corr_coef, _, slope_stderr = stats.linregress(pressure, langmuir_points)
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


def langmuir_parameters(slope, intercept, cross_section):
    """Calculate the Langmuir parameters from slope and intercept."""
    n_monolayer = 1 / slope
    langmuir_const = 1 / (intercept * n_monolayer)
    langmuir_area = n_monolayer * cross_section * (10 ** (-18)) * constants.Avogadro
    return n_monolayer, langmuir_const, langmuir_area


def simple_lang(pressure, n_total, k_const):
    """Return loading at a pressure using a simple Langmuir equation."""
    return n_total * k_const * pressure / (1 + k_const * pressure)
