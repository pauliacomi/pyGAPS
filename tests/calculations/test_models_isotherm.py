"""
This test module tests all the isotherm model functions
"""

import numpy
import pytest

import pygaps.calculations.models_isotherm as mi
from pygaps.utilities.exceptions import ParameterError
from ..conftest import modelling

MODELS = {
    'Henry': [1, 1],
    'Langmuir': [0.5, 0.69315],
    'DSLangmuir': [0.3303, 0.40323],
    'TSLangmuir':  [0.55257, 0.69713],
    'BET': [0.50758, 0.69818],
    'Quadratic': [0.5, 0.54930],
    'TemkinApprox': [0.5, 0.69314],
}


@modelling
class TestIsothermModels(object):
    """
    Tests the isotherm models
    """

    def test_base_class(self):
        "Tests base class for model"
        model = mi.model.IsothermModel()
        model.loading(1)
        model.pressure(1)
        model.spreading_pressure(1)
        model.default_guess(1, 1)

    def test_get_model(self):
        "Model getter function"

        model_name = 'Henry'

        model = mi.get_isotherm_model(model_name)
        assert model.name == model_name

        with pytest.raises(ParameterError):
            mi.get_isotherm_model('bad_model')

    @pytest.mark.parametrize("name, loading",
                             [(key, MODELS[key][0]) for key in MODELS])
    def test_models_loading(self, name, loading):
        "Parametrised test for each model"

        model = mi.get_isotherm_model(name)
        model.params = model.default_guess(1, 1)

        assert numpy.isclose(model.loading(1), loading, 0.001)

    @pytest.mark.parametrize("name, loading",
                             [(key, MODELS[key][0]) for key in MODELS])
    def test_models_pressure(self, name, loading):
        "Parametrised test for each model"

        model = mi.get_isotherm_model(name)
        model.params = model.default_guess(1, 1)

        assert numpy.isclose(model.pressure(loading), 1, 0.001)

    @pytest.mark.parametrize("name, s_pressure",
                             [(key, MODELS[key][1]) for key in MODELS])
    def test_models_s_pressure(self, name, s_pressure):
        "Parametrised test for each model"

        model = mi.get_isotherm_model(name)
        model.params = model.default_guess(1, 1)

        assert numpy.isclose(model.spreading_pressure(1), s_pressure, 0.001)
