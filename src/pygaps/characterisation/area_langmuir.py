"""This module contains Langmuir area calculations."""

import logging

logger = logging.getLogger('pygaps')
import textwrap
import warnings

import numpy

from .. import scipy
from ..core.adsorbate import Adsorbate
from ..graphing.calc_graphs import langmuir_plot
from ..utilities.exceptions import CalculationError
from ..utilities.exceptions import ParameterError
from ..utilities.exceptions import pgError


def area_langmuir(isotherm, branch='ads', limits=None, verbose=False):
    r"""
    Calculate the Langmuir-determined surface area of an isotherm.

    Parameters
    ----------
    isotherm : PointIsotherm
        The isotherm of which to calculate the Langmuir surface area.
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
        volume of material):

        - ``area`` (float) : calculated Langmuir surface area, in m2/unit of material
        - ``langmuir_const`` (float) : the constant in the Langmuir fit
        - ``n_monolayer`` (float) : the amount adsorbed at the monolayer
        - ``langmuir_slope`` (float) : slope of the Langmuir plot
        - ``langmuir_intercept`` (float) : intercept of the Langmuir plot
        - ``corr_coef`` (float) : correlation coefficient of the linear region in the Langmuir plot

    Notes
    -----
    *Description*

    The Langmuir theory [#]_, proposed at the start of the 20th century, states that
    adsorption happens on active sites on a surface in a single layer. It is
    derived based on several assumptions.

        * All sites are equivalent and have the same chance of being occupied
        * Each adsorbate molecule can occupy one adsorption site
        * There are no interactions between adsorbed molecules
        * The rates of adsorption and desorption are proportional to the number
          of sites currently free and currently occupied, respectively
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
    .. [#] I. Langmuir, J. American Chemical Society 38, 2219(1916); 40, 1368(1918)

    """
    # get adsorbate properties
    adsorbate = Adsorbate.find(isotherm.adsorbate)
    cross_section = adsorbate.get_prop("cross_sectional_area")

    # Read data in
    loading = isotherm.loading(
        branch=branch, loading_unit='mol', loading_basis='molar'
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
    ) = area_langmuir_raw(pressure, loading, cross_section, limits=limits)

    if verbose:

        logger.info(
            textwrap.dedent(
                f"""\
            Langmuir surface area: a = {langmuir_area:.2e} m2/{isotherm.material_unit}
            Minimum pressure point is {pressure[minimum]:.3f} and maximum is {pressure[maximum -1]:.3f}
            The slope of the Langmuir line: s = {slope:.2e}
            The intercept of the Langmuir line: i = {intercept:.2e}
            The Langmuir constant is: K = {langmuir_const:.1f}
            Amount for a monolayer: n = {n_monolayer:.2e} mol/{isotherm.material_unit}"""
            )
        )

        # Generate plot of the langmuir points chosen
        langmuir_plot(
            pressure, langmuir_transform(pressure, loading), minimum, maximum,
            slope, intercept
        )

    return {
        'area': langmuir_area,
        'langmuir_const': langmuir_const,
        'n_monolayer': n_monolayer,
        'langmuir_slope': slope,
        'langmuir_intercept': intercept,
        'corr_coef': corr_coef,
        'limits': [minimum, maximum]
    }


def area_langmuir_raw(pressure, loading, cross_section, limits=None):
    """
    Calculate Langmuir-determined surface area.

    This is a 'bare-bones' function to calculate Langmuir surface area which is
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
    if len(pressure) != len(loading):
        raise ParameterError(
            "The length of the pressure and loading arrays do not match."
        )
    # Ensure numpy arrays, if not already
    loading = numpy.asarray(loading)
    pressure = numpy.asarray(pressure)

    # select the maximum and minimum of the points and the pressure associated
    if limits is None:
        limits = [0.05, 0.9]

    maximum = len(pressure) - 1
    minimum = 0

    if limits[1]:
        maximum = numpy.searchsorted(pressure, limits[1])

    if limits[0]:
        minimum = numpy.searchsorted(pressure, limits[0])

    if maximum - minimum < 3:  # (for 2 point minimum)
        raise CalculationError(
            "The isotherm does not have enough points (at least 2) "
            "in selected region. Unable to calculate Langmuir area."
        )

    # calculate the Langmuir slope and intercept
    langmuir_array = langmuir_transform(
        pressure[minimum:maximum], loading[minimum:maximum]
    )
    slope, intercept, corr_coef = langmuir_optimisation(
        pressure[minimum:maximum], langmuir_array
    )

    # calculate the Langmuir parameters
    n_monolayer, langmuir_const, langmuir_area = langmuir_parameters(
        slope, intercept, cross_section
    )

    # Checks for consistency
    if langmuir_const < 0:
        warnings.warn("The Langmuir constant is negative.")
    if corr_coef < 0.99:
        warnings.warn("The correlation is not linear.")

    return (
        langmuir_area, langmuir_const, n_monolayer, slope, intercept, minimum,
        maximum, corr_coef
    )


def langmuir_transform(pressure, loading):
    """Langmuir transform function."""
    return pressure / loading


def langmuir_optimisation(pressure, langmuir_points):
    """Finds the slope and intercept of the Langmuir region."""
    slope, intercept, corr_coef, p, stderr = scipy.stats.linregress(
        pressure, langmuir_points
    )
    return slope, intercept, corr_coef


def langmuir_parameters(slope, intercept, cross_section):
    """Calculates the Langmuir parameters from the slope and intercept."""
    n_monolayer = 1 / slope
    langmuir_const = 1 / (intercept * n_monolayer)
    langmuir_area = n_monolayer * cross_section * \
        (10**(-18)) * scipy.const.Avogadro
    return n_monolayer, langmuir_const, langmuir_area
