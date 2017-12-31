# pylint: disable=C0103,W0612
# flake8: noqa
"""
The module contains the utilities for interacting with the CoolProp backend.
"""

#: The backend which CoolProp uses, either HEOS or REFPROP.
COOLPROP_BACKEND = 'HEOS'


def backend_use_refprop():
    """
    Switches the equation of state used to REFPROP
    User should have REFPROP installed.
    """
    COOLPROP_BACKEND = 'REFPROP'

    return


def backend_use_coolprop():
    """
    Switches the equation of state used to CoolProp.
    """
    COOLPROP_BACKEND = 'HEOS'

    return
