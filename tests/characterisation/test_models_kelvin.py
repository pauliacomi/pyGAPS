"""
This test module has tests relating to kelvin model validations.

All functions in /calculations/models_kelvin.py are tested here.
The purposes are:

    - testing the meniscus shape determination function
    - testing the output of the kelvin equations
    - testing that the "function getter" is performing as expected.

The kelvin functions are tested against pre-calculated values
at several points.
"""

import numpy
import pytest

import pygaps.characterisation.models_kelvin as km
import pygaps.utilities.exceptions as pgEx


@pytest.mark.characterisation
class TestKelvinModels():
    """Test the kelvin models."""
    @pytest.mark.parametrize(
        'branch, pore, geometry', [
            ('ads', 'slit', 'hemicylindrical'),
            ('ads', 'cylinder', 'cylindrical'),
            ('ads', 'sphere', 'hemispherical'),
            ('des', 'slit', 'hemicylindrical'),
            ('des', 'cylinder', 'hemispherical'),
            ('des', 'sphere', 'hemispherical'),
        ]
    )
    def test_meniscus_geometry(self, branch, pore, geometry):
        """Test the meniscus geometry function."""
        assert km.get_meniscus_geometry(branch, pore) == geometry

    @pytest.mark.parametrize(
        'model, pressure', [
            (km._KELVIN_MODELS['Kelvin'], [0.1, 0.4, 0.9]),
        ]
    )
    @pytest.mark.parametrize(
        'geometry, c_radius', [
            ('cylindrical', [0.208, 0.522, 4.539]),
            ('hemispherical', [0.415, 1.044, 9.078]),
            ('hemicylindrical', [0.831, 2.090, 18.180]),
        ]
    )
    def test_kelvin_model(
        self, model, geometry, pressure, c_radius, basic_adsorbate
    ):
        """Test each model against pre-calculated values for N2 at 77K."""
        temperature = 77.355
        pressure = [0.1, 0.4, 0.9]
        for index, value in enumerate(pressure):
            radius = model(
                value, geometry, temperature,
                basic_adsorbate.liquid_density(temperature),
                basic_adsorbate.molar_mass(),
                basic_adsorbate.surface_tension(temperature)
            )

            assert numpy.isclose(radius, c_radius[index], 0.01, 0.01)

    def test_kelvin_kjs_model(self, basic_adsorbate):
        """Test Kelvin KJS model against pre-calculated values for N2 at 77K."""
        temperature = 77.355
        pressure = [0.1, 0.4, 0.9]
        c_radius = [0.715, 1.344, 9.378]
        model = km._KELVIN_MODELS['Kelvin-KJS']
        geometry = 'cylindrical'
        for index, value in enumerate(pressure):
            radius = model(
                value, geometry, temperature,
                basic_adsorbate.liquid_density(temperature),
                basic_adsorbate.molar_mass(),
                basic_adsorbate.surface_tension(temperature)
            )

            assert numpy.isclose(radius, c_radius[index], 0.01, 0.01)

        # Now check for excluding other models
        geometry = 'hemispherical'
        with pytest.raises(pgEx.ParameterError):
            radius = model(
                value, geometry, temperature,
                basic_adsorbate.liquid_density(temperature),
                basic_adsorbate.molar_mass(),
                basic_adsorbate.surface_tension(temperature)
            )

    def test_get_kelvin_error(self):
        """When the model requested is not found we raise."""
        with pytest.raises(pgEx.ParameterError):
            km.get_kelvin_model('bad_model')

    def test_get_kelvin_callable(self):
        """When we pass a function and dict, we receive a partial back."""
        def call_this(addendum):
            return 'called' + addendum

        ret = km.get_kelvin_model(call_this, addendum='add')
        assert ret() == 'calledadd'
