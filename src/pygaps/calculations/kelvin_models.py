"""
Module contains functions to calculate the critical evaporation/condensation pore radius
the mesopore range.
"""

import numpy
import scipy


def meniscus_geometry(branch, pore_geometry):
    """
    Function which determines the meniscus geometry

    :param branch: branch of the isotherm used
    :param geometry: geometry of the pore

    :returns: geometry of the meniscus in the pore
    """
    if branch == 'adsorption':
        if pore_geometry == 'cylinder':
            m_geometry = 'cylinder'
        elif pore_geometry == 'sphere':
            m_geometry = 'sphere'
        elif pore_geometry == 'slit':
            m_geometry = 'cylinder'
    if branch == 'desorption':
        if pore_geometry == 'cylinder':
            m_geometry = 'sphere'
        elif pore_geometry == 'sphere':
            m_geometry = 'sphere'
        elif pore_geometry == 'slit':
            m_geometry = 'slit'

    return m_geometry


def kelvin_radius_std(pressure, meniscus_geometry, temperature,
                      liquid_density, adsorbate_molar_mass, adsorbate_surface_tension):
    """
    Calculates the kelvin radius of the pore, using the standard
    form of the kelvin equation.

    :param pressure: relative, unitless
    :param meniscus_geometry: geometry of the interface of the vapour and liquid phase
        **WARNING**: it is not the same as the pore geometry
    :param temperature: in kelvin
    :param liquid_density: g/cm3
    :param adsorbate_molar_mass: g/mol
    :param adsorbate_surface_tension: in mN/m

    :returns: radius(nm)

    Description:

    The standard kelvin equation for determining critical pore radius for condensation or
    evaporation.

    Limitations:

    The Kelvin equation assumes that adsorption in a pore is not different than adsorption
    on a standard surface. Therefore, no interactions with the adsorbent is accounted for.

    Furthermore, the geometry of the pore itself is considered to be invariant accross the
    entire adsorbate.

    """

    if meniscus_geometry == 'cylinder':
        geometry_factor = 1.0
    elif meniscus_geometry == 'sphere':
        geometry_factor = 2.0
    elif meniscus_geometry == 'slit':
        geometry_factor = 0.5

    adsorbate_molar_density = adsorbate_molar_mass / liquid_density

    coefficient = (geometry_factor * adsorbate_surface_tension *
                   adsorbate_molar_density) / (scipy.constants.gas_constant * temperature)

    radius = - coefficient / numpy.log(pressure)

    return radius
