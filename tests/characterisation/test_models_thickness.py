"""
Tests relating to thickness model validation.

All functions in /calculations/models_thickness.py are tested here.
The purposes are:

    - testing the output of the thickness functions
    - testing that the "function getter" is performing as expected.

The thickness functions are tested against pre-calculated values
at several points.
"""

import pytest

import pygaps.characterisation.models_thickness as mt
import pygaps.utilities.exceptions as pgEx


@pytest.mark.characterisation
class TestThicknessModels():
    """Test the thickness models."""
    def test_get_thickness_model(self):
        """Get a regular model."""
        assert mt.get_thickness_model('Halsey') == mt._THICKNESS_MODELS['Halsey']

    def test_get_thickness_model_precalc(self):
        """Get a pre-calculated isotherm model."""
        assert mt.get_thickness_model('SiO2 Jaroniec/Kruk/Olivier')

    def test_get_thickness_error(self):
        """When the model requested is not found we raise."""
        with pytest.raises(pgEx.ParameterError):
            mt.get_thickness_model('bad_model')

    def test_get_thickness_callable(self):
        """When we pass a function, we receive it back."""
        def call_this():
            return 'called'

        ret = mt.get_thickness_model(call_this)
        assert ret() == 'called'

    @pytest.mark.parametrize(
        'modelname, thickness', [
            ('Halsey', [0.46, 0.62, 1.28]),
            ('Harkins/Jura', [0.37, 0.57, 1.32]),
            ('zero thickness', [0, 0, 0]),
            ('SiO2 Jaroniec/Kruk/Olivier', [0.362, 0.538, 1.036]),
            ('carbon black Kruk/Jaroniec/Gadkaree', [0.374, 0.565, 1.257]),
        ]
    )
    def test_models(self, modelname, thickness):
        """Test each model against pre-calculated values."""
        model = mt.get_thickness_model(modelname)
        for index, value in enumerate([0.1, 0.4, 0.9]):
            assert model(value) == pytest.approx(thickness[index], 0.01)
