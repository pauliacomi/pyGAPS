"""
This module calculates the t-plot based on an isotherm
"""

__author__ = 'Paul A. Iacomi'

import scipy

import adsutils.data as data

# from .bet import area_BET
from .thickness_curves import thickness_halsey
from .thickness_curves import thickness_harkins_jura

_MODELS = ["Halsey", "Harkins/Jura"]


def t_plot(isotherm, thickness_model):
    """
    Calculates the external surface area and adsorbed volume using the t-plot method
    """
    # Checks
    if thickness_model is None:
        raise Exception("Specify a model to generate the thickness curve"
                        " e.g. thickness_model=\"Halsey\"")
    if thickness_model not in _MODELS:
        raise Exception("Model {} not an option for t-plot.".format(thickness_model),
                        "Available models are {}".format(_MODELS))

    if thickness_model == "Halsey":
        t_model = thickness_halsey

    if thickness_model == "Harkins/Jura":
        t_model = thickness_harkins_jura

    # See if gas exists in master list
    ads_gas = next((gas for gas in data.GAS_LIST if isotherm.gas == gas.name))
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
    if liquid_density is None:
        raise Exception("Gas {0} does not have a property named "
                        "liquid_density. This must be available for t-plot "
                        "calculation".format(isotherm.gas))

    # Read data in
    adsorption = isotherm.adsdata()

    # Generate the thickness model columns
    adsorption = adsorption.assign(
        thickness=t_model(adsorption[isotherm.loading_key]))

    # Get minimum and maximum pressure
    min_p = 0.5
    max_p = 0.8

    # select the maximum and minimum of the points
    t_points = adsorption.loc[adsorption[isotherm.pressure_key]
                              > min_p: adsorption[isotherm.pressure_key] < max_p]

    slope, intercept, corr_coef, p, stderr = scipy.stats.linregress(
        t_points[isotherm.loading_key] / scipy.constants.milli, t_points.thickness / scipy.constants.nano)

    # TODO units
    adsorbed_volume = intercept * molar_mass / liquid_density
    external_area = slope * molar_mass / liquid_density

    return adsorbed_volume, external_area
