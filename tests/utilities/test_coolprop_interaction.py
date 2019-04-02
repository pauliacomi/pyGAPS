"""Test CoolProp interaction."""

import pygaps


def test_backend_change():
    previous_backend = pygaps.COOLPROP_BACKEND
    pygaps.backend_use_refprop()
    assert previous_backend != pygaps.COOLPROP_BACKEND
