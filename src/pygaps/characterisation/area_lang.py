"""This module contains Langmuir area calculations."""

import textwrap

import numpy
from scipy import constants
from scipy import stats

from pygaps import logger
from pygaps.core.adsorbate import Adsorbate
from pygaps.core.modelisotherm import ModelIsotherm
from pygaps.core.pointisotherm import PointIsotherm
from pygaps.utilities.exceptions import CalculationError
from pygaps.utilities.exceptions import ParameterError
from pygaps.utilities.exceptions import pgError


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
        Pressure range in which to perform the calculation.
    verbose : bool, optional
        Prints extra information and plots graphs of the calculation.

    Returns
    -------
    dict
        A dictionary of results with the following components. The basis of these
        results will be derived from the basis of the isotherm (per mass, per
        volume, or per mole of adsorbent):

        - ``area`` (float) : calculated Langmuir surface area, in m2/unit of material
        - ``langmuir_const`` (float) : the constant in the Langmuir fit
        - ``n_monolayer`` (float) : the amount adsorbed at the monolayer
        - ``langmuir_slope`` (float) : slope of the Langmuir plot
        - ``langmuir_intercept`` (float) : intercept of the Langmuir plot
        - ``corr_coef`` (float) : correlation coefficient of the linear region in the Langmuir plot

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
    except pgError as err:
        raise CalculationError(
            "The isotherm cannot be converted to a relative basis. "
            "Is your isotherm supercritical?"
        ) from err

    # If on an desorption branch, data will be reversed
    if branch == 'des':
        loading = loading[::-1]
        pressure = pressure[::-1]

    # use the langmuir function
    (
        langmuir_area,
        langmuir_const,
        n_monolayer,
        slope,
        intercept,
        minimum,
        maximum,
        corr_coef,
    ) = area_langmuir_raw(
        pressure,
        loading,
        cross_section,
        p_limits,
    )

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

    return {
        'area': langmuir_area,
        'langmuir_const': langmuir_const,
        'n_monolayer': n_monolayer,
        'langmuir_slope': slope,
        'langmuir_intercept': intercept,
        'corr_coef': corr_coef,
        'p_limit_indices': (minimum, maximum),
    }


def area_langmuir_raw(
    pressure: "list[float]",
    loading: "list[float]",
    cross_section: float,
    p_limits: "tuple[float,float]" = None,
):
    """
    Calculate Langmuir-determined surface area.

    This is a 'bare-bones' function to calculate Langmuir surface area which is
    designed as a low-level alternative to the main function.
    Designed for advanced use, its parameters have to be manually specified.

    Parameters
    ----------
    pressure : list[float]
        Pressures, relative.
    loading : list[float]
        Loadings, in mol/basis.
    cross_section : float
        Adsorbed cross-section of the molecule of the adsorbate, in nm.
    p_limits : tuple[float, float], optional
        Pressure range in which to perform the calculation.

    Returns
    -------
    langmuir_area : float
        Calculated Langmuir surface area.
    langmuir_const : float
        K constant from the Langmuir equation.
    n_monolayer : float
        Adsorbed quantity in the monolayer.
    slope : float
        Calculated slope of the Langmuir plot.
    intercept : float
        Calculated intercept of the Langmuir plot.
    minimum : float
        Minimum point taken for the linear region.
    maximum : float
        Maximum point taken for the linear region.
    corr_coef : float
        Correlation coefficient of the straight line in the Langmuir plot.

    """
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

    # Determine the limits
    if p_limits[0]:
        minimum = numpy.searchsorted(pressure, p_limits[0])
    if p_limits[1]:
        maximum = numpy.searchsorted(pressure, p_limits[1]) - 1
    if maximum - minimum < 2:  # (for 2 point minimum)
        raise CalculationError(
            "The isotherm does not have enough points (at least 2) "
            "in selected region. Unable to calculate Langmuir area."
        )
    pressure = pressure[minimum:maximum + 1]
    loading = loading[minimum:maximum + 1]

    # calculate the Langmuir slope and intercept
    langmuir_array = langmuir_transform(
        pressure,
        loading,
    )
    slope, intercept, corr_coef = langmuir_fit(
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

    return (
        langmuir_area,
        langmuir_const,
        n_monolayer,
        slope,
        intercept,
        minimum,
        maximum,
        corr_coef,
    )


def langmuir_transform(pressure, loading):
    """Langmuir transform function."""
    return pressure / loading


def langmuir_fit(pressure, langmuir_points):
    """Find the slope and intercept of the Langmuir region."""
    slope, intercept, corr_coef, p, stderr = stats.linregress(pressure, langmuir_points)
    return slope, intercept, corr_coef


def langmuir_parameters(slope, intercept, cross_section):
    """Calculate the Langmuir parameters from slope and intercept."""
    n_monolayer = 1 / slope
    langmuir_const = 1 / (intercept * n_monolayer)
    langmuir_area = n_monolayer * cross_section * (10**(-18)) * constants.Avogadro
    return n_monolayer, langmuir_const, langmuir_area


def simple_lang(pressure, n_total, k_const):
    """A simple Langmuir equation returning loading at a pressure."""
    return (n_total * k_const * pressure / (1 + k_const * pressure))
