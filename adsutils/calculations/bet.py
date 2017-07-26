"""
This module calculates the BET surface area based on an isotherm
"""

__author__ = 'Paul A. Iacomi and Bastien Aillet'

#%%
import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
import scipy.stats
import adsutils


AVOGADRO_NUMBER = 6.02214 * (10 ** 23)
NITROGEN_CROSS_SECTION = 1.62 * (10 ** (-19))
PROPANE_CROSS_SECTION = 3.9 * (10 ** (-19))


def area_BET(isotherm, verbose=False):
    """
    Fonction retournant le graphe de l'isotherm d'adsorption de
    l'expérience du triflex en prenant le file en format CSV
    """

    if isotherm.mode_adsorbent != "mass":
        raise Exception("The isotherm must be in per mass of adsorbent."
                        "First convert it using implicit functions")
    if isotherm.mode_pressure != "relative":
        raise Exception("The isotherm must be in relative pressure mode."
                        "First convert it using implicit functions")
    if isotherm.unit_loading != "mmol":
        raise Exception("The loading must be in mmol."
                        "First convert it using implicit functions")

    # Read data in
    adsorption = isotherm.adsdata()

    # Generate the BET values
    adsorption = adsorption.assign(roquerol=lambda adsorption:
                                   adsorption[isotherm.loading_key] / 1000 *
                                   (1 - adsorption[isotherm.pressure_key]))
    adsorption = adsorption.assign(BET=lambda adsorption:
                                   adsorption[isotherm.pressure_key] /
                                   adsorption.roquerol)
    adsorption = adsorption.assign(good=lambda adsorption: 
                                   adsorption.loc[:, 'roquerol'].diff().fillna(0) < 0)

    bet_points = adsorption.iloc[:(adsorption.loc[:, 'good'].values.argmax())]


    slope, intercept, r, p, stderr = scipy.stats.linregress(bet_points[isotherm.pressure_key], bet_points.BET)

    C = (slope / intercept) + 1
    amount_monolayer = 1 / (intercept * C)
    area = amount_monolayer * PROPANE_CROSS_SECTION * AVOGADRO_NUMBER

    # TODO Implement all of roquerol's laws for BET
    # mono_capacity_real = 
    # mono_capacity_calc = 1 / (np.sqrt(C) + 1)



    # Checks for consistency

    if C < 0:
        raise Warning("The C constant is negative")
    if r < 0.9:
        raise Warning("The correlation is not linear")


    # PLOTTING
    if verbose:
        # Generate plot of isotherm with desorption and adsorption branches
        fig = plt.figure()
        ax1 = fig.add_subplot(111)

        ax1.plot(adsorption[isotherm.pressure_key], adsorption[isotherm.loading_key], marker='o', color='r', label='adsorption')
        ax1.set_title("Adsorption isotherm")
        ax1.set_xlabel('p/p°')
        ax1.set_ylabel('Quantity Adsorbed (mmol/g)')
        ax1.legend(loc='best')
        plt.show()


        # Generate plot of the BET points chosen

        fig2 = plt.figure()
        ax2 = fig2.add_subplot(111)
        ax2.plot(bet_points[isotherm.pressure_key], bet_points['BET'], marker='o', color='r', label='chosen points')
        ax2.plot(adsorption[isotherm.pressure_key], adsorption['BET'], marker='', color='g', label='all points')
        ax2.set_ylim(ymin=0, ymax=bet_points['BET'].iloc[-1] * 1.2)
        ax2.set_xlim(xmin=0, xmax=bet_points[isotherm.pressure_key].iloc[-1] * 1.2)
        ax2.set_title("BET plot")
        ax2.set_xlabel('p/p°')
        ax2.set_ylabel('(p/p°)/(n(1-(P/P°)))')
        ax2.legend(loc='best')
        plt.show()


        # Generate plot of the Roquerol points chosen

        fig2 = plt.figure()
        ax2 = fig2.add_subplot(111)
        ax2.plot(bet_points[isotherm.pressure_key], bet_points['roquerol'], marker='o', color='r', label='chosen points')
        ax2.plot(adsorption[isotherm.pressure_key], adsorption['roquerol'], marker='', color='g', label='all points')
        ax2.set_title("BET plot")
        ax2.set_xlabel('p/p°')
        ax2.set_ylabel('(p/p°)/(n(1-(P/P°)))')
        ax2.legend(loc='best')
        plt.show()


        print('The slope of the BET line: s =', round(slope, 3))
        print("The intercept of the BET line: i =", round(intercept, 3))
        print("C =", int(round(C, 0)))
        print("Amount for a monolayer: n =", round(amount_monolayer, 3), "mol/g")
        print("BET surface area: a =", int(round(area, 0)), "m²/g")

    return area
