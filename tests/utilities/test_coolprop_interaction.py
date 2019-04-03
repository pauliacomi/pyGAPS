"""Test CoolProp interaction."""

import pygaps


def test_backend_change():
    previous_backend = pygaps.COOLPROP_BACKEND
    pygaps.backend_use_refprop()
    assert previous_backend != pygaps.COOLPROP_BACKEND


def test_backend_names():
    for adsorbate in pygaps.ADSORBATE_LIST:
        try:
            adsorbate.backend.molar_mass()
        except pygaps.utilities.exceptions.ParameterError:
            pass
        pygaps.backend_use_refprop()
        try:
            adsorbate.backend.molar_mass()
        except pygaps.utilities.exceptions.ParameterError:
            pass
        pygaps.backend_use_coolprop()
