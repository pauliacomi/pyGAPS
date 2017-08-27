"""
This module has functions for calculating the thickness of an adsorbed layer at a
particular pressure
"""
import math

_THICKNESS_MODELS = ["Halsey", "Harkins/Jura"]


def thickness_halsey(pressure):
    """
    Function for the Halsey thickness curve
    Applicability: nitrogen at 77K

    :param pressure: relative pressure
    :returns: thickness of layer in nm
    """
    return 0.354 * ((-5) / math.log(pressure))**0.333


def thickness_harkins_jura(pressure):
    """
    Function for the Harkins and Jura thickness curve
    Applicability: nitrogen at 77K

    :param pressure: relative pressure
    :returns: thickness of layer in nm
    """
    return (0.1399 / (0.034 - math.log10(pressure)))**0.5
