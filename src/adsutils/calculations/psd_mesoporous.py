"""
Module contains 'classical' methods of calculating a pore size distribution for pores in
the mesopore range (2-50 nm).
"""

import numpy
import scipy


def psd_bjh(loading, pressure, pore_geometry,
            thickness_model, condensation_model,
            liquid_density, gas_molar_mass):
    """
    Calculates the pore size distribution using the BJH method

    :param loading: in mmol/g
    :param pressure: relative
    :param pore_geometry: 'sphere', 'cylinder' or 'slit'
    :param thickness_model: a callable which returns the thickenss of the adsorbed layer
        at a pressure p
    :param condensation_model: a callable which returns the critical kelvin radius at a pressure p
    :param liquid_density: density of the adsorbate in the adsorbed state, in g/cm3
    :param gas_molar_mass: in g/mol

    :returns: pore widths, pore distribution
    :rtype: arrays

    **Description:**

    The BJH or Barrett, Joyner and Halenda method for calculation of pore size distribution
    is based on a classical description of the adsorbate behaviour in the adsorbent pores.
    Under this method, the adsorbate is adsorbing on the pore walls in a predictable way,
    and decreasing the apparent pore volume until condensation takes place, filling the
    entire pore. The two variables, layer thickness and radius where condensation takes
    place can be modelled by a thickness model (such as Halsey, Harkins & Jura, etc.) and a
    critical radius model for condensation/evaporation, based on a form of the Kelvin equation.

    **Limitations:**

    According to Roquerol, in adopting this approach, it is assumed that:

        - the Kelvin equation is applicable over the pore range (mesopores)
        - the meniscus curvature is controlled be the pore size and shape
        - the pores are rigid and of well defined shape
        - the filling/emptying of each pore does not depend on its location
        - the adsorption on the pore walls is not different from surface adsorption

    Practical considerations for use of BJH:

        - only pore sized upwards of 2.5 nm can be considered accurately predicted
        - the pores are considered open-ended and non-intersecting

    """
    # Paramter checks
    if len(pressure) != len(loading):
        raise Exception("The length of the pressure and loading arrays"
                        " do not match")

    if pore_geometry == 'slit':
        raise Exception('Not implemented')
    elif pore_geometry == 'cylinder':
        pass
    elif pore_geometry == 'sphere':
        raise Exception('Not implemented')

    # Calculate the adsorbed volume of liquid and diff
    volume_adsorbed = loading * gas_molar_mass / liquid_density * 1000
    d_volume = -numpy.diff(volume_adsorbed)

    # Generate the thickness curve, average and diff
    thickness_curve = numpy.array(list(map(thickness_model, pressure)))
    avg_thickness = numpy.add(thickness_curve[:-1], thickness_curve[1:]) / 2
    d_thickness = -numpy.diff(thickness_curve)

    # Generate the Kelvin pore radii and average
    kelvin_radius = numpy.array(list(map(condensation_model, pressure)))
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

        R_factor = (avg_pore_radii[i] / (avg_k_radius[i] + d_thickness[i]))**2
        D_var = d_thickness[i] * sum_d_area
        E_var = d_thickness[i] * avg_thickness[i] * sum_d_area_div_r

        pore_volume = (d_volume[i] - D_var + E_var) * R_factor

        d_area = 2 * pore_volume / avg_pore_radii[i]
        sum_d_area += d_area
        sum_d_area_div_r += d_area / avg_pore_radii[i]

        pore_volumes.append(pore_volume)

    pore_widths = 2 * avg_pore_radii
    pore_dist = (pore_volumes / (2 * d_pore_radii)) / 1e6

    return pore_widths, pore_dist


def psd_dollimore_heal(loading, pressure, pore_geometry,
                       thickness_model, condensation_model,
                       liquid_density, gas_molar_mass):
    """
    Calculates the pore size distribution using the Dollimore-Heal method

    :param loading: in mmol/g
    :param pressure: relative
    :param pore_geometry: 'sphere', 'cylinder' or 'slit'
    :param thickness_model: a callable which returns the thickenss of the adsorbed layer
        at a pressure p
    :param condensation_model: a callable which returns the critical kelvin radius at a pressure p
    :param liquid_density: density of the adsorbate in the adsorbed state, in g/cm3
    :param gas_molar_mass: in g/mol

    :returns: pore widths, pore distribution
    :rtype: arrays

    **Description:**

    The DH or Dollimore-Heal method of calculation of pore size distribution is an
    extension of the BJH method, which takes into account the geometry of the pores
    by introducing a length component.

    Like the BJH method, it is based on a classical description of the adsorbate behaviour
    in the adsorbent pores. Under this method, the adsorbate is adsorbing on the pore walls
    in a predictable way, and decreasing the apparent pore volume until condensation takes
    place, filling the entire pore. The two variables, layer thickness and radius where
    condensation takes place can be modelled by a thickness model (such as Halsey, Harkins
    & Jura, etc.) and a critical radius model for condensation/evaporation, based
    on a form of the Kelvin equation.

    **Limitations:**

    According to Roquerol, in adopting this approach, it is assumed that:

        - the Kelvin equation is applicable over the pore range (mesopores)
        - the meniscus curvature is controlled be the pore size and shape
        - the pores are rigid and of well defined shape
        - the filling/emptying of each pore does not depend on its location
        - the adsorption on the pore walls is not different from surface adsorption

    Practical considerations for use of DH method:

        - only pore sized upwards of 2.5 nm can be considered accurately predicted
        - the pores are considered open-ended and non-intersecting

    """
    # Checks
    if len(pressure) != len(loading):
        raise Exception("The length of the pressure and loading arrays"
                        " do not match")

    if pore_geometry == 'slit':
        raise Exception('Not implemented')
    if pore_geometry == 'cylinder':
        pass
    if pore_geometry == 'sphere':
        raise Exception('Not implemented')

    # Calculate the adsorbed volume of liquid and diff
    volume_adsorbed = loading * gas_molar_mass / liquid_density * 1000
    d_volume = -numpy.diff(volume_adsorbed)

    # Generate the thickness curve, average and diff
    thickness_curve = numpy.array(list(map(thickness_model, pressure)))
    avg_thickness = numpy.add(thickness_curve[:-1], thickness_curve[1:]) / 2
    d_thickness = -numpy.diff(thickness_curve)

    # Generate the Kelvin pore radii and average
    kelvin_radius = numpy.array(list(map(condensation_model, pressure)))
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

        R_factor = (avg_pore_radii[i] /
                    (avg_k_radius[i] + d_thickness[i] / 2))**2
        D_var = d_thickness[i] * sum_d_area
        E_var = 2 * scipy.constants.pi * \
            d_thickness[i] * avg_thickness[i] * sum_length

        pore_volume = (d_volume[i] - D_var + E_var) * R_factor

        d_area = 2 * pore_volume / avg_pore_radii[i]
        length = d_area / (2 * scipy.constants.pi * avg_pore_radii[i])
        sum_d_area += d_area
        sum_length += length

        pore_volumes.append(pore_volume)

    pore_widths = 2 * avg_pore_radii
    pore_dist = (pore_volumes / (2 * d_pore_radii)) / 1e6

    return pore_widths, pore_dist
