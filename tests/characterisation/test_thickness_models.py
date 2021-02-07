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
    @pytest.mark.parametrize(
        'model, thickness', [
            (mt._THICKNESS_MODELS['Halsey'], [0.46, 0.62, 1.28]),
            (mt._THICKNESS_MODELS['Harkins/Jura'], [0.37, 0.57, 1.32]),
        ]
    )
    def test_static_models(self, model, thickness):
        """Test each model against pre-calculated values."""
        for index, value in enumerate([0.1, 0.4, 0.9]):
            assert model(value) == pytest.approx(thickness[index], 0.01)

    def test_get_thickness(self):
        """Get a regular model."""
        assert mt.get_thickness_model('Halsey'
                                      ) == mt._THICKNESS_MODELS['Halsey']

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
