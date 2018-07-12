"""
Module contains functions to calculate the critical evaporation/condensation pore radius
the mesopore range.
"""

import numpy
import scipy


def meniscus_geometry(branch, pore_geometry):
    """
    Function which determines the meniscus geometry.

    Parameters
    ----------
    branch : {'ads', 'des'}
        Branch of the isotherm used.
    geometry : {'slit', 'cylinder', 'cylinder'}
        Geometry of the pore.

    Returns
    -------
    str
        Geometry of the meniscus in the pore.
    """
    if branch == 'ads':
        if pore_geometry == 'cylinder':
            m_geometry = 'cylinder'
        elif pore_geometry == 'sphere':
            m_geometry = 'sphere'
        elif pore_geometry == 'slit':
            m_geometry = 'cylinder'
    if branch == 'des':
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

    Parameters
    ----------
    pressure :
        Relative, unitless.
    meniscus_geometry : str
        Geometry of the interface of the vapour and liquid phase.
        **WARNING**: it is not the same as the pore geometry.
    temperature : float
        Temperature in kelvin.
    liquid_density : float
        Density of the adsorbed phase, assuming it can be approximated as a
        liquid g/cm3.
    adsorbate_molar_mass : float
        Molar area of the adsorbate, g/mol.
    adsorbate_surface_tension : float
        Surface tension of the adsorbate, in mN/m.

    Returns
    -------
    float
        Kelvin radius(nm).

    Notes
    -----
    *Description*

    The standard kelvin equation for determining critical pore radius
    for condensation or evaporation.

    .. math::
        \\ln\\Big(\\frac{p}{p_0}\Big) = -\\frac{2 \\cos\\theta M_m \\gamma}{r_K\\rho_l RT}

    *Limitations*

    The Kelvin equation assumes that adsorption in a pore is not different than adsorption
    on a standard surface. Therefore, no interactions with the adsorbent is accounted for.

    Furthermore, the geometry of the pore itself is considered to be invariant accross the
    entire adsorbate.

    """

    if meniscus_geometry == 'cylinder':
        geometry_factor = 2.0
    elif meniscus_geometry == 'sphere':
        geometry_factor = 1.0
    elif meniscus_geometry == 'slit':
        geometry_factor = 4.0

    adsorbate_molar_density = adsorbate_molar_mass / liquid_density

    coefficient = (2 * adsorbate_surface_tension *
                   adsorbate_molar_density) / (geometry_factor *
                                               scipy.constants.gas_constant * temperature)

    radius = - coefficient / numpy.log(pressure)

    return radius


_KELVIN_MODELS = {
    'Kelvin': kelvin_radius_std,
}
