"""
This module has functions for calculating the thickness of an adsorbed layer at a
particular pressure
"""
import math

from ..classes.adsorbate import Adsorbate
from ..classes.isotherm import Isotherm
from ..utilities.exceptions import ParameterError


def get_thickness_model(model):
    """
    The ``model`` parameter is a string which names the thickness equation which
    should be used. Alternatively, a user can implement their own thickness model, either
    as an experimental isotherm or a function which describes the adsorbed layer. In that
    case, instead of a string, pass the Isotherm object or the callable function as the
    ``model`` parameter.


    Parameters
    ----------
    model : obj(`str`) or obj(`Isotherm`) or obj(`callable`)
        Name of the thickness model to use.

    Returns
    -------
    callable
        A callable that takes a pressure in and returns a thickness
        at that point.

    Raises
    ------
    ``ParameterError``
        When string is not in the dictionary of models.
    """
    # If the model is a string, get a model from the _THICKNESS_MODELS
    if isinstance(model, str):
        if model not in _THICKNESS_MODELS:
            raise ParameterError("Model {} not an option for t-plot.".format(model),
                                 "Available models are {}".format(_THICKNESS_MODELS.keys()))
        else:
            t_model = _THICKNESS_MODELS[model]

    # If the model is an isotherm, transform it into a thickness curve
    elif issubclass(model, Isotherm):
        t_model = thickness_isotherm(model)

    # If the model is an callable, return it instead
    else:
        t_model = model

    return t_model


def thickness_halsey(pressure):
    """
    Function for the Halsey thickness curve
    Applicability: nitrogen at 77K

    Parameters
    ----------
    pressure : float
        relative pressure
    Returns
    -------
    float
        thickness of layer in nm
    """
    return 0.354 * ((-5) / math.log(pressure))**0.333


def thickness_harkins_jura(pressure):
    """
    Function for the Harkins and Jura thickness curve
    Applicability: nitrogen at 77K

    Parameters
    ----------
    pressure : float
        relative pressure
    Returns
    -------
    float
        thickness of layer in nm
    """
    return (0.1399 / (0.034 - math.log10(pressure)))**0.5


def thickness_isotherm(isotherm):
    """
    Function for calculating thickness from isotherm data
    Applicability: standard isotherms on non-porous materials

    Parameters
    ----------
    isotherm : Isotherm
        isotherm on which to get thickness function
    Returns
    -------
    callable
        function which takes pressure and returns thickness
    """

    adsorbate = Adsorbate.from_list(isotherm.adsorbate)
    layer_thickness = adsorbate.get_prop('layer_thickness')
    loading_max = max(isotherm.loading(branch='ads'))

    def thickness(pressure):
        return isotherm.loading_at(pressure, pressure_mode='relative') / loading_max * layer_thickness

    return thickness


_THICKNESS_MODELS = {
    "Halsey": thickness_halsey,
    "Harkins/Jura": thickness_harkins_jura
}
