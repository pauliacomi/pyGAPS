"""
This module calculates the BET surface area based on an isotherm
"""


import warnings

import scipy.constants as constants
import scipy.stats

from ..classes.adsorbate import Adsorbate
from ..graphing.calcgraph import bet_plot
from ..graphing.calcgraph import roq_plot


def area_BET(isotherm, verbose=False):
    """
    Function returns the BET surface area of an isotherm object which
    is passed to it.

    Parameters
    ----------
    isotherm : PointIsotherm
        The isotherm on which to calculate the BET surface area
    verbose : bool
        Prints extra information and graphs with the calculation

    Returns
    -------
    result_dict : dictionary
        A dictionary of results with the following components

        - 'bet_area': bet_area,
        - 'c_const': c_const,
        - 'n_monolayer': n_monolayer,
        - 'p_monolayer': p_monolayer,
        - 'bet_slope': slope,
        - 'bet_intercept': intercept,
        - 'corr_coef': corr_coef,

    Notes
    -----
    The BET theory [1]_ is

    References
    ----------
    .. [1] “Adsorption of Gases in Multimolecular Layers”, Stephen Brunauer,
    P. H. Emmett and Edward Teller, J. Amer. Chem. Soc., 60, 309(1938)
    """
    # Checks
    if isotherm.mode_adsorbent != "mass":
        raise Exception("The isotherm must be in per mass of adsorbent."
                        "First convert it using implicit functions")
    if isotherm.mode_pressure != "relative":
        isotherm.convert_pressure_mode('relative')

    # get adsorbate properties
    adsorbate = Adsorbate.from_list(isotherm.gas)
    cross_section = adsorbate.get_prop("cross_sectional_area")

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
                 p_monolayer, n_monolayer,
                 roq_transform(n_monolayer, p_monolayer))

        # Generate plot of the Roquerol points chosen
        roq_plot(pressure,
                 roq_transform(loading, pressure),
                 minimum, maximum,
                 p_monolayer, n_monolayer,
                 bet_transform(n_monolayer, p_monolayer))

    return result_dict


def area_BET_raw(loading, pressure, cross_section):
    """
    Raw function to calculate BET area

    Parameters
    ----------
    loading : array
        loadings, in mol/g
    pressure : array
        pressures, relative
    cross_section : float
        adsorbed cross-section of the molecule of the adsorbate, in nm

    Returns
    -------
    bet_area : float
        calculated BET surface area
    c_const : float
        C constant from the BET equation
    n_monolayer : float
        adsorbed quantity in the statistical monolayer
    p_monolayer : float
        pressure at the statistical monolayer
    slope : float
        calculated slope of the BET plot
    intercept : float
        calculated intercept of the BET plot
    minimum : float
        miminum loading of the point taken for the linear region
    maximum : float
        maximum loading of the point taken for the linear region
    corr_coef : float
        correlation coefficient of the straight line in the BET plot

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
