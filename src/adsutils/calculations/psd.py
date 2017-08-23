"""
This module calculates the pore size distribution based on an isotherm
"""

__author__ = 'Paul A. Iacomi'

from functools import partial

import numpy
import scipy.constants

import matplotlib.pyplot as plt

from ..classes.gas import Gas

from .thickness_curves import _THICKNESS_MODELS
from .thickness_curves import thickness_halsey
from .thickness_curves import thickness_harkins_jura

_PSD_MODELS = ['BJH', 'DH']
_PORE_GEOMETRIES = ['cylinder', 'sphere', 'slit']


def pore_size_distribution(isotherm, branch, psd_model, thickness_model, pore_geometry='cylinder', verbose=False):
    """
    Calculates the pore size distribution using a 'classical' model

    According to Roquerol, in adopting this approach, it is assumed that:
        - the Kelvin equation is applicable over the pore range (mesopores)
        - the meniscus curvature is controlled be the pore size and shape nad
        - the pores are rigid and of well defined shape
        - the filling/emptying of each pore does not depend on its location
        - the adsorption on the pore walls is not different from surface adsorption
    """

    # Function parameter checks
    if isotherm.mode_adsorbent != "mass":
        raise Exception("The isotherm must be in per mass of adsorbent."
                        "First convert it using implicit functions")
    if isotherm.mode_pressure != "relative":
        raise Exception("The isotherm must be in relative pressure mode."
                        "First convert it using implicit functions")

    if branch not in ['adsorption', 'desorption']:
        raise Exception("Branch {} not an option for psd.".format(branch),
                        "Select either 'adsorption' or 'desorption'")
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
    if pore_geometry not in _PORE_GEOMETRIES:
        raise Exception("Geometry {} not an option for pore size distribution.".format(pore_geometry),
                        "Available geometries are {}".format(_PORE_GEOMETRIES))

    # Get adsorbate properties
    ads_gas = Gas.from_list(isotherm.gas)
    molar_mass = ads_gas.molar_mass()
    liquid_density = ads_gas.liquid_density(isotherm.t_exp)
    surface_tension = ads_gas.surface_tension(isotherm.t_exp)

    # Read data in, depending on branch requested
    if branch == 'adsorption':
        loading = isotherm.loading_ads(unit='mmol')[::-1]
        pressure = isotherm.pressure_ads()[::-1]
    # If on desorption branch, data will be reversed
    elif branch == 'desorption':
        loading = isotherm.loading_des(unit='mmol')
        pressure = isotherm.pressure_des()
    if loading is None:
        raise Exception("The isotherm does not have the required branch for"
                        " this calculation")

    # Thickness model definitions
    if thickness_model == 'Halsey':
        t_model = thickness_halsey
    elif thickness_model == 'Harkins/Jura':
        t_model = thickness_harkins_jura

    # Kelvin model definitions
    meniscus_geometry = kelvin_geometry(branch, pore_geometry)
    k_model = partial(kelvin_radius_std,
                      meniscus_geometry=meniscus_geometry,
                      temperature=isotherm.t_exp,
                      liquid_density=liquid_density,
                      gas_molar_mass=molar_mass,
                      gas_surface_tension=surface_tension)

    # Call specified pore size distribution function
    if psd_model == 'BJH':
        pore_widths, pore_dist = psd_bjh_raw(
            loading, pressure, pore_geometry,
            t_model, k_model,
            liquid_density, molar_mass)
    elif psd_model == 'DH':
        pore_widths, pore_dist = psd_dollimore_heal_raw(
            loading, pressure, pore_geometry,
            t_model, k_model,
            liquid_density, molar_mass)

    result_dict = {
        'pore_widths': pore_widths,
        'pore_distribution': pore_dist,
    }

    if verbose:
        fig = plt.figure()
        psd_plot(fig, pore_widths, pore_dist)

    return result_dict


def psd_bjh_raw(loading, pressure, pore_geometry, thickness_model, kelvin_model, liquid_density, gas_molar_mass):
    """
    Calculates the pore size distribution using the BJH method

    loading: in mmol/g
    pressure: relative
    pore_geometry: 'sphere', 'cylinder' or 'slit'
    thickness_model: a callable which returns the thickenss of the adsorbed layer at a pressure p
    kelvin_model: a callable which returns the critical kelvin radius at a pressure p
    liquid_density: density of the adsorbate in the adsorbed state, in g/cm3
    gas_molar_mass: in g/mol

    """
    # Checks
    if len(pressure) != len(loading):
        raise Exception("The length of the pressure and loading arrays"
                        " do not match")

    # Calculate the adsorbed volume of liquid and diff
    volume_adsorbed = loading * gas_molar_mass / liquid_density * 1000
    d_volume = -numpy.diff(volume_adsorbed)

    # Generate the thickness curve, average and diff
    thickness_curve = list(map(thickness_model, pressure))
    avg_thickness = numpy.add(thickness_curve[:-1], thickness_curve[1:]) / 2
    d_thickness = -numpy.diff(thickness_curve)

    # Generate the Kelvin pore radii and average
    kelvin_radius = list(map(kelvin_model, pressure))
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
    pore_dist = (pore_volumes / (2 * d_pore_radii)) / 1e6

    return pore_widths, pore_dist


def psd_dollimore_heal_raw(loading, pressure, pore_geometry, thickness_model, kelvin_model, liquid_density, gas_molar_mass):
    """
    Calculates the pore size distribution using the Dollimore-Heal method

    loading: in mmol/g
    pressure: relative
    pore_geometry: 'sphere', 'cylinder' or 'slit'
    thickness_model: a callable which returns the thickenss of the adsorbed layer at a pressure p
    kelvin_model: a callable which returns the critical kelvin radius at a pressure p
    liquid_density: density of the adsorbate in the adsorbed state, in g/cm3
    gas_molar_mass: in g/mol
    """
    # Checks
    if len(pressure) != len(loading):
        raise Exception("The length of the pressure and loading arrays"
                        " do not match")

    # Geometry factors
    if pore_geometry == 'cylinder':
        factor = 2
    elif pore_geometry == 'sphere':
        factor = 3

    # Calculate the adsorbed volume of liquid and diff
    volume_adsorbed = loading * gas_molar_mass / liquid_density * 1000
    d_volume = -numpy.diff(volume_adsorbed)

    # Generate the thickness curve, average and diff
    thickness_curve = list(map(thickness_model, pressure))
    avg_thickness = numpy.add(thickness_curve[:-1], thickness_curve[1:]) / 2
    d_thickness = -numpy.diff(thickness_curve)

    # Generate the Kelvin pore radii and average
    kelvin_radius = list(map(kelvin_model, pressure))
    avg_k_radius = numpy.add(kelvin_radius[:-1], kelvin_radius[1:]) / 2

    # Critical pore radii as a combination of the adsorbed
    # layer thickness and kelvin pore radius, with average and diff
    pore_radii = numpy.add(thickness_curve, kelvin_radius)
    avg_pore_radii = numpy.add(avg_thickness, avg_k_radius)
    d_pore_radii = -numpy.diff(pore_radii)

    # Now we can iteratively calculate the pore size distribution
    d_area = 0
    length = 0
    sum_d_area = 0
    sum_length = 0
    pore_volumes = []

    for i, _ in enumerate(avg_pore_radii):

        Q_var = (avg_pore_radii[i] / (avg_k_radius[i] + d_thickness[i]))**2
        D_var = d_thickness[i] * sum_d_area
        E_var = 2 * scipy.constants.pi * \
            d_thickness[i] * avg_thickness[i] * sum_length

        pore_volume = (d_volume[i] - D_var + E_var) * Q_var

        d_area = 2 * pore_volume / avg_pore_radii[i]
        length = d_area / (2 * scipy.constants.pi * avg_pore_radii[i])
        sum_d_area += d_area
        sum_length += length

        pore_volumes.append(pore_volume)

    pore_widths = 2 * avg_pore_radii
    pore_dist = (pore_volumes / (2 * d_pore_radii)) / 1e6

    return pore_widths, pore_dist


def kelvin_geometry(branch, geometry):
    if branch == 'adsorption':
        if geometry == 'cylinder':
            kelvin_geometry = 'cylinder'
        elif geometry == 'sphere':
            kelvin_geometry = 'sphere'
        elif geometry == 'slit':
            kelvin_geometry = 'cylinder'
    if branch == 'desorption':
        if geometry == 'cylinder':
            kelvin_geometry = 'sphere'
        elif geometry == 'sphere':
            kelvin_geometry = 'sphere'
        elif geometry == 'slit':
            kelvin_geometry = 'slit'

    return kelvin_geometry


def kelvin_radius_std(pressure, meniscus_geometry, temperature, liquid_density, gas_molar_mass, gas_surface_tension):
    """
    Calculates the kelvin radius of the pore

    pressure: relative, unitless
    branch: 'adsorption' or 'desorption'
    temperature: in kelvin
    liquid_density: g/cm3
    gas_molar_mass: g/mol
    gas_surface_tension: in mN/m

    return radius(nm)

    """

    if meniscus_geometry == 'cylinder':
        geometry_factor = 1.0
    elif meniscus_geometry == 'sphere':
        geometry_factor = 2.0
    elif meniscus_geometry == 'slit':
        geometry_factor = 0.5

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
    ax1.set_ylim(ymin=0)
    plt.show()
