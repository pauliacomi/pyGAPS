"""
This module performs the heart of the IAST calculations, given the
pure-component adsorption isotherm model.
"""

import numpy
import scipy.optimize

from ..graphing.iastgraphs import plot_iast_svp
from ..graphing.iastgraphs import plot_iast_vle
from ..utilities.exceptions import CalculationError
from ..utilities.exceptions import ParameterError
from .models_isotherm import is_iast_model


def iast_binary_vle(isotherms, pressure,
                    verbose=False, warningoff=False,
                    adsorbed_mole_fraction_guess=None):
    """
    Perform IAST calculations to predict the vapour-liquid equilibrium curve
    at a fixed pressure, over the entire range of partial pressures.

    Pass a list of two of pure-component adsorption isotherms `isotherms`, with the
    first one being selected as a basis.

    Parameters
    ----------
    isotherms : list of ModelIsotherms or PointIsotherms
        Model adsorption isotherms.
        e.g. [methane_isotherm, ethane_isotherm]
    pressure : float
        Pressure at which the vapour-liquid equilibrium is to be
        calculated.
    verbose : bool, optional
        Print off a extra information, as well as a graph.
    warningoff: bool, optional
        When False, warnings will print when the IAST
        calculation result required extrapolation of the pure-component
        adsorption isotherm beyond the highest pressure in the data.
    adsorbed_mole_fraction_guess : array or list, optional
        Starting guesses for adsorbed phase mole fractions that
        `iast` solves for.

    Returns
    -------
    dict
        Dictionary with two components:
            - `y` the mole fraction of the selected adsorbate in the gas phase
            - `x` mole fraction of the selected adsorbate in the adsorbed phase

    """
    # Parameter checks
    if len(isotherms) > 2 or len(isotherms) < 2:
        raise ParameterError(
            "The binary vle graph can only take two components as parameters"
        )

    # Generate fractions array
    y_data = numpy.linspace(0.01, 0.99, 30)
    y2_data = 1 - y_data
    binary_fractions = numpy.array((y_data, y2_data)).transpose()

    # Generate the array of loadings
    component_loadings = numpy.zeros((len(binary_fractions), 2))

    # Run IAST
    for index, fraction in enumerate(binary_fractions):
        # We assume ideal behaviour
        partial_pressures = pressure * fraction
        component_loadings[index, :] = iast(
            isotherms, partial_pressures, warningoff=warningoff,
            adsorbed_mole_fraction_guess=adsorbed_mole_fraction_guess)

    x_data = [x[0] / (x[0] + x[1]) for x in component_loadings]

    # Add start and end points
    x_data = numpy.concatenate([[0], x_data, [1]])
    y_data = numpy.concatenate([[0], y_data, [1]])

    # Generate the array of partial pressures
    if verbose:
        plot_iast_vle(x_data, y_data,
                      isotherms[0].adsorbate, isotherms[1].adsorbate,
                      pressure, isotherms[0].pressure_unit)

    return dict(x=x_data, y=y_data)


def iast_binary_svp(isotherms, mole_fractions, pressures,
                    verbose=False, warningoff=False,
                    adsorbed_mole_fraction_guess=None):
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
    verbose : bool, optional
        Print off a extra information, as well as a graph.
    warningoff: bool, optional
        When False, warnings will print when the IAST
        calculation result required extrapolation of the pure-component
        adsorption isotherm beyond the highest pressure in the data.
    adsorbed_mole_fraction_guess : array or list, optional
        Starting guesses for adsorbed phase mole fractions that
        `iast` solves for.

    Returns
    -------
    dict
        Dictionary with two components:
            - `selectivity` the selectivity of the selected component
            - `pressure` the pressure for each selectivity

    """

    # Parameter checks
    if len(isotherms) > 2 or len(mole_fractions) > 2:
        raise ParameterError(
            "The selectivity graph can only take two components as parameters"
        )
    if sum(mole_fractions) != 1:
        raise ParameterError(
            "Mole fractions do not add up to unity"
        )

    # Convert to numpy arrays just in case
    pressures = numpy.array(pressures)
    mole_fractions = numpy.array(mole_fractions)

    # Generate the array of partial pressures
    component_loadings = numpy.zeros((len(pressures), 2))

    for index, pressure in enumerate(pressures):
        partial_pressures = pressure * mole_fractions
        component_loadings[index, :] = iast(
            isotherms, partial_pressures, warningoff=warningoff,
            adsorbed_mole_fraction_guess=adsorbed_mole_fraction_guess)

    selectivities = [(x[0] / mole_fractions[0]) /
                     (x[1] / mole_fractions[1]) for x in component_loadings]

    if verbose:
        plot_iast_svp(pressures, selectivities,
                      isotherms[0].adsorbate, isotherms[1].adsorbate,
                      mole_fractions[0], isotherms[0].pressure_unit)

    return dict(pressure=pressures, selectivity=selectivities)


def iast(isotherms, partial_pressures, verbose=False, warningoff=False,
         adsorbed_mole_fraction_guess=None):
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
        e.g. [methane_isotherm, ethane_isotherm]
    partial_pressures : array or list
        Partial pressures of gas components,
        e.g. [5.0, 10.0] (bar).
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
    array
        Predicted uptakes of each component.

    """
    for isotherm in isotherms:
        if hasattr(isotherm, 'model'):
            if not is_iast_model(isotherm.model.name):
                raise ParameterError(
                    "Model {} cannot be used with IAST.".format(isotherm.model.name))

    partial_pressures = numpy.array(partial_pressures)
    n_components = len(isotherms)  # number of components in the mixture
    if n_components == 1:
        raise ParameterError("Pass list of pure component isotherms...")

    if numpy.size(partial_pressures) != n_components:
        print("""Example use:\n
              IAST([0.5,0.5], [xe_isotherm, kr_isotherm], verbose=true)""")
        raise ParameterError("Length of partial pressures != length of array of"
                             " isotherms...")

    if verbose:
        print("%d components." % n_components)
        for i in range(n_components):
            print("\tPartial pressure component %d = %f" % (i,
                                                            partial_pressures[i]))

    # Assert that the spreading pressures of each component are equal
    def spreading_pressure_differences(adsorbed_mole_fractions):
        """
        Assert that spreading pressures of each component at fictitious pressure
        are equal.

        Parameters
        ----------
        adsorbed_mole_fractions : array
            Mole fractions in the adsorbed
            phase; numpy.size(adsorbed_mole_fractions) = n_components - 1 because
            sum z_i = 1 asserted here automatically.

        Returns
        -------
        array
            Spreading pressure difference between component i and i+1.
        """
        spreading_pressure_diff = numpy.zeros((n_components - 1,))
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
        loading_guess = [isotherms[i].loading_at(partial_pressures[i]) for i in
                         range(n_components)]
        loading_guess = numpy.array(loading_guess)
        adsorbed_mole_fraction_guess = loading_guess / numpy.sum(loading_guess)
    else:
        numpy.testing.assert_almost_equal(1.0,
                                          numpy.sum(
                                              adsorbed_mole_fraction_guess),
                                          decimal=4)
        # if list, convert to numpy array
        adsorbed_mole_fraction_guess = numpy.array(
            adsorbed_mole_fraction_guess)

    res = scipy.optimize.root(
        spreading_pressure_differences, adsorbed_mole_fraction_guess[:-1],
        method='lm')

    if not res.success:
        raise CalculationError(
            """Root finding for adsorbed phase mole fractions failed.
        This is likely because the default guess is not good enough.
        Try a different starting guess for the adsorbed phase mole fractions by
        passing an array adsorbed_mole_fraction_guess to this function. Scipy error
        message: {}""".format(res.message))

    adsorbed_mole_fractions = res.x

    # concatenate mole fraction of last component
    adsorbed_mole_fractions = numpy.concatenate((adsorbed_mole_fractions,
                                                 numpy.array(
                                                     [1.0 - numpy.sum(adsorbed_mole_fractions)])
                                                 ))

    if (numpy.sum(adsorbed_mole_fractions < 0.0) != 0) | (
            numpy.sum(adsorbed_mole_fractions > 1.0) != 0):
        raise CalculationError("""Adsorbed mole fraction not in [0,1]. Try a different
                                starting guess for the adsorbed mole fractions by passing an array or
                                list 'adsorbed_mole_fraction_guess' into this function.
                                e.g. adsorbed_mole_fraction_guess=[0.2, 0.8]""")

    pressure0 = partial_pressures / adsorbed_mole_fractions

    # solve for the total gas adsorbed
    inverse_loading = 0.0
    for i in range(n_components):
        inverse_loading += adsorbed_mole_fractions[i] / isotherms[i].loading_at(
            pressure0[i])
    loading_total = 1.0 / inverse_loading

    # get loading of each component by multiplying by mole fractions
    loadings = adsorbed_mole_fractions * loading_total
    if verbose:
        # print IAST loadings and corresponding pure-component loadings
        for i in range(n_components):
            print("Component ", i)
            print("\tp = ", partial_pressures[i])
            print("\tp^0 = ", pressure0[i])
            print("\tLoading: ", loadings[i])
            print("\tx = ", adsorbed_mole_fractions[i])
            print("\tSpreading pressure = ", isotherms[i].spreading_pressure_at(
                pressure0[i]))

    # print warning if had to extrapolate isotherm in spreading pressure
    if not warningoff:
        for i in range(n_components):
            if pressure0[i] > isotherms[i].pressure(branch='ads').max():
                print("""WARNING:
                      Component %d: p^0 = %f > %f, the highest pressure
                      exhibited in the pure-component isotherm data. Thus,
                      pyGAPS had to extrapolate the isotherm data to achieve
                      this IAST result.""" % (i, pressure0[i],
                                              isotherms[i].pressure(branch='ads').max()))

    # return loadings [component 1, component 2, ...]. same units as in data
    return loadings


def reverse_iast(isotherms, adsorbed_mole_fractions, total_pressure,
                 verbose=False, warningoff=False,
                 gas_mole_fraction_guess=None):
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
        Adsorbed component loadings according to reverse IAST.

    """
    for isotherm in isotherms:
        if hasattr(isotherm, 'model'):
            if not is_iast_model(isotherm.model.name):
                raise ParameterError(
                    "Model {} cannot be used with IAST.".format(isotherm.model.name))

    n_components = len(isotherms)  # number of components in the mixture
    adsorbed_mole_fractions = numpy.array(adsorbed_mole_fractions)
    if n_components == 1:
        raise ParameterError("Pass list of pure component isotherms...")

    if numpy.size(adsorbed_mole_fractions) != n_components:
        print("""Example use:\n
              reverse_IAST([0.5,0.5], 1.0, [xe_isotherm, kr_isotherm],
              verbose=true)""")
        raise ParameterError("Length of desired adsorbed mole fractions != length of"
                             " array of isotherms...")

    if numpy.sum(adsorbed_mole_fractions) != 1.0:
        raise ParameterError(
            "Desired adsorbed mole fractions should sum to 1.0...")

    if verbose:
        print("%d components." % n_components)
        for i in range(n_components):
            print("\tDesired adsorbed phase mole fraction of component %d = %f"
                  % (i, adsorbed_mole_fractions[i]))

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
        spreading_pressure_diff = numpy.zeros((n_components - 1,))
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
        numpy.testing.assert_almost_equal(1.0, numpy.sum(gas_mole_fraction_guess),
                                          decimal=4)
        # if list, convert to numpy array
        gas_mole_fraction_guess = numpy.array(gas_mole_fraction_guess)

    res = scipy.optimize.root(
        spreading_pressure_differences, gas_mole_fraction_guess[:-1],
        method='lm')

    if not res.success:
        raise CalculationError(
            """Root finding for gas phase mole fractions failed.
        This is likely because the default guess is not good enough.
        Try a different starting guess for the gas phase mole fractions by
        passing an array or list gas_mole_fraction_guess to this function. Scipy error
        message: {}""".format(res.message))

    gas_mole_fractions = res.x

    # concatenate mole fraction of last component
    gas_mole_fractions = numpy.concatenate((gas_mole_fractions,
                                            numpy.array([1.0 -
                                                         numpy.sum(gas_mole_fractions)])))

    if (numpy.sum(gas_mole_fractions < 0.0) != 0) | (
            numpy.sum(gas_mole_fractions > 1.0) != 0):
        raise CalculationError(
            """Gas phase mole fraction not in [0,1]. Try a different
        starting guess for the gas phase mole fractions by passing an array or
        list 'gas_mole_fraction_guess' into this function.
        e.g. gas_mole_fraction_guess=[0.2, 0.8]""")

    pressure0 = total_pressure * gas_mole_fractions / adsorbed_mole_fractions

    # solve for the total gas adsorbed
    inverse_loading = 0.0
    for i in range(n_components):
        inverse_loading += adsorbed_mole_fractions[i] / isotherms[i].loading_at(
            pressure0[i])
    loading_total = 1.0 / inverse_loading

    # get loading of each component by multiplying by mole fractions
    loadings = adsorbed_mole_fractions * loading_total

    if verbose:
        # print off IAST loadings and corresponding pure component loadings
        for i in range(n_components):
            print("Component ", i)
            print("\tDesired mole fraction in adsorbed phase, x = ",
                  adsorbed_mole_fractions[i])
            print("\tBulk gas mole fraction that gives this, y = ",
                  gas_mole_fractions[i])
            print("\tSpreading pressure = ",
                  isotherms[i].spreading_pressure_at(pressure0[i]))
            print("\tp^0 = ", pressure0[i])
            print("\tLoading: ", loadings[i])

    # print warning if had to extrapolate isotherm in spreading pressure
    if not warningoff:
        for i in range(n_components):
            if pressure0[i] > isotherms[i].pressure(branch='ads').max():
                print("""WARNING:
                  Component %d: p0 = %f > %f, the highest pressure
                  exhibited in the pure-component isotherm data. Thus,
                  code had to extrapolate the isotherm data to achieve
                  this IAST result.""" % (i, pressure0[i],
                                          isotherms[i].pressure(branch='ads').max()))

    # return mole fractions in gas phase, component loadings
    return gas_mole_fractions, loadings
