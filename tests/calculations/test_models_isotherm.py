"""Test all the isotherm model functions."""

import ast
import os

import numpy
import pytest

import pygaps.calculations.models_isotherm as models
from pygaps.utilities.exceptions import ParameterError

MODEL_DATA_PATH = os.path.join(os.path.dirname(__file__), 'isotherm_model_data')

MODELS_TESTED = {
    'Henry': pytest.mark.okay,
    'Langmuir': pytest.mark.okay,
    'DSLangmuir': pytest.mark.okay,
    'TSLangmuir': pytest.mark.okay,
    'BET': pytest.mark.okay,
    'GAB': pytest.mark.okay,
    'Freundlich': pytest.mark.okay,
    'DR': pytest.mark.okay,
    'DA': pytest.mark.okay,
    'Quadratic': pytest.mark.okay,
    'TemkinApprox': pytest.mark.okay,
    'Jensen-Seaton': pytest.mark.okay,
    'Toth': pytest.mark.okay,
    'Virial': pytest.mark.xfail,
    'W-VST': pytest.mark.xfail,
    'FH-VST': pytest.mark.xfail,
}


@pytest.mark.modelling
class TestIsothermModels():
    """Test the isotherm models."""

    def test_base_class(self):
        """Test base class for model."""
        model = models.base_model.IsothermBaseModel()
        model.loading(1)
        model.pressure(1)
        model.spreading_pressure(1)

    def test_get_model(self):
        """Test model getter function."""
        for model_name in MODELS_TESTED:
            model = models.get_isotherm_model(model_name)
            assert model.name == model_name

        with pytest.raises(ParameterError):
            models.get_isotherm_model('bad_model')

    @pytest.mark.parametrize("name", MODELS_TESTED.keys())
    def test_models_loading(self, name, capsys):
        """Test each model loading function."""

        with open(MODEL_DATA_PATH + "/" + name + ".txt") as f:

            model = models.get_isotherm_model(name)
            model.params = ast.literal_eval(f.readline())

            for line in f:
                line_comp = list(map(float, line.split(',')))
                pressure, loading = line_comp[0], line_comp[1]
                assert numpy.isclose(model.loading(pressure), loading, 0.001)

    @pytest.mark.parametrize("name", [key for key in MODELS_TESTED])
    def test_models_pressure(self, name, capsys):
        """Test each model pressure function."""

        with open(MODEL_DATA_PATH + "/" + name + ".txt") as f:

            model = models.get_isotherm_model(name)
            model.params = ast.literal_eval(f.readline())

            for line in f:
                line_comp = list(map(float, line.split(',')))
                pressure, loading = line_comp[0], line_comp[1]
                assert numpy.isclose(model.pressure(loading), pressure, 0.001)

    @pytest.mark.parametrize("name", [pytest.param(key, marks=MODELS_TESTED[key]) for key in MODELS_TESTED])
    def test_models_s_pressure(self, name):
        """Test each model spreading pressure function."""

        with open(MODEL_DATA_PATH + "/" + name + ".txt") as f:

            model = models.get_isotherm_model(name)
            model.params = ast.literal_eval(f.readline())

            for line in f:
                line_comp = list(map(float, line.split(',')))
                pressure, s_pressure = line_comp[0], line_comp[2]
                assert numpy.isclose(model.spreading_pressure(pressure), s_pressure, 0.001)
