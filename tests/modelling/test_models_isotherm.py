"""Check model equations against historical references and quantify synthetic fits."""

import numpy
import pytest

import pygaps.modelling as models
import pygaps.utilities.exceptions as pgEx

from .conftest import FIT_DOMAINS
from .conftest import FIT_PARAMETER_OVERRIDES
from .conftest import MODEL_DATA

FIT_RTOL = 1e-4
FIT_ATOL = 1e-10
ANALYTICAL_INVERSES = ['Henry', 'Langmuir', 'DSLangmuir', 'BET', 'GAB', 'Freundlich', 'DA', 'DR', 'Quadratic', 'Toth']


def make_fit_case(name):
    parameters = dict(MODEL_DATA[name]['test_parameters'])
    parameters.update(FIT_PARAMETER_OVERRIDES.get(name, {}))
    reference = models.get_isotherm_model(name, parameters=parameters)
    native_input = numpy.geomspace(*FIT_DOMAINS[name], 64)
    held_input = numpy.sqrt(native_input[:-1] * native_input[1:])
    response = getattr(reference, reference.calculates)(native_input)
    assert numpy.isfinite(response).all() and (response > 0).all()
    pressure, loading = (native_input, response) if reference.calculates == 'loading' else (response, native_input)
    return reference, pressure, loading, held_input


def make_fitting_model(reference, pressure, loading):
    model = models.get_isotherm_model(
        reference.name,
        pressure_range=(min(pressure), max(pressure)),
        loading_range=(min(loading), max(loading)),
    )
    # A deterministic non-exact guess exercises recovery, not just solver execution.
    guess = {key: value * (1.2 if index % 2 == 0 else 0.8) for index, (key, value) in enumerate(reference.params.items())}
    if reference.name in ('DSLangmuir', 'TSLangmuir', 'DSToth'):
        sites = range(1, 4 if reference.name == 'TSLangmuir' else 3)
        keys = ('K', 'n_m', 't') if reference.name == 'DSToth' else ('K', 'n_m')
        site_guesses = [tuple(guess[f'{key}{site}'] for key in keys) for site in sites]
        # Deliberately reverse site labels to exercise permutation-equivalent recovery.
        for site, values in zip(sites, reversed(site_guesses)):
            guess.update({f'{key}{site}': value for key, value in zip(keys, values)})
    return model, guess


def recoverable_parameters(model):
    if model.name in ('DSLangmuir', 'TSLangmuir', 'DSToth'):
        sites = range(1, 4 if model.name == 'TSLangmuir' else 3)
        keys = ('K', 'n_m', 't') if model.name == 'DSToth' else ('K', 'n_m')
        return numpy.array(sorted(tuple(model.params[f'{key}{site}'] for key in keys) for site in sites))
    if model.name == 'ChemiPhysisorption':
        # A single temperature identifies only the Arrhenius-weighted capacity.
        return numpy.array(
            [model.params[key] for key in ('n_m1', 'K1', 't1', 'K2')] + [model.params['n_m2'] * numpy.exp(-model.params['Ea'] / model.rt)]
        )
    return numpy.array([model.params[key] for key in model.param_names])


def calculate_fit_rmse(model, pressure, loading):
    if model.name == 'Virial':
        residual = numpy.log(model.pressure(loading) / loading) - numpy.log(pressure / loading)
        return numpy.sqrt(numpy.mean(residual**2))
    if model.calculates == 'loading':
        residual = model.loading(pressure) - loading
        response_range = numpy.ptp(loading)
    else:
        residual = model.pressure(loading) - pressure
        response_range = numpy.ptp(pressure)
    return numpy.sqrt(numpy.mean(residual**2)) / response_range


@pytest.mark.modelling
class TestIsothermModels:
    """Test the isotherm models."""

    def test_check_functions(self):
        """Test the model checking functions."""
        assert models.is_model("Henry")
        assert models.is_model("henry")
        assert models.is_model("henRY")
        assert models.is_model("dslangmuir")
        assert models.is_model_guess("dslangmuir")
        assert models.is_model_iast("dslangmuir")
        assert not models.is_model("horny")
        assert not models.is_model_guess("FHVST")
        assert not models.is_model_iast("DR")

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
            assert numpy.isclose(model.loading(p), test_values['loading'][i], 0.001)

    @pytest.mark.parametrize("m_name", [key for key in MODEL_DATA])
    def test_models_pressure(self, m_name):
        """Test each model's pressure function."""

        model = models.get_isotherm_model(m_name)
        model.params = MODEL_DATA[m_name]['test_parameters']
        test_values = MODEL_DATA[m_name]['test_values']

        for i, load in enumerate(test_values['loading']):
            assert numpy.isclose(model.pressure(load), test_values['pressure'][i], 0.01)

    @pytest.mark.parametrize("m_name", [name for name in MODEL_DATA if name not in ('Virial', 'FHVST', 'WVST')])
    def test_models_s_pressure(self, m_name):
        """Test each model's spreading pressure function."""

        model = models.get_isotherm_model(m_name)
        model.params = MODEL_DATA[m_name]['test_parameters']
        test_values = MODEL_DATA[m_name]['test_values']

        for i, p in enumerate(test_values['pressure']):
            assert numpy.isclose(model.spreading_pressure(p), test_values['spreading_pressure'][i], 0.001)

    @pytest.mark.parametrize('m_name', ['Virial', 'FHVST', 'WVST'])
    def test_models_spreading_pressure_unsupported(self, m_name):
        model = models.get_isotherm_model(m_name)
        with pytest.raises(NotImplementedError):
            model.spreading_pressure(1)

    @pytest.mark.parametrize("m_name", [key for key in MODEL_DATA])
    def test_models_fit_function(self, m_name):
        """Recover a known curve on points not used in the fit."""
        reference, pressure, loading, held_input = make_fit_case(m_name)
        model, guess = make_fitting_model(reference, pressure, loading)
        model.fit(pressure, loading, guess, optimization_params={'max_nfev': 2000})

        prediction = getattr(model, model.calculates)(held_input)
        expected = getattr(reference, reference.calculates)(held_input)
        assert prediction.shape == held_input.shape
        assert numpy.isfinite(prediction).all()
        assert numpy.isfinite(expected).all()
        numpy.testing.assert_allclose(prediction, expected, rtol=FIT_RTOL, atol=FIT_ATOL)
        assert numpy.isfinite(list(model.params.values())).all()
        assert numpy.isfinite(model.rmse) and model.rmse >= 0
        numpy.testing.assert_allclose(model.rmse, calculate_fit_rmse(model, pressure, loading), rtol=1e-6, atol=1e-14)
        numpy.testing.assert_allclose(recoverable_parameters(model), recoverable_parameters(reference), rtol=FIT_RTOL, atol=1e-8)

    @pytest.mark.parametrize('m_name', MODEL_DATA)
    def test_models_array_guess(self, m_name):
        reference, pressure, loading, _ = make_fit_case(m_name)
        model, _ = make_fitting_model(reference, pressure, loading)
        guess = model.initial_guess(pressure, loading)

        assert set(guess) == set(model.param_names)
        assert numpy.isfinite(list(guess.values())).all()
        for key, value in guess.items():
            lower, upper = model.param_bounds[key]
            assert lower <= value <= upper

    @pytest.mark.parametrize('m_name', ['Henry', 'Langmuir', 'Virial'])
    def test_models_fit_rmse_with_residual(self, m_name):
        """Verify reported RMSE with a nonzero, independently recomputed residual."""
        reference, pressure, loading, _ = make_fit_case(m_name)
        noise = 1 + 0.005 * numpy.sin(numpy.arange(len(pressure)))
        if reference.calculates == 'loading':
            loading = loading * noise
        else:
            pressure = pressure * noise
        model, guess = make_fitting_model(reference, pressure, loading)
        model.fit(pressure, loading, guess, optimization_params={'max_nfev': 2000})

        expected_rmse = calculate_fit_rmse(model, pressure, loading)
        assert numpy.isfinite(expected_rmse) and expected_rmse > 1e-5
        numpy.testing.assert_allclose(model.rmse, expected_rmse, rtol=1e-6, atol=1e-14)

    @pytest.mark.parametrize('m_name', ANALYTICAL_INVERSES)
    def test_models_fit_analytical_inverse(self, m_name):
        reference, pressure, loading, held_input = make_fit_case(m_name)
        model, guess = make_fitting_model(reference, pressure, loading)
        model.fit(pressure, loading, guess, optimization_params={'max_nfev': 2000})
        predicted_loading = model.loading(held_input)

        inverse = model.pressure(predicted_loading)
        assert inverse.shape == held_input.shape
        numpy.testing.assert_allclose(inverse, held_input, rtol=FIT_RTOL, atol=FIT_ATOL)
        scalar_inverse = model.pressure(float(predicted_loading[len(held_input) // 2]))
        assert numpy.isscalar(scalar_inverse)
        numpy.testing.assert_allclose(scalar_inverse, held_input[len(held_input) // 2], rtol=FIT_RTOL, atol=FIT_ATOL)

    @pytest.mark.parametrize('m_name', ['Henry', 'Virial'])
    def test_models_fit_exhausted_budget(self, m_name):
        reference, pressure, loading, _ = make_fit_case(m_name)
        model, guess = make_fitting_model(reference, pressure, loading)
        with pytest.raises(pgEx.CalculationError, match='maximum number of function evaluations'):
            model.fit(pressure, loading, guess, optimization_params={'max_nfev': 1})

    def test_virial_fit_insufficient_low_loading(self):
        loading = numpy.array([1.0, 1.5, 2.0])
        reference = models.get_isotherm_model('Virial', parameters=MODEL_DATA['Virial']['test_parameters'])
        pressure = reference.pressure(loading)
        model, guess = make_fitting_model(reference, pressure, loading)
        with pytest.raises(pgEx.CalculationError, match='very few points below 0.5'):
            model.fit(pressure, loading, guess)
