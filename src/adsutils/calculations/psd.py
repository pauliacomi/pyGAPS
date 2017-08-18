"""
This module calculates the pore size distribution based on an isotherm
"""

__author__ = 'Paul A. Iacomi'

import numpy
import scipy.constants

import matplotlib.pyplot as plt

import adsutils.data as data

from .thickness_curves import _THICKNESS_MODELS
from .thickness_curves import thickness_halsey
from .thickness_curves import thickness_harkins_jura

_PSD_MODELS = ['BJH']


def pore_size_distribution(isotherm, psd_model, branch, thickness_model, verbose=False):
    """
    Calculates the pore size distribution using a 'classical' model

    According to Roquerol, inn adopting this approach, it is assumed that:
        - the Kelvin equation is applicable over the pore range (mesopores)
        - the meniscus curvature is controlled be the pore size and shape nad
        - the pores are rigid and of well defined shape
        - the filling/emptying of each pore does not depend on its location
        - the adsorption on the pore walls is not different from surface adsorption
    """

    # Function parameter checks
    if psd_model is None:
        raise Exception("Specify a model to generate the pore size"
                        " distribution e.g. psd_model=\"BJH\"")
    if psd_model not in _PSD_MODELS:
        raise Exception("Model {} not an option for psd.".format(psd_model),
                        "Available models are {}".format(_PSD_MODELS))

    if thickness_model is None:
        raise Exception("Specify a model to generate the thickness curve"
                        " e.g. thickness_model=\"Halsey\"")

    if thickness_model not in _THICKNESS_MODELS:
        raise Exception("Model {} not an option for pore size distribution.".format(thickness_model),
                        "Available models are {}".format(_THICKNESS_MODELS))

    if thickness_model == 'Halsey':
        t_model = thickness_halsey

    elif thickness_model == 'Harkins/Jura':
        t_model = thickness_harkins_jura

    # Get gas and properties from master list
    # TODO think about how to automate these
    ads_gas = next(
        (gas for gas in data.GAS_LIST if isotherm.gas == gas.name), None)
    if ads_gas is None:
        raise Exception("Gas {0} does not exist in list of gasses. "
                        "First populate adsutils.GAS_LIST "
                        "with required gas class".format(isotherm.gas))

    gas_molar_mass = ads_gas.properties.get("molar_mass")
    if gas_molar_mass is None:
        raise Exception("Gas {0} does not have a property named "
                        "molar_mass. This must be available for PSD "
                        "calculation".format(isotherm.gas))

    gas_surface_tension = ads_gas.properties.get("surface_tension")
    # TODO delete
    gas_surface_tension = 8.85
    if gas_surface_tension is None:
        raise Exception("Gas {0} does not have a property named "
                        "surface_tension. This must be available for PSD "
                        "calculation".format(isotherm.gas))

    liquid_density = ads_gas.properties.get("liquid_density")
    # TODO delete
    liquid_density = 0.807
    if liquid_density is None:
        raise Exception("Gas {0} does not have a property named "
                        "liquid_density. This must be available for PSD "
                        "calculation".format(isotherm.gas))

    # Read data in, depending on branch requested
    if branch == 'adsorption':
        loading = isotherm.loading_ads(unit='mol')[::-1]
        pressure = isotherm.pressure_ads()[::-1]
        geometry = 'cylinder'
    # If on desorption branch, data will be reversed
    elif branch == 'desorption':
        geometry = 'sphere'
        loading = isotherm.loading_des(unit='mol')
        pressure = isotherm.pressure_des()

    if loading is None:
        raise Exception("The isotherm does not have the required branch for"
                        " this calculation")

    if psd_model == 'BJH':
        pore_widths, pore_dist = psd_bjh_raw(
            loading, pressure, t_model, isotherm.t_exp,
            liquid_density, gas_molar_mass, gas_surface_tension, geometry)

    result_dict = {
        'pore_widths': pore_widths,
        'pore_distribution': pore_dist,
    }

    if verbose:
        fig = plt.figure()
        psd_plot(fig, pore_widths, pore_dist)

    return result_dict


def psd_bjh_raw(loading, pressure, thickness_model, temperature, liquid_density, gas_molar_mass, gas_surface_tension, geometry):
    """
    Calculates the pore size distribution using the BJH method

    loading:
    pressure:
    """
    # Checks
    if len(pressure) != len(loading):
        raise Exception("The length of the pressure and loading arrays"
                        " do not match")

    # Calculate the adsorbed volume of liquid and diff
    volume_adsorbed = loading * gas_molar_mass / liquid_density * 1e6
    d_volume = -numpy.diff(volume_adsorbed)

    # Generate the thickness curve, average and diff
    thickness_curve = list(map(thickness_model, pressure))
    avg_thickness = numpy.add(thickness_curve[:-1], thickness_curve[1:]) / 2
    d_thickness = -numpy.diff(thickness_curve)

    # Generate the Kelvin pore radii and average
    kelvin_radius = kelvin_radius_std(
        pressure, temperature, liquid_density, gas_molar_mass, gas_surface_tension, geometry)
    avg_k_radius = numpy.add(kelvin_radius[:-1], kelvin_radius[1:]) / 2

    # Critical pore radii as a combination of the adsorbed
    # layer thickness and kelvin pore radius, with average and diff
    pore_radii = numpy.add(thickness_curve, kelvin_radius)
    avg_pore_radii = numpy.add(avg_thickness, avg_k_radius)
    d_pore_radii = -numpy.diff(pore_radii)

    # Now we can iteratively calculate the pore size distribution
    d_area = 0
    sum_d_area = 0
    sum_d_area_div_r = 0
    pore_volumes = []

    for i, _ in enumerate(avg_pore_radii):

        Q_var = (avg_pore_radii[i] / avg_k_radius[i])**2
        D_var = d_thickness[i] * sum_d_area
        E_var = d_thickness[i] * avg_thickness[i] * sum_d_area_div_r

        pore_volume = (d_volume[i] - D_var + E_var) * Q_var

        d_area = 2 * pore_volume / avg_pore_radii[i]
        sum_d_area += d_area
        sum_d_area_div_r += d_area / avg_pore_radii[i]

        pore_volumes.append(pore_volume)

    pore_widths = 2 * avg_pore_radii
    pore_dist = numpy.divide(pore_volumes, 2 * d_pore_radii) / 1e6

    return pore_widths, pore_dist


def kelvin_radius_std(pressure, temperature, liquid_density, gas_molar_mass, gas_surface_tension, geometry):
    """
    Calculates the kelvin radius of the pore

    pressure: relative, unitless
    temperature: K
    liquid_density: g/cm3
    gas_molar_mass: g/mol
    gas_surface_tension mN/m

    returns radius(nm)

    """

    if geometry == 'cylinder':
        geometry_factor = 1
    elif geometry == 'sphere':
        geometry_factor = 2

    gas_molar_density = gas_molar_mass / liquid_density

    coefficient = (geometry_factor * gas_surface_tension *
                   gas_molar_density) / (scipy.constants.gas_constant * temperature)

    radius = - coefficient / numpy.log(pressure)

    return radius


def psd_plot(fig, pore_radii, pore_dist):
    """Draws the pore size distribution plot"""
    ax1 = fig.add_subplot(111)
    ax1.plot(pore_radii, pore_dist,
             marker='', color='g', label='distribution')
    ax1.set_xscale('log')
    ax1.set_title("PSD plot")
    ax1.set_xlabel('Pore width (A)')
    ax1.set_ylabel('Pore size')
    ax1.legend(loc='best')
    plt.show()
