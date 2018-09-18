"""
This test module tests all the isotherm model functions
"""

import numpy
import pandas
import pytest

import pygaps.calculations.models_isotherm as mi
from pygaps.utilities.exceptions import ParameterError

MODELS = {
    'Henry': [11, 11, pytest.mark.okay],
    'Langmuir': [1, 2.6376848, pytest.mark.okay],
    'DSLangmuir': [0.911428571, 1.955441434, pytest.mark.okay],
    'TSLangmuir':  [0.821333333, 1.545618429, pytest.mark.okay],
    'BET': [1.121304791, 2.743535635, pytest.mark.okay],
    'Quadratic': [1.040540541, 2.590241611, pytest.mark.okay],
    'TemkinApprox': [1, 2.6376848, pytest.mark.okay],
    'Jensen-Seaton': [1.692307, 3.071936612, pytest.mark.okay],
    'Toth': [1, 2.6376848, pytest.mark.okay],

    'Virial': [11, 1, pytest.mark.xfail],
    'W-VST': [0.9910, 1, pytest.mark.xfail],
    'FH-VST': [0.9910, 1, pytest.mark.xfail],
}


@pytest.mark.modelling
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
        dframe = pandas.DataFrame(data={'n': [0, 1], 'p': [0, 1]})
        model.params = model.default_guess(dframe, 'n', 'p')

        assert numpy.isclose(model.loading(1), loading, 0.001)

    @pytest.mark.parametrize("name, loading",
                             [(key, MODELS[key][0]) for key in MODELS])
    def test_models_pressure(self, name, loading, capsys):
        "Parametrised test for each model"

        model = mi.get_isotherm_model(name)
        dframe = pandas.DataFrame(data={'n': [0, 1], 'p': [0, 1]})
        model.params = model.default_guess(dframe, 'n', 'p')

        assert numpy.isclose(model.pressure(loading), 1, 0.001)

    @pytest.mark.parametrize("name, s_pressure",
                             [pytest.param(key, MODELS[key][1], marks=MODELS[key][2]) for key in MODELS])
    def test_models_s_pressure(self, name, s_pressure):
        "Parametrised test for each model"

        model = mi.get_isotherm_model(name)
        dframe = pandas.DataFrame(data={'n': [0, 1], 'p': [0, 1]})
        model.params = model.default_guess(dframe, 'n', 'p')

        assert numpy.isclose(model.spreading_pressure(1), s_pressure, 0.001)
