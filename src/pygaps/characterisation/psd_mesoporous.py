"""
Methods of calculating a pore size distribution for pores in the mesopore range
(2-100 nm), based on the Kelvin equation and pore condensation/evaporation.
"""

import numpy

from ..core.adsorbate import Adsorbate
from ..graphing.calc_graphs import psd_plot
from ..utilities.exceptions import CalculationError
from ..utilities.exceptions import ParameterError
from ..utilities.exceptions import pgError
from .models_kelvin import get_kelvin_model
from .models_kelvin import get_meniscus_geometry
from .models_thickness import get_thickness_model

_MESO_PSD_MODELS = ['pygaps-DH', 'BJH', 'DH']
_PORE_GEOMETRIES = ['slit', 'cylinder', 'sphere']


def psd_mesoporous(
    isotherm,
    psd_model='pygaps-DH',
    pore_geometry='cylinder',
    branch='des',
    thickness_model='Harkins/Jura',
    kelvin_model='Kelvin',
    p_limits=None,
    verbose=False
):
    r"""
    Calculate the mesopore size distribution.

    Uses methods based on the Kelvin equation and capillary condensation.

    Parameters
    ----------
    isotherm : Isotherm
        Isotherm for which the pore size distribution will be calculated.
    psd_model : str
        The pore size distribution model to use.
    pore_geometry : str
        The geometry of the adsorbent pores.
    branch : {'ads', 'des'}, optional
        Branch of the isotherm to use. It defaults to desorption.
    kelvin_model : callable, optional
        A custom user kelvin model. It should be a callable that only takes
        relative pressure as an argument.
    thickness_model : str or callable, optional
        The thickness model to use for PSD, It defaults to Harkins and Jura.
    p_limits : [float, float]
        Pressure range in which to calculate PSD, defaults to entire isotherm.
    verbose : bool
        Prints out extra information on the calculation and graphs the results.

    Returns
    -------
    dict
        A dictionary with the pore widths and the pore distributions, of the form:

            - ``pore_widths`` (array) : the widths of the pores
            - ``pore_distribution`` (array) : contribution of each pore width to the
              overall pore distribution

    Notes
    -----
    Calculates the pore size distribution using a 'classical' model which attempts to
    describe the adsorption in a pore as a combination of a statistical thickness and
    a condensation/evaporation behaviour described by surface tension.
    It is based on solving the following equation:

    .. math::

        \Delta V_n = R V_p + \Delta t \sum_{i=1}^{n-1} A_i

    Which states that the volume adsorbed or desorbed during an isotherm step
    is a sum of the capillary condensation / evaporation volume, expressed as a
    function of the total pore volume, and the volume of the thickness increase
    or decrease in a pore.

    Currently, the methods provided are:

        - the pygaps-DH model, an expanded DH model for multiple geometries
        - the original BJH or Barrett, Joyner and Halenda method
        - the original DH or Dollimore-Heal method, an extension of the BJH method

    According to Rouquerol [#]_, in adopting this approach, it is assumed that:

        - The Kelvin equation is applicable over the pore range (mesopores). Therefore
          in pores which are below a certain size (around 2.5 nm), the granularity
          of the liquid-vapour interface becomes too large for classical bulk methods
          to be applied.
        - The meniscus curvature is controlled be the pore size and shape. Ideal shapes
          for the curvature are assumed.
        - The pores are rigid and of well defined shape. They are considered
          open-ended and non-intersecting
        - The filling/emptying of each pore does not depend on its location.
        - The adsorption on the pore walls is not different from surface adsorption.

    .. caution::

        A common mantra of data processing is: **garbage in = garbage out**. Only use
        methods when you are aware of their limitations and shortcomings.

    References
    ----------
    .. [#] "Adsorption by Powders & Porous Solids", F. Rouquerol, J Rouquerol
       and K. Sing, Academic Press, 1999

    See Also
    --------
    pygaps.characterisation.psd_mesoporous.psd_pygapsdh : the pygaps-DH method
    pygaps.characterisation.psd_mesoporous.psd_bjh : the BJH or Barrett, Joyner and Halenda method
    pygaps.characterisation.psd_mesoporous.psd_dollimore_heal : the DH or Dollimore-Heal method

    """
    # Function parameter checks
    if psd_model is None:
        raise ParameterError(
            "Specify a model to generate the pore size"
            " distribution e.g. psd_model=\"BJH\""
        )
    if psd_model not in _MESO_PSD_MODELS:
        raise ParameterError(
            f"Model {psd_model} not an option for psd.",
            f" Available models are {_MESO_PSD_MODELS}"
        )
    if pore_geometry not in _PORE_GEOMETRIES:
        raise ParameterError(
            f"Geometry {pore_geometry} not an option for pore size distribution. ",
            f"Available geometries are {_PORE_GEOMETRIES}"
        )
    if branch not in ['ads', 'des']:
        raise ParameterError(
            f"Branch '{branch}' not an option for PSD.",
            "Select either 'ads' or 'des'"
        )
    if not isinstance(isotherm.adsorbate, Adsorbate):
        raise ParameterError(
            "Isotherm adsorbate is not known, cannot calculate PSD."
        )

    # Get required adsorbate properties
    molar_mass = isotherm.adsorbate.molar_mass()
    liquid_density = isotherm.adsorbate.liquid_density(isotherm.temperature)
    surface_tension = isotherm.adsorbate.surface_tension(isotherm.temperature)

    # Read data in, depending on branch requested
    loading = isotherm.loading(
        branch=branch, loading_basis='molar', loading_unit='mmol'
    )
    if loading is None:
        raise ParameterError(
            "The isotherm does not have the required branch for this calculation"
        )
    try:
        pressure = isotherm.pressure(branch=branch, pressure_mode='relative')
    except pgError:
        raise CalculationError(
            "The isotherm cannot be converted to a relative basis. "
            "Is your isotherm supercritical?"
        )
    # If on an adsorption branch, data will be reversed
    if branch == 'ads':
        loading = loading[::-1]
        pressure = pressure[::-1]

    # Determine the limits
    if not p_limits:
        p_limits = (None, None)
    minimum = 0
    maximum = len(pressure)
    if p_limits[0]:
        minimum = numpy.searchsorted(pressure, p_limits[0])
    if p_limits[1]:
        maximum = numpy.searchsorted(pressure, p_limits[1])
    if maximum - minimum < 3:  # (for 3 point minimum)
        raise CalculationError(
            "The isotherm does not have enough points (at least 3) "
            "in the selected region."
        )
    pressure = pressure[minimum:maximum]
    loading = loading[minimum:maximum]

    # calculated volume adsorbed
    volume_adsorbed = loading * molar_mass / liquid_density / 1000

    # Thickness model definitions
    t_model = get_thickness_model(thickness_model)

    # Kelvin model definitions
    k_model_args = {
        "meniscus_geometry": get_meniscus_geometry(branch, pore_geometry),
        "temperature": isotherm.temperature,
        "liquid_density": liquid_density,
        "adsorbate_molar_mass": molar_mass,
        "adsorbate_surface_tension": surface_tension
    }
    k_model = get_kelvin_model(kelvin_model, **k_model_args)

    # Call specified pore size distribution function
    if psd_model == 'pygaps-DH':
        pore_widths, pore_dist, pore_vol_cum = psd_pygapsdh(
            volume_adsorbed, pressure, pore_geometry, t_model, k_model
        )
    elif psd_model == 'BJH':
        pore_widths, pore_dist, pore_vol_cum = psd_bjh(
            volume_adsorbed, pressure, pore_geometry, t_model, k_model
        )
    elif psd_model == 'DH':
        pore_widths, pore_dist, pore_vol_cum = psd_dollimore_heal(
            volume_adsorbed, pressure, pore_geometry, t_model, k_model
        )

    # Plot if verbose
    if verbose:
        psd_plot(
            pore_widths,
            pore_dist,
            pore_vol_cum=pore_vol_cum,
            method=psd_model,
            left=1.5
        )

    return {
        'pore_widths': pore_widths,
        'pore_distribution': pore_dist,
        'pore_volume_cumulative': pore_vol_cum,
    }


def psd_pygapsdh(
    volume_adsorbed, relative_pressure, pore_geometry, thickness_model,
    condensation_model
):
    r"""
    Calculate a pore size distribution using an expanded Dollimore-Heal method.

    Parameters
    ----------
    volume_adsorbed : array
        Volume adsorbed of "liquid" phase in cm3.
    relative_pressure : array
        Relative pressure.
    pore_geometry : str
        The geometry of the pore, eg. 'sphere', 'cylinder' or 'slit'.
    thickness_model : callable
        Function which returns the thickness of the adsorbed layer
        at a pressure p.
    condensation_model : callable
        Function which returns the critical kelvin radius at a pressure p.

    Returns
    -------
    pore widths : array
        Widths of the pores.
    pore_dist : array
        Amount of each pore width.
    pore_vol_cum : array
        Cumulative pore volume.

    Notes
    -----
    This method is an extended DH method which is applicable to multiple pore
    geometries (slit, cylinder, spherical).

    The calculation is performed in terms of the characteristic dimension of the
    pore geometry: width for slits, diameter for cylinders and spheres. The
    characteristic dimension is calculated in terms of the Kelvin radius and
    adsorbed layer thickness:

    .. math::

        w_{p} = 2 r_k + 2 t

    The Kelvin radius and layer thickness are calculated based on the
    functions provided, no assessment of the meniscus shape or thickness is
    performed here.

    The basic equation for all geometries is as follows:

    .. math::

        V_p = \Big(\Delta V_n - \Delta t_n \sum_{i=1}^{n-1}
                \Big(\frac{\bar{w}_{p,i} - 2 t_{n,i}}{\bar{w}_{p,i}}\Big)^{(l-1)}
                \frac{2 l \Delta V_{p,i}}{w_{p,i}}\Big)
                \Big(\frac{\bar{w}_p}{\bar{w}_p - 2 t_n}\Big)^l

    Where :
        - :math:`V_p` is the volume of pores of size :math:`\bar{r}_p`
        - :math:`\Delta V_n` is the adsorbed volume change between two points
        - :math:`\bar{r}_p` is the average pore radius calculated as a sum of the
          kelvin radius and layer thickness of the pores at pressure p between two
          measurement points
        - :math:`\bar{r}_k` is the average kelvin radius between two measurement points
        - :math:`t_n` is the layer thickness at point n
        - :math:`\bar{t}_n` is the average layer thickness between two measurement points
        - :math:`\Delta t_n` is the change in layer thickness between two measurement points
        - :math:`l` is a characteristic dimension of the system

    In order to account for different geometries, factors are calculated in
    terms of a characteristic number of the system:

        - In a slit pore, the relationship between pore volume and pore surface
          is :math:`A_p = 2 V_p / w_p`. The pore area stays the same throughout
          any changes in layer thickness, therefore no correction factor is applied.
          Finally, the relationship between the volume of the kelvin capillary and the
          total pore width is :math:`\frac{\bar{w}_{p,i}}{\bar{w}_{p,i} - 2 t_{n,i}}`.

        - In a cylindrical pore, the relationship between pore volume and pore surface
          is :math:`A_p = 4 V_p / w_p`. The ratio between average pore area at a point
          and total pore area can be expressed by using
          :math:`\frac{\bar{w}_{p,i} - 2 t_{n,i}}{\bar{w}_{p,i}}`.
          Finally, the relationship between the inner Kelvin capillary and the
          total pore diameter is :math:`\frac{\bar{w}_{p,i}}{\bar{w}_{p,i} - 2 t_{n,i}}^2`.

        - In a spherical pore, the relationship between pore volume and pore surface
          is :math:`A_p = 6 V_p / w_p`. The ratio between average pore area at a point
          and total pore area can be expressed by using
          :math:`\frac{\bar{w}_{p,i} - 2 t_{n,i}}{\bar{w}_{p,i}}^2`.
          Finally, the relationship between the inner Kelvin sphere and the
          total pore diameter is :math:`\frac{\bar{w}_{p,i}}{\bar{w}_{p,i} - 2 t_{n,i}}^3`.


    References
    ----------
    .. [#] "Adsorption by Powders & Porous Solids", F. Rouquerol, J Rouquerol
       and K. Sing, Academic Press, 1999

    """
    # Checks
    if len(volume_adsorbed) != len(relative_pressure):
        raise ParameterError(
            "The length of the pressure and loading arrays do not match"
        )

    # Pore geometry specifics
    if pore_geometry == 'slit':
        c_length = 1

    elif pore_geometry == 'cylinder':
        c_length = 2

    elif pore_geometry == 'sphere':
        c_length = 3

    # Calculate the adsorbed volume of liquid and diff
    d_volume = numpy.negative(numpy.diff(volume_adsorbed))

    # Generate the thickness curve, average and diff
    thickness = thickness_model(relative_pressure)
    avg_thickness = numpy.add(thickness[:-1], thickness[1:]) / 2
    d_thickness = numpy.negative(numpy.diff(thickness))

    # Generate the Kelvin pore radii and average
    kelvin_radius = condensation_model(relative_pressure)

    # Critical pore radii as a combination of the adsorbed
    # layer thickness and kelvin pore radius, with average and diff
    pore_widths = 2 * numpy.add(thickness, kelvin_radius)
    avg_pore_widths = numpy.add(pore_widths[:-1], pore_widths[1:]) / 2
    d_pore_widths = numpy.negative(numpy.diff(pore_widths))

    # Now we can iteratively calculate the pore size distribution
    sum_area_factor = 0
    pore_volumes = []

    for i in range(len(avg_pore_widths)):

        # Calculate the ratio of the pore to the evaporated capillary "core"
        ratio_factor = (
            avg_pore_widths[i] / (avg_pore_widths[i] - 2 * thickness[i])
        )**c_length

        # Calculate the volume desorbed from thinning of all pores previously emptied
        thickness_factor = -d_thickness[i] * sum_area_factor

        # Equation for pore volume, then add to the array
        pore_volume = (d_volume[i] + thickness_factor) * ratio_factor
        pore_volumes.append(pore_volume)

        # Calculate the area of the newly emptied pore then add it to the total pore area
        pore_area_correction = ((avg_pore_widths[i] - 2 * avg_thickness[i]) /
                                avg_pore_widths[i])**(c_length - 1)
        pore_avg_area = 2 * c_length * pore_volume / avg_pore_widths[i]
        sum_area_factor += pore_area_correction * pore_avg_area

    pore_dist = pore_volumes / d_pore_widths

    return pore_widths[:0:-1], pore_dist[::-1], numpy.cumsum(
        pore_volumes[::-1]
    )


def psd_bjh(
    volume_adsorbed, relative_pressure, pore_geometry, thickness_model,
    condensation_model
):
    r"""
    Calculate a pore size distribution using the BJH method.

    Parameters
    ----------
    volume_adsorbed : array
        Volume adsorbed of "liquid" phase in cm3.
    relative_pressure : array
        Relative pressure.
    pore_geometry : str
        The geometry of the pore, eg. 'sphere', 'cylinder' or 'slit'.
    thickness_model : callable
        Function which returns the thickness of the adsorbed layer
        at a pressure p.
    condensation_model : callable
        Function which returns the critical kelvin radius at a pressure p.

    Returns
    -------
    pore widths : array
        Widths of the pores.
    pore_dist : array
        Amount of each pore width.
    pore_vol_cum : array
        Cumulative pore volume.

    Notes
    -----
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

        V_p = \Big(\Delta V_n - \Delta t_n \sum_{i=1}^{n-1}
                \Big(\frac{\bar{r}_{p,i} - t_{n,i}}{\bar{r}_{p,i}}\Big) \frac{2 \Delta V_{p,i}}{r_{p,i}}\Big)
                \Big(\frac{\bar{r}_p}{\bar{r}_k + \Delta t_n}\Big)^2

    Where :
        - :math:`V_p` is the volume of pores of size :math:`\bar{r}_p`
        - :math:`\Delta V_n` is the adsorbed volume change between two points
        - :math:`\bar{r}_p` is the average pore radius calculated as a sum of the
          kelvin radius and layer thickness of the pores at pressure p between two
          measurement points
        - :math:`\bar{r}_k` is the average kelvin radius between two measurement points
        - :math:`t_n` is the layer thickness at point n
        - :math:`\bar{t}_n` is the average layer thickness between two measurement points
        - :math:`\Delta t_n` is the change in layer thickness between two measurement points

    Then, by plotting :math:`V_p / (2 \Delta r_p)` versus the width of the pores calculated
    for each point, the pore size distribution can be obtained.

    The code in this function is an accurate implementation of the original BJH method.

    References
    ----------
    .. [#] "The Determination of Pore Volume and Area Distributions in Porous Substances.
       I. Computations from Nitrogen Isotherms", Elliott P. Barrett, Leslie G. Joyner and
       Paul P. Halenda, J. Amer. Chem. Soc., 73, 373 (1951)

    .. [#] "Adsorption by Powders & Porous Solids", F. Rouquerol, J Rouquerol
       and K. Sing, Academic Press, 1999

    """
    # Parameter checks
    if len(volume_adsorbed) != len(relative_pressure):
        raise ParameterError(
            "The length of the pressure and loading arrays"
            " do not match"
        )

    if pore_geometry in ('slit', 'sphere'):
        raise ParameterError(
            "The BJH method is provided for compatibility and only applicable"
            " to cylindrical pores. Use the pyGAPS-DH method for other options."
        )

    # Calculate the adsorbed volume of liquid and diff
    d_volume = numpy.negative(numpy.diff(volume_adsorbed))

    # Generate the thickness curve, average and diff
    thickness = thickness_model(relative_pressure)
    avg_thickness = numpy.add(thickness[:-1], thickness[1:]) / 2
    d_thickness = numpy.negative(numpy.diff(thickness))

    # Generate the Kelvin pore radii and average
    kelvin_radius = condensation_model(relative_pressure)
    avg_k_radius = numpy.add(kelvin_radius[:-1], kelvin_radius[1:]) / 2

    # Critical pore radii as a combination of the adsorbed
    # layer thickness and kelvin pore radius, with average and diff
    pore_widths = 2 * numpy.add(thickness, kelvin_radius)
    avg_pore_widths = 2 * numpy.add(avg_thickness, avg_k_radius)
    d_pore_widths = numpy.negative(numpy.diff(pore_widths))

    # Now we can iteratively calculate the pore size distribution
    sum_area_factor = 0
    pore_volumes = []

    for i in range(len(avg_pore_widths)):

        # Calculate the ratio of the pore to the evaporated capillary "core"
        ratio_factor = (
            avg_pore_widths[i] / (2 * (avg_k_radius[i] + d_thickness[i]))
        )**2

        # Calculate the volume desorbed from thinning of all pores previously emptied
        thickness_factor = -d_thickness[i] * sum_area_factor

        # Equation for pore volume, then add to the array
        pore_volume = (d_volume[i] + thickness_factor) * ratio_factor
        pore_volumes.append(pore_volume)

        # Calculate the area of the newly emptied pore then add it to the total pore area
        pore_area_correction = (avg_pore_widths[i] -
                                2 * avg_thickness[i]) / avg_pore_widths[i]
        pore_avg_area = (4 * pore_volume / avg_pore_widths[i])
        sum_area_factor += pore_area_correction * pore_avg_area

    pore_dist = pore_volumes / d_pore_widths

    return pore_widths[:0:-1], pore_dist[::-1], numpy.cumsum(
        pore_volumes[::-1]
    )


def psd_dollimore_heal(
    volume_adsorbed, relative_pressure, pore_geometry, thickness_model,
    condensation_model
):
    r"""
    Calculate a pore size distribution using the Dollimore-Heal method.

    Parameters
    ----------
    volume_adsorbed : array
        Volume adsorbed of "liquid" phase in cm3.
    relative_pressure : array
        Relative pressure.
    pore_geometry : str
        The geometry of the pore, eg. 'sphere', 'cylinder' or 'slit'.
    thickness_model : callable
        Function which returns the thickness of the adsorbed layer
        at a pressure p.
    condensation_model : callable
        Function which returns the critical kelvin radius at a pressure p.

    Returns
    -------
    pore widths : array
        Widths of the pores.
    pore_dist : array
        Amount of each pore width.
    pore_vol_cum : array
        Cumulative pore volume.

    Notes
    -----
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
    above. The computation is done cumulatively, starting from the filled pores and calculating for
    each point the volume adsorbed in a pore from the following equation:

    .. math::

        V_p = \Big(\Delta V_n - \Delta t_n \sum_{i=1}^{n-1} \frac{2 \Delta V_{p,i}}{r_{p,i}}
                + \Delta t_n \bar{t}_n \sum_{i=1}^{n-1} \frac{2 \Delta V_{p,i}}{r_{p,i}^2}
                \Big)\Big(\frac{\bar{r}_p}{\bar{r}_p - t_n}\Big)^2

    Where :
        - :math:`V_p` is the volume of pores of size :math:`\bar{r}_p`
        - :math:`\Delta V_n` is the adsorbed volume change between two points
        - :math:`\bar{r}_p` is the average pore radius calculated as a sum of the
          kelvin radius and layer thickness of the pores at pressure p between two
          measurement points
        - :math:`t_n` is the layer thickness at point n
        - :math:`\bar{t}_n` is the average layer thickness between two measurement points
        - :math:`\Delta t_n` is the change in layer thickness between two measurement points

    Then, by plotting :math:`V_p/(2*\Delta r_p)` versus the width of the pores calculated
    for each point, the pore size distribution can be obtained.

    The code in this function is an accurate implementation of the original DH method.

    References
    ----------
    .. [#] D. Dollimore and G. R. Heal, J. Applied Chem. 14, 109 (1964);
       J. Colloid Interface Sci. 33, 508 (1970)

    """
    # Checks
    if len(volume_adsorbed) != len(relative_pressure):
        raise ParameterError(
            "The length of the pressure and loading arrays"
            " do not match"
        )

    if pore_geometry in ('slit', 'sphere'):
        raise ParameterError(
            "The DH method is provided for compatibility and only applicable"
            " to cylindrical pores. Use the pyGAPS-DH method for other options."
        )

    # Calculate the first differential of volume adsorbed
    d_volume = numpy.negative(numpy.diff(volume_adsorbed))

    # Generate the thickness curve, average and diff
    thickness = thickness_model(relative_pressure)
    avg_thickness = numpy.add(thickness[:-1], thickness[1:]) / 2
    d_thickness = numpy.negative(numpy.diff(thickness))

    # Generate the Kelvin pore radii and average
    kelvin_radius = condensation_model(relative_pressure)
    avg_k_radius = numpy.add(kelvin_radius[:-1], kelvin_radius[1:]) / 2

    # Critical pore radii as a combination of the adsorbed
    # layer thickness and kelvin pore radius, with average and diff
    pore_widths = 2 * numpy.add(thickness, kelvin_radius)
    avg_pore_widths = 2 * numpy.add(avg_thickness, avg_k_radius)
    d_pore_widths = numpy.negative(numpy.diff(pore_widths))

    # Now we can iteratively calculate the pore size distribution
    sum_area_factor = 0
    sum_length_factor = 0
    pore_volumes = []

    for i in range(len(d_pore_widths)):

        # Calculate the ratio of the pore to the evaporated capillary "core"
        ratio_factor = (
            avg_pore_widths[i] / (avg_pore_widths[i] - 2 * thickness[i])
        )**2

        # Calculate the volume desorbed from thinning of all pores previously emptied
        thickness_factor = - d_thickness[i] * sum_area_factor + \
            d_thickness[i] * avg_thickness[i] * sum_length_factor

        # Equation for pore volume, then add to the array
        pore_volume = (d_volume[i] + thickness_factor) * ratio_factor
        pore_volumes.append(pore_volume)

        # Calculate the two factors in the DH method, for area and length
        pore_avg_area = (4 * pore_volume / avg_pore_widths[i])
        pore_avg_length = (8 * pore_volume / avg_pore_widths[i]**2)
        sum_area_factor += pore_avg_area
        sum_length_factor += pore_avg_length

    pore_dist = pore_volumes / d_pore_widths

    return pore_widths[:0:-1], pore_dist[::-1], numpy.cumsum(
        pore_volumes[::-1]
    )
