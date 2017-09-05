"""
This module has functions for calculating the thickness of an adsorbed layer at a
particular pressure
"""
import math

from ..classes.adsorbate import Adsorbate

_THICKNESS_MODELS = ["Halsey", "Harkins/Jura"]


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

    adsorbate = Adsorbate.from_list(isotherm.gas)
    layer_thickness = adsorbate.get_prop('layer_thickness')
    loading_max = max(isotherm.loading_ads())

    def thickness(pressure):
        return isotherm.loading_at(pressure) / loading_max * layer_thickness

    return thickness
