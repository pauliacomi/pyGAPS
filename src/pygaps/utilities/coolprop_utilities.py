"""Utilities for interacting with the CoolProp backend."""
import pygaps

#: The backend which CoolProp uses, either HEOS or REFPROP.
COOLPROP_BACKEND = 'HEOS'


def backend_use_refprop():
    """Switch the equation of state used to REFPROP. User should have REFPROP installed."""
    pygaps.COOLPROP_BACKEND = 'REFPROP'


def backend_use_coolprop():
    """Switch the equation of state used to HEOS (CoolProp)."""
    pygaps.COOLPROP_BACKEND = 'HEOS'
