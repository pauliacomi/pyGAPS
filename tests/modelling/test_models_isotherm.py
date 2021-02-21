"""
Test all the isotherm model functions.

All models present in ./modelling/*.py are tested here.
The purposes are:

    - testing the overarching model interaction, and functions
    - testing individual models against known outputs

Models are tested against pre-calculated outputs for the model outputs.
These include loading, pressure and spreading pressure.
The pre-calculated outputs are found as files in the
tests/calculations/isotherm_model_data/*.txt folder.
"""

import numpy
import pytest

import pygaps.modelling as models
import pygaps.utilities.exceptions as pgEx

from .conftest import MODEL_DATA


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
        for model_name in MODEL_DATA:
            model = models.get_isotherm_model(model_name)
            assert model.name == model_name

        with pytest.raises(pgEx.ParameterError):
            models.get_isotherm_model('bad_model')

    @pytest.mark.parametrize("m_name", MODEL_DATA.keys())
    def test_models_default_guess(self, m_name):
        """Test each model's default guess function."""

        model = models.get_isotherm_model(m_name)
        exp_guess = MODEL_DATA[m_name]['initial_guess']
        def_guess = model.initial_guess(1, 1)
        for param in def_guess:
            assert numpy.isclose(exp_guess[param], def_guess[param], 0.01)

    @pytest.mark.parametrize("m_name", MODEL_DATA.keys())
    def test_models_loading(self, m_name):
        """Test each model's loading function."""

        model = models.get_isotherm_model(m_name)
        model.params = MODEL_DATA[m_name]['test_parameters']
        test_values = MODEL_DATA[m_name]['test_values']

        for i, p in enumerate(test_values['pressure']):
            assert numpy.isclose(
                model.loading(p), test_values['loading'][i], 0.001
            )

    @pytest.mark.parametrize("m_name", [key for key in MODEL_DATA])
    def test_models_pressure(self, m_name):
        """Test each model's pressure function."""

        model = models.get_isotherm_model(m_name)
        model.params = MODEL_DATA[m_name]['test_parameters']
        test_values = MODEL_DATA[m_name]['test_values']

        for i, l in enumerate(test_values['loading']):
            assert numpy.isclose(
                model.pressure(l), test_values['pressure'][i], 0.001
            )

    @pytest.mark.parametrize(
        "m_name", [
            pytest.param(
                key,
                marks=MODEL_DATA[key]['test_values']['spreading_pressure_mark']
            ) for key in MODEL_DATA
        ]
    )
    def test_models_s_pressure(self, m_name):
        """Test each model's spreading pressure function."""

        model = models.get_isotherm_model(m_name)
        model.params = MODEL_DATA[m_name]['test_parameters']
        test_values = MODEL_DATA[m_name]['test_values']

        for i, p in enumerate(test_values['pressure']):
            assert numpy.isclose(
                model.spreading_pressure(p),
                test_values['spreading_pressure'][i], 0.001
            )

    @pytest.mark.parametrize("m_name", [key for key in MODEL_DATA])
    def test_models_fit_function(self, m_name):

        model = models.get_isotherm_model(m_name)
        test_values = MODEL_DATA[m_name]['test_values']
        param_guess = model.initial_guess(
            numpy.array(test_values['pressure']),
            numpy.array(test_values['loading']),
        )
        # param_real = MODEL_DATA[m_name]['test_parameters']

        model.fit(
            numpy.array(test_values['pressure']),
            numpy.array(test_values['loading']),
            param_guess,
            optimization_params=dict(max_nfev=1e6),
            verbose=True,
        )
        # for param in param_real:
        #     assert numpy.isclose(model.params[param], param_real[param], 0.01)
