"""
This module performs the heart of the IAST calculations, given the
pure-component adsorption isotherm models from the `isotherms` module.
"""

import numpy
import scipy.optimize


def iast(partial_pressures, isotherms, verboseflag=False, warningoff=False,
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
    partial_pressures : array or list
        partial pressures of gas components,
        e.g. [5.0, 10.0] (bar)
    isotherms : list of ModelIsotherms
        model adsorption isotherms.
        e.g. [methane_isotherm, ethane_isotherm]
    verboseflag : bool
        print off a lot of information
    warningoff: bool
        when False, warnings will print when the IAST
        calculation result required extrapolation of the pure-component
        adsorption isotherm beyond the highest pressure in the data
    adsorbed_mole_fraction_guess : array or list
        starting guesses for adsorbed phase mole fractions that
        `pyiast.iast` solves for

    Returns
    -------
    array
        predicted uptakes of each component

    """

    partial_pressures = numpy.array(partial_pressures)
    n_components = len(isotherms)  # number of components in the mixture
    if n_components == 1:
        raise Exception("Pass list of pure component isotherms...")

    if numpy.size(partial_pressures) != n_components:
        print("""Example use:\n
              IAST([0.5,0.5], [xe_isotherm, kr_isotherm], verboseflag=true)""")
        raise Exception("Length of partial pressures != length of array of"
                        " isotherms...")

    if verboseflag:
        print("%d components." % n_components)
        for i in range(n_components):
            print("\tPartial pressure component %d = %f" % (i,
                                                            partial_pressures[i]))

    # assert that the spreading pressures of each component are equal
    def spreading_pressure_differences(adsorbed_mole_fractions):
        """
        Assert that spreading pressures of each component at fictitious pressure
        are equal.

        Parameters
        ----------
        adsorbed_mole_fractions : array
            mole fractions in the adsorbed
            phase; numpy.size(adsorbed_mole_fractions) = n_components - 1 because
            sum z_i = 1 asserted here automatically.

        Returns
        -------
        array
            spreading pressure difference between component i and i+1
        """
        spreading_pressure_diff = numpy.zeros((n_components - 1,))
        for i in range(n_components - 1):
            if i == n_components - 2:
                # automatically assert \sum z_i = 1
                adsorbed_mole_fraction_n = 1.0 - \
                    numpy.sum(adsorbed_mole_fractions)
                spreading_pressure_diff[i] = isotherms[i].spreading_pressure(
                    partial_pressures[i] / adsorbed_mole_fractions[i]) - \
                    isotherms[i + 1].spreading_pressure(
                    partial_pressures[i + 1] / adsorbed_mole_fraction_n)
            else:
                spreading_pressure_diff[i] = isotherms[i].spreading_pressure(
                    partial_pressures[i] / adsorbed_mole_fractions[i]) - \
                    isotherms[i + 1].spreading_pressure(
                        partial_pressures[i + 1] /
                        adsorbed_mole_fractions[i + 1])
        return spreading_pressure_diff

    ###
    #   Solve for mole fractions in adsorbed phase by equating spreading
    #   pressures.
    ####
    if adsorbed_mole_fraction_guess is None:
        # Default guess: pure-component loadings at these partial pressures.
        loading_guess = [isotherms[i].loading(partial_pressures[i]) for i in
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
        print(res.message)
        raise Exception("""Root finding for adsorbed phase mole fractions failed.
        This is likely because the default guess in pyIAST is not good enough.
        Try a different starting guess for the adsorbed phase mole fractions by
        passing an array adsorbed_mole_fraction_guess to this function.""")

    adsorbed_mole_fractions = res.x

    # concatenate mole fraction of last component
    adsorbed_mole_fractions = numpy.concatenate((adsorbed_mole_fractions,
                                                 numpy.array([1.0 - numpy.sum(adsorbed_mole_fractions)])))

    if (numpy.sum(adsorbed_mole_fractions < 0.0) != 0) | (
            numpy.sum(adsorbed_mole_fractions > 1.0) != 0):
        raise Exception("""Adsorbed mole fraction not in [0,1]. Try a different
        starting guess for the adsorbed mole fractions by passing an array or
        list 'adsorbed_mole_fraction_guess' into this function.
        e.g. adsorbed_mole_fraction_guess=[0.2, 0.8]""")

    pressure0 = partial_pressures / adsorbed_mole_fractions

    # solve for the total gas adsorbed
    inverse_loading = 0.0
    for i in range(n_components):
        inverse_loading += adsorbed_mole_fractions[i] / isotherms[i].loading(
            pressure0[i])
    loading_total = 1.0 / inverse_loading

    # get loading of each component by multiplying by mole fractions
    loadings = adsorbed_mole_fractions * loading_total
    if verboseflag:
        # print IAST loadings and corresponding pure-component loadings
        for i in range(n_components):
            print("Component ", i)
            print("\tp = ", partial_pressures[i])
            print("\tp^0 = ", pressure0[i])
            print("\tLoading: ", loadings[i])
            print("\tx = ", adsorbed_mole_fractions[i])
            print("\tSpreading pressure = ", isotherms[i].spreading_pressure(
                pressure0[i]))

    # print warning if had to extrapolate isotherm in spreading pressure
    if not warningoff:
        for i in range(n_components):
            if pressure0[i] > isotherms[i].df[isotherms[i].pressure_key].max():
                print("""WARNING:
                      Component %d: p^0 = %f > %f, the highest pressure
                      exhibited in the pure-component isotherm data. Thus,
                      pyIAST had to extrapolate the isotherm data to achieve
                      this IAST result.""" % (i, pressure0[i],
                                              isotherms[i].df[isotherms[i].pressure_key].max()))

    # return loadings [component 1, component 2, ...]. same units as in data
    return loadings


def reverse_iast(adsorbed_mole_fractions, total_pressure, isotherms,
                 verboseflag=False, warningoff=False,
                 gas_mole_fraction_guess=None):
    """
    Perform reverse IAST to predict gas phase composition at total pressure
    `total_pressure` that will yield adsorbed mole fractions
    `adsorbed_mole_fractions`.

    Pass a list of pure-component adsorption isotherms `isotherms`.

    Parameters
    ----------
    adsorbed_mole_fractions : array
        desired adsorbed mole fractions,
        e.g. [.5, .5]
    total_pressure : float
        total bulk gas pressure
    isotherms : list
        pure-component adsorption isotherms.
        e.g. [ethane_isotherm, methane_isotherm]
    verboseflag : bool
        print stuff
    warningoff : bool
        when False, warnings will print when the IAST
        calculation result required extrapolation of the pure-component
        adsorption isotherm beyond the highest pressure in the data
    gas_mole_fraction_guess : array or list
        starting guesses for gas phase mole fractions that
        `pyiast.reverse_iast` solves for

    Returns
    -------
    gas_mole_fractions : array
        bulk gas mole fractions that yield
        desired adsorbed mole fractions `adsorbed_mole_fractions` at
        `total_pressure`
    loadings : array
        adsorbed component loadings according to reverse IAST

    """
    n_components = len(isotherms)  # number of components in the mixture
    adsorbed_mole_fractions = numpy.array(adsorbed_mole_fractions)
    if n_components == 1:
        raise Exception("Pass list of pure component isotherms...")

    if numpy.size(adsorbed_mole_fractions) != n_components:
        print("""Example use:\n
              reverse_IAST([0.5,0.5], 1.0, [xe_isotherm, kr_isotherm],
              verboseflag=true)""")
        raise Exception("Length of desired adsorbed mole fractions != length of"
                        " array of isotherms...")

    if numpy.sum(adsorbed_mole_fractions) != 1.0:
        raise Exception("Desired adsorbed mole fractions should sum to 1.0...")

    if verboseflag:
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
            mole fractions in bulk gas phase
            numpy.size(y) = n_components - 1 because \sum y_i = 1 asserted here
            automatically.

        Returns
        -------
        array
            spreading pressure difference
            between component i and i+1
        """
        spreading_pressure_diff = numpy.zeros((n_components - 1,))
        for i in range(n_components - 1):
            if i == n_components - 2:
                # automatically assert \sum y_i = 1
                gas_mole_fraction_n = 1.0 - numpy.sum(gas_mole_fractions)
                spreading_pressure_diff[i] = isotherms[i].spreading_pressure(
                    total_pressure * gas_mole_fractions[i] /
                    adsorbed_mole_fractions[i]) - \
                    isotherms[i + 1].spreading_pressure(
                    total_pressure * gas_mole_fraction_n /
                    adsorbed_mole_fractions[i + 1])
            else:
                spreading_pressure_diff[i] = isotherms[i].spreading_pressure(
                    total_pressure * gas_mole_fractions[i] /
                    adsorbed_mole_fractions[i]) - \
                    isotherms[i + 1].spreading_pressure(
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
        print(res.message)
        raise Exception("""Root finding for gas phase mole fractions failed.
        This is likely because the default guess in pyIAST is not good enough.
        Try a different starting guess for the gas phase mole fractions by
        passing an array or list gas_mole_fraction_guess to this function.""")

    gas_mole_fractions = res.x

    # concatenate mole fraction of last component
    gas_mole_fractions = numpy.concatenate((gas_mole_fractions,
                                            numpy.array([1.0 -
                                                         numpy.sum(gas_mole_fractions)])))

    if (numpy.sum(gas_mole_fractions < 0.0) != 0) | (
            numpy.sum(gas_mole_fractions > 1.0) != 0):
        raise Exception("""Gas phase mole fraction not in [0,1]. Try a different
        starting guess for the gas phase mole fractions by passing an array or
        list 'gas_mole_fraction_guess' into this function.
        e.g. gas_mole_fraction_guess=[0.2, 0.8]""")

    pressure0 = total_pressure * gas_mole_fractions / adsorbed_mole_fractions

    # solve for the total gas adsorbed
    inverse_loading = 0.0
    for i in range(n_components):
        inverse_loading += adsorbed_mole_fractions[i] / isotherms[i].loading(
            pressure0[i])
    loading_total = 1.0 / inverse_loading

    # get loading of each component by multiplying by mole fractions
    loadings = adsorbed_mole_fractions * loading_total

    if verboseflag:
        # print off IAST loadings and corresponding pure component loadings
        for i in range(n_components):
            print("Component ", i)
            print("\tDesired mole fraction in adsorbed phase, x = ",
                  adsorbed_mole_fractions[i])
            print("\tBulk gas mole fraction that gives this, y = ",
                  gas_mole_fractions[i])
            print("\tSpreading pressure = ",
                  isotherms[i].spreading_pressure(pressure0[i]))
            print("\tp^0 = ", pressure0[i])
            print("\tLoading: ", loadings[i])

    # print warning if had to extrapolate isotherm in spreading pressure
    if not warningoff:
        for i in range(n_components):
            if pressure0[i] > isotherms[i].df[isotherms[i].pressure_key].max():
                print("""WARNING:
                  Component %d: p0 = %f > %f, the highest pressure
                  exhibited in the pure-component isotherm data. Thus,
                  pyIAST had to extrapolate the isotherm data to achieve
                  this IAST result.""" % (i, pressure0[i],
                                          isotherms[i].df[isotherms[i].pressure_key].max()))

    # return mole fractions in gas phase, component loadings
    return gas_mole_fractions, loadings


def print_selectivity(component_loadings, partial_pressures):
    """
    Calculate selectivity as a function of component loadings and bulk gas
    pressures

    Parameters
    ----------
    component_loadings : numpy array
        component loadings
    partial_pressures : numpy array
        partial pressures of components
    """
    n_components = numpy.size(component_loadings)
    for i in range(n_components):
        for j in range(i + 1, n_components):
            print("Selectivity for component %d over %d = %f" % (i, j,
                                                                 component_loadings[i] / component_loadings[j] /
                                                                 (partial_pressures[i] / partial_pressures[j])))
