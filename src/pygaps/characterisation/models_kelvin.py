"""
Module contains functions to calculate the critical
evaporation/condensation pore radius the mesopore range,
as a function of pressure.
"""
import typing as t
from functools import partial

import numpy
from scipy import constants

from pygaps.utilities.exceptions import ParameterError


def get_meniscus_geometry(branch: str, pore_geometry: str):
    """
    Determine the meniscus geometry.

    Parameters
    ----------
    branch : {'ads', 'des'}
        Branch of the isotherm used.
    geometry : {'slit', 'cylinder', 'halfopen-cylinder', 'sphere'}
        Geometry of the pore.

    Returns
    -------
    str
        Geometry of the meniscus in the pore.

    """
    if branch == 'ads':
        if pore_geometry == 'slit':
            m_geometry = 'hemicylindrical'
        elif pore_geometry == 'cylinder':
            m_geometry = 'cylindrical'
        elif pore_geometry == 'halfopen-cylinder':
            m_geometry = 'hemispherical'
        elif pore_geometry == 'sphere':
            m_geometry = 'hemispherical'
        else:
            raise ParameterError(
                "Pore geometry must be either 'slit', 'cylinder', 'halfopen-cylinder', or 'sphere'"
            )
    elif branch == 'des':
        if pore_geometry == 'slit':
            m_geometry = 'hemicylindrical'
        elif pore_geometry == 'cylinder':
            m_geometry = 'hemispherical'
        elif pore_geometry == 'halfopen-cylinder':
            m_geometry = 'hemispherical'
        elif pore_geometry == 'sphere':
            m_geometry = 'hemispherical'
        else:
            raise ParameterError(
                "Pore geometry must be either 'slit', 'cylinder', 'halfopen-cylinder', or 'sphere'"
            )
    else:
        raise ParameterError("Adsorption branch must be either 'ads' or 'des'.")

    return m_geometry


def kelvin_radius(
    pressure: "list[float]",
    meniscus_geometry: str,
    temperature: float,
    liquid_density: float,
    adsorbate_molar_mass: float,
    adsorbate_surface_tension: float,
):
    r"""
    Calculate the kelvin radius of the pore, using the standard
    form of the kelvin equation.

    Parameters
    ----------
    pressure :
        Relative pressure (p/p0), unitless.
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
        \ln\Big(\frac{p}{p_0}\Big) = -\frac{2 \cos\theta M_m \gamma}{r_K\rho_l RT}

    *Limitations*

    The Kelvin equation assumes that adsorption in a pore is not different than adsorption
    on a standard surface. Therefore, no interactions with the adsorbent is accounted for.

    Furthermore, the geometry of the pore itself is considered to be invariant accross the
    entire adsorbate.

    See Also
    --------
    pygaps.characterisation.models_kelvin.kelvin_radius_kjs : KJS corrected Kelvin function

    """
    # Define geometry factor depending on meniscus
    if meniscus_geometry == 'cylindrical':
        geometry_factor = 2.0
    elif meniscus_geometry == 'hemispherical':
        geometry_factor = 1.0
    elif meniscus_geometry == 'hemicylindrical':
        geometry_factor = 0.5

    adsorbate_molar_density = adsorbate_molar_mass / liquid_density

    return - (2 * adsorbate_surface_tension * adsorbate_molar_density) / \
        (geometry_factor * constants.gas_constant * temperature * numpy.log(pressure))


def kelvin_radius_kjs(
    pressure: "list[float]",
    meniscus_geometry: str,
    temperature: float,
    liquid_density: float,
    adsorbate_molar_mass: float,
    adsorbate_surface_tension: float,
):
    r"""
    Calculate the kelvin radius of the pore, using the
    Kruck-Jaroniec-Sayari correction.

    Parameters
    ----------
    pressure :
        Relative pressure (p/p0), unitless.
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

    The KJS correction to the kelvin equation equation is modified with a constant
    term of 0.3 nm. The authors arrived at this constant by using the adsorption
    branch of the isotherm on several MCM-41 materials calibrated with XRD data.

    .. math::
        \ln\Big(\frac{p}{p_0}\Big) = -\frac{2 \cos\theta M_m \gamma}{r_K\rho_l RT} + 0.3

    *Limitations*

    Besides the standard limitations of the Kelvin equation, the KJS correction
    is empirical in nature.

    References
    ----------
    .. [#] M. Kruk, M. Jaroniec, A. Sayari, Langmuir 13, 6267 (1997)

    See Also
    --------
    pygaps.characterisation.models_kelvin.kelvin_radius : standard Kelvin function

    """
    # Check for correct geometry
    if meniscus_geometry != 'cylindrical':
        raise ParameterError(
            "The KJS Kelvin correction is not applicable for meniscus "
            "geometries other than cylindrical (adsorption branch + cylindrical pore geometry)."
        )

    adsorbate_molar_density = adsorbate_molar_mass / liquid_density

    return - (2 * adsorbate_surface_tension * adsorbate_molar_density) / \
        (constants.gas_constant * temperature * numpy.log(pressure)) + 0.3


#: List of kelvin model functions
_KELVIN_MODELS = {
    'Kelvin': kelvin_radius,
    'Kelvin-KJS': kelvin_radius_kjs,
}


def get_kelvin_model(model: t.Union[str, t.Callable], **model_args):
    """
    Return a function calculating an kelvin-based critical radius.

    The ``model`` parameter is a string which names the Kelvin model to
    be used. Alternatively, a user can implement their own model,
    as a function which returns the critical radius the adsorbed layer. In that
    case, instead of a string, pass a callable function as the
    ``model`` parameter.

    Parameters
    ----------
    model : str or callable
        Name of the kelvin model to use or function that returns
        a critical radius.

    model_args: dict
        any arguments needed for the model

    Returns
    -------
    callable
        A callable that takes pressure in and returns a critical kelvin radius
        at that point.

    Raises
    ------
    ParameterError
        When string is not in the dictionary of models.
    """
    # If the model is a string, get a model from the _THICKNESS_MODELS
    if isinstance(model, str):
        if model not in _KELVIN_MODELS:
            raise ParameterError(
                f"Model {model} not an implemented Kelvin model. ",
                f"Available models are {_KELVIN_MODELS.keys()}"
            )

        return partial(_KELVIN_MODELS[model], **model_args)

    # If the model is an callable, return it instead
    else:
        return partial(model, **model_args)
