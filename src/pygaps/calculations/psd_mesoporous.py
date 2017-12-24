"""
Module contains 'classical' methods of calculating a pore size distribution for pores in
the mesopore range (2-50 nm).
"""

import numpy
import scipy

from ..utilities.exceptions import ParameterError


def psd_bjh(loading, pressure, pore_geometry,
            thickness_model, condensation_model,
            liquid_density, adsorbate_molar_mass):
    """
    Calculates the pore size distribution using the BJH method.

    Parameters
    ----------
    loading : array
        Adsorbed amount in mmol/g.
    pressure : array
        Relative pressure.
    pore_geometry : str
        The geometry of the pore, eg. 'sphere', 'cylinder' or 'slit'.
    thickness_model : callable
        Function which returns the thickness of the adsorbed layer
        at a pressure p.
    condensation_model : callable
        Function which returns the critical kelvin radius at a pressure p.
    liquid_density : float
        Density of the adsorbate in the adsorbed state, in g/cm3.
    adsorbate_molar_mass : float
        Molar mass of the adsorbate in g/mol.

    Returns
    -------
    pore widths : array
        Widths of the pores.
    pore_dist : array
        Amount of each pore width.

    Notes
    -----
    *Description*

    The BJH or Barrett, Joyner and Halenda [#]_ method for calculation of pore size distribution
    is based on a classical description of the adsorbate behaviour in the adsorbent pores.
    Under this method, the adsorbate is adsorbing on the pore walls in a predictable way,
    and decreasing the apparent pore volume until condensation takes place, filling the
    entire pore. The two variables, layer thickness and radius where condensation takes
    place can be modelled by a thickness model (such as Halsey, Harkins & Jura, etc.) and a
    critical radius model for condensation/evaporation, based on a form of the Kelvin equation.

    .. math::

        r_p = t + r_k

    The original model used the desorption curve as a basis for calculating pore size distribution.
    Between two points of the curve, the volume desorbed can be described as the volume contribution
    from pore evaporation and the volume from layer thickness decrease as per the equation
    above. The computation is done cumulatively, starting from the filled pores and calculating for each
    point the volume adsorbed in a pore from the following equation:

    .. math::

        V_p & = \\Big(\\frac{\\bar{r}_p}{\\bar{r}_k + \\Delta t_n}\\Big)^2
                (\\Delta V_n - \\Delta t_n \\sum_{i=1}^{n-1} \\Delta A_p
                + \\Delta t_n \\bar{t}_n \\sum_{i=1}^{n-1} \\frac{\\Delta A_p}{\\bar{r}_p})

        A & = 2 \\Delta V_p / r_p

    Where :
        - :math:`\\Delta A_p` is the area of the pores
        - :math:`\\Delta V_p` is the adsorbed volume change between two points
        - :math:`\\bar{r}_p` is the average pore radius calculated as a sum of the
          kelvin radius and layer thickness of the pores at pressure p between two
          measurement points
        - :math:`\\bar{r}_k` is the average kelvin radius between two measurement points
        - :math:`\\bar{t}_n` is the average layer thickness between two measurement points
        - :math:`\\Delta t_n` is the average change in layer thickness between two measurement points

    Then, by plotting :math:`\\Delta V / (2*\\Delta r_p)` versus the width of the pores calculated
    for each point, the pore size distribution can be obtained.

    References
    ----------
    .. [#] “The Determination of Pore Volume and Area Distributions in Porous Substances.
       I. Computations from Nitrogen Isotherms”, Elliott P. Barrett, Leslie G. Joyner and
       Paul P. Halenda, J. Amer. Chem. Soc., 73, 373 (1951)

    .. [#] "Adsorption by Powders & Porous Solids", F. Roquerol, J Roquerol
       and K. Sing, Academic Press, 1999
    """
    # Parameter checks
    if len(pressure) != len(loading):
        raise ParameterError("The length of the pressure and loading arrays"
                             " do not match")

    if pore_geometry == 'slit':
        raise NotImplementedError
    elif pore_geometry == 'cylinder':
        pass
    elif pore_geometry == 'sphere':
        raise NotImplementedError

    # Calculate the adsorbed volume of liquid and diff
    volume_adsorbed = loading * adsorbate_molar_mass / liquid_density * 1000
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
                       liquid_density, adsorbate_molar_mass):
    """
    Calculates the pore size distribution using the Dollimore-Heal method.

    Parameters
    ----------
    loading : array
        Adsorbed amount in mmol/g.
    pressure : array
        Relative pressure.
    pore_geometry : str
        The geometry of the pore, eg. 'sphere', 'cylinder' or 'slit'.
    thickness_model : callable
        Function which returns the thickness of the adsorbed layer
        at a pressure p.
    condensation_model : callable
        Function which returns the critical kelvin radius at a pressure p.
    liquid_density : float
        Density of the adsorbate in the adsorbed state, in g/cm3.
    adsorbate_molar_mass : float
        Molar mass of the adsorbate in g/mol.

    Returns
    -------
    pore widths : array
        Widths of the pores.
    pore_dist : array
        Amount of each pore width.

    Notes
    -----
    *Description*

    The DH or Dollimore-Heal method [#]_ of calculation of pore size distribution is an
    extension of the BJH method, which takes into account the geometry of the pores
    by introducing a length component.

    Like the BJH method, it is based on a classical description of the adsorbate behaviour
    in the adsorbent pores. Under this method, the adsorbate is adsorbing on the pore walls
    in a predictable way, and decreasing the apparent pore volume until condensation takes
    place, filling the entire pore. The two variables, layer thickness and radius where
    condensation takes place can be modelled by a thickness model (such as Halsey, Harkins
    & Jura, etc.) and a critical radius model for condensation/evaporation, based
    on a form of the Kelvin equation.

    .. math::

        r_p = t + r_k

    The original model used the desorption curve as a basis for calculating pore size distribution.
    Between two points of the curve, the volume desorbed can be described as the volume contribution
    from pore evaporation and the volume from layer thickness decrease as per the equation
    above. The computation is done cumulatively, starting from the filled pores and calculating for each
    point the volume adsorbed in a pore from the following equation:

    .. math::

        V_p & = \\Big(\\frac{\\bar{r}_p}{\\bar{r}_k + \\Delta t_n}\\Big)^2
                (\\Delta V_n - \\Delta t_n \\sum_{i=1}^{n-1} \\Delta A_p
                + 2 \\pi \\Delta t_n \\bar{t}_n \\sum_{i=1}^{n-1} L_p)

        A & = 2 \\Delta V_p / r_p

        L & = \\Delta A_p / 2 \\pi r_p

    Where :
        - :math:`\\Delta A_p` is the area of the pores
        - :math:`\\Delta V_p` is the adsorbed volume change between two points
        - :math:`\\bar{r}_p` is the average pore radius calculated as a sum of the
          kelvin radius and layer thickness of the pores at pressure p between two
          measurement points
        - :math:`\\bar{r}_k` is the average kelvin radius between two measurement points
        - :math:`\\bar{t}_n` is the average layer thickness between two measurement points
        - :math:`\\Delta t_n` is the average change in layer thickness between two measurement points

    Then, by plotting :math:`\\Delta V/(2*\\Delta r_p)` versus the width of the pores calculated
    for each point, the pore size distribution can be obtained.

    References
    ----------
    .. [#] D. Dollimore and G. R. Heal, J. Applied Chem. 14, 109 (1964);
       J. Colloid Interface Sci. 33, 508 (1970)
    """
    # Checks
    if len(pressure) != len(loading):
        raise ParameterError("The length of the pressure and loading arrays"
                             " do not match")

    if pore_geometry == 'slit':
        raise NotImplementedError
    if pore_geometry == 'cylinder':
        pass
    if pore_geometry == 'sphere':
        raise NotImplementedError

    # Calculate the adsorbed volume of liquid and diff
    volume_adsorbed = loading * adsorbate_molar_mass / liquid_density * 1000
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
