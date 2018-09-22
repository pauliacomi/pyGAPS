"""
This test module has tests relating to kelvin model validations
"""

import numpy
import pytest

import pygaps.calculations.models_kelvin as km
from pygaps.calculations.models_kelvin import _KELVIN_MODELS


@pytest.mark.characterisation
class TestKelvinModels(object):
    """
    Tests the thickness models
    """

    @pytest.mark.parametrize('branch, pore, geometry', [
        ('ads', 'slit', 'cylinder'),
        ('ads', 'cylinder', 'cylinder'),
        ('ads', 'sphere', 'sphere'),
        ('des', 'slit', 'slit'),
        ('des', 'cylinder', 'sphere'),
        ('des', 'sphere', 'sphere'),
    ])
    def test_meniscus_geometry(self, branch, pore, geometry):

        assert km.meniscus_geometry(branch, pore) == geometry

    @pytest.mark.parametrize('model, pressure', [
        (_KELVIN_MODELS['Kelvin'], [0.1, 0.4, 0.9]),
    ])
    @pytest.mark.parametrize('geometry, c_radius', [
        ('slit', [0.104, 0.261, 2.270]),
        ('cylinder', [0.208, 0.522, 4.539]),
        ('sphere', [0.415, 1.044, 9.078]),
    ])
    def test_static_models(self, model, geometry, pressure, c_radius, basic_adsorbate):

        temperature = 77.355
        for index, value in enumerate(pressure):
            radius = model(value,
                           geometry,
                           temperature,
                           basic_adsorbate.liquid_density(temperature),
                           basic_adsorbate.molar_mass(),
                           basic_adsorbate.surface_tension(temperature))

            assert numpy.isclose(radius, c_radius[index], 0.01, 0.01)
