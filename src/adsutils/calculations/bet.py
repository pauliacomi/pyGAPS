"""
This module calculates the BET surface area based on an isotherm
"""

__author__ = 'Paul A. Iacomi and Bastien Aillet'

import warnings
import matplotlib.pyplot as plt
import scipy.stats
import scipy.constants as constants

import adsutils.data as data


def area_BET(isotherm, optimize=True, verbose=False):
    """
    Function returns the BET surface area of an isotherm object which
    is passed to it.
    """
    # Checks
    if isotherm.mode_adsorbent != "mass":
        raise Exception("The isotherm must be in per mass of adsorbent."
                        "First convert it using implicit functions")
    if isotherm.mode_pressure != "relative":
        raise Exception("The isotherm must be in relative pressure mode."
                        "First convert it using implicit functions")
    if isotherm.unit_loading != "mmol":
        raise Exception("The loading must be in mmol."
                        "First convert it using implicit functions")

    # Check to see if gas exists in master list
    ads_gas_list = [gas for gas in data.GAS_LIST if isotherm.gas == gas.name]

    if len(ads_gas_list) == 0:
        raise Exception("Gas {0} does not exist in list of gasses. "
                        "First populate adsutils.GAS_LIST "
                        "with required gas class".format(isotherm.gas))

    ads_gas = ads_gas_list[0]

    cross_section = ads_gas.properties.get("cross_sectional_area")
    if cross_section is None:
        raise Exception("Gas {0} does not have a property named "
                        "cross_sectional_area. This must be available for BET "
                        "calculation".format(isotherm.gas))

    # Read data in
    adsorption = isotherm.adsdata()

    # Generate the BET and Roquerol columns
    adsorption = adsorption.assign(roquerol=lambda adsorption:
                                   adsorption[isotherm.loading_key] / 1000 *
                                   (1 - adsorption[isotherm.pressure_key]))
    adsorption = adsorption.assign(BET=lambda adsorption:
                                   adsorption[isotherm.pressure_key] /
                                   adsorption.roquerol)

    # select the maximum and minimum of the points
    maximum = (adsorption.loc[:, 'roquerol'].diff().fillna(
        0) < 0).values.argmax()
    max_p_chosen = adsorption[isotherm.pressure_key].iloc[maximum]
    bet_points = adsorption.iloc[: maximum].loc[adsorption[isotherm.pressure_key]
                                                > max_p_chosen / 10]
    min_p_chosen = bet_points[isotherm.pressure_key].iloc[0]

    # calculate the bet parameters
    slope, intercept, corr_coef, p, stderr = scipy.stats.linregress(
        bet_points[isotherm.pressure_key], bet_points.BET)
    c_const = (slope / intercept) + 1
    n_monolayer = 1 / (intercept * c_const)
    bet_area = n_monolayer * cross_section * (10**(-18)) * constants.Avogadro

    p_monolayer = 1 / (scipy.sqrt(c_const) + 1)
    roq_monolayer = n_monolayer * (1 - p_monolayer)
    bet_monolayer = p_monolayer / roq_monolayer

    # Checks for consistency

    if c_const < 0:
        warnings.warn("The C constant is negative")

    if corr_coef < 0.99:
        warnings.warn("The correlation is not linear")

    if (
        bet_points[isotherm.loading_key].iloc[1] > n_monolayer * 1000
    ) or (
        bet_points[isotherm.loading_key].iloc[-1] < n_monolayer * 1000
    ):
        warnings.warn("The monolayer point is not within the BET region")

    # PLOTTING
    if verbose:

        print("The slope of the BET line: s =", round(slope, 3))
        print("The intercept of the BET line: i =", round(intercept, 3))
        print("C =", int(round(c_const, 0)))
        print("Amount for a monolayer: n =",
              round(n_monolayer, 3), "mol/g")
        print("Minimum pressure point chosen is {0} and maximum is {1}".format(
            min_p_chosen, max_p_chosen))
        print("BET surface area: a =", int(round(bet_area, 0)), "m²/g")

        # Generate plot of isotherm
        fig = plt.figure()
        ax1 = fig.add_subplot(111)
        ax1.plot(adsorption[isotherm.pressure_key], adsorption[isotherm.loading_key],
                 marker='o', color='r', label='adsorption')
        ax1.set_title("Adsorption isotherm")
        ax1.set_xlabel('p/p°')
        ax1.set_ylabel('Quantity Adsorbed (mmol/g)')
        ax1.legend(loc='best')
        plt.show()

        # Generate plot of the BET points chosen

        fig = plt.figure()
        ax1 = fig.add_subplot(111)
        ax1.plot(adsorption[isotherm.pressure_key], adsorption['BET'],
                 marker='', color='g', label='all points')
        ax1.plot(bet_points[isotherm.pressure_key], bet_points['BET'],
                 marker='o', linestyle='', color='r', label='chosen points')
        ax1.plot(p_monolayer, bet_monolayer,
                 marker='x', linestyle='', color='black', label='monolayer point')
        ax1.set_ylim(ymin=0, ymax=bet_points['BET'].iloc[-1] * 1.2)
        ax1.set_xlim(
            xmin=0, xmax=bet_points[isotherm.pressure_key].iloc[-1] * 1.2)
        ax1.set_title("BET plot")
        ax1.set_xlabel('p/p°')
        ax1.set_ylabel('(p/p°)/(n(1-(P/P°)))')
        ax1.legend(loc='best')
        plt.show()

        # Generate plot of the Roquerol points chosen

        fig = plt.figure()
        ax1 = fig.add_subplot(111)
        ax1.plot(adsorption[isotherm.pressure_key], adsorption['roquerol'],
                 marker='', color='g', label='all points')
        ax1.plot(bet_points[isotherm.pressure_key], bet_points['roquerol'],
                 marker='o', linestyle='', color='r', label='chosen points')
        ax1.plot(p_monolayer, roq_monolayer,
                 marker='x', linestyle='', color='black', label='monolayer point')
        ax1.set_title("Roquerol plot")
        ax1.set_xlabel('p/p°')
        ax1.set_ylabel('(p/p°)/(n(1-(P/P°)))')
        ax1.legend(loc='best')
        plt.show()

    return bet_area
