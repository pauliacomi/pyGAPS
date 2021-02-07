"""Utilities for interacting with the CoolProp backend."""

import logging

import CoolProp

logger = logging.getLogger('pygaps')

logger.debug(f"CoolProp version is '{CoolProp.__version__}'")

#: The backend which CoolProp uses, normally either HEOS or REFPROP.
COOLPROP_BACKEND = 'HEOS'


def thermodynamic_backend():
    global COOLPROP_BACKEND
    return COOLPROP_BACKEND


def backend_use_refprop():
    """Switch the equation of state used to REFPROP. User should have REFPROP installed."""
    global COOLPROP_BACKEND
    COOLPROP_BACKEND = 'REFPROP'


def backend_use_coolprop():
    """Switch the equation of state used to HEOS (CoolProp)."""
    global COOLPROP_BACKEND
    COOLPROP_BACKEND = 'HEOS'
