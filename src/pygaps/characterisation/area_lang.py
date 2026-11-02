"""Langmuir area calculations."""

import textwrap
import warnings
from typing import TYPE_CHECKING
from typing import cast

import numpy
from scipy import constants
from scipy import stats
from scipy.optimize import OptimizeWarning
from scipy.optimize import curve_fit

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
    fit_method: str = 'nonlinear',
):
    r"""
    Calculate the Langmuir area of an isotherm.

    The optional ``p_limits`` parameter specifies the inclusive pressure range.
    By default, the routine uses 5-90% of the maximum input pressure. Always
    justify the selected pressure range for scientific use.

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
    fit_method : {'nonlinear', 'linearized'}, optional
        Fit the Langmuir equation directly to loading values (the default), or
        use the legacy linear regression of pressure/loading against pressure.

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
        - ``corr_coef`` (float) : correlation coefficient between observed and fitted loading
        - ``r_squared`` (float) : coefficient of determination in loading space
        - ``loading_rmse`` (float) : root-mean-square residual in loading units
        - ``area_stderr`` (float) : conditional standard error of the area estimate
        - ``n_monolayer_stderr`` (float) : standard error of the monolayer loading
        - ``langmuir_slope_stderr`` (float) : standard error of the theoretical plot slope
        - ``langmuir_intercept_stderr`` (float) : standard error of the theoretical plot intercept
        - ``fit_method`` (str) : estimator used
        - ``selected_p_limits`` (tuple[float, float]) : inclusive pressure interval actually used for fitting
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

    The traditional linearized estimator plots :math:`\frac{P}{n}` against
    pressure and derives :math:`n_m` and K from the slope and intercept. This
    remains available as ``fit_method='linearized'``. The default estimator
    instead fits the Langmuir equation directly to loading values, avoiding
    the transformed response and its pressure-dependent error propagation.

    .. math::

        n_m = \frac{1}{s}

        K = \frac{1}{i * n_m}

    The surface area can then be calculated by using the moles adsorbed at the
    monolayer. If the specific area taken by one of the adsorbate molecules on the surface
    is known, it is inserted in the following equation together with Avogadro's number:

    .. math::

        a(Langmuir) = n_m A_N \sigma

    *Limitations*

    The Langmuir method for determining surface area assumes that only one
    single layer is adsorbed on the surface of the material. As most adsorption
    processes (except chemisorption) do not follow this behaviour, regard the
    Langmuir surface area as an estimate.

    By default, the Langmuir model is fitted nonlinearly to loading values by
    unweighted least squares, assuming independent errors with constant
    absolute variance in loading. The ``linearized`` option instead performs
    ordinary least squares on the transformed Langmuir plot. Returned residual
    diagnostics are calculated in the original loading domain. The area
    standard error is conditional on the selected pressure range and fixed
    molecular cross-sectional area; it does not include uncertainty in the
    isotherm, model selection, or cross-sectional area.
    The automatic pressure interval (5-90% of maximum input pressure) is an
    estimate.

    The calculation emits warnings when the Langmuir constant, monolayer
    loading, or area is not positive and finite. These warnings do not prevent
    an estimate from being returned.

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
            'fit_method': fit_method,
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
    ``p_limits`` and ``fit_method`` are optional. The automatic 5-90% pressure
    interval is a convenience heuristic, not a model-validity test.

    By default, the Langmuir model is fitted nonlinearly to loading values by
    unweighted least squares, assuming independent errors with constant
    absolute variance in loading. ``fit_method='linearized'`` selects the
    legacy ordinary least squares fit to pressure/loading versus pressure.
    Residual diagnostics are calculated in the original loading domain. The
    nonlinear fit covariance and propagated area standard error are
    conditional on this assumption and the selected pressure range; they do
    not include uncertainty in the isotherm, pressure-range selection, or
    molecular cross-sectional area.

    Parameters
    ----------
    data : dict
        Calculation inputs:

        - ``pressure`` : finite, ascending relative pressures between 0 and 1.
        - ``loading`` : finite, non-negative loadings in mol/basis.
        - ``cross_section`` : positive finite molecular cross-sectional area in nm^2.
        - ``p_limits`` : optional inclusive pressure range.
        - ``fit_method`` : optional ``'nonlinear'`` (default) or ``'linearized'``.

        Pressure and loading must be one-dimensional arrays of equal length.
        Loading must be positive for every point selected for fitting; zero
        loading is allowed outside that range (for example, at the origin).

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
        - ``corr_coef`` (float): correlation coefficient between observed and
          predicted loading values.
        - ``p_limit_indices`` (tuple[int, int]): inclusive start and end indices
          of the points used from the supplied pressure and loading arrays.
        - ``area_stderr`` (float): conditional standard error of area, in m²
          per adsorbent basis.
        - ``n_monolayer_stderr`` (float): standard error of the fitted
          monolayer loading.
        - ``langmuir_slope_stderr`` (float): standard error of
          ``langmuir_slope``.
        - ``langmuir_intercept_stderr`` (float): standard error of
          ``langmuir_intercept``.
        - ``fit_method`` (str): estimator used.
        - ``selected_p_limits`` (tuple[float, float]): inclusive pressure
          interval actually used for fitting.
        - ``loading_residuals`` (array): observed minus fitted loading for
          points in the selected pressure range.
        - ``loading_rmse`` (float): root-mean-square loading residual.
        - ``r_squared`` (float): coefficient of determination in loading space.
        - ``cross_sectional_area`` (float): supplied molecular cross-sectional
          area in nm², treated as exact in the reported area uncertainty.

        A warning is emitted if the Langmuir constant, monolayer loading, or
        area is not positive and finite; the estimate is still returned.

    """
    if not isinstance(data, dict):
        raise ParameterError("Langmuir raw inputs must be supplied as a dictionary.")
    missing = {'pressure', 'loading', 'cross_section'} - data.keys()
    if missing:
        raise ParameterError(f"Missing required Langmuir input keys: {', '.join(sorted(missing))}.")

    try:
        pressure = numpy.asarray(data['pressure'], dtype=float)
        loading = numpy.asarray(data['loading'], dtype=float)
        cross_section = numpy.asarray(data['cross_section'], dtype=float)
    except (OverflowError, TypeError, ValueError) as err:
        raise ParameterError("Langmuir inputs must contain numeric values.") from err

    p_limits = data.get('p_limits')

    if pressure.ndim != 1 or loading.ndim != 1:
        raise ParameterError("The pressure and loading inputs must be one-dimensional.")
    if pressure.size == 0:
        raise ParameterError("Empty input values!")
    if pressure.size != loading.size:
        raise ParameterError("The length of the pressure and loading arrays do not match.")
    if not numpy.isfinite(pressure).all() or not numpy.isfinite(loading).all():
        raise ParameterError("Pressure and loading values must be finite.")
    if numpy.any((pressure < 0) | (pressure > 1)):
        raise ParameterError("Relative pressures must be between 0 and 1.")
    if numpy.any(loading < 0):
        raise ParameterError("Loading values must be non-negative.")
    if numpy.any(numpy.diff(pressure) < 0):
        raise ParameterError("Pressure values must be in ascending order.")
    if (
        cross_section.shape != ()
        or not numpy.isfinite(cross_section).item()
        or cross_section.item() <= 0
    ):
        raise ParameterError("The molecular cross-sectional area must be a positive finite number.")
    cross_section = float(cross_section)
    fit_method = data.get('fit_method', 'nonlinear')
    if fit_method not in {'nonlinear', 'linearized'}:
        raise ParameterError("Langmuir fit_method must be 'nonlinear' or 'linearized'.")

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
    if maximum - minimum < 2:  # At least 3 points are required for regression.
        raise CalculationError(
            "The isotherm does not have enough points (at least 3) in selected "
            "region. Unable to calculate Langmuir area."
        )
    pressure = pressure[minimum : maximum + 1]
    loading = loading[minimum : maximum + 1]
    if numpy.any(loading == 0):
        raise ParameterError("Loading must be positive in the selected pressure range for the Langmuir transform.")
    if numpy.unique(pressure).size < 2:
        raise CalculationError("At least two distinct pressure values are required for the Langmuir fit.")

    if fit_method == 'nonlinear':
        n_monolayer, langmuir_const, covariance = langmuir_fit_nonlinear(
            pressure,
            loading,
        )
        slope = 1 / n_monolayer
        intercept = 1 / (langmuir_const * n_monolayer)
        slope_gradient = numpy.array([-1 / n_monolayer**2, 0.0])
        intercept_gradient = numpy.array(
            [
                -1 / (langmuir_const * n_monolayer**2),
                -1 / (langmuir_const**2 * n_monolayer),
            ]
        )
        slope_variance = slope_gradient @ covariance @ slope_gradient
        intercept_variance = intercept_gradient @ covariance @ intercept_gradient
        n_monolayer_stderr = numpy.sqrt(numpy.maximum(covariance[0, 0], 0))
        slope_stderr = numpy.sqrt(numpy.maximum(slope_variance, 0))
        intercept_stderr = numpy.sqrt(numpy.maximum(intercept_variance, 0))
    else:
        with numpy.errstate(over='ignore', divide='ignore', invalid='ignore'):
            langmuir_array = langmuir_transform(pressure, loading)
        if not numpy.isfinite(langmuir_array).all():
            raise CalculationError("The Langmuir transform contains non-finite values.")
        with numpy.errstate(over='ignore', divide='ignore', invalid='ignore'):
            fit_result = langmuir_fit(pressure, langmuir_array)
        if not numpy.isfinite(fit_result).all():
            raise CalculationError("The Langmuir fit contains non-finite values.")
        slope, intercept, _, slope_stderr, intercept_stderr = fit_result
        with numpy.errstate(over='ignore', divide='ignore', invalid='ignore'):
            n_monolayer, langmuir_const, _ = langmuir_parameters(
                slope,
                intercept,
                cross_section,
            )
        n_monolayer_stderr = n_monolayer**2 * slope_stderr

    langmuir_area = n_monolayer * cross_section * 1e-18 * constants.Avogadro
    with numpy.errstate(over='ignore', divide='ignore', invalid='ignore'):
        predicted_loading = simple_lang(pressure, n_monolayer, langmuir_const)
    loading_residuals = loading - predicted_loading
    if not numpy.isfinite(predicted_loading).all() or not numpy.isfinite(loading_residuals).all():
        raise CalculationError("The Langmuir model produced non-finite loading predictions.")
    with numpy.errstate(over='ignore', invalid='ignore'):
        total_variation = numpy.sum((loading - numpy.mean(loading)) ** 2)
    if total_variation <= 0 or not numpy.isfinite(total_variation):
        raise CalculationError("The selected loading values do not identify a Langmuir fit.")
    with numpy.errstate(over='ignore', invalid='ignore'):
        residual_sum_squares = numpy.sum(loading_residuals**2)
    r_squared = 1 - residual_sum_squares / total_variation
    with numpy.errstate(over='ignore', divide='ignore', invalid='ignore'):
        corr_coef = numpy.corrcoef(loading, predicted_loading)[0, 1]
    loading_rmse = numpy.sqrt(numpy.mean(loading_residuals**2))
    if not numpy.isfinite((r_squared, corr_coef, loading_rmse)).all():
        raise CalculationError("The Langmuir fit diagnostics contain non-finite values.")

    # Checks for consistency
    for parameter, value in (
        ("Langmuir constant", langmuir_const),
        ("monolayer loading", n_monolayer),
        ("Langmuir area", langmuir_area),
    ):
        if not numpy.isfinite(value) or value <= 0:
            logger.warning(f"The {parameter} is not positive and finite.")
    if r_squared < 0.99:
        logger.warning("The Langmuir fit has an R-squared below 0.99 in loading space.")

    area_stderr = cross_section * 1e-18 * constants.Avogadro * n_monolayer_stderr

    return {
        'area': langmuir_area,
        'langmuir_const': langmuir_const,
        'n_monolayer': n_monolayer,
        'langmuir_slope': slope,
        'langmuir_intercept': intercept,
        'corr_coef': corr_coef,
        'p_limit_indices': (minimum, maximum),
        'area_stderr': area_stderr,
        'n_monolayer_stderr': n_monolayer_stderr,
        'langmuir_slope_stderr': slope_stderr,
        'langmuir_intercept_stderr': intercept_stderr,
        'fit_method': fit_method,
        'selected_p_limits': (float(pressure[0]), float(pressure[-1])),
        'loading_residuals': loading_residuals,
        'loading_rmse': loading_rmse,
        'r_squared': r_squared,
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


def langmuir_fit_nonlinear(pressure, loading):
    """Fit the Langmuir equation to loading and return parameters and covariance."""
    initial_capacity = float(numpy.max(loading) * 1.1)
    initial_constant = float(1 / max(numpy.median(pressure), numpy.finfo(float).eps))
    if not numpy.isfinite((initial_capacity, initial_constant)).all():
        raise CalculationError("The nonlinear Langmuir fit could not be initialized.")

    with warnings.catch_warnings():
        warnings.simplefilter('error', OptimizeWarning)
        try:
            parameters, covariance = curve_fit(
                simple_lang,
                pressure,
                loading,
                p0=(initial_capacity, initial_constant),
                bounds=(0, numpy.inf),
                x_scale='jac',
                ftol=1e-12,
                xtol=1e-12,
                gtol=1e-12,
                maxfev=10000,
            )
        except (OptimizeWarning, RuntimeError, ValueError, FloatingPointError) as err:
            raise CalculationError("The nonlinear Langmuir fit failed.") from err
    if not numpy.isfinite(parameters).all() or not numpy.isfinite(covariance).all():
        raise CalculationError("The nonlinear Langmuir fit returned non-finite values.")

    n_monolayer, langmuir_const = parameters
    if n_monolayer <= 0 or langmuir_const <= 0:
        raise CalculationError("The nonlinear Langmuir fit returned non-positive parameters.")
    return n_monolayer, langmuir_const, covariance
