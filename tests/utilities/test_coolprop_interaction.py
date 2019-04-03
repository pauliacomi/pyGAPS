"""Test CoolProp interaction."""

import pygaps

import CoolProp


def test_backend_change():
    previous_backend = pygaps.COOLPROP_BACKEND
    pygaps.backend_use_refprop()
    assert previous_backend != pygaps.COOLPROP_BACKEND


def test_backend_names_coolprop():
    for adsorbate in pygaps.ADSORBATE_LIST:
        try:
            adsorbate.backend.molar_mass()
        except pygaps.utilities.exceptions.ParameterError:
            pass


def test_backend_names_refprop():
    version = CoolProp.CoolProp.get_global_param_string("REFPROP_version")
    if version:
        for adsorbate in pygaps.ADSORBATE_LIST:
            pygaps.backend_use_refprop()
            try:
                adsorbate.backend.molar_mass()
            except pygaps.utilities.exceptions.ParameterError:
                pass
            pygaps.backend_use_coolprop()
