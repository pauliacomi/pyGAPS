"""
This module calculates the BET surface area based on an isotherm
"""

__author__ = 'Paul A. Iacomi and Bastien Aillet'

import warnings

import matplotlib.pyplot as plt
import scipy.constants as constants
import scipy.stats

from ..classes.gas import Gas


def area_BET(isotherm, verbose=False):
    """
    Function returns the BET surface area of an isotherm object which
    is passed to it.
    """
    # Checks
    if isotherm.mode_adsorbent != "mass":
        raise Exception("The isotherm must be in per mass of adsorbent."
                        "First convert it using implicit functions")
    if isotherm.mode_pressure != "relative":
        isotherm.convert_pressure_mode('relative')

    # get gas properties
    ads_gas = Gas.from_list(isotherm.gas)
    cross_section = ads_gas.get_prop("cross_sectional_area")

    # Read data in
    loading = isotherm.loading_ads(unit='mol')
    pressure = isotherm.pressure_ads()

    # use the bet function
    bet_area, c_const, n_monolayer, p_monolayer, slope, intercept, minimum, maximum, corr_coef = area_BET_raw(
        loading, pressure, cross_section)

    result_dict = {
        'bet_area': bet_area,
        'c_const': c_const,
        'n_monolayer': n_monolayer,
        'p_monolayer': p_monolayer,
        'bet_slope': slope,
        'bet_intercept': intercept,
        'corr_coef': corr_coef,
    }

    # PLOTTING
    if verbose:

        print("The slope of the BET line: s =", round(slope, 3))
        print("The intercept of the BET line: i =", round(intercept, 3))
        print("C =", int(round(c_const, 0)))
        print("Amount for a monolayer: n =",
              round(n_monolayer, 3), "mol/g")
        print("Minimum pressure point chosen is {0} and maximum is {1}".format(
            round(pressure[minimum], 3), round(pressure[maximum], 3)))
        print("BET surface area: a =", int(round(bet_area, 0)), "m²/g")

        # Generate plot of the BET points chosen
        bet_plot(pressure,
                 bet_transform(loading, pressure),
                 minimum, maximum,
                 p_monolayer, n_monolayer)

        # Generate plot of the Roquerol points chosen
        roq_plot(pressure,
                 roq_transform(loading, pressure),
                 minimum, maximum,
                 p_monolayer, n_monolayer)

    return result_dict


def area_BET_raw(loading, pressure, cross_section):
    """
    Raw function to calculate BET area

    :param pressure: array of pressures, relative
    :param loading: array of loadings, in mol/g
    :param cross_section: adsorbed cross-section of the molecule of the
        adsorbate, in nm

    :returns:
    :rtype: dict
    """
    if len(pressure) != len(loading):
        raise Exception("The length of the pressure and loading arrays"
                        " do not match")

    # Generate the Roquerol array
    roq_t_array = roq_transform(loading, pressure)

    # select the maximum and minimum of the points and the pressure associated
    maximum = len(roq_t_array) - 1
    for index, value in enumerate(roq_t_array):
        if value > roq_t_array[index + 1]:
            maximum = index
            break
    min_p = pressure[maximum] / 10

    minimum = 0
    for index, value in enumerate(pressure):
        if value > min_p:
            minimum = index
            break

    # calculate the BET transform, slope and intercept
    bet_t_array = bet_transform(
        loading[minimum:maximum], pressure[minimum:maximum])
    slope, intercept, corr_coef = bet_optimisation(
        pressure[minimum:maximum], bet_t_array)

    # calculate the BET parameters
    n_monolayer, p_monolayer, c_const, bet_area = bet_parameters(
        slope, intercept, cross_section)

    # Checks for consistency
    if c_const < 0:
        warnings.warn("The C constant is negative")
    if corr_coef < 0.99:
        warnings.warn("The correlation is not linear")
    if (loading[minimum] > n_monolayer) or (loading[maximum] < n_monolayer):
        warnings.warn("The monolayer point is not within the BET region")

    return bet_area, c_const, n_monolayer, p_monolayer, slope, intercept, minimum, maximum, corr_coef


def roq_transform(loading, pressure):
    "Roquerol transform function"
    return loading * (1 - pressure)


def bet_transform(loading, pressure):
    "BET transform function"
    return pressure / roq_transform(loading, pressure)


def bet_optimisation(pressure, bet_points):
    "Finds the slope and intercept of the BET region"
    slope, intercept, corr_coef, p, stderr = scipy.stats.linregress(
        pressure, bet_points)
    return slope, intercept, corr_coef


def bet_parameters(slope, intercept, cross_section):
    "Calculates the BET parameters from the slope and intercept"

    c_const = (slope / intercept) + 1
    n_monolayer = 1 / (intercept * c_const)
    p_monolayer = 1 / (scipy.sqrt(c_const) + 1)
    bet_area = n_monolayer * cross_section * (10**(-18)) * constants.Avogadro
    return n_monolayer, p_monolayer, c_const, bet_area


def roq_plot(pressure, roq_points, minimum, maximum, p_monolayer, n_monolayer):
    """Draws the roquerol plot"""
    fig = plt.figure()
    ax1 = fig.add_subplot(111)
    ax1.plot(pressure, roq_points,
             marker='', color='g', label='all points')
    ax1.plot(pressure[minimum:maximum], roq_points[minimum:maximum],
             marker='o', linestyle='', color='r', label='chosen points')
    ax1.plot(p_monolayer, roq_transform(n_monolayer, p_monolayer),
             marker='x', linestyle='', color='black', label='monolayer point')
    ax1.set_title("Roquerol plot")
    ax1.set_xlabel('p/p°')
    ax1.set_ylabel('(p/p°)/(n(1-(P/P°))')
    ax1.legend(loc='best')
    plt.show()


def bet_plot(pressure, bet_points, minimum, maximum, p_monolayer, n_monolayer):
    """Draws the bet plot"""
    fig = plt.figure()
    ax1 = fig.add_subplot(111)
    ax1.plot(pressure, bet_points,
             marker='', color='g', label='all points')
    ax1.plot(pressure[minimum:maximum], bet_points[minimum:maximum],
             marker='o', linestyle='', color='r', label='chosen points')
    ax1.plot(p_monolayer, bet_transform(n_monolayer, p_monolayer),
             marker='x', linestyle='', color='black', label='monolayer point')
    ax1.set_ylim(ymin=0, ymax=bet_points[maximum] * 1.2)
    ax1.set_xlim(
        xmin=0, xmax=pressure[maximum] * 1.2)
    ax1.set_title("BET plot")
    ax1.set_xlabel('p/p°')
    ax1.set_ylabel('(p/p°)/(n(1-(P/P°))')
    ax1.legend(loc='best')
    plt.show()
