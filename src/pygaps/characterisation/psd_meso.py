"""
Methods of calculating a pore size distribution for pores in the mesopore range
(2-100 nm), based on the Kelvin equation and pore condensation/evaporation.
"""
import typing as t

import numpy

from pygaps import logger
from pygaps.characterisation.models_kelvin import get_kelvin_model
from pygaps.characterisation.models_kelvin import get_meniscus_geometry
from pygaps.characterisation.models_thickness import get_thickness_model
from pygaps.core.adsorbate import Adsorbate
from pygaps.core.modelisotherm import ModelIsotherm
from pygaps.core.pointisotherm import PointIsotherm
from pygaps.utilities.exceptions import CalculationError
from pygaps.utilities.exceptions import ParameterError
from pygaps.utilities.exceptions import pgError

_MESO_PSD_MODELS = ['pygaps-DH', 'BJH', 'DH']
_PORE_GEOMETRIES = ['slit', 'cylinder', 'halfopen-cylinder', 'sphere']
_MENISCUS_GEOMETRIES = ["hemicylindrical", "cylindrical", "hemispherical"]


def psd_mesoporous(
    isotherm: "PointIsotherm | ModelIsotherm",
    psd_model: str = 'pygaps-DH',
    pore_geometry: str = 'cylinder',
    meniscus_geometry: str = None,
    branch: str = 'des',
    thickness_model:
    "str | PointIsotherm | ModelIsotherm | t.Callable[[float], float]" = 'Harkins/Jura',
    kelvin_model: "str | t.Callable[[float], float]" = 'Kelvin',
    p_limits: "tuple[float, float]" = None,
    verbose: bool = False
):
    r"""
    Calculate the mesopore size distribution using a Kelvin-type model.

    Expected pore geometry must be specified as ``pore_geometry``.
    If the meniscus (adsorbed/gas interface) geometry is known, it
    can be equally specified, otherwise it will be inferred from the
    pore geometry.

    The ``thickness_model`` parameter is a string which names the thickness
    equation which should be used. Alternatively, a user can implement their own
    thickness model, either as an Isotherm or a function which describes the
    adsorbed layer. In that case, instead of a string, pass the Isotherm object
    or the callable function as the ``thickness_model`` parameter.

    Parameters
    ----------
    isotherm : PointIsotherm, ModelIsotherm
        Isotherm for which the pore size distribution will be calculated.
    psd_model : str
        The pore size distribution model to use.
    pore_geometry : str
        The geometry of the meniscus (adsorbed/gas interface) in the pores.
    meniscus_geometry : str, optional
        The geometry of the adsorbent pores.
    branch : {'ads', 'des'}, optional
        Branch of the isotherm to use. It defaults to desorption.
    thickness_model : str, callable, optional
        The thickness model to use for PSD, It defaults to ``Harkins/Jura``.
    kelvin_model : str, callable, optional
        A custom user kelvin model. It should be a callable that only takes
        relative pressure as an argument.
    p_limits : tuple[float, float]
        Pressure range in which to calculate PSD, defaults to (0.1, 0.99).
    verbose : bool
        Prints out extra information on the calculation and graphs the results.

    Returns
    -------
    dict
        A dictionary of results of the form:

        - ``pore_widths`` (ndarray) : the widths (or diameter) of the pores, nm
        - ``pore_volumes`` (ndarray) : pore volume for each pore width, cm3/material
        - ``pore_volume_cumulative`` (ndarray) : cumulative sum of pore volumes, in cm3/material
        - ``pore_distribution`` (ndarray) : contribution of each pore width to the
          overall pore distribution, cm3/material/nm
        - ``pore_areas`` (ndarray) : specific area for each pore width, m2/material
        - ``pore_area_total`` (float) : total specific area, m2/material
        - ``limits`` (tuple[int, int]) : indices of selection limits

    Raises
    ------
    ParameterError
        When something is wrong with the function parameters.
    CalculationError
        When the calculation itself fails.

    Notes
    -----
    Calculates the pore size distribution using a 'classical' model which attempts to
    describe the adsorption in a pore as a combination of a statistical thickness and
    a condensation/evaporation behaviour related to adsorbate surface tension.
    It is based on solving the following equation:

    .. math::

        \Delta V_n = V_{k,n} + V_{t,n}

    Which states that the volume adsorbed or desorbed during a pressure step,
    :math:`\Delta V_n`, can be described as a sum of the volume involved in
    capillary condensation / evaporation (:math:`\Delta V_{k,n}`), and the
    volume corresponding to the increase / decrease of the adsorbed layer
    thickness in the surface of all non-filled pores (:math:`\Delta V_{t,n}`).

    Expressions are derived for the pore volume as a function of pore geometry,
    the shape of the liquid-gas interface (meniscus), relationship between
    pore width and critical condensation width (:math:`R_{p}`), rearranging
    the equation to:

    .. math::

        V_{p,n} = (\Delta V_n - V_{t,n}) R_p

    Currently, the methods provided are:

    - the pygaps-DH model, a custom expanded DH model for multiple pore geometries
    - the original BJH or Barrett, Joyner and Halenda method
    - the original DH or Dollimore-Heal method

    According to Rouquerol [#]_, in adopting this approach, it is assumed that:

    - The Kelvin equation is applicable over the pore range (mesopores).
      In pores which are below a certain size (around 2.5 nm), the
      granularity of the liquid-vapour interface becomes too large the method
      to hold.
    - The meniscus curvature is controlled be the pore size and shape. Ideal
      shapes for the curvature are assumed.
    - The pores are rigid and of well defined shape. They are considered
      open-ended and non-intersecting.
    - The filling/emptying of each pore does not depend on its location,
      i.e. no diffusion or blocking effects.
    - Adsorption on the pore walls is not different from surface adsorption.

    .. caution::

        A common mantra of data processing is: **garbage in = garbage out**. Only use
        methods when you are aware of their limitations and shortcomings.

    References
    ----------
    .. [#] "Adsorption by Powders & Porous Solids", F. Rouquerol, J Rouquerol
       and K. Sing, Academic Press, 1999

    See Also
    --------
    pygaps.characterisation.psd_meso.psd_pygapsdh : low-level pygaps-DH method
    pygaps.characterisation.psd_meso.psd_bjh : low-level BJH or Barrett, Joyner and Halenda method
    pygaps.characterisation.psd_meso.psd_dollimore_heal : low-level DH or Dollimore-Heal method

    """
    # Function parameter checks
    if psd_model is None:
        raise ParameterError(
            "Specify a model to generate the pore size"
            " distribution e.g. psd_model=\"BJH\""
        )
    if psd_model not in _MESO_PSD_MODELS:
        raise ParameterError(
            f"Model {psd_model} not an option for psd.", f" Available models are {_MESO_PSD_MODELS}"
        )
    if pore_geometry not in _PORE_GEOMETRIES:
        raise ParameterError(
            f"Geometry {pore_geometry} not an option for pore size distribution. "
            f"Available geometries are {_PORE_GEOMETRIES}"
        )
    if meniscus_geometry and meniscus_geometry not in _MENISCUS_GEOMETRIES:
        raise ParameterError(
            f"Meniscus geometry {meniscus_geometry} not an option for pore size distribution. "
            f"Available geometries are {_MENISCUS_GEOMETRIES}"
        )
    if branch not in ['ads', 'des']:
        raise ParameterError(
            f"Branch '{branch}' not an option for PSD.", "Select either 'ads' or 'des'"
        )
    if not isinstance(isotherm.adsorbate, Adsorbate):
        raise ParameterError("Isotherm adsorbate is not known, cannot calculate PSD.")

    # Get required adsorbate properties
    molar_mass = isotherm.adsorbate.molar_mass()
    liquid_density = isotherm.adsorbate.liquid_density(isotherm.temperature)
    surface_tension = isotherm.adsorbate.surface_tension(isotherm.temperature)

    # Read data in, depending on branch requested
    volume_adsorbed = isotherm.loading(
        branch=branch,
        loading_basis='volume_liquid',
        loading_unit='cm3',
    )
    if volume_adsorbed is None:
        raise ParameterError("The isotherm does not have the required branch for this calculation")
    try:
        pressure = isotherm.pressure(
            branch=branch,
            pressure_mode='relative',
        )
    except pgError as err:
        raise CalculationError(
            "The isotherm cannot be converted to a relative basis. "
            "Is your isotherm supercritical?"
        ) from err

    # If on an desorption branch, data will be reversed
    if branch == 'des':
        pressure = pressure[::-1]
        volume_adsorbed = volume_adsorbed[::-1]

    # select the maximum and minimum of the points and the pressure associated
    minimum = 0
    maximum = len(pressure) - 1  # As we want absolute position

    # Set default values
    if p_limits is None:
        p_limits = (0.1, 0.99)

    if p_limits[0]:
        minimum = numpy.searchsorted(pressure, p_limits[0])
    if p_limits[1]:
        maximum = numpy.searchsorted(pressure, p_limits[1]) - 1
    if maximum - minimum < 2:  # (for 3 point minimum)
        raise CalculationError(
            "The isotherm does not have enough points (at least 3) "
            "in the selected region."
        )
    pressure = pressure[minimum:maximum + 1]
    volume_adsorbed = volume_adsorbed[minimum:maximum + 1]

    # Thickness model
    t_model = get_thickness_model(thickness_model)

    # Kelvin model
    if not meniscus_geometry:
        meniscus_geometry = get_meniscus_geometry(branch, pore_geometry)
    k_model = get_kelvin_model(
        kelvin_model,
        meniscus_geometry=meniscus_geometry,
        temperature=isotherm.temperature,
        liquid_density=liquid_density,
        adsorbate_molar_mass=molar_mass,
        adsorbate_surface_tension=surface_tension
    )

    # Call specified pore size distribution function
    if psd_model == 'pygaps-DH':
        results = psd_pygapsdh(volume_adsorbed, pressure, pore_geometry, t_model, k_model)
    elif psd_model == 'BJH':
        results = psd_bjh(volume_adsorbed, pressure, pore_geometry, t_model, k_model)
    elif psd_model == 'DH':
        results = psd_dollimore_heal(volume_adsorbed, pressure, pore_geometry, t_model, k_model)

    results['pore_volume_cumulative'] = numpy.cumsum(results['pore_volumes'])
    results['pore_volume_cumulative'] = (
        results['pore_volume_cumulative'] - results['pore_volume_cumulative'][-1] +
        volume_adsorbed[-1]
    )
    results['limits'] = (minimum, maximum)
    results['pore_area_total'] = sum(results['pore_areas'])

    if any(results['pore_volume_cumulative'] < 0):
        logger.warning(
            "Negative values encountered in cumulative pore volumes. "
            "It is very likely that the model or its limits are wrong. "
            "Check that your pore geometry, meniscus geometry and thickness function "
            "are suitable for the material."
        )

    # Plot if verbose
    if verbose:
        from pygaps.graphing.calc_graphs import psd_plot
        psd_plot(
            results["pore_widths"],
            results["pore_distribution"],
            pore_vol_cum=results['pore_volume_cumulative'],
            method=psd_model,
            left=1.5,
        )

    return results


def psd_pygapsdh(
    volume_adsorbed: "list[float]",
    relative_pressure: "list[float]",
    pore_geometry: str,
    thickness_model: t.Callable,
    condensation_model: t.Callable,
):
    r"""
    Calculate a pore size distribution using an expanded Dollimore-Heal method.
    This function should not be used with isotherms (use instead
    :func:`pygaps.characterisation.psd_meso.psd_mesoporous`).

    Parameters
    ----------
    volume_adsorbed : array
        Volume adsorbed of "liquid" phase in cm3/material.
    relative_pressure : array
        Relative pressure.
    pore_geometry : str
        The geometry of the pore, eg. 'sphere', 'cylinder' or 'slit'.
    thickness_model : callable
        Function which returns the thickness of the adsorbed layer
        at a pressure p, in nm.
    condensation_model : callable
        Function which returns the critical kelvin radius at
        a pressure p, in nm.

    Returns
    -------
    dict
        A dictionary of results of the form:

        - ``pore_widths`` (ndarray) : the widths (or diameter) of the pores, nm
        - ``pore_volumes`` (ndarray) : pore volume for each pore width, cm3/material
        - ``pore_areas`` (ndarray) : specific area for each pore width, m2/material
        - ``pore_distribution`` (ndarray) : volumetric pore distribution, cm3/material/nm

    Notes
    -----
    This method is an extended DH method which is applicable to multiple pore
    geometries (slit, cylinder, spherical).

    The calculation is performed in terms of the characteristic dimension of the
    pore geometry: width for slits, diameter for cylinders and spheres. The
    characteristic dimension is calculated in terms of the Kelvin radius and
    adsorbed layer thickness:

    .. math::

        w_p = 2 * r_p = (r_k + t)

    The Kelvin radius and layer thickness are calculated based on the
    functions provided, no assessment of the meniscus shape or thickness is
    performed here.

    The basic equation for all geometries is as follows:

    .. math::

        V_p = \Big[\Delta V_n - \Delta t_n \sum_{i=1}^{n-1}
                \Big(\frac{\bar{w}_{p,i} - 2 t_{n}}{\bar{w}_{p,i}}\Big)^{l-1}
                \frac{2 l V_{p,i}}{w_{p,i}}\Big]
                \Big(\frac{\bar{w}_p}{\bar{w}_p - 2 t_n}\Big)^l

    Where :
        - :math:`V_p` is the volume of pores of size :math:`\bar{r}_p`
        - :math:`\Delta V_n` is the adsorbed volume change between two points
        - :math:`\bar{r}_p` is the average pore radius calculated as a sum of the
          kelvin radius and layer thickness of the pores at pressure p between two
          measurement points
        - :math:`\bar{r}_k` is the average kelvin radius between two pressure points
        - :math:`t_n` is the layer thickness at point n
        - :math:`\bar{t}_n` is the average layer thickness between two pressure points
        - :math:`\Delta t_n` is the change in layer thickness between two pressure points
        - :math:`l` is the characteristic dimension of the system

    In order to account for different geometries, factors are calculated in
    terms of a characteristic number of the system:

    - In a slit pore, the relationship between pore volume and pore surface is
      :math:`A_p = 2 V_p / w_p`. The pore area stays the same throughout any
      changes in layer thickness, therefore no correction factor is applied.
      Finally, the relationship between the volume of the kelvin capillary and
      the total pore width is
      :math:`\frac{\bar{w}_{p,i}}{\bar{w}_{p,i} - 2 t_{n,i}}`.

    - In a cylindrical pore, the relationship between pore volume and pore
      surface is :math:`A_p = 4 V_p / w_p`. The ratio between average pore area
      at a point and total pore area can be expressed by using
      :math:`\frac{\bar{w}_{p,i} - 2 t_{n,i}}{\bar{w}_{p,i}}`. Finally, the
      relationship between the inner Kelvin capillary and the total pore
      diameter is :math:`\frac{\bar{w}_{p,i}}{\bar{w}_{p,i} - 2 t_{n,i}}^2`.

    - In a spherical pore, the relationship between pore volume and pore surface
      is :math:`A_p = 6 V_p / w_p`. The ratio between average pore area at a
      point and total pore area can be expressed by using
      :math:`\frac{\bar{w}_{p,i} - 2 t_{n,i}}{\bar{w}_{p,i}}^2`. Finally, the
      relationship between the inner Kelvin sphere and the total pore diameter
      is :math:`\frac{\bar{w}_{p,i}}{\bar{w}_{p,i} - 2 t_{n,i}}^3`.


    References
    ----------
    .. [#] "Adsorption by Powders & Porous Solids", F. Rouquerol, J Rouquerol
       and K. Sing, Academic Press, 1999

    """
    # Checks
    if len(relative_pressure) == 0:
        raise ParameterError("Empty input values!")
    if len(volume_adsorbed) != len(relative_pressure):
        raise ParameterError("The length of the pressure and loading arrays do not match.")

    # Pore geometry specifics
    # A constant is defined which is used in the general formula.
    if pore_geometry == 'slit':
        c_length = 1
    elif pore_geometry == 'cylinder':
        c_length = 2
    elif pore_geometry == 'sphere':
        c_length = 3
    else:
        raise ParameterError("Unknown pore geometry.")

    # We reverse the arrays, starting from the highest loading
    volume_adsorbed = volume_adsorbed[::-1]  # [cm3/mat]
    relative_pressure = relative_pressure[::-1]  # [unitless]

    # Calculate the adsorbed volume of liquid and diff, [cm3/mat]
    d_volume = -numpy.diff(volume_adsorbed)

    # Generate the thickness curve, average and diff, [nm]
    thickness = thickness_model(relative_pressure)
    avg_thickness = (thickness[:-1] + thickness[1:]) / 2
    d_thickness = -numpy.diff(thickness)

    # Generate the Kelvin pore radii and average, [nm]
    kelvin_radii = condensation_model(relative_pressure)

    # Critical pore radii as a combination of the adsorbed
    # layer thickness and kelvin pore radius, with average and diff, [nm]
    pore_widths = 2 * (thickness + kelvin_radii)
    avg_pore_widths = (pore_widths[:-1] + pore_widths[1:]) / 2
    d_pore_widths = -numpy.diff(pore_widths)

    # Calculate the ratios of the pore to the evaporated capillary "core", [unitless]
    ratio_factors = (avg_pore_widths / (avg_pore_widths - 2 * avg_thickness))**2

    # Now we can iteratively calculate the pore size distribution
    sum_area_correction = 0  # cm3/nm
    pore_areas = numpy.zeros_like(avg_pore_widths)  # areas of pore populations [m2/mat]
    pore_volumes = numpy.zeros_like(avg_pore_widths)  # volume of pore populations, [cm3/mat]

    for i, avg_pore_width in enumerate(avg_pore_widths):

        # Volume desorbed from thinning of all pores previously emptied, [cm3]
        d_thickness_volume = d_thickness[i] * sum_area_correction

        # Volume of newly emptied pore, [cm3]
        pore_volume = (d_volume[i] - d_thickness_volume) * ratio_factors[i]
        pore_volumes[i] = pore_volume

        # Area of the newly emptied pore, [m2]
        pore_geometry_correction = ((avg_pore_width - 2 * avg_thickness[i]) /
                                    avg_pore_width)**(c_length - 1)
        pore_area = 2 * c_length * pore_volume / avg_pore_width  # cm3/nm
        pore_areas[i] = pore_area * 1e3  # cm3/nm = 1e-6 m3/ 1e-9m

        sum_area_correction += pore_geometry_correction * pore_area

    return {
        "pore_widths": pore_widths[:0:-1],  # [nm]
        "pore_areas": pore_areas[::-1],  # [m2/mat]
        "pore_volumes": pore_volumes[::-1],  # [cm3/mat]
        "pore_distribution": (pore_volumes / d_pore_widths)[::-1],  # [cm3/mat/nm]
    }


def psd_bjh(
    volume_adsorbed: "list[float]",
    relative_pressure: "list[float]",
    pore_geometry: str,
    thickness_model: t.Callable,
    condensation_model: t.Callable,
):
    r"""
    Calculate a pore size distribution using the original BJH method.
    This function should not be used with isotherms (use instead
    :func:`pygaps.characterisation.psd_meso.psd_mesoporous`).

    Parameters
    ----------
    volume_adsorbed : array
        Volume adsorbed of "liquid" phase in cm3/material.
    relative_pressure : array
        Relative pressure.
    pore_geometry : str
        The geometry of the pore, eg. 'sphere', 'cylinder' or 'slit'.
    thickness_model : callable
        Function which returns the thickness of the adsorbed layer
        at a pressure p, in nm.
    condensation_model : callable
        Function which returns the critical kelvin radius at
        a pressure p, in nm.

    Returns
    -------
    dict
        A dictionary of results of the form:

        - ``pore_widths`` (ndarray) : the widths (or diameter) of the pores, nm
        - ``pore_volumes`` (ndarray) : pore volume for each pore width, cm3/material
        - ``pore_areas`` (ndarray) : specific area for each pore width, m2/material
        - ``pore_distribution`` (ndarray) : volumetric pore distribution, cm3/material/nm

    Notes
    -----

    The BJH or Barrett, Joyner and Halenda [#]_ method for calculation of pore
    size distribution is based on a classical description of the adsorbate
    behaviour in the adsorbent pores. Under this method, the adsorbate is
    adsorbing on the pore walls forming a layer of known thickness, therefore
    decreasing the apparent pore volume until condensation takes place, filling
    the entire pore. The two variables, layer thickness and critical pore width
    where condensation takes place can be respectively modelled by a thickness
    model (such as Halsey, Harkins & Jura, etc.) and a model for
    condensation/evaporation based on a form of the Kelvin equation.

    .. math::

        1/2 w_p = r_p = r_k + t

    The original model used the desorption curve as a basis for calculating pore
    size distribution. Between two points of the curve, the volume desorbed can
    be described as the volume contribution from pore evaporation and the volume
    from layer thickness decrease as per the equation above. The computation is
    done cumulatively, starting from the filled pores and calculating for each
    point the volume adsorbed in a pore from the following equation:

    .. math::

        V_p = \Big[\Delta V_n - \Delta t_n \sum_{i=1}^{n-1}
                \Big(\frac{\bar{r}_{p,i} - t_{n}}{\bar{r}_{p,i}}\Big) A_{p,i}\Big]
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
    # Checks
    if len(relative_pressure) == 0:
        raise ParameterError("Empty input values!")
    if len(volume_adsorbed) != len(relative_pressure):
        raise ParameterError("The length of the pressure and loading arrays do not match.")

    # Pore geometry specifics
    if pore_geometry != 'cylinder':
        raise ParameterError(
            "The BJH method is provided for compatibility and only applicable"
            " to cylindrical pores. Use the pyGAPS-DH method for other options."
        )

    # We reverse the arrays, starting from the highest loading
    volume_adsorbed = volume_adsorbed[::-1]
    relative_pressure = relative_pressure[::-1]

    # Calculate the adsorbed volume of liquid and diff, [cm3/mat]
    d_volume = -numpy.diff(volume_adsorbed)

    # Generate the thickness curve, average and diff, [nm]
    thickness = thickness_model(relative_pressure)
    avg_thickness = (thickness[:-1] + thickness[1:]) / 2
    d_thickness = -numpy.diff(thickness)

    # Generate the Kelvin pore radii and average, [nm]
    kelvin_radii = condensation_model(relative_pressure)
    avg_k_radii = (kelvin_radii[:-1] + kelvin_radii[1:]) / 2

    # Critical pore radii as a combination of the adsorbed
    # layer thickness and kelvin pore radius, with average and diff, [nm]
    pore_radii = thickness + kelvin_radii
    avg_pore_radii = (pore_radii[:-1] + pore_radii[1:]) / 2
    d_pore_radii = -numpy.diff(pore_radii)

    # Calculate the ratio of the pore to the evaporated capillary "core", [unitless]
    ratio_factors = (avg_pore_radii / (avg_k_radii + d_thickness))**2

    # Now we can iteratively calculate the pore size distribution
    pore_areas = numpy.zeros_like(avg_pore_radii)  # areas of pore populations [m2/mat]
    pore_volumes = numpy.zeros_like(avg_pore_radii)  # volume of pore populations, [cm3/mat]

    for i, avg_pore_rad in enumerate(avg_pore_radii):

        # Pore area correction
        sum_area_factor = 0  # [m2]
        for x in range(i):
            area_ratio = (avg_pore_radii[x] - avg_thickness[i]) / avg_pore_radii[x]
            sum_area_factor += area_ratio * pore_areas[x]

        # Calculate the volume desorbed from thinning of all pores previously emptied, [cm3/mat]
        # nm * m3 = 1e-7 cm * 1e4 cm2 = 1e-3 cm3
        d_thickness_volume = d_thickness[i] * sum_area_factor * 1e-3

        # Calculate volume of newly emptied pore, [cm3]
        pore_volume = (d_volume[i] - d_thickness_volume) * ratio_factors[i]
        pore_volumes[i] = pore_volume

        # Calculate the area of the newly emptied pore, [m2]
        pore_area = 2 * pore_volume / avg_pore_rad * 1e3  # cm3/nm = 1e-6 m3/ 1e-9m
        pore_areas[i] = pore_area

    return {
        "pore_widths": pore_radii[:0:-1] * 2,  # [nm]
        "pore_areas": pore_areas[::-1],  # [m2/mat]
        "pore_volumes": pore_volumes[::-1],  # [cm3/mat]
        "pore_distribution": (pore_volumes / d_pore_radii / 2)[::-1],  # [cm3/mat/nm]
    }


def psd_dollimore_heal(
    volume_adsorbed: "list[float]",
    relative_pressure: "list[float]",
    pore_geometry: str,
    thickness_model: t.Callable,
    condensation_model: t.Callable,
):
    r"""
    Calculate a pore size distribution using the original Dollimore-Heal method.
    This function should not be used with isotherms (use instead
    :func:`pygaps.characterisation.psd_meso.psd_mesoporous`).

    Parameters
    ----------
    volume_adsorbed : array
        Volume adsorbed of "liquid" phase in cm3/material.
    relative_pressure : array
        Relative pressure.
    pore_geometry : str
        The geometry of the pore, eg. 'sphere', 'cylinder' or 'slit'.
    thickness_model : callable
        Function which returns the thickness of the adsorbed layer
        at a pressure p, in nm.
    condensation_model : callable
        Function which returns the critical kelvin radius at
        a pressure p, in nm.

    Returns
    -------
    dict
        A dictionary of results of the form:

        - ``pore_widths`` (ndarray) : the widths (or diameter) of the pores, nm
        - ``pore_volumes`` (ndarray) : pore volume for each pore width, cm3/material
        - ``pore_areas`` (ndarray) : specific area for each pore width, m2/material
        - ``pore_distribution`` (ndarray) : volumetric pore distribution, cm3/material/nm

    Notes
    -----
    The DH or Dollimore-Heal method [#]_ of calculation of pore size distribution is an
    extension of the BJH method.

    Like the BJH method, it is based on a classical description of the adsorbate
    behaviour in the adsorbent pores. Under this method, the adsorbate is
    adsorbing on the pore walls in a predictable way, and decreasing the
    apparent pore radius until condensation takes place, filling the entire
    pore. The two components, layer thickness (t) and radius (r_k) where
    condensation takes place can be modelled by a thickness model (such as
    Halsey, Harkins & Jura, etc.) and a critical radius model for
    condensation/evaporation, based on a form of the Kelvin equation.

    .. math::

        1/2 w_p = r_p = r_k + t

    The original model used the desorption curve as a basis for calculating pore
    size distribution. Between two points of the curve, the volume desorbed can
    be described as the volume contribution from pore evaporation and the volume
    from layer thickness decrease as per the equation above. The computation is
    done cumulatively, starting from the filled pores and calculating for each
    point the volume adsorbed in a pore from the following equation:

    .. math::

        V_p = \Big(\Delta V_n - \Delta V_m\Big)\Big(\frac{\bar{r}_p}{\bar{r}_p - t_n}\Big)^2

        V_p = \Big[\Delta V_n - \Delta t_n \sum_{i=1}^{n-1} A_{p,i}
                + \Delta t_n \bar{t}_n \sum_{i=1}^{n-1} 2 \pi L_{p,i}
                \Big]\Big(\frac{\bar{r}_p}{\bar{r}_p - t_n}\Big)^2

    Where :
        - :math:`\bar{r}_p` is the average pore radius calculated as a sum of the
          kelvin radius and layer thickness of the pores at pressure p between two
          measurement points
        - :math:`V_p` is the volume of pores of size :math:`\bar{r}_p`
        - :math:`\Delta V_n` is the adsorbed volume change between two points
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
    if len(relative_pressure) == 0:
        raise ParameterError("Empty input values!")
    if len(volume_adsorbed) != len(relative_pressure):
        raise ParameterError("The length of the pressure and loading arrays do not match.")

    # Pore geometry specifics
    if pore_geometry != 'cylinder':
        raise ParameterError(
            "The DH method is provided for compatibility and only applicable "
            "to cylindrical pores. Use the pyGAPS-DH method for other options."
        )

    # We reverse the arrays, starting from the highest loading
    volume_adsorbed = volume_adsorbed[::-1]  # [cm3/mat]
    relative_pressure = relative_pressure[::-1]  # [unitless]

    # Calculate the first differential of volume adsorbed, [cm3/mat]
    d_volume = -numpy.diff(volume_adsorbed)

    # Generate the thickness curve, average and diff, [nm]
    thickness = thickness_model(relative_pressure)
    avg_thickness = (thickness[:-1] + thickness[1:]) / 2
    d_thickness = -numpy.diff(thickness)

    # Generate the Kelvin pore radii and average, [nm]
    kelvin_radii = condensation_model(relative_pressure)
    avg_k_radii = (kelvin_radii[:-1] + kelvin_radii[1:]) / 2

    # Critical pore radii as a combination of the adsorbed
    # layer thickness and kelvin pore radius, with average and diff, [nm]
    pore_radii = thickness + kelvin_radii
    avg_pore_radii = (pore_radii[:-1] + pore_radii[1:]) / 2
    d_pore_radii = -numpy.diff(pore_radii)

    # Calculate the ratios of the pore to the evaporated capillary "core", [unitless]
    ratio_factors = (avg_pore_radii / (avg_k_radii + d_thickness))**2

    # Now we can iteratively calculate the pore size distribution
    sum_area_factor = 0  # cm3/nm
    sum_2pi_length_factor = 0  # cm3/nm2
    pore_areas = numpy.zeros_like(avg_pore_radii)  # areas of pore populations [m2/mat]
    pore_volumes = numpy.zeros_like(avg_pore_radii)  # volume of pore populations, [cm3/mat]

    for i, avg_pore_radius in enumerate(avg_pore_radii):

        # Calculate the volume desorbed from thinning of all pores previously emptied
        # dt * \sum A - t * dt * 2 * \pi * \sum L
        d_thickness_volume = d_thickness[i] * sum_area_factor - \
            d_thickness[i] * avg_thickness[i] * sum_2pi_length_factor  # [cm3/mat]

        # Pore volume, then store
        # dVp = (dV - dVt) * Rp
        pore_volume = (d_volume[i] - d_thickness_volume) * ratio_factors[i]  # [cm3/mat]
        pore_volumes[i] = pore_volume

        # Calculate the two correction factors in the DH method, for area and length
        # Ap = 2 * dVp / rp
        pore_area = 2 * pore_volume / avg_pore_radius  # cm3/nm
        pore_areas[i] = pore_area * 1e3  # cm3/nm = 1e-6 m3/ 1e-9m = 1e3 m2
        sum_area_factor += pore_area

        # 2 * \pi * Lp = Ap / rp
        sum_2pi_length_factor += pore_area / avg_pore_radius  # cm3/nm2

    return {
        "pore_widths": pore_radii[:0:-1] * 2,  # [nm]
        "pore_areas": pore_areas[::-1],  # [m2/mat]
        "pore_volumes": pore_volumes[::-1],  # [cm3/mat]
        "pore_distribution": (pore_volumes / d_pore_radii / 2)[::-1],  # [cm3/mat/nm]
    }
