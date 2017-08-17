"""
This module calculates the t-plot based on an isotherm
"""

__author__ = 'Paul A. Iacomi'

import scipy

import matplotlib.pyplot as plt

import adsutils.data as data

from .thickness_curves import _THICKNESS_MODELS
from .thickness_curves import thickness_halsey
from .thickness_curves import thickness_harkins_jura


def t_plot(isotherm, thickness_model, verbose=False):
    """
    Calculates the external surface area and adsorbed volume using the t-plot method
    """
    # Checks
    if isotherm.mode_adsorbent != "mass":
        raise Exception("The isotherm must be in per mass of adsorbent."
                        "First convert it using implicit functions")
    if isotherm.mode_pressure != "relative":
        raise Exception("The isotherm must be in relative pressure mode."
                        "First convert it using implicit functions")

    if thickness_model is None:
        raise Exception("Specify a model to generate the thickness curve"
                        " e.g. thickness_model=\"Halsey\"")
    if thickness_model not in _THICKNESS_MODELS:
        raise Exception("Model {} not an option for t-plot.".format(thickness_model),
                        "Available models are {}".format(_THICKNESS_MODELS))

    if thickness_model == "Halsey":
        t_model = thickness_halsey

    elif thickness_model == "Harkins/Jura":
        t_model = thickness_harkins_jura

    # See if gas exists in master list
    ads_gas = next(
        (gas for gas in data.GAS_LIST if isotherm.gas == gas.name), None)
    if ads_gas is None:
        raise Exception("Gas {0} does not exist in list of gasses. "
                        "First populate adsutils.GAS_LIST "
                        "with required gas class".format(isotherm.gas))

    molar_mass = ads_gas.properties.get("molar_mass")
    if molar_mass is None:
        raise Exception("Gas {0} does not have a property named "
                        "molar_mass. This must be available for t-plot "
                        "calculation".format(isotherm.gas))

    liquid_density = ads_gas.properties.get("liquid_density")
    # TODO remove
    liquid_density = 34.679  # cm3/mol
    if liquid_density is None:
        raise Exception("Gas {0} does not have a property named "
                        "liquid_density. This must be available for t-plot "
                        "calculation".format(isotherm.gas))

    # Read data in
    loading = isotherm.loading_ads(unit='mol')
    pressure = isotherm.pressure_ads()

    adsorbed_volume, external_area = t_plot_raw(
        loading, pressure, t_model, molar_mass, liquid_density, verbose)

    result_dict = {
        'adsorbed_volume': adsorbed_volume,
        'external_area': external_area,
    }

    return result_dict


def t_plot_raw(loading, pressure, thickness_model, molar_mass, liquid_density, verbose=False):
    """
    Calculates the external surface area and adsorbed volume using the t-plot method
    """

    # Generate the thickness model columns
    thickness_curve = list(map(thickness_model, pressure))

    # Get minimum and maximum pressure
    min_p = 0.00
    max_p = 0.90

    minimum = None
    maximum = None

    # select the maximum and minimum of the points
    for index, value in enumerate(pressure):
        if minimum is None and value > min_p:
            minimum = index
        if maximum is None and value > max_p:
            maximum = index

    # do the regression
    slope, intercept, corr_coef, p, stderr = scipy.stats.linregress(
        loading[minimum:maximum],
        thickness_curve[minimum:maximum])

    # TODO units
    adsorbed_volume = intercept * molar_mass / liquid_density / scipy.constants.nano
    external_area = slope * molar_mass / liquid_density

    if verbose:
        fig = plt.figure()
        plot_tp(fig, thickness_curve, loading, minimum, maximum)

    return adsorbed_volume, external_area


def plot_tp(fig, thickness_curve, loading, minimum, maximum):
    """Draws the t-plot"""
    ax1 = fig.add_subplot(111)
    ax1.plot(thickness_curve, loading,
             marker='', color='g', label='all points')
    ax1.plot(thickness_curve[minimum:maximum], loading[minimum:maximum],
             marker='o', linestyle='', color='r', label='chosen points')
    ax1.set_title("t-plot")
    ax1.set_xlabel('t')
    ax1.set_ylabel('amount adsorbed')
    ax1.legend(loc='best')
    plt.show()
