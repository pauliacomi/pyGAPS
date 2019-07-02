"""
This test module has tests relating to kelvin model validations.

All functions in /calculations/models_kelvin.py are tested here.
There are three goals:

    - testing the meniscus shape determination function
    - testing the output of the kelvin equations
    - testing that the "function getter" is performing as expected.

The kelvin functions are tested against pre-calculated values
at several points.
"""

import numpy
import pytest

import pygaps.calculations.models_kelvin as km
from pygaps.calculations.models_kelvin import _KELVIN_MODELS


@pytest.mark.characterisation
class TestKelvinModels():
    """
    Test the kelvin models.
    """

    @pytest.mark.parametrize('branch, pore, geometry', [
        ('ads', 'slit', 'hemicylindrical'),
        ('ads', 'cylinder', 'cylindrical'),
        ('ads', 'sphere', 'spherical'),
        ('des', 'slit', 'hemicylindrical'),
        ('des', 'cylinder', 'spherical'),
        ('des', 'sphere', 'spherical'),
    ])
    def test_meniscus_geometry(self, branch, pore, geometry):
        """Test the meniscus geometry function."""
        assert km.meniscus_geometry(branch, pore) == geometry

    @pytest.mark.parametrize('model, pressure', [
        (_KELVIN_MODELS['Kelvin'], [0.1, 0.4, 0.9]),
        (_KELVIN_MODELS['Kelvin-KJS'], [0.1, 0.4, 0.9]),
    ])
    @pytest.mark.parametrize('geometry, c_radius', [
        ('cylindrical', [0.104, 0.261, 2.270]),
        ('spherical', [0.208, 0.522, 4.539]),
        ('hemicylindrical', [0.415, 1.044, 9.078]),
    ])
    def test_static_models(self, model, geometry, pressure, c_radius, basic_adsorbate):
        """Test each model against pre-calculated values."""
        temperature = 77.355
        for index, value in enumerate(pressure):
            radius = model(value,
                           geometry,
                           temperature,
                           basic_adsorbate.liquid_density(temperature),
                           basic_adsorbate.molar_mass(),
                           basic_adsorbate.surface_tension(temperature))

            assert numpy.isclose(radius, c_radius[index], 0.01, 0.01)
