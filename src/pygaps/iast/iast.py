"""Module calculating IAST, given the pure-component adsorption isotherm model."""

import logging

logger = logging.getLogger('pygaps')
import textwrap
import warnings

import numpy

from .. import scipy
from ..graphing.iast_graphs import plot_iast_svp
from ..graphing.iast_graphs import plot_iast_vle
from ..modelling import is_iast_model
from ..utilities.exceptions import CalculationError
from ..utilities.exceptions import ParameterError


def iast_binary_vle(
    isotherms,
    total_pressure,
    npoints=30,
    adsorbed_mole_fraction_guess=None,
    warningoff=False,
    verbose=False,
    ax=None
):
    """
    Perform IAST calculations to predict the vapour-liquid equilibrium curve
    at a fixed pressure, over the entire range of gas phase composition
    (0-1 of the first component).

    Pass a list of two of pure-component adsorption isotherms `isotherms`, with the
    first one being selected as a basis.

    Parameters
    ----------
    isotherms : list of ModelIsotherms or PointIsotherms
        Model adsorption isotherms.
        e.g. [methane_isotherm, ethane_isotherm]
    total_pressure : float
        Pressure at which the vapour-liquid equilibrium is to be
        calculated.
    npoints: int
        Number of points in the resulting curve. More points
        will be more computationally intensive.
    adsorbed_mole_fraction_guess : array or list, optional
        Starting guesses for adsorbed phase mole fractions that
        `iast` solves for.
    warningoff: bool, optional
        When False, warnings will print when the IAST
        calculation result required extrapolation of the pure-component
        adsorption isotherm beyond the highest pressure in the data.
    verbose : bool, optional
        Print off a extra information, as well as a graph.
    ax : matplotlib axes object, optional
        The axes object where to plot the graph if a new figure is
        not desired.

    Returns
    -------
    dict
        Dictionary with two components:
            - `y` the mole fraction of the selected adsorbate in the gas phase
            - `x` mole fraction of the selected adsorbate in the adsorbed phase

    """
    # Parameter checks
    if len(isotherms) != 2:
        raise ParameterError(
            "The binary equilibrium calculation can only take two components as parameters."
        )

    # Generate fractions array
    y_data = numpy.linspace(0.01, 0.99, npoints)
    binary_fractions = numpy.array((y_data, 1 - y_data)).transpose()

    # Generate the array of loadings
    component_loadings = numpy.zeros((npoints, 2))

    # Run IAST
    for index, fraction in enumerate(binary_fractions):
        component_loadings[index, :] = iast(
            isotherms,
            fraction,
            total_pressure,
            warningoff=warningoff,
            adsorbed_mole_fraction_guess=adsorbed_mole_fraction_guess
        )

    x_data = [x[0] / (x[0] + x[1]) for x in component_loadings]

    # Add start and end points
    x_data = numpy.concatenate([[0], x_data, [1]])
    y_data = numpy.concatenate([[0], y_data, [1]])

    # Generate the array of partial pressures
    if verbose:
        plot_iast_vle(
            x_data,
            y_data,
            isotherms[0].adsorbate,
            isotherms[1].adsorbate,
            total_pressure,
            isotherms[0].pressure_unit,
            ax=ax
        )

    return dict(x=x_data, y=y_data)


def iast_binary_svp(
    isotherms,
    mole_fractions,
    pressures,
    warningoff=False,
    adsorbed_mole_fraction_guess=None,
    verbose=False,
    ax=None
):
    """
    Perform IAST calculations to predict the selectivity of one of the components
    as a function of pressure.

    Pass a list of two of pure-component adsorption isotherms `isotherms`, with the
    first one being selected as a basis.

    Parameters
    ----------
    isotherms : list of ModelIsotherms or PointIsotherms
        Model adsorption isotherms.
        e.g. [methane_isotherm, ethane_isotherm]
    mole_fractions : float
        Fraction of the gas phase for each component. Must add to 1.
        e.g. [0.1, 0.9]
    pressures : list
        Pressure values at which the selectivity should be calculated.
    warningoff: bool, optional
        When False, warnings will print when the IAST
        calculation result required extrapolation of the pure-component
        adsorption isotherm beyond the highest pressure in the data.
    adsorbed_mole_fraction_guess : array or list, optional
        Starting guesses for adsorbed phase mole fractions that
        `iast` solves for.
    verbose : bool, optional
        Print off a extra information, as well as a graph.
    ax : matplotlib axes object, optional
        The axes object where to plot the graph if a new figure is
        not desired.

    Returns
    -------
    dict
        Dictionary with two components:
            - `selectivity` the selectivity of the selected component
            - `pressure` the pressure for each selectivity

    """

    # Parameter checks
    if len(isotherms) != 2 or len(mole_fractions) != 2:
        raise ParameterError(
            "The selectivity calculation can only take two components as parameters."
        )
    if sum(mole_fractions) != 1:
        raise ParameterError("Mole fractions do not add up to unity")

    # Convert to numpy arrays just in case
    pressures = numpy.asarray(pressures)
    mole_fractions = numpy.asarray(mole_fractions)

    # Generate the array of partial pressures
    component_loadings = numpy.zeros((len(pressures), 2))

    for index, pressure in enumerate(pressures):
        component_loadings[index, :] = iast(
            isotherms,
            mole_fractions,
            pressure,
            warningoff=warningoff,
            adsorbed_mole_fraction_guess=adsorbed_mole_fraction_guess
        )

    selectivities = [(x[0] / mole_fractions[0]) / (x[1] / mole_fractions[1])
                     for x in component_loadings]

    if verbose:
        plot_iast_svp(
            pressures,
            selectivities,
            isotherms[0].adsorbate,
            isotherms[1].adsorbate,
            mole_fractions[0],
            isotherms[0].pressure_unit,
            ax=ax
        )

    return dict(pressure=pressures, selectivity=selectivities)


def iast(
    isotherms,
    gas_mole_fraction,
    total_pressure,
    verbose=False,
    warningoff=False,
    adsorbed_mole_fraction_guess=None
):
    """
    Perform IAST calculation to predict multi-component adsorption isotherm from
    pure component adsorption isotherms.

    The material is now in equilibrium with a mixture of gases with partial
    pressures in the array `partial_pressures` in units corresponding to those
    passed in the list of isotherms.

    Pass a list of pure-component adsorption isotherms `isotherms`.

    Parameters
    ----------
    isotherms : list of ModelIsotherms or PointIsotherms
        Model adsorption isotherms.
        e.g. [methane_isotherm, ethane_isotherm, ...]
    gas_mole_fraction : array or list
        Partial pressures of gas components,
        e.g. [0.5, 0.5].
    total_pressure : float
        Total gas phase pressure, e.g. 5 (bar)
    verbose : bool, optional
        Print off a lot of information.
    warningoff: bool, optional
        When False, warnings will print when the IAST
        calculation result required extrapolation of the pure-component
        adsorption isotherm beyond the highest pressure in the data.
    adsorbed_mole_fraction_guess : array or list, optional
        Starting guesses for adsorbed phase mole fractions that
        `iast` solves for.

    Returns
    -------
    loading : array
        Predicted uptakes of each component (mmol/g or equivalent in isotherm units).

    """
    for isotherm in isotherms:
        if hasattr(isotherm, 'model'):
            if not is_iast_model(isotherm.model.name):
                raise ParameterError(
                    f"Model {isotherm.model.name} cannot be used with IAST."
                )

    n_components = len(isotherms)  # number of components in the mixture
    if n_components == 1:
        raise ParameterError("Pass at least two isotherms.")

    partial_pressures = numpy.asarray(gas_mole_fraction) * total_pressure
    if numpy.size(partial_pressures) != n_components:
        raise ParameterError(
            "Number of partial pressures != number of isotherms. Example use:\n"
            "pygaps.iast([iso1, iso2, iso3], [p1,p2,p3], total_p)"
        )

    if verbose:
        logger.info(f"{n_components:d} components.")
        for i in range(n_components):
            logger.info(
                f"\tPartial pressure component {i:d} = {partial_pressures[i]:.4f}"
            )

    # Assert that the spreading pressures of each component are equal
    def spreading_pressure_differences(adsorbed_mole_fractions):
        """
        Assert that spreading pressures of each component at fictitious pressure
        are equal.

        Parameters
        ----------
        adsorbed_mole_fractions : array
            Mole fractions in the adsorbed phase;
            numpy.size(adsorbed_mole_fractions) = n_components - 1
            because sum z_i = 1 asserted here automatically.

        Returns
        -------
        array
            Spreading pressure difference between component i and i+1.
        """
        spreading_pressure_diff = numpy.zeros((n_components - 1, ))
        for i in range(n_components - 1):
            if i == n_components - 2:
                # automatically assert \sum z_i = 1
                adsorbed_mole_fraction_n = 1.0 - \
                    numpy.sum(adsorbed_mole_fractions)
                spreading_pressure_diff[i] = isotherms[i].spreading_pressure_at(
                    partial_pressures[i] / adsorbed_mole_fractions[i]) - \
                    isotherms[i + 1].spreading_pressure_at(
                    partial_pressures[i + 1] / adsorbed_mole_fraction_n)
            else:
                spreading_pressure_diff[i] = isotherms[i].spreading_pressure_at(
                    partial_pressures[i] / adsorbed_mole_fractions[i]) - \
                    isotherms[i + 1].spreading_pressure_at(
                        partial_pressures[i + 1] /
                        adsorbed_mole_fractions[i + 1])
        return spreading_pressure_diff

    ###
    #   Solve for mole fractions in adsorbed phase by equating spreading
    #   pressures.
    ####
    if adsorbed_mole_fraction_guess is None:
        # Default guess: pure-component loadings at these partial pressures.
        loading_guess = numpy.asarray([
            isotherms[i].loading_at(partial_pressures[i])
            for i in range(n_components)
        ])
        adsorbed_mole_fraction_guess = loading_guess / numpy.sum(loading_guess)
    else:
        numpy.testing.assert_almost_equal(
            1.0, numpy.sum(adsorbed_mole_fraction_guess), decimal=4
        )
        # if list, convert to numpy array
        adsorbed_mole_fraction_guess = numpy.asarray(
            adsorbed_mole_fraction_guess
        )

    res = scipy.optimize.root(
        spreading_pressure_differences,
        adsorbed_mole_fraction_guess[:-1],
        method='lm'
    )

    if not res.success:
        raise CalculationError(
            textwrap.dedent(
                f"""
                Root finding for adsorbed phase mole fractions failed. This is
                likely because the default guess is not good enough. Try a
                different starting guess for the adsorbed phase mole fractions
                by passing an array adsorbed_mole_fraction_guess to this
                function. Scipy error message: \n\t{res.message}
                """
            )
        )

    adsorbed_mole_fractions = res.x

    # concatenate mole fraction of last component
    adsorbed_mole_fractions = numpy.concatenate((
        adsorbed_mole_fractions,
        numpy.asarray([1.0 - numpy.sum(adsorbed_mole_fractions)])
    ))

    if numpy.any((adsorbed_mole_fractions < 0.0)
                 | (adsorbed_mole_fractions > 1.0)):
        raise CalculationError(
            textwrap.dedent(
                """
                Some adsorbed mole fractions are below 0 or over 1. Try a different
                starting guess for the adsorbed mole fractions by passing an array or
                list 'adsorbed_mole_fraction_guess' into this function.
                e.g. adsorbed_mole_fraction_guess=[0.2, 0.8]"""
            )
        )

    pressure0 = partial_pressures / adsorbed_mole_fractions

    # solve for the total gas adsorbed
    inverse_loading = 0.0
    for i in range(n_components):
        inverse_loading += adsorbed_mole_fractions[i] / isotherms[
            i].loading_at(pressure0[i])
    loading_total = 1.0 / inverse_loading

    # get loading of each component by multiplying by mole fractions
    loadings = adsorbed_mole_fractions * loading_total
    if verbose:
        # print IAST loadings and corresponding pure-component loadings
        for i in range(n_components):
            logger.info(f"Component {i}")
            logger.info(f"\tp = {partial_pressures[i]:.4f}")
            logger.info(f"\tp^0 = {pressure0[i]:.4f}")
            logger.info(f"\tLoading = {loadings[i]:.4f}")
            logger.info(f"\tx = {adsorbed_mole_fractions[i]:.4f}")
            logger.info(
                f"\tSpreading pressure = {isotherms[i].spreading_pressure_at(pressure0[i]):.4f}"
            )

    # print warning if had to extrapolate isotherm in spreading pressure
    if not warningoff:
        for i in range(n_components):
            if pressure0[i] > isotherms[i].pressure(branch='ads').max():
                warnings.warn(
                    textwrap.dedent(
                        f"""
                        WARNING:
                        Component {i:d}: p0 = {pressure0[i]:.2f} > \
                            {isotherms[i].pressure(branch='ads').max():.2f}
                        the highest pressure exhibited in the pure-component
                        isotherm data. Thus, pyGAPS had to extrapolate the
                        isotherm data to achieve this IAST result."""
                    )
                )

    # return loadings [component 1, component 2, ...]. same units as in data
    return loadings


def reverse_iast(
    isotherms,
    adsorbed_mole_fractions,
    total_pressure,
    verbose=False,
    warningoff=False,
    gas_mole_fraction_guess=None
):
    """
    Perform reverse IAST to predict gas phase composition at total pressure
    `total_pressure` that will yield adsorbed mole fractions
    `adsorbed_mole_fractions`.

    Pass a list of pure-component adsorption isotherms `isotherms`.

    Parameters
    ----------
    isotherms : list
        Pure-component adsorption isotherms.
        e.g. [ethane_isotherm, methane_isotherm]
    adsorbed_mole_fractions : array
        Desired adsorbed mole fractions,
        e.g. [.5, .5]
    total_pressure : float
        Total bulk gas pressure.
    verbose : bool
        Print extra information.
    warningoff : bool
        When False, warnings will print when the IAST
        calculation result required extrapolation of the pure-component
        adsorption isotherm beyond the highest pressure in the data.
    gas_mole_fraction_guess : array or list
        Starting guesses for gas phase mole fractions that
        `iast.reverse_iast` solves for.

    Returns
    -------
    gas_mole_fractions : array
        Bulk gas mole fractions that yield desired adsorbed mole fractions
        `adsorbed_mole_fractions` at `total_pressure`.
    loadings : array
        Adsorbed component loadings according to reverse IAST
        (mmol/g or equivalent in isotherm units).

    """
    for isotherm in isotherms:
        if hasattr(isotherm, 'model'):
            if not is_iast_model(isotherm.model.name):
                raise ParameterError(
                    f"Model {isotherm.model.name} cannot be used with IAST."
                )

    n_components = len(isotherms)  # number of components in the mixture
    if n_components == 1:
        raise ParameterError("Pass at least two isotherms.")

    adsorbed_mole_fractions = numpy.asarray(adsorbed_mole_fractions)
    if numpy.size(adsorbed_mole_fractions) != n_components:
        raise ParameterError(
            "Number of adsorbed mole fractions is different from number of isotherms. Example use:\n"
            "pygaps.reverse_iast([iso1, iso2], [p1,p2], total_p)"
        )

    if numpy.sum(adsorbed_mole_fractions) != 1.0:
        raise ParameterError(
            "Desired adsorbed mole fractions should sum to 1.0."
        )

    if verbose:
        logger.info(f"{n_components:d} components.")
        for i in range(n_components):
            logger.info(
                f"\tDesired adsorbed phase mole fraction of component {i:d} = {adsorbed_mole_fractions[i]:.4f}"
            )

    # assert that the spreading pressures of each component are equal
    def spreading_pressure_differences(gas_mole_fractions):
        r"""
        Assert that spreading pressures of each component at fictitious pressure
        are equal.

        Parameters
        ----------
        gas_mole_fractions : array
            Mole fractions in bulk gas phase
            numpy.size(y) = n_components - 1 because \sum y_i = 1 asserted here
            automatically.

        Returns
        -------
        array
            Spreading pressure difference
            between component i and i+1.
        """
        spreading_pressure_diff = numpy.zeros((n_components - 1, ))
        for i in range(n_components - 1):
            if i == n_components - 2:
                # automatically assert \sum y_i = 1
                gas_mole_fraction_n = 1.0 - numpy.sum(gas_mole_fractions)
                spreading_pressure_diff[i] = isotherms[i].spreading_pressure_at(
                    total_pressure * gas_mole_fractions[i] /
                    adsorbed_mole_fractions[i]) - \
                    isotherms[i + 1].spreading_pressure_at(
                    total_pressure * gas_mole_fraction_n /
                    adsorbed_mole_fractions[i + 1])
            else:
                spreading_pressure_diff[i] = isotherms[i].spreading_pressure_at(
                    total_pressure * gas_mole_fractions[i] /
                    adsorbed_mole_fractions[i]) - \
                    isotherms[i + 1].spreading_pressure_at(
                    total_pressure * gas_mole_fractions[i + 1] /
                    adsorbed_mole_fractions[i + 1])
        return spreading_pressure_diff

    ###
    #  Solve for mole fractions in gas phase by equating spreading pressures
    if gas_mole_fraction_guess is None:
        # Default guess: adsorbed mole fraction
        gas_mole_fraction_guess = adsorbed_mole_fractions
    else:
        numpy.testing.assert_almost_equal(
            1.0, numpy.sum(gas_mole_fraction_guess), decimal=4
        )
        # if list, convert to numpy array
        gas_mole_fraction_guess = numpy.asarray(gas_mole_fraction_guess)

    res = scipy.optimize.root(
        spreading_pressure_differences,
        gas_mole_fraction_guess[:-1],
        method='lm'
    )

    if not res.success:
        raise CalculationError(
            textwrap.dedent(
                f"""
                Root finding for gas phase mole fractions failed.
                This is likely because the default guess is not good enough.
                Try a different starting guess for the gas phase mole fractions by
                passing an array or list gas_mole_fraction_guess to this function.
                Scipy error message: \n\t{res.message}"""
            )
        )

    gas_mole_fractions = res.x

    # concatenate mole fraction of last component
    gas_mole_fractions = numpy.concatenate((
        gas_mole_fractions, numpy.array([1.0 - numpy.sum(gas_mole_fractions)])
    ))

    if numpy.sum(gas_mole_fractions < 0.0
                 ) != 0 or numpy.sum(gas_mole_fractions > 1.0) != 0:
        raise CalculationError(
            textwrap.dedent(
                """Gas phase mole fraction not in [0,1]. Try a different
                starting guess for the gas phase mole fractions by passing an
                array or list 'gas_mole_fraction_guess' into this function. e.g.
                gas_mole_fraction_guess=[0.2, 0.8]"""
            )
        )

    pressure0 = total_pressure * gas_mole_fractions / adsorbed_mole_fractions

    # solve for the total gas adsorbed
    inverse_loading = 0.0
    for i in range(n_components):
        inverse_loading += adsorbed_mole_fractions[i] / isotherms[
            i].loading_at(pressure0[i])
    loading_total = 1.0 / inverse_loading

    # get loading of each component by multiplying by mole fractions
    loadings = adsorbed_mole_fractions * loading_total

    if verbose:
        # print off IAST loadings and corresponding pure component loadings
        for i in range(n_components):
            logger.info(f"Component {i}")
            logger.info(
                f"\tDesired mole fraction in adsorbed phase, x = {adsorbed_mole_fractions[i]:.4f}"
            )
            logger.info(
                f"\tBulk gas mole fraction that gives this, y = {gas_mole_fractions[i]:.4f}"
            )
            logger.info(f"\tp^0 = {pressure0[i]:.4f}")
            logger.info(f"\tLoading = {loadings[i]:.4f}")
            logger.info(
                f"\tSpreading pressure = {isotherms[i].spreading_pressure_at(pressure0[i]):.4f}"
            )

    # print warning if had to extrapolate isotherm in spreading pressure
    if not warningoff:
        for i in range(n_components):
            if pressure0[i] > isotherms[i].pressure(branch='ads').max():
                warnings.warn(
                    textwrap.dedent(
                        f"""
                        WARNING:
                        Component {i}: p0 = {pressure0[i]} > {isotherms[i].pressure(branch='ads').max()}, the highest pressure
                        exhibited in the pure-component isotherm data. Thus,
                        code had to extrapolate the isotherm data to achieve
                        this IAST result.
                        """
                    )
                )

    # return mole fractions in gas phase, component loadings
    return gas_mole_fractions, loadings
